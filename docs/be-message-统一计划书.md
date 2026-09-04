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

### 2.10 跳转契约：后端只发「前端路由名」（2026-09-01）

- **禁止后端拼站内路径**：后端下发给前端的跳转目标（`msg_notify.jump_url`、通知正文 `#{文本}{"url"}` 内联链接、`AuditSourceInfo.url`）
  **一律只写前端路由名**，格式 `route:{路由名}?{query}`，如 `route:抽奖卡片详情?id=883000000010&rpid=352279778667008000`。
- **路由名唯一真相源在后端**：`app/models/enums.py::FrontendRouteEnum`（str 枚举，**值 = 前端 `src/router/index.ts` 里路由的 `name`**）。
  新增跳转点 = 先在 `FrontendRouteEnum` 加成员、前端加/改对应路由，**两侧 `name` 对齐**；
  **路径只在前端路由表写一次**，后端不感知、不硬编码任何 `/app/...` 路径（避免路由下线后后端仍发死链）。
- **三类目标**由前端 `src/utils/routeJump.ts::jumpToTarget()` 统一判定：

  | 目标 | 形态 | 前端行为 |
  | --- | --- | --- |
  | 站外 | `http(s)://...` | 新标签页打开（no-referrer） |
  | 站内路由（现行） | `route:{name}?{query}` | `router.push({ name, query })` |
  | 站内路径（存量兼容） | `/app/...` | `router.push(path)`，仅兼容历史数据，**不再新增** |

- **安全兜底**：`app/utils/notify_markup.py::_is_safe_target()` 只放行 `http(s)://` / `/app/` / `route:` + `FrontendRouteEnum` **已注册成员**，
  未知路由名一律降级为纯文本（不渲染成链接）。后端构造统一走 `app/utils/route_target.py::build_route_target()`，禁止手拼 `route:` 字符串。
- 后端正则 `INLINE_LINK_RE` 与前端 `notifyContent.ts` 的解析正则**必须同步**（新增协议形态时两端一起改）。

---

## 3. 数据模型（当前）

### 3.1 MySQL 主库核心表（`BiliMessageDB`）

| 模块 | 表 | 要点 |
| --- | --- | --- |
| 动态 | `TMoment`（dynId 雪花 PK、dynType/auditStatus/content JSON 富文本…，**内容/渲染表**）、`TMomentContent`、`TMomentAudit`、`TMomentAuditLog`（审核流水，**泛化为 `TResourceAuditLog`**：原 `dynId` 列与对 TMoment 的 FK 移除，新增 `bizType(INT)+bizId` 定位任意资源，`operatorMid` 字段名统一为 `mid`，**继承 `ResourceBase`**，见 §3.1.1）、`TMomentLike`（点赞明细）、`TMomentDislike`（点踩明细，**均继承 `ResourceBase`**，移除 `dynId` 列与对 TMoment 的 FK，幂等 `uq(bizType,bizId,mid)`，2.35.0 泛化 → §3.1.1 收口）、`TMomentFavorite`、`TMomentTopic`（topicId 雪花、auditStatus）、`TMomentTopicRel`（多话题关系）、`TResourceFeed`（**通用 feed 元数据表**：`bizType+bizId` 唯一 + mid/pubTime/auditStatus/tags/deletedAt/**visibleScope**（动态冗余可见范围，2.46.0），动态与非动态资源统一入 feed，2.36.0）、`moment_author_quality`（作者质量聚合：平均互动率/近 7 天发布量/违规数，定时任务计算，2.35.0） | 动态正文为富文本节点数组（WORDS/AT/TOPIC/LINK），模块化渲染；**计数统一走 `TInteractionStat`**（2.36.0 起 `TMomentStat`/`TMomentViewLog` 废弃，2.46.0 删表落地） |
| 评论 | `msg_comment_subject`（评论区：oid+type 唯一）、`msg_comment_index`（列表主表：rpid 雪花、root/parent/dialog/floor、hot_score 冗余、state）、`msg_comment_content`（正文/图片/@/IP）、`msg_comment_action`（赞/踩，uq(rpid,mid)）、`msg_comment_at`（@ 关系 + notified 补偿标记）、`msg_user_profile`（用户展示快照） | 三表分离；无 Redis，靠冗余计数 + 覆盖索引 |
| 消息 | `msg_notify`（系统通知，读扩散）、`msg_event`（事件提醒，写扩散 + `dedup_key` 幂等 + `biz_id` 出参）、`msg_dm_index` / `msg_dm_session` / `msg_dm_content`（私信，写扩散 + 正文按月分片 + `recalled_by`）、`msg_user_setting`（消息设置）、`msg_user_activity`（活跃度）、`msg_user_follow`（关注） | 通知读扩散（游标去重）、事件/私信写扩散 |
| 收藏夹 | `TFavoriteFolder`（含 cover_url + 封面审核）、`TFavoriteItem`、`TFolderCoverAudit`（封面审核流水） | 封面 URL 先下载校验后进审核，不直接写库 |
| 用户 | `TUserAvatarAudit`（头像审核：pending/approved/rejected + old/new avatar + 审核人/原因/时间） | 公开头像只存审核通过后的值 |
| 互动 | `TInteractionStat`（**通用互动计数**：like/comment/repost/view/favorite/share/dislike/coin，2.36.0 起动态与非动态统一）、`TInteractionViewLog`（泛化浏览去重） | 全资源统一计数：动态并入 `TInteractionStat`，`TMomentStat` 废弃 |
| 举报 | `TResourceReport`（**通用资源举报**，继承 bili-common `ReportBase`：`pk+bizType+bizId+accusedMid+reportMid+reasonType+...+uq(reportMid,bizType,bizId)`，已被 dynamic/lottery/rpa_*/comment/user 共用，2.37.0） | 举报资源唯一性由 `bizType+bizId` 唯一确定（详见 `.codebuddy/rules/举报资源唯一性.mdc`） |

### 3.1.1 通用资源型表抽象 `ResourceBase`（2026-09-02）

**背景**：`TMomentLike` / `TMomentDislike` 已"半泛化"——支持任意 `bizType+bizId`，但**仍保留 `dynId` 冗余列 + `TMoment.dynId` 的 `CASCADE` FK**，且 `TMomentAuditLog` 完全是动态专属（写死 `dynId`）。这导致：
- 互动明细/审核流水在概念上是"任意资源上的操作"，实现却被绑定到 TMoment，扩展新资源需绕过 `dynId`；
- cleanup 强依赖 `TMoment` CASCADE 自动级联，泛化资源无法走同一套清理；
- 三张子表重复声明 `pk + bizType + bizId + mid + created_at/updated_at` 等公共字段。

**决策**：
1. **新增抽象基类 `ResourceBase`**（`SQLModel`、`table=False`），统一承载"任意业务资源上发生的操作/记录"的公共骨架：
   - `pk: BIGINT autoinc` 主键；
   - `bizType: InteractionBizTypeEnum`（落 `INT`）；
   - `bizId: BIGINT NOT NULL` 资源定位（dynamic 时 = `dynId`）；
   - `mid: BIGINT NOT NULL` 操作者 / 触发者 UID（点赞者 / 点踩者 / 审核操作人 / 举报人等"对该资源施加动作的 mid"）；
   - `created_at / updated_at`（来自 `TimestampMixin`，自动 join）；
   - 抽象类不建表，由各业务子表 `table=True` 继承并 `__tablename__` 起具体表名。
2. **四张子表统一继承 `ResourceBase`**（已通用化 + 移除 `dynId` 列与对 TMoment 的 FK），各自追加业务专属字段；**类名/表名同步改为 `TResource*` 前缀**（与既有 `TResourceReport` / `TResourceFeed` 同前缀语义统一）：
   - `TResourceLike`（**原 `TMomentLike` → `TResourceLike`**）：`likeType`（点赞类型，预留扩展）；
   - `TResourceDislike`（**原 `TMomentDislike` → `TResourceDislike`**）：仅继承，无专属字段；
   - `TResourceFavorite`（**原 `TMomentFavorite` → `TResourceFavorite`**，收藏明细）：`folderId(BIGINT NOT NULL)`（所属收藏夹 id，favorite 特有字段）、`note(VARCHAR(200) NULL)`（收藏备注，预留）。**唯一约束仍是 `(bizType, bizId, folderId)`**——语义是"同夹内不重复收藏"，与 `ResourceBase` 默认的 `(bizType, bizId, mid)` 不同，由 favorite 表显式覆盖。
   - `TResourceAuditLog`（**原 `TMomentAuditLog` → `TResourceAuditLog`**，承担任何资源的审核流水；**保留** `MomentAuditLogActionEnum` / `MomentAuditLogOperatorRoleEnum` 与现有动作语义 `CREATE/EDIT/DELETE/APPROVE/REJECT/RESUBMIT`）：`operatorRole(from AUTHOR/ADMIN)`、`fromStatus/toStatus`、`actionType`、`rejectReason/remark/clientIp/userAgent`。
3. **`TResourceReport` 不动**：已是终点态（继承 bili-common `ReportBase`，含 `accusedMid/reportMid/reasonType/...`），与 `ResourceBase` 抽象同源（都强调 `bizType+bizId` 定位），但因业务字段集（reasonType/pics/auditStatus）差异大，**不复用** `ResourceBase`，避免强行合并破坏 `ReportBaseService` 既有契约。
4. **物理表迁移**：RENAME `TMomentLike → TResourceLike`、`TMomentDislike → TResourceDislike`、`TMomentFavorite → TResourceFavorite`、`TMomentAuditLog → TResourceAuditLog`；删 `dynId` 列及对应 FK。**用户手动改库**（详见本节末尾"手动改库 DDL 提示"）。

**目标字段结构**（用户改库对照）：

| 子表 | 列（含继承自 `ResourceBase` 的列，加粗为 base 字段） | 约束 / 索引 |
| --- | --- | --- |
| `TResourceLike`（原 `TMomentLike`） | **pk, bizType(INT), bizId, mid, created_at, updated_at**, `likeType` | `PK(pk)`; `uq(bizType,bizId,mid)`; `idx(mid,created_at DESC)`; `idx(bizType,bizId)` |
| `TResourceDislike`（原 `TMomentDislike`） | **pk, bizType, bizId, mid, created_at, updated_at** | `PK(pk)`; `uq(bizType,bizId,mid)`; `idx(mid,created_at DESC)`; `idx(bizType,bizId)` |
| `TResourceFavorite`（原 `TMomentFavorite`） | **pk, bizType, bizId, mid, created_at, updated_at**, `folderId(BIGINT NOT NULL)`, `note(VARCHAR(200) NULL)` | `PK(pk)`; `uq(bizType,bizId,folderId)`（同夹内不重复）; `idx(mid,created_at DESC)`; `idx(folderId,created_at DESC)`; `idx(bizType,bizId)` |
| `TResourceAuditLog`（原 `TMomentAuditLog`） | **pk, bizType, bizId, mid, created_at, updated_at**, `operatorRole(ENUM)`, `fromStatus(ENUM NULL)`, `toStatus(ENUM)`, `actionType(ENUM)`, `rejectReason`, `remark`, `clientIp`, `userAgent` | `PK(pk)`; `idx(bizType,bizId,created_at DESC)`; `idx(mid,created_at DESC)`; `idx(actionType,created_at DESC)` |

**引用影响（必同步调整代码，否则运行报错）**：
- `app/models/db/moment_tbl.py`：`TMomentLike → TResourceLike`、`TMomentDislike → TResourceDislike`、`TMomentAuditLog → TResourceAuditLog` 三类**同时改类名与表名**（`__tablename__`、PK 名、唯一约束名、索引名同步改为新名）。`__all__` 导出同步。
- `app/models/db/favorite_tbl.py`：`TMomentFavorite → TResourceFavorite` 类与表名同步改，**继承 `ResourceBase`**（去掉显式 `mid` 字段、删 `dynId` 冗余列），保留 favorite 特有的 `folderId` / `note` 字段与唯一约束 `(bizType, bizId, folderId)`。
- `app/models/db/favorite_tbl.py`：`TMomentFavorite → TResourceFavorite` 类与表名同步改，**继承 `ResourceBase`**（去掉显式 `mid` 字段、删 `dynId` 冗余列），保留 favorite 特有的 `folderId` / `note` 字段与唯一约束 `(bizType, bizId, folderId)`。
- `app/models/db/__init__.py`：导入与 `__all__` 导出全部同步新名。
- `services/moment/moment_audit.py`：`_build_audit_log` 加 `biz_type` / `biz_id` 入参，写 `TResourceAuditLog(bizType=..., bizId=..., mid=operator_mid, ...)`；`MomentAuditService.log_list` 改 `biz_type + biz_id` 替代 `dyn_id` 过滤；`MomentAuditService.detail` 改为 `(biz_type=DYNAMIC, biz_id=moment_id)` 过滤；`MomentAuditLogItem` schema **保留旧字段 `dynId/operatorMid`**（值分别取 `bizId`/`mid`，前端契约不变）。
- `services/moment/moment_publish.py` / `_create_word / _create_forward / edit / remove / repost`：作者侧 AuditLog 写入由 `moment_id` → `(biz_type=DYNAMIC, biz_id=moment_id)`。
- `services/interaction_actions/common/ops.py`：`do_like_dynamic / do_like_generic / do_dislike / do_favorite / do_unfavorite` 移除 `dynId=...` 入参（dynamic 分支不再写冗余列，统一通过 `bizId` 定位）；类引用改 `TResourceLike`/`TResourceDislike`/`TResourceFavorite`。
- `services/interaction_actions/dynamic/biz.py`：`DynamicBiz.dislike` 移除 `dynId=self.biz_id`；`DynamicBiz.audit_approve/audit_reject` 调用 `_build_audit_log` 时传 `biz_type=DYNAMIC, biz_id=self.biz_id`；类引用 `TMomentDislike → TResourceDislike`。
- `services/moment/moment_feed.py` / `feed_engine.py` / `api/moment.py`：所有 `TMomentLike` 引用改 `TResourceLike`；查询统一加 `bizType=DYNAMIC` 过滤。
- `services/cleanup/cleanup_moment.py` / `cleanup_favorite.py`：删除 `TResourceLike/TResourceDislike/TResourceFavorite/TResourceAuditLog` 改为**显式按 `(bizType=DYNAMIC, bizId IN dyn_ids)` 删**——`TMoment` CASCADE 自动清理不再有效（已去 FK）。`TResourceFavorite` 仍按 `mid == uid` 一并清（一个用户全删）。
- `tests/test_moment_*` / `tests/test_report.py` / `tests/test_edgerank.py` 等：导入类名 + 硬编码 `dynId=` 的 SQL 断言改 `bizType=DYNAMIC AND bizId=` + 新表名。
- `app/models/enums.py`：保留 `MomentAuditLogActionEnum` / `MomentAuditLogOperatorRoleEnum`（值不变），注释更新为"通用资源审核日志枚举"。
- **API 契约保持**：`audit_history` 入参仍 `dynId + operatorMid`；`MomentAuditLogItem` 出参仍 `dynId/operatorMid`（值映射自 `bizId`/`mid`）。前端无需改。

