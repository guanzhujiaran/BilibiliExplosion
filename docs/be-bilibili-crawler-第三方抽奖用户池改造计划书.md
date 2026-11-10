# 第三方抽奖（GetOthersLotDyn）用户池改造计划书

## 1. 背景

生产库（`biliopusdb`）round 365 的实际数据：

| 指标 | 数值 |
|---|---|
| 采集用户 | 40 个 |
| 抓到空间动态 | 630 条 |
| 其中转发的原动态命中抽奖 | 404 条（去重后轮次记录 lotNum=325） |
| 人均命中 | 10.1 条 |

用户质量没问题（参与者空间里 70%~100% 的转发都是抽奖），但池子一直是同一批号：

- 生产 Redis `get_other_lot_redis_manager:target_uid_list` 里是 **50 条**，逐条等于代码里的默认 uid 名单；
- 40 个采集用户里 30 个在 `CONFIG.get_others_lot.default_user_uids` 中；
- `TargetUserItem.last_round_lot_count` 清一色为 0；
- 轮次产出逐轮衰减：`362: 2039 → 363: 949 → 364: 580 → 365: 325`。

## 2. 根因

### 2.1 用户池管理根本没在生产入口执行

`_manage_user_list()`（剔除 + 补充）只在 `GetOthersLotDyn.get_new_dyn()` 里被调用，
而该方法只由 HTTP 接口触发（`controller/common/CommonRouter.py:247`）。

生产定时调度走的是 `GenericCrawlerScheduler(crawler=get_others_lot_dyn_robot)`
（`Service/BackgroundService/CrawlerScheduler.py:102-107`），最终调用 `GetOthersLotDynRobot.main()`，
**该方法不含任何用户池管理逻辑**。

因此 Redis 里的名单自写入后再没被更新过，既不会补充新号也不会剔除。

### 2.2 剔除口径用错了字段

`countValidLotByUidInTimeRange()` 按 `t_lotdyninfo.up_uid` 统计，
而 `up_uid` 是「被转发原动态的作者」（`bili_dynamic_item.py:425`），不是采集用户本人。

实测生产 40 个采集用户里，`up_uid` 命中数基本在 0~5 之间（只有本身就是抽奖发起者的两个号是 431 / 514），
阈值「14 天 ≥10 条」下会导致 **全员被剔除**，Redis 列表被写空，随后只能回落默认名单。

### 2.3 列表容量过小

`max_user_list_size = 20`，而 Redis 里历史遗留 50 条，二者口径不一致；
补充阶段最多只补到 20 个，导致覆盖面被人为压缩。

## 3. 改造目标

1. 用户池管理接入**调度路径**，每轮采集结束后自动执行。
2. 剔除口径改为「**用户自己空间里转发的原动态命中抽奖数**」，阈值只按天数和条数。
3. 列表容量调大（200），补充阶段补满。**（已被 5.2 修订为「容量 20 + 超容量裁剪」，再被 5.3 修订为容量 40）**
4. 抓取失败（本轮/窗口内抓到 0 条动态）的用户不参与剔除，避免误杀。

## 4. 具体改动

### 4.1 DAO：新增按用户统计的查询

文件：`be-bilibili-crawler/Service/GetOthersLotDyn/Sql/sql_helper.py`

新增 `LotUserFetchStat`（pydantic 模型，`uid / total / lot`）和：

```python
async def getUserLotHitStats(uid_list, days) -> list[LotUserFetchStat]
```

统计逻辑（一条 SQL）：

```sql
SELECT s.spaceUid, COUNT(*) AS total, SUM(命中抽奖) AS lot
FROM t_lotuserspaceresp s
JOIN t_lotdyninfo t
  ON t.dynId = CAST(JSON_UNQUOTE(JSON_EXTRACT(s.spaceRespJson, '$.orig.id_str')) AS SIGNED)
WHERE s.spaceUid IN (...)
  AND s.dynLotRound_id > (SELECT MAX(lotRound_id) FROM t_lotmaininfo) - :days
GROUP BY s.spaceUid
```

`spaceOffset` 是外层转发动态 id，各用户互不冲突，因此按 `spaceUid` 聚合是安全的。

