# be-bilibili-crawler 代理选取与获取策略计划书

> 触发问题：第三方抽奖采集（`GET_OTHERS_LOT_DYN`）从 2026-11-09 08:00 起 14+ 小时停留在前两阶段，
> `t_lotdyninfo` 自 2026-11-07 19:54 起 0 新增；空间动态请求大量 `curl (28) timed out` / `(7) CONNECT tunnel failed`。
> 状态：**A 已实施（bug 修复）**，**B/C 按本计划实施**

---

## 1. 现状（2026-11-09 23:00 实测，生产库）

### 1.1 数据事实

| 指标 | 实测值 | 说明 |
|---|---|---|
| `proxy_tab` 总行数 | **1,594,530** | |
| `success_times IS NULL`（从未被使用） | 547,060 | 34.3% |
| `success_times = 0` | 1,552 | |
| `success_times < 0`（用过但净失败） | **1,041,165** | 65.3%，真正的「僵尸」 |
| `success_times > 0`（至少成功过一次） | 4,753 | 0.30% |
| `score` 分布 | `score=50` 548,612；**`MIN(score)=10`**，`score<=0` 为 **0 行** | 见 1.3 第 3 条 |
| `status != 0` | **0 行** | `refresh_proxy()` 每 10 分钟把 `-412` 复位成 0 |
| `MAX(add_ts)` | **2026-10-27 00:01:35**（13 天前） | 近 7 天新增入库 **0** |
| `available_proxy` 行数 / `SUM(counter)` / `MAX(counter)` | **139 / 139 / 1** | 每行只在写入时 counter=1，**从未被取用** |
| `zset_bili_proxy`（Redis db=6）成员数 | **1,335,758** | |

### 1.2 链路与死区（根因 A，已确认）

`available_proxy_sql_helper.get_rand_available_proxy_sql()`：

```
available_num=139 > MIN_USABLE_PROXY_NUM(50) 但 use_good_proxy_flag=False（只在 >150 时置 True）
→ 走 else 分支：139 < 150 且 139 > 50 → 直接 return None, 139
```

即使 `space_dynamic_fetcher` 明确传 `is_use_available_proxy=True`，Attempt 1 也永远拿不到，
回退 Attempt 2 去 `zset_bili_proxy` 做**均匀随机**：命中「近一天活跃」的概率 ≈ 4,753 / 1,335,758 ≈ **0.36%**。

### 1.3 与任务描述不一致的两处实测（影响 C 的实现口径）

1. **获取侧近 13 天零新增**（不是每天 255~593）：`MAX(add_ts)=2026-10-27`。
   原因：`_add_to_proxy_list()` 先用 `is_exist_proxy_by_proxy()` 判重，免费源反复返回的仍是那批
   早已入库的代理串，因此「新入库」恒为 0。**单纯放大 `get_proxy_page` 不会带来新代理**，
   只能让「源站当前仍在列」的老代理重新进入视野 —— 这正是方案 B「新鲜度池」要利用的信号。
2. **`clear_unusable_proxy()` 实际删 0 行**：其口径是 `score <= 0 OR success_times < -3`，
   但 `score` 有 10 的下限（50 分起、每次失败 -10、`refresh_proxy()` 只会把 `< -50` 重置回 50），
   `success_times < -3` 的行数为 **0**。淘汰逻辑形同虚设，104 万僵尸永远留在 zset 里。
   → 因此 C 的僵尸口径改为 **`success_times < 0`**（用失败证据判定，不依赖 score），
   不再以 `score <= 0` 作为必要条件（该条件在本库恒为假）。

### 1.4 为什么不做代理可用性预验证（约束）

- 免费代理寿命只有几小时，预验证通过不代表几分钟后可用；
- `GetProxyFromNet.check_proxy_flag=True` 会走 B 站 `web-interface/zone` 接口，消耗风控额度；
- 预验证本身要发 1 次请求，等于用 1 次额度换 1 个「可能可用」的代理，性价比低于「取到即用 + 用真实结果回写」。

---

## 2. 方案 A：修 `available_proxy` 死区（bug，直接改）

### 2.1 改动

`Utils/代理/数据库操作/available_proxy_sql_helper.py`

- 删除 `use_good_proxy_flag` 作为前置门槛：`available_num > 0` 即从 `available_proxy` 按
  `counter/resp_code/冷却` 条件随机取一条，取不到再返回 `None`；
- `MIN_USABLE_PROXY_NUM` / `MAX_USABLE_PROXY_NUM` 保留但不再参与「是否使用」判定
  （`MAX_USABLE_PROXY_NUM` 仅作池子偏大提示阈值，见代码注释）；
- 把「可用」判定抽成**唯一的 SQL 谓词构造函数**，`get_num()` 与 `get_rand_available_proxy_sql()`
  共用，保证「计数口径」与「可选口径」严格一致（历史上 51 vs 55 的差异就是两处谓词各自演化造成的；
  现在同源，差异只会来自两小时冷却中不可选的行，且这种行既不计入也不可选）。

`Utils/代理/数据库操作/ProxyCommOp.py`

- 保留 `is_use_available_proxy or __available_proxy_num > 300`（300 是「池子很大就别客气」的加速阈值，
  不是使用门槛）；补充注释说明 `__available_proxy_num` 已被 `get_rand_available_proxy_sql`
  回写为最新计数，不会挡住使用。