**手动改库 DDL 提示**（用户手动执行；alembic 不升级；dev 无生产数据可走 DROP+CREATE 最短路径）：
```sql
-- ============================================================
-- 阶段 A：删旧四张表（dev 阶段无生产数据，直接 DROP 重建）
-- ============================================================
DROP TABLE IF EXISTS TMomentLike;
DROP TABLE IF EXISTS TMomentDislike;
DROP TABLE IF EXISTS TMomentFavorite;
DROP TABLE IF EXISTS TMomentAuditLog;

-- ============================================================
-- 阶段 B：建新四张表（继承 ResourceBase：pk + bizType + bizId + mid + 时间戳）
-- ============================================================

-- 1) 通用资源点赞明细（TResourceLike，原 TMomentLike）
CREATE TABLE TResourceLike (
  pk           BIGINT PRIMARY KEY AUTO_INCREMENT,
  bizType      INT NOT NULL,                       -- InteractionBizTypeEnum 值
  bizId        BIGINT NOT NULL,
  mid          BIGINT NOT NULL,                    -- 操作者 UID
  likeType     INT NOT NULL DEFAULT 1,             -- 1=普通点赞（预留扩展）
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY TResourceLike_bizType_bizId_mid_key (bizType, bizId, mid),
  KEY idx_resource_like_mid_time (mid, created_at DESC),
  KEY idx_resource_like_biz (bizType, bizId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='通用资源点赞明细：一人一赞，继承 ResourceBase，唯一约束(bizType,bizId,mid)保证幂等双写；原 TMomentLike';

-- 2) 通用资源点踩明细（TResourceDislike，原 TMomentDislike）
CREATE TABLE TResourceDislike (
  pk           BIGINT PRIMARY KEY AUTO_INCREMENT,
  bizType      INT NOT NULL,
  bizId        BIGINT NOT NULL,
  mid          BIGINT NOT NULL,
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY TResourceDislike_bizType_bizId_mid_key (bizType, bizId, mid),
  KEY idx_resource_dislike_mid_time (mid, created_at DESC),
  KEY idx_resource_dislike_biz (bizType, bizId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='通用资源点踩明细：一人一踩，继承 ResourceBase，唯一约束(bizType,bizId,mid)保证幂等双写；原 TMomentDislike';

-- 3) 通用资源收藏明细（TResourceFavorite，原 TMomentFavorite）
--    唯一约束改为 (bizType, bizId, folderId)：同夹内不重复收藏
CREATE TABLE TResourceFavorite (
  pk           BIGINT PRIMARY KEY AUTO_INCREMENT,
  bizType      INT NOT NULL,                       -- InteractionBizTypeEnum 值
  bizId        BIGINT NOT NULL,                    -- 被收藏资源 id（dynamic 时 = dynId）
  mid          BIGINT NOT NULL,                    -- 收藏者 UID
  folderId     BIGINT NOT NULL,                    -- 所属收藏夹 id（雪花 ID）
  note         VARCHAR(200) NULL,                  -- 收藏备注（预留）
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY TResourceFavorite_bizType_bizId_folderId_key (bizType, bizId, folderId),
  KEY idx_resource_favorite_mid_created (mid, created_at DESC),
  KEY idx_resource_favorite_folder_created (folderId, created_at DESC),
  KEY idx_resource_favorite_biz (bizType, bizId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='通用资源收藏明细：同夹内唯一约束(bizType,bizId,folderId)防重复收藏；继承 ResourceBase；原 TMomentFavorite';

-- 4) 通用资源审核流水（TResourceAuditLog，原 TMomentAuditLog）
CREATE TABLE TResourceAuditLog (
  pk           BIGINT PRIMARY KEY AUTO_INCREMENT,
  bizType      INT NOT NULL,                       -- InteractionBizTypeEnum 值
  bizId        BIGINT NOT NULL,
  mid          BIGINT NOT NULL,                    -- 原 operatorMid 改名
  operatorRole VARCHAR(16) NOT NULL,               -- AUTHOR / ADMIN（保持原枚举名）
  fromStatus   VARCHAR(16) NULL,
  toStatus     VARCHAR(16) NOT NULL,
  actionType   VARCHAR(16) NOT NULL,                -- CREATE/EDIT/DELETE/APPROVE/REJECT/RESUBMIT
  rejectReason VARCHAR(500) NULL,
  remark       VARCHAR(500) NULL,
  clientIp     VARCHAR(64) NULL,
  userAgent    VARCHAR(512) NULL,
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  KEY idx_res_audit_biz (bizType, bizId, created_at DESC),
  KEY idx_res_audit_mid (mid, created_at DESC),
  KEY idx_res_audit_action (actionType, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='通用资源审核流水：bizType+bizId 定位任意资源（继承 ResourceBase）；原 TMomentAuditLog';

-- ============================================================
-- 阶段 C（可选）：如有外站/生产数据需保留，按下表执行迁移
--   1) ALTER TABLE TMomentAuditLog DROP FOREIGN KEY TMomentAuditLog_dynId_fkey;  -- 旧 FK
--   2) 按"先建新表 → INSERT...SELECT → DROP 旧表"做数据迁移（字段映射见上）
-- ============================================================
```


`TUserInfo`（uid/role）、`TUserDetail`（uname/sign/sex/birthday/**avatar 对外公开头像**）、`TUserLevel`（current_level）、`TUserVip`、`TUserActInfoLog`（登录记录：act_info=`login_succ`/`daily_login`/`reg`）、`TUserExpRecord`（经验记录，`ExpActionType`）。

---

## 4. API 总览（当前已上线，按功能域）

> 统一前缀 `/api/v1`，响应 `{code,msg,data}`，64 位 ID 字符串出参。

### 4.1 动态 Moment（`/api/v1/community`，2.41.0 由 `/api/v1/moment` 更名）

- **发布**：`POST /create`（scene=WORD/FORWARD、content 富文本、attach?{bizType,bizId}、repostSrc、topics?[]、lbs、option{closeComment?、**visibleScope?**}）→ 创建即 `auditing`；**visibleScope 仅 WORD 可设（缺省 PUBLIC，非法值 422）、FORWARD 一律强制 PUBLIC（服务端忽略传入值，2.46.0）**；`POST /remove`（作者本人软删）；`POST /admin/remove`（root 删任意动态）；`POST /repost`（源须 normal）；`POST /space/top|untop`；`POST /create/check`（发布页预校验）。**每日 WORD 创建上限（`moment_daily_create_limit`，超限回 4102）见 §5.15；`POST /edit` 已移除（2.58.0，§5.16）。**
- **Feed**：`GET /feed/all`（综合页，**recommend 推荐流模式（默认，对齐 B 站 `/x/web-interface/wbi/index/top/feed/rcmd`）**：无 page/offset 游标，请求带 `last_showlist`（逗号分隔已展示 dynId，服务端去重）、`ps`（单页条数）、`last_clicklist`（已互动，预留反馈）、`fresh_idx`/`fresh_idx_1h`/`uniq_id`（刷新/客户端标识）；登录用户按关注/互动历史**个性化排序**（2.33.0，未登录为全局排序）；`sort=time` 最新模式保留 `historyOffset` 游标）、`GET /feed/space/{mid}`（本人见全部状态、访客仅 normal）、`GET /feed/topic/{topicId}`、`GET /feed/following`（关注流，须登录）；`GET /detail/{dynId}`、`POST /details`（批量，限 20）。
- **互动（2.56.0 全面通用化，§5.13）**：`POST /thumb`（点赞/取消，幂等）、`POST /dislike`（点踩/取消，幂等，2.35.0）、`POST /share`（分享计数 +1，2.35.0）、`POST /report`（举报，不改 auditStatus）——**四个写接口一律以 `bizType`（缺省 `dynamic`）+ `bizId` 唯一定位资源**（2.56.0 去除 `dynId` 别名，动态资源也一律传 `bizId`），经 `get_biz()` 取资源实例调用 `like()` / `dislike()` / `share()` / `report()`，支持 dynamic / lottery / rpa_* 全部资源；响应统一带 `bizType` / `bizId` / `bizIdStr`。`POST /repost` 仍为动态专属（转发 = 创建 FORWARD 动态，语义使然）。
- **互动态查询**：`GET /interaction/status`（批量态，防乱调校验资源存在）、`GET /interaction/status/{bizId}`（detail 专用，触发浏览计数；2.42.0 起浏览明细每用户每资源一行、`lastViewAt` 判自然日窗口）——**2.60.0 起匿名可读（§5.18）**：依赖降为 `OptionalUser`，匿名时 `viewer_mid=0`（`isLike`/`isFavorite` 恒 false、计数照常返回），**浏览 MQ 仍仅登录用户投递**。统一举报另有独立域 `POST /api/v1/report`（2.41.0 网关 `/api/v1/` 通配后恢复）。
- **话题**：`GET /topic/square` / `/topic/hot-search`（EdgeRank 排序，仅 normal）、`/topic/mine`、`POST /topic/create`（创建即 auditing）；`GET /at/list|search`、`GET /poi/nearby|search`。
- **空间/用户**：`GET /user/space/info`（对标 B 站 acc/info，**2.51.0 起内联 `follow_stat`{following_count/follower_count/mutual_count} + `upstat`{dynamic_count/like_count} 聚合统计**，空间页 / 悬浮用户卡片只需这一次请求）、`GET /user/user_info/update`（**avatar 走审核流程**，返回 `avatar_status`）。
  - **已删除（2.52.0）**：`GET /community/upstat`、`GET /message/follow/stat` —— 统计已由 `/user/space/info` 内联返回（**且这两个端点未进网关匿名白名单，未登录访问恒返回 `-101`，前端从未真正取到过数据**）；服务层 `MomentFeedService.get_upstat` / `FollowService.get_counts` 仍被 `/user/space/info` 复用，保留；响应模型 `MomentUpStatResp` 随端点一并删除（`SpaceUpStat` / `SpaceFollowStat` 取代）。

### 4.2 评论（`/api/v1/comment`）

`POST /add`（正文 @ 占位、图片 ≤9 白名单、10s 内 ≤3 次防刷、**每日创建上限 `comment_daily_create_limit`，超限回 4101，见 §5.15**）、`POST /del`、`GET /main`（hot/time 排序、内嵌 3 条楼中楼、作者可见本人 auditing）、`GET /reply`（楼中楼分页）、`GET /detail/{rpid}`、`GET /count`、`POST /action`（赞/踩/取消，幂等）、`GET /at/search`、`POST /top`（置顶）、`POST /report`（举报，达阈值仅加入审核队列，2.40.0）。`type` 白名单（`dynamic/article/lottery/feedback/other`）后端唯一真相源，非法值 422。

### 4.3 消息（`/api/v1/message`）

- 通知：`/notify/pull|list|unread|system|delete`、`/notify/admin/create|update|revoke|list`（受众 ALL/CUSTOM/LEVEL/ROLE/VIP）。**读取即自动已读（2.49.0）**：`/pull` / `/list` / `/system` 在返回前把本页命中的通知批量置为已读，`POST /notify/read` 已删除。
- 事件：`/event/report|aggregate|list|read|delete|unread`（like/reply/at 三类，`biz_id` 出参支持跳转）。
- 私信：`/dm/send|sessions|session/delete|session/top|messages|delete|recall|ack|unread`（撤回记录 `recalled_by`、删除后不可撤回、`content_ready` 兜底；**发送含每日上限 + 陌生人单条闸门限制**，见 §5.14；**会话置顶 `top_ts`** 见 §5.17）。
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
- `interaction_actions/`（通用互动操作对象模型，跨 bizType 通用，**不属于 moment 域**，直接置于 `services/` 下）：`base.py`（权限原语）/ `base_biz.py`（`BaseBiz` 资源基类 + `get_biz` 入口 + `@biz_action` 权限装饰器）/ `resources.py`（汇总导入，触发继承即登记）/ `folder.py`（收藏夹管理）/ `common/`（`ops.py` 共享操作 + `generic_biz.py` 通用资源基类）/ `<resource>/`（每个资源一个 `biz.py`，如 dynamic/lottery/rpa_action/rpa_browser/rpa_plugin/rpa_workflow/comment/user）
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
    **2.62.0 补充**：本条仅覆盖「点踩 → 对所有人略降」；「点踩 → 对点踩者本人大幅降权」不在本公式内，
    而是在 `feed_engine` 精排后处理（`s' = s·scale − weight`，详见 §5.20），保证算法层保持无 IO 纯函数。
  - 评论深度以评论系统 `root_count`（已有 comment 加权）近似，不单独建库。
  - **时间衰减基准改用最近活跃时间（2.43.0）**：EdgeRank 时间衰减 `decay(age)` 的 `age` 基准由**仅发布时间 `pubTime`** 改为 **`max(pubTime, 最后评论时间)`**——「最后评论时间」取评论系统 `CommentSubject.updated_at`（该字段含 `onupdate`，评论新增/删除时自动刷新，即最后评论活跃时间；无评论动态无 `CommentSubject` 行、`updated_at` 缺失，回退为 `pubTime`）。使持续被评论的动态保持新鲜度、衰减更慢，避免「刚发但早已无人评论」的动态排在「刚被热议但发得早」的动态之前。开关 `edgerank_decay_use_last_activity`（默认 true），由 `feed_engine` 将 `last_activity_time` 经 `extra` 注入算法层；`compute_moment_score` 从 `extra["last_activity_time"]` 读取衰减基准，算法层保持数据驱动、与配置解耦。
  - **`rank_feed` 增强入参 SQLModel 化（2.44.0）**：推荐引擎增强信号入参弃用模糊的原始 dict/tuple 类型，统一改为 SQLModel 实体——作者质量 `{mid: MomentAuthorQuality}`（直传实体，弃 `(avgEngagement, recentPublish, fansCount, currentLevel)` 元组）；pending 举报数 `{biz_id: ResourceReportCount}`（新增 `ResourceReportCount{biz_id, pending_count}` DTO 承载聚合结果）；评论信号合并原 `comment_override`（实时计数）与 `comment_activity_at`（最后评论时间）为单一 `{biz_id: CommentSubject}`（`root_count` + `updated_at` 同源单次查询，删除冗余双查询）。话题 hot 排序路径同步适配。
  - **`EdgeRank`/`feed_engine` 内部数据结构 SQLModel 化（2.45.0）**：`edgerank.build_anon_profile` 弃用 `model_dump()`→dict 扰动→`model_validate()` 的 dict 中间态，改为 `FEED_PROFILE.model_copy()` + 权重字段直接赋值（自始至终保持 `EdgeRankProfile` 实例，不经 dict 中转）；`_profile_from_settings` 直接以关键字构造 `EdgeRankProfile`（dict 仅作为 pydantic-settings JSON 配置的桥接保留，不扩散到算法内部）。`feed_engine.rank_feed` / `_extra` 的 `{id: Entity}` 索引映射（`counts: {biz_id: TInteractionStat}` / `author_quality: {mid: MomentAuthorQuality}` / `report_counts: {biz_id: ResourceReportCount}` / `comment_subjects: {biz_id: CommentSubject}`）为**批量查询结果索引**（一次 IN 查询后按 id 点查，避免 N+1），保留 dict 语义，值一律为 SQLModel 实体。`tests/test_edgerank.py` 同步弃用旧 dict 传参（`extra={...}`、`profile.weights`/`weight(k)` 属性），改为 `EdgeRankExtra` 实例与字段访问。
- **计数范式**：高频计数走「明细表 + 原子 ±1」（禁 COUNT 扫描）；低频统计（用户空间聚合统计：`/user/space/info` 的 `follow_stat` / `upstat`，2.51.0 起随空间资料一次返回）允许聚合。评论/动态热度用冗余列排序。
- **通用资源 Feed 引擎（2.36.0）**：Feed 计算收口到 `feed_engine`（`FeedProvider` 适配器模式）——任意 `bizType+bizId` 资源经适配器提供候选（`{bizType, bizId, mid, pubTime, tags}`）与计数（`TInteractionStat` + `CommentSubject`），引擎统一执行 EdgeRank 打分（含 2.35.0 全量维度）/ 个性化 / 匿名随机 / `last_showlist` 去重 / 分页；动态与非动态资源共用一套计算。动态 provider 渲染回 `TMoment` 内容模块；其他资源走 RPC 详情。
- **计数统一（2.36.0，消除双轨）**：`TInteractionStat` 扩展 comment/repost/share/dislike/coin 全计数，动态互动（点赞/点踩/分享/转发/浏览/评论）全部并入 `TInteractionStat`（`bizType=dynamic` 行），`TMomentStat`/`TMomentViewLog` 废弃（**2.46.0 删表落地**）；浏览去重统一 `TInteractionViewLog`（**2.42.0 每用户每资源一行**，唯一约束 bizType+bizId+mid，`lastViewAt` 判自然日窗口、跨天访问才给 Stat +1），点赞/点踩明细统一 `TMomentLike`/`TMomentDislike`（已泛化）。
- **举报反馈通用化（2.37.0，方案 A）**：举报 `bizType` 直接复用 `InteractionBizTypeEnum` 值（业务资源类型即举报来源类型：dynamic/lottery/rpa_*/comment/user），`bizType+bizId` 唯一确定被举报资源——废弃原 `ReportBizTypeEnum`（dynamic/comment/user/resource 分流）+ 冗余 `resourceType` 字段。举报 API `ReportCreateReq` 仅保留 `bizType`+`bizId`。EdgeRank 附加维度 `report_count`（按 `bizType+bizId` 统计 pending 举报数）降权，**全资源通用**（非动态资源不再恒 0）。**举报表更名 `TMomentReport → TResourceReport`**（动态专属 FK 移除，任意资源可举报，2.37.0）。
- **作者粉丝/等级维度（2.37.0）**：`moment_author_quality` 扩展 `fansCount`（≈ 被关注数，`msg_user_follow` 按 `target_mid` COUNT，不跨库）+ `currentLevel`（pptr `PptrUserLevel.current_level` 回查）；定时任务低频聚合。EdgeRank 附加维度 `fans`/`level`：`+ w_fans·log(1+fans) + w_level·level`。
- **无作者资源兼容（2.37.0）**：`TResourceFeed.mid` 允许 NULL——lottery/rpa_* 等资源可能无作者；引擎 `FeedCandidate.mid` 为 `int | None`，作者维度（`moment_author_quality` / `msg_user_follow` 关注信号）在无作者资源上**自动跳过**（`mid=None` 不命中任何信号，不参与作者质量/关注 boost），不崩溃不误加权。
- **举报资源处置（2.38.0）**：管理端审核举报 `resolve` 时可选 `resourceAction=hide` 联动处置被举报资源——动态（`bizType=dynamic`）：`TMoment.auditStatus → hidden`（管理员下架）+ `TResourceFeed.auditStatus='hidden'`（退出 Feed）；评论（`bizType=comment`）：`CommentIndex.state → hidden`；用户（`bizType=user`）预留。**下架后若资源有作者（mid 非空）发 `HIDE` 站内事件通知作者**（`EventTypeEnum.HIDE`，弱依赖独立会话，失败不阻塞处置）。
- **通用资源举报与跨项目处置（2.39.0）**：lottery/rpa_* 资源以各自 `InteractionBizTypeEnum`（`lottery`/`rpa_action`/`rpa_workflow`/`rpa_browser`/`rpa_plugin`）作为 `bizType` 直接举报，落 `TResourceReport`（与 dynamic 同表，原 `ReportBizTypeEnum.RESOURCE="resource"` 分流 + `resourceType` 字段已废弃）。处置（`resourceAction=hide`）为**双层**：
  1. **Feed 层（be-message 本地，立即可控）**：`TResourceFeed.auditStatus='hidden'`，被举报资源**立即退出 Feed**，与归属服务可用性无关；
  2. **资源层（RPC，弱依赖）**：RPC 契约 `message.rpa.rpc.hide_resource`（`HideResourceParams{bizType,bizId,operatorMid,reason}`），be-message 作为客户端调用**归属服务**（RPA-Browser 按 bizType 内部路由：lottery→be-bilibili-crawler、rpa_*→本地），资源实际下架/停用；RPC 超时/失败仅告警降级（Feed 层已生效）。
  归属服务需实现 `hide_resource` 服务端（跨仓库跟进）：**rpa_* 已在 RPA-Browser 落地**（`app/services/mq/rpc_server.py::rpc_hide_resource`，对 rpa_action/rpa_workflow/rpa_plugin 置 `is_public=False` 退出社区；rpa_browser 为运行态实例无下架语义，返回不支持），lottery 仍归属 be-bilibili-crawler 项目待跟进。同步清理：RPA-Browser 侧社区互动/举报已统一迁移 be-message，`community_router` / `community_crud` / 本地 `admin/report_router` 及 `ResourceReport` 表等本地实现已删除（前端社区广场数据源后续另议）。
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

