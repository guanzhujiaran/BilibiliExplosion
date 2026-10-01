# RPA 多观看者并发直播计划书

> 关联：`docs/rpa-会话状态SSE推送计划书.md`（会话状态推送）、
> `docs/be-message-统一计划书.md` §5.15（闲置三级软着陆）、§5.16（帧生产性能）、§5.18（清晰度/暂停）。
> 涉及仓库：`RPA-Browser`（主）、`Vue3FrontEndDemoExercise`（前端）。
> 前端需求另见：`docs/frontend_requirements/多观看者并发直播.md`。

## 1. 背景与结论

### 1.1 现状：整套视频链路是按「单观看者」写的

同一个 `mid` + 同一个 `browser_id` 在多地登录观看时，两端会落到**同一个会话、同一个 WebRTC 管理器**上，
于是目前的表现是「互相抢流」，而不是并发观看：

| # | 现状 | 位置 | 多地观看的后果 |
| --- | --- | --- | --- |
| 1 | 新流按 `page_index` 淘汰旧流 | `stream_manager.py:111-115` | B 开播即关掉 A 的流 |
| 2 | `stream_key = {mid}:{browser_id}:page_{i}`，**不含观看者标识** | `stream_manager.py:120` | 淘汰重建后新流 key 与旧流**完全相同** |
| 3 | answer / 候选按 `stream_key` 查流 | `webrtc/router.py:164`、`:201` | A 延迟到达的 SDP/候选打到 **B 的新流**上（串流污染），两端都连不上 |
| 4 | 暂停 / 档位 / 可见性都是**会话级** | `stream_manager.py:72`、`:241-277` | A 暂停 → B 也停；A 选清晰度 → B 跟着变 |
| 5 | 帧队列是**消费式**（取出即消失） | `video_frame_producer.py:430-435` | 两个 track 同时取帧会各拿一半，都卡 |
| 6 | 前端卡死看门狗会自动重拉流 | `LiveBox.vue:55-58`、`:651-669` | 被踢的一端 8s 后重连 → 又踢回去 → **互踢死循环** |

### 1.2 结论

把「帧源」与「观看者」彻底解耦：

- **帧源**（一页一份，唯一 screencast）：负责采集与解码，「供所有人看」。
- **观看者**（一条 PeerConnection 一份）：各自独立编码、独立暂停、独立档位、独立缩放。

并顺带修掉上表 #2/#3 的**串流污染**（这是现在就存在的真实缺陷，只是单人使用时暴露不出来）。

### 1.3 决策记录（已与需求方确认）

| 决策点 | 结论 |
| --- | --- |
| 清晰度档位（帧源唯一） | **帧源按所有活跃观看者的最高档采集**；各观看者在自己的 track 里**缩放 + 抽帧**到自己的档位。全员低档时帧源自动降档，不浪费浏览器侧编码 |
| 并发上限 | **不限制**（保留配置旋钮 `browser_webrtc_max_viewers`，默认 `0` = 不限，将来可一键收紧） |
| 失联回收 | 观看者 **60s** 无心跳即回收 |
| 界面提示 | **显示**「当前 N 人在观看」 |

### 1.4 明确不做（本次范围外）

- **不共享编码**：同一帧会被 N 个观看者各自编码一次（共享的是**解码**，不是编码）。
  CPU 随人数线性增长，这是 aiortc 每 PeerConnection 一份编码器的固有代价，本次不引入转码复用层。
- **不改会话级生命周期语义**：闲置降级 / 挂起 / 关实例三级软着陆保持现状（见 §5.3）。
- **不改操作指令的作用域**：`/operation/*`（切页、新建页、关页）仍然是**会话级**——
  它们改的是浏览器本身，物理上无法按观看者隔离。本次只把**播放层**（暂停 / 档位 / 可见性）下沉。
- **不做 WebRTC 信令走 WS/DataChannel**：信令保持 HTTP（见 `docs/rpa-会话状态SSE推送计划书.md` §1.2）。

## 2. 核心约束与设计决策

### 2.1 约束一：一个 page 只能有一个 screencast

`VideoFrameProducer._start_screencast()`（`video_frame_producer.py:286-307`）在重复调用时会拿到
`already started` 异常，代码里不得不做「先 stop 再 start」的恢复。这决定了
**采集器必须被复用，不能每个观看者一份**。

→ 引入 `PageFrameSource`：每个 `page_index` 一份，持有唯一的 `VideoFrameProducer`。

### 2.2 约束二：帧是「消费式」的，必须改为广播

```430:435:RPA-Browser/app/services/RPA_browser/webrtc/video_frame_producer.py
                jpeg_data = await self.frame_queue.get()
                if jpeg_data is _STOP_SENTINEL:
                    return None

                # 合并积压：落后时只解码最新的一帧
                jpeg_data, dropped = self._coalesce_pending(jpeg_data)
```

`get_next_frame()` 从队列「取走」帧，取走即消失。两个 `WebRTCMediaTrack.recv()` 并发调用会
**各拿一半帧**，表现为两端都卡。

→ 改成**最新帧广播**：

- 解码仍然只做一次（在生产者线程池里）。
- 解码结果写入每个订阅者各自的 **`FrameSlot`（容量 1 的「最新帧槽」+ 事件）**。
- 慢消费者只丢自己槽里的旧帧，**不影响其他人**，也不再需要 `_coalesce_pending`。
- 「背压限帧」（`_wait_for_frame_slot`：延迟 ack 让浏览器降帧）**保留**，仍按帧源档位生效。

### 2.3 约束三：档位直接改 screencast 参数

```267:275:RPA-Browser/app/services/RPA_browser/webrtc/video_frame_producer.py
        changed = (
            params.quality != self._quality
            or params.frame_interval != self._frame_interval
            or params.size != self._screencast_size
        )
```

`quality` / `size` / `frame_interval` 是**帧源级**参数，无法同时满足不同观看者。

→ **两级档位**：

| 层级 | 取值 | 作用 |
| --- | --- | --- |
| 帧源档位 | `max(所有未暂停且在线观看者的档位)` | 重建 screencast（quality / size / fps） |
| 观看者档位 | 各观看者自己选择 | 在 track 内 `reformat(width, height)` 缩放 + 按自己的 fps 抽帧 |

要点：