### 2.2 风险与回滚

纯 bug 修复，无新增依赖/结构；回滚即还原函数。副作用：`available_proxy.counter` 会开始增长（预期）。

---

## 3. 方案 B：取代理从「均匀随机」改为「新鲜度优先」

### 3.1 方案对比

| 方案 | 做法 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| B1 新增 `zset_bili_proxy_fresh` | score=「最近一次被源站列出/入库」的时间戳，取代理时先在这一池里随机 | 语义独立、可整体 DEL 回滚；与 `zset_bili_proxy` 的「分数」语义解耦 | 多一把 key（约 5~15k 成员） | **采用** |
| B2 `select_proxy("rand")` 改高分段随机 | 复用 `_zget_top_score`，按 `score` 分档随机 | 零新增结构 | 新代理的 `score=50` 与老僵尸 `score=40/30/20` 只差几档，且 `refresh_proxy()` 会把老僵尸重置回 50，**排序不可信** | 否决 |

### 3.2 实现

Redis db=6 新增 `zset_bili_proxy_fresh`（member=代理串，score=源站时间戳）：

- **写入**：`_add_to_proxy_list()` 中
  - 新代理：写库成功后 `zadd(fresh, {key: now})`；
  - 已存在代理：若 `status == 0 且 success_times >= 0`（没被判死），也 `zadd(fresh, {key: now})`
    —— 表示「源站当前仍列出它」。被明确判死（`status != 0` 或 `success_times < 0`）的不写，
    避免每轮都把已知坏代理重新塞回去浪费请求。
- **读取**：`_select_proxy_via_zset(top=False)` 先取 fresh 池中**分数最高（最新）的 300 个成员**再随机挑一个，
  取不到才回退 `zset_bili_proxy` 的全局随机；
- **淘汰**：代理被业务请求判失败时（`redis_update_proxy` 且 `status != 0`）同时从 fresh 池 `zrem`；
  取到 MySQL 已不存在的僵尸时也从两个池 `zrem`；
- **过期**：`refresh_proxy_zset()`（每小时）顺带 `ZREMRANGEBYSCORE fresh -inf (now-24h)`，只保留最近 24h。

### 3.3 成本与风险

- 内存：24h 内约 5,000~15,000 成员 × 约 60B ≈ **0.3~1MB**，可忽略；
- 查询：每次取代理多 1 次 `ZCARD`（可省，直接用 `ZRANGEBYSCORE ... DESC LIMIT 300`，空结果即回退）
  + 命中后仍是原来的 1 次 `computed_proxy_str` 索引查询，无额外 MySQL 压力；
- 风险：免费源「在列」不等于「可用」——但取到即用、失败即摘，不会比现状更差（现状 0.36% 命中率）。
- 回滚：`DEL zset_bili_proxy_fresh` + 还原代码；旧池 `zset_bili_proxy` 不受影响。

---

## 4. 方案 C：提高获取侧产出 + 摘除僵尸 + 可观测性

### 4.1 抓取参数

| 参数 | 现状 | 调整为 | 依据 |
|---|---|---|---|
| `GetProxyFromNet.get_proxy_sep_time` | 2h | **45 min** | 调度 5 分钟一次；45min 既提升轮次又不至于把免费源打挂 |
| `GetProxyFromNet.get_proxy_page` | 10 | **25** | 单源翻页上限；失败源由现有 120s 超时自然跳过 |
| `check_proxy_flag` | False | **保持 False** | 约束 2（禁止代理可用性验证） |

### 4.2 僵尸摘除（zset 侧，不动 MySQL 数据行）

- 口径：`ProxyTab.success_times < 0`（见 1.3 第 2 条），`success_times IS NULL`（从未使用）不算僵尸；
- **主池靠整点重建精确剔除**：`select_available_proxy_key_pairs()`（`refresh_proxy_zset()` 的数据源）
  加上同一口径，重建时用临时 key + 原子 `RENAME` 顶替 `zset_bili_proxy`，
  等价于对 104 万僵尸做了一次全量 `ZREM`，且不会出现「清掉又被装回」；
- **不逐 key `ZREM`**：104 万 key 单轮删除会长时间阻塞 Redis，且若按 `LIMIT` 分批，
  同一批僵尸（MySQL 行不删就永远排在最前）每轮都会被重复扫到、永远推进不了；
  原子重建天然规避这两个问题，所以 `clear_unusable_proxy()` 只保留 MySQL 侧删除
  （原口径，实测 0 行）+ 打印僵尸规模，不再做逐 key zrem；
- `ZSET_MIN_REBUILD_SIZE=300` 的保护继续有效：过滤后若不足 300 条，宁可不动 zset；
- **不删除 MySQL 行**：104 万行删除会长时间持锁且不可回滚，收益只是省磁盘；
  现有「`score<=0 or success_times<-3`」删除逻辑保持原样（实测删 0 行，无行为变化）。

### 4.3 可观测性（不涉及任何代理探测）

每轮抓取结束打一条 `WARNING`（生产 `LOG_LEVEL=WARNING` 可见，同时落 `error_MysqlProxy_log.log`）：

```
代理抓取轮次结束：源站返回=xxx 去重后=xxx 抽样丢弃=xxx 新增入库=xxx 已存在=xxx
写入fresh=xxx fresh池=xxx 主zset=xxx 耗时=xxxs
```