- **话题 Feed 重新实现（参考动态综合页，承接 2.46.0 召回 + 精排两段式）**：`GET /feed/topic/{topicId}`（实现 `P5-T2`）从「直接查 `TMoment` + 内存 hot 重排」升级为与综合页 `comprehensive_feed` **同一套召回 + 精排管线**，服务抽离为 `app/services/moment/topic_feed.py` 的 `TopicFeedService`，API 层改为调用之：
  - **候选统一从 `TResourceFeed` 召回**（bizType=dynamic，normal + PUBLIC + 未软删 + pubTime 非空）；话题范围由「`TMoment.topicId = ?` ∪ `TMomentTopicRel.topicId = ?`」得到该话题动态 bizId 集合后 `bizId IN (...)` 过滤（**不依赖 `TResourceFeed.tags` JSON 包含查询**，与 2.22.0 双条件查询一致；`tags` 仍仅用于个性化信号），候选上限 `edgerank_candidate_limit`；
  - **精排统一走 `rank_feed` 通用引擎**（`feed_engine.rank_feed` 新增可选 `profile` 参数，话题 Feed 传 `TOPIC_FEED_PROFILE`：评论 1.8 / 转发 1.5 / 点赞 1.2 / 半衰期 6h）：`sort=recommend`（**默认**，与综合页一致）支持 `last_showlist` 去重、未登录匿名随机排序（`build_anon_profile` 以 `TOPIC_FEED_PROFILE` 为基、不再硬编码 `FEED_PROFILE`）、登录个性化（关注/互动作者 boost，复用 `load_personal_signals`）；`hasMore` = 排除已展示后候选仍有剩余；`sort=time` 保留 pubTime 倒序 + `historyOffset` 游标；`sort=hot` 作为 `recommend` 的兼容别名保留；
  - **不新增 `bizType=topic` 资源类型**：话题 Feed 展示的是「话题下的动态」（动态已是 `TResourceFeed` 资源且携带话题 id），只需在动态候选召回阶段按话题过滤即可复用同一引擎；`rank_feed` 本就资源无关（`FeedCandidate`），「edgerank 引擎处理所有资源」已成立（指定 Profile 即可）；话题广场（列话题本身）走 `compute_topic_score` / `TOPIC_SQUARE_PROFILE`，语义不同，不并入 `rank_feed`；
  - 装配复用 `moment_feed` 的 `_build_feed_item` / `_attach_authors` / `_attach_topics` / `_load_stats` / `_load_like_states` / `_load_comment_subjects` / `_build_lottery_detail_map` / `_load_topic_rel_map` / `_assemble_page`（无 N+1）。

