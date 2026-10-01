# RPA 会话状态 SSE 推送计划书

> 关联：`docs/frontend_requirements/浏览器启动内存排队.md`（排队轮询）、
> `docs/be-message-统一计划书.md` §5.15（闲置三级软着陆）。
> 涉及仓库：`RPA-Browser`（主）、`Vue3FrontEndDemoExercise`（前端）、`be-gateway`（仅确认代理链路，无需改动）。
> 前端需求另见：`docs/frontend_requirements/会话状态SSE推送.md`。

## 1. 背景与结论

### 1.1 现状

RPA 直播界面（`Vue3FrontEndDemoExercise/src/views/rpa-browser/BrowserStream.vue`
+ `src/components/rpa-browser/LiveBox.vue`）目前用 HTTP 轮询获取会话状态：

| 轮询点 | 位置 | 间隔 | 说明 |
| --- | --- | --- | --- |
| 会话生命周期 | `LiveBox.vue:281-289` | 20s | 只读，不刷新活跃时间，不干扰闲置判定 |
| 启动排队进度 | `BrowserStream.vue:210/276-284` | 2s | 仅排队态运行，短时高频 |
| 会话状态（非轮询） | `BrowserStream.vue:334/476` | onMounted + 手动刷新 | — |

后端 RPA 的会话状态是**进程内内存态**（`LiveService._browser_sessions`，
`app/services/RPA_browser/session/live_service.py:64`），状态修改点集中在
`live_service.py` 的少数几处（`touch` / `_apply_idle_action` / 会话创建 / 释放）。

会话状态变化的真实来源有相当一部分是**服务端自己触发的**：
闲置降级 / 挂起 / 进入宽限期、后台排队启动完成、过期清理释放。
这些变化前端只能靠 20s 轮询感知，最坏有 20s 滞后。

### 1.2 结论

**引入 SSE（Server-Sent Events）单向推送**，替换 `LiveBox` 的 20s 生命周期轮询；
排队轮询（2s）保持不动。

理由：

1. **方向匹配**：会话状态是纯 server→client 单向数据，SSE 比 WebSocket 更贴合，
   且不需要握手协商、双向帧、连接保活协议。
2. **鉴权复用**：前端 hey-api 生成的 `client.sse.*` 是 **fetch 实现**（非 `EventSource`），
   会走 `onRequest` 拦截器注入 `x-bili-mid / x-bili-level / x-bili-role` 请求头，
   并携带 `credentials: 'include'`；网关侧 `bili_jwt` 是 HttpOnly Cookie 也会自动带上，
   鉴权链路与既有 POST 接口完全一致，**无需为 SSE 新开鉴权旁路**。
3. **零新依赖**：后端用 Starlette/FastAPI 的 `StreamingResponse` + 异步生成器
   （即 FastAPI 官方 "Custom Response - StreamingResponse" 教程写法），
   不需要引入 `sse-starlette`；前端复用已生成的 SSE 客户端核心。
4. **进程模型允许**：RPA 服务单进程单 worker（`main.py:81-87`
   `uvicorn.run` 未指定 `workers`），会话表与订阅者表都在同一进程内存，
   进程内事件总线即可完成广播，**不需要 Redis / MQ**。
5. **中间件安全**：既有 `ErrorStatusMiddleware` 只处理
   `content-type: application/json` 的响应（`bili_common/middlewares/error_status.py:68-69`），
   SSE 的 `text/event-stream` 会被原样透传，不会被缓冲/重写。

### 1.3 明确不做（本次范围外）

- **不改排队轮询（仅 `/queue_status`）**：排队**排位 / 预计时长**取决于其他用户的加入与放行，
  SSE 流里只有「我自己这份会话」的状态，做不成全局队列广播，收益不成比例，故仍以 2s 轮询
  `POST /browser/control/queue_status` 展示进度。
- **但排队期的 `/status` 轮询已移除**：`BrowserStream.loadLaunchQueue()` 原先每 2s 顺带调一次
  `/browser/control/status` 来判断「是否已启动完成」（放行后 `in_queue` 仍为 true，
  只能靠 `browser_running` 判断）。该信号现在由 SSE 推送承载，故改为
  **仅在 SSE 未就绪时降级补一次 HTTP**（否则连接断掉会卡死在排队面板）。
