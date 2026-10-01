# be-bilibili-crawler LLM 不可用状态机计划书

> 目标：把现在「`disabled` 布尔 + `consecutive_failures` 计数」这种**只有两种状态**的粗粒度
> 熔断，细化为**按服务器返回的 HTTP 状态码 + 错误 code / 文案分类**的显式状态机，
> 让「不同类型的不可用」各自有正确的恢复方式：能自动恢复的不误删、需要等的按时间等、彻底坏掉的直接删。
>
> 状态：**实施中**（2026-09-27 起；2026-09-29 追加第 9 节「统计口径与观测性修正」，依据生产日志
> `be-bilibili-crawler-20260929102451.log`）
> 关联：
> - `Service/llm_service/tracked_llm.py`（实例统计 + 熔断判定，现状所在）
> - `Service/llm_service/pool.py`（实例池 / `get_all_free_llms` / `AllLLMsDisabledError`）
> - `Service/GetOthersLotDyn/parser/prize_extractor.py`（实际调用大模型的循环）
> - `Service/MQ/base/MQClient/PrizeExtract.py`（永不 nack 的消费流程）
> - `controller/common/CommonRouter.py`（`GET /llm/stats` 观测接口）
> - 前序计划书：`docs/be-bilibili-crawler-LLM槽位并行计划书.md`（槽位并发闸，已实施）
>
> **2026-10-01 修订**：`Service/llm_service/slot.py`（槽位租约）与进程内 `_SlotLockRegistry`
> 已整体移除，请求节流改由每个实例的 langchain `InMemoryRateLimiter` 承担 ——
> 详见 `be-bilibili-crawler-LLM槽位并行计划书.md` 第 0 节。本文件第 4/8/9 节中涉及
> `slot.py` / `get_llm_slots()` / `llm_slot_pool` 的描述同步作废，健康状态机本身的
> 设计与实现不受影响。

---

## 1. 现状与问题

### 1.1 现状（`tracked_llm.py`）

只有两个字段表达可用性：

```python
consecutive_failures: int      # 连续失败次数
disabled: bool                 # 是否熔断
disabled_reason: str | None

available = (not disabled) and consecutive_failures < MAX_CONSECUTIVE_FAILURES  # 3
```

判定逻辑：

```python
NON_RETRYABLE_STATUS_CODES = frozenset({400, 401, 403, 404})
status_code = _extract_status_code(error)
if status_code in NON_RETRYABLE_STATUS_CODES:
    disabled = True     # 永久熔断：只能重启 / 热更新配置
```

### 1.2 问题

| # | 问题 | 后果 |
|---|---|---|
| 1 | **429 限流和 401 鉴权失败被同等对待**（都不在 400/401/403/404 里就只累计次数；429 累计到 3 次后 `available=False`，但 3 秒后第二次调用就又试一遍） | 限流时反复撞墙，越撞越限流；没有「休息一会儿」的语义 |
| 2 | **完全没区分「今日额度耗尽」** | 额度用完当天，要么无意义地整夜重试（白打请求），要么被误判为永久故障 |
| 3 | **400 一律视为不可恢复** | 400 也可能是本次请求内容的问题（超长 / 审核 / 格式），误熔断一条好配置 |
| 4 | **`disabled` 只是内存标记，不删配置** | 池里长期挂着一堆死配置，`get_llm_slots()` 仍会构造它们，等待逻辑看不出「还会不会好」 |
| 5 | **无自动恢复时间概念** | `slot.py` 的「没有可用槽位」只能按固定指数退避（≤60s）盲等，不知道最近一个槽位什么时候会恢复 |
| 6 | **`insufficient_quota`（余额/额度耗尽）与 `rate_limit_exceeded`（限流）无法区分** | 欠费的 key 会被无限重试 |

---

## 2. 错误分类（优化后的分类）

服务器返回的错误按「**能否恢复 + 怎么恢复**」分成 7 类，判定依据是
**HTTP 状态码 + 响应体里的 `code` / `type` / `message` 文案 + `Retry-After` 头**：