- **缩放是零解码成本的**：帧源已经是 YUV420P 的 `av.VideoFrame`，
  `frame.reformat(w, h)` 底层走 swscale，只需重采样一次。
- 当观看者档位 == 帧源档位时（单人观看、或全员同档），**不做任何缩放**，路径与现状完全一致。
- 帧源档位取 `max` 而非固定 HIGH：全员选低档时，浏览器侧 screencast 也降下来，
  不会出现「没人要 1080p 却一直按 1080p 编码」的浪费。
- `ultra`（超清）不设「浏览器自适应」而是显式 `1920×1080`，因此同页只要有 1 个超清观看者，
  帧源就按 1080p 采集；`medium` / `low` 各自 `reformat` 缩放下去，`high` 因不设上限
  也会拿到同源的更高分辨率帧（观感更好，代价是该端编码量上升）。
- `original`（原画）是最高档：JPEG 质量 100，且 screencast **显式传页面真实视口尺寸**
  （浏览器侧默认会把画面等比缩放进 800×800，只有给出视口尺寸才是未缩放的原始图像），
  因此同页只要有 1 个原画观看者，其余档位都从这份未缩放的帧源缩放下来。
- 帧源档位变化才触发 screencast 重启；`_apply_effective_level()` 已有「参数没变就跳过」的去重，
  避免多个观看者切档时反复重启。

### 2.4 暂停：观看者级 + 引用计数

- **观看者级**：`viewer.paused = True` → 该观看者的 `ViewerMediaTrack.recv()` 挂起，不取帧、不发送。
  接收端画面停在最后一帧（浏览器行为），**其他观看者不受影响**。
- **引用计数**：当**所有**在线观看者都暂停时，才真正 `producer.set_paused(True)`（停 screencast）。
  于是**单人观看时「暂停 = 浏览器侧零编码」的省 CPU 语义完整保留**，多人时才有取舍。
- 可见性降档（`visible=false`）与暂停同理，**下沉到观看者级**。

### 2.5 串流污染修复（顺带修掉的真缺陷）

`stream_key` 加上观看者后缀，且**所有信令端点都按 `viewer_id` 校验归属**：

```
stream_key = {mid}:{browser_id}:page_{page_index}:{viewer_id}
```

这样 A 延迟到达的 answer / 候选只会命中 A 自己的流；若该观看者已被回收，则明确返回
`WEBRTC_STREAM_NOT_ACTIVE` 并 WARNING 留痕（`webrtc/router.py:203-212` 已有该分支）。

### 2.6 帧对象必须每观看者一份（不可忽略的细节）

`WebRTCMediaTrack.recv()` 会**就地修改**帧对象：

```80:82:RPA-Browser/app/services/RPA_browser/webrtc/media_track.py
        frame.pts = pts
        frame.time_base = VIDEO_TIME_BASE
        return frame
```

多个 track 共享同一个 `av.VideoFrame` 实例时会**互相覆盖 `pts`**，导致某一路的时间戳被另一路改写。
因此：

- 需要缩放时：`reformat()` 天然返回**新对象**，安全。
- 不需要缩放时：**显式拷贝一份**（`VideoFrame(w, h, format)` + 逐 plane `update`）。
- **仅在观看者数 > 1 时拷贝**：单人观看保持零拷贝，路径与现状一致。

> 这是「共享帧源」必须付的代价，且无法靠「反正在同一事件循环里」来论证安全——
> `recv()` 返回与编码之间是否插入 await 属于 aiortc 的实现细节，不能作为正确性依据。

### 2.7 观看者身份：IP 与设备（供归属者判断「是谁在看」）

同一账号多地登录时，归属者需要知道「是谁在另一个地方看」。两个数据来源：

| 数据 | 来源 | 说明 |
| --- | --- | --- |
| 客户端 IP | 请求头 `x-bili-client-ip` | 由**网关**解析前置 nginx 传来的 `X-Real-IP` / `X-Forwarded-For` 后注入（`ProxyHelper.resolveClientIp`），同时清除客户端伪造的同名头 |
| 设备 | `User-Agent` | 浏览器直接发送，经 nginx / 网关照常转发；口径为「系统 · 浏览器 大版本」，如 `Windows · Chrome 126` |
| 设备类型 | `User-Agent` | 稳定码 `desktop` / `mobile` / `tablet`（iPad 与 Android 平板都归 `tablet`，判断顺序见下）；**文案由前端 i18n 出**，后端只给码 |
| 浏览器大版本 | `User-Agent` | 结构化字段，如 `126`（Safari 取 `Version/x`）；后端同时把它拼进设备串，前端无需二次拼接 |
| IP 属地 | be-message 的 GeoLite2 mmdb（**经 RPC**） | 形如「浙江 杭州」；**内网 / 回环 / 未命中 / RPC 失败一律为空**，前端显示「未知属地」 |
| IP 运营商 | 同上（GeoLite2-**ASN** mmdb） | ASN 组织名，如 `China Unicom Shanghai network`；解析不出为空，前端显示「未知运营商」。⚠️ **值是英文**（GeoLite2-ASN 不含中文本地化，与评论 / 动态展示的 ISP 完全同值），不做二次翻译以保证「同源同值」 |

**IP 属地为什么走 be-message 的 RPC，而不是 RPA 自己装 geoip2**：

- **mmdb 单一来源**：GeoLite2 库（含 66MB 的 `GeoLite2-City.mmdb`）与下载 / 更新流程
  都只在 be-message 侧（`docker_vol/geoip/mmdb`，见其 `scripts/download_geoip_mmdb.py`）。
  各服务各存一份 = 一份库要更新 N 次，且内存里多开 N 个 Reader；
- **口径一致**：评论 / 动态的 `lbsPoi` 与「谁在看」的地域标签出自同一段解析代码
  （`be-message-service/app/services/infrastructure/geo_ip.py`），不会出现
  「动态显示浙江、观看者显示杭州」这类不一致；
- **调用方零新依赖**：RPA 只用既有的 RabbitMQ RPC 客户端（`rpc_client`），
  不必新增 `geoip2` / `maxminddb`，镜像也不必挂载 mmdb。

契约与实现：