用于下次判断「源站没产出」还是「选取策略不对」。

### 4.4 补充获取路径：GitHub 镜像 + 数据驱动源（2026-11-10 追加）

#### 4.4.1 问题：76 个 GitHub 源其实一直是死的

容器内实测（网络可达性，不是代理可用性）：

| 目标 | 结果 |
|---|---|
| `raw.githubusercontent.com` | **连不通** |
| `cdn.jsdelivr.net` | **连不通** |
| V2Ray（`host.docker.internal:10809`） | **连不通**（启动自检也报失败） |
| `https://ghproxy.net/<原 URL>` | 200，完整内容 |
| `https://gh-proxy.com/<原 URL>` | 200 |

而 `GetProxyFromNet.py` 里 76 个 `get_proxy_from_*` 全部写死了
`my_async_httpx.get(..., proxies=_github_proxy)`（V2Ray），所以这些源长期 0 产出，
一轮只有国内几个站在供货（实测 20,066 条，其中新增入库仅 1,330）。

#### 4.4.2 做法：模块内请求入口加镜像回退（不改 76 个方法体）

- `MirrorAwareHttpx`（同名同签名覆盖本模块的 `my_async_httpx`）：GitHub 源的尝试顺序为
  **V2Ray（原行为）→ `settings.github_proxy_urls` 顺序 → 原生直连兜底**，任一路径返回 200 且内容非空即采用；
- 镜像清单是**通用配置**（`CONFIG.Settings.github_proxy_urls`，与 RPA-Browser 的
  `settings.github_proxy_urls` 同语义、同量级：约 120 项，首项 `None` 表示直连，其余为前缀），
  代码里不再硬编码任何镜像域名；可用环境变量覆盖：
  `GITHUB_PROXY_URLS='[null,"https://ghproxy.net/"]'`；
- 配套两个上限（列表太长，必须限流）：`github_proxy_max_attempts=6`（顺序取前 N 个，命中即停）、
  `github_proxy_timeout=12s`（镜像候选的单次超时；部分仓库单文件 1MB+，调用方默认 10s 不够，
  实测 `fyvri` 需 12s 才能下完）；
- jsdelivr 的 `cdn.jsdelivr.net/gh/OWNER/REPO@REF/PATH` 会先归一化成
  `raw.githubusercontent.com/OWNER/REPO/REF/PATH`，再套镜像前缀；
- 非 GitHub 源候选只有一个、行为与改造前完全一致；
- 全部路径失败的返回值改为「falsy + 空 text」的占位响应：原代码 `if req: ... else: self.log.info(req.text)`
  在 req 为 None 时会抛 `AttributeError`，现在能正常走失败分支。

#### 4.4.3 新增数据驱动源表

`SUPPLEMENT_SOURCES`（pydantic `ProxySourceSpec`，新增源只加一行）共 **36 个**，全部实测能拿到数据：

- 第一批（GitHub 5 仓库 / 14 条）：`monosans/proxy-list`（http/socks4/socks5）、`clarketm/proxy-list`、
  `ShiftyTR/Proxy-List`（http/https/socks4/socks5）、`vakhov/fresh-proxy-list`（4 协议）、
  `TheSpeedX/PROXY-List`（socks4/socks5，http 原已有）；
- 第二批扩张（2026-11-10，GitHub 10 仓库 / 17 条 + API 4 条）：
  `ErcinDedeoglu/proxies`（http/https/socks4/socks5）、`jetkai/proxy-list`（4 协议）、
  `hookzof/socks5_list`、`proxifly/free-proxy-list` 的 socks4/socks5 协议路径、
  `zloi-user/hideip.me` socks4、`roosterkid/openproxylist` SOCKS4/SOCKS5_RAW、
  `mmpx12/proxy-list` socks4/socks5、`MuRongPIG/Proxy-Master` socks5；
- 非 GitHub 纯文本 API（4 条）：`api.openproxylist.xyz` socks4/socks5、`proxyspace.pro` socks4/socks5；
- 非 GitHub JSON API（1 条）：`proxylist.geonode.com`。
- 由 `get_proxy_from_supplement_sources()` 抓取：单源 20s 超时、内部并发上限 12
  （源多后全并发容易被镜像限流，实测 `mmpx12` 会返回 200 + `error code: 1015`），
  纳入原有 `(列表, 是否成功)` 约定。

解析侧新增 `extract_proxy_text()`：从行首提取 `[协议://]ip:port`，兼容
`31.43.63.70:4145:Ukraine`（hideip.me）、`ip:port 高匿`、`socks5://ip:port` 等写法，
避免为每种格式再复制一个方法。

#### 4.4.4 上限与处理方式（镜像打通后必须限流）

镜像一旦生效，部分仓库单文件大到离谱（实测 `fyvri` 246,905 行、某源 517,371 行）：

| 上限 | 值 | 理由 |
|---|---|---|
| 单源行数截断 `_RAW_LIST_MAX_LINES` | 3,000 | 只对「≥90% 行是 `ip:port`」的文本生效；HTML/JSON/短文本原样返回 |
| 单轮总量 `_MAX_PROXIES_PER_ROUND` | 150,000（**仅安全阀**） | 正常一轮去重后 9 万条**全量处理**，不抽样；只有镜像集体恢复（99+36 源 × 3000 行 ≈ 40 万）才截断 |