| 类别 | `LLMFailureKind` | 判定依据 | 处置 |
|---|---|---|---|
| **可删除**（彻底不能用） | `PERMANENT` | `401` / `403` / `404` / **`410`**；或 code ∈ `{invalid_api_key, model_not_found, model_not_available, no_permission, account_deactivated}`；或 400 且 code 指向模型/配置问题；**或文案命中模型下线关键词（`end of life` / `no longer available` / `decommissioned` …，不限状态码）** | **直接从 `settings.llm_apis` 删除该配置**，状态终态 `REMOVED` |
| **需充值**（人工介入） | `SUSPENDED` | `402`；或 code ∈ `{insufficient_quota, billing_hard_limit_reached, quota_exceeded, insufficient_balance}`；或文案含 `balance / credit / billing / 余额 / 欠费 / 充值 / 账户` | 进入 `SUSPENDED`，冷却 **1h 起步、逐次翻倍、封顶 24h** 后自动试探；可被人工热更新或充值立即化解 |
| **等明天**（每日额度） | `QUOTA_EXHAUSTED` | `429` 且文案/code 含 `daily / today / per day / 每日 / 今日 / 当天 / rpd` | 进入 `QUOTA_WAIT`，**等到本地时间次日 00:00**（+60s 随机抖动）自动恢复 |
| **休息一会儿**（频率限流） | `RATE_LIMITED` | `429`（不含上面两种特征）；`Retry-After` 头优先 | 进入 `COOLING`，冷却取 `max(Retry-After, 60s × 2^(n-1))`，封顶 30min |
| **瞬时故障** | `TRANSIENT` | `5xx` / 超时 / 连接错误 / 其他非 HTTP 异常 | **连续 3 次**才进 `COOLING`（15s 起步、封顶 120s）；单次失败只计数不改状态。**显式 `Retry-After` 优先于封顶**：自算的退避有上限，但上游明确要求的等待时间不截断（`RATE_LIMITED` 同理） |
| **本次请求问题** | `REQUEST` | `400 / 413 / 422` 且 code 指向输入内容（`context_length_exceeded` 等） | 视为普通失败计数（**不立即删、不立即冷却**），连续 3 次仍会进 `COOLING`，避免坏配置白打请求 |
| **输出不合规** | `OUTPUT_INVALID` | 与 HTTP 无关：pydantic `ValidationError`（模型返回的 JSON 不符合结果模型）、langchain 解析抛出的 `OutputParserException` / 解析器内 `IndexError`（例如模型只回散文、无 tool call，解析器 `result[0]` 越界） | 同 `REQUEST`：只计数 + 连续 3 次进 `COOLING`。**不删配置**——这是「模型不擅长这个任务」，换模型即可；连续命中说明该模型不适合，短暂冷却避免一直被浪费 |

分类优先级（自上而下短路）：
`OUTPUT_INVALID` → `PERMANENT` → `SUSPENDED` → `QUOTA_EXHAUSTED` → `RATE_LIMITED` → `TRANSIENT` → `REQUEST`。

> `OUTPUT_INVALID` 排在最前：它只跟「模型返回的文本」有关，与 HTTP 状态码无关；
> 若先判状态码，解析类失败（无状态码）会被兜底成 `TRANSIENT`，把「模型不听话」
> 误当成「上游 5xx 抖动」来熔断。

> **相对需求原分类的优化**：
> 1. 把原「频率限流」拆成 **限流（休息一会儿）/ 每日额度（等明天）/ 余额不足（等充值）**——
>    三者在服务器上都是 429/402，只在 code 与文案上可区分，混在一起必然「要么全删、要么全等」；
> 2. 新增 **瞬时故障** 与 **请求内容问题** 两类**不误伤槽位**的错误——
>    5xx 抖动、内容超长不应该把一个健康 key 停掉；
> 3. `400` 从「一律删除」改为「按 code 细分」：只有明确指向模型/配置的才删，指向输入的只计数。

