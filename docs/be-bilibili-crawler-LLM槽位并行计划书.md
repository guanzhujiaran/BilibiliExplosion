# be-bilibili-crawler LLM 槽位并行（per-slot 1 并发）计划书

> 目标：把 LLM 并发闸从「全局计数信号量（N 个名额）」改为「每个 (base_url, model_name, token)
> 槽位各 1 并发」——同一 key 跨进程互斥、不同 key 真正并行，让 N 条 LLM 配置的吞吐从 ≈1 恢复到 ×N；
> 同时把消费侧的 ack/nack 语义收敛为「**只有真正完成才 ack，否则本机退避重试，永不 nack**」，
> 消除现有「重新入队」路径的丢数据窗口。
> 状态：**已实施**（2026-09-27）；第 4 节改动清单全部落地，测试见第 6 节
> 关联：
> - `Service/MQ/base/MQClient/PrizeExtract.py`（并发闸与消费流程所在）
> - `Service/MQ/base/MQClient/base.py`、`Models/MQ/BaseMQModel.py`（订阅参数 / prefetch）
> - `Service/llm_service/tracked_llm.py`（进程内调用锁）
> - `Service/llm_service/pool.py`（实例池）
> - `Service/GetOthersLotDyn/parser/prize_extractor.py`（实际调用大模型的循环）

---

## 0. 修订（2026-10-01）：槽位锁已整体移除，改用 langchain rate limiter

> 本节覆盖第 3～7 节的并发控制设计；被移除的是「加锁」这件事，**a/b 节之前的
> 健康状态机、去重锁、ack/nack 语义、ConsumeBudget 预算等设计与实现保持不变**。

**决定**：不再自己实现「同一槽位同时最多 1 个在途请求」的互斥，请求节流全部交给
langchain 的 `InMemoryRateLimiter`（每个实例一个，已在 `pool.py` 构建时挂上）。

**删除内容**：

| 文件 | 改动 |
|---|---|
| `Service/llm_service/tracked_llm.py` | 删除进程内 `_SlotLockRegistry` / `_slot_locks`；`invoke` / `ainvoke` 不再加锁，仅保留统计与健康状态机 |
| `Service/llm_service/slot.py` | **删除**：`LLMSlotLease` / `LLMSlotPool` / `llm_slot_pool`（redis 租约 + 心跳 + BLPOP 等待） |
| `Service/llm_service/pool.py` | 删除仅为租约池服务的 `LLMSlot` / `get_llm_slots()`（已无调用方） |
| `Service/llm_service/__init__.py` | 移除上述符号的导入与导出 |
| `Service/MQ/base/MQClient/PrizeExtract.py` | 去掉「抢槽位 → 用该槽位」流程；`_do_extract_and_store` 不再接收 lease，直接调用 `extract_prize_info_for_*`（不传 `chat_openai_client`，由 `prize_extractor` 内部 `get_all_free_llms()` 轮询逐个尝试） |
| `test/test_prize_extract_flow.py` | 移除租约桩与 `llm_slot_pool` patch；原「等槽位超预算」用例改为「`_consume_once` 主动报告预算耗尽」 |

**新的并发/限流语义**：

- 每个 `TrackedChatOpenAI` 实例自带一个 `InMemoryRateLimiter(requests_per_second=cfg.requests_per_second, check_every_n_seconds=0.1, max_bucket_size=1)`：
  `invoke` / `ainvoke` 前自动取令牌，超速时阻塞等待（`max_bucket_size=1` ⇒ 无突发，等效于按速率串行）；
- 多实例之间互不阻塞，天然并行；
- **不再有跨进程互斥**：多消费者实例可能同时打同一条配置，节流由两侧各自的
  rate limiter 兜底（如需严格跨进程控制需另行引入分布式限流，本次不做）；
- MQ 消费者的「选哪条 LLM」改为 `get_all_free_llms()`（健康检查 + 轮转）逐个尝试，
  全失败时由 `prize_extractor` 内部的等比退避继续重试。

---

## 1. 背景与现状

### 1.1 现有链路

```
PrizeExtract.process_prize_extract
  1. redis 去重锁          抢不到 → ack 丢弃
  2. 查库是否已有提取结果   有 → ack 结束
  3. 全局 redis 信号量（名额 = len(settings.llm_apis)）
       抢不到 → 重新发布到队尾 + ack           ← 第一条丢数据路径
  4. run_with_backoff(_do_extract_and_store)
       → prize_extractor._do_extract
            → get_all_free_llms() 拿全部实例 → for 逐个试 → 全失败则等比退避无限重试
       异常且重试耗尽 → nack(requeue=True)      ← 第二条丢数据路径
```