**处理方式：批量预筛，不再逐条查库。** 抓取完成后先对全部候选做一次
`SELECT computed_proxy_str, status, success_times WHERE computed_proxy_str IN (...)`
（每 1000 条一批，`SQLHelper.lookup_proxy_keys`），得到 `existing` / `alive` 两个内存 set；
入库阶段只查内存，新代理才 `INSERT`、存活代理才写 fresh。

这样 9.5 万条候选只需 **96 次批量查询**（原来 9.5 万次单条查询），
全量处理耗时反而比之前「抽样 3 万」更快（实测 200s vs 238s）。

#### 4.4.5 实测效果（同一容器，前后对比）

| 指标 | 补路径前 | 补路径后 |
|---|---|---|
| 源站返回原始条数 | 20,066 | **111,297** |
| 去重后 | 17,331 | 71,131（抽样 30,000） |
| 新增入库 | 1,330 | **6,945** |
| 写入 fresh | 8,349 | 16,160（fresh 池 21,800） |
| 单轮耗时 | 138s | 249s（远小于 45min 间隔） |

#### 4.4.5.1 改为「逐源流式入库」（2026-11-10 二次调整）

**问题**：4.4.4 的单源 3,000 行截断是拿数据换时间——实测一轮有 **38 个源被截断、丢弃 2,352,607 行**
（原始总量约 251 万行，截断后只剩 16 万）。截断既丢数据，又依赖「文件顶部最新」这个假设。

**改法（用时间换空间）**：不再截断，也不再等所有源抓完再统一处理，改成**每个源一返回就立刻入库并释放**。

| 环节 | 改造前 | 改造后 |
|---|---|---|
| 单源上限 | 3,000 行（丢 235 万行） | **无上限**，全量解析 |
| 汇总方式 | `asyncio_gather` 等全部源完成 → 一个 250 万条的 list | `asyncio.as_completed`：谁先完成谁先进库，处理完即释放 |
| 去重 | 全局 list 二次遍历 | 全局 `seen` set 边收边去重（只存代理串，约 250 万 × 100B ≈ 250MB） |
| 入库 | 全部抓完后 `run()` 逐条 | 每批次先 `lookup_proxy_keys` 批量预筛（1000/批），再限并发（10）写库 |
| 内存峰值 | 250 万 dict ≈ 700MB+ | **单源峰值**（最大源 517k 行 ≈ 150MB）+ seen set |
| 单轮总量上限 | 30,000 → 150,000 抽样 | **取消**（流式后总量不再影响内存） |
| 单源超时 | 120s | **180s**（不截断后大文件要下完整，实测 517k 行约 5MB） |

**代价**：一轮时长上升（源站 250 万行全部解析 + 预筛 + 写 fresh），实测 384s；
仍远小于 45 分钟的抓取间隔，且内存从 O(全部) 降到 O(单源)。

**实测对比（同一环境，连续两轮）**：

| 指标 | 截断版（3,000 行/源） | 流式版（无截断） |
|---|---|---|
| 源站返回 | 163,687 | **3,033,681** |
| 去重后 | 95,393 | **600,113** |
| 新增入库 | 9,093 | **104,665** |
| 已存在 | 86,300 | 495,448 |
| 写入 fresh | 50,959 | 278,801（fresh 池 279,689） |
| 入库失败 | — | 0 |
| 耗时 | 200s | 384s |
| 容器内存峰值 | ~1.3GB | ~1.5GB（含常驻服务进程） |

**过程中发现并修复的坑**：源方法返回的是裸代理字典 `{"http": ..., "https": ...}`，
直接传给 `_add_to_proxy_list` 会 `KeyError`（它需要 `proxy/status/update_ts/score` 结构），
而 `asyncio_gather` 默认把异常吞成 `None`、`log=None` 时不记录 —— 首轮出现「已入库 0 条」静默失败。
现在入库前统一 `_proxy_warrper()` 包装，且 `_one()` 自己捕获异常回传给调用方统计
（`ingest_failures` 进 WARNING 日志），不再依赖 gather 的返回值。

**回滚**：恢复 `truncate_raw_list_payload` 与 `__get_proxy` 的 gather 版本即可，无数据变更。

#### 4.4.5.2 再进一步：96 个源方法改成 async generator + 底层流式读取

上面那版还有一个残留：源方法仍把整个文件 `req.text` 读进内存再 `split("\n")`，
单源峰值取决于文件大小（最大 51 万行 ≈ 150MB）。本次把源头也改成流式：

| 环节 | 改造前 | 改造后 |
|---|---|---|
| 源方法签名 | `async def get_proxy_from_x() -> tuple[list, bool]` | `async def get_proxy_from_x() -> AsyncGenerator[list, None]`（96 个全部改） |
| 纯文本源（75 个） | `req.text.split("\n")` 一次性解析 | 统一走 `_iter_raw_list_source()`：`iter_lines()` 逐行 yield → 每 2000 条 yield 一批 |
| HTML / JSON / 分页源（21 个） | 同上 | 保留各自解析逻辑，解析完 `yield` 一次（这些源只有几百条，不是内存瓶颈） |
| 底层读取 | `AsyncSession.get()` 整包返回 | `AsyncSession.get(stream=True)` + `resp.aiter_lines()`，边下边切行 |
| 调度 | `asyncio.as_completed` 等「源整体返回」 | `asyncio.Queue` + `_pump_source()`：源每产出一批就入队，主循环即时入库 |
| 并发 | 96 个源同时发请求 | 流式连接会一直占用，限制 `_SOURCE_CONCURRENCY=32` |
| 镜像回退 | 整包 200 才采用 | `iter_lines()` 里第一个连通的候选即用，读到一半失败自动换下一个候选 |