---

## 3. 状态机设计

### 3.1 状态

```python
class LLMState(StrEnumAutoDoc):
    HEALTHY     = "healthy"      # 正常，可调用
    COOLING     = "cooling"      # 短暂冷却（限流 / 连续瞬时失败），到点自动恢复
    QUOTA_WAIT  = "quota_wait"   # 今日额度耗尽，等到次日 0 点自动恢复
    SUSPENDED   = "suspended"    # 欠费 / 余额不足，长时间冷却，充值或人工热更新可立即恢复
    REMOVED     = "removed"      # 不可恢复，配置已删除（终态）
```

### 3.2 迁移图

```
                        ┌──────────── 成功调用 ────────────┐
                        ▼                                  │
                    ┌────────┐                             │
        ┌──────────►│ HEALTHY │◄──────────┐                 │
        │           └────┬─────┘           │                 │
        │                │                 │                 │
        │   RATE_LIMITED │  │ TRANSIENT/REQUEST/OUTPUT_INVALID(×3)
        │                ▼  ▼               │                 │
        │           ┌────────────────┐      │                 │
        │           │    COOLING     │──────┘ 成功 / 冷却到点   │
        │           └────────────────┘                        │
        │                                                     │
        │  QUOTA_EXHAUSTED                                    │
        ├──────────► QUOTA_WAIT ──── 跨过次日 0 点 ────────────┤
        │                                                     │
        │  SUSPENDED（402 / insufficient_quota）               │
        ├──────────► SUSPENDED ── 冷却到点 / 人工热更新 ───────┤
        │                                                     │
        │  PERMANENT（401/403/404 / model_not_found）          │
        └──────────► REMOVED（终态，配置已删除，不再回到 HEALTHY）
```

要点：
- `REMOVED` 是**终态**：`record_success` 不会把它拉回来；配置已从 `settings.llm_apis` 删除。
- `COOLING / QUOTA_WAIT / SUSPENDED` 都带 `resume_at`（自动恢复的 unix 时间戳），
  **读取时惰性刷新**（`state` / `available` 属性访问时若已过期则自动回 `HEALTHY`），
  因此不需要后台定时器。
- `SUSPENDED` 冷却逐次翻倍（`1h → 2h → 4h …`，封顶 24h），避免欠费 key 被高频试探；
  任一时刻人工 `POST /llm/config` 热更新即可立即恢复（指纹变化 = 新槽位 = `HEALTHY`）。

### 3.3 数据模型（`Service/llm_service/health.py`，新增）

```python
class LLMFailureKind(StrEnumAutoDoc): ...      # 上一节的 6 类
class LLMState(StrEnumAutoDoc): ...            # 本节的 5 态

class LLMHealth(BaseModel):
    """单个槽位的健康状态机：只负责状态与迁移，不含调用统计口径。"""

    # state / reason / since / resume_at / escalation 均为 computed_field，
    # 背后是 PrivateAttr，读取时先做一次惰性刷新（过期的冷却自动回 HEALTHY）。
    state: LLMState
    reason: str | None
    resume_at: float | None          # 自动恢复时间戳；None 表示不会自动恢复
    state_since: float | None
    escalation: int                  # 同类故障的连续升级次数（用于冷却翻倍）
    failure_kind: LLMFailureKind | None

    def record_success(self) -> None: ...
    def record_failure(self, kind, *, consecutive_failures, retry_after=None) -> LLMState: ...
    def resume_delay(self) -> float | None: ...   # 距自动恢复还有多少秒
```

`classify_llm_failure(error: BaseException) -> LLMFailureKind`：纯函数，从异常的
`status_code` / `code` / `body` / `response.headers` / `__class__.__name__` 提取特征后分类。
关键词集合全部是模块级常量（`_PERMANENT_CODES` / `_SUSPENDED_CODES` / `_SUSPENDED_KEYWORDS` /
`_DAILY_KEYWORDS` / `_REQUEST_CODES`），方便按上游厂商差异调整。