### 1.2 四个问题

1. **信号量粒度不对**：`_max_concurrency()` 是全局计数，只保证「总数 ≤ N」，**不保证同一条配置不被并发使用**。下游 `_do_extract` 是「遍历实例列表逐个试」，两个并发任务很容易同时选中同一条配置 → 同一个 apikey 被打多份并发。

2. **进程内还有一把全局锁，把多配置并行彻底抹平**：

   ```python
   # Service/llm_service/tracked_llm.py
   _LLM_GLOBAL_LOCK = asyncio.Lock()   # 所有 TrackedChatOpenAI 实例共用

   async def ainvoke(...):
       async with _LLM_GLOBAL_LOCK:    # 任意时刻只有 1 个请求打到上游
   ```
   配置再多也只有 1 个在途请求；redis 信号量放进来的 N 个任务里有 N-1 个卡在这把锁上排队，同时还各自占着 redis 名额与未 ack 的 MQ 消息。

3. **现有 ack/nack 路径存在丢数据窗口**（本次一并修）：

   | 路径 | 竞态 |
   |---|---|
   | 「并发已满 → `pub_prize_extract` 重发 + `msg.ack()`」 | 重发的副本可能在**原副本仍持有去重锁**（`finally` 还没执行）时被消费 → 命中「正在查询/处理中，跳过」→ **ack 丢弃**；若原副本随后也失败，这条消息就没人处理了 |
   | 「异常 → `msg.nack(requeue=True)`」后 `finally` 才释放锁 | RabbitMQ 立即重投，重投副本同样可能撞上未释放的锁 → 被「跳过」分支 ack 丢弃 |

   根因：**「抢不到去重锁 / 抢不到槽位」这类「本次没干成任何事」的分支也在 ack**。

4. **两层重试叠加**：`_do_extract` 内有「全失败 → 等比退避（10s→20s→…→600s）无限重试」，外层 `run_with_backoff` 又有一层指数退避；内层无限重试还会让任务长期占住并发名额。

### 1.3 本次要落地的目标语义

- 同一 `(base_url, model_name, token)` 同时最多 **1 个在途请求**，**跨进程也成立**（未来多实例部署安全）；
- 不同槽位可并行 → N 条配置真正并行（吞吐 ×N）；
- **没有可用槽位时在本机退避等待**（等运维通过 `POST /llm/config` 补一条可用配置），**不 nack、不重新入队**；
- **消费侧 ack/nack 收敛**：只有「确认库里已有 / 本轮成功写库」才 ack，其余情况一律保持消息未确认、本机继续重试（进程崩溃时由 broker 重投未确认消息），从根上消除 1.2-3 的两个丢数据窗口。

---

## 2. 方案选型

| 方案 | 做法 | 结论 |
|---|---|---|
| A | redis 层用一把**全局**租约锁（跨进程总 1 并发） | 与 `_LLM_GLOBAL_LOCK` 意图一致，但多配置依旧用不上并行，吞吐仍 ≈1，弃 |
| **B** | **每槽位 1 并发**：进程内 `_LLM_GLOBAL_LOCK` → 每槽位一把 asyncio.Lock；跨进程 redis 每槽位一把租约锁 | **选它**。语义与「同一 key 1 并发」精确对应，N 条配置真正并行 |
| C | 保留全局串行现状，只把 redis 信号量换成 per-槽位租约 | 单实例下 per-槽位锁被 `_LLM_GLOBAL_LOCK` 完全掩盖，收益为 0，弃 |

选 B 的代价（已确认接受）：上游从「总 1 并发」变成「每 key 1 并发」，靠各槽位的 `requests_per_second` 继续兜底。

---

## 3. 设计

### 3.1 槽位与指纹

**槽位 = `settings.llm_apis` 里的每一条 `LLMApiConfig`**，身份用指纹表示：

```python
slot_fingerprint(base_url, model_name, token) -> str
    = sha256(f"{base_url}|{model_name}|{token}").hexdigest()[:16]
```

- 用 sha256 而非明文拼接：apikey **不落明文**到 redis key / 日志 / 报错里；
- 改 token / model / base_url → 指纹变化 → 视为新槽位，旧槽位的锁随 TTL 自然释放。

### 3.2 进程内：每槽位一把 `asyncio.Lock`