时间窗口按「最近 N 轮」而不是原动态 `pubTime`：参与者的空间里大量是几天前发布的老抽奖，
用 `pubTime` 过滤会把「今天才被抓到的老抽奖」整体漏掉（实测 7 天窗口下 40 个用户只剩 27 个有数据）。

### 4.2 用户池管理下沉为独立服务

新增 `be-bilibili-crawler/Service/GetOthersLotDyn/core/user_pool_service.py`：

- `LotUserPoolService.manage_user_list()`：先剔除、后补充，返回汇总
- `LotUserPoolService.cull_users()`
- `LotUserPoolService.supplement_users()`
- `LotUserPoolService._get_users_from_latest_lot_dyn_comment()`
- `LotUserPoolService.push_round_summary()`

之所以从 `GetOthersLotDyn` 里搬出来：`robot.py` 需要调用，而 `get_others_lot_dyn.py`
已经 import 了 `robot.py`，放在原处会形成循环导入；项目规范也不允许函数内动态 import。

`GetOthersLotDyn` 保留同名薄封装（保持原有调用方兼容），`get_new_dyn()` 里不再重复调用用户池管理。

### 4.3 接入调度路径

文件：`be-bilibili-crawler/Service/GetOthersLotDyn/core/robot.py`

`main()` 末尾（`isRoundFinished` 写入之后）执行：

```python
summary = await lot_user_pool_service.manage_user_list()
await lot_user_pool_service.push_round_summary(summary)
```

### 4.4 剔除规则

文件：`Service/GetOthersLotDyn/core/user_pool_service.py`

```python
stats = await SqlHelper.getUserLotHitStats(uids, days=settings.get_others_lot.remove_check_days)
removed = [
    item for item in uid_list
    if (stat := stat_map.get(item.uid)) is not None
    and stat.total > 0                     # 抓到过动态才判定
    and stat.lot <= settings.get_others_lot.min_valid_lot_threshold
]
```

### 4.5 补充规则

- 目标数量：`max_user_list_size - len(uid_list)`；
- 单轮新增上限 `supplement_max_per_round = 50`，避免评论翻页耗时失控；
- 只有列表**完全为空**时才使用默认 uid 兜底（保持原语义）；
- `last_round_lot_count / last_round_total_count` 改用新口径（`getUserLotHitStats` 的按轮次版本）。

评论挖人同时修复了翻页参数：`x/v2/reply/main` 的 `next` 是**游标**（首页为 0，后续取响应
`data.cursor.next`），原实现按 1、2、3 递增，首页只能拿到 1 条且马上 `cursor=0` 结束。
实测修复前后（生产动态 `1266420984717508610`）：

```
next=0 mode=2 → replies=8  cursor=122
next=1 mode=2 → replies=1  cursor=0
```

### 4.6 配置调整

> 本节表格是 2026-11-05 的原始改造记录，**容量相关两项已被 5.2 修订**，
> 其余三项（`remove_check_days` / `min_valid_lot_threshold` / 新增字段）保持不变。

文件：`be-bilibili-crawler/CONFIG.py`

| 字段 | 原值 | 新值 | 说明 |
|---|---|---|---|
| `max_user_list_size` | 20 | 200 | 池子容量（5.2 改回 20） |
| `remove_check_days` | 14 | 7 | 剔除统计窗口（天） |
| `min_valid_lot_threshold` | 10 | 1 | 窗口内命中抽奖数 ≤ 此值剔除 |
| `supplement_max_per_round` | — | 50（新增） | 单轮最多补入的新用户数（5.2 改为 20） |

## 5. 验证方式

1. 静态：`python -c "import Service.GetOthersLotDyn.core.robot"` 可导入，无循环依赖。
2. 本地（连生产只读核对，不写）：跑 `LotUserPoolService.cull_users()` 的统计部分，
   确认 40 个用户里被剔除的数量与「7 天内命中 ≤1 条」一致，且抓取失败用户不被误杀。
3. 生产实跑一轮调度，确认：
   - Redis `target_uid_list` 长度 > 20，且出现非默认名单的 uid；
   - `last_round_lot_count` 不再全为 0；
   - 下一轮 `round.allNum` 不再逐轮衰减。