| 项 | 值 |
| --- | --- |
| 路由键 | `message.geoip.rpc.resolve_ip_region`（前缀见 `bili_common.rpc.base.GEOIP_RPC_ROUTING_KEY_PREFIX`） |
| 契约 | `bili_common.rpc.geoip`：`ResolveIpRegionParams{ip}` → `ResolveIpRegionResult{region, isp}` |
| 服务端 | be-message `app/mq/rpc_geoip.py`（复用 `geo_ip.lookup`：City 库出属地、ASN 库出运营商，`@rpc_safe` 兜异常） |
| 客户端 | RPA `app/services/mq/rpc_geoip.py`：`resolve_ip_profile(ip) -> IpProfile{region, isp}` |

**调用时机与降级**（属地是展示信息，任何情况下都不阻塞建流）：

- 只在**观看者接入**（`POST /webrtc/offer` 的 `get_client_context` 依赖）解析一次，
  之后随观看者对象带着走，answer / ICE / 心跳都不再调用；
- 客户端侧先做**内网 / 回环 / 空 IP 短路**（本地开发直接命中，省一次往返）；
- RPC 超时 2s、be-message 不可用、返回非 0 → 一律返回空画像（属地/运营商皆空
  = 未知属地 / 未知运营商），连流照建，只在 debug 日志里留痕。

**为什么要由网关来做**：RPA 服务看到的连接来源是网关自己（同机即 `127.0.0.1`），
拿不到真实客户端。而 nginx 传来的 `X-Real-IP` / `X-Forwarded-For` 由代理层覆盖 / 追加
（客户端自带的值在代理层即被替换），因此在网关侧解析并固化成可信头 `x-bili-client-ip`。
取值顺序：`X-Real-IP` → `X-Forwarded-For` 最左值 → socket 地址；都取不到则留空，
前端显示「未知来源」。

⚠️ **前提**：网关不直接暴露公网。若绕过 nginx 直连网关，这两个头可被伪造，
此时 `resolveClientIp` 应改为只信任 socket 地址。

**设备识别**在 RPA 侧做粗粒度归类（`app/utils/depends/client_context.py` 的 `describe_device`），
不引入 ua-parser 依赖。判断顺序**不可调换**：Android 的 UA 含 `linux`、iPad 的 UA 含 `mac os`；
Edge 的 UA 含 `chrome`、Chrome 的 UA 含 `safari`。

**管理员观看者完全隐藏**（需求方决策）：

- 监管管理员可经 `verify_browser_ownership_or_admin` 访问他人浏览器；若原样展示，
  等于**把审核员的 IP 暴露给普通用户** —— 这是反向的信息泄露；
- 因此 `ViewerStream.is_admin=True` 的观看者不计入对外人数
  （`public_viewer_count`；状态接口与 SSE 的 `viewer_count` 都用它），
  也不出现在 `/webrtc/status` 的 `viewers[]` 中（`viewers_info()` 默认 `include_admin=False`），
  即归属者完全无感知；
- **监管拉流已打通**（见 §10.5）：管理员访问他人浏览器时，会话定位回退为按 `browser_id`
  反查归属者会话（`live_service.find_session_entry_by_browser_id`），并以 `is_admin=True`
  创建观看者 —— 因此管理员**能看到**，而归属者**看不到他**。

**展示方式**：顶部浮层的「N 人」徽标可点击，弹出观看者列表，不常显 ——
人数多时一屏 IP 会淹没画面。每行两段：

```
● Windows · Chrome 126  [移动]
  浙江 杭州 · China Unicom Shanghai network · 112.65.13.88 · 20:13
```

- 第一行：设备串 + 设备类型徽标（`desktop` / `mobile` / `tablet` → 前端 i18n 文案）
  + 暂停时的「画面已暂停」；
- 第二行：属地 · 运营商 · IP · 接入时间（HH:MM），
  缺失时分别显示「未知属地」「未知运营商」「未知来源」。

**hover 查看完整信息**：鼠标悬停任一行时弹出 tooltip（`placement="right"`，`:show-after="200"`），
把该行**被省略/截断**的信息补全 —— 面板窄、长值（如 `China Unicom Shanghai network`、
完整设备串）在行内会被挤压，tooltip 以「标签 + 值」逐行给出：

```
设备      Windows · Chrome 126
类型      桌面
属地      上海市 上海
运营商    China Unicom Shanghai network
IP        112.65.13.88
接入时间  2026-09-28 20:13:45   ← 行内只有 HH:MM，这里给到秒
清晰度    高清（生效 标清）      ← 两者不同才追加「生效」后缀
```

- 与行内同源同值（同一份 `LiveViewerInfo`），不额外发请求；
- 「清晰度」的用户档位与生效档位不同时（本端不可见被降档）才显示 `生效`，
  相同则只显示一个值，避免噪音；
- 暂停态不复述 —— 行内第一行已有「画面已暂停」。

**后端日志口径**（与前端面板同源、字段对齐）：观看者**接入 / 断开 / 被回收**时，
日志都带一行客户端摘要
`设备 · 设备类型 · 属地 · 运营商 · IP · 接入=HH:MM:SS · 档位=<生效档位>[ · 已暂停][ · 监管观看]`，
断开与回收另附观看时长。单一口径由 `ViewerStreamInfo.client_summary` 提供
（`ViewerStream.client_summary` / `watch_seconds` 委托 `info()` 的同一实现）。
设备类型在日志里打印**稳定码**（`desktop` / `mobile` / `tablet`），只有前端才翻译成文案；
客户端各项为空时统一打印 `-`（日志里不写「未知 X」，中文文案只在前端出）。

- 为什么：原先日志里只有 `viewer_id`（一串 uuid），运维看不出「是谁在看」，
  排查「人数不对 / 这是谁的连接被回收了」时还得回头翻前端面板；
- 为什么不直接打原始 User-Agent：UA 上百字符且高度重复，日志里价值低，
  展示口径仍统一走 `describe_device` 的「系统 · 浏览器」归类；
- 监管观看者的 `监管观看` 标记只在**后端日志**出现 —— 它对归属于者仍然完全隐藏（见上），
  但运维排查时需要能区分「这条连接是审核员在看」。

## 3. 目标架构

### 3.1 对象模型