### 3.4 常量

| 常量 | 值 | 说明 |
|---|---|---|
| `MAX_CONSECUTIVE_FAILURES` | 3 | 连续瞬时 / 请求类失败达到该值进入 `COOLING` |
| `COOLING_BASE_SECONDS` | 60 | 限流首次冷却 |
| `COOLING_MAX_SECONDS` | 1800 | 限流冷却上限（30min） |
| `TRANSIENT_COOLING_SECONDS` | 15 | 瞬时故障首次冷却 |
| `TRANSIENT_COOLING_MAX_SECONDS` | 120 | 瞬时故障冷却上限 |
| `SUSPENDED_BASE_SECONDS` | 3600 | 欠费首次停用（1h） |
| `SUSPENDED_MAX_SECONDS` | 86400 | 欠费停用上限（24h） |
| `QUOTA_RESET_JITTER_SECONDS` | 60 | 次日额度恢复后的随机抖动，避免整点惊群 |

---

## 4. 改动清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `Service/llm_service/health.py` | **新增**：`LLMFailureKind` / `LLMState` / `LLMHealth` 状态机 + `classify_llm_failure()` + 常量 |
| 2 | `Service/llm_service/tracked_llm.py` | `LLMUsageStats` 内嵌 `health: LLMHealth`；`record_failure` 改为「分类 → 迁移」；`available` / `disabled` / `disabled_reason` 语义对齐新状态；`slot_fingerprint` 增加失败回调 `on_state_change`（`PrivateAttr`，由 pool 注入） |
| 3 | `Service/llm_service/pool.py` | `get_all_free_llms()` 只返回 `HEALTHY` 实例；新增 `AllLLMsCoolingError`（带 `resume_at`）；新增 `remove_llm_by_fingerprint()`（删配置 + 同步摘除缓存实例，**保留其他实例的统计**，不整池重建）；`_build_free_llms` 注入状态变更回调（`REMOVED` → 删配置 + 告警；`SUSPENDED` / `QUOTA_WAIT` → 节流告警） |
| 4 | `Service/llm_service/slot.py` | `_enabled_slots()` 改用 `available`；「没有可用槽位」的等待时长取 `min(指数退避, 最近一个 resume_at)`，并区分「已删除 / 冷却中」两种日志文案 |
| 5 | `Service/llm_service/__init__.py` | 导出 `LLMState` / `LLMFailureKind` / `AllLLMsCoolingError` |
| 6 | `Service/GetOthersLotDyn/parser/prize_extractor.py` | `_do_extract`：锁定槽位不可用时按状态分支 —— `REMOVED` 抛 `AllLLMsDisabledError`、其余冷却态抛 `AllLLMsCoolingError`（让上层释放槽位换一个 / 等冷却）；非槽位路径捕获 `AllLLMsCoolingError` 后**睡到 `resume_at`** 再继续，不再走 10s 等比退避空转；告警文案同步更新 |
| 7 | `controller/common/CommonRouter.py` | 无需改动（`get_llm_stats()` 直接透出 `health` 与 `state`），仅在文档中说明响应新增字段 |

**明确不做**：
- 不做「已删除指纹」的持久化黑名单：配置的唯一事实来源是环境变量 / `POST /llm/config`，
  服务重启后从配置恢复是预期行为（运维应同步修掉环境变量里的坏配置）。
- 不引入后台定时器：冷却到期用「读取时惰性刷新」实现，避免多一份需要关停的生命周期。

---

## 5. 兼容与回退

- `TrackedChatOpenAI.disabled` / `.available` / `.stats.disabled` / `.stats.available` 名称保留：
  - `disabled` 语义收敛为「**已删除（`REMOVED`）**」——即当前所有 `not llm.disabled` 的过滤点
    （`pool.get_all_free_llms` / `slot._enabled_slots`）语义正确：删除的才彻底剔除，冷却的改由 `available` 过滤；
  - `available` 语义为「`state == HEALTHY`」。