`tracked_llm.py`：

- 新增 `slot_fingerprint()` + `TrackedChatOpenAI.slot_fingerprint`（由 `openai_api_base` / `model_name` / `openai_api_key` 计算）；
- `_LLM_GLOBAL_LOCK` 替换为「按指纹取锁的注册表」（小类封装 `{fingerprint: asyncio.Lock}`，不用裸 dict）：
  同一槽位串行、不同槽位互不阻塞；
- `ainvoke` 改成 `async with registry.lock_for(self.slot_fingerprint)`，统计逻辑不动。

### 3.3 跨进程：redis 槽位租约（复用 redis-py `Lock`）

不再自研 zset/Lua 计数，直接用 `redis.asyncio.lock.Lock`：

| 项 | 做法 | 理由 |
|---|---|---|
| key | `llm_slot:lock:{fingerprint}` | 每槽位一把锁，并发上限天然为 1，正好是 `Lock` 的语义 |
| 构造 | `Lock(client, name=key, timeout=SLOT_LEASE_TTL, thread_local=False, raise_on_release_error=False)` | `thread_local=False`：同一事件循环里 thread-local 被所有任务共享，必须按租约一实例；`raise_on_release_error=False`：租约被回收后再释放不抛错（幂等） |
| 获取 | `await lock.acquire(blocking=False)` | 非阻塞尝试；等待交给 BLPOP 通知（`blocking=True` 是 0.1s sleep 轮询，不用） |
| 续约 | 心跳每 `SLOT_LEASE_TTL/3` 秒 `await lock.extend(SLOT_LEASE_TTL, replace_ttl=True)` | 处理耗时超过租约也不会被回收；`LockNotOwnedError` → 名额已丢，记日志并停止心跳 |
| 释放 | `await lock.release()` | Lua 比对 token 才删，不会误删他人的锁 |
| 崩溃自愈 | `timeout`(PX) 到期自动释放 | 进程被 kill 时心跳消失，锁自动回收 |
| 连接 | 租约期间持有一个 `redis_client_factory(pool=...)` 客户端，`release` 后关闭 | 池上限 4096、槽位数为个位数，占用可忽略 |
| redis 实例 | 沿用 `CONFIG.database.getOtherLotRedis` | 与 MQ 流程同一个 redis，少一个配置面 |

### 3.4 抢槽位与等待（`LLMSlotPool.acquire`）

```
可用槽位 = get_llm_slots() 中「实例存在且未熔断」的槽位

若没有可用槽位（未配置 / 全熔断）：
    ← 不返回、不抛到外层：在本机按指数退避（上限 SLOT_WAIT_MAX_BACKOFF）无限等待，
      直到运维通过 POST /llm/config 加回一条可用配置为止（消息始终未确认 → 不丢）
有可用槽位：
    shuffle(可用槽位)                     # 随机顺序，避免所有实例都抢列表第一条
    for slot in shuffled: 抢到其锁 → 启动心跳 → 返回 lease
    全忙 → BLPOP(所有可用槽位的 notify key, timeout=min(5, 剩余))    # 事件驱动，零轮询
             被唤醒/超时后重新尝试，整体持续等待直到拿到或「可用槽位集合发生变化」
```

- 每次 `NoAvailableLLMSlot` / 抢不到都按 `bili_common.core.backoff` 的指数等待 + 抖动退避，并在**首次**和**每 N 分钟**推一次告警（沿用 `_push_all_llms_disabled_error` 的思路，避免刷屏）；
- 释放槽位时 `LPUSH notify 1` + `LTRIM 0 SLOT_NOTIFY_BACKLOG-1`；
- `BLPOP` 多 key 返回 `(key, value)`，天然知道哪个槽位空出来了；
- 单次 `BLPOP` 上限 5s：兜底漏唤醒，且不超 `socket_timeout=10`。

### 3.5 调用链、重试与故障转移

`process_prize_extract` 改为「单轮封装 + 外层无限循环」，**ack 只出现在成功路径**：

```python
while True:                                  # 外层：永不 nack，本轮没成就在本机继续
    try:
        await _consume_once(params, mq_props, msg)   # 抢锁 → 查库 → 抢槽位 → 提取写库 → ack
        return result
    except Exception:
        # 本机退避后继续下一轮（消息保持未确认；进程崩溃时 broker 会重投）
```

`_consume_once` 内部：