- **Feed 引擎通用化 + 曝光去重（承接 2.47.0）**：`app/services/moment/feed_engine.py`：
  - **互动状态特征全量入模（通用化）**：`TInteractionStat` 的 like / comment / repost / **favorite / share / coin** / view / dislike **全部**参与特征构造（此前 `_extra` 只取 like/comment/repost/view/dislike，favorite/share/coin 被浪费）；特征构造收敛为「纯 stat 驱动」的 `build_extra_from_stat`（无资源类型分支），资源特有信号（内容丰富度 / 是否转发 / 作者质量）一律由 Provider 以通用结构注入；
  - **去除动态专属耦合**：引擎不再 import 动态专属表 `MomentAuthorQuality`（`moment_author_quality`），改为通用 `AuthorQualitySignal`（`avg_engagement` / `recent_publish` / `fans` / `level`），由 Provider（动态 Feed / 话题 Feed）映射后传入——引擎自此对 `bizType` 完全无感知；
  - **曝光去重（新增表 `TFeedImpression`）**：`uq(viewerKey, bizType, bizId, feedScene)` + `idx(viewerKey, feedScene, lastImpressionAt DESC)`；`viewerKey` = `mid:{mid}`（登录）/ `anon:{uniq_id}`（匿名且无 `uniq_id` 则跳过）；`feedScene` = `comprehensive` / `topic`；TTL 窗口 `edgerank_dedup_impression_ttl_hours`（默认 24h）内已下发资源不再重复下发；每次下发后批量 upsert 曝光记录（单条 `INSERT ... ON DUPLICATE KEY UPDATE`）；**不查 `TInteractionViewLog`**（该表语义为浏览计数去重，与曝光解耦，且少一次查询）；
  - **尽力去重 + 自动降级**：过滤优先级 `last_showlist` ∪ 曝光记录 → 候选不足一页时**逐级放宽**（先去掉曝光过滤只按 `last_showlist`；仍不足则不做任何去重），**保证 feed 永不因去重见底**；`hasMore` = 放宽后剩余候选 > `page_size`；`settings.edgerank_dedup_enabled=False` 时退化为原纯 `last_showlist` 行为。

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
  - **互动操作枚举 `InteractionActionEnum`**（`base.py`）：枚举通用内容型互动全集 `LIKE / DISLIKE / FAVORITE / SHARE / REPOST / VIEW / REPORT / AUDIT_APPROVE / AUDIT_REJECT`，作为 `InteractionActionTypeEnum` 的成员（2.48.0 合并）；工厂映射表已移除，资源按 `BaseBiz` 子类声明方法，详见 §5.10；
  - **工厂分发（补全通用互动表）**：`interaction_actions/factory.py` 用 `InteractionActionEnum` 作 key，补全 **7 个通用内容型互动（点赞 / 点踩 / 收藏 / 分享 / 转发 / 浏览 / 举报）在全部 6 个 biz_type 的实现**（非动态经 `common/` 的 `ResourceLikeAction` / `ResourceDislikeAction` / `ResourceFavoriteAction` / `ResourceShareAction` / `ResourceRepostAction` / `ResourceViewAction` / `ResourceReportAction`）——**非动态「转发」= attach 行为计数**（`ResourceRepostAction` 复用 `TInteractionStat.repostCount` 记录 attach 次数）；**审核操作（`AUDIT_APPROVE` / `AUDIT_REJECT`）**为 DAC 审核员操作，当前仅动态已对象化（`dynamic/audit.py` 的 `AuditApproveAction` / `AuditRejectAction`，迁移原 `MomentAuditService.approve/reject`），其余类型待接入对应审核服务后补全；提供 `get_action` / `get_like_action` / `get_favorite_action` / `get_view_action`，按资源类型返回对应操作类（每个类自带 `_biz_type`）；`/thumb` `/favorite/add|remove` 与浏览 MQ 消费等通用入口均经工厂分发（2.48.0 起工厂分发改用 `get_biz(biz_type, ...)` 资源方法，详见 §5.10 `BaseBiz` 类体系）；
  - **收藏夹管理对象化**：原静态 `FavoriteService` 的收藏夹管理（创建 / 更新 / 删除 / 列表 / 收藏明细 / 主页可见性设置 / 他人公开读 / 默认夹 get_or_create）迁移为 `interaction_actions/folder.py` 的 `FavoriteFolderAction(session, actor_mid)`（用户维度操作类，方法即操作）；
  - **接口层调用方式**：直接实例化对应操作类（从 `interaction_actions` 或对应子包导入），把 `actor_mid / biz_id / dyn_id / folder_id / up / action / reasonType` 等各类 id 赋给 `__init__` 属性（`biz_type` 由类声明），调用 `await get_biz(biz_type, session, biz_id, actor_mid).like(up=1)` 等资源方法即可；`/thumb` `/dislike` `/share` `/repost` `/report` `/favorite/add|remove` 与浏览 MQ 消费（`consumers/interaction_view.py`）均经 `get_biz()` 取资源实例调用方法（无需工厂分发）；**原静态 `MomentInteractionService` / `FavoriteService` 已整体删除**，逻辑全部收口到 `BaseBiz` 资源类，收藏夹管理经 `FavoriteFolderAction`，测试改为直接取资源实例调用方法。

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
- **`--dry-run` 覆盖全互动阶段（2.53.0）**：原先 `--dry-run` 只在阶段二（大数据灌数 `run_bulk`）短路，阶段一 `_run_full` **完全不检查该参数**——help 与文档都写着「只打印计划，不调用接口」，实际却直接开始往 MySQL 主库写动态 / 评论 / 私信 / 关注关系，只能靠 Ctrl-C 中断且已落库数据无法回滚。现 `_run_full` 在**任何接口调用之前**检查 `args.dry_run`，打印阶段一计划（动态条数 / 并发 / 用户池、混合资源池构成、后续互动项）后直接 return，与阶段二行为一致。
- **全互动动态创建并发化**：`seed_moment` 用 `asyncio.Semaphore(concurrency)` + `create_task` 并发执行（发布/审核/点赞/浏览/转发），单条失败软降级跳过；共享状态（normal_ids 转发池等）在单事件循环内聚合，无竞态。
- **进度展示统一用 tqdm**：全互动阶段（动态/评论等主循环）与大数据灌数阶段均以 tqdm 进度条呈现，不打印手写「已处理 X/N」日志。
- **大数据灌数新增私信填充**：`run_bulk` 阶段在 pptr 用户池上经 `_seed_bulk_dm` 做 O(n²) 批量互发私信（复用场景 E 逻辑，取前 `--full-count` 对、每对 1 条，业务拒绝软降级跳过），补齐全互动阶段仅在随机 12 人子集上发私信的覆盖缺口——使登录 demo 的任意 pptr 用户（如测试账号 127763472）也都有私信内容可读（发送方自己的消息始终可见）。
- 大数据灌数单条失败**软降级跳过**；私信撤回/删除断言**响亮报错**（暴露代码 bug）。
- **私信双向互发**：`seed_message` 覆盖 a→b 与 b→a **两个方向**的「发送 → 审核 → 已读 → 撤回（双方 RECALLED + recalled_by/recalled_at 落库与出参）→ 再发送 → 单方面删除（自己视角不可见、对方仍可见）→ 删除后撤回被拒」全链路，验证私信写扩散在双向均正确落库；另对**多对用户**做双向互发（发送 → 审核 → 已读 → 双方可见），覆盖「用户之间互相私信」的会话网络广度（被陌生人过滤的配对宽容跳过）。
- **动态 + lottery 混合资源池统一互动（2.53.0）**：`seed_comment` 不再只吃动态 id，改吃 `_build_resource_pool()` 产出的**混合资源池** `[(oid, biz_type)]`——动态（`InteractionBizTypeEnum.DYNAMIC`）与真实 lottery（crawler `GetAllLottery` 接口，不可达时降级直连 `dyndetail.lotdata`，默认取 2 个）**交错排列**（`zip_longest`，避免前半段全动态、后半段全抽奖的覆盖偏斜），同一套「一级评论 → 楼中楼 → 评论赞踩 → @ → 举报 → 置顶」在两种 `biz_type` 上各跑一遍：发评 / 楼中楼 / @ 经 `add_comment(biz_type=)` 走评论子系统（自动生成 REPLY / AT 事件），资源点赞按 `biz_type` 分流（DYNAMIC → `thumb`、LOTTERY → `thumb_lottery`），置顶与列表回查同步透传 `biz_type`。原 `seed_lottery_resource` 中重复的「lottery 评论 + @」删除，只保留其**点赞 + 显式补 LIKE 事件**（通用资源点赞后端不自动生成事件）与「事件统一落点同一测试用户」的消息中心覆盖职责。
- **黑名单归一 + 私信配对避让（2.53.0）**：黑名单**持久化且跨 seed 累积**——每多一条就多一个用户被静默排除在评论 / 私信 / 关注 / @ 通知之外（服务端静默拒绝，seed 只能软降级跳过，互动覆盖逐轮变窄）。新增 `_normalize_blocklist()`：只读查 `msg_user_follow`（`status=blocked`）汇总每个用户的主动拉黑关系，**每人只保留 1 条**用于验证「拉黑后不可互动」的负面场景，其余走 `POST /message/follow/unblock` 接口解除（读走只读探针、写仍走业务接口，不直写主库）。归一后的黑名单集合透传给 `seed_message`：`_pick_dm_pair` 与场景 D 的配对、场景 E 的 `others_pool` 均按「`(receiver, sender) ∈ blocked` 即接收方已拉黑发送方」（对齐 `FollowService.is_blocked_by(sender_mid, receiver_mid)` 的**单向**判定）**主动避让**，私信不再因历史黑名单大面积发送失败。
- **批量私信场景 E 收敛为总计 `--full-count` 条（2.53.0）**：原实现「每个用户随机选一个接收方发 `full_count` 条 = `n × full_count` 条」，发送量随用户数 n 放大、且反复打同一接收方、覆盖率差。改为 **O(n²) 遍历所有有序用户对** `(sender, receiver)`（剔除「接收方已拉黑发送方」的必拒方向），**取前 `full_count` 对、每对发 1 条**——总发送量严格受控为 `min(full_count, 可发对数)`，同时用户对分布更均匀，覆盖「用户对网络」广度。
- **雪花 ID 分钟级容量**：分钟步进短 ID 每 worker 每分钟 16 个（默认 `sequence_bits=4`），灌数超速时服务端锁外等待下一分钟（≤60s）；客户端超时已环境变量化（`SEED_HTTP_TIMEOUT` 默认 90s / `SEED_REQ_TIMEOUT` 默认 120s），开发灌数如需提速配 `*_SEQUENCE_BITS=7`（需清库）。

### 5.8 LLM 治理（爬虫/抽奖链路，非 be-message 本体）

- 所有 LLM 调用共享模块级 `asyncio.Lock`（`TrackedChatOpenAI`），任意时刻只有一个请求打到上游，消除账户级并发超限（429/1302）；锁仅包网络请求，统计在锁外；同步路径无运行 loop 时退化为无锁。
- SQL `1040 Too many connections` 报错补充业务调用栈（`traceback.format_stack()`），便于定位高频协程。

### 5.9 biz_type 单一真相源（2026-09-01）

- `InteractionBizTypeEnum`（bili-common）是**业务资源类型的唯一真相源**；`SourceTypeEnum`（事件来源）/ `CommentTypeEnum`（评论区类型）
  保留各自存储取值，**语义一律经 `app/models/biz_type.py` 与 biz_type 建立关联**：
  - `source_type_to_biz_type()` / `biz_type_to_source_type()`、`comment_type_to_biz_type()` / `biz_type_to_comment_type()`；
  - 展示名统一由 `biz_type_label()` 供给（底层以 `InteractionBizTypeEnum.to_text()` 的 `dynamic` / `lottery` / `rpa_*` 为键），
    **禁止各模块再自行维护「业务类型 → 中文名」字典**——原 `schemas/event.py::_BUSINESS_NAME`、
    `utils/audit_source.py::_COMMENT_TYPE_LABEL`、`services/message/insite/events.py::_SOURCE_TYPE_TO_BIZ_TYPE`
    三处重复定义已全部收敛到该模块；
  - 无对应 biz_type 的历史类型（视频 / 专栏 / 评论 / 反馈区 / 其他）走模块内 `_EXTRA_LABEL` 兜底，未知值回落「其他」。
- **待确认（本次未实施）**：是否把 `SourceTypeEnum` / `CommentTypeEnum` 的**数值**也对齐 `InteractionBizTypeEnum`
  （当前同名不同值，如 `LOTTERY` 在 `CommentTypeEnum=3`、`InteractionBizTypeEnum=2`）。
  对齐需 Alembic 数据迁移（`msg_comment_subject.type` / `msg_event.source_type` 存量行重编号），
  暂以映射关联保证语义一致，**数值不动**。

### 5.10 资源为中心的统一操作模型（2026-09-01）

- **动作枚举单一真相源**：`InteractionActionTypeEnum`（bili-common）合并原 be-message 内部
  `InteractionActionEnum`（`interaction_actions/base.py`，**已删除**）。合并动机：两者语义重复
  （同为「互动操作类型」），但取值互相撞车——值 2 在前为 `REPLY`、在后为 `DISLIKE`，
  3/4/5/6/7 同理全部冲突，**不可按原值直接合并**。
- **取值分配（保守，零数据迁移）**：保留 `InteractionActionTypeEnum` 既有 1~7 原值不动
  （`msg_event.event_type` 存量约束），新增操作自 **8** 起编号：
  `LIKE=1 / REPLY=2 / AT=3 / AUDIT_REJECT=4 / HIDE=5 / REPORT_REJECT=6 / REPORT_RESOLVED=7 /
  DISLIKE=8 / FAVORITE=9 / SHARE=10 / REPOST=11 / VIEW=12 / REPORT=13 / AUDIT_APPROVE=14`。
  语义一致的 `LIKE`、`AUDIT_REJECT` 直接复用既有值，不重复新增。
- **`interaction_actions/` 以资源为主体（2.48.0 改为 `BaseBiz` 类体系）**：
  **废弃「每资源 × 每动作一个类 + 工厂注册表」的写法**，改为：
  - `base_biz.py::BaseBiz`：以 `InteractionBizTypeEnum` 为主体的资源基类，把
    `InteractionActionTypeEnum` 的**全部成员声明为方法接口**（基类默认抛
    「该资源不支持」），并承载举报体系（`report` / `resolve_accused` / `hide`）与
    审核结果（`report_reject` / `report_resolved`）、评论类操作（`reply` / `at`）——
    这些 `InteractionActionTypeEnum` 成员同样是资源方法接口；
  - 每个资源一个类（`<resource>/biz.py`，声明 `_biz_type`），**实现**自己支持的操作；
    通用资源（lottery / rpa_*）共享 `common/generic_biz.py::GenericResourceBiz`，
    差异（如 lottery 禁止下架）靠覆盖方法表达；
  - **继承即登记**：`BaseBiz.__init_subclass__` 自动把子类写入登记表，
    **不再维护任何 `动作 → {资源 → 类}` 工厂映射表**；新增资源 = 写类 + 声明 `_biz_type`；
  - 权限仍声明式：原「动作类的 `relation_scope` / `acl_scope` 类属性」改由
    `@biz_action(relation=[...], acl=[...])` 装饰器挂在方法上，执行前由基类集中强制校验；
  - 共享逻辑抽到 `common/ops.py`（函数），资源方法按需调用，避免逐资源重复实现。
- **举报与管理路径纳入统一模型（2.48.0 随 `BaseBiz` 一并落地）**：举报**提交**与**管理端审核 /
  处置 / 列表**全部资源化，资源定位键恒为 `(bizType, bizId)`（见 `.codebuddy/rules/举报资源唯一性.mdc`）：
  - **举报差异随资源走**：`report()` / `resolve_accused()` / `hide()` 与审核结果 `report_reject()` /
    `report_resolved()` 均为 `BaseBiz` 的方法——`report_reject` / `report_resolved` 是
    `InteractionActionTypeEnum.REPORT_REJECT` / `REPORT_RESOLVED` 的**通用实现**（落到本资源的
    `model` 举报表、通知举报人、可选联动 `hide()`），与 `like()` / `dislike()` 等并列；每个可举报资源
    只需声明 `model` + `resolve_accused()` + `hide()` 即得完整举报能力，无需额外处理器类
    （原 `BaseReportHandler` 已并入 `BaseBiz`）。`dynamic` 走本地 `TMoment` + Feed hidden 并通知作者；
    `comment` 走 `CommentIndex` hidden；`user` 走 pptr `PptrUserInfo` 校验、处置预留；USER 专属关系操作（关注 / 取关 / 拉黑 / 解除拉黑 `follow` / `unfollow` / `block` / `unblock`）仅 USER 资源使用，置于 `UserBiz` 而非 `BaseBiz` 接口，方法内委托 `FollowService`；API `/api/v1/message/follow/{do,undo,block,unblock}` 经 `get_biz(InteractionBizTypeEnum.USER, session, target_mid, user.mid)` 调用，与动态 `like()` 统一走 `get_biz()` 入口。
    `lottery` **禁止下架**（覆盖 `hide()` 跳过）；`rpa_*` 走通用处理器的「Feed 层 + RPC」双层处置。
  - **`ReportService` 退化为纯协调器**（`services/admin/report.py`）：只编排「资源校验 → 落库 → 阈值
    → 审核 → 通知」通用流程，**删除了全部按 `bizType` 的 `if/elif` 分流**与自维护的「bizType → 子表」
    并行映射；「资源 → 表」的唯一真相源是资源类的 `model` 属性（`_model_for()` 读
    `get_biz_class(biz).model`，`_distinct_models()` 遍历 `BaseBiz._registry`）。
  - **审核入口**：`ReportService.review()` 先按 pk 跨 `_distinct_models()` 找到举报记录，再用
    `get_biz(rec.bizType, ...)` 取对应资源实例，委托 `biz.report_reject()` /
    `biz.report_resolved(resource_action="hide")`——协调器不感知任何资源差异。
  - **跨表汇总去重**：`ReportService._distinct_models()` 用
    `dict.fromkeys(c.model for c in BaseBiz._registry.values() if c.model is not None)` 去重，
    避免 `TResourceReport`（被 dynamic + 5 个通用资源共用）在列表 / 检索时被重复查询 6 次。