```
WebRTCStreamManager（每 会话 一份，现状保留）
├─ _sources: dict[int, PageFrameSource]        ← 帧源级（每个 page_index 一份）
│    ├─ producer: VideoFrameProducer           ← 唯一 screencast
│    └─ broadcast(frame)                        ← 每帧投递到所有 viewer 的 slot
└─ _viewers: dict[str, ViewerStream]           ← 观看者级（每条连接一份）
     ├─ viewer_id: str                         ← 前端生成，每次 offer 一枚
     ├─ stream_key: str                        ← {mid}:{browser_id}:page_{i}:{viewer_id}
     ├─ page_index / source（弱引用或显式 attach/detach）
     ├─ pc: RTCPeerConnection                  ← 独占
     ├─ track: ViewerMediaTrack                ← 独占，订阅 source 的帧
     ├─ level / paused / visible               ← 观看者级（本次从会话级下沉）
     ├─ last_activity: float                   ← 心跳刷新
     └─ state: WebRTCStreamState
```

**索引对照**：

| 索引 | 键 | 用途 |
| --- | --- | --- |
| `_viewers` | `viewer_id` | 信令端点 O(1) 查观看者 |
| `_streams_by_key` | `stream_key` | 兼容既有 `/webrtc/status` 与 close 语义 |
| `_sources` | `page_index` | 帧源查找（一个 page 一份） |

### 3.2 帧分发路径

```
page.screencast.on_frame(JPEG)
   └─ 背压限帧（按帧源档位 frame_interval 延迟 ack，保留现状）
        └─ 写入 producer 的内部队列（容量 1 的最新帧槽）
             └─ 解码线程池：解出唯一 av.VideoFrame
                  └─ broadcast 到每个 viewer 的 FrameSlot
                       ├─ ViewerMediaTrack(观看者A)：按 A 的档位 scale / 抽帧 / clone → 编码 → A 的 pc
                       └─ ViewerMediaTrack(观看者B)：按 B 的档位 scale / 抽帧 / clone → 编码 → B 的 pc
```

### 3.3 档位仲裁

`PageFrameSource.recompute()` 在以下时机调用：

- 观看者加入 / 离开 / 被回收
- 观看者切档、暂停、恢复、上报可见性

```python
active = [v for v in self.viewers.values() if v.attached and not v.paused]
# 1) 是否还有人要看
await self.producer.set_paused(len(active) == 0)
# 2) 帧源按最高需求采集（幂等，参数未变时 _apply_effective_level 内部跳过重启）
if active:
    await self.producer.set_level(max(v.level for v in active))
```

`effective_level` 的构成（`video_frame_producer.py:188-192`）调整：

| 来源 | 层级 | 说明 |
| --- | --- | --- |
| 用户档位 | **观看者级** | 各自选择 |
| 页面不可见 | **观看者级** | 各自的标签页 / 组件遮挡 |
| 会话闲置降档 | 帧源级（保留） | 有活跃观看者时不会触发（见 §5.3） |

## 4. 接口设计

### 4.1 `viewer_id` 的引入

- **生成**：前端 `initWebRTC()` 时 `crypto.randomUUID()`，存组件内 `ref`。
  **不落 `localStorage`**（多标签会串同一个 id），**不用 `sessionStorage`**（复制标签页会被一起复制），
  刷新页面即换新 id，旧 id 由 60s 回收兜底。
- **传递**：所有 WebRTC 信令与播放控制请求的 body 增加 `viewer_id` 字段。
- **幂等重连**：同一 `viewer_id` 再次 `/webrtc/offer` 时**复用并重建**该观看者
  （关掉旧 pc、旧 track，新建 pc/track），**而不是**淘汰别人 —— 这是与现状最关键的行为差异。

### 4.2 端点改动一览

| 端点 | 改动 |
| --- | --- |
| `POST /webrtc/offer` | body 增加 `viewer_id`；返回 `stream_key` 带观看者后缀；不再淘汰同页其他流 |
| `POST /webrtc/answer` | body 增加 `viewer_id` 并校验归属 |
| `POST /webrtc/ice-candidate` | 同上 |
| `POST /webrtc/close` | body 增加 `viewer_id`；只关该观看者，**不关其他人的流** |
| `POST /webrtc/pause` | 作用于该观看者；返回**该观看者**的档位快照 |
| `POST /webrtc/quality` | 同上 |
| `POST /webrtc/visibility` | 同上 |
| `POST /webrtc/status` | 保持只读；`data` 增加 `viewers[]` 与 `viewer_count` |
| **新增** `POST /webrtc/heartbeat` | body `{viewer_id}`；刷新观看者活跃时间并 `live_service.touch()` |

> `/webrtc/status` 的**只读**约定（`docs/rpa-会话状态SSE推送计划书.md` §4.3）不变，
> 保活必须走新增的 `/webrtc/heartbeat`，避免「看一眼状态就续命」把闲置回收打穿。

### 4.3 观看者保活（**无需心跳**，以 WebRTC 连接状态为准）

> 原设计为「前端每 15s 发 `/webrtc/heartbeat`」，实现后（§10.7）已废弃 ——
> HTTP 心跳既多一条请求链路，又与真实链路状态脱节（SSE 抖动、代理超时都会造成误判）。

最终方案：观看者与会话的活性一律以 **`pc.connectionState`**（ICE/DTLS 层）判定：

- **观看者回收**：后台任务 `reap_idle_viewers`（间隔 20s）扫描：
  - `connected` → 无论多久没有 HTTP 请求都不回收；
  - 其余状态（`new` / `connecting` / `disconnected` / `failed`）→ 超过
    `browser_webrtc_viewer_idle_timeout`（默认 60s，宽限期）仍未恢复才回收。
    宽限同时覆盖「新建尚未完成协商」与「断线等 ICE 自愈」两种情形。
- **会话豁免**：`_evaluate_session_cleanup` 在「过期」之后、闲置动作之前检查
  `manager.has_live_viewer()` —— 存在 connected 观看者则视为活跃，
  不降级、不挂起（`action="restore"`）。到期（`expires_at`）是硬约束，优先于该豁免。
- **为什么不是 SSE 存活**：① SSE 走 HTTP 代理，抖动断连的瞬间不该牵连 WebRTC；
  ② 会话状态 SSE 是严格 owner 校验，监管页（管理员）根本不订阅它；
  ③ SSE 连接与观看者连接是两套生命周期，无法可靠映射。
- **暂停中的观看者不会被误回收**：暂停只停出帧，ICE/DTLS 保活仍在。

`/webrtc/heartbeat` 端点保留（SDK 兼容 + 手动兜底），常规链路前端不再调用。