**内存**：从「单源 150MB」降到「一批 2000 条 ≈ 0.5MB」+ 跨源去重集合（60 万串 ≈ 60MB）。

**实测（连续第二轮，源站内容与上一轮高度重叠）**：

| 指标 | 非流式（4.4.5.1） | 流式本版 |
|---|---|---|
| 源站返回 | 3,033,681 | 3,077,974 |
| 去重后 | 600,113 | 613,862 |
| 新增入库 | 104,665（首轮，库内没有） | 7,456（同一批源的第二轮，基本都命中） |
| 已存在 | 495,448 | 606,406 |
| 写入 fresh | 278,801 | 289,522（fresh 池 290,740） |
| 入库失败 | 0 | 0 |
| 耗时 | 384s | **323s** |
| 容器内存峰值 | ~1.5GB | ~1.43GB |

单源验证：`fyvri` 的 1.45MB 归档文件 **246,905 行 / 7.8s** 流式读完（走 gh-proxy 镜像），
全程没有把整份文本攒进内存。

#### 4.4.5.3 最终形态：去掉 Redis 池，取代理只用 MySQL 随机（2026-11-10）

**背景**：前面几版把 Redis 当"热索引"（`zset_bili_proxy` + `fresh` + 变更缓冲），需要重建、
过期清理、口径对齐等一整套维护成本。实测池子里的有效信号极弱（68.4 万可用行里只有 0.9%
"曾经成功过"、98.9% 从未使用），分层带来的收益有限，因此按"彻底简化"处理：

| 项 | 改造前 | 改造后 |
|---|---|---|
| 取代理 | Redis `ZRANDMEMBER` → 按 key 回 MySQL 查整行 | **MySQL 随机主键起点，一条 SQL 拿到整行** |
| 新鲜度池 | `zset_bili_proxy_fresh`（29 万） | **删除** |
| 主索引池 | `zset_bili_proxy`（68.4 万） | **删除** |
| 评分 | 写 Redis 变更缓冲 `bili_proxy_changed_hm`，整点回写 MySQL | **每次事件单条 UPDATE**（`computed_proxy_str` 索引） |
| 整点同步 | `check_redis_data` / `sync_2_database` / `refresh_proxy_zset` | **全部删除**，连定时任务一起 |
| 池状态接口 | 从 Redis 取计数 | MySQL 实时 count |

**关键性能约束（实测，69 万可用行）**：

| 写法 | 耗时 |
|---|---|
| `ORDER BY RAND() LIMIT 1` | **2,301~2,370 ms** |
| `LIMIT 1 OFFSET 300000` | 1,656~1,749 ms |
| 随机 `proxy_id` 起点 + `ORDER BY proxy_id LIMIT 1` | **14~18 ms** |

→ 所以"MySQL 直接随机"必须用随机主键起点，`ORDER BY RAND()` 会让每次请求多等 2.3 秒。
随机点落在尾部空洞（取空）时回退"从头取下一条"，保证有结果。

**改动清单**：

- `async_proxy_op_alchemy_mysql_ver.py`：删除 `SubRedisStore`（254 行）、`sync_2_database`/
  `check_redis_data`（109 行）、`_select_proxy_via_zset`/`select_available_proxy_key_pairs`/
  `refresh_proxy_zset`（88 行）；新增 `select_random_proxy()`、`get_usable_proxy_num()`、
  `to_proxy_key()`（模块级）；`update_to_proxy_list()` 改为单条 UPDATE（分数 SQL 原子增减 + ±10000 钳制）；
  `get_proxy_database_redis()` 改 MySQL 统计。
- `ProxyCommOp.get_available_proxy()`：只剩一条路径（MySQL 随机 + 取不到就抓一轮），
  `is_use_available_proxy` 保留签名但不再生效。
- `GetProxyFromNet`：不再写 fresh 池；移除 `check_redis_data` 调用；统计字段改为
  `新增/已存在（其中判死）/入库失败/可用池`。
- `available_proxy` 表保留（仍由 `ProxyEvent` 写入），但**不参与取代理**，仅作统计与将来恢复用。

**实测**：

| 项 | 结果 |
|---|---|
| `select_proxy("rand")` 10 次 | min 5.6ms / avg 9.0ms / max 24.8ms |
| `update_to_proxy_list`（单条 UPDATE） | 8.4ms，返回 True |
| 完整一轮抓取 | 源站 3,063,275 → 去重 613,706 → 新增 327（第三轮，池已饱和）/ 已存在 613,379（其中判死 324,368），可用池 691,965，耗时 330s |
| Redis 是否还在写 | `zset_bili_proxy` 684,188 / `zset_bili_proxy_fresh` 290,740 / `changed_hm` 0，**一轮跑完三个数都不变** |

**回滚**：`git revert` 这几个文件 + 重建 zset（原重建代码已删，需从历史版本恢复）。

#### 4.4.5.4 收尾：删 `available_proxy` 表 + 超时 15s + 并发翻倍（2026-11-10）