- **不用 WebSocket**：无需双向通道。
- **不做事件回放 / `Last-Event-ID` 续传**：状态是**全量快照**语义，
  断线重连后首帧即为当前最新状态，无需重放历史。
- **不推送 WebRTC 信令**：视频与其信令链路保持现状。

## 2. 接口设计

### 2.1 新增：会话状态事件流

`GET /api/v1/rpa/browser/control/events`（网关前缀 + RPA 内部前缀对齐，
见 `controller_base_path=/api/v1/rpa` + `RouterPrefix.BROWSER_CONTROL=/browser/control`）

- 鉴权：`Depends(get_auth_info_from_header)` + `Depends(verify_browser_ownership)`，
  与 `/browser/control/status` 完全一致（`browser_id` 走 query，`mid` 走请求头）。
- 响应：`text/event-stream`，`StreamingResponse`。
- 无需请求体；用 **GET**（SSE 语义、幂等、便于排障）。

**事件帧**

事件名固定为 `session_status`，`data` 为 `/browser/control/status` 的
`data` 全量快照（`BrowserSessionStatusData`），前端可直接复用同一套状态映射逻辑。

```
event: session_status
data: {"session_exists":true,"browser_running":true,"lifecycle_state":"active",...}

```

**建连首帧**：连接建立后立即下发一帧当前快照（等价于一次 `/status` 调用），
前端无需在建连后再补一次 HTTP 请求。

**心跳**：每 `heartbeat_interval`（默认 15s，见 `settings.browser_session_sse_heartbeat_interval`）
无状态变更时下发一行 SSE 注释行 `: keep-alive`，用于穿过网关的
`socket` 空闲超时（`be-gateway/ExpressServerEnd/app.js:83` 全站 `timeout("30s")`，
RPA 前缀在 `ProxyEndPort.js:66-68` 覆盖为 `180000`；心跳必须小于该值）。
注释行不产生 `data`，hey-api 客户端不会当作事件回调，前端无感。

**响应头**：`Cache-Control: no-cache`、`Connection: keep-alive`、
`X-Accel-Buffering: no`（若后续前面加 nginx，必须关闭响应缓冲，否则推送会被攒批）。

**OpenAPI 内容类型必须显式声明**：路由上声明
`response_class=StreamingResponse` + `responses={200: {"content": {"text/event-stream": {}}}}`。
否则 openapi.json 会把它记成 `application/json`，导致：

1. Swagger 文档描述错误；
2. hey-api 生成器依据 `operation.responses[*].mediaType === "text/event-stream"`
   判定是否生成 SSE 方法，未声明时会生成一个普通 `.get()` —— 它会读满整个响应体才返回，
   对长连接等于永久挂起。

### 2.2 推送时机（事件源）

状态快照只有在**快照签名发生变化**时才推送，签名取自稳定字段：

```
session_exists / browser_running / status / lifecycle_state /
is_pinned / pending_termination_at /
in_launch_queue / queue_state / queue_type / queue_position
```

**刻意排除 `idle_seconds` / `created_at` / `expires_at`** 等每请求都会变化的字段，
否则会退化成「每秒推送」，失去 SSE 的意义。
`pending_termination_at` 已进入签名，因此「进入宽限期」这一变化会立刻推送，
前端本地 1s 倒计时（`LiveBox.vue:244-249`）保持现状。

埋点位置（均在 `app/services/RPA_browser/session/live_service.py`）：

| 位置 | 触发场景 |
| --- | --- |
| `touch()` 末尾（~L124） | 操作/信令使会话回到 ACTIVE，解除挂起/降级 |
| `_apply_idle_action()` 末尾（~L321） | 闲置降级 / 挂起 / 恢复 |
| `_reuse_or_create_session_entry()` 复用分支（~L440、~L459） | 复用既有会话复位为 RUNNING/ACTIVE |
| `_reuse_or_create_session_entry()` 注册新会话后（~L494） | 会话建立（`session_exists: false → true`） |
| `release_browser_session()` 删除会话后（~L523） | 会话关闭 / 过期清理（`session_exists: true → false`），并清理签名缓存 |
| `create_browser_session()` 显式复位后（~L621） | 直创成功 |
| `_background_launch()` 启动完成后（~L695） | 排队放行后启动完成（`queued → running`） |