## 5.1 后续补充（2026-11-05 部署后暴露的问题）

### 5.1.1 低活跃用户告警降噪

`space_dynamic_fetcher.py` 里「本轮获取到的动态数量过少」由逐条 `warning` 降为 `debug`，
同时给 `BiliSpaceUserItem` 增加 `fetched_dyn_count` 字段，由 `robot.main()` 在第一阶段结束后
汇总成一条 info，并作为轮次总结的一行（「本轮无新增动态: N 个 [uid...]」）。

不把这批用户直接纳入剔除：刚补充进来的新用户本轮尚未被采集，`total=0` 属于数据未知，
直接剔除会重演「池子被清空」的问题；是否剔除仍交给 `cull_users` 的窗口统计。

### 5.1.2 MQ 超时未处理动态的补偿

`_after_scrapy` 等待 `t_lot_extra_info` 超时（`_MQ_POLL_MAX_IDLE` / `_MQ_POLL_TOTAL_TIMEOUT`）时，
此前只打一行 warning 就丢弃，这些动态会被永久判成「非抽奖」。

改为：

- 未能等到 `extra_info` 的 `dynamic_id` 写入 Redis
  `get_other_lot_redis_manager:pending_extra_refs`（JSON 列表）；
- 下一轮 `_after_scrapy` 开始前 `_retry_pending_extra_refs()`：按 id 回查 `t_lotdyninfo`，
  用 `pub_prize_extract_from_dyn` 重新投递到 MQ，投递后清空该键；
- 本轮全部处理完时也写空列表，避免上一轮的残留被反复重投。

## 5.2 容量回归 20 与超容量裁剪（2026-11-08 修订）

> 本节为本次修订的执行依据，**覆盖第 3 节目标 3 与 4.6 节中「容量 200 / 单轮补充 50」的约定**；
> 其余改造（调度路径接入、剔除口径、评论区挖人、翻页修复、MQ 补偿）全部保持不变。

### 5.2.1 现象与根因

- 每轮采集（第一阶段）的用户数涨到一百多个，`target_uid_list` 从 20 单调涨到 120 / 194；
- `max_user_list_size=200` 且 `supplement_max_per_round=50`：单轮最多补 50，`need_count` 恒为正；
- 剔除条件要求 `total > 0`，`total == 0`（新补入 / 抓取失败）被整体豁免，剔除速度远低于补充速度；
- `supplement_users()` 只在 `need_count > 0` 时补充，**没有 `len > 容量` 的裁剪分支**，
  因此把容量改回 20 后，Redis 里已有的超额用户也不会自动减少；
- 第一阶段遍历 Redis 全量用户，查询量与池子长度线性相关，容量 200 时「查一百多个用户」是必然结果。

### 5.2.2 本轮改动

1. 配置回归：`max_user_list_size: 200 → 20`，`supplement_max_per_round: 50 → 20`（不超过容量）；
   全部通过 `settings.get_others_lot.*` 读取，不在业务代码里硬编码容量数值。
2. 新增超容量裁剪（幂等）：在 `cull_users()` 尾部、写回 Redis 前执行，位置等价于
   「剔除之后、补充之前」，复用同一次 `getUserLotHitStats` 结果，不额外查库。
   排序规则（明确且稳定）：
   - 主键：窗口内命中抽奖数 `stat.lot` 降序；统计缺失（含 `total == 0`）视为 `lot = 0`，排后；
   - 同分：按 Redis 原列表顺序保留（稳定排序，先入池者优先），保持列表原顺序输出；
   - 被裁掉的 uid 记录在 `trimmed`，按原列表顺序输出，便于日志 / 推送对照；
   - `len(uid_list) <= 容量` 时原样返回且 `trimmed` 为空 → 连续跑两轮，第二轮不再触发裁剪。
3. 摘要与推送：`UserPoolCullSummary` / `UserPoolSupplementSummary` / `LotUserPoolSummary`
   增加 `trimmed: list[int]`；`push_round_summary` 恒输出「剔除 / 超容量裁剪 / 新补充」三行数量，
   保证第二轮（无剔除、无补充时）也能看到三个数字。