- **通知系统兼容**：`EVENT_REGISTRY` 仅登记具备通知语义的类型（LIKE / REPLY / AT /
  AUDIT_REJECT / HIDE / REPORT_REJECT / REPORT_RESOLVED）；新增的非通知类操作
  （DISLIKE / FAVORITE / SHARE / REPOST / VIEW / REPORT / AUDIT_APPROVE）**不登记**，
  未登记类型由 `base._resolve_handler_cls` 回落 `GenericEvent`，既有通知链路不受影响。
- **DDL 约束（⚠️ 存量遗留）**：`msg_event.event_type` / `msg_event_cursor.event_type` 当前用
  `sqlalchemy.Enum(...)` 落为 **MySQL 原生 ENUM 存成员名**，与 §2.3 / C6「禁原生 ENUM」约定
  **不一致**（存量遗留，本次不改）。因此新增枚举成员**必须同步 ALTER 两表 ENUM 取值**，
  否则写入新值报错；`tests/test_phase_e_enums.py::test_event_enum_round_trip_all_members`
  会遍历全部成员 × 全部 biz_type 落库，是本次合并的回归守门测试。

---

## 5.11 事件资源定位统一（resource_type + 批量快照加载器，2026-09-02）

**背景**：事件提醒读取时只回捞标题/封面（`source_meta._resolve_source_meta`），跳转 uri 由前端按
`business`+`type` 本地拼（`eventJump.openEventDetail`）。三个问题：① 跳转路由名散落前端，后端无法统一管控；
② 资源不存在/被删时无法在读取侧优雅降级；③ 新增资源类型需前后端各改一份逻辑，扩展性差。

**设计（对齐 §2.10 跳转契约）**：

- **资源身份统一为 `(resource_type, resource_id)`**：`EventMsgfeedContent.resource_type`（顶层资源
  `InteractionBizTypeEnum`：DYNAMIC=1 / LOTTERY=2 / …）+ `resource_id`（顶层 oid / 卡片 id）唯一确定被互动的
  原资源，前端据此 `router.push(name)`。评论类事件的 `resource_type` 取评论所属**顶层资源**类型
  （DYNAMIC/LOTTERY），`resource_id` 取其 oid，`source_id` 携带 rpid 作楼层锚点。
- **后端下发跳转路由名**：`FrontendRouteEnum`（§2.10 已定义，值 = 前端路由 `name`）继续作为路由名唯一真相源；
  读取时按 `resource_type` 映射出 `FrontendRouteEnum` + 查询参数，经 `build_route_target()` 拼成
  `route:{name}?{query}` 写入 `EventMsgfeedContent.jump_target`（含 `rpid` 楼层锚点）。前端 `openEventDetail`
  退化为 `jumpToTarget(router, content.jump_target)`（复用 §2.10 的 `routeJump.ts::jumpToTarget`），不再本地拼 uri。
- **面向对象资源快照（复用既有互动资源 Biz 体系，非新注册表）**：直接复用
  `app/services/interaction_actions` 的 `BaseBiz` / `GenericResourceBiz` 与统一资源表示
  `InteractionResource`（`app/models/schemas/interaction.py`），不另写注册表。用户要求：用面向对象设计落到
  `GenericResourceBiz`/`BaseBiz` 的方法，返回 generic 的 `InteractionResource` 类；`InteractionResourceValidator`
  的存在性校验拆分到各资源子类方法、由基类统一调用。
  - `BaseBiz.get_resource(rpid=None)` 统一装配器：依次调用子类钩子 `check_exists()`（资源是否存在）/
    `_load_meta()`（返回 `(标题, 封面)`）/`_load_author_mid()`/`_load_interactable()`，折叠出
    `InteractionResource`（含 `cover` 封面图、`jumpTarget` 后端跳转目标）。`jumpTarget` 由
    `app/utils/route_target.jump_target_for` 按 `bizType` 映射 `FrontendRouteEnum` + 参数拼出
    （`route:{name}?{query}`，含可选 `rpid` 楼层锚点）。
  - 各资源子类实现钩子，把原 `InteractionResourceValidator` 注册式校验**下沉为方法、由基类统一调用**：
    - `DynamicBiz`：`check_exists()` 查 `TMoment`（命中且未软删且 `auditStatus∉{REJECTED,HIDDEN}`）；
      `_load_meta()` 取 `contentText` + `_first_pic(contentJson)`。
    - `LotteryBiz`：`check_exists()` 经抽奖 RPC `lottery_exists`；`_load_meta()` 经 RPA RPC `get_resource_detail`。
    - `CommentBiz` / `UserBiz`：同理按各自表实现 `check_exists` / `_load_meta`。
    - `GenericResourceBiz`（RPA 系列）：`_load_meta()` 经 RPA RPC 取名称/封面；`check_exists` 默认放行。
  - **批量接口（每个资源类一个）**：`BaseBiz.batch_get_resources(session, biz_ids, rpid_map=...)` 类方法
    （默认逐条 `get_resource` 即「批量接口」）；`DynamicBiz`/`LotteryBiz` 覆盖为一次 `IN` 查询 / `asyncio.gather`
    批量 RPC，避免 N+1。`InteractionResource.exists=False` 即「资源已被删除 / 不可见 / 未知类型（无对应 Biz 类）」的空占位。
  - `InteractionResourceValidator`（bili-common）的 be-message 注册（`_check_dynamic`/`_check_lottery`）已移除；
    `ops.validate_exists` / `moment_publish._validate_attach` 改为 `get_biz(...).check_exists()`（未实现资源类默认放行）。
- **读取侧装配**：`list_msgfeed` 在聚合构建完所有 `item` 后，收集 `(resource_type, resource_id, rpid)` 去重组，
  经 `get_biz_class(rt).batch_get_resources(...)` 批量回捞 `InteractionResource`，把 `title/image`（= `cover`，
  取代原 `_resolve_source_meta`）、`resource_deleted=not exists`、`jump_target`（资源不存在则为空串、前端不跳转）
  写回每个 `item`。`aggregate` / `list_detail` 同步迁移（复用同一 Biz 体系；评论类按其 `biz_id=rpid` 经
  `CommentIndex` 解析出顶层 `resource_type/resource_id` / `rpid`，见 `events/base.py::_resolve_event_identities`）。
- **扩展新资源类型**：只需在 `InteractionBizTypeEnum` 加成员 + 实现一个 `XxxBiz(BaseBiz)` 子类（覆盖
  `check_exists` / `_load_meta`，按需覆盖 `batch_get_resources`）+ 在 `FrontendRouteEnum` 加对应路由名
  （并在 `route_target._JUMP_ROUTE_MAP` 登记映射），事件读取全链路自动支持，无 `if/elif` 分发。
- 原 `source_meta._resolve_source_meta`（按 source_type 的标题/封面回捞）由 Biz 体系取代，`source_meta.py`
  仅保留 `_first_pic` 共享工具；`event.py` 的
  `EventMsgfeedContent` 新增 `jump_target: str` 与 `resource_deleted: bool`；`comment_deleted`
  （评论正文级）与 `resource_deleted`（顶层资源级）正交并存。

---

## 5.12 评论锚定事件的评论原始信息回捞（CommentBiz 批量快照，2.54.0，2026-09-02）

**背景**：§5.11 把**顶层资源**（动态 / 抽奖）的标题 / 封面 / 跳转统一收敛到 Biz 体系批量回捞，
但**评论锚定**事件（REPLY / 评论 @ / 评论点赞 / 评论处置）里真正被展示的**评论正文**
（`source_content` / `target_content`）仍是 `list_msgfeed` 直接 `select(CommentContent)`
回捞的——绕过 Biz 体系，与 §5.11「按资源类型走 `batch_get_resources`」不一致；且评论的
**原始信息**（作者 mid 等）未随事件下发，前端楼层卡片展示不出「谁写的这一层」。

**设计（沿用 §5.11 的 Biz 体系，不新增注册表）**：

- **`CommentBiz` 补齐资源快照能力**（`app/services/interaction_actions/comment/biz.py`）：
  - `_load_interactable()`：`CommentIndex.state is NORMAL` 才可互动（其余状态只可举报、不进展示）；
  - `_build_jump_target(rpid)`：评论无独立详情页，跳转目标按所属**顶层资源**
    （`CommentIndex.type` + `oid`）拼 `route:{name}?{query}` + `rpid` 楼层锚点，
    与 `_locate_comment` 的 `resource_type + resource_id` 同源；
  - `batch_get_resources()` **覆盖基类逐条兜底**：一次 `IN` 查 `CommentIndex` +
    一次 `IN` 查 `CommentContent`，按 rpid 装配 `InteractionResource`
    （`title` = 评论正文、`authorMid` = 评论作者、`exists` = 索引存在、
    `interactable` = 状态 normal、`jumpTarget` = 顶层资源 + 楼层锚点），避免 N+1
    （对齐 `DynamicBiz` 的一次 IN 查询）。
- **事件读取侧装配**（`app/services/message/insite/events/base.py`）：
  - `MsgfeedBuildContext` 新增 `comment_resources: dict[int, InteractionResource]`
    （rpid → 评论快照），由 `list_msgfeed` 在构建内容体**之前**一次性批量回捞；
  - 新增 `_load_comment_resources(session, rpids)` 薄封装，走
    `CommentBiz.batch_get_resources(..., rpid_map={rpid: rpid})`，SQL 次数恒定；
  - `_locate_comment` 的 `source_content` / `target_content` 改由评论快照回捞
    （`ctx.comment_content` 由 `CommentBiz` 批量结果填充；非 NORMAL 状态按既有逻辑
    不回捞正文并置 `comment_deleted`），作者 mid 从同一批快照取；
  - 楼层关系（`root` / `parent` / `oid` / `type` / `state`）仍由 `CommentIndex` 查询承担
    （结构性查询，与 Biz 的展示快照职责不同，各自一次 IN 查询，无 N+1）；
  - `@{mid}` → `@昵称` 替换继续在事件层统一做（按 `at_mids` 经 `PptrUser.get_many` 回查），
    作用在回捞出的正文上，Biz 层不感知用户服务，保持职责单一。
- **出参**：`EventMsgfeedContent` 新增 `source_mid` / `source_name` 与 `target_mid` /
  `target_name`（触发评论 / 被回复（被 @）评论作者的 mid + 昵称），随事件下发，
  前端楼层卡片据此展示各层作者；昵称由后端在 `list_msgfeed` 回查块经**一次**
  `PptrUser.get_many` 与 `@` 昵称合并批量回查，缺失时前端降级为「用户{mid}」。
- **正交不变**：`comment_deleted`（评论正文级）与 `resource_deleted`（顶层资源级）
  继续并存，语义不变（§5.11 末段）。

---

## 5.13 互动接口通用化 + 路由层瘦身（2.56.0，2026-09-03）

**背景**：`/api/v1/community` 下的互动写接口只有 `/thumb` 是泛化的（2.17.0）——`/share`
与 `/report` 仍是**动态专属**（只收 `dynId`），`/dislike` 虽带 `bizType` 却在路由层硬编码
拒绝非 dynamic（而 `GenericResourceBiz.dislike` 早已实现）。结果：同一动作存在两套入口，
非动态资源（lottery / rpa_*）要上报分享或举报只能绕到别的域，新增资源类型还得改路由。
同时 `app/api/moment.py` 内联了约 150 行装配逻辑（`_verify_resources_exist` 防乱调校验 /
`_query_status_items` 计数 + 用户态 + 详情装配），路由层既做参数校验又做查询编排，
service 层反而空着（§5.5 已把动作收口到 Biz 体系，查询侧却没跟上）。

**设计（沿用 Biz 体系，不新增注册表）**：

- **统一资源定位键（C18 / C20）**：四个互动写接口（`thumb` / `dislike` / `share` /
  `report`）的请求体一律为 `bizType` + `bizId`（2.56.0 去除 `dynId` 别名，动态资源也一律传
  `bizId`）。解析归一收敛为服务层 `resolve_target()`（缺参 / 非法抛 `ValueError`，路由层统一转
  400），路由层不再手写 `if bizType == DYNAMIC` 分支。
- **动作仍走 Biz 体系**：解析出 `(biz_type, biz_id)` 后 `get_biz(...)` 取资源实例调用
  `like()` / `dislike()` / `share()` / `report()`；非动态资源由 `GenericResourceBiz`
  （`common/ops.py`）承载、动态由 `DynamicBiz` 覆盖，**新增资源类型无需改路由**
  （继承即登记，§5.10）。
- **响应泛化**：`MomentThumbResp` / `MomentDislikeResp` / `MomentShareResp` /
  `MomentReportResp` 统一带 `bizType` / `bizId` / `bizIdStr`（2.56.0 去除 `dynId` / `dynIdStr`
  兼容字段）；前端按 `bizType` 判定资源类型而非字段名。
- **路由层瘦身**：`_verify_resources_exist` / `_query_status_items` 迁入
  `app/services/interaction_actions/interaction_status.py` 的 `InteractionStatusService`
  （`verify_resources_exist` / `query_status_items` / `query_status_item`），路由层只做三件事：
  `resolve_target()` 归一 → `get_biz(...).动作()` → 装配响应模型。
- **客户端上下文显式化**：`BaseBiz` 新增 `client_ip` / `user_agent` 实例属性（默认 `None`，
  由 `/repost` 等需要写审核日志的接口注入），取代原「动态属性 + `getattr` 兜底」的隐式约定。

**不变**：`/repost`（转发 = 发布 FORWARD 动态）保持 `dynId`；统一举报独立域
`POST /api/v1/report` 不变；`MomentPublishService` 发布类接口不变；防乱调语义
（任一资源缺失 → 整体 400，不返回部分结果）不变。

