# 统一响应码与 HTTP 状态设计（response-code-design）

> 本文是「业务码 `body.code` ↔ HTTP 状态码」的唯一标准。
> 代码注释里长期引用的 `docs/response-code-design.md` 就是本文件，此前一直缺失，
> 导致两套语义各自演化、互相打架（见 §1 事故复盘）。
>
> 适用范围：共用 `bili_common` 的全部后端 —— RPA-Browser、be-message-service、be-bilibili-crawler。

---

## 1. 事故复盘：为什么要重新设计

**现象**：`POST /api/v1/rpa/browser/control/status?browser_id=93626176` → `HTTP/1.1 400 Bad Request`，
而「会话还没建立」是前端每 20s 轮询的最常见状态。

**链路**（已在进程内复现：`HTTP 400` + `{"code":1006,...}`）：

1. `browser_session_status` 用业务码表达状态：`SESSION_NOT_FOUND(1006)` / `BROWSER_NOT_STARTED(1007)`；
2. `ErrorStatusMiddleware` 读取响应体顶层 `code`，用 `http_status_for_code()` 回写 HTTP 状态；
3. `http_status_for_code()` 对**所有 1000+ 自定义码一律兜底 400**；
4. 前端 hey-api SDK 的配置是 `responseStyle: 'data'` + `ignoreResponseError: true`，
   在 `data` 风格下 `wrapErrorReturn()` **直接返回 `undefined`，body 被整包丢弃**。

**两个根因**：

- **根因 A（语义错位）**：把「正常状态」用「错误码」表达。没有会话 = 一个正常的状态，不是错误。
- **根因 B（契约错位）**：把「业务码」当「HTTP 状态码」用。1000+ 业务码没有 HTTP 语义，兜底成 400 后：
  - HTTP 层无法表达「不存在 / 冲突 / 超限 / 服务端失败」的区别（全被压成 400）；
  - 更致命的是——**非 2xx 的 body 前端读不到**，业务错误的 `msg` 全部丢失。

**为什么必须解决根因 B**：前端的事实契约是以 `body.code` 为唯一业务判定源：

- `src/utils/businessHandler.ts`：`if (response.code === 0)` 成功，否则读 `response.msg` 弹提示；
- `src/api/user/utils.ts`：`if (resp?.code === -101 || status === 401)` 判定未登录（**HTTP 状态仅作兜底**）；
- `src/api/http.ts`：注释明确「优先按业务码识别：有 code 字段（含业务失败…）」；
- 而 `businessHandler` 里 `const response = await asyncFn; if (response.code === 0)` ——
  非 2xx 时 `response` 是 `undefined`，会直接抛 `TypeError`，用户只看到「操作失败: Cannot read properties of undefined」。

即：**只要失败响应是非 2xx，前端就拿不到 `code`/`msg`，无法做精准业务提示。**

---

## 2. 三条铁律

### R1　状态不是错误（Status ≠ Error）

只读查询类接口的「无数据 / 未就绪 / 不存在」，是**正常状态**，用 `code = 0` + `data` 里的状态字段表达，**禁止使用错误码**。

```jsonc
// ✅ 正确：查询「会话状态」，没有会话也是成功
{"code": 0, "msg": "会话不存在", "data": {"session_exists": false, "browser_running": false, "status": "terminated"}}

// ❌ 错误：把正常状态当错误码返回（历史上会连锁触发 HTTP 400）
{"code": 1006, "msg": "浏览器会话不存在", "data": {...}}
```

对应的**命令类**接口不受此限：「关闭一个不存在的会话」确实是失败，允许失败语义。
判断标准：**调用方是在「问状态」还是在「提要求」**。

#### R1 的边界：什么时候「查不到」可以用错误码

只看「是否无数据」会误判（曾据此错误地建议改掉 `USER_NOT_FOUND`）。
真正的判据是 —— **「无数据」这一事实是否已经能由 `code = 0` 的响应体完整表达**：

| 场景 | 事实能否由 data 表达 | 做法 |
|---|---|---|
| 会话状态查询：`data.session_exists = false` 已经说明「没有会话」 | 能 | `code = 0` + 状态字段 |
| 列表查询：空数组即为「没有数据」 | 能 | `code = 0` + `[]` |
| 单用户资料：没有资料就没有任何可渲染内容，且前端必须把「用户不存在」与「网络失败」分开处理（前者静默回落兜底、后者可重试） | 不能 | 允许业务码，如 `USER_NOT_FOUND(1008)`（HTTP 200 承载） |

一句话判据：**前端需要把「无数据」与「请求失败」区别对待 → 用业务码；只是渲染空态 → 用 `code = 0` + 空数据。**

### R2　业务码是唯一业务判定源，由 HTTP 200 承载