4. 容量是硬约束：
   - 补充只取 `need_count = 容量 - len(uid_list)`，并对评论区返回做 `[:need_count]` 二次截断；
   - `default_user_uids` 兜底的**触发语义不变**（仅列表完全为空时才使用），但数量截断到容量；
   - `supplement_users()` 写回前再做一次防御性截断，超出部分计入 `trimmed` 并打 warning；
   - 「`total == 0` 豁免剔除」的防误杀语义保持不变，但豁免不再能让池子超过容量。

### 5.2.3 验证

1. 静态：`uv run python -c "import Service.GetOthersLotDyn.core.robot"`；
   `uv run pytest test/test_get_other_lot_main.py -v`。
2. 单测：构造 194 个 uid（`total=0` 与 `lot>0` 混合），验证裁剪后长度 == 20、
   高 `lot` 用户保留、二次裁剪幂等、`added` 后总长度 <= 20、推送含三行数量。
3. 实跑：重启 `be-bilibili-crawler` 容器，回读 Redis 长度、第一阶段用户数日志、
   PushMe 轮次总结，连续两轮稳定在 20 不反弹。

### 5.2.4 不做的事

- 不改 `GetOthersLotDynRobot` 三阶段抓取逻辑、不改 MQ / 判定流程、不改数据库表结构；
- 不改 `RPA-Browser/app/services/execution/actions/**`；
- 不采用「容量保留 200、按活跃度只查 Top N」的替代方案：它只是掩盖池子失控，
  且需要改三阶段抓取逻辑，超出本次范围。

## 5.3 容量回调 40（2026-11-09 修订）

> 本节覆盖 5.2 中「容量 20 / 单轮补充 20」的约定；剔除口径、超容量裁剪、
> `total == 0` 豁免、推送三行数量等其余逻辑全部保持不变。

### 5.3.1 改动

1. `max_user_list_size: 20 → 40`，`supplement_max_per_round: 20 → 40`（仍不超过容量）；
   容量依然只从 `settings.get_others_lot.*` 读取，业务代码不硬编码数值。
2. 逻辑不动：裁剪 / 补充 / 默认名单兜底三条路径本来就是按配置收敛，
   本轮只调整配置数值，不改 `LotUserPoolService` 的算法。
3. 20 → 40 无需迁移：`_trim_to_capacity` 幂等（不足上限时原样返回），
   补充阶段按 `need_count = 40 - 当前长度` 补满，单轮上限 40。

### 5.3.2 影响

- 第一阶段空间采集用户数从 20 涨到 40，查询量约翻倍，`space_dyn_concurrency` 不变；
- 轮次总结推送里的「超容量裁剪(上限40)」自动跟随配置输出；
- 单测里对 20 的硬编码断言同步改为 40，`_build_194_users` 用例仍可覆盖「超容量裁剪」。

### 5.3.3 验证

1. `uv run pytest test/test_get_other_lot_main.py -v`；
2. 重启 `be-bilibili-crawler`，下一轮调度结束后回读 Redis
   `get_other_lot_redis_manager:target_uid_list`，长度为 40。

### 5.4 轮次收尾只等「本轮实际产生/更新的 dynId」（2026-11-11 修订）

> 本节覆盖 5.1.2 中「`_after_scrapy` 等待整轮动态」的约定；补偿重投（Redis
> `pending_extra_refs` + `pub_prize_extract_from_dyn`）与用户池管理逻辑保持不变。

#### 5.4.1 现象与根因

- 生产 GET_OTHERS_LOT_DYN 轮次 370 自 2026-11-09 01:40 起一直 `isRoundFinished=0`，被跨进程复用 3 天；
  2026-01 起的历史动态全部被 `addDynInfo` 的 `session.merge` 改写成该轮，整轮 2913 条；
- `_after_scrapy()` 用 `getAllLotDynInfoByRoundNum(nowRound.lotRound_id)` 取「整轮」动态等待
  `t_lot_extra_info`，其中 345 条历史脏数据既没有 MQ 在途消息也不会再被处理 → 964s 才超时
  （上限 900s），本轮新抓的动态全部进入待补偿列表，前端第三方抽奖列表 `is_lot` 缺失，
  最新可见 `pubTime` 停在 2026-11-10 10:33；