| 步骤 | 行为 |
|---|---|
| 1. 抢去重锁 | 抢不到（另一副本在处理）→ **不 ack**，短退避后重试抢锁（副本的正确归宿是「处理」或「确认库已有」，不是「什么都不做就丢」） |
| 2. 查库已有提取结果 | **ack**（数据确实已在库，消息使命完成）|
| 3. 抢槽位 | 见 3.4；期间消息始终未确认 |
| 4. 提取 + 写库 | `run_with_backoff(_do_extract_and_store(params, lease))`，沿用现有「指数等待 + 抖动」与 `mq_consume_*` 上限；每轮耗尽仍推告警 |
| 5. 成功 | **ack** |
| finally | 释放槽位租约（沿用现有 shield 托管 + 强引用的取消安全释放）|

**故障转移粒度**：锁定槽位后不能在单次调用里换 provider，因此改为「消息级重试换槽位」：

1. `prize_extractor._do_extract` 只加一处判断——指定的 `chat_openai_client` 已 `disabled`（熔断）时抛 `AllLLMsDisabledError`，不再对已熔断的槽位做无限退避；
2. 抛出 → 释放该槽位 → 回到步骤 3 重新抢槽位（可用列表已剔除熔断槽位）→ 自然换到别的槽位；若此时全部熔断 → 回到 3.4 的「无限等待配置恢复」；
3. 未熔断但临时失败（429 / 超时等）仍按现有等比退避重试**同一个**槽位——重试不应增加并发。

`PrizeExtract` 里 `_do_extract_and_store` 通过**已有的** `chat_openai_client` 参数把槽位实例透传给 `extract_prize_info_for_*`
（`_do_extract` 内部已有 `if chat_openai_client: all_llms = [chat_openai_client]`，天然就是「锁定哪个槽位就用哪个」），**公开签名不变**。

### 3.6 配套：用 prefetch 限制「在途未确认消息数」

3.4/3.5 让消息在等待期间保持未确认，必须给这两条队列加**消费者预取上限**，否则 broker 会把整条队列的积压全部推成未确认消息（未确认消息驻留 broker 内存）：

- `MQPropBase` 增加 `prefetch_count: int | None = None`；
- `BaseFastStreamMQ.sub_params` 在该字段非空时附加 `channel=Channel(prefetch_count=..., global_qos=True)`；
- 只给 `PrizeExtractBiliOpusQueue` / `PrizeExtractDynDetailQueue` 两个 prop 设值：
  `prefetch_count = max(8, len(settings.llm_apis) * 2)`（导入时按当时的配置计算），
  保证「在途消息数 ≥ 槽位数」让槽位不空转，同时把堆积挡在 broker 侧。

### 3.7 常量（已实施）

| 常量 | 位置 | 值 | 说明 |
|---|---|---|---|
| `SLOT_LEASE_TTL` | `slot.py` | 600 | 秒；单槽位租约时长，心跳停止后到期自动回收 |
| `SLOT_HEARTBEAT_INTERVAL` | `slot.py` | `SLOT_LEASE_TTL / 3` | 秒；心跳续约间隔 |
| `SLOT_NOTIFY_BLPOP_TIMEOUT` | `slot.py` | 5 | 秒；单次 BLPOP 阻塞上限（< `socket_timeout=10`） |
| `SLOT_NOTIFY_BACKLOG` | `slot.py` | 64 | 唤醒令牌堆积上限 |
| `SLOT_WAIT_MAX_BACKOFF` | `slot.py` | 60 | 秒；「没有可用槽位」时本机退避的等待上限 |
| `SLOT_ALERT_INTERVAL` | `slot.py` | 600 | 秒；「没有可用槽位」告警的推送间隔（同因告警靠 message-service 聚合） |
| `LOCK_TTL` | `PrizeExtract.py` | 600 | 秒；去重锁兜底过期 |
| `LOCK_RETRY_MAX_BACKOFF` / `LOCK_RETRY_MIN_WAIT` | `PrizeExtract.py` | 30 / 1 | 秒；抢不到去重锁时的退避上下限 |

`llm_slot_pool.acquire()` **不设总超时**：槽位全忙或没有可用槽位都在本机等（消息保持未确认），
因此不再需要 `SLOT_WAIT_TIMEOUT` 这类常量，也不再有「抢不到就重新入队」的分支。

删除：`SEM_KEY` / `SEM_LEASE_TTL` / `SEM_ACQUIRE_TIMEOUT` / `SEM_NOTIFY_BLPOP_TIMEOUT` / `SEM_NOTIFY_BACKLOG` / `_max_concurrency()` / `BiliLotDataPublisher.pub_prize_extract` 的消费侧重入队调用。