- `AllLLMsDisabledError` 保留（全部被删除时抛出）；新增 `AllLLMsCoolingError`（全部在冷却中）。
  两者都是 `RuntimeError` 子类，因此既有的 `except RuntimeError` 兜底分支仍然有效。
- `extract_prize_info_for_biliopusdb` / `extract_prize_info_for_lotdata` 签名不变。
- `GET /llm/stats` 为**新增字段**（`health` / `state` / `resume_at`），不删旧字段，向后兼容。
- 回退：`git revert` 本次提交即可（`health.py` 为新增文件，其余为原地修改）。

---

## 6. 验证

1. `uv run pytest test/`（重点 `test_prize_extract_flow.py`：槽位 `acquire` / `release` 仍被替换，流程不受影响）；
2. 分类函数单测（新增）：构造带 `status_code` / `code` / `message` 的假异常，覆盖
   401 / 402 / 403 / 404 / 429(限流) / 429(每日额度) / 429(insufficient_quota) / 500 / 超时 / context_length_exceeded；
3. 状态机单测（新增）：`HEALTHY --429--> COOLING --到点--> HEALTHY`；
   `HEALTHY --401--> REMOVED`（终态）；`HEALTHY --每日额度--> QUOTA_WAIT`；
   `SUSPENDED` 冷却翻倍并封顶；
4. 手工：Mock 一个返回 401 的上游 → 日志出现「配置已删除」且 `GET /llm/config` 少一条；
   Mock 429 → `GET /llm/stats` 里该槽位 `state=cooling`、`resume_at` 有值，冷却到期后自动回 `healthy`。

---

## 7. 风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| 上游文案差异导致误分类 | 各厂商 429 的 `message` 措辞不同，关键词可能漏匹配 | 分类默认落到 `RATE_LIMITED`（最保守：只短暂冷却，不删配置）；关键词集合集中在常量里便于调整 |
| 误删配置 | `401/403/404` 被判为 `PERMANENT` 后配置被删，若是上游抖动误报 401 则丢了可用 key | 删除只影响运行时内存，**不写回环境变量**；重启即恢复；同时推送告警让运维确认 |
| 全部槽位同时进入 `QUOTA_WAIT` | 抽奖提取会整夜停摆（消息保持未确认，不丢，但不处理） | `QUOTA_WAIT` 状态下 `slot._wait_for_any_slot` 会按 `resume_at` 精确睡到次日 0 点，并推送一次告警提示补配置 |
| `remove_llm_by_fingerprint` 与遍历并发 | 删除发生在 `record_failure`（同步、无 await）中，删除用「整体替换列表」而非原地 mutate | 单线程事件循环内原子；`get_llm_slots()` 的长度校验会在不一致时返回空列表（按「没有可用槽位」处理） |

---

## 8. 消息确认超时预算（配套必做）

### 8.1 问题

RabbitMQ 有 `consumer_timeout`（broker 端配置，默认 **30 分钟 = 1800s**）：
消费者收到消息后在超时时限内没有 ack/nack，broker 会**强制关闭 channel 并把消息重投**。
对上层表现为「莫名重投 + 重复消费」，而且此时 channel 已被关闭，`msg.ack()` 也会失败。

而本服务的入库队列恰好是「刻意长时间不确认」的设计：

- 没有可用槽位 → `llm_slot_pool.acquire()` 本机**无限等待**；
- 槽位在冷却中（本次新增）→ 「今日额度」要等到**次日 0 点**、「欠费」最长 **24h**；
- 外层 `process_prize_extract` 的 `while True` **没有任何总时长上界**
  （`mq_consume_max_time=600s` 只约束单轮 `run_with_backoff`，不约束外层循环）。

结论：**在引入冷却状态前，长等待就已经会踩中 30 分钟上限**；引入 `QUOTA_WAIT` 后必然踩中。
必须补一层「主动在 broker 超时之前交还消息」的机制。

### 8.2 设计