| 项 | 改动 | 说明 |
|---|---|---|
| `available_proxy` 表 | **DROP**（迁移 `3f7c1a92d5b8`） | 取代理已不读它，`ProxyEvent` 也不再写；同步删除 `ProxyModel.AvailableProxy`、`ProxyEvent` 里的 5 处调用、`available_proxy_sql_helper.py` 整个文件 |
| 代理请求超时 | 30s → **15s**（`RequestWithProxy.timeout` / `available_proxy_timeout`） | 免费代理多数 5~10s 内要么连通要么直接失败，30s 只是白占 worker；缩短后坏代理更快被打分淘汰 |
| 空间采集并发 | 2 → **4**（`CONFIG.concurrency.space_dyn`） | 随机取代理命中率下降，用并发补吞吐 |
| 抽奖判定并发 | 2 → **4**（`CONFIG.concurrency.judge_dyn`） | 同上 |

**取舍**：并发越高，同一代理在短时间内的请求越密集，被 B 站风控（-412）的概率也越高；
4 是「翻倍但保守」的值，若观察到 412 明显上升可回调到 3，或改为「每代理最小间隔」。

**验证**：

```
concurrency: dyn_detail=20 rm_following=20
             reserve=1 topic=1 refresh_lot_db=1 sams_club=1 sams_club_spu=1
             lottery_api=20 bili_live=20 get_others_lot_dyn=1
             space_dyn=4 judge_dyn=4
             proxy_source_fetch=32 / ingest=10 / supplement=12
timeout= 15 available_proxy_timeout= 15
proxy= http://47.82.180.34:3129        # 取代理正常（MySQL 随机）
proxy_db 剩余表：alembic_version / proxy_tab   # available_proxy 已删除
alembic_version：3f7c1a92d5b8          # 迁移已应用
GetProxyStatus：200
```

#### 4.4.5.5 并发统一到 `ConcurrencyConfig`（2026-11-10）

原先并发数散落在三处：各爬虫 `CrawlerConfig.max_sem`、`GetOthersLotDynConfig.space_dyn_concurrency`
/ `judge_dyn_concurrency`、`GetProxyFromNet` 的模块常量。现在**只有一个入口** `CONFIG.concurrency`，
且**每个爬虫一项**（完整字段与取值见 4.4.5.6）：

- 各爬虫不再写并发数字，只声明 `concurrency_key`（如 `"reserve"` → `concurrency.reserve`）；
- `GetOthersLotDynConfig` 里的两个并发字段**已删除**，`robot.py` 直接读 `settings.concurrency.*`；
- 抓取侧三个常量改为读 `settings.concurrency.*`；
- 部署时可用环境变量覆盖（嵌套模型双下划线，需 `env_nested_delimiter="__"`）：
  `CONCURRENCY__RESERVE=2`、`CONCURRENCY__SPACE_DYN=6`。

**回滚**：`alembic downgrade -1` 会重建空表（数据不可恢复），再还原 `ProxyModel`/`ProxyEvent`/helper。

#### 4.4.5.6 爬虫配置全部统一（2026-11-10）

原先 11 个爬虫的 `CrawlerConfig` 子类各自抄一遍 `worker_max_timeout` / `requeue_on_*` /
`max_retries` / `log_*` / `worker_error_delay`，真实差异只有 5 项。现在统一到两个入口：

| 入口 | 内容 | env 示例 |
|---|---|---|
| `CONFIG.concurrency`（`ConcurrencyConfig`） | **每个爬虫一项**：`dyn_detail` / `rm_following` / `reserve` / `topic` / `lottery_api` / `refresh_lot_db` / `sams_club` / `sams_club_spu` / `bili_live` / `get_others_lot_dyn`，外加 `space_dyn`、`judge_dyn`、`proxy_source_*`、兜底 `crawler_workers` | `CONCURRENCY__RESERVE=2` |
| `CONFIG.crawler_runtime`（`CrawlerRuntimeConfig`） | 所有运行行为：`worker_max_timeout`(None=不限)、`requeue_on_fetch_fail`、`requeue_on_timeout`、`max_retries`(-1=无限)、`log_timeout_error`、`log_error`、`worker_error_delay` | `CRAWLER_RUNTIME__MAX_RETRIES=3` |

**并发不再写在各爬虫里**：`CrawlerConfig` 只有 `concurrency_key`（指向 `ConcurrencyConfig` 的字段名）
和 `max_sem`（运行时覆盖，平时为 0）。解析在 `UnlimitedCrawler.__init__`：
`getattr(CONFIG.concurrency, config.concurrency_key)`，key 拼错会打 WARNING 并回退 `crawler_workers`。

**其它运行行为的哨兵值**：`worker_max_timeout = -1` → 跟随 `crawler_runtime.worker_max_timeout`
（不能用 `None`，`None` 本身是「不限制」的合法值）；其余字段 `None` → 跟随 `crawler_runtime`。

各爬虫当前取值（`CRAWLER_CONFIG_REGISTRY` 实测）：

