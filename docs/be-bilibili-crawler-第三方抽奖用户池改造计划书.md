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
3. 列表容量调大（200），补充阶段补满。
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

文件：`be-bilibili-crawler/CONFIG.py`

| 字段 | 原值 | 新值 | 说明 |
|---|---|---|---|
| `max_user_list_size` | 20 | 200 | 池子容量 |
| `remove_check_days` | 14 | 7 | 剔除统计窗口（天） |
| `min_valid_lot_threshold` | 10 | 1 | 窗口内命中抽奖数 ≤ 此值剔除 |
| `supplement_max_per_round` | — | 50（新增） | 单轮最多补入的新用户数 |

## 5. 验证方式

1. 静态：`python -c "import Service.GetOthersLotDyn.core.robot"` 可导入，无循环依赖。
2. 本地（连生产只读核对，不写）：跑 `LotUserPoolService.cull_users()` 的统计部分，
   确认 40 个用户里被剔除的数量与「7 天内命中 ≤1 条」一致，且抓取失败用户不被误杀。
3. 生产实跑一轮调度，确认：
   - Redis `target_uid_list` 长度 > 20，且出现非默认名单的 uid；
   - `last_round_lot_count` 不再全为 0；
   - 下一轮 `round.allNum` 不再逐轮衰减。

## 6. 不做的事

- 不改 `actions/**`（本项目无关）。
- 不改评论接口的 `type/rid` 映射（现有映射 `{"17":"4","1":"8","11":"2","12":"64"}` 已验证可用，
  游客态能拿到 `replies`）。
- 不动 4101128 的处理（另案）。
