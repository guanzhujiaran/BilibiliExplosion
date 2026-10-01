# 会话状态 SSE 推送（前端需求）

> 对应后端：RPA-Browser —— 会话状态事件流。
> 关联计划书：`docs/rpa-会话状态SSE推送计划书.md`。
> 接口统一前缀：`/api/v1/rpa`（下文省略），会话相关接口挂在 `/browser/control` 下。

## 1. 背景

`LiveBox` 目前用 **20s 轮询** `POST /browser/control/status` 获取会话生命周期，
服务端主动触发的状态变化（闲置降级/挂起、进入宽限期、排队放行后启动完成、过期清理）
最坏要 20s 才能被前端看到。

后端新增一条 **SSE 事件流**，状态变化即时下发。前端把 `LiveBox` 的 20s 轮询
替换为 SSE 订阅；**排队轮询（`queue_status`，2s）保持不动**。

## 2. 新增接口：会话状态事件流

### `GET /browser/control/events?browser_id={browser_id}`

- 鉴权：与 `/browser/control/status` 一致（`mid` 走请求头，`browser_id` 走 query）。
- 响应：`text/event-stream`，长连接。
- 事件名固定 `session_status`，`data` 就是 `/browser/control/status` 的 `data` 全量快照
  （`BrowserSessionStatusData`），**字段与既有 `POST /status` 完全相同**，
  前端可直接复用现有的状态字段映射逻辑。

**建连首帧**：连接建立后服务端立即下发一帧当前快照（等价于一次 `/status`），
前端不需要在建连后再补一次 HTTP 请求。

**心跳**：无状态变化时每 15s 下发一行 SSE 注释（`:` 开头），前端**无需处理、不会触发事件回调**，
仅用于穿过网关空闲超时。

事件帧示例：

```
event: session_status
data: {"session_exists":true,"browser_running":true,"lifecycle_state":"active","idle_seconds":3,"is_pinned":false,"pending_termination_at":null,"in_launch_queue":false,"queue_state":null,"queue_type":null,"queue_position":null,"queue_waiting_seconds":0,...}

```

推送时机（快照变化才会推）：

| 变化 | 典型场景 |
| --- | --- |
| `session_exists: false → true` | 会话创建成功 / 排队放行后启动完成 |
| `session_exists: true → false` | 手动关闭 / 过期清理 |
| `status` / `lifecycle_state` 变化 | 闲置降级、挂起（`idle`）、恢复（`active`）、进入 `terminating` |
| `pending_termination_at` 变化 | 进入 / 退出关闭宽限期 |
| `is_pinned` 变化 | 自动化任务占用 / 释放 |

**不会推送**：`idle_seconds` 的逐秒增长（前端仍用本地 1s 时钟自行累加/倒计时）。

## 3. 前端交互要求

0. **连接归属在页面级（`BrowserStream`），不是 `LiveBox`**：
   页面模板是 `v-if 加载中 / v-else-if 排队面板 / v-else 含 LiveBox`，
   **排队期 `LiveBox` 尚未渲染**；连接若放在 `LiveBox`，排队期就没有通道，
   只能用 HTTP 轮询判断「启动完成」。故由页面持有唯一一条连接，
   覆盖排队期与直播期，`LiveBox` 通过 `inject` 消费同一份快照。
1. **建连**：进入直播页后建立 SSE 连接；收到 `session_status` 事件后，
   用原有字段映射更新会话生命周期、闲置时长、pin 状态、待关闭截止时间，
   并同时喂给会话状态机（驱动 `queued → connected`）。
2. **首帧即快照，且没有任何 HTTP 兜底**：订阅后不再调用 `/status`（首帧、排队循环、
   连接异常三处都不调）。通道可用性完全依赖客户端无限指数退避重连。
3. **监管只读模式（`readonly`）不订阅**：该接口是严格 owner 校验，
   管理员访问他人浏览器会 403，与现状一致（`AdminBrowserMonitorView` 不注入快照，走默认值）。
4. **断线重连**：客户端负责自动重连（指数退避），重连成功后以服务端首帧为准覆盖本地状态；
   页面卸载 / 组件销毁必须主动断开连接，避免连接泄漏。
5. **不得再起 `/status` 定时轮询**：SSE 与轮询不能同时存在，否则会出现双来源状态抖动。
6. **本地倒计时保留**：`pending_termination_at` 到达后的逐秒倒计时仍由前端本地时钟驱动。
7. **排队期只轮询 `/queue_status`（2s）**：排位与预计时长取决于其他用户的加入/放行，
   仍需轮询展示；但**其中的 `/status` 调用已删除** —— 「启动完成」改由 SSE 推送驱动。
   仅当 SSE 非 `open` 时，该循环才降级补一次 `/status`，避免连接断掉后卡死在排队面板。

## 4. 错误与边界

| 场景 | 期望表现 |
| --- | --- |
| 连接建立失败（网络/鉴权） | 不弹错误 toast（属于后台刷新）；头部显示「实时通道断开，重连中」，客户端自动重连 |
| 排队期间通道断开 | 排队进度仍由 `/queue_status` 展示；「启动完成」要等重连后的首帧，标识提示状态可能过期 |
| 连接中途断开 | 静默重连，不发提示；重连期间使用最后一次已知状态，并保留断开标识 |
| 收到非 `session_status` 事件 | 忽略（含心跳注释行） |
| `browser_id` 无效 / 无权限 | 连接被拒绝（非 2xx），按「建立失败」处理 |