| Config | concurrency_key | 并发 | 说明 |
|---|---|---|---|
| DynDetail | `dyn_detail` | 20 | |
| GetRmFollowingListV2 | `rm_following` | 20 | |
| Reserve / Topic | `reserve` / `topic` | 1 | 串行（接口要求顺序执行） |
| LotteryApi | `lottery_api` | 20 | DYN/RESERVE 两个实例共用，不再由 `sem_num` 覆盖（原实际为 2） |
| RefreshBiliLotDatabase | `refresh_lot_db` | 1 | 串行，避免与采集抢 DB |
| SamsClub / SamsSPU | `sams_club` / `sams_club_spu` | 1 | |
| BiliLive | `bili_live` | 20 | |
| GetOthersLotDyn | `get_others_lot_dyn` | 1 | 运行时切到 `space_dyn` / `judge_dyn` |

解析在 `UnlimitedCrawler.__init__`（`_resolve()`），各爬虫 Config 只声明「与统一值不同」的项。
`worker_max_timeout` 统一默认保持 **None（不限制）**：刷新抽奖库 / 直播监控 / 分页抓取这类
单任务时长不可预估，强行 300s 会打断原本能跑完的任务；原本显式 300s 的 4 个爬虫保留声明。

解析结果（`CRAWLER_CONFIG_REGISTRY` 实测）：

| Config | rq_fail | rq_timeout | retries | wmt | log_timeout | err_delay | sem |
|---|---|---|---|---|---|---|---|
| GetProxyMethods | False | True | -1 | 300 | False | 300 | 20 |
| DynDetail | **True** | True | -1 | 300 | False | 300 | 20 |
| GetRmFollowingListV2 | False | True | -1 | None | False | 300 | 20 |
| Reserve / Topic | False | True | -1 | 300 | False | 300 | 1 |
| LotteryApi | False | True | -1 | None | False | 300 | 20 |
| RefreshBiliLotDatabase | False | True | -1 | None | False | 300 | 1 |
| SamsClub / SamsSPU | False | True | -1 | None | False | 300 | 1 |
| BiliLive | False | True | -1 | None | False | 300 | 20 |
| GetOthersLotDyn | False | **False** | **0** | None | False | **0** | 1 |

唯一有意的行为变化：`log_timeout_error` 由基类原默认 `True` 统一为 `False`（生产少噪音），
其余字段与原值逐项一致。

#### 4.4.6 取舍与风险

- 镜像清单来自 `settings.github_proxy_urls`（参考 RPA-Browser 的百项列表），公共镜像的可用性不由我方保证；
  前 6 个候选通常含 `gh-proxy.com` / `gh-proxy.org` / `ghproxy.net` 等主力站，全挂时回退原生直连，
  最终失败也只是少一份数据（单源失败不影响其它源），不会阻塞轮次；
- 列表可持续追加、失效项留在原位：`github_proxy_max_attempts` 决定每轮实际尝试几个，
  想试更多镜像调大即可（代价是单源耗时上限 = 10s + N × `github_proxy_timeout`，仍受 120s 单源上限约束）；
- 采样只取列表前 3,000 行：多数仓库把最新代理放在文件顶部，配合 fresh 池（按时间戳取最新）已足够；
  真需要更多可调大 `_RAW_LIST_MAX_LINES`；
- 新增源只写入 fresh 池，不进主 zset（主 zset 由整点重建对齐），因此「新入库能否立即被使用」依赖 fresh 池 ——
  这正是方案 B 的池，取代理时优先。滚动回滚：还原 `my_async_httpx` 覆盖与 `SUPPLEMENT_SOURCES` 即可。

---

## 5. 验收标准

| 指标 | 采集方式 | 期望 |
|---|---|---|
| available_proxy 被使用 | `SELECT SUM(counter), MAX(counter) FROM proxy_db.available_proxy;` | counter 总和持续增长（当前 139/139/1） |
| 主 zset 去僵尸 | `docker exec fastapi-redis redis-cli -n 6 zcard zset_bili_proxy` | 1,335,758 → 约 55 万（`success_times<0` 被剔除） |
| fresh 池建立 | `docker exec fastapi-redis redis-cli -n 6 zcard zset_bili_proxy_fresh` | > 0 且随抓取轮次变化 |
| 抓取可观测 | `docker logs be-bilibili-crawler \| grep 代理抓取轮次结束` | 每轮一条，字段齐全 |
| 空间请求成功率 | `docker logs --since 30m be-bilibili-crawler \| grep -c 重试后成功` vs `遇到可忽略错误` | 错误占比 < 20% |
| 单测 | `uv run pytest test/test_proxy_pool_selection.py -q` | 全绿 |

**禁止**用 curl/脚本验证某个代理通不通（约束 2/4）。

---

## 6. 实施顺序与回滚

1. A（bug）→ 单测；
2. B（新鲜度池）→ 单测；新增 key 可单独 DEL；
3. C（抓取参数 + 僵尸口径 + WARNING）；
4. `uv run python -m compileall` + `uv run pytest test/test_proxy_pool_selection.py -q`；
5. 重启 `be-bilibili-crawler`（bind mount，无需重建镜像），按第 5 节观测。

回滚：代码回退 + `DEL zset_bili_proxy_fresh`；无表结构变更、无数据迁移，`zset_bili_proxy` 每小时由 MySQL 重建，
回滚后最多 1 小时自动恢复原状态。

---

## 7. 实施记录与验证（2026-11-09 23:46~23:55）

重启 `be-bilibili-crawler` 后逐项验证（全部为只读取数 / 手动触发一轮抓取，**未做任何代理可用性探测**）：