- 轮次一直不结束的另一半原因：`init_round()` 复用未完成轮次时又用旧对象
  `addLotMainInfo()` 覆写 `isRoundFinished`；多进程/被取消的上一轮会把刚被别人关掉的轮次重新打开。
  此外 `bili_space_user_items_set` 只 `update` 不 `clear`，旧 `BiliSpaceUserItem` 的
  `dynamic_infos / pub_lot_users` 跨轮残留，待判定集合本来就不是「本轮」的。

#### 5.4.2 本轮改动（`Service/GetOthersLotDyn/core/robot.py`）

1. 新增每轮清空的 `self._run_dyn_ids: set[int]`；阶段 3 的 `handle_fetch()` 在
   `judge_lottery()` 返回后，从 `BiliDynamicItemJudgeLotteryResult` 的
   `cur_dynamic / orig_dynamic / attached_card` 收集「本次 run 实际写入且已投 MQ」的 dynId
   （`dynContent` 为空的失效动态不投 MQ，跳过）。
2. `main()` 开头清空 `_run_dyn_ids` 与 `bili_space_user_items_set`（连同其它跨轮残留状态一起重置）。
3. `_after_scrapy()` 用 `getDynInfoByIds(sorted(_run_dyn_ids))` 取代
   `getAllLotDynInfoByRoundNum(round)`；官方/预约/充电分支、common 等待循环、超时补偿、
   `is_lot` 口径（`t_lot_extra_info.lot_type='common'`）、`allNum/lotNum/uselessNum` 统计口径
   全部不变，只是集合从「整轮」缩到「本次 run」。日志输出集合规模，便于与超时日志对照。
4. `init_round()`：每次重置 `isPreviousRoundFinished`；未完成轮次若 `created_at` 早于
   `_ROUND_REUSE_MAX_AGE`（默认 6 小时）则先强制关闭旧轮、再新建 `lotRound_id + 1`，
   避免一个僵死轮次被无限复用；用 `created_at` 而不是 `updated_at`（后者每次
   `addLotMainInfo` 都会被刷新，正是「复用 3 天」看不出陈旧的原因）。
5. `main()` 中 `_after_scrapy()` 用 `try/finally` 包住 `isRoundFinished = 1` +
   `addLotMainInfo()`：收尾等待异常/被取消时也一定关闭轮次，单轮超时不再拖住后续轮次。

#### 5.4.3 验证

1. 新增单测：构造「本轮 3 条 + 历史脏数据 345 条挂在同轮」的场景，断言
   `_after_scrapy` 只按 3 条查 `extra_info`、不调用 `getAllLotDynInfoByRoundNum`；
   断言 `_after_scrapy` 抛异常时轮次仍被标记为完成；断言陈旧未完成轮次会新开一轮。
2. `uv run pytest test/test_get_others_lot_round.py test/test_get_other_lot_main.py -v`。
3. 重启 `be-bilibili-crawler` 容器并手动触发一轮（`GET /get_others_lot_dyn`）：
   日志中「本轮实际产生/更新」规模为本轮新增量级、不再出现「本轮有 N 条动态未等到
   extra_info」中 N 为整轮量级；轮次结束后 `isRoundFinished=1`。

#### 5.4.4 不做的事

- 不改 `addDynInfo` 的 merge / MQ 发布逻辑，不动官方/预约/充电/话题抽奖链路；
- 不新增表、不改 `t_lot_extra_info` 的 `is_lot` 判定口径；
- 不改 `pending_extra_refs` 跨轮补偿语义（仍由下一轮 `_retry_pending_extra_refs` 重投）。

## 6. 不做的事

- 不改 `actions/**`（本项目无关）。
- 不改评论接口的 `type/rid` 映射（现有映射 `{"17":"4","1":"8","11":"2","12":"64"}` 已验证可用，
  游客态能拿到 `replies`）。
- 不动 4101128 的处理（另案）。