### 4.4 状态暴露

`POST /webrtc/status` 的 `data`：

```json
{
  "enabled": true,
  "total_streams": 2,
  "viewer_count": 2,
  "viewers": [
    {"viewer_id": "…", "page_index": 0, "state": "active", "paused": false,
     "level": "high", "effective_level": "high",
     "client_ip": "112.65.13.88", "client_device": "Windows · Chrome 126",
     "client_device_type": "desktop", "client_browser_version": "126",
     "client_ip_region": "浙江 杭州", "client_ip_isp": "China Unicom Shanghai network",
     "connected_at": 1767196800}
  ],
  "active_streams": [ /* 兼容字段，保留 */ ]
}
```

status 的 `viewers[]` 与 SSE 共用 `manager.viewer_summaries()` 同一构造，字段完全一致
（`idle_seconds` / `idle_duration` 已移除，见 §10.6），前端只需一套 `ViewerInfo` 类型。

**会话状态 SSE**（`session_status` 事件）的 `BrowserSessionStatusData` 增加 `viewer_count`
与 `viewers[]`（元素为 `BrowserSessionViewerData`），两者都加入
`_STATUS_SIGNATURE_FIELDS`，因此「人数变化」「有人加入 / 离开 / 暂停 / 切档」都会即时推送。

**前端因此不再轮询 `/webrtc/status`**：
人数、观看者列表（设备 / IP / 接入时间）全部来自 SSE 快照（建连首帧即全量，见 §10.6）。

`/webrtc/status` 仍保留 —— 监管页必须用它（SSE 端点是严格 owner 校验，管理员 403），
排障与 SDK 消费者也需要标准查询接口。

## 5. 后端改动（RPA-Browser）

### 5.1 `webrtc_models.py`

- 新增 `ViewerStreamInfo`（`viewer_id` / `page_index` / `state` / `paused` / `level` /
  `effective_level` / `idle_seconds`）。
- `StreamQualitySnapshot` 增加 `viewer_id` 字段（明确快照归属，避免前端误当会话级）。

### 5.2 `video_frame_producer.py`（帧源改造）

| 改动 | 说明 |
| --- | --- |
| 新增 `FrameSlot` | 容量 1 的最新帧槽 + `asyncio.Event`；`subscribe()` / `unsubscribe()` |
| `get_next_frame()` → `FrameSlot.next_frame()` | 消费式改订阅式；停止哨兵语义保留（`MediaStreamError` 收尾逻辑不变） |
| 删除 `_coalesce_pending()` | 广播模式下不再需要（慢消费者丢自己的槽） |
| `_on_frame_callback()` | 解码后 `for slot in self._slots: slot.offer(frame)` |
| `_paused` | 语义变为「**帧源级**暂停」（全员暂停才置位），由 `PageFrameSource` 驱动 |
| `_visibility_low` | **移除**（下沉到观看者）；`effective_level()` 只用 `_level` + `_degraded` |
| `set_level()` | 语义变为「帧源采集档位」（= 观看者档位的 max） |

> `VideoFrameProducerStats`（自带 `paused` / `level` / `quality` 字段）语义相应变为
> **帧源级**统计，前端展示的「该观看者是否暂停」改由观看者快照提供。

### 5.3 `stream_manager.py`（管理器改造）

- 新增 `_sources: dict[int, PageFrameSource]`；`start_stream(page_index, viewer_id)` 语义变更：
  - **不再淘汰**同页其他观看者的流；
  - 同 `viewer_id` 已存在 → 复用（重建 pc/track）；
  - 返回该观看者的 `ViewerStream`。
- `set_level` / `set_paused` / `set_visibility` 改为**观看者级**：`(viewer_id, value)` →
  改该观看者 → 调用所属 `PageFrameSource.recompute()`。
- `quality_snapshot(viewer_id)`：返回**该观看者**的档位快照。
- `_sources` 与 `_viewers` 的生命周期联动：
  - 观看者离开且该 page 无其他观看者 → 停该帧源（screencast + 解码），保留 `PageFrameSource` 实例以便快速重建；
  - `close_all_streams()`（闲置挂起用）→ 关闭所有观看者并停所有帧源。

### 5.4 新增 `viewer_stream.py`

`ViewerStream`：持有 `pc` + `ViewerMediaTrack` + 观看者级状态，负责
`create_offer` / `handle_answer` / `add_ice_candidate` / `close` / `set_paused` / `set_level`。
迁移自现有 `WebRTCStreamSession`（`stream_session.py`）的信令部分，
`PageWebRTCState` 弱引用机制保留（`stream_session.py:38-70`）。

### 5.5 新增 `ViewerMediaTrack`（`media_track.py`）

在现有 `WebRTCMediaTrack` 基础上增加：

1. **抽帧**：按观看者 fps 对齐（复用现有 PTS 逻辑，帧源帧率更高时跳过不必要的帧）。
2. **缩放**：档位低于帧源档位时 `frame.reformat(w, h)`；相等时跳过。
3. **克隆**：观看者数 > 1 且无需缩放时显式拷贝（见 §2.6）。
4. **暂停**：`paused` 时挂起（**不能返回 `None`** —— 会被判定为轨道结束，见
   `video_frame_producer.py:131-136` 的既有注释）。

### 5.6 `live_service.py`

- `touch()` 调用方新增观看者心跳（`source="webrtc_viewer"`）。
- `get_browser_session_status()` 的 `BrowserSessionStatusData` 增加 `viewer_count`
  （从该会话的 `webrtc_manager` 读取）；`_STATUS_SIGNATURE_FIELDS` 增加 `viewer_count`。
- **闲置语义澄清**：有活跃观看者时心跳持续 `touch()` → 不会降级 / 挂起。
  这同时修掉了「静看 120s 变糊、300s 黑屏」的现存缺陷（根因是连上后不再有 `touch` 调用）。

### 5.7 `config.py`

| 配置项 | 默认 | 说明 |
| --- | --- | --- |
| `browser_webrtc_max_viewers` | `0` | 单会话最大观看者数，**0 = 不限制**（按需求方决策） |
| `browser_webrtc_viewer_idle_timeout` | `60` | 观看者无心跳回收阈值（秒） |
| `browser_webrtc_viewer_reap_interval` | `20` | 观看者回收扫描间隔（秒） |
| `browser_webrtc_viewer_heartbeat_interval` | `15` | 前端心跳间隔（秒），须小于回收阈值 |