| 项 | 命令 | 结果 |
|---|---|---|
| A：available_proxy 可用即用 | 容器内 `get_rand_available_proxy_sql()` | `available_num=139`，返回代理，`counter` 1→2 |
| A：调用方不再被门槛挡住 | 连续 5 次 `get_available_proxy(is_use_available_proxy=True)` | 5/5 `used_available_proxy=True`；`SUM(counter)` 140→145 |
| C：zset 去僵尸 | 手动 `check_redis_data(force=True)` | `zset_bili_proxy` 1,335,758 → **553,230**；僵尸 1,041,290 条被剔除；MySQL 删除 2 行（原口径） |
| C：抓取产出 | 手动 `get_proxy_methods.main()` | 源站返回 20,066 / 去重 17,331 / **新增入库 1,330** / 已存在 16,001 / 写入 fresh 8,349（新增 1,330 + 已存在未判死 7,019）/ 耗时 138s |
| C：可观测 WARNING | `docker logs be-bilibili-crawler \| grep 代理抓取轮次结束` | `代理抓取轮次结束：源站返回=20066 去重后=17331 新增入库=1330 已存在=16001 写入fresh=8349 fresh池=8349 主zset=553230 耗时=138s` |
| B：fresh 池建立 | `Z CARD zset_bili_proxy_fresh` | 0 → **8,349** |
| B：取代理命中 fresh | 抽样 10 次 `select_proxy("rand")` 并回查 `ZSCORE` | **10/10** 命中 fresh 池 |
| 单测 | `uv run pytest test/test_proxy_pool_selection.py -q` | 7 passed |
| 静态检查 | `uv run python -m compileall` + IDE lint | 无新增错误 |
| 轮次未被误增 | `t_lotuserspaceresp dynLotRound_id` | 仍为 360（重启只中断，不跳轮） |

补充路径（4.4）追加验证，2026-11-10 00:00~00:06：

| 项 | 命令 | 结果 |
|---|---|---|
| 镜像回退生效 | 直接调 `get_proxy_from_fyvri_fresh_proxy_list_http()` | V2Ray 失败 → ghproxy 超时 → **gh-proxy 成功**，拿到 246,905 条（截断后 3,000） |
| jsdelivr 还原 | `get_proxy_from_gh_proxifly_free_proxy_list()` | jsdelivr 直连失败 → 镜像按 raw 路径成功，11,075 条 |
| 补充源 | `get_proxy_from_supplement_sources()` | 15 个源全部成功，解析 8,315 条 |
| 单轮总量 | 完整一轮 | 源站返回 111,297 → 去重 71,131 → 抽样 30,000 → 新增入库 6,945，耗时 249s |
| 补充源（36 个） | `get_proxy_from_supplement_sources()` | 36/36 源成功，解析 **46,230** 条（首批 15 源时 8,315） |
| 加源后单轮（抽样 3 万） | 完整一轮 | 源站返回 158,991 → 去重 92,147 → 抽样 30,000 → 新增入库 4,265 / 已存在 25,735，fresh 池 37,733，耗时 238s |
| 加源后单轮（全量） | 完整一轮 | 源站返回 **163,687** → 去重 **95,393 全量处理**（抽样丢弃 0，库中已存在 86,300 / 其中可用 41,866）→ 新增入库 **9,093**、写入 fresh 50,959、fresh 池 53,555，耗时 **200s** |
| 流式版单轮（无单源截断） | 完整一轮 | 源站返回 **3,033,681** → 去重 **600,113** → 新增入库 **104,665**、写入 fresh 278,801、fresh 池 279,689、入库失败 0，耗时 **384s**，内存峰值 ~1.5GB |
| 镜像配置化 | `GITHUB_PROXY_URLS='[null,"https://ghproxy.net/"]'` 启动 | 配置被正确解析，候选 = 直连 + 镜像（环境变量可覆盖） |
| 百项列表可用性 | `get_proxy_from_gh_proxifly_free_proxy_list()` | 走 `gh-proxy.com` 成功，11,075 条 |
| 大文件源 | `get_proxy_from_fyvri_fresh_proxy_list_http()` | 12s 超时下走 `gh-proxy.com` 成功，截断后 3,000 条 |
| 单测 | `uv run pytest test/test_proxy_source_mirror.py test/test_proxy_pool_selection.py -q` | 40 passed |

### 7.1 环境事实（需要人工确认，不在本次改动范围）

该容器 `IS_DEV=1`（来自 `be-bilibili-crawler/.env.fastapi.dev`），而 `FastapiLifespan` 在
`IS_DEV` 为真时**不启动 `GLOBAL_SCHEDULER`**，因此：

- 代理抓取（`GET_PROXY_METHODS_SCHEDULER`）、整点 zset 重建（`sync_proxy_database_redis`）、
  第三方抽奖采集（`GET_OTHERS_LOT_DYN`）在该容器里都不会自动运行，需要按原有方式手动启动；
- 这解释了 `sync_ts:bili_proxy` 长期停在 4 月：整点重建已经几个月没跑过，
  zset 只靠增量事件维系，成员数才涨到 133 万；
- 本次 `refresh_proxy_zset()` 的僵尸过滤是手动触发一次生效的；此后新僵尸会在
  `redis_update_proxy`（`status != 0`）时即时从两个池摘掉，不依赖定时重建。