凡需要前端按 `code` / `msg` 分支的响应，**必须返回 HTTP 200**（body 才能被 SDK 解包）。
因此自定义业务码（1000+ / 2xxx / 3xxx / 4xxx / 41xx）一律映射为 **HTTP 200**。

### R3　HTTP 状态码只表达 HTTP 层语义

只用于「前端全局兜底 / 网关 / 监控能自行处理、不需要读文案」的场景：

| HTTP | 场景 | 前端全局处理 |
|---|---|---|
| 401 | 未登录、令牌失效 | 跳登录（前端已同时兼容 `code === -101`） |
| 403 | 无权限 | 提示无权限 |
| 404 | **路由**不存在 | 开发期错误 |
| 405 / 408 / 410 | 方法 / 超时 / 已下线 | — |
| 429 | 网关级限流 | 稍后重试 |
| 5xx | 服务端故障、依赖不可用、未捕获异常 | 全局「服务器繁忙」+ **告警** |

约定：**只有 5xx 才应触发告警**。业务失败改由 `body.code` 维度做统计。

---

## 3. 映射规则（唯一来源：`bili_common.exceptions.http_status_for_code`）

| 业务码 | HTTP | 依据 |
|---|---|---|
| `0` SUCCESS | 200 | 成功（含 R1 的「无数据 / 未就绪」） |
| `-101` NOT_LOGGED_IN | 401 | 未登录（B 站官方约定码值，前端据此跳登录） |
| `400 ~ 599` | **同值** | 码值本身就是 HTTP 语义码（400/401/403/404/405/408/409/410/429/5xx），直接沿用 |
| 其余自定义码（1000+ / 2xxx / 3xxx / 4xxx / 41xx） | **200** | 业务语义，只由 `body.code` 表达（R2） |
| 未登记 / 未知码 | **200** | 不再隐式兜底 400；未知码属业务语义，由 `body.code` 表达 |
| 其他负数码 | 200 | 同「业务语义」处理 |

> 关键变化：**兜底值由 400 改为 200**。这条规则一改，
> 所有「手写 `error_response(code=1006)`」与「抛业务异常」两条链路的对外表现同时被纠正。

### 3.1 现有业务码归类

| 码 | 名称 | HTTP | 归类理由 |
|---|---|---|---|
| 1000 | BUSINESS_ERROR | 200 | 通用业务拒绝，需给用户文案 |
| 1001 | VALIDATION_ERROR | 200 | 业务规则校验（非 HTTP 参数解析） |
| 1002 | DATABASE_ERROR | 200 | 依赖故障但可被业务提示；若要告警请改 5xx 码值 |
| 1003 | NETWORK_ERROR | 200 | 同上 |
| 1004 | MID_NOT_FOUND | 200 | **业务**资源不存在（非路由） |
| 1005 | BROWSER_ID_NOT_FOUND | 200 | 同上 |
| 1006 | SESSION_NOT_FOUND | 200 | 同上（且查询场景应改用 R1） |
| 1007 | BROWSER_NOT_STARTED | 200 | 前置状态不满足 |
| 1008 | USER_NOT_FOUND | 200 | 同上（注意其「替代空列表」用法违反 R1，见 §7.4） |
| 1009 | NAME_ALREADY_EXISTS | 200 | 同名资源冲突，必须提示用户改名 |
| 1010 | BROWSER_NOTIFY_CONF_NOT_FOUND | 200 | 通知配置不存在（命令类删除场景） |
| 1011 | ACTION_NOT_FOUND | 200 | 引用的自定义操作不存在，需提示用户 |
| 2001~2006 | WEBRTC_*_FAILED | 200 | 媒体链路操作失败，需提示具体原因 |
| 2007 | PAGE_CLOSED | 200 | 前置状态不满足（页面已关闭） |
| 2008 | FINGERPRINT_LIMIT_EXCEEDED | 200 | 额度超限，需提示「升级/清理」 |
| 2009 | WEBRTC_STREAM_NOT_ACTIVE | 200 | 前置状态不满足 |
| 2010 / 2011 | GET_BROWSER_INFO_FAILED / PAGE_NAVIGATION_FAILED | 200 | 操作失败 |
| 2012 | SCREENSHOT_FAILED | 200 | 截图操作失败（原与 PAGE_CLOSED 共用 2007，见 §7.2） |
| 3001 / 3003 | CASDOOR_OAUTH_ERROR / TOKEN_PARSE_FAILED | 200 | 认证流程业务失败，需文案引导重新授权；若前端全局按 401 跳登录，可改码值口径 |
| 3002 | CASDOOR_ENDPOINT_NOT_CONFIGURED | 200 | 配置缺失，需运维文案 |
| 3004 | CASDOOR_USER_NOT_FOUND | 200 | 业务资源不存在 |
| 3005 | CASDOOR_CREATE_USER_FAILED | 200 | 操作失败 |
| 4001 / 4002 | DM_SEND_*_LIMIT | 200 | 额度/策略限制，需具体文案 |
| 4101 / 4102 / 4103 | *_DAILY_CREATE_LIMIT | 200 | 额度限制，需具体文案 |
| 401 / 403 / 404 / 405 / 409 / 429 / 500… | 通用 HTTP 码 | 同值 | 属 R3，保持 HTTP 语义 |