### 5.8 `background_tasks.py` + `setup.py`

新增 `BackgroundTasks.reap_idle_viewers`，在 `register_background_tasks()` 中按
`settings.browser_webrtc_viewer_reap_interval` 注册（沿用现有 `add_interval_job` 写法）。

## 6. 前端改动（Vue3FrontEndDemoExercise）

### 6.1 `LiveBox.vue`

| 位置 | 改动 |
| --- | --- |
| `initWebRTC()`（`:451`） | 生成 `viewerId`；offer / answer / ice / close 请求体带 `viewer_id` |
| `handleTogglePause()`（`:1042`） | 语义变为「本端暂停」，注释同步更正（不再是会话级） |
| `handleSetQuality()`（`:1020`） | 同上；快照仅代表本端 |
| `reportVisibility()`（`:1069`） | 带 `viewer_id` |
| `startStatsMonitor()`（`:922`） | 每 15s 发一次 `/webrtc/heartbeat` |
| `loadWebrtcStatus()`（`:183`） | 判断「我是否在直播」改为在 `viewers[]` 中按 `viewer_id` 匹配，不再用 `total_streams`（多人时会被别人的流数误导） |
| 模板 | 新增「当前 N 人在观看」提示（数据来自 SSE 的 `viewer_count`） |
| `watch(isPaused…)`（`:1066`） | 注释更正：暂停是本端状态，不再是会话级 |

### 6.2 SDK

新增 `/webrtc/heartbeat` 端点后，需**手动重新生成 hey-api SDK**
（`npx @hey-api/openapi-ts`），以获得类型化方法。
若暂不重新生成，可先用通用 `client.post` 接入（本次实现按「先通用、生成后归位」的顺序推进）。

## 7. 兼容性与影响面

| 项 | 影响 |
| --- | --- |
| 单人观看 | **行为与现状完全一致**（零缩放、零拷贝、暂停仍停 screencast） |
| 会话级闲置回收 | 语义不变，但**保活来源从「信令」变为「心跳」**，修掉了静看被挂起的缺陷 |
| 操作类接口（切页/新建/关页） | 仍为会话级，多端共享；一端切页其余端跟随（物理必然，已写入文档） |
| `/webrtc/status` 的 `active_streams` | 保留兼容字段；`total_streams` 含义变为「观看者连接数」 |
| 网关 | 无需改动 |
| 多实例部署 | **仍不支持**：会话与观看者都在进程内存（同 SSE 计划书的限制） |

## 8. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| **CPU 随人数线性增长**（每观看者一份 H264 编码器；需求方选择不设上限） | 帧源解码仍只有一次；`browser_webrtc_max_viewers` 旋钮随时可收敛；日志记录每会话观看者数便于观测 |
| 帧对象共享导致 PTS 互相覆盖 | 缩放必产生新对象；不缩放时多观看者场景显式克隆（§2.6） |
| 帧源档位在多端切档时反复重启 screencast | `_apply_effective_level()` 已有参数去重；切档仍按「max」收敛而非逐端重启 |
| 切档瞬间帧尺寸变化导致解码/编码抖动 | 抽帧与缩放均在本端 track 内完成，不重建 PeerConnection |
| 观看者异常退出占资源 | 60s 心跳超时回收 + 20s 扫描；回收时关 pc、解订阅、清索引 |
| 心跳把闲置回收打穿 | 心跳仅在**该观看者仍在线**时发送；页面卸载即停；`/webrtc/status` 保持只读不保活 |
| 同一 `viewer_id` 并发 offer（前端重连竞态） | 后端对同 id 做「复用并重建」，加会话内的观看者级锁，避免两个 pc 并存 |
| 串流污染残留 | `stream_key` 含观看者后缀 + 各端点校验归属；不匹配时明确返回 `WEBRTC_STREAM_NOT_ACTIVE` 并留痕 |

## 9. 验收要点

1. **双端并发观看**：同一账号在两个浏览器（或两个标签）打开同一 `browser_id`，
   两端**同时有画面**，互不踢流；后端日志可见两个 `viewer_id` 各一条流。
2. **暂停隔离**：A 端暂停 → A 定格、B 继续播放；B 的画面与码率不受影响。
3. **全暂停省电**：两端都暂停后，后端日志出现「帧源暂停」（screencast 已停）。
4. **档位隔离**：A 选 `low`、B 保持 `high` → A 收到 640×360/5fps，B 仍为高分辨率/30fps；
   帧源按 HIGH 采集（后端日志 `VideoFrameProducer 档位生效: level=high`）。
5. **全员低档**：两端都选 `low` → 帧源档位自动降到 `low`（浏览器侧编码降下来）。
6. **保活**：静看 10 分钟，**不出现**降级 / 挂起（对照现状：120s 降级、300s 黑屏）。
7. **异常回收**：A 端直接关闭标签页 → 60~80s 内后端回收该观看者的连接并留日志；
   B 端不受影响。
8. **串流污染回归**：A 建立连接后立刻在 B 建立连接，
   检查后端日志中 A 的 answer / 候选**只**命中 A 自己的流，无 `stream_key` 混用。
9. **单人回归**：仅一个观看者时，暂停/恢复、切档、切页重连与改造前行为一致。

## 10. 实现记录

### 10.1 文件变动

