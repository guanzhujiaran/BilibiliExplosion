# be-message 系统统一计划书

> **定位**：be-message 生态（后端 `be-message-service` + 共享层 `bili-common` + 前端 `Vue3FrontEndDemoExercise`）的**唯一权威计划书**。
> 本文合并原《消息系统实现计划书》《B站式评论系统计划书》《动态卡片开发计划书（dynamic_card_dev_plan）》《头像更换审核计划书》
> 《个人中心「我的记录」计划书》《RPA 中台流程设计计划书》《前端 i18n / 统一响应码 / LLM 治理》等文档，
> **只保留当前现状**；历史演进过程与逐阶段任务记录请查阅 git 历史。
>
> 关联规则：新增/修改功能需**先改本计划书再改代码**；前端 SDK（`src/api/**/hey-api/`）为生成代码，**禁止手改**，需重新生成时必须暂停等待用户手动同步。

---

## 1. 系统架构与边界

| 组件 | 职责 | 技术栈 |
| --- | --- | --- |
| `be-message-service` | 消息（私信/通知/事件/设置/推送）、动态 Moment、评论、收藏夹、用户中心、审核管理 | FastAPI + FastStream(RabbitMQ) + SQLModel + Alembic + APScheduler，**仅 MySQL（不用 Redis）** |
| `bili-common` | 共享层：统一响应码/异常、雪花 ID、RPC 契约与客户端、i18n locale、推送 MQ 发布函数、枚举/模型 | 纯 Python 包（loguru / faststream 为按需子模块） |
| pptr Postgres | 用户主数据：`TUserInfo` / `TUserDetail` / `TUserLevel` / `TUserVip`、登录/经验记录（`TUserActInfoLog` / `TUserExpRecord`） | 由 be-message 接管读写（跨库不 JOIN，需快照时建本地镜像表） |
| RPA-Browser / be-bilibili-crawler | 非动态资源详情（lottery / rpa_*）经 **RPC** 提供；RPA 网关转发 `/api/` | 经 RabbitMQ `message_exchange` 同步 RPC |
| 前端 `Vue3FrontEndDemoExercise` | 用户端 + 管理后台 | Vue3 + TS + Tailwind + Element Plus + pinia + vue-i18n + hey-api SDK |

**存储边界**：
- MySQL 主库 `BiliMessageDB` 存业务主数据（动态/评论/消息/收藏/互动计数/审核）。
- 私信正文**按月分库 + 库内 100 表**（`sharding` 按 `YYYYMM` + `msgkey%100` 路由，`prewarm_shard_job` 跨月预热）。
- 用户主数据在 pptr Postgres；be-message 只建**展示快照表**（如 `msg_user_profile`）避免跨库 JOIN。
- 图片**只存 URL 不落本地**（不接 MinIO），仅做域名白名单/数量/长度校验。

---

## 2. 统一工程约定

### 2.1 响应契约（`bili_common.models.response`）

- 对外 **HTTP 状态码恒为 200**，业务成败一律看 `body.code`；`{ code, msg, data }`。
- 公共业务码单一来源 `bili_common.models.response_code.ResponseCode`（**禁止业务代码硬编码字面量**）：
  `0` 成功 / `-101` 未登录（B 站官方约定，HTTP 仍 200）/ `400` 参数错误 / `401` 未授权 / `403` 无权限 / `404` 不存在 / `500` 内部错误。
- 异常统一走 `bili_common.exceptions`：`BaseException`（携带 code/msg/status_code=200）、`NotLoggedInException`（-101）、
  `BiliException` 等 HTTP 辅助异常。`register_exception_handlers(app)` 一键注册（be-message 用）；RPA-Browser 用 `register_business_exception_handlers(app)`。
- **未登录一律 `NotLoggedInException`，各后端不得自定义未登录异常**。

### 2.2 对外 ID（雪花 ID，见 `.codebuddy/rules/snowflake-id.mdc`）

- 统一生成器 `bili_common/core/snowflake.py`：`SnowflakeIdGenerator`（可配位宽/时间单位）+ `MinuteSnowflakeIdGenerator`（分钟步进短 ID）。
- 分钟级短 ID 位布局：`| 时间戳(分钟) | 4 bits worker | N bits 序列号 |`，**总位数恒 39 bits**；默认 `sequence_bits=4`（每 worker 每分钟 16 个）。
- **`sequence_bits` 环境变量可配**（`UID_SEQUENCE_BITS` / `MOMENT_ID_SEQUENCE_BITS` / `TOPIC_ID_SEQUENCE_BITS`，默认 4，范围 4~15，时间戳位宽缩减为 `31-(seq-4)`）；
  ⚠️ 变更位宽会与已发布 ID 数值重叠，**仅限清库重建的开发/测试环境**，生产保持默认 4。
- 实体独立生成器（独立 `worker_id`+`epoch`，避免跨实体碰撞）：uid(`UID_WORKER_ID` 默认 1) / moment_id(`MOMENT_ID_WORKER_ID` 默认 2) / topic_id(`TOPIC_ID_WORKER_ID` 默认 3)；毫秒级 `msgkey`（41+10+12，多实例须区分 `MSGKEY_WORKER_ID`）。
- 64 位 ID（雪花）**一律以字符串出参**（避免 JS `Number.MAX_SAFE_INTEGER` 精度丢失）；业务封装收敛在 `app/core/sharding.py`。

### 2.3 枚举落库

- 实现位置：`bili-common/bili_common/models/db_types.py` 定义两个 `TypeDecorator` 列类型 `StrEnum` / `IntEnum` 并对外导出；`be-message-service` 的 `app/models/db/base_tbl.py` **不再自行实现枚举列类型**，模型文件直接从 `bili_common.models.db_types` 导入 `IntEnum` / `StrEnum` 使用（不再经 `base_tbl.py` 中转再导出）。
- **统一策略（2026-08 改造）**：所有业务枚举一律定义为标准库 `enum.IntEnum` 整数枚举，模型字段统一写成 `Field(sa_type=IntEnum(EnumCls))`，落库为 `SMALLINT` 存整数 value（0/1/2…）。`StrEnum`/`VARCHAR` 方案已废弃（可读性换存储/索引效率，并避免对外接口暴露无语义字符串值）；`StrEnum` 类型定义保留仅作兼容兜底，新代码禁止再用。
- 用法：`IntEnum` 要求被映射的枚举必须是 `enum.IntEnum` 子类（值本身为整数），否则 `__init__` 抛 `TypeError`；读写经 `.value` 互转，业务侧仍拿到枚举成员可用 `is` 比较。**禁用 MySQL 原生 ENUM**（存成员名会导致查询/过滤错乱），有回归测试 `tests/test_phase_e_enums.py` 守约。**不使用 `SAEnum(native_enum=...)`**，避免原生 ENUM 与成员名存储；已删除原工厂函数 `str_enum_type()` / `int_enum_type()`。

### 2.4 鉴权

- 身份来自网关注入的 `x-bili-*` 头（微服务互信、不校验 JWT）；`AuthInfo` 含 `mid/uname/level/role/vip_status`（无头像，展示用快照表补齐）。
- 依赖注入（`bili_common.deps.auth`）：`CurrentUser` / `RequiredUser`(未登录 401) / `AdminUser`(非 admin 403) / `RootUser`（root 专属，管理端审核接口统一用）。

#### 2.4.1 JWT 存储（2026-08 安全加固：弃用 localStorage → HttpOnly Cookie）