每次投递（每个 `process_prize_extract` 调用）建一个 **`ConsumeBudget`**，
用「收到消息的时间戳」计算剩余预算，把**所有可能长时间阻塞的等待**按剩余预算截断；
预算耗尽时**主动 `nack(requeue=True)`**，把消息交还队列，由下一个消费者以新预算重新开始。

```
收到消息 → ConsumeBudget.start(ack_timeout - reserve)
  while True:
      if budget.expired():          # 预算耗尽
          释放锁（上一轮的 finally 已做） → nack(requeue=True) → return
      抢去重锁        wait = budget.bound(wait)      # 单次等待按预算截断
      抢槽位          acquire(max_wait=budget.remaining())
      提取/写库       run_with_backoff(max_time=budget.remaining())
```

关键取舍：

| 事项 | 取舍 |
|---|---|
| 为什么不用 `asyncio.wait_for` 硬超时 | 会在 await 中间抛出取消，可能打断「正在写库」的事务；改为**协作式**：只在安全的等待点检查预算 |
| 为什么不继续「永不 nack」 | 超过 `consumer_timeout` 时 broker 会强行 nack（channel 关闭、行为不可控）；**主动**在超时前 nack 至少是可控的、且能保证锁已释放 |
| 重投会不会重复消费 | 去重 redis 锁 + 写库前 `_already_stored` 复查 + 写库 upsert，重投副本要么「确认已有」直接 ack，要么重新处理；`nack` 发生在锁释放之后，不存在「重投副本撞上未释放的锁被 ack 丢弃」的窗口 |
| 为什么不在 `nack` 前长睡 | `nack(requeue=True)` 是立即重投；加一个 1~5s 抖动，避免同一批消息在同一刻集体重投形成热点 |
| 为什么不「发现等不起就立刻交还」 | `nack(requeue=True)` 不能带延迟：立刻交还 → 新投递又以新预算等 29 分钟 → 在「全部槽位冷却数小时」时退化成紧凑重投循环。改为**在预算内以 ≤60s 粒度等槽位恢复、等不到才交还**，天然把重投频率限制在每 ~29 分钟一次 |
| broker 端要不要一起调 | **决策：不调**（已确认「多投几次没事」）。保持 broker 默认 `consumer_timeout=1800s`，代码侧预算 `1800 - 60 = 1740s`，即每约 29 分钟重投一次；消息不丢，只是多几次投递。若将来想减少重投次数，同步调大 `consumer_timeout` 与 `mq_consume_ack_timeout`（如都设为 86400）即可 |

### 8.3 常量与配置

| 名称 | 位置 | 值 | 说明 |
|---|---|---|---|
| `mq_consume_ack_timeout` | `CONFIG.settings` | 1800.0 | 秒；与 broker `consumer_timeout` 对齐（默认 30 分钟） |
| `mq_consume_ack_reserve` | `CONFIG.settings` | 60.0 | 秒；留给「释放锁 + nack + 日志」的收尾余量，预算 = timeout - reserve |
| `CONSUME_REQUEUE_JITTER` | `consume_budget.py` | 5.0 | 秒；重投前的随机抖动上限，避免集体重投 |

### 8.4 改动清单（在第 4 节基础上追加）