**兼容**：`bizType` 缺省 `dynamic` + `dynId` 别名保留，既有前端 `thumbMoment` /
`reportMoment` 与 seed 脚本零改动可用；上报**非动态**资源的分享 / 举报需 SDK 重新生成后
传 `bizType` + `bizId`。

---

## 5.14 私信发送限制（每日上限 + 陌生人单条闸门，2.57.0，2026-09-04）

**背景**：私信是高频骚扰 / 营销渠道，此前只靠「接收方关闭陌生人私信」被动防御，没有对
**主动发送方**做主动拦截。需要两道闸门：① 每用户**每日发送总量**上限；② 对**未被接收方
关注**（对方未关注我）的陌生对象，在对方**回过我消息之前**，我仅能发一条——防止对陌生人
单方面狂轰滥炸（B 站等主流 IM 均有此治理）。

**设计（改动点全部收口在 `DmSessionObject.send` 落库之前，被限消息一律不落库）**：

- **配置（`app/core/config.py::Settings`，`dm_` 前缀）**：
  - `dm_daily_send_limit: int = 1000`：单用户每自然日发送私信总量上限（0 表示不限制）。
  - `dm_stranger_gate_enabled: bool = True`：陌生人单条闸门总开关。
  - `dm_stranger_gate_limit: int = 1`：对方未关注我、且未回过我消息时，我可发送的条数上限。
- **每日上限**：发送前统计「本自然日 `sender_uid == 我`（`owner_mid == 我`，msg_ts 落在当日 0 点~次日 0 点毫秒窗口）」的索引行条数，`>= dm_daily_send_limit` 则拒绝——口径为**当天作为发送者的全部私信**（不看接收者，含被陌生人过滤只留发送方视角的行）。
- **陌生人单条闸门**（判定复用关注表 `msg_user_follow`，与现有 `_is_stranger` 语义对齐但更贴合需求文案）：
  1. `receiver 是否关注 sender`：`FollowService.is_following(session, receiver_mid, sender_mid)`；
  2. `receiver 是否回过 sender`：`DmMessageIndex` 中 `owner_mid==receiver AND sender_uid==receiver AND talker_mid==sender AND msg_status != DELETED` 是否有行；
  3. 若「receiver 未关注 sender 且 receiver 从未回过 sender」，再统计 `sender` 已发给 `receiver` 的条数（`owner_mid==sender AND sender_uid==sender AND talker_mid==receiver AND msg_status != DELETED`），`>= dm_stranger_gate_limit` 则拒绝；否则放行（本条成为对方回我前的最后一条额度）。
  4. **解除条件**：一旦 receiver 关注了 sender，或 receiver 给 sender 回过任意一条消息，该方向闸门即解除（对方视角会话 `relation` 会因 upsert 的 STRANGER→NORMAL 升级逻辑自动转为 NORMAL）。
- **业务码（bili-common `ResponseCode` 单一来源新增，互不撞车）**：
  - `DM_SEND_DAILY_LIMIT = 4001`：触发每日上限；
  - `DM_SEND_STRANGER_LIMIT = 4002`：触发陌生人单条闸门。
  - 语义：均返回 `{code, msg, data}`，HTTP 恒 200；msg 说明具体原因；**消息不落库**。区别于既有 `403`（封禁私信）/ `400`（参数 / 黑名单 / 账号停用等通用错误）。
- **错误反馈**：`DmSessionObject.send` 对两类限制抛出带业务码的专用异常（`DmDailySendLimitError` / `DmStrangerSendLimitError`），`api/dm.py::send_dm` 先捕获专用异常回对应 `code`，再回落既有 `ValueError → 400`、通用 `Exception → 500`。
- **判定时机**：两条校验都放在 `_persist_dm`（写扩散落库）之前，命中直接抛异常，**不产生任何索引 / 会话 / 分片数据**，与「发送方被拉黑」「账号停用」同级优先于陌生人过滤。

**影响面与兼容**：
- **seed 脚本**：`seed_message` / 大数据 `_seed_bulk_dm` 原先是「对同用户对双向互发、且对陌生对象可能连发多条」；服务端新闸门会拒掉部分连发。seed 是开发灌数工具，不应改动其目标，故 seed 侧按其「已关注 / 已互回」的用户池天然规避（场景本就多回发、且会话互发后即解除）；若确需对未互动的陌生对象批量灌数，可配 `DM_STRANGER_GATE_ENABLED=false`（开发环境）。
- **既有前端**：`dm/send` 契约不变（`{msgkey, session_key, msg_ts, filtered, content_async}` 仍按原样返回），仅当触发限制时多出 `code!=0` 的分支响应；前端对 `4001/4002` 展示后端 msg 即可，无需改 SDK（无新字段）。

---

## 5.15 内容发布每日上限（评论 / 动态 / 话题，2.58.0，2026-09-04）

**背景**：在 §5.14 私信发送限制之外，把「单用户每自然日创建量上限」扩展到内容发布三类——
评论、动态、话题，防刷屏 / 防滥用。`limiter` 能力**交给各 biz 自治接入**（非强制每个资源都用），
本类只给「评论 / 动态 / 话题」三个创建入口接入。

**配置（`app/core/config.py::Settings`，env 环境变量可覆盖，命名 = 大写下划线字段名）**：
- `comment_daily_create_limit: int = 100`（`COMMENT_DAILY_CREATE_LIMIT`，0 = 不限制）
- `moment_daily_create_limit: int = 30`（`MOMENT_DAILY_CREATE_LIMIT`，0 = 不限制）
- `topic_daily_create_limit: int = 10`（`TOPIC_DAILY_CREATE_LIMIT`，0 = 不限制）

**计数口径（「删除也算次数」的根基）**：按「当天创建行存在数」统计——查询各资源表
`创建时间列 ∈ 本自然日窗口 AND 作者列 == 当前 mid` 的**全部行数**（**不过滤**软删 / 审核中 /
被驳回等状态）。因三者的删除均为软删（评论 `state=DELETED`、动态 `deletedAt`、话题无删除），
行始终保留且 `mid / created_at` 不被改写，故用户「创建后删除、再创建」无法绕过当日上限；
编辑为 update 原行、不产生新 created 行，天然不计（且动态编辑功能 2.58.0 已移除）。

**计资源范围**：
- **评论**：`CommentService.add` 每次调用计 1（一级与楼中楼都算）——统计 `msg_comment_index.mid + created_at`；
- **动态**：仅**创建 WORD** 计；**FORWARD 转发不算**（用户口径）；编辑已移除；——统计 `TMoment.mid + created_at` 且 `dynType=WORD`；
- **话题**：`create_topic` 每次计 1——统计 `TMomentTopic.creatorMid + created_at`（创建即 auditing，无法软删，无需考虑删除返还）。

**业务码（bili-common `ResponseCode` 新增，独立可区分，承接 §5.14 语义）**：
- `COMMENT_DAILY_CREATE_LIMIT = 4101` / `MOMENT_DAILY_CREATE_LIMIT = 4102` / `TOPIC_DAILY_CREATE_LIMIT = 4103`。
- 触发时接口返回对应 `code` + `msg`（说明已到上限），HTTP 恒 200，**不落库**。

**实现（各 biz 自治，共享一个通用 limiter）**：
- `app/services/common/daily_limit.py`：`count_created_today(session, model, author_field, created_field, mid)` 通用计数 + `check_create_limit(limit, cnt, err_cls)` 判超；由各 biz 按需 import 自己表 / 列 / 上限 / 异常。
- 各 biz 服务（`CommentService.add` / `MomentPublishService.create`(仅 WORD 分支) / `MomentTopicService.create_topic`）在真正 `session.add` **之前**调用检查，超限抛带码专用异常。
- 各 API（`comment.py::add_comment` / `moment.py::create_dynamic`、`topic_create`）先捕获专用异常回各自 `code`，再回落 `ValueError`（评论 / 动态 → 400，话题 → 422）。

---

## 5.16 移除「动态编辑」功能（2.58.0，2026-09-04）

**背景**：产品决策——不再提供动态编辑；转发 FORWARD / 发布 WORD / 删除 remove / 置顶均保留。
编辑既不会被每日上限计入，又与「发布后不可改」的新语义冲突，故整体下线。

**后端改动（干净剥离，单一消费点 `edit_dynamic → MomentPublishService.edit`，无 seed/admin/audit 旁路）**：
- `app/api/moment.py`：删 `POST /edit` 的 `edit_dynamic` 接口（含 import `MomentEditReq/MomentEditResp`、docstring）。
- `app/services/moment/moment_publish.py`：删 `MomentPublishService.edit()`（含其 import `MomentEditReq`）；**共享 helper 全部保留**（`_validate_topics` / `_persist_topic_rels` / `_resolve_attach` 等被 create/remove/repost 复用）；`_resolve_topics` 类型注解 `MomentCreateReq | MomentEditReq` → `MomentCreateReq`。
- `app/models/schemas/moment.py`：删 `MomentEditReq` / `MomentEditResp`；**共享基类 / 节点 / option 保留**（create/repost 复用）；`schemas/__init__.py` 未导出二者，无需动。
- `app/models/enums.py::MomentAuditLogActionEnum`：**保留 `EDIT=2`**（共享动作枚举，DB/迁移/审计日志仍引用）。
- 测试 `tests/test_moment_publish.py`：删 `test_edit_normal_forward_decrs_src` 用例与 `MomentEditReq` import。

**前端改动**：
- `src/api/notify/moment-api.ts`：删 `editMoment()`、相关 `MomentEditReq/Resp` import 与 re-export。
- `components/moment/MomentPublishForm.vue`：`isEdit` prop 与 `dialogTitle/submitLabel` 的编辑态文案分支为**未接线死分支**，一并精简；`MomentCard.vue` 未使用的 `edit` emit 声明可删。
- **hey-api 生成 SDK**（`api/community/hey-api/`）：含 `editDynamicApiV1CommunityEditPost` / `MomentEditReq/Resp` 等，为生成代码**禁手改**；后端去掉 `/edit` 后需重新生成 openapi SDK，届时自动消失（暂停等待用户手动重新生成）。

**兼容**：移除为破坏性变更（删除对外端点），按 2.49.0（删 `/notify/read`）先例记为 **MINOR**。

---

## 5.17 私信会话置顶（top_ts，2.59.0，2026-09-04）

**背景**：会话列表需要「置顶聊天」：置顶的会话恒排在普通会话之前。此前模型只有冗余 `is_top: bool`
（从未被任何接口写过，纯死字段），现改用**置顶时间戳 `top_ts`** 作为唯一真相源，并新增置顶/取消接口。

**设计**：
- **`top_ts` 列**（`msg_dm_session.top_ts`，BIGINT 毫秒时间戳，`0`=未置顶）替换语义上的 `is_top`：
  置顶写当前毫秒时间戳，取消置顶写 `0`。**可多个会话同时置顶**（各自独立 `top_ts`，互不影响，
  与评论「全区唯一置顶互斥」不同）。`is_top` 模型列不再作为权威（保留列兼容，但列表以 `top_ts` 排序、
  出参 `is_top` 由 `top_ts != 0` 推导）。
- **排序**：`list_sessions` 排序改为 `top_ts DESC（置顶优先，最近置顶在前）→ last_msg_ts DESC`。
  **所有页统一此序**（不做首页/后续页分流）：置顶恒排在普通前、跨页 offset 稳定，天然不重复不遗漏
  （最终需求方确认：不做「后续页排除置顶」的分页特判，仅保证置顶优先）。
- **置顶接口**：新增 `POST /api/v1/message/dm/session/top`，body `{ talker_mid, top: bool }`：
  - `top=true` → 置顶：`top_ts = now_ms`；
  - `top=false` → 取消置顶：`top_ts = 0`。
  幂等（重复置顶刷新时间戳，未置顶取消 no-op）。返回受影响会话条数 + `top_ts` / `is_top`。
- **`DmSessionItem` 出参**：新增 `top_ts: int`（0=未置顶）；保留 `is_top: bool`（= `top_ts != 0`，兼容前端 flag 用法）。
- **DDL（用户手动执行，dev 无生产数据可 DROP+CREATE 或直接加列）**：
  ```sql
  ALTER TABLE msg_dm_session ADD COLUMN top_ts BIGINT NOT NULL DEFAULT 0 COMMENT '置顶时间戳(毫秒)，0=未置顶';
  ```
  （新增索引可选：置顶会话量小，排序走内存即可；若量大可加 `idx(owner_mid, top_ts DESC)`。）

**影响**：私信 `DmSessionObject` 增加 `top(owner)` 实例方法；`api/dm.py` 挂 `/session/top`；`DmInbox.list_sessions`
排序用 `top_ts`；`_to_session_item` 出参补 `top_ts` / 推导 `is_top`。前端会话列表按后端排序直接展示即可，
置顶按钮调新接口，取消置顶后前端本地把该会话移回普通区或刷新第一页。

---

## 5.18 互动态查询开放匿名访问（2.60.0，2026-09-04）

**背景**：`GET /community/interaction/status`（批量）与 `/interaction/status/{bizId}`（detail）此前为
`RequiredUser` 且未进 be-gateway 匿名白名单 —— 未登录用户浏览动态 Feed / 详情页时网关先拦一道 `-101`，
即便网关放行、上游 `RequiredUser` 仍再拦一道，**匿名浏览卡片永远拿不到点赞 / 收藏 / 评论计数**，
与已开放的 `feed/all`、`detail/{dynId}`、`comment/main` 语义不一致（那些接口匿名可读）。

**设计**：
- **鉴权降级**：两接口依赖由 `RequiredUser` 改为 `OptionalUser`（`app.dependencies.user.get_optional_user`，
  匿名返回 `None` 而非抛 -101）；装配互动态时 `viewer_mid = user.mid if user else 0` —— `0` 不是合法 mid，
  点赞 / 收藏明细查询自然为空，`isLike` / `isFavorite` 恒 `false`，计数照常返回。
- **浏览统计不匿名投递**：detail 接口的 `InteractionViewPayload` 仅在 `user` 非空时投递。
  `TInteractionViewLog` 唯一约束为 `bizType+bizId+mid`，匿名无 mid 会把全部游客流量压成 `mid=0` 一行
  （计数失真 + 污染明细表），故沿用 D26「浏览统计仅登录用户」的既有语义：匿名进详情不累计浏览。