---

## 4. 实施点

| 文件 | 改动 |
|---|---|
| `bili-common/bili_common/exceptions.py` | `http_status_for_code()` 兜底 400 → 200；`BaseException.status_code` 去掉「推导结果若是 2xx 一律回退 400」的强制；补注释 |
| `bili-common/bili_common/middlewares/error_status.py` | 更新契约注释：中间件现在只对「HTTP 语义码（400~599）」生效，业务码为 no-op |
| `bili-common/bili_common/models/response_code.py` | 删除与实现矛盾的那段注释（「所有对外 HTTP 响应状态码恒为 200」只对业务码成立，且原来与 `-101 → 401` 自相矛盾），改为指向本文 |
| `RPA-Browser/app/exceptions/handlers.py` | 参数校验失败 `HTTP 422` → `HTTP 400`，与 `bili_common._validation_exception_handler` 对齐（同一项目不再两套契约）；`_status_for_biz_code` 注释同步 |
| `RPA-Browser/app/controller/.../session/router.py` | `/status` 恒返回 `code=0` + 状态字段（R1） |
| `RPA-Browser/app/controller/.../webrtc/router.py` | `/webrtc/status` 无流时返回 `code=0` + `{enabled:false, active_streams:[]}`（R1）；offer/answer/ice-candidate 等命令类保持失败语义 |

---

## 5. 影响面与风险

**覆盖范围**：`http_status_for_code()` 是三个后端共用的唯一入口，一处改动即全量生效。

**行为变化**：

| 场景 | 改前 | 改后 |
|---|---|---|
| 自定义业务码失败（1001/1006/2008/4101…） | HTTP 400，前端拿到 `undefined` | HTTP 200 + `code`/`msg`，前端可精准提示 |
| 未授权 / 越权 / 路由 404 / 5xx | 401 / 403 / 404 / 5xx | 不变 |
| 未捕获异常 | 500 + error_id | 不变 |
| 查询类「无数据」 | 1006 → HTTP 400 | `code=0` → HTTP 200 |

**风险**：少数「以响应对象是否存在判断成功」的写法（`if (res) {...}`）在业务失败时会从
「抛 TypeError」变成「拿到对象」，可能误入成功分支。需在联调时排查；
统一入口 `businessHandler` 及其它 `code === 0` 判断不受影响。

**监控**：业务失败不再计入 4xx 比例，告警改以 5xx + `body.code` 维度统计。

---

## 6. 验证方式

1. **单元**：对 §3.1 全码表断言 `http_status_for_code()` 结果。
2. **接口**（`TestClient`）：
   - `/api/v1/rpa/browser/control/status` 无会话 → `HTTP 200` + `code 0` + `session_exists:false`
   - `/api/v1/rpa/browser/control/webrtc/status` 无流 → `HTTP 200` + `code 0` + `enabled:false`
   - 越权 → `403`；未登录 → `401`；漏传参数 → `400`；未捕获异常 → `500`
3. **前端**：`businessHandler` 能弹出业务 `msg`（不再出现 `TypeError` 兜底文案）。

---

## 7. 迁移清单（本文档定调，分批实施）

### 7.1 业务异常码归位 ✅ 已实施

语义是业务、却借用了 4xx 码值的异常，会让前端丢文案；改为业务码空间（1000+），走 R2 的 200 通道：

| 异常 | 改前 | 改后 | 说明 |
|---|---|---|---|
| `NameAlreadyExistsException` | `BAD_REQUEST(400)` | `NAME_ALREADY_EXISTS(1009)` | 重名冲突必须提示用户改名（工作流 / 插件） |
| `BrowserNotStartedException` | `NOT_FOUND(404)` | `BROWSER_NOT_STARTED(1007)` | 前置状态不满足，不是「路由不存在」 |
| `BrowserFingerprintNotFoundException` | `NOT_FOUND(404)` | `BROWSER_ID_NOT_FOUND(1005)` | 业务资源不存在 |
| `BrowserNotifyConfNotFoundException` | `NOT_FOUND(404)` | `BROWSER_NOTIFY_CONF_NOT_FOUND(1010)` | 新增码值（命令类删除场景） |
| `ActionNotFoundException` | `NOT_FOUND(404)` | `ACTION_NOT_FOUND(1011)` | 新增码值，引用动作已删除需提示 |
| `InvalidUIDException`（RPA 本地） | `UNAUTHORIZED(401)` | `BAD_REQUEST(400)` | 「uid 格式非法」是参数错误而非未认证，原值会误触发前端跳登录；与 `bili_common` 同名异常对齐 |