| # | 文件 | 改动 |
|---|---|---|
| 9 | `Service/MQ/base/MQClient/consume_budget.py` | **新增**：`ConsumeBudget`（记录起始时间戳、剩余预算、按预算截断等待）+ `ConsumeBudgetExceeded` |
| 10 | `CONFIG.py` | 新增 `mq_consume_ack_timeout` / `mq_consume_ack_reserve` |
| 11 | `Service/MQ/base/MQClient/consume_backoff.py` | `BackoffConfig` 增加 `giveup`：`AllLLMsCoolingError` / `AllLLMsDisabledError` 立即放弃本轮（换槽位/等冷却），且这类「槽位不可用」不推送「MQ消费失败」告警；新增 `max_time_limit` 参数供上层用预算封顶 |
| 12 | `Service/llm_service/slot.py` | `acquire(max_wait)` 支持上界，超出抛 `LLMSlotWaitTimeout`（不再无限等）；`_wait_notify` / `_wait_for_any_slot` 同步按上界截断 |
| 13 | `Service/GetOthersLotDyn/parser/prize_extractor.py` | `_do_extract(max_wait)`：需要的冷却等待超过本轮预算时不睡掉预算，直接抛出交给上层重投 |
| 14 | `Service/MQ/base/MQClient/PrizeExtract.py` | 每轮投递建 `ConsumeBudget`；`_wait_own_lock` / `acquire` / `run_with_backoff` 全部按预算截断；预算耗尽或 `LLMSlotWaitTimeout` → 记录后 `nack(requeue=True)` |

> 「永不 nack」的表述据此修正为：**只在「本轮成功写库 / 确认库里已有」时 ack；只在「确认超时预算耗尽」时主动 nack 重投**（重投前锁已释放，幂等由去重锁 + upsert 保证）。

### 8.5 验证（追加）

1. 把 `mq_consume_ack_timeout` 临时设为 30s、`mq_consume_ack_reserve` 设为 5s，用一个必然不可用的槽位跑单条消息：
   应在 ~25s 内看到「预算耗尽，主动交还队列」的日志与 `nack(requeue=True)`，而不是被 broker 断连；
2. 模拟 429 限流 → 槽位进入 `cooling` → 消息在本轮预算内不再空转该槽位，直接交还重投；
3. 回归：正常路径（有可用槽位、一次成功）不受影响，仍在秒级 ack。

---

## 9. 统计口径与观测性修正（2026-09-29 追加）

### 9.1 依据

生产日志 `be-bilibili-crawler-20260929102451.log`（2026-09-27 11:44 ~ 2026-09-29 10:24，线上版本
`ca74d78`）暴露的问题：

| 现象 | 日志证据 | 后果 |
|---|---|---|
| **本地修复成功仍被记成失败** | `已本地修复后采用` **449** 次 | 解析类失败在 `TrackedChatOpenAI` 层记 `failure`，业务层修复后**没有回滚**；`consecutive_failures` 只增不减 ⇒ 只要累计 3 次「能修好的格式问题」，槽位就被判定不可用且**永不恢复**（`ca74d78` 没有冷却，只能靠一次真成功清零）。统计上 GLM-4.7-Flash 单模型 380 次失败、0 次成功 |
| **410 Gone 未被判为不可恢复** | `Error code: 410 ... has reached its end of life on 2026-09-21` **278** 次 | 410 不判定则永远只计数 ⇒ 每轮轮询都白跑一次 |
| **失败调用不计耗时 / token** | GLM 系列失败数百次，`total_elapsed_seconds` / `input_tokens` 全为 0 | 无法评估「白烧了多少配额、超时耗了多久」；`avg_latency_seconds` 系统性偏乐观 |
| **29 次限流被同一阈值打死** | `429` 共 **121** 次 | `ca74d78` 里 429 与其它错误共用同一个 `consecutive_failures` 阈值，连续 3 次限流 = 永久不可用 |
| **`CancelledError` 被记成失败** | 09-28 04:00:31 同一秒 6 个槽位 | 进程关闭 / 任务取消会污染统计并把健康槽位推向不可用 |
| **`IndexError` 无人处理** | kimi-k3 **5** 次（模型只回散文、无 tool call，解析器 `result[0]` 越界） | 既不在本地修复范围内（只认 `ValidationError`），也无法分类，纯浪费一次调用 |

### 9.2 改动