> 背景：`localStorage` 存放 JWT 可被 XSS 脚本任意读取，风险高。改为由**浏览器直连的服务端**写入
> **HttpOnly + Secure + SameSite=Lax + path=/** 的 `bili_jwt` Cookie，前端 JS 无法读取，从根上消除 XSS 窃取。

- **签发方（写 Cookie）**：`be-message`（作为 JWT 签发方，经网关注理，代理透传 `Set-Cookie` 时浏览器按网关域名落盘）在
  - `POST /api/v1/user/refresh_token`
  - `GET /api/v1/user/nav`（非当天签发自动续期时）
  - `GET /api/v1/user/casdoor/callback`（OAuth 登录回调）
  通过 `set_jwt_cookie()` 下发新 token，**不再写入响应体 / URL**（避免日志、Referer、XSS 读取）。
- **清除**：`be-gateway` 的 `POST /api/v1/user/logout` 调用 `clearJwtCookie()`。
- **校验（读 Cookie）**：`be-gateway` 的 `jwtAuth` / `jwtAuthOptional` / `PrefetchUserInfo` / `UserGatewayProxy`
  统一从 `bili_jwt` Cookie 取 token（兼容 `Authorization` 头兜底），再经 `x-bili-*` 头传给 `be-message`。
- **前端**：删除所有 `Authorization: Bearer` 注入与 `localStorage` 持久化；请求自动带 Cookie
  （axios `withCredentials=true`、hey-api `credentials:'include'`）。登录态改由 `nav` 返回的 `user_nav` 判定。
- **`secure` 开关**：环境变量 `JWT_COOKIE_SECURE`（缺省按环境：`production=true` / `development=false`），
  开发环境走 HTTP 时可置 `false` 以便本地登录。

### 2.5 i18n

- **后端**：`bili-common` 共享层 fastapi-i18n，locale 统一在 `bili_common/locale/`（zh_CN 默认 / en / zh_TW / ja / ko）；随请求 `Accept-Language` 切换。
  **延迟翻译**（枚举/异常类体不能直接 `_()`）：枚举存原文 key、取值时 `.t()`；异常 msg 在 `to_response` 时翻译；动态串先 `_("模板")` 再 `.format()`。
  接入：`FastAPI(dependencies=[Depends(i18n)])` + `FASTAPI_I18N__LOCALE_DIR` / `FASTAPI_I18N__LOCALE_DEFAULT=zh_CN`。
- **前端**：vue-i18n（legacy:false），`src/i18n/modules/*.ts` 命名空间；axios/hey-api 注入 `Accept-Language`；locale 持久化 localStorage。

### 2.6 前端工程规范（强制）

- Vue + **Tailwind 原子类**；**禁止 `<style>` 块、禁止 `:style` 内联**；主题变量统一 `src/assets/theme.css`，只用语义化 class（`text-info-light-3` 等），**禁止 `var()` / `text-[var(--x)]`**。
- 优先 Element Plus 组件（`el-text`/`el-button`…）；尺寸只用 `large`/`default`，**禁用 `small`**。
- 功能元素必须带业务语义 class（BEM，如 `comment-card__avatar`），禁止纯样式类作为唯一标识。
- **业务图标一律用 `src/assets/svgs/` 下 SVG**（`?component` 导入、`<component :is>` 渲染；`width="100%" height="100%"` + `fill="currentColor"`），禁止用 Element Plus 图标/内联 SVG 凑数；缺资源须暂停等用户补充。
- API 调用一律走 hey-api 生成 SDK，**不手写请求、不手改 `hey-api/` 生成文件**；SDK 需更新时暂停等待用户重新生成。

### 2.7 MQ 契约

- 单 TOPIC exchange `message_exchange`，按 routing_key 分流独立队列（私信/推送/评论/事件物理隔离）。
- 队列：`message.push`（站外推送，尽力而为，消费失败 ack 丢弃不重投）、`dm_content` / `dm_notify` / `event_push` / `notify_push`（站内信幂等链路，`AckPolicy.MANUAL` + 重投）、评论 `comment.notify/audit/count`。
- **通知发布不额外开队列（2.48.0）**：`notify_push` 已负责「已发布通知 → 用户会话」的异步投递；「发布通知」本身是低频写操作，统一走 RPC 函数 `message.notify.rpc.publish_notify`（契约在 `bili_common.rpc.notify`），系统内部触发（新用户欢迎等）则同进程直连服务层，不再另设 `notify_publish` 队列。
- **RPC 模式**：服务端经 `@broker.subscriber(routing_key=...)` 暴露，客户端用 direct reply-to（`amq.rabbitmq.reply-to`）；返回 `StandardResponse`，异常在 RPC 边界转 `error_response`（不静默、不吞错）。
- 公共设施统一收编 `bili_common/rpc/`（`base.py` 路由键/白名单、`safe.py` 装饰器、`client.py` 通用客户端、按系统契约 `lottery.py`/`pptr_user.py`/`push.py`）；`bili_common/core/message_pub.py` 提供 fire-and-forget 推送发布函数。

### 2.8 日志规范（loguru）

- 业务日志统一使用 loguru，**输出到 stderr/stdout，不写任何日志文件**——容器日志由 Docker（`docker logs`）收集与持久化，本地开发终端直接可见。
- **输出等级由环境变量 `LOG_LEVEL` 控制**（`app.core.config.Settings.log_level`，默认 `WARNING`）：**生产只打印 WARNING 及以上**（压日志量）；开发环境设 `DEBUG` 看全量。
- **开发环境额外落盘**：`APP_ENV=development`（`Settings.app_env`，默认 `production`）时，在 `LOG_FILE_DIR`（默认 `logs/`）追加写 **WARNING 及以上**的日志文件（rotation 10MB / retention 7 天），便于排查问题；**生产（默认 production）不写任何文件**，日志全部交给 docker。
- FastStream 框架自身日志等级独立由 `FASTSTREAM_LOG_LEVEL` 控制（默认 `INFO`），与业务日志（loguru）解耦。
- 本地 CLI 脚本（`scripts/seed_cli.py` 等）走 loguru 默认 stderr 输出，无需额外配置。

### 2.9 模型文件命名（2026-08-29）

- **数据库表模型统一 `_tbl.py` 后缀**：`be-message-service/app/models/db/` 下的表模型文件一律命名为 `<模块>_tbl.py`（如 `moment_tbl.py` / `comment_tbl.py` / `base_tbl.py`），用于与 `app/models/` 及 `app/models/schemas/` 下的**普通（非表）模型**区分；`db/__init__.py` 保持 `__init__.py` 不改名，包名仍为 `app.models.db`。
- **导入方式不变**：外部一律 `from app.models.db import Xxx`（走 `db/__init__.py` 集中导出）；确需直连模块时写 `from app.models.db.moment_tbl import TMoment`。
- **新增表模型**：新建 `<模块>_tbl.py` → 在 `db/__init__.py` 追加导入与 `__all__` 导出（Alembic autogenerate 依赖该导出），**禁止**再创建无 `_tbl` 后缀的表模型文件。

---

## 3. 数据模型（当前）

### 3.1 MySQL 主库核心表（`BiliMessageDB`）

| 模块 | 表 | 要点 |
| --- | --- | --- |
| 动态 | `TMoment`（dynId 雪花 PK、dynType/auditStatus/content JSON 富文本…，**内容/渲染表**）、`TMomentContent`、`TMomentAudit`、`TMomentAuditLog`（审核流水）、`TMomentLike`、`TMomentDislike`（点踩明细，幂等 uq(bizType,bizId,mid)，2.35.0）、`TMomentFavorite`、`TMomentTopic`（topicId 雪花、auditStatus）、`TMomentTopicRel`（多话题关系）、`TResourceFeed`（**通用 feed 元数据表**：`bizType+bizId` 唯一 + mid/pubTime/auditStatus/tags/deletedAt/**visibleScope**（动态冗余可见范围，2.46.0），动态与非动态资源统一入 feed，2.36.0）、`moment_author_quality`（作者质量聚合：平均互动率/近 7 天发布量/违规数，定时任务计算，2.35.0） | 动态正文为富文本节点数组（WORDS/AT/TOPIC/LINK），模块化渲染；**计数统一走 `TInteractionStat`**（2.36.0 起 `TMomentStat`/`TMomentViewLog` 废弃，2.46.0 删表落地） |
| 评论 | `msg_comment_subject`（评论区：oid+type 唯一）、`msg_comment_index`（列表主表：rpid 雪花、root/parent/dialog/floor、hot_score 冗余、state）、`msg_comment_content`（正文/图片/@/IP）、`msg_comment_action`（赞/踩，uq(rpid,mid)）、`msg_comment_at`（@ 关系 + notified 补偿标记）、`msg_user_profile`（用户展示快照） | 三表分离；无 Redis，靠冗余计数 + 覆盖索引 |
| 消息 | `msg_notify`（系统通知，读扩散）、`msg_event`（事件提醒，写扩散 + `dedup_key` 幂等 + `biz_id` 出参）、`msg_dm_index` / `msg_dm_session` / `msg_dm_content`（私信，写扩散 + 正文按月分片 + `recalled_by`）、`msg_user_setting`（消息设置）、`msg_user_activity`（活跃度）、`msg_user_follow`（关注） | 通知读扩散（游标去重）、事件/私信写扩散 |
| 收藏夹 | `TFavoriteFolder`（含 cover_url + 封面审核）、`TFavoriteItem`、`TFolderCoverAudit`（封面审核流水） | 封面 URL 先下载校验后进审核，不直接写库 |
| 用户 | `TUserAvatarAudit`（头像审核：pending/approved/rejected + old/new avatar + 审核人/原因/时间） | 公开头像只存审核通过后的值 |
| 互动 | `TInteractionStat`（**通用互动计数**：like/comment/repost/view/favorite/share/dislike/coin，2.36.0 起动态与非动态统一）、`TInteractionViewLog`（泛化浏览去重） | 全资源统一计数：动态并入 `TInteractionStat`，`TMomentStat` 废弃 |

### 3.2 pptr Postgres（用户主数据，只读/受控写）

`TUserInfo`（uid/role）、`TUserDetail`（uname/sign/sex/birthday/**avatar 对外公开头像**）、`TUserLevel`（current_level）、`TUserVip`、`TUserActInfoLog`（登录记录：act_info=`login_succ`/`daily_login`/`reg`）、`TUserExpRecord`（经验记录，`ExpActionType`）。

---

## 4. API 总览（当前已上线，按功能域）

> 统一前缀 `/api/v1`，响应 `{code,msg,data}`，64 位 ID 字符串出参。

### 4.1 动态 Moment（`/api/v1/community`，2.41.0 由 `/api/v1/moment` 更名）

- **发布**：`POST /create`（scene=WORD/FORWARD、content 富文本、attach?{bizType,bizId}、repostSrc、topics?[]、lbs、option{closeComment?、**visibleScope?**}）→ 创建即 `auditing`；**visibleScope 仅 WORD 可设（缺省 PUBLIC，非法值 422）、FORWARD 一律强制 PUBLIC（服务端忽略传入值，2.46.0）**；`POST /edit`（rejected/auditing 编辑后回 auditing）；`POST /remove`（作者本人软删）；`POST /admin/remove`（root 删任意动态）；`POST /repost`（源须 normal）；`POST /space/top|untop`；`POST /create/check`（发布页预校验）。
- **Feed**：`GET /feed/all`（综合页，**recommend 推荐流模式（默认，对齐 B 站 `/x/web-interface/wbi/index/top/feed/rcmd`）**：无 page/offset 游标，请求带 `last_showlist`（逗号分隔已展示 dynId，服务端去重）、`ps`（单页条数）、`last_clicklist`（已互动，预留反馈）、`fresh_idx`/`fresh_idx_1h`/`uniq_id`（刷新/客户端标识）；登录用户按关注/互动历史**个性化排序**（2.33.0，未登录为全局排序）；`sort=time` 最新模式保留 `historyOffset` 游标）、`GET /feed/space/{mid}`（本人见全部状态、访客仅 normal）、`GET /feed/topic/{topicId}`、`GET /feed/following`（关注流，须登录）；`GET /detail/{dynId}`、`POST /details`（批量，限 20）。
- **互动**：`POST /thumb`（bizId+bizType 泛化点赞）、`POST /dislike`（点踩/取消，幂等，2.35.0）、`POST /share`（分享计数 +1，2.35.0）、`GET /interaction/status`（批量态，防乱调校验资源存在）、`GET /interaction/status/{bizId}`（detail 专用，触发浏览计数；2.42.0 起浏览明细每用户每资源一行、`lastViewAt` 判自然日窗口）、`POST /report`（统一举报，独立域 `/api/v1/report`，2.41.0 网关 `/api/v1/` 通配后恢复）。
- **话题**：`GET /topic/square` / `/topic/hot-search`（EdgeRank 排序，仅 normal）、`/topic/mine`、`POST /topic/create`（创建即 auditing）；`GET /at/list|search`、`GET /poi/nearby|search`。
- **空间/用户**：`GET /user/space/info`（对标 B 站 acc/info，**2.51.0 起内联 `follow_stat`{following_count/follower_count/mutual_count} + `upstat`{dynamic_count/like_count} 聚合统计**，空间页 / 悬浮用户卡片只需这一次请求）、`GET /user/user_info/update`（**avatar 走审核流程**，返回 `avatar_status`）。
  - **已删除（2.52.0）**：`GET /community/upstat`、`GET /message/follow/stat` —— 统计已由 `/user/space/info` 内联返回（**且这两个端点未进网关匿名白名单，未登录访问恒返回 `-101`，前端从未真正取到过数据**）；服务层 `MomentFeedService.get_upstat` / `FollowService.get_counts` 仍被 `/user/space/info` 复用，保留；响应模型 `MomentUpStatResp` 随端点一并删除（`SpaceUpStat` / `SpaceFollowStat` 取代）。

### 4.2 评论（`/api/v1/comment`）

`POST /add`（正文 @ 占位、图片 ≤9 白名单、10s 内 ≤3 次防刷）、`POST /del`、`GET /main`（hot/time 排序、内嵌 3 条楼中楼、作者可见本人 auditing）、`GET /reply`（楼中楼分页）、`GET /detail/{rpid}`、`GET /count`、`POST /action`（赞/踩/取消，幂等）、`GET /at/search`、`POST /top`（置顶）、`POST /report`（举报，达阈值仅加入审核队列，2.40.0）。`type` 白名单（`dynamic/article/lottery/feedback/other`）后端唯一真相源，非法值 422。

### 4.3 消息（`/api/v1/message`）

- 通知：`/notify/pull|list|unread|system|delete`、`/notify/admin/create|update|revoke|list`（受众 ALL/CUSTOM/LEVEL/ROLE/VIP）。**读取即自动已读（2.49.0）**：`/pull` / `/list` / `/system` 在返回前把本页命中的通知批量置为已读，`POST /notify/read` 已删除。
- 事件：`/event/report|aggregate|list|read|delete|unread`（like/reply/at 三类，`biz_id` 出参支持跳转）。
- 私信：`/dm/send|sessions|session/delete|messages|delete|recall|ack|unread`（撤回记录 `recalled_by`、删除后不可撤回、`content_ready` 兜底）。
- 设置：`/setting`（GET/POST）、`/setting/activity`；聚合：`/msg_feed/unread|heartbeat`。
- 推送：`/push`（站外提醒，投递 `message.push` 队列）、`/push/test`（立即发送）。

### 4.4 收藏夹（`/api/v1/favorite`）

`/folder/create|update|delete|list`（**封面 URL 校验后进审核**，响应 `coverAuditStatus`）、`/folder/cover/audit/list|approve|reject|mine`（root 审核封面）、`/add|remove|list|items`、`/dyn/folders`、`/setting`（可见性）、`/user/folders|dynamics`（公开读）。

### 4.5 用户中心（`/api/v1/user`）

`/nav`（每日首次登录加经验 + `daily_login` 落登录记录）、`/user_info`、`/user_info/update`（昵称/签名/性别/生日即时；**avatar 提交审核**）、`/role/set`（root）、`/search`（root）、`/casdoor/info`、`/logout`、`/identify`、`/refresh_token`、`/casdoor/callback`；
**我的记录**：`GET /act-log`（最近 7 天登录，IP 脱敏 + geo 属地）、`GET /exp-record`（最近 7 天经验）；
**头像审核**：`GET /user/avatar/audit/mine`（本人）、`/user/avatar/audit/list|approve|reject`（root）。

**黑名单管理（新增，2026-08-28）**：用户侧黑名单（拉黑用户）管理，复用 `FollowService`（状态 `BLOCKED`，表 `msg_user_follow`），与关注关系互斥。
- `GET /api/v1/user/blocklist?page_num=1&page_size=20`：本人拉黑列表（分页，返回 mid + 拉黑时间）。
- `POST /api/v1/user/blocklist`：拉黑指定 mid（`BlockReq{target_mid}`），返回 `FollowOpResp`；拉黑即解除对方对自己的 following。
- `DELETE /api/v1/user/blocklist?target_mid=`：解除拉黑，返回 `FollowOpResp`。
- `GET /api/v1/user/blocklist/check?target_mid=`：校验关系（是否已拉黑对方 / 被对方拉黑）。
- 后端实现：`app/services/user/follow.py` 新增 `FollowService.list_blocked`；路由挂在 `app/api/pptr_user_gateway.py`（前缀 `/api/v1/user`）。
- 前端：页面 `BlocklistView`（`RouteName.USER_CENTER_BLOCKLIST`）。

**账号注销（新增，2026-08-28）**：用户侧主动注销账户。
- `POST /api/v1/user/deactivate`：二次确认后入队 `message.user.deactivate`，由 consumer（`app/consumers/deactivate.py`）调用 `UserDeactivateService`（`app/services/user/deactivate.py`）+ `app/services/cleanup.*` 异步清理。
- 后端实现：路由挂在 `app/api/pptr_user_gateway.py`；鉴权同其他用户接口（当前登录 mid）。
- 前端：页面 `AccountDeactivateView`（`RouteName.USER_CENTER_DEACTIVATE`）负责注销说明与二次确认提示。

**后端 `app/services` 目录重组（本次重构，2026-08-28）**：由扁平结构拆分为「用户侧 / 系统侧」分离：
- `user/`（端用户可触发）：follow、user_deactivate、pptr_user、casdoor_service、avatar_audit、avatar_check、folder_cover_audit
- `message/`（消息域）：notify、event、dm、dm_content、setting、activity、push、push_helper、publisher、comment*、dm_admin
- `interaction_actions/`（通用互动操作对象模型，跨 bizType 通用，**不属于 moment 域**，直接置于 `services/` 下）：base、factory、folder、common/dynamic/lottery/rpa_action/rpa_browser/rpa_plugin/rpa_workflow
- `moment/`（动态域，仅放 moment 资源的实现方法）：moment_*、edgerank、feed_engine、interaction
- `admin/`（管理端）：report、ban_service、message_admin
- `infrastructure/`（基础设施）：jwt_service、rpa_rpc、lottery_rpc、geo_ip
- `cleanup/`（账号注销异步清理，保持子包）
所有 `from app.services.X` 引用同步更新为 `app.services.<group>.X`。

### 4.6 管理端

- 动态审核：`/api/v1/community/audit/list`（按 `auditStatus` 筛选：auditing/normal/rejected/hidden）、`/list/history`、`/approve`、`/reject`（支持从任意状态驳回）、`/{dynId}`。
- 话题审核：`/api/v1/community/topic/audit/list|approve|reject`（驳回通知创建者）。
- 评论管理：`/api/v1/comment/admin/audit`（队列/通过/驳回/下架/明文 IP）、`/admin/stats`。
- 举报管理：`/api/v1/report/admin/list`（biz_type/status 过滤 + 分页，含被举报次数/人数双口径）、`/api/v1/report/admin/review`（resolve/reject + resourceAction=hide，通知举报人）——独立域，网关 `/api/v1/` 通配覆盖（2.41.0）。

### 4.7 RPC（RabbitMQ 同步调用，非 HTTP）

- `message.pptr.rpc.*`：用户资料/创建用户（`rpc_create_user` **新建**用户成功后发布「欢迎注册」系统通知：同进程直连 `NotifyService.create_idempotent` 的 CUSTOM 定向投放，与管理端 / 对外 RPC 同一发布执行体）等。
- `message.notify.rpc.*`：系统通知发布（2.48.0，`publish_notify`，供其它系统调用，幂等）。
- `message.push.rpc.*`：`PUSH_MESSAGE`（投递队列异步）/ `SEND_PUSH_NOW`（立即发送同步）。
- 非动态资源详情：`get_resource_detail(biz_type, biz_id)` → `{name, cover, authorMid, jumpUrl, extra?}`；超时/缺失**弱依赖降级**（互动态照常返回，详情字段置空）。

---

## 5. 核心机制

### 5.1 审核状态机

- **动态**：`auditing → normal / rejected / hidden`；驳回/恢复写 `TMomentAuditLog` 流水；FORWARD 涉及源动态 `repostCount ±1`；驳回通知作者；失误过审可从 normal 驳回。
- **话题**：创建即 `auditing`；通过 → `normal` + `pubTime`（不发通知）；驳回 → `rejected` + 通知创建者。仅 `normal` 话题可被动态关联、可入广场/热搜。
- **头像 / 收藏夹封面**：提交 URL 校验（http/https、1s 内下载、≤1MB、image/*）→ `pending`；通过 → **同事务**写入公开字段 + 通知用户；驳回 → 保持原值 + 通知（附原因）；同用户至多一条 pending（新提交覆盖旧 pending）。
- **评论**：DFA 敏感词同步拦截（高危 `rejected`、疑似 `auditing`）；审核中作者本人可见；**过程性状态（auditing→normal）不通知**，仅驳回/下架通知；互动通知（回复/@）仅对 NORMAL 投递，恢复后经 `msg_comment_at.notified` 补偿补发。

### 5.2 消息投递模型

- **通知（读扩散）**：发布即对所有目标用户可见，`/pull` 游标去重；可见性（受众/等级/角色/VIP/免打扰）在读取时过滤；**`publish_at` 判定统一用数据库时钟 `func.now()`**（避免语句缓存陈旧 now 导致忽隐忽现）。
- **通知发布入口唯一**：所有系统通知（管理端/seed 脚本发布 + 系统自动触发的新用户欢迎通知）一律走 `NotifyService.create`（对外 HTTP 为 `POST /api/v1/message/notify/admin/create`）；系统自动触发时 `target_type=CUSTOM` + `target_value=uid` 定向、`creator_mid=0` 标识系统发布、`publish_now=True` 立即生效。
- **通知发布入口唯一（2.48.0）**：管理端 / seed 脚本 / 对外 RPC / 系统内部触发，一律落到 `NotifyService.create`（或其幂等包装 `create_idempotent`），没有第二套实现：
  - 管理端 HTTP `POST /api/v1/message/notify/admin/create`：人工显式发布，不判重；
  - 对外 RPC `message.notify.rpc.publish_notify`（`app.mq.rpc_notify`）：供 be-gateway / RPA-Browser 等其它系统调用，**幂等**（CUSTOM 单人按 `(target_value, title)` 判重），便于调用方超时重试；
  - 系统内部触发（新用户欢迎）：同进程直连服务层，不走 RPC 自调用，失败仅记 ERROR（弱依赖，不阻断主流程）。
- **事件（写扩散）**：`EventService.report` 组装 `dedup_key` 幂等（重复上报被拦）→ 聚合索引 + 计数；`biz_id` 落库并全链路出参。
- **@ / 回复的黑名单闸门（2.50.0，动态与评论同一逻辑）**：**@ 本身一律允许**——动态正文 `AT` 节点、评论 `msg_comment_at` 关系照常落库并渲染成 `@昵称`（被拉黑者仍能在正文里看到自己被 @）；但**提醒绝不投递进黑名单用户的消息中心**。`BaseEvent.report` 在「消息设置闸门 → 自赞过滤」之后增设**黑名单闸门**：`event_type ∈ {AT, REPLY}` 且接收方 `mid` 与触发者 `actor_mid` 之间存在**任一向**黑名单关系（`FollowService.is_blocked_relation`）时直接返回 `accepted=False` 跳过落库。动态 @（`MomentPublishService._notify_at_batch`）、评论 @（`CommentService._notify_at`）与评论回复（`_notify_reply`）以及审核通过后的**补偿通道**（`CommentAdminService`）全部收敛在这一个闸门上，不再各写一份判断。点赞 / 收藏 / 转发 / 评论等互动在互动层已按 `NOT_BLOCKED` 拦截（黑名单双向拒绝），审核驳回 / 下架 / 举报结果等**系统侧通知**（actor 为管理员或系统）不受此闸门影响。
- **私信（写扩散）**：会话/索引主库 + 正文异步分片（`content_ready` 兜底返回 `content_preview`）+ 死信补偿（`retry_dead_letter_job`）。
- **站内信 vs 第三方推送**：系统通知/事件/私信属**站内信**，送达由 DB 写路径保证，**不经任何第三方渠道**；第三方推送（PushMe/PushPlus）仅服务 `/api/v1/message/push` 的「站外提醒」，与站内信完全解耦。

### 5.3 动态渲染与装配（对齐 B 站 Moment 模型）

- 动态卡片**模块化渲染对齐 `DynModuleType`**：`module_author → module_extend(话题卡) → module_desc(正文) → module_dynamic → module_interaction`；附加卡是**独立 `module_additional` 模块**（渲染于正文下方），不得塞进正文 desc。**2.41.0：`module_stat` 已移除**（`MomentModule` 无 stat 计数字段）——卡片计数统一由 `GET /interaction/status` 提供（详情单条 / 列表批量拉取后按 bizId 装配），不再随卡片冗余返回。
- **attach 卡只存 `bizType + bizId`**（对标 `CreateCommonAttachCard{type,biz_id}` / `ModuleAdditional{type,rid}`），读取时 RPC 实时取详情，**禁止冗余保存 name/cover/jumpUrl 快照**。
- 正文富文本节点：WORDS / AT / TOPIC / LINK（外链图片 `picMeta.renderAsImage`）。
- **@ 节点（AT）交互（2.50.0，前端 `components/moment/MomentContentRenderer.vue`）**：展示文本优先取节点自带 `text`（`@昵称`），缺失时用 `@` + `name` 兜底（两者皆无则 `@` + mid）。**节点带 `bizId`（被 @ 用户 mid）时**复用通用用户单元格 `UserBriefCell`（`to-space` + `show-after=300`）：悬浮 300ms 展示被 @ 用户卡片，**点击直接跳用户空间**（路由 `MOMENT_USER_SPACE`，`params.mid = bizId`）；**不再用 `href`**——`jumpUrl` 只属于 LINK / RESOURCE，AT 节点取不到，会退化成 `href="#"` 空锚点。无 `bizId` 的历史数据降级为纯文本 `@昵称`，不悬浮、不跳转。渲染容器保留空白（`whitespace-pre-wrap`），保证多行正文与 @ 前后空格不被 HTML 空白折叠吞掉。
- **通用用户信息单元格 `UserBriefCell`**（`src/components/message/UserBriefCell.vue`，审核页 `CommentAdminView` / `DmAdminView` 与动态正文 @ 节点共用）：`el-popover` + `UserCard`（`show-actions=false` 只读卡），props = `mid` / `brief` / `toSpace` / `showAfter`；**默认插槽**可自定义触发文案（@ 节点传 `@昵称`，审核页回落昵称/「用户{mid}」）。数据优先级：① 调用方内嵌 `brief`（审核列表后端已装配，零请求）→ ② `useUserBrief` 跨页面共享缓存（审核端批量接口预热）→ ③ 悬浮时按 mid 走**公开接口 `GET /user/space/info` 懒加载一次**（2.51.0 起统计已内联，不再并发 `fetchRelationStat` + `fetchUpStat`），黑名单 403 / 用户不存在静默回落昵称兜底。审核端旧行为（只传 `brief`、不跳空间、立即展示）保持不变。
- **悬浮用户卡片数据常驻缓存（2.51.0，前端 `src/composables/useUserCardCache.ts`）**：卡片数据由组件内 `ref` 改为**模块级 `reactive(Map)` 共享缓存**——已加载的用户资料不再随组件卸载 / 列表重渲染 / popover 销毁而丢弃，同一用户在任意位置再次悬浮零请求；同一 mid 并发悬浮共享同一个 in-flight Promise 去重；**请求失败不写缓存**（可重试，修复原「请求前即标记 loadedMid，失败后该 mid 永久不再加载」的缺陷）。`MomentCard`（头像悬浮）与 `UserBriefCell`（@ 节点 / 审核列表）共用；关注/取关成功后直接 `patchUserCard` 改本地 `is_following`，不再回查 `/message/follow/relation`。
- 多话题：`TMomentTopicRel` 批量回填 `topics[]`，存量单话题兜底。
- **卡片点击行为**：正文（`module_desc`）文字**不跳转动态详情**（正文内部 `@`/话题/链接/资源节点自带跳转除外，不受影响）；跳详情仅由时间标签等显式入口触发；话题卡跳话题流、转发卡跳原动态详情、头像/用户名跳用户空间。

### 5.4 排序与计数

- **EdgeRank**（动态综合页 / 话题广场 / 热搜）：`Σ(w·log(count+1))·decay(pubTime)`，权重配置化。
- **推荐流去重（对齐 B 站 rcmd，2.32.0）**：综合页 `sort=recommend` **无 page/offset 分页**——客户端维护已展示列表 `last_showlist`（逗号分隔 dynId，服务端上限 100 个防滥用），服务端 EdgeRank 排序后**排除已展示项**再取 `ps` 条；`hasMore` = 排除后候选是否仍有剩余。`last_clicklist`（已互动列表）预留反馈通道，当前仅接收不参与排序；`fresh_idx`/`fresh_idx_1h` 仅用于日志统计。`sort=time` 最新模式保留 dynId 游标（`historyOffset`）不变。
- **推荐流个性化（2.33.0，MVP）**：综合页 `sort=recommend` 在全局 EdgeRank 基础上叠加**用户个性化因子**——`score = base + Σ(w_personal · signal)`，三类信号（权重配置化）：
  - 关注作者（`w_follow`）：作者 ∈ 我的关注列表（`msg_user_follow`）；
  - 互动作者（`w_liked_author`）：作者被我点赞过（`TMomentLike` + `TMoment`，关注冷启动补充）；
  - 话题偏好（`w_topic`）：动态话题 ∈ 我互动过的话题（`TMomentTopicRel`）。
  个性化信号按需批量加载（一次 IN 查询，历史回看上限 `edgerank_personalized_like_history_limit` 防全量扫描）。
  **未登录不采用全局排序（2.34.0）**：以客户端 `uniq_id` 为随机种子派生一组扰动权重（`build_anon_profile`，每项权重 × `[1±edgerank_anon_perturb_ratio]`），使不同匿名用户/会话看到不同排序（分数相近内容间顺序分化，整体仍以热度为基调）；`uniq_id` 缺失时每次请求随机。`edgerank_personalized_enabled=False`（登录侧）仍退化为全局排序。
- **EdgeRank 多维打分（2.35.0，全量维度）**：综合 Feed `recommend` 打分扩展为
  `score = content_quality·decay(age) + author_signal + fresh_bonus + feedback_penalty + personalized/anon`，其中：
  - **content_quality** = 互动加权（like/comment/repost/view/favorite/**share**）+ `w_engagement·engagement`（`(like+comment+repost)/max(view,1)` 防僵尸爆款）+ `w_rich·rich`（`contentJson` 含图片/视频/LINK 节点）+ `w_forward·is_forward`（FORWARD 转发惩罚，负权重）；
  - **author_signal** = `w_author_q·author_quality − w_author_spam·publish_penalty`（作者质量来自新表 `moment_author_quality`，定时任务聚合：平均互动率 / 近 7 天发布量 / 违规数，违规与刷屏降权）；
  - **fresh_bonus** = `w_fresh/(1+exposure)`（`exposure`= `TInteractionStat.viewCount` 即曝光量，新内容冷启动，防被高互动旧内容埋没）；
  - **feedback_penalty** = `−w_dislike·dislike_ratio`（点踩：新表 `TMomentDislike` 幂等明细 + `TInteractionStat.dislikeCount` 原子 ±1，`dislike_ratio=dislike/(dislike+like)`）+ 登录用户 `last_clicklist` 已互动作者/话题 `w_click` 加权；
  - 评论深度以评论系统 `root_count`（已有 comment 加权）近似，不单独建库。
  - **时间衰减基准改用最近活跃时间（2.43.0）**：EdgeRank 时间衰减 `decay(age)` 的 `age` 基准由**仅发布时间 `pubTime`** 改为 **`max(pubTime, 最后评论时间)`**——「最后评论时间」取评论系统 `CommentSubject.updated_at`（该字段含 `onupdate`，评论新增/删除时自动刷新，即最后评论活跃时间；无评论动态无 `CommentSubject` 行、`updated_at` 缺失，回退为 `pubTime`）。使持续被评论的动态保持新鲜度、衰减更慢，避免「刚发但早已无人评论」的动态排在「刚被热议但发得早」的动态之前。开关 `edgerank_decay_use_last_activity`（默认 true），由 `feed_engine` 将 `last_activity_time` 经 `extra` 注入算法层；`compute_moment_score` 从 `extra["last_activity_time"]` 读取衰减基准，算法层保持数据驱动、与配置解耦。
  - **`rank_feed` 增强入参 SQLModel 化（2.44.0）**：推荐引擎增强信号入参弃用模糊的原始 dict/tuple 类型，统一改为 SQLModel 实体——作者质量 `{mid: MomentAuthorQuality}`（直传实体，弃 `(avgEngagement, recentPublish, fansCount, currentLevel)` 元组）；pending 举报数 `{biz_id: ResourceReportCount}`（新增 `ResourceReportCount{biz_id, pending_count}` DTO 承载聚合结果）；评论信号合并原 `comment_override`（实时计数）与 `comment_activity_at`（最后评论时间）为单一 `{biz_id: CommentSubject}`（`root_count` + `updated_at` 同源单次查询，删除冗余双查询）。话题 hot 排序路径同步适配。
  - **`EdgeRank`/`feed_engine` 内部数据结构 SQLModel 化（2.45.0）**：`edgerank.build_anon_profile` 弃用 `model_dump()`→dict 扰动→`model_validate()` 的 dict 中间态，改为 `FEED_PROFILE.model_copy()` + 权重字段直接赋值（自始至终保持 `EdgeRankProfile` 实例，不经 dict 中转）；`_profile_from_settings` 直接以关键字构造 `EdgeRankProfile`（dict 仅作为 pydantic-settings JSON 配置的桥接保留，不扩散到算法内部）。`feed_engine.rank_feed` / `_extra` 的 `{id: Entity}` 索引映射（`counts: {biz_id: TInteractionStat}` / `author_quality: {mid: MomentAuthorQuality}` / `report_counts: {biz_id: ResourceReportCount}` / `comment_subjects: {biz_id: CommentSubject}`）为**批量查询结果索引**（一次 IN 查询后按 id 点查，避免 N+1），保留 dict 语义，值一律为 SQLModel 实体。`tests/test_edgerank.py` 同步弃用旧 dict 传参（`extra={...}`、`profile.weights`/`weight(k)` 属性），改为 `EdgeRankExtra` 实例与字段访问。
- **计数范式**：高频计数走「明细表 + 原子 ±1」（禁 COUNT 扫描）；低频统计（用户空间聚合统计：`/user/space/info` 的 `follow_stat` / `upstat`，2.51.0 起随空间资料一次返回）允许聚合。评论/动态热度用冗余列排序。
- **通用资源 Feed 引擎（2.36.0）**：Feed 计算收口到 `feed_engine`（`FeedProvider` 适配器模式）——任意 `bizType+bizId` 资源经适配器提供候选（`{bizType, bizId, mid, pubTime, tags}`）与计数（`TInteractionStat` + `CommentSubject`），引擎统一执行 EdgeRank 打分（含 2.35.0 全量维度）/ 个性化 / 匿名随机 / `last_showlist` 去重 / 分页；动态与非动态资源共用一套计算。动态 provider 渲染回 `TMoment` 内容模块；其他资源走 RPC 详情。
- **计数统一（2.36.0，消除双轨）**：`TInteractionStat` 扩展 comment/repost/share/dislike/coin 全计数，动态互动（点赞/点踩/分享/转发/浏览/评论）全部并入 `TInteractionStat`（`bizType=dynamic` 行），`TMomentStat`/`TMomentViewLog` 废弃（**2.46.0 删表落地**）；浏览去重统一 `TInteractionViewLog`（**2.42.0 每用户每资源一行**，唯一约束 bizType+bizId+mid，`lastViewAt` 判自然日窗口、跨天访问才给 Stat +1），点赞/点踩明细统一 `TMomentLike`/`TMomentDislike`（已泛化）。
- **举报反馈通用化（2.37.0，方案 A）**：`ReportBase` 增加 `resourceType`（`InteractionBizTypeEnum` 值，可空）标识被举报对象所属资源类型——动态/评论/用户举报自动填充（dynamic→1），lottery/rpa_* 等资源举报时显式传入；举报 API `ReportCreateReq` 新增 `resourceType`。EdgeRank 附加维度 `report_count`（按 `resourceType+bizId` 统计 pending 举报数）降权，**全资源通用**（非动态资源不再恒 0）。**举报表更名 `TMomentReport → TResourceReport`**（动态专属 FK 移除，任意资源可举报，2.37.0）。
- **作者粉丝/等级维度（2.37.0）**：`moment_author_quality` 扩展 `fansCount`（≈ 被关注数，`msg_user_follow` 按 `target_mid` COUNT，不跨库）+ `currentLevel`（pptr `PptrUserLevel.current_level` 回查）；定时任务低频聚合。EdgeRank 附加维度 `fans`/`level`：`+ w_fans·log(1+fans) + w_level·level`。
- **无作者资源兼容（2.37.0）**：`TResourceFeed.mid` 允许 NULL——lottery/rpa_* 等资源可能无作者；引擎 `FeedCandidate.mid` 为 `int | None`，作者维度（`moment_author_quality` / `msg_user_follow` 关注信号）在无作者资源上**自动跳过**（`mid=None` 不命中任何信号，不参与作者质量/关注 boost），不崩溃不误加权。
- **举报资源处置（2.38.0）**：管理端审核举报 `resolve` 时可选 `resourceAction=hide` 联动处置被举报资源——动态（`bizType=dynamic`）：`TMoment.auditStatus → hidden`（管理员下架）+ `TResourceFeed.auditStatus='hidden'`（退出 Feed）；评论（`bizType=comment`）：`CommentIndex.state → hidden`；用户（`bizType=user`）预留。**下架后若资源有作者（mid 非空）发 `HIDE` 站内事件通知作者**（`EventTypeEnum.HIDE`，弱依赖独立会话，失败不阻塞处置）。
- **通用资源举报与跨项目处置（2.39.0）**：新增举报来源 `ReportBizTypeEnum.RESOURCE="resource"`——lottery/rpa_* 资源以 `bizType=resource` + `resourceType`（`InteractionBizTypeEnum` 值）举报，落 `TResourceReport`。处置（`resourceAction=hide`）为**双层**：
  1. **Feed 层（be-message 本地，立即可控）**：`TResourceFeed.auditStatus='hidden'`，被举报资源**立即退出 Feed**，与归属服务可用性无关；
  2. **资源层（RPC，弱依赖）**：新增 RPC 契约 `message.rpa.rpc.hide_resource`（`HideResourceParams{bizType,bizId,operatorMid,reason}`），be-message 作为客户端调用**归属服务**（RPA-Browser 按 bizType 内部路由：lottery→be-bilibili-crawler、rpa_*→本地），资源实际下架/停用；RPC 超时/失败仅告警降级（Feed 层已生效）。
  归属服务需实现 `hide_resource` 服务端（跨仓库，待 crawler / RPA 项目跟进）。
- **处置策略与权限（2.40.0）**：
  - **lottery（crawler 资源）不允许下架**——举报仅记录（入审核队列），`resourceAction=hide` 对其**拒绝处置**（Feed 层/RPC 均不执行）；
  - **rpa_* 允许下架**（走双层处置）；dynamic/comment 可下架/隐藏（2.38.0）；
  - **下架仅限管理员/权限用户**：举报审核接口已要求 `AdminUser`（role=root），`resourceAction=hide` 只能在审核时由管理员显式触发；**举报达阈值仅「加入审核队列」——不改变资源状态**（`_linkage` 不再改 auditStatus），资源照常展示，是否下架由管理员在队列审核中决定；
  - **被举报数量（双口径）**：`reportCount` = 被举报次数（`COUNT(*)`，累计）；`reportPeopleCount` = 举报人数（`COUNT(DISTINCT reportMid)`，同一人多次举报只记一次）。管理端举报列表 `ReportItem` 与资源互动状态接口 `InteractionStatusItem`（`GET /interaction/status[/{biz_id}]`）均返回两个口径。
  - **审核结果通知举报人（2.40.0）**：审核员 `reject`（举报不成立）→ 举报记录置 `rejected`（移出待处理队列）并**通知举报人**（`EventTypeEnum.REPORT_REJECT`，内容"你提交的举报未通过审核"，弱依赖独立会话）；`resolve`（成立）→ 举报记录置 `resolved` 并**通知举报人**（`EventTypeEnum.REPORT_RESOLVED`，内容"你提交的举报已成立并处理"），可选 `resourceAction=hide` 下架。
- **计数对账已移除**：计数加减全部在同一数据库事务内原子 ±1（明细表幂等 + 计数 UPDATE），数据一致由事务保证，无需定时全量对账兜底（2.46.0 起不再注册 `comment_reconcile_job`，消除高并发下全量重算持锁/占连接导致的接口卡死风险）。
- **可见范围过滤（2.46.0）**：`TMoment.visibleScope`（0=公开/1=仅关注/2=仅自己/3=充电专享）正式启用：
  - **语义**：仅**创建动态（WORD）**可设置——创建接口 `option.visibleScope` 传入（缺省 `PUBLIC`，非法值 422）；**转发动态（FORWARD）一律强制 `PUBLIC`**（服务端忽略传入值）；
  - **冗余落 Feed 元数据**：`TResourceFeed` 新增 `visibleScope` 列（动态行冗余写入、与 `TMoment.visibleScope` 一致；lottery/rpa_* 等非动态资源为 NULL）；发布/编辑时同步，推荐流候选**零 join** 直接过滤 `visibleScope='PUBLIC'`；
  - **过滤范围**：**所有公共流**（综合页 recommend/time、话题 Feed、关注流、访客视角空间 Feed）仅展示 `visibleScope=PUBLIC`；**本人视角空间 Feed** 可看自己全部状态（含 SELF/auditing/rejected）。
- **候选集多路召回（2.46.0，替代纯时间窗口）**：综合页 `sort=recommend` 候选由「72h 最新 300 条」升级为**多路召回 → 并集去重 → `rank_feed` 精排**两段式：
  - 五路召回（每路独立开关 `edgerank_recall_*_enabled` 与上限 `edgerank_recall_*_limit`，配置化；返回 `bizId` 列表，召回阶段不排序）：
    1. **热门/趋势路**：`TResourceFeed` normal + PUBLIC + pubTime 窗口最新 N，∪ `TInteractionStat` 互动量（like+comment+repost）倒序 top M ∩ normal + PUBLIC——兜底「新且热」，替代纯时间窗口；
    2. **社交关系路**（登录）：我关注作者（`msg_user_follow`）最近动态（`TResourceFeed.mid IN`，复用关注流信号），未登录跳过；
    3. **内容标签/分类路**（登录）：我互动过的话题（`TMomentTopicRel`，复用 `load_personal_signals` 偏好话题）下动态；
    4. **地理位置路**（可选）：请求带 `lat/lng` 时按 `TMoment.lbsLat/lbsLng` 附近范围召回，未传/无 LBS 数据则空；
    5. **协同过滤路（MVP 近似）**：以「我点赞/互动过的作者（`TMomentLike`+`TMoment`，ItemCF 简化）」新动态召回；完整 user-based CF（相似用户矩阵）标记 Phase 2 遗留；
  - 并集去重后统一进入 `rank_feed`（EdgeRank 多维打分 + 个性化 + 匿名随机 + `last_showlist` 去重 + 分页），总候选上限 `edgerank_candidate_limit` 保持；任一/多路数据缺失自动退化为剩余路并集，`settings.edgerank_enabled=False` 仍回退时间倒序。

### 5.5 泛化互动与 RPC 详情

- 点赞/收藏/浏览/点踩/分享支持多资源（`bizType`：dynamic/lottery/rpa_*），be-message 只存「互动明细 + 计数」，**不冗余资源详情**；详情经 RPC `get_resource_detail` 实时获取，失败降级。
- **计数统一（2.36.0）**：动态资源计数并入 `TInteractionStat`（与 lottery/rpa_* 同一张表，`bizType` 区分行），点赞/点踩明细 `TMomentLike`/`TMomentDislike`、浏览去重 `TInteractionViewLog`（2.42.0 每用户每资源一行）、评论 `CommentSubject(oid,type)` 均已是泛化结构；`TMomentStat`/`TMomentViewLog` 废弃并删除（**2.46.0 删表落地**）。
- **浏览去重（2.42.0）**：`TInteractionViewLog` 每用户每资源仅一行（唯一约束 bizType+bizId+mid），`viewCount` 累计浏览次数、`lastViewAt` 记录最后访问时间；同日重复访问仅刷新明细行，**跨自然日再次访问**才给 `Stat.viewCount` +1；用户浏览历史（`WHERE mid=? ORDER BY lastViewAt DESC`）直接点查，无需聚合。**对账脚本已移除**（单行明细丢失逐次访问日期，无法作为对账权威源；浏览计数非关键数据，由热路径原子 ±1 + MQ 幂等保证一致性）。
- **互动操作对象化（2.47.0）**：点赞 / 收藏 / 转发 / 分享 / 点踩等互动操作从「moment 专属静态方法」重构为**通用操作对象模型**（`be-message-service/app/services/interaction_actions/`）：
  - **抽象基类 `BaseInteractionAction`**（`abc.ABC`，模板方法模式）统一编排
    `run()` = `_check_biz_type()` 类型校验 → `get_resource()` 获取资源 → `_check_relation()` 关注关系权限 →
    `check_resource_exists()`（不存在抛 `InteractionActionError`）→ `do_execute()` 执行操作 → `after_execute()` 操作后 hook；
  - **关注关系权限（原子检查项数组 + 注册表）**：基类用 `relation_scope: list[InteractionRelationScopeEnum]`（**原子**检查项数组，空列表 = 无限制，可任意组合）集中控制每个互动操作对「关注 / 非关注 / 黑名单」关系的权限；原子项仅三个：`FOLLOWING` 仅关注 / `NON_FOLLOWING` 仅非关注 / `NOT_BLOCKED` 黑名单双向任一向禁止，每个原子项对应 `_RELATION_CHECKERS` 注册表中一个独立校验器（`_check_relation` 遍历数组逐个执行）；黑名单判定复用 `FollowService.is_blocked_relation`（任一向拉黑即拒绝，资源无作者 / 操作对象是本人不拦截）；**后续新增权限**（如 `VIP_ONLY` 会员专属、`SUPPORTER` 对方粉丝会员）只需加枚举项 + 注册校验器，即可被任意操作组合使用，无需改动基类；各操作的报错信息集中在类属性 `error_messages`（基类默认 + 子类覆盖 / 补充）；
  - **统一资源表示 `InteractionResource`（SQLModel）**：`app/models/schemas/interaction.py` 新增统一资源模型（`bizType` / `bizId` / `authorMid` / `ownerMid` / `exists` / `interactable` / `title` / `content`，非 DB 表）；各子类 `get_resource()` **统一返回该模型**，基类据此统一做存在性（`exists`）/ 可互动性（`interactable`，如动态需 normal 未软删、收藏语义允许 auditing）/ 作者关系（`authorMid`，关注 / 黑名单校验）/ 所有者（`ownerMid`，DAC `OWNER_ONLY` 校验）判断——`check_resource_exists` 收敛为基类默认实现（子类按语义置 `exists` / `interactable` 即可），`after_execute` hook 统一取 `authorMid` / `bizId` / `content`；
  - **DAC 权限控制（围绕资源展开）**：基类新增 `InteractionAclScopeEnum`（`OWNER_ONLY` 仅资源所有者 / `AUDITOR_ONLY` 仅审核员）与 `acl_scope` 原子检查项数组（空列表 = 公开）+ `_ACL_CHECKERS` 注册表（与 `relation_scope` 互补：前者描述操作者**身份/授权**，后者描述操作者与作者的**关系**）；`run()` 流程在关系校验后执行 `_check_acl`；`_is_owner`（默认比较 `ownerMid`，回退 `authorMid`）、`_is_auditor`（默认 True——审核接口鉴权层已保证管理员，可覆盖）；后续新增权限（如会员专属 / 对方粉丝会员）只需加枚举项 + 注册校验器；
  - **子类（继承者实现接口）**：`LikeAction`（点赞/取消，`NOT_BLOCKED` + 点赞后 LIKE 事件通知 hook）、`FavoriteAction`（收藏/取消，多夹 + 按用户去重计数，缺省默认夹）、`RepostAction`（转发 FORWARD，`NOT_BLOCKED`，`do_execute` 复用 `MomentPublishService.repost`）、`ShareAction`（分享上报，动态 `shareCount` +1）、`DislikeAction`（点踩/取消）、`ReportAction`（举报，复用 `ReportService`，不改 auditStatus）、`ViewAction`（浏览去重上报，弱依赖不校验资源存在）；各子类按 **`biz_type` 分文件夹**组织，**覆盖全部 6 个 `InteractionBizTypeEnum`**：`dynamic/`（点赞 / 收藏 / 转发 / 分享 / 点踩 / 举报 / 浏览）、`lottery/`、`rpa_action/`、`rpa_workflow/`、`rpa_browser/`、`rpa_plugin/`（点赞 / 收藏 / 浏览，继承 `common/` 通用实现，仅声明 `_biz_type`）；基类 / 权限注册表仍位于顶层 `base.py`；
  - **不可变 biz_type 属性**：基类 `BaseInteractionAction` 增加 `_biz_type` 类属性（子类声明自己对应的资源类型）+ 只读 property `biz_type`（无 setter，运行期不可变；未声明抛 `TypeError`）；`__init__` 不再接收 `biz_type` 参数，接口层无需传资源类型；
  - **互动操作枚举 `InteractionActionEnum`**（`base.py`）：枚举通用内容型互动全集 `LIKE / DISLIKE / FAVORITE / SHARE / REPOST / VIEW / REPORT / AUDIT_APPROVE / AUDIT_REJECT`，作为 `factory._ACTION_TABLES` 的 key，统一盘点每个 `biz_type` 支持哪些互动、还缺哪些；新增互动先在此声明枚举项再注册表；
  - **工厂分发（补全通用互动表）**：`interaction_actions/factory.py` 用 `InteractionActionEnum` 作 key，补全 **7 个通用内容型互动（点赞 / 点踩 / 收藏 / 分享 / 转发 / 浏览 / 举报）在全部 6 个 biz_type 的实现**（非动态经 `common/` 的 `ResourceLikeAction` / `ResourceDislikeAction` / `ResourceFavoriteAction` / `ResourceShareAction` / `ResourceRepostAction` / `ResourceViewAction` / `ResourceReportAction`）——**非动态「转发」= attach 行为计数**（`ResourceRepostAction` 复用 `TInteractionStat.repostCount` 记录 attach 次数）；**审核操作（`AUDIT_APPROVE` / `AUDIT_REJECT`）**为 DAC 审核员操作，当前仅动态已对象化（`dynamic/audit.py` 的 `AuditApproveAction` / `AuditRejectAction`，迁移原 `MomentAuditService.approve/reject`），其余类型待接入对应审核服务后补全；提供 `get_action` / `get_like_action` / `get_favorite_action` / `get_view_action`，按资源类型返回对应操作类（每个类自带 `_biz_type`）；`/thumb` `/favorite/add|remove` 与浏览 MQ 消费等通用入口均经工厂分发；
  - **收藏夹管理对象化**：原静态 `FavoriteService` 的收藏夹管理（创建 / 更新 / 删除 / 列表 / 收藏明细 / 主页可见性设置 / 他人公开读 / 默认夹 get_or_create）迁移为 `interaction_actions/folder.py` 的 `FavoriteFolderAction(session, actor_mid)`（用户维度操作类，方法即操作）；
  - **接口层调用方式**：直接实例化对应操作类（从 `interaction_actions` 或对应子包导入），把 `actor_mid / biz_id / dyn_id / folder_id / up / action / reasonType` 等各类 id 赋给 `__init__` 属性（`biz_type` 由类声明），调用 `await XxxAction(session, actor_mid, biz_id, ...).run()` 即可；`/thumb` `/dislike` `/share` `/repost` `/report` `/favorite/add|remove` 与浏览 MQ 消费（`consumers/interaction_view.py`）均直接实例化操作类（通用入口经 `factory.get_action("like"|"favorite"|"view", biz_type)` 分发）；**原静态 `MomentInteractionService` / `FavoriteService` 已整体删除**，逻辑全部收口到对象模型，收藏夹管理经 `FavoriteFolderAction`，测试改为直接实例化操作类。

### 5.6 通知可见性细节

- 受众解析 `resolve_target_mids`（按 `recv_notify`）；投放类型 ALL/CUSTOM/LEVEL/ROLE/VIP；免打扰时段/关闭推送由 `can_push_now` 判定；活跃度（`UserActivity`）仅用于前端轮询节奏，**与消息送达解耦**。
- **读取即已读（2.49.0）**：`/notify/pull` / `/notify/list` / `/notify/system` 一律「先按当前状态构造出参 → 再把本页 id 批量 upsert 为已读」，因此出参里的 `is_read` 是**读取前的快照**（前端仍可据此高亮「本次新到」），落库状态则已是已读；重复读取靠 `(mid, notify_id)` 唯一索引 + `ON DUPLICATE KEY UPDATE` 幂等。对外不再提供 `POST /notify/read`，前端不再单独调已读接口。
- **已删除 `only_unread` 查询参数（2.49.0）**：读取即已读后「仅看未读」的结果集会在翻页过程中持续收缩（第 1 页读掉的条目从第 2 页候选里消失），offset 分页必然跳条。该参数与前端筛选框一并移除；「新到未读」由出参 `is_read` 快照 + `/notify/unread` 红点表达。

### 5.7 seed 灌数（`be-message-service/scripts/seed_cli.py`，唯一入口）

- **一个命令跑完全部**：`uv run python scripts/seed_cli.py`（全互动联调 + 大数据灌数两阶段顺序执行）。
- 数据源只读：动态/话题取自 biliopusdb 真实数据；作者/点赞者/浏览者/**@对象**统一取自 pptr Postgres 真实用户（`fetch_pptr_user_pool` 返回 `(uid, uname)`，昵称供动态 AT 节点用）。
- **素材池真实化**：`_SENTENCES`/`_COMMENTS`/`_REPLIES` 启动时从 `biliopusdb.t_lotdyninfo.dynContent` 真实动态正文按长度分池加载（长文→动态正文、短文→评论/回复语，去空白去重）；`_TOPIC_NAMES` 从 `bilidb.t_topic_item` 加载（自动探测话题名列）。外库连接/结构失败时降级内置硬编码兜底，不阻断 seed。
- **严禁直写 MySQL 灌数**——统一经 be-message HTTP 接口（`moment/create`、`audit/approve`、`thumb`、`interaction/status` 等）。
- **@ 提及全覆盖（2026-08-29）**：动态正文与评论正文末尾统一追加**随机 @**，让 seed 数据天然覆盖 @ 链路（原评论末尾的 `·{uuid4 随机串}` 仅用于正文去重，现改为随机 @，兼作去重——规避「同用户同正文 10s 内 >3 次」的评论限流）：
  - **动态**：末尾追加 `AT` 富文本节点（`bizId`=被@ mid、`name`=昵称，不 @ 自己）。全互动阶段（发布 / 转发）与大数据灌数阶段均追加；灌数阶段正文长度超过 `_BULK_AT_CONTENT_MAXLEN`（1900，动态正文上限 2000 留余量）时**跳过 @**，避免触发长度校验导致整条动态灌入失败。
  - **评论**：末尾追加 `@昵称` 文本，并同时带 `at_mids` / `at_name_to_mid`（服务端归一为 `@{mid}` 占位符存储）。一级评论 / 楼中楼 / 显式 @ 场景均追加，不 @ 自己；显式传入的 `at_mids` / `at_name_to_mid` 与随机 @ 目标合并下发。
  - **回查验证**：`_verify_dynamic_at` 查 `GET /community/detail/{dynId}` 断言 desc 模块回显 AT 节点、且正文 `text` 已渲染为 `@昵称`；`_verify_comment_at` 查 `GET /comment/main` 断言出参带 `at_name_to_mid` / `at_users`、且 `message` 已把 `@{mid}` 渲染回 `@昵称`；二者再经 `_verify_at_event` 查被 @ 用户的 AT 事件提醒是否含该 `resource_id`（动态=dynId / 评论=rpid）。@ 通知为**弱依赖**，未命中只 warning：黑名单静默（2.50.0，seed 随机 @ 可能命中持久化黑名单）/ 消息设置闸门 / 幂等去重均属预期。
- 阶段/细项开关：`--skip-full` / `--skip-bulk` / `--dry-run` / `--skip-follow`；参数 `--full-count`(默认10000，**全互动动态条数与大数据灌数条数统一由该参数控制**；已删除独立的 `--bulk-count`) / `--full-concurrency`(默认20，**全互动动态创建与大数据灌数统一并发数，`asyncio.Semaphore` 控制**；已删除独立的 `--bulk-concurrency`) / `--base-url` / `--admin-mid`。
- **全互动动态创建并发化**：`seed_moment` 用 `asyncio.Semaphore(concurrency)` + `create_task` 并发执行（发布/审核/点赞/浏览/转发），单条失败软降级跳过；共享状态（normal_ids 转发池等）在单事件循环内聚合，无竞态。
- **进度展示统一用 tqdm**：全互动阶段（动态/评论等主循环）与大数据灌数阶段均以 tqdm 进度条呈现，不打印手写「已处理 X/N」日志。
- 大数据灌数单条失败**软降级跳过**；私信撤回/删除断言**响亮报错**（暴露代码 bug）。
- **私信双向互发**：`seed_message` 覆盖 a→b 与 b→a **两个方向**的「发送 → 审核 → 已读 → 撤回（双方 RECALLED + recalled_by/recalled_at 落库与出参）→ 再发送 → 单方面删除（自己视角不可见、对方仍可见）→ 删除后撤回被拒」全链路，验证私信写扩散在双向均正确落库；另对**多对用户**做双向互发（发送 → 审核 → 已读 → 双方可见），覆盖「用户之间互相私信」的会话网络广度（被陌生人过滤的配对宽容跳过）。
- **雪花 ID 分钟级容量**：分钟步进短 ID 每 worker 每分钟 16 个（默认 `sequence_bits=4`），灌数超速时服务端锁外等待下一分钟（≤60s）；客户端超时已环境变量化（`SEED_HTTP_TIMEOUT` 默认 90s / `SEED_REQ_TIMEOUT` 默认 120s），开发灌数如需提速配 `*_SEQUENCE_BITS=7`（需清库）。

### 5.8 LLM 治理（爬虫/抽奖链路，非 be-message 本体）

- 所有 LLM 调用共享模块级 `asyncio.Lock`（`TrackedChatOpenAI`），任意时刻只有一个请求打到上游，消除账户级并发超限（429/1302）；锁仅包网络请求，统计在锁外；同步路径无运行 loop 时退化为无锁。
- SQL `1040 Too many connections` 报错补充业务调用栈（`traceback.format_stack()`），便于定位高频协程。

---

## 6. 关键约束与决策（当前有效）

| 编号 | 决策项 | 结论 |
| --- | --- | --- |
| C1 | 存储 | 仅 MySQL（`BiliMessageDB`），**不引入 Redis**；私信按月分库 + 100 表；图片只存 URL |
| C2 | 评论系统归属 | Node 端评论代码与 Postgres 表**就地冻结只读**，新评论全部由 be-message 承担（`/api/v1/comment/*`） |
| C3 | 评论 `type` 白名单 | 后端 `CommentTypeEnum` 为唯一真相源，前端只消费不发明，非法值 422 |
| C4 | IP 处理 | 只存原始 IP 不做属地，出参打码（v4 保留前 2 段 / v6 保留前 2 组），管理员明文 |
| C5 | 对外 ID | 雪花 ID 字符串出参；分钟级短 ID 位布局 39 bits、`sequence_bits` 默认 4 可配（限开发清库环境）；实体独立 worker/epoch |
| C6 | 枚举落库 | VARCHAR/INTEGER 存 value，禁原生 ENUM |
| C7 | 站内信 vs 第三方推送 | 站内信 DB 写路径保证送达，不转第三方；第三方仅「站外提醒」（`/push`） |
| C8 | 通知可见性 | 读时用数据库时钟 `func.now()` 判定 `publish_at`；受众精确过滤在读取侧 |
| C9 | attach 卡 | 只存 `bizType+bizId`，读取时 RPC 实时取详情，禁存快照 |
| C10 | 动态渲染 | 模块化渲染对齐 `DynModuleType`，附加卡独立 `module_additional` 模块 |
| C11 | 响应契约 | HTTP 恒 200，业务码在 body；公共码单一来源 bili-common；未登录恒 `-101` |
| C12 | i18n | bili-common 层 fastapi-i18n + 延迟翻译；前端 vue-i18n + Accept-Language 注入 |
| C13 | RPC 契约 | `bili_common/rpc/` 统一收编；异常边界转 `error_response` 不静默 |
| C14 | seed | 严禁直写 MySQL，统一走 HTTP API；单文件 `seed_cli.py` 唯一入口 |
| C15 | 前端 | Tailwind + Element Plus（禁 style 块/内联/var()）、SVG 图标资源、hey-api SDK 生成不动、先计划书后代码 |

---

## 7. 当前完成度与遗留

### 7.1 已完成（当前现状）

- **消息系统**：通知/事件/私信/设置/推送全链路（Phase A–K），RPC 化（`message.push.rpc.*`）、新建用户发布「欢迎注册」系统通知（同进程直连 `NotifyService.create_idempotent`，仅 `created=True` 时发布）、对外 RPC `publish_notify` 供其它系统发布通知（幂等）、事件 `biz_id` 持久化出参、私信撤回记录/删除互斥、seed CLI 收敛。
- **评论后端**：发布/列表/楼中楼/点赞/置顶/@/通知/DFA 审核/管理端审核队列+明文 IP+统计/热度重算全落地（单测 26 用例通过）；**计数对账已移除**（计数加减同一事务原子 ±1 保证一致，2.46.0）。
- **动态 Moment**：发布/Feed/详情/互动/话题/审核/关注流/空间/收藏夹/泛化互动/EdgeRank/浏览计数等（Phase 1–27）；综合页推荐流对齐 B 站 rcmd（`last_showlist` 去重、无 page/offset，2.32.0）并支持**个性化排序**（关注/互动作者、话题偏好加权，2.33.0）与**匿名随机权重**（2.34.0）；**EdgeRank 多维打分**（互动率/内容丰富度/内容类型/曝光冷启动/点踩反馈/作者质量/分享，2.35.0）；雪花 ID `sequence_bits` 可配（2.31.0）。
- **通用资源 Feed 引擎 + 计数统一**（2.36.0）：`TResourceFeed` 统一 feed 元数据、`TInteractionStat` 扩展全计数、动态计数并入通用互动表（`TMomentStat`/`TMomentViewLog` 废弃，2.46.0 删表落地）、`feed_engine` 适配器模式供任意 `bizType+bizId` 资源复用 EdgeRank 计算/去重/个性化/随机。
- **可见范围 + 候选集多路召回**（2.46.0）：`visibleScope` 启用（WORD 可设、FORWARD 强制 PUBLIC，`TResourceFeed` 冗余落列、推荐流只推 PUBLIC）；`sort=recommend` 候选升级为五路召回（热门趋势/社交关系/内容标签/地理位置/协同过滤近似）并集去重后走 `rank_feed` 精排。
- **互动操作对象化**（2.47.0）：`app/services/interaction_actions/` 新增抽象基类 `BaseInteractionAction`（ABC 模板方法，`_biz_type` 不可变资源类型属性 + 只读 property、`relation_scope` 原子关系权限数组 + 注册表、`acl_scope` **DAC 权限数组** + 注册表（围绕资源展开：`OWNER_ONLY` / `AUDITOR_ONLY`）、`error_messages` 集中报错信息、统一 `check_resource_exists`）、统一资源表示 `InteractionResource`（SQLModel，含 `ownerMid`）与互动操作枚举 `InteractionActionEnum`（LIKE/DISLIKE/FAVORITE/SHARE/REPOST/VIEW/REPORT/AUDIT_APPROVE/AUDIT_REJECT）；按 **全部 6 个 biz_type** 分目录的互动子类，**7 个通用内容型互动（点赞/点踩/收藏/分享/转发/浏览/举报）全部 6 类型完整实现**（非动态「转发」= attach 计数 `ResourceRepostAction`；`dynamic/` 有专属实现），**审核操作对象化**（`dynamic/audit.py` 的 `AuditApproveAction` / `AuditRejectAction`，DAC 审核员权限，迁移原 `MomentAuditService.approve/reject`）；`folder.py` 的 `FavoriteFolderAction` 承载收藏夹管理；`factory.py` 以 `InteractionActionEnum` 为 key 分发；接口层 `/thumb` `/dislike` `/share` `/repost` `/report` `/audit/approve|reject` `/favorite/*` 与浏览 MQ 消费全部直接实例化操作类并把各类 id 赋给初始化属性后调用 `run()`（biz_type 由类声明，无需传参）；**原静态 `MomentInteractionService` / `FavoriteService` 已删除**，逻辑全部收口到对象模型。
- **TMomentStat 废弃收尾**（2.46.0）：唯一残留读取（`api/favorite._get_favorite_count`）统一走 `TInteractionStat`，模型类 / `__init__` 导出 / `moment.py` `__all__` 移除，Alembic 迁移 `c7d8e9f0a1b2` `drop_table TMomentStat`；测试侧 `TMomentStat` 引用（seed/cleanup/级联断言）全部清理，相关过时注释/docstring 同步更新为 `TInteractionStat` 表述。
- **用户中心**：空间信息/资料更新（头像走审核）/登录+经验记录（我的记录）。
- **i18n**：后端 bili-common 5 语言全部落地；前端基础设施 + common/根 views/message 核心/admin（Phase 0–4）完成。
- **数据库表模型文件命名统一（2026-08-29 重构）**：`app/models/db/` 下 16 个表模型文件统一加 `_tbl` 后缀（`admin_tbl.py` / `avatar_audit_tbl.py` / `ban_tbl.py` / `base_tbl.py` / `comment_tbl.py` / `dm_tbl.py` / `event_tbl.py` / `favorite_tbl.py` / `folder_cover_audit_tbl.py` / `follow_tbl.py` / `interaction_tbl.py` / `moment_tbl.py` / `notify_tbl.py` / `report_tbl.py` / `resource_feed_tbl.py` / `setting_tbl.py`），包名 `app.models.db` 与集中导出方式不变；全部 `from app.models.db.<模块>` 直连导入同步更新为 `<模块>_tbl`，Alembic autogenerate 与现有测试无感知（`from app.models.db import Xxx` 写法不受影响）。
- **统一响应码/异常**：bili-common 单一来源 + 各后端接入。
- **回复通知 `biz_id` 收敛为评论 rpid（2.50.0）**：`CommentService._notify_reply` 对 `type_=DYNAMIC` 的评论原先把 `biz_id` 写成**动态 oid**，而 `EventService.list_msgfeed` 是把 `biz_id` 当**评论 rpid** 去查 `CommentIndex` 的，必然 miss，连带三个后果：①`source_id/root_id/target_id/source_content/target_content` 全空 → 回复卡片只有「头像 + 动作 + 时间」，回复正文与「被回复的评论」上下文都不显示（正文只剩 `desc` 一处，前端卡片不读它）；②出参 `source_id` 变成动态 id，前端 `openEventDetail` 当 rpid 去查评论详情 → 深链定位楼层失效；③`dedup_key` 含 `biz_id`，同一个人对同一动态下**不同评论**的多条回复会被判重复而只记一条。改为恒写 `str(rpid)`（`resource_id` 仍由 `idx.oid` 推导出动态 id，`_resolve_source_meta` 的 DYNAMIC 分支只吃 `source_id`，跳转与标题/封面回捞不受影响）。另对**历史行**（`biz_id` 仍是 oid）加兜底：`idx` miss 且 `etype=REPLY` 时 `source_content` 回落事件表 `content`（即回复正文）；前端 `ReplyEventCard` 同步 `sourceContent || desc` 兜底。
- **空间资料聚合统计 + 悬浮卡片常驻缓存（2.51.0，补记）**：`GET /user/space/info` 的 `SpaceInfoResp` 新增两个只读派生字段 `follow_stat`（following_count/follower_count/mutual_count）与 `upstat`（dynamic_count/like_count），路由层在黑名单校验通过后**串行**补查 `FollowService.get_counts` 与 `MomentFeedService.get_upstat` 并内联返回（串行而非 `asyncio.gather`——同一 `AsyncSession` 不支持并发 `await`）。原需 3 次 HTTP + 3 次网关鉴权/黑名单判定的悬浮卡片与空间页降为 1 次；两个原端点 2.52.0 删除。前端新增跨组件共享缓存 `src/composables/useUserCardCache.ts`（详见 §5.3），`MomentSpaceView` 移除 `fetchRelationStat` / `fetchUpStat` 两次独立请求。
- **删除 `/community/upstat` 与 `/message/follow/stat`（2.52.0）**：统计已由 `/user/space/info` 内联返回，两端点无任何调用方（前端薄封装 `fetchUpStat` / `fetchRelationStat` 随之移除）。同时删除 `MomentUpStatResp` 响应模型（由 `SpaceUpStat` 取代）、`FollowCountResp` **保留**（`/message/follow/count` 仍在使用）；`tests/test_str_int_route_params.py` 的 StrInt 回归 URL 列表移除对应两条（保留 `/user/space/info`）。**破坏性变更**：对外端点移除，按本计划书 2.49.0（删除 `/notify/read`）先例记为 MINOR。
- **系统通知「读取即已读」（2.49.0）**：`NotifyService.pull` / `list_for_user`（含 B 站风格 `/notify/system`）在构造完出参后调用内部 `NotifyService._mark_read_ids` 把本页 id 批量 upsert 为已读（幂等）；对外删除 `POST /api/v1/message/notify/read` 与 `NotifyReadResp`，`NotifyReadReq` 因仅剩删除在用更名 `NotifyDeleteReq`；`/notify/list` 移除 `only_unread` 参数。前端 `NotifyListView` 去掉「标记已读 / 全部已读 / 仅看未读」，改为加载完成后 `emit('refreshUnread')` 让红点跟着清零；`message-api.ts` 移除 `markNotifyRead` 与 `NotifyReadResp` 导出。

### 7.2 遗留 / 待办

- **评论前端组件**（`CommentEditor`/`CommentList`/`CommentSubList`/`CommentCard`）：阻塞于前端仓库接入，未实施。
- **回复通知出参对齐 B 站 x/msgfeed/reply**（Phase L）：`EventMsgfeedContent` 补 `subject_id/root_id/source_id/target_id` + 三段评论正文 + `like_state/follow`，list_msgfeed 批量回捞（SQL 次数恒定）。
- **动态审核总统计**（Phase M）：`GET /moment/audit/statistics` 按 dynType+auditStatus 聚合。
- **i18n 前端**：Phase 5–11（rpa-browser views/components、lottery_data、moment、admin、stores/utils 文案）；`generated.ts` 8 处 TS 错误需收尾修复。
- **评论性能**：`EXPLAIN` 覆盖索引验证、深翻页游标分页待补。
- **中台流程**（RPA-Browser 治理层）：审批强制联动（execute/publish 校验 approved 审批单）、举报审核端点、细粒度权限、管理员操作审计表等（P0/P1/P2 阶梯）。
- **前端类型遗留**：moment-api.ts 一批既有类型错误（SDK 更新引入），非计划书范围内。