| 文件 | 变动 |
| --- | --- |
| `webrtc/video_frame_producer.py` | 新增 `FrameSlot`（广播槽）、`clone_video_frame`；`get_next_frame()` → `_pump()` + `_broadcast()`；移除 `_visibility_low`（下沉观看者） |
| `webrtc/frame_source.py` | **新增** `PageFrameSource`：页级帧源 + 观看者登记 + 档位/暂停仲裁 |
| `webrtc/viewer_stream.py` | **新增** `ViewerStream` + `ViewerMediaTrack`（缩放 / 抽帧 / 克隆 / 暂停），信令部分迁移自 `stream_session.py` |
| `webrtc/stream_manager.py` | 重写为「帧源 + 观看者」双索引；`start_stream(page_index, viewer_id)` 不再淘汰他人 |
| `webrtc/stream_session.py`、`webrtc/media_track.py` | **删除**（被上面两个新文件取代，无其他引用） |
| `controller/v1/browser_control/webrtc/router.py` | 全部端点接入 `viewer_id` + 归属校验；新增 `/webrtc/heartbeat`；`/webrtc/status` 增加 `viewers[]`；新增 `_resolve_session()` 支持监管管理员访问他人浏览器（§10.5） |
| `models/router/router_prefix.py` | `BrowserSessionRouterPath.webrtc_heartbeat` |
| `models/runtime/webrtc_models.py` | 新增 `ViewerStreamInfo`；`StreamQualitySnapshot` 增加 `viewer_id` |
| `models/runtime/control.py` | `BrowserSessionStatusData` 增加 `viewer_count` 与 `viewers[]`（`BrowserSessionViewerData`，随 SSE 下发，见 §10.6） |
| `services/RPA_browser/session/live_service.py` | 状态快照填充 `viewer_count` + `active_connections` / `video_streaming`；签名加入 `viewer_count`；新增 `find_session_entry_by_browser_id()`（监管反查，§10.5） |
| `services/RPA_browser/background_tasks.py`、`app/setup.py` | 新增 `reap_idle_viewers` 周期任务 |
| `app/config.py` | 3 项观看者配置（见 §5.7；`heartbeat_interval` 已随 §10.7 移除） |
| `LiveBox.vue` | `viewerId`、心跳、按 viewer 判定自身状态、人数提示、各请求带 `viewer_id`；播放器控制层（参考 B 站直播播放器）；观看者列表弹层 |
| `i18n/modules/generated.ts` | 5 种语言新增 `viewerCount` / `multiViewerHint` / `quality` / `fullscreenEnter` / `fullscreenExit` / `viewersTitle` / `viewerUnknownDevice` / `viewerUnknownIp` / `viewersEmpty` |
| `app/utils/depends/client_context.py` | **新增**：客户端上下文依赖（`x-bili-client-ip` + `User-Agent` → IP / 设备描述） |
| `be-gateway/…/ProxyHelper.js` | 新增 `resolveClientIp`；`setUserHeaders` 注入 `x-bili-client-ip` 并把该头加入 `headersToRemove`（防伪造） |

### 10.2 与计划书的偏差

1. **（已废弃）前端心跳**：最初用通用 `client.post` 接入心跳端点；
   §10.7 落地后前端心跳整体下线，该偏差不复存在。
2. **`viewer_id` 复用策略**：自动重连 / 切页重连**复用同一 `viewer_id`**（后端 `start_stream`
   对同 id 做「复用并重建」），仅在用户主动停播、或后端明确回收该观看者时才换新 id。
   这样不会留下一堆等待 60s 回收的僵尸连接。
3. **人数上限**：`browser_webrtc_max_viewers` 默认 `0`（不限制，按需求方决策）；
   超额时复用 `WEBRTC_OFFER_FAILED` 业务码并给出明确 msg（未新增业务码，避免改动 `bili-common`）。

### 10.3 已验证

- 后端改动文件 `py_compile` 全通过；`main.app.openapi()` 确认 10 个 webrtc/SSE 路由注册正常（含 `/webrtc/heartbeat`）。
- 核心语义脚本验证通过（临时脚本已删除）：
  - 广播槽：多槽各取同一帧、慢消费者丢旧保新、关闭后返回 `None`
  - 共享帧克隆的独立性（`pts` 不互相改写）；单人观看零拷贝
  - 观看者轨道：按本端档位缩放到 640×360、PTS 单调、暂停时 `recv` 挂起
  - 帧源仲裁：全员暂停 → 停采；有人看 → 取最高档；只剩低档 → 降为 `low`
  - 管理器：未知观看者心跳返回 `False`、空表回收为 0、关闭不存在的观看者幂等
- 前端 `nuxt typecheck` 对改动文件 **0 报错**。
- 设备识别（`describe_device`）6 组真实 UA + 空值全部通过：
  Windows·Chrome、macOS·Safari、iPhone·Safari、Android·Chrome、Windows·Edge、macOS·Firefox。
- 活性判定（§10.7）：connected 永不回收 / 协商中与自愈中宽限 / 断线超时与 failed 回收 /
  `has_live_viewer` 判定 / 会话豁免只认 connected 观看者，全部通过。

### 10.4 待办

- **重新生成 hey-api SDK**（`npx @hey-api/openapi-ts`）：新增 `/webrtc/heartbeat` 端点、
  各请求体新增 `viewer_id`、`/webrtc/status` 新增 `viewers[]` / `viewer_count`。
  生成后把前端心跳切回类型化方法（见 §10.2.1）。
- 运行时联调（双端并发观看 / 暂停隔离 / 串流污染回归），见 §9。

### 10.5 监管（管理员）拉流

**问题**：`verify_browser_ownership_or_admin` 允许管理员越过归属校验，但它返回的
`auth_info.mid` 仍是**管理员自己**的 mid；而会话表以 `f"{owner_mid}_{browser_id}"` 为键，
原 `_get_webrtc_manager()` 拿它找会话必然落空 → 管理员只会拿到「会话不存在」，
监管页（`AdminBrowserMonitorView` 的「查看」抽屉）看不到直播。
更糟的是 `/webrtc/offer` 会走 `ensure_webrtc_session(admin_mid, browser_id)`，
等于**用管理员身份创建出第二个浏览器实例**。

**修复**：

1. `live_service.find_session_entry_by_browser_id(browser_id)` —— 按 browser_id 反查会话条目
   （browser_id 全局唯一），用于拿不到归属者 mid 的场景；
2. 路由侧新增 `_resolve_session()` 作为统一定位入口：
   - 先按 `{自己的 mid}_{browser_id}` 找（普通用户 / 归属者路径）；
   - 未命中则按 browser_id 反查归属者会话，并返回 `is_admin=True`；
3. `create_webrtc_offer` 在监管分支**不走 `ensure_webrtc_session`**：目标浏览器必须已在运行，
   否则直接返回「目标浏览器未在运行」；
4. answer / ice / 心跳的 `live_service.touch()` 一律改用**归属者 mid** ——
   否则会出现「管理员看着看着，归属者会话被闲置挂起」导致画面突然中断；
5. `start_stream(..., is_admin=True)` → 该观看者不计入对外人数、不出现在归属者的观看者列表；
6. `/webrtc/status` 对监管访问传 `include_admin=True`，管理员可看到全部连接（便于审核）。