> `_check_session_cleanup()` 中「设置 / 清空 `terminate_scheduled_at`」的变化，
> 由紧随其后的 `_apply_idle_action()` 统一推送，无需单独埋点。

## 3. 后端改动（RPA-Browser）

### 3.1 新增 `app/services/RPA_browser/session/session_status_bus.py`

进程内会话状态广播 + SSE 帧生成，**不依赖 `live_service`（避免循环 import）**：

- `SessionStatusBus`：
  - `subscribe(mid, browser_id) -> asyncio.Queue[BrowserSessionStatusData]`
  - `unsubscribe(mid, browser_id, queue)`
  - `publish(mid, browser_id, status)`：线程安全（在事件循环内直接投递；
    若在非循环线程调用，用已绑定的 loop `call_soon_threadsafe` 投递）
  - 慢消费者策略：队列有界（如 32），满则丢最旧帧保最新帧
- `bind_loop(loop)`：在 `main.py` lifespan 中绑定事件循环
- `iter_session_status_events(mid, browser_id, initial, heartbeat_interval)`：
  async generator，产出 SSE 文本帧；`finally` 中反订阅（客户端断开即释放）
- 单例 `session_status_bus`

### 3.2 路由常量

`app/models/router/router_prefix.py` → `BrowserSessionRouterPath` 增加：

```python
events = "/events"  # 会话状态 SSE 事件流
```

### 3.3 路由端点

`app/controller/v1/browser_control/session/router.py` 增加
`browser_session_events`（GET），返回 `StreamingResponse`，
**不声明 `response_model`**（流式响应与 `StandardResponse` envelope 互斥，
见 FastAPI 官方 StreamingResponse 教程）。

### 3.4 配置

`app/config.py` 增加：

| 配置项 | 默认 | 说明 |
| --- | --- | --- |
| `browser_session_sse_heartbeat_interval` | `15` | SSE 心跳间隔（秒），须小于网关 180s 空闲超时 |

### 3.5 生命周期

`main.py` lifespan 中 `session_status_bus.bind_loop(asyncio.get_running_loop())`。
订阅者表随连接增删，进程退出自然释放；无需额外清理任务。

## 4. 前端改动（Vue3FrontEndDemoExercise）

### 4.1 新增 `src/composables/useBrowserSessionEvents.ts`

- 入参：`browserId`、`onStatus(data)`、`disabled`（均为 getter，便于延迟取值）。
- 接入方式：重新生成 SDK 后得到的类型化 SSE 方法
  `浏览器会话控制Service.browserSessionEventsApiV1RpaBrowserControlEventsGet`
  （生成条件见 §2.1 的「OpenAPI 内容类型必须显式声明」）。不使用通用 `client.sse.*`，
  也不手写 URL 字符串。
- 带 `AbortController.signal`，`onSseEvent` 中过滤出 `session_status` 事件回调
  （心跳是 SSE 注释行，不带事件名，天然被过滤）。
- 断线重连：交给 hey-api SSE 客户端内置的指数退避重试
  （`core/serverSentEvents.gen.ts:224-235`，`sseMaxRetryAttempts` 不设即无限重试）。
- `onUnmounted` / `stop()` 时 `abort()`，避免连接泄漏。
- 暴露连接态（`idle / connecting / open`）供调用方做降级判断。

### 4.2 连接归属：页面级 `BrowserStream.vue`（**不是 LiveBox**）

关键点：**排队期 `LiveBox` 根本没渲染**。`BrowserStream` 的模板是
`v-if="isLoadingInfo"` / `v-else-if="isQueued"`(排队面板) / `v-else`(含 `LiveBox`)，
所以把 SSE 放在 `LiveBox` 里，排队期就没有连接可用 —— 这正是原先必须轮询 `/status` 的原因。

因此连接上移到页面：

- `BrowserStream` 持有唯一一条 SSE，挂载即订阅，覆盖**排队期 + 直播期**。
- `onSseEvent` 的 data 一份两用：① 喂给状态机 `onStatusResponse`（驱动 queued→connected）；
  ② 存进 `sessionLifecycleSnapshot` 并通过 `provide` 下发。