- **服务层约定**：`InteractionStatusService.query_status_items` / `query_status_item` 的 `mid`
  以 **`0` 表示匿名观众**（路由层 `OptionalUser` 为 None 时传 0），装配时 `viewer_mid = int(mid)`，
  0 非合法 mid → 点赞 / 收藏明细自然为空。
- **网关白名单**（`be-gateway/ExpressServerEnd/Service/user_permission_module/JwtModule.js` 的 `jwtAuth.unless`）：
  新增 `{ url: /\/api\/v1\/community\/interaction\/status/ }`（正则未锚定，同时覆盖批量与单资源两个 URL）。
  互动**写**接口（`thumb` / `dislike` / `share` / `report`）不在白名单，仍走 `jwtAuth` + 上游 `RequiredUser`。

**影响**：匿名可读互动态与全部计数；匿名点赞态恒「未点赞 / 未收藏」（前端据此渲染登录引导）；
匿名访问详情页不产生浏览计数（与 2.23.0 起的既有约定一致）。无 DDL 变更，无前端 SDK 契约变更。

---

## 5.19 举报列表追加用户信息与资源快照（2.61.0，2026-09-04）

**背景**：`GET /report/admin/list` 的 `ReportItem` 只有 ID 类字段（`reportMid` / `accusedMid` /
`bizType` / `bizId` / `reasonType` …），管理员在审核队列里看不到「谁举报的 / 被举报的是谁 /
被举报内容是什么」，只能拿 `bizId` 人肉判别，审核效率低且易误判。

**设计（复用既有能力，不新增注册表 / 不冗余快照）**：

- **用户信息（一次批量，弱依赖）**：`ReportService.list_reports` 在装配 item 前收集本页
  `reportMid` + `accusedMid` 去重，**一次** `PptrUser.get_many(mids)` 回查（与 §5.12 事件侧同一
  批量入口，直连 pptr 只读，不冗余用户快照），`ReportItem` 新增 `reporterName` /
  `reporterFace` / `accusedName` / `accusedFace`（字段风格对齐 `MomentAuditItem` 的
  `authorName` / `authorFace`）；回查失败仅告警并降级为 `null`（沿用
  `moment_audit._safe_author_brief` 的弱依赖语义），前端降级「用户{mid}」。
- **资源信息（按 bizType 分组批量，§5.11 既有能力）**：按 `bizType` 分组收集 `bizId`，经
  `get_biz_class(bt).batch_get_resources(session, ids)` 批量回捞统一资源快照
  `InteractionResource`（`DynamicBiz` / `CommentBiz` 已覆盖为一次 IN 查询，RPA 系列走批量 RPC，
  无 N+1），`ReportItem` 内嵌新增 `resource: InteractionResource | None`（含 `title` / `cover` /
  `exists` / `authorMid` / `jumpTarget`）。`exists=false` 表示被举报内容已删除 / 不可见 /
  未知类型，前端据此展示「内容已删除」并禁用跳转；`jumpTarget` 供管理员一键跳到被举报内容
  （`route:{name}?{query}`，§2.10 / C16 / C20）。
- **调用次数恒定**：每页 1 次用户批量 + 每个 `bizType` 1 次资源批量，与分页大小无关，
  跨表汇总分支同样只按当页结果回捞。
- **单一真相源**：资源快照仍由各资源 Biz 子类的 `check_exists()` / `_load_meta()` 钩子供给，
  协调器不按 `bizType` 写 `if/elif`（§5.10 / C21）；新增资源类型自动获得举报列表的资源展示能力。

**不变**：举报落库 / 达阈值 / 审核处置 / 通知链路与 `ReportListResp` 结构不变（仅 item 增字段）；
无 DDL 变更；`reportCount` / `reportPeopleCount` 双口径聚合（2.40.0）不变。

**影响**：纯新增出参字段，记 MINOR；前端需重新生成 hey-api SDK（vite dev 自动拉
`http://localhost:18739/openapi.json`，`InteractionResource` 为新增类型）。

---

## 5.20 点踩负反馈闭环（动态点踩入口 + 双层降权，2.62.0，2026-09-04）

**背景**：

- **评论点踩已闭环**（§4.2）：`hot_score = like − 1.5·hate + 0.5·rcount − age·0.1`，点踩即参与排序降权。
- **动态 / 话题动态流前端无点踩入口**：后端 `POST /community/dislike`（2.35.0）、`TResourceDislike` 幂等明细
  （`uq(bizType,bizId,mid)`）、`TInteractionStat.dislikeCount` 原子计数、SDK 生成代码全部就绪，
  仅缺前端按钮 + `moment-api.ts` 薄封装。
- **降权只有全局一维**：EdgeRank `feedback_penalty = −w_dislike·dislike_ratio`（2.35.0）达成「对所有人略降」，
  但**对点踩者本人没有任何个性化降权**——`load_personal_signals` 只有正向 boost
  （关注作者 / 互动作者 / 偏好话题 / `last_clicklist`），打分阶段不读观众自己的 `TResourceDislike`。

**目标**：点踩 → ① 全站 `dislike_ratio` 略降（已存在，不动）；② 对点踩者本人**大幅降权**（新增）。

**设计**：

1. **双层降权**：
   - **全局（不变）**：`−w_dislike · dislike_ratio`，`dislike_ratio = dislike / max(dislike + like, 1)`（§5.4 2.35.0）。
   - **本人（新增）**：精排后处理，命中「我点踩过」的候选 → `s' = s · scale − weight`：
     - `edgerank_personal_dislike_scale`（默认 0.3，比例压制：高分内容也显著下沉）；
     - `edgerank_personal_dislike_weight`（默认 5.0，固定扣分：中等分数内容直接沉底）；
     - 与 `_boost`（正向个性化）对称，同在 `feed_engine` 实现，`edgerank` 保持纯函数（无 IO / 无 DB）。
   - **开关**：`edgerank_personal_dislike_enabled`（默认 True，随 2.33.0 个性化总开关一并由
     `edgerank_personalized_enabled` 兜底）+ `edgerank_personal_dislike_exclude`
     （默认 False；置 True 时点踩过的资源**直接剔除**出该观众的 Feed，硬约束）。
   - **作用范围**：综合 Feed（`feed_scene=comprehensive`）与话题 Feed（`feed_scene=topic`）共用
     `rank_feed`，一处实现两处生效（§4.1 / 2.36.0 通用 Feed 引擎）。
2. **信号源复用既有明细，不新增表**：`PersonalSignals` 增 `disliked: set[int]`，在
   `load_personal_signals` 内按 `bizType` + 候选 `bizId` 一次 IN 查询 `TResourceDislike`
   （与既有 `follow` / `liked_author` 同批加载，不增加 SQL 轮次）；`load_personal_signals` 新增
   `biz_type` 入参（缺省 `DYNAMIC`，向后兼容）。
3. **点踩态回传（契约新增出参字段）**：`InteractionStatusItem` **仅新增 `isDislike`**（当前观众是否已踩；
   匿名 `mid=0` 恒 false，对齐 2.60.0 匿名语义），由 `InteractionStatusService.query_status_items`
   增加一次 `TResourceDislike` 明细 IN 查询得到；默认 false，**向后兼容**。
   **点踩计数不对外暴露**：`dislikeCount` 仍留在 `TInteractionStat`（2.36.0 全资源统一已有该列），
   仅供 EdgeRank `dislike_ratio` 全局降权内部消费，**不出参、前端不展示**——避免负向数字外显
   （对齐 B 站：评论外的负反馈只体现为「已踩」态与排序变化，不展示踩数）。
4. **前端入口**：`MomentStatBar` 增加「踩」按钮（与点赞同排，`CaretBottom` 图标，已踩高亮）；
   `MomentCard` 透传 `is-disliked` 并 emit `dislike`，由父组件（综合 Feed / 话题 Feed / 详情页）
   调 `dislikeMoment`（`moment-api.ts` 新增薄封装，复用 SDK 既有 `MomentService.dislike...`，
   **不新增后端端点**）并乐观更新 `status.isDislike` / `dislikeCount`。

**不变**：点踩写接口 / 明细表 / 计数 / 全局 `dislike_ratio` 降权 / 评论 `hot_score` 点踩惩罚一律不动；
点踩**不改变内容可见性**（只降权不下架）——下架仍由举报审核 `resourceAction=hide` 独占（2.38.0），
两者语义分离：点踩是排序负反馈，举报是内容治理。

**风控**：一人一踩幂等（`uq(bizType,bizId,mid)`）防刷全局计数；`dislike_ratio` 取占比而非绝对值，
单人点踩对全站影响有限（即「略降」）；本人降权**默认不剔除**（内容仍可见，仅排序靠后），
避免点踩被滥用为「静默屏蔽作者」；`exclude` 开关保留给运营按需开启。

**测试**（`be-message-service/tests/test_edgerank.py`，25 用例全通过）：
`test_apply_dislike_penalty_hits_only_disliked`（纯函数：命中降权 / 未命中与开关关闭原分返回）、
`test_comprehensive_feed_personal_dislike_penalty`（端到端：点踩者对本人降权 + **不影响他人**的候选）、
`test_comprehensive_feed_personal_dislike_exclude`（`exclude` 开启时点踩项被剔除）。