**安全前提**：反查分支只在 `verify_browser_ownership_or_admin` 通过后被调用。普通用户即使猜到
他人 browser_id，也会在归属校验阶段被拒（`BrowserIdNotBeloneToUserException`），拿不到反查机会。

### 10.6 观看者列表改由会话状态 SSE 下发

**问题**：`viewers[]`（设备 / IP / 档位 / 暂停态）没有随会话状态推送，前端只能靠
stats 定时器每 10s 轮询一次 `/webrtc/status` 来刷新列表 —— 而 SSE 建连时本就是全量快照，
让列表走另一条路既多余，又会让人数 / 列表形成双来源。

**改动**：

1. 新增 `BrowserSessionViewerData`（`models/runtime/control.py`），挂在
   `BrowserSessionStatusData.viewers` 上，随会话状态一并下发；
2. 该模型**刻意不含** `idle_seconds` / `last_activity` —— 两者每次请求都在变，
   会让签名去重失效、退化成逐秒推送（有断言验证）；
3. `_STATUS_SIGNATURE_FIELDS` 加入 `viewers`：有人加入 / 离开 / 暂停 / 切档都即时推送；
4. 构造时按 `viewer_id` 排序，避免字典顺序抖动造成「假变化」触发推送；
5. 前端 `LiveBox` 删除 stats 里每 10s 的 `/webrtc/status` 轮询，观看者列表、人数、
   连接数全部消费 SSE 快照；弹层打开时也不再发请求。

**`/webrtc/status` 仍保留**（不改语义），但 **LiveBox 已完全不调用**：

- 最初留了「挂载时兜底一次」用于恢复直播状态，复盘后删除 —— 该理由本就不成立：
  刷新页面后 `viewer_id` 是新生成的，观看者列表里**永远找不到自己**，
  「恢复」逻辑从未生效；而人数 / 列表 SSE 首帧即覆盖；
- `startStreamCore` 里启动后的一次同步同样删除：answer 落地即触发后端 `touch`
  → SSE 推送新快照（签名含 `viewer_count` / `viewers`），无需主动查询；
- 现仍在调用它的只剩：
  - **BrowserStream 的「刷新 WebRTC 状态」按钮**（用户手动触发，给即时反馈）；
  - 监管场景 / 排障 / 其他 SDK 消费者（SSE 端点是严格 owner 校验，管理员 403）。

### 10.7 保活改以 WebRTC 连接状态为准（前端心跳下线）

**动机**：HTTP 心跳与真实链路状态是两套信号 —— SSE / 代理抖动会造成误判，
监管页（不订阅 SSE）还必须单独保活；而 ICE/DTLS 本身就自带保活，
`pc.connectionState` 是最真实、全场景通用的活性依据。

**改动**：

| 项 | 改造前 | 改造后 |
| --- | --- | --- |
| 观看者活性 | HTTP 心跳（15s 一次） | `pc.connectionState == "connected"` |
| 观看者回收 | 无心跳超 60s 回收 | 非 connected 且超 60s 宽限才回收（覆盖协商中 / 自愈中） |
| 会话闲置豁免 | 无（靠心跳续期） | `_evaluate_session_cleanup` 检查 `has_live_viewer()`，connected 观看者存在则不降级 / 不挂起 |
| 前端 | 每隔 15s 发 `/webrtc/heartbeat` | **零心跳** |
| 配置 | `browser_webrtc_viewer_heartbeat_interval` | 已删除 |

**边界行为**：

- 新观看者 offer→answer 之间 `connectionState` 是 `new` / `connecting`，
  与断线自愈共用宽限期，不会被误杀；
- 暂停中的观看者：暂停只停出帧，ICE/DTLS 保活仍在 → 不会被回收；
- 到期会话（`expires_at`）优先于观看者豁免（硬约束）；
- 监管页不订阅 SSE 也完全正常工作 —— WebRTC 连接在，观看者与会话就都保活。

**验证**（临时脚本，已删）：connected 永不回收 / 协商中与自愈中宽限 / 断线超时与
failed 回收 / `has_live_viewer` 空表与断线为 False / 会话豁免只认 connected 观看者，
全部通过。

### 10.8 同档位观看者共享缩放结果

帧源按最高档采集，低档观看者此前各自 `reformat` 一次 —— 3 个同选「流畅」的观看者
= 每帧 3 次相同的重采样（1080p→360p 约 1~2ms/帧）。

**改动**：帧源广播改为**按档位分组**：

- `VideoFrameProducer._slots` 从 `set` 改为 `dict[FrameSlot, 档位]`；
  `subscribe(level)` 注册、`set_slot_level()` 更新（观看者切档 / 可见性变化时由
  `WebRTCStreamManager._sync_slot_level` 同步 —— 与轨道档位同源于
  `viewer.effective_level`，两条路径不会漂移）；
- `_broadcast()` 对每个档位组只做**一次**缩放，组内各槽共享缩放产物
  （`shared=True`，消费者克隆后改写 pts）—— N 个同档观看者从
  「N 次缩放」降为「1 次缩放 + N 次内存拷贝」（拷贝远便宜于重采样）；
- 单订阅者且无需缩放时保持零拷贝路径；`ViewerMediaTrack._prepare_frame`
  保留缩放作为兜底（仅槽位与轨道档位短暂不同步时触发）。

### 10.9 ICE 候选批量上报

建连期 Chrome 陆续产出 3~6 个候选，逐个 POST 就是同量级的额外请求。

- 新增端点 `POST /webrtc/ice-candidates`（body: `viewer_id` + `stream_key` +
  `candidates[]`，上限 32），逐个交给 `ViewerStream.add_ice_candidate`，
  单个失败（如 mDNS 候选跳过）不影响批次内其他候选；返回 `{total, added, skipped}`。
  旧的单候选端点保留（兼容 + 批量失败时的前端回退路径）；
- 前端：answer 提交前的候选仍入队；answer 成功后并入批量队列**一次 flush**；
  之后的 trickle 候选攒 200ms 批量上报，批量失败回退逐个（候选不能丢）；
  已切到生成的类型化方法 `addIceCandidatesApiV1RpaBrowserControlWebrtcIceCandidatesPost`；
- 候选顺序约束不变：必须先 answer（`setRemoteDescription`）再 addIceCandidate，
  攒批只发生在 answer 之后，不会破坏该顺序。