- **无 HTTP 兜底**：首屏、排队循环、连接异常三处都不再调用 `/status`；
  `onMounted` 只做 `loadBrowserInfo()` + `startSessionEvents()`。
- **失败可见**：因为没有第二来源，头部在连接非 `open` 时显示一个 warning 标签
  （`rpa.sessionEventsOffline`：「实时通道断开，重连中」），避免用户对着可能过期的状态界面猜。
- **手动刷新 = 重连**：头部「刷新会话状态」按钮改为 `startSessionEvents()`
  （重连后服务端立刻下发首帧），不再是 HTTP 查询。
- `onUnmounted` 时 `stop()`。

### 4.3 接入 `LiveBox.vue`（改为被动消费）

- 删除自身的 SSE 订阅、`loadSessionLifecycle()` HTTP 查询与 8s 兜底定时器；
  改为 `inject('sessionLifecycleSnapshot', ref(null))` + `watch(..., { immediate: true })`
  走原有字段映射（`lifecycle_state` / `idle_seconds` / `is_pinned` / `pending_termination_at`）。
- 本地 1s 倒计时时钟（`pending_termination_at`）保留。
- 「一键恢复/续命」后不再手动刷新：后端 `ensure_webrtc_session` 内部会 `touch()`，
  由 SSE 自动推送新的生命周期。
- 监管只读页 `AdminBrowserMonitorView.vue` 不注入快照 → 走 `ref(null)` 默认值，
  行为与原本「readonly 不订阅」一致（该接口是严格 owner 校验，管理员访问他人浏览器会 403）。

## 5. 兼容性与影响面

| 项 | 影响 |
| --- | --- |
| 既有 HTTP 接口 | 无改动，`/status` 仍可用（作为兜底与首帧等价物） |
| 前端轮询流量 | `LiveBox` 20s 轮询、排队期 2s `/status` 轮询均消失；单连接常驻，心跳 15s 一行注释；排队期仅剩 2s `/queue_status` |
| 连接数 | 每个打开的直播页 1 条 SSE；同用户多标签各自一条（可接受） |
| 网关 | 无需改动（`/api/v1/rpa` 已配置代理与 180s 空闲超时） |
| 多实例部署 | **当前不支持**：事件总线是进程内。若未来多 worker/多副本，需引入 Redis pub/sub 广播，本计划书预留 `SessionStatusBus` 抽象层以便替换 |

## 6. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 代理/中间件缓冲导致推送不实时 | 响应头 `X-Accel-Buffering: no`；`ErrorStatusMiddleware` 只处理 JSON 已确认不缓冲 |
| 连接空闲被网关掐断 | 15s 心跳 < 180s 空闲超时 |
| 高频事件刷屏 | 快照签名去重，排除 `idle_seconds` 等易变字段 |
| 客户端断开后订阅残留 | generator `finally` 反订阅；队列有界 |
| 前端拿不到 `x-bili-mid` | 生成的 SSE 方法走 `onRequest` 拦截器注入，与 POST 接口一致 |
| **通道不可用时状态没有第二来源**（纯 SSE 架构的固有代价） | 客户端内置无限指数退避重连；头部 `rpa.sessionEventsOffline` 标识把「断开 / 重连中」暴露出来，让可能过期的状态是**可见的**，而不是伪装成正常 |
| mDNS host 候选解析失败刷 ERROR | 已改为跳过 + WARNING，仅在 ICE 真的 `failed` 时按计数给出针对性提示（见 `stream_session.add_ice_candidate`） |

## 7. 验收要点

1. 打开直播页（含**启动排队期**），浏览器网络面板可见一条 `text/event-stream` 常驻请求，
   且无任何周期的 `/status` 轮询（排队期只应看到 2s 的 `/queue_status`）。
2. 手动触发闲置挂起（或等待宽限期），状态变化在 **1s 内**到达前端，
   倒计时与挂起样式同步更新。
3. 排队态 → 后台启动完成，`session_exists` / `browser_running` 变化即时到达。
4. 杀掉 RPA 进程再重启，前端在重连后自动恢复推送（无需刷新页面）。
5. 页面卸载后，后端订阅者表回到空（`SessionStatusBus` 无残留 key）。