**影响**：MINOR。后端 `InteractionStatusItem` 新增 `isDislike` 出参 → **前端 hey-api SDK 已重新生成**
（`types.gen.ts` 已含 `InteractionStatusItem.isDislike`）；前端另用会话级缓存
`src/composables/useMomentDislike.ts` 承担乐观更新与跨组件存活（卡片卸载不闪回「未踩」）；
点踩过的资源对点踩者本人下沉属预期行为变化。

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
| C16 | 跳转契约 | 后端只发前端路由名（`route:{name}?query`，枚举 `FrontendRouteEnum`），路径只在前端路由表写一次；站内 `/app/...` 仅存量兼容 |
| C17 | biz_type | `InteractionBizTypeEnum` 为业务类型唯一真相源；`SourceTypeEnum` / `CommentTypeEnum` 经 `app/models/biz_type.py` 关联，展示名禁止各模块自建字典 |
| C18 | 动作枚举 | `InteractionActionTypeEnum` 为互动操作唯一真相源（已合并删除内部 `InteractionActionEnum`）；取值保 1~7、新增自 8 起；`interaction_actions/` 以 `InteractionBizTypeEnum` 为主体组织；新增成员须同步 ALTER `msg_event` / `msg_event_cursor` 原生 ENUM |
| C19 | 跨项目枚举导入 | bili-common 收口的枚举（`InteractionBizTypeEnum` / `InteractionActionTypeEnum`）一律 `from bili_common.models import ...`；`app/models/enums.py` 与 `app/models/__init__.py` **不做 re-export**，避免同一枚举出现多个导入入口 |
| C20 | 事件资源定位 | 事件跳转身份统一为 `(resource_type, resource_id)`（顶层 `InteractionBizTypeEnum` + oid/卡片 id）；路由名由后端 `FrontendRouteEnum` + `build_route_target` 下发 `route:{name}?{query}`，前端只 `router.push(name)`；按资源类型注册 `ResourceLoader` 批量回捞 `ResourceSnapshot`，不存在返回 `exists=False` 空占位（§5.11） |
| C21 | 互动接口定位与分层 | 互动写接口（`thumb` / `dislike` / `share` / `report`）一律以 `bizType`+`bizId` 唯一定位资源（2.56.0 去除 `dynId` 别名，动态资源亦传 `bizId`）；参数归一（`resolve_target`）、存在性校验、互动态装配一律在 service 层（`InteractionStatusService`），路由层只做「归一 → `get_biz(...).动作()` → 装配响应」，禁止在路由层按 `bizType` 分流（§5.13） |
| C22 | 内容每日上限 | 评论/动态/话题按「当天创建行（作者+created_at）」计数，软删仍算次数；上限配置化（`*_daily_create_limit`，env 可调，0=不限制）；超限回独立业务码 `4101/4102/4103`；limiter 由各 biz 自治接入（§5.15） |
| C23 | 动态不可编辑 | 已移除动态编辑 `POST /edit`（§5.16）；转发/发布/删除/置顶保留；`MomentAuditLogActionEnum.EDIT` 枚举保留；端点移除记 MINOR |
| C24 | 会话置顶 | 私信会话置顶用 `msg_dm_session.top_ts`（毫秒，0=未置顶）为唯一真相源；列表统一 `top_ts DESC → last_msg_ts DESC` 排序（所有页一致）；可多会话同时置顶；取消置顶写 0；`POST /dm/session/top`（§5.17） |

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
- **回复 / @ 通知 `source_type` 按「被互动对象」区分（2026-09-02 修复）**：`CommentService._notify_reply` 与 `_notify_at` 原逻辑按 `type_`（评论区类型）一刀切：动态评论区下的所有回复 / @ 通知 `source_type` 都标 `DYNAMIC`，结果楼中楼回复显示成「回复了我的动态」——业务来源本应该是**被回复的那条评论**（`InteractionBizTypeEnum.COMMENT`），`business_name` 才对齐为「评论」、`business=COMMENT` 触发前端 `targetName` 修正文案为「回复了我的**评论**」。正确规则：① `_notify_reply` 按**当前评论自身** `root` 是否为 0 判定——一级评论（对动态/抽奖本身的回复）`source_type = type_`（DYNAMIC/LOTTERY），楼中楼 `source_type = COMMENT`；② `_notify_at` 统一 `source_type = COMMENT`（被通知人是「评论正文里被点名」，业务来源统一是评论本身，不管该评论是一级还是楼中楼）。`_notify_reply` 函数签名加 `root: int`，调用点 `add` / `CommentAdminService._resend_interact_notify` 同步传入。对应 `ReplyEvent.build_msgfeed_content` 增加 `resource_type` 修正：当 `biz_type is COMMENT` 且能查到 `idx` 时，`resource_type` 用 `idx.type`（评论所属顶层资源类型）——保证 `resource_type + resource_id` 仍配对为前端 `openEventDetail` 能跳转的「动态/抽奖详情页」组合，而不是误判成「跳转评论详情」。`@` 通知同步受益（`source_type` 之前同样错位），`_resolve_source_meta` 的 COMMENT 分支按 `biz_id=rpid` 查 `CommentIndex.oid` 回捞动态标题/封面，跳转由 `resource_id=oid` 带 rpid 定位。
- **一级评论通知「资源创建者」（新增，2026-09-02）**：一级评论（`root==0`，对资源本身发表评论）在 `audit_state==NORMAL` 时，若资源**有创建者**则给创建者发 `REPLY` 通知（文案「XX 回复/评论了你的动态」，`source_type=资源类型`、`source_id=oid`、`biz_id=rpid`）；**无创建者则不发**。创建者判定按实际 owner：优先 `CommentSubject.up_mid`（评论区作者 = 资源 owner），若为 0 且资源类型为 `DYNAMIC` 则回查 `TMoment.mid` 兜底（保证动态 up 主总能收到）；lottery/rpa_* 等通用资源无 `up_mid`（=0）自然不通知。实现位置 `CommentService.add` 通知分支新增一级评论处理，复用 `_notify_reply(root=0)`；审核通过补偿通道 `CommentAdminService._resend_interact_notify` 同步补发（对 `row.root==0` 的一级评论，按 `CommentSubject.up_mid`/`TMoment.mid` 判定后补发），保持「审核通过后补发已跳过通知」的 D6 语义一致。`_notify_reply` docstring 同步说明其承担「一级评论→资源创建者」与「楼中楼→被回复评论作者」两类投递。
- **空间资料聚合统计 + 悬浮卡片常驻缓存（2.51.0，补记）**：`GET /user/space/info` 的 `SpaceInfoResp` 新增两个只读派生字段 `follow_stat`（following_count/follower_count/mutual_count）与 `upstat`（dynamic_count/like_count），路由层在黑名单校验通过后**串行**补查 `FollowService.get_counts` 与 `MomentFeedService.get_upstat` 并内联返回（串行而非 `asyncio.gather`——同一 `AsyncSession` 不支持并发 `await`）。原需 3 次 HTTP + 3 次网关鉴权/黑名单判定的悬浮卡片与空间页降为 1 次；两个原端点 2.52.0 删除。前端新增跨组件共享缓存 `src/composables/useUserCardCache.ts`（详见 §5.3），`MomentSpaceView` 移除 `fetchRelationStat` / `fetchUpStat` 两次独立请求。
- **删除 `/community/upstat` 与 `/message/follow/stat`（2.52.0）**：统计已由 `/user/space/info` 内联返回，两端点无任何调用方（前端薄封装 `fetchUpStat` / `fetchRelationStat` 随之移除）。同时删除 `MomentUpStatResp` 响应模型（由 `SpaceUpStat` 取代）、`FollowCountResp` **保留**（`/message/follow/count` 仍在使用）；`tests/test_str_int_route_params.py` 的 StrInt 回归 URL 列表移除对应两条（保留 `/user/space/info`）。**破坏性变更**：对外端点移除，按本计划书 2.49.0（删除 `/notify/read`）先例记为 MINOR。
- **系统通知「读取即已读」（2.49.0）**：`NotifyService.pull` / `list_for_user`（含 B 站风格 `/notify/system`）在构造完出参后调用内部 `NotifyService._mark_read_ids` 把本页 id 批量 upsert 为已读（幂等）；对外删除 `POST /api/v1/message/notify/read` 与 `NotifyReadResp`，`NotifyReadReq` 因仅剩删除在用更名 `NotifyDeleteReq`；`/notify/list` 移除 `only_unread` 参数。前端 `NotifyListView` 去掉「标记已读 / 全部已读 / 仅看未读」，改为加载完成后 `emit('refreshUnread')` 让红点跟着清零；`message-api.ts` 移除 `markNotifyRead` 与 `NotifyReadResp` 导出。
- **前端事件/评论枚举迁移对齐唯一真相源（2026-09-01）**：SDK 重新生成后 `EventTypeEnum` / `SourceTypeEnum` / `CommentTypeEnum` 已从 hey-api 移除，相关前端代码全部迁移到 `InteractionActionTypeEnum`（事件类型，取值 1~7 与旧 `EventTypeEnum` 完全一致、新增自 8 起）与 `InteractionBizTypeEnum`（业务类型；评论区 `CommentTypeEnum.LOTTERY=3 → InteractionBizTypeEnum.LOTTERY=2` 数值有变、必须替换）。涉及：`message-api.ts`（`EventType`/`SourceType` 类型别名改指新枚举）、事件三视图（Reply/At/LikeListView）、事件卡片族（`cards/index.ts`、`useEventCard.ts` 的 `EVENT_TYPE_VALUES`/`EVENT_CARD_TABLE`/`actionTextMap` 与 `business === InteractionBizTypeEnum.COMMENT` 判断）、`eventJump.ts`（`openFallback` 的 `SourceTypeEnum` 与评论详情 `CommentTypeEnum` 判定改用 `InteractionBizTypeEnum`）、评论区（`lottery_comment.ts` 重导出、`MomentDetailView`、`lottery_detail.ts`、`LotteryCommentSection`、`MomentCard`）。事件出参 `business` 现直接为 `InteractionBizTypeEnum` 值，前端资源类型判断同步改用新枚举。
- **事件资源定位统一（resource_type + Biz 批量快照，2026-09-02）**：事件跳转身份收敛为 `(resource_type, resource_id)`，由后端 `FrontendRouteEnum` + `build_route_target` 下发 `jump_target`（`route:{name}?{query}`），前端 `openEventDetail` 退化为 `jumpToTarget(router, content.jump_target)`（§2.10 / §5.11 / C20）。复用既有 `BaseBiz`/`GenericResourceBiz` 体系：各资源子类实现 `check_exists()`/`_load_meta()` 钩子（原 `InteractionResourceValidator` 注册式校验下沉为方法），`BaseBiz.get_resource()` 统一装配 `InteractionResource`（`cover` + `jumpTarget`），`batch_get_resources(session, ids, rpid_map=)` 为每类资源的批量接口（`DynamicBiz`/`LotteryBiz` 覆盖为一次 IN 查询 / 批量 RPC）；`EventMsgfeedContent`/`EventItem`/`EventAggregateItem` 新增 `jump_target` / `resource_deleted`，`list_msgfeed`/`aggregate`/`list_detail` 经 `get_biz_class(rt).batch_get_resources(...)` 批量装配，`_resolve_source_meta` 退役（`source_meta.py` 仅留 `_first_pic`）。前端需重新生成 hey-api SDK 以拿到 `jump_target` / `resource_deleted` 字段。
- **评论锚定事件的评论原始信息回捞（CommentBiz 批量快照，2.54.0）**：AT / REPLY 等评论锚定事件的 `source_content` /   `target_content` 由 `list_msgfeed` 直接 `select(CommentContent)` 改为经 `CommentBiz.batch_get_resources` 批量回捞（§5.12）：`CommentBiz` 覆盖 `batch_get_resources`（一次 IN 查 `CommentIndex` + `CommentContent`）并新增 `_load_interactable` / 覆盖 `_build_jump_target`（按所属顶层资源 `type+oid` 带 `rpid` 锚点）；`MsgfeedBuildContext` 新增 `comment_resources`，`_locate_comment` 改从评论快照取正文；`EventMsgfeedContent` 新增 `source_mid` / `target_mid` 下发各楼层评论作者。前端需重新生成 hey-api SDK 以拿到这两个字段。
- **楼层作者昵称随事件下发（2026-09-02 增补 §5.12）**：`EventMsgfeedContent` 在 `source_mid` / `target_mid` 基础上新增 `source_name` / `target_name`，由后端 `list_msgfeed` 回查块经一次 `PptrUser.get_many` 与 `@` 昵称合并批量回查楼层评论作者昵称并随 item 下发；前端 `useEventCard.nicknameOf` 优先采用下发昵称、`mid` 查 `users` 兜底、最终降级「用户{mid}」。前端需重新生成 hey-api SDK 以拿到这四个字段。

- **互动接口通用化 + 路由层瘦身（2.56.0，§5.13）**：`/thumb` `/dislike` `/share` `/report` 四个互动写接口统一为 `bizType`（缺省 `dynamic`）+ `bizId` 定位任意资源（2.56.0 去除 `dynId` 别名，动态资源也一律传 `bizId`），`/dislike` 不再硬编码拒绝非 dynamic、非动态资源也能上报分享与举报；请求解析收口到 `interaction_status.resolve_target()`，`api/moment.py` 内联的 `_verify_resources_exist`（防乱调存在性校验）与 `_query_status_items`（计数 / 用户态 / 详情装配，约 150 行） 迁入 `app/services/interaction_actions/interaction_status.py` 的 `InteractionStatusService`；`BaseBiz` 新增 `client_ip` / `user_agent` 显式属性取代隐式 `getattr` 兜底。
- **私信发送限制（2.57.0，§5.14）**：`DmSessionObject.send` 落库前新增两道闸门——① 每日上限（`dm_daily_send_limit`，默认 1000，统计当天作为发送者的全部私信）；② 陌生人单条闸门（`dm_stranger_gate_enabled` / `dm_stranger_gate_limit`，默认开 / 1）：对方未关注我且未回过我消息时，我至多可发 1 条，回聊或互关即解除。触发分别返回新增业务码 `DM_SEND_DAILY_LIMIT=4001` / `DM_SEND_STRANGER_LIMIT=4002`，消息不落库；`api/dm.py` 对专用异常先回对应 code 再回落通用 400/500。
- **内容发布每日上限（2.58.0，§5.15）**：评论 / 动态（仅 WORD）/ 话题三个创建入口接入「当天创建行计数」上限（`comment_daily_create_limit=100` / `moment_daily_create_limit=30` / `topic_daily_create_limit=10`，env 可调，0=不限制）；软删仍保留 created 行故「删除也算次数」；超限分别回新增业务码 `4101/4102/4103`，不落库。limiter 通用工具 `app/services/common/daily_limit.py`，由各 biz 自治接入。
- **移除动态编辑（2.58.0，§5.16）**：下线 `POST /community/edit` 与 `MomentPublishService.edit`、`MomentEditReq/Resp`；转发/发布/删除/置顶保留；`MomentAuditLogActionEnum.EDIT` 枚举保留（共享）。后端端点移除 + 前端 `editMoment` 封装移除，记 MINOR（前端 hey-api SDK 需重新生成）。
- **私信会话置顶（2.59.0，§5.17）**：`msg_dm_session` 新增 `top_ts`（毫秒，0=未置顶）作为置顶唯一真相源；`DmInbox.list_sessions` 排序统一为 `top_ts DESC → last_msg_ts DESC`（所有页一致，置顶恒在前）；新增 `POST /dm/session/top`（置顶写 now、取消写 0，幂等，可多会话同时置顶）；`DmSessionItem` 新增 `top_ts` 出参、`is_top` 由 `top_ts != 0` 推导。
- **互动态查询开放匿名访问（2.60.0，§5.18）**：`GET /community/interaction/status[/{bizId}]` 依赖由 `RequiredUser` 降级为 `OptionalUser`（匿名 `viewer_mid=0` → `isLike` / `isFavorite` 恒 false、计数照常返回），be-gateway `jwtAuth.unless` 新增 `/api/v1/community/interaction/status` 正则；detail 的浏览 MQ 仍仅登录用户投递（沿用 D26「浏览统计仅登录用户」）；`InteractionStatusService` 装配以 `mid=0` 表示匿名观众。互动写接口不放开。
- **举报列表追加用户信息与资源快照（2.61.0，§5.19）**：`ReportItem` 新增 `reporterName` / `reporterFace` / `accusedName` / `accusedFace` 与内嵌 `resource`（`InteractionResource`），分别由**一次** `PptrUser.get_many` 与按 `bizType` 分组的 `get_biz_class(bt).batch_get_resources` 批量回捞（弱依赖，失败降级为空）；审核队列可直接看到举报人 / 被举报人与被举报内容标题 / 封面，并按 `jumpTarget` 跳转、`exists=false` 展示「内容已删除」。
- **点踩负反馈闭环（2.62.0，§5.20）**：动态 / 话题动态流新增点踩入口（`MomentStatBar` 踩按钮 + `dislikeMoment` 薄封装，复用既有 `POST /community/dislike`，无新端点）；EdgeRank 升级为**双层降权**——全局仍走 `−w_dislike·dislike_ratio`（略降），新增「对点踩者本人大幅降权」（`feed_engine` 精排后处理 `s' = s·scale − weight`，scale=0.3 / weight=5.0，可选 `exclude` 直接剔除），信号源复用既有 `TResourceDislike` 幂等明细（不新增表）；`InteractionStatusItem` 新增 `isDislike` 出参（向后兼容，匿名恒 false）；**点踩计数不外露**（`dislikeCount` 仅内部供 EdgeRank 降权，不出参、前端不展示）。

### 7.2 遗留 / 待办

- **评论前端组件**（`CommentEditor`/`CommentList`/`CommentSubList`/`CommentCard`）：阻塞于前端仓库接入，未实施。
- **回复通知出参对齐 B 站 x/msgfeed/reply**（Phase L）：`EventMsgfeedContent` 补 `subject_id/root_id/source_id/target_id` + 三段评论正文 + `like_state/follow`，list_msgfeed 批量回捞（SQL 次数恒定）。
- **动态审核总统计**（Phase M）：`GET /moment/audit/statistics` 按 dynType+auditStatus 聚合。
- **i18n 前端**：Phase 5–11（rpa-browser views/components、lottery_data、moment、admin、stores/utils 文案）；`generated.ts` 8 处 TS 错误需收尾修复。
- **评论性能**：`EXPLAIN` 覆盖索引验证、深翻页游标分页待补。
- **中台流程**（RPA-Browser 治理层）：审批强制联动（execute/publish 校验 approved 审批单）、举报审核端点、细粒度权限、管理员操作审计表等（P0/P1/P2 阶梯）。
- **前端类型遗留**：moment-api.ts 一批既有类型错误（SDK 更新引入），非计划书范围内。