---

## 4. 改动清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `Service/llm_service/tracked_llm.py` | 新增 `slot_fingerprint()` 与 `TrackedChatOpenAI.slot_fingerprint`；`_LLM_GLOBAL_LOCK` → 按槽位取锁的注册表；`ainvoke` 改用槽位锁 |
| 2 | `Service/llm_service/slot.py` | **新增**：`LLMSlot`、`LLMSlotLease`、`LLMSlotPool`（redis 租约 + 心跳 + BLPOP 等待 + 无可用槽位时无限退避） |
| 3 | `Service/llm_service/pool.py` | 新增 `get_llm_slots() -> list[LLMSlot]`（`settings.llm_apis` 与实例一一对应，熔断实例为 `None`） |
| 4 | `Service/llm_service/__init__.py` | 导出 `get_llm_slots` / `LLMSlotPool` |
| 5 | `Service/GetOthersLotDyn/parser/prize_extractor.py` | `_do_extract`：指定的 `chat_openai_client` 已熔断 → 抛 `AllLLMsDisabledError` |
| 6 | `Service/MQ/base/MQClient/PrizeExtract.py` | 删自研 zset 信号量 → 改用 `LLMSlotPool`；消费流程改为「单轮封装 + 外层无限循环」；ack 只保留成功/已存在两种；去掉 `pub_prize_extract` 重新入队与 `nack` 路径；常量替换 |
| 7 | `Models/MQ/BaseMQModel.py` | `MQPropBase` 增加 `prefetch_count: int \| None` |
| 8 | `Service/MQ/base/MQClient/base.py` | `sub_params` 支持 `channel=Channel(prefetch_count=...)`；两条入库队列的 prop 设值 |
| 9 | `test/test_prize_extract_flow.py` | patch 点由 `acquire_semaphore_blocking` / `release_semaphore` 改为槽位池的 `acquire` / `release`；补「抢不到锁 / 无可用槽位时不 ack」的用例 |

---

## 5. 兼容与回退

- `extract_prize_info_for_biliopusdb` / `extract_prize_info_for_lotdata` 签名**不变**（继续用可选的 `chat_openai_client`），
  `scripts/database/backfill_*`、`scripts/judge_grand_prize` 等调用方零改动；
- `LLMSlotPool` 只被 `PrizeExtract` 使用，其他入口（脚本、接口）不经过槽位闸，行为与现在一致；
- `consume_with_backoff` / `_requeue` 保持原样（其他队列仍在用），只是这两条队列不再走 nack；
- 回退：`git revert` 本次提交即可。

---

## 6. 验证

1. `uv run pytest test/test_prize_extract_flow.py`（现有 18 项 + 新增用例）；
2. 手工（本地 redis）：
   - 并发 2 个任务、配置 1 个槽位 → `llm_slot:lock:*` 同一时刻只有 1 个成员，另一个在等待；
   - 运行超过 `SLOT_LEASE_TTL` → 心跳 `extend` 生效，锁不被他人抢走；
   - `kill -9` 消费者 → 锁在 TTL 后能被重新抢到；
   - 清空 `llm_apis` → 消息既不 ack 也不 nack，日志按退避重试；`POST /llm/config` 加回配置后自动继续处理；
3. 回归：确认 `requests_per_second` 仍按槽位生效（`InMemoryRateLimiter`）。

---

## 7. 风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| 上游并发翻倍 | 从「总 1 并发」变为「每 key 1 并发」 | 每槽位仍有 `requests_per_second` 限流；必要时下调该值 |
| 故障转移变慢 | 指定槽位在熔断（`MAX_CONSECUTIVE_FAILURES` 次连续失败）前会一直重试该槽位 | 熔断即抛出 → 重新抢槽位 |
| 未确认消息堆积 | 「本机等待」期间消息保持未确认 | 3.6 的 prefetch 上限；进程崩溃时 broker 重投，不丢 |
| 心跳期间持连接 | 租约期间占用一个 redis 连接 | 槽位数为个位数，池上限 4096 |
| 重复副本会多跑一次 | 去重锁抢不到的副本会等锁释放后重试，若届时库里仍无结果则会重复提取 | 写库是 upsert（幂等）；重复率由去重锁压低 |
| 配置热更新 | 改 token 后指纹变化，新槽位从零开始（旧锁自然到期） | 属预期行为，文档说明 |