| # | 文件 | 改动 |
|---|---|---|
| 15 | `Service/llm_service/tracked_llm.py` | `LLMUsageStats.record_failure()` 增加 `elapsed_seconds` / `input_tokens` / `output_tokens` / `total_tokens` 入参，落到**失败桶**（`failed_*` 字段）；新增 `record_recovered()`：把「最近一次失败」纠正为一次成功（`success_count +1`、`failure_count -1`、连续失败清零、耗时与 token 从失败桶挪到成功桶、清 `last_error`、按成功重置健康状态）；新增 `recovered_count` 计数；新增全部口径 `total_all_elapsed_seconds` / `avg_latency_all_seconds` / `avg_tokens_per_call_all` |
| 16 | `Service/llm_service/tracked_llm.py` | `invoke` / `ainvoke` 的 `except BaseException` 改为 `except Exception`：`asyncio.CancelledError` / `KeyboardInterrupt` / `SystemExit` 不再计入失败统计（取消不是槽位的错）；失败分支补传 `elapsed_seconds`，并尽力从异常回溯里取回 token（见 9.3） |
| 17 | `Service/llm_service/health.py` | 新增 `LLMFailureKind.OUTPUT_INVALID` + `_is_output_invalid()`；`_PERMANENT_STATUS_CODES = {401,403,404,410}`；`_MODEL_MISSING_KEYWORDS` 扩展为「模型下线」关键词（不限状态码）；`TRANSIENT` 冷却也采纳 `Retry-After` |
| 18 | `Service/GetOthersLotDyn/parser/prize_extractor.py` | 本地修复成功、并在**统计层确实记过一次失败**时调用 `record_recovered()` 回滚该次失败；日志区分「修复采用（已回滚统计）」与「修复采用（统计层未记失败：解析发生在统计埋点之外）」 |
| 19 | `Service/llm_service/pool.py` | 槽位指纹口径统一：`_build_free_llms` 在 token 为空时填 `"not-needed"` 占位，而比对侧用 `cfg.token`，导致**空 token 配置两边指纹必然不等** ⇒ `remove_llm_by_fingerprint` 早退、配置删不掉，且进程内锁与 redis 租约 key 不一致（互斥失效）。改为 pool 内统一经 `_slot_fingerprint_of(cfg)` 计算 |

### 9.3 已知限制

- **失败调用的 token 只能尽力而为**：上游报错时没有响应体，拿不到 `usage`；只有「模型已返回、解析阶段失败」这类情况可以从异常回溯里回溯出 `AIMessage.usage_metadata`（best-effort，取不到就是 0）。
- **`OUTPUT_INVALID` 的处置与 `REQUEST` 对齐**（连续 3 次进 `COOLING`），不是「只计数不冷却」：完全不冷却会让「模型不擅长这个任务」的槽位被无限轮询（正是生产里 GLM 系列被反复白跑的原因）。

### 9.4 部署前必须确认（独立风险，不属于本计划书范围）

线上容器实际运行的 `langchain-openai` **与 `uv.lock` 锁定的 1.6.6 不是同一版本**：

- 线上日志里 1438 次解析失败全部是 `PydanticOutputFunctionsParser` 风格的
  `model_validate_json`（`Invalid JSON: expected value at line 1 column 1`），该调用点在
  `langchain-core 1.6.5` 里只存在于 `output_parsers/openai_functions.py`，**已不被
  `langchain_openai 1.6.6` 的 `with_structured_output` 使用**；
- 而 1.6.6 的默认 `method="json_schema"` 走 `_oai_structured_outputs_parser`，只认
  `additional_kwargs["parsed"]`（OpenAI 官方 Structured Outputs 才会填），非 OpenAI 上游
  一律抛 `ValueError: Structured Output response does not have a 'parsed' field`；
- 三天日志里该 `ValueError` **出现 0 次** ⇒ 线上不是 1.6.6。

因此：**按 `uv.lock` 重建镜像会让所有非 OpenAI 上游的结构化输出立刻全挂**，而且该异常抛在
`TrackedChatOpenAI` 之外，连 `/llm/stats` 都看不到失败。部署前必须先在
`prize_extractor._do_extract` 里**显式指定 `method`**（并确认目标上游支持 tool calling），
或改为「普通调用 + 本地解析」；本计划书不擅自决定该方法，需单独确认。

