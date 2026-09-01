# LLM 调用治理与 SQL 连接诊断增强 计划书

> 关联问题：日志中大量 `PrizeExtractBiliOpusQueue` 并发处理时，
> 出现两类错误：
> 1. LLM 抽奖判断失败：`429 RateLimitError` / `400 BadRequestError` / `1302 速率限制`
> 2. 数据库 `1040 Too many connections`（proxy_db 连接池被打满）
>
> 本文档记录两项修复性改动，不涉及新业务功能。

## 1. 报错信息增强：1040 连接数过多补充业务调用栈

**背景**：`Utils/通用/Common.py` 的 `handle_sql_operational_error` 当前仅打印
最底层 SQL helper 方法名（`AvailableProxySqlHelper.get_available_proxy_by_proxy_id` 等），
无法定位是哪个业务协程在高并发触发，难以判断根因。

**改动**：在 `1040` 分支增加调用栈输出（`traceback.format_stack()`），
打印触发该 SQL 操作的业务协程栈，便于定位高频调用方。

**影响范围**：仅日志增强，不改变重试/等待逻辑，属于可观测性修复。

## 2. 所有 LLM 调用共享一把全局锁

**背景**：抽奖判断等场景并发调用多个免费 LLM 实例，上游返回
`429 / 1302 您的账户已达到速率限制`，说明账户级并发配额被打满。
LangChain 自带的 `InMemoryRateLimiter` 是按单实例限流，无法在多个实例与多个
调用方之间做全局串行，仍会出现瞬时并发叠加。

**方案**：在集中调用子类 `Service/llm_service/tracked_llm.py` 的
`TrackedChatOpenAI` 上引入模块级 `asyncio.Lock`（所有实例共享），
在 `invoke` / `ainvoke` 实际发起上游请求前 `async with` 获取该锁。
这样任意时刻只有一个 LLM 请求真正打到上游，消除账户级并发超限。

**注意**：
- 锁为全局单实例，所有 `TrackedChatOpenAI` 实例共享，符合「所有 LLM 共享一个锁」要求。
- 仅在事件循环已运行（`asyncio.get_event_loop().is_running()`）时才使用异步锁；
  同步 `invoke` 路径在 throttling 场景下若无运行中的 loop 则退化为无锁，
  避免 `RuntimeError: no running event loop`。
- 锁仅包裹 `super().ainvoke/super().invoke` 的实际网络请求，统计 `record_start/success/failure`
  在锁外，不影响统计准确性。

**影响范围**：降低 LLM 上游并发，可能轻微增加抽奖判断延迟，但消除 429 失败重试开销。