**经核查保持不动的归类**（避免为了「能弹文案」而无差别地把 4xx 全部改掉）：

- 权限类 `403`：`BrowserIdNotBeloneToUserException`、`ActionNotAccessibleException`、`PluginIdNotBelongToUserException`；
- 真正的参数错误 `400`：`BrowserIdIsNoneExeception`、`InvalidMidFormatException`、`PluginIdIsNoneException`、`BrowserPageIndexError`；
- 服务端故障 `5xx`：`VideoStreamInitFailedException`、`GetBrowserSessionFailedException`、
  `GetBrowserInfoFailedException`、`WebRTCStreamNotActiveException`、`BilibiliLoginFailedException`
  （保留 5xx 以便告警；对用户只需通用文案）。

### 7.2 码值语义复用拆分 ✅ 已实施

`SCREENSHOT_FAILED == PAGE_CLOSED == 2007` 两义共码，已拆分：

| 码值 | 成员 | 说明 |
|---|---|---|
| `2007` | `PAGE_CLOSED` | **保留原值**（4 处实际使用：`webrtc/router.py`、`pages/router.py`）；2007 的规范成员名随之由 `SCREENSHOT_FAILED` 变为 `PAGE_CLOSED`，语义更准确 |
| `2012` | `SCREENSHOT_FAILED` | 移到「浏览器/页面操作失败」族（原值从未被任何代码引用） |

影响：`PAGE_CLOSED` 码值未变，4 个使用点行为零变化；仅枚举成员名解析（如接口文档生成）变得更准确。

### 7.3 R1 存量整改 ❌ 已复核：无需整改（原建议有误）

原建议「`USER_NOT_FOUND(1008)` 应改为 `code=0` + 空列表」**是错的**：

- `be-message-service/app/api/pptr_user_gateway.py:631` 明确把「用户不存在返回专用错误码」
  作为设计决策（原文：「而非空数据兜底」）；
- 前端**主动消费**该码：`useUserCardCache.ts:69`（403 黑名单 / 1008 用户不存在 / 网络失败
  三者均不写缓存）、`UserBriefCell.vue:120`（1008 静默回落昵称兜底）、`moment-api.ts:710` 有契约说明。

即：单用户资料「查不到」时没有任何可渲染内容，且前端必须把它与「网络失败」分开处理，
符合 §2 新增的 **R1 边界判据**（事实无法由 `code=0` 的 data 表达 → 允许业务码）。

结论：**保持现状**；同时把该判据写入 R1，避免后续再次误判。

### 7.4 前端消费约定 ✅ 已实施（结论：不升级 SDK）

**不升级 SDK**——改 `responseStyle` 或开启 `throwOnError` 会让 200+ 个调用点拿到不同的
对象结构 / 开始抛异常，回归面远大于收益。改为**修正调用点 + 把约定固化到本文**。

**前端消费约定（R2 的前端侧对应条款）**

1. hey-api 客户端在 `responseStyle: 'data'` 下：HTTP **2xx** → 返回响应体 `{code,msg,data}`
   （**业务失败也是 2xx**）；HTTP **非 2xx**（401/403/404/5xx）→ 返回 `undefined`（body 被丢弃）。
   因此 **`res` 为真 ≠ 成功**。
2. 直连 SDK 的调用点**必须显式判 `code === 0`**，禁止用 `if (res)` / `if (res.data)` 判定成功；
   优先走 `request()`（`src/api/http.ts`）或 `businessHandler` 收口。
3. 未登录的全局识别无需改动：`src/api/user/utils.ts:35` 同时判 `code === -101` 与 `status === 401`，
   对两种口径都成立。

**本次修正的 4 个调用点**（契约变更后会把业务失败误判为成功的直连裸 SDK 点）：

| 文件 | 位置 | 原问题 |
|---|---|---|
| `src/components/message/BanUserDialog.vue` | 封禁用户（写） | `if (res)` → 业务失败也弹「封禁成功」 |
| `src/views/admin/AdminPermissionView.vue` | 授予权限（写） | `if (res)` → 业务失败也弹「授权成功」并刷新列表 |
| `src/views/admin/AdminPermissionView.vue` | 撤销权限（写） | `if (res)` → 同上 |
| `src/views/admin/AdminPermissionView.vue` | 管理员列表（读） | 以 `res.data` 是否存在判定成功，依据脆弱 |

若未来整体改造前端 SDK 口径，届时「4xx 能否承载业务错误」可重新评估。
