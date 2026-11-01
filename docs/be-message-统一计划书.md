# be-message 系统统一计划书

> **定位**：be-message 生态（后端 `be-message-service` + 共享层 `bili-common` + 前端 `Vue3FrontEndDemoExercise`）的**唯一权威计划书**，只保留当前现状；历史演进过程请查阅 git 历史。
> 关联规则：新增/修改功能需**先改本计划书再改代码**；前端 SDK（`src/api/**/hey-api/`）为生成代码**禁止手改**。

---

## 1. 系统架构与边界

| 组件 | 职责 | 技术栈 |
| --- | --- | --- |
| `be-message-service` | 消息（通知/事件/私信/推送）、动态 Moment、评论、收藏夹、用户中心、审核管理 | FastAPI + FastStream(RabbitMQ) + SQLModel + Alembic + APScheduler，仅 MySQL |
| `bili-common` | 共享层：响应码/异常、雪花 ID、RPC 契约与客户端、i18n、推送、枚举/模型 | 纯 Python 包 |
| pptr Postgres | 用户主数据（`TUserInfo/TUserDetail/TUserLevel/TUserVip` 等） | be-message 接管读写，跨库不 JOIN，快照建本地表 |
| RPA-Browser / be-bilibili-crawler | 非动态资源（lottery/rpa_*）详情经 RPC 提供；RPA 网关转发 | RabbitMQ 同步 RPC |
| 前端 `Vue3FrontEndDemoExercise` | 用户端 + 管理后台 | Vue3 + TS + Tailwind + Element Plus + hey-api SDK |

**存储边界**：MySQL 主库 `BiliMessageDB` 存业务主数据；私信正文按月分库 + 100 表；图片只存 URL；用户主数据在 pptr Postgres，be-message 只建展示快照避免跨库 JOIN。

---

## 2. 统一工程约定

- **响应契约**：**失败一律返回非 200 的 HTTP 状态码**（HTTP 状态只表达错误大类，无需与 `body.code` 同值）；业务细分仍看 `body.code`；公共业务码单一来源 `bili_common.models.response_code.ResponseCode`；未登录恒 `NotLoggedInException`（业务码 -101 + HTTP 401）。映射规则见 `bili_common.exceptions.http_status_for_code`（400~599 沿用、-101→401、其余自定义业务码→400、未捕获异常→500）；业务代码里「HTTP 200 + 非 0 业务码」的返回由 `bili_common.middlewares.ErrorStatusMiddleware` 在出口统一改写。
- **对外 ID**：雪花 ID 字符串出参；分钟级短 ID 位布局 39 bits、`sequence_bits` 默认 4 可配（限清库开发环境）；实体独立 worker/epoch。
- **字符串版 ID 字段后缀**：响应模型的雪花 ID 除数值字段外，由 **`@auto_str` 类装饰器**（`bili_common.models.auto_str`）自动派生字符串版字段，**后缀优先级：装饰器 `suffix=` 参数 > 类属性 `_auto_str_suffix` > 默认 `"Str"`（`mid` -> `midStr`）**；出参整体为 snake_case 的模型可用 `"_str"`（`mid` -> `mid_str`）。**同一接口内不得混用两种后缀**；新增模型按其字段命名风格二选一，禁止为兼容存量而全局改默认后缀（改默认=破坏性变更，需同步重生成全部前端 SDK）。可选字段（``X | None``）按内层类型判定，同样派生，出参为 ``str | None``。
- **派生机制**：一律用 `@auto_str` 装饰器（**不再用 `AutoStrMixin` 继承**，后者仅作遗留兼容保留）。装饰器在类创建**之后**注入 `computed_field`，因此必须重建 `__pydantic_decorators__` 再 `model_rebuild(force=True)`——pydantic 只在 `ModelMetaclass.__new__` 里 build 一次 decorators，`model_rebuild()` 不会重新扫描类字典；重建时须以既有 decorators 为底合并（否则类体手写的 `@computed_field` / 校验器会丢）。模型含「指向本模块后面才定义的类」的前向引用时，重建会暂时失败，交由 pydantic 的 `MockValSer` 在首次使用时自动重试。
- **枚举落库**：业务枚举一律标准库 `enum.IntEnum`，模型字段 `Field(sa_type=IntEnum(EnumCls))` 落 SMALLINT 整数；**禁用原生 ENUM**（存成员名会导致查询/过滤错乱）；列类型从 `bili_common.models.db_types` 导入 `IntEnum/StrEnum`。
- **鉴权**：身份来自网关注入 `x-bili-*` 头（微服务互信）；依赖注入 `CurrentUser/RequiredUser/AdminUser/RootUser`（管理端审核统一 `RootUser`）。
- **i18n**：后端 bili-common 层 fastapi-i18n + 延迟翻译；前端 vue-i18n + Accept-Language。
- **MQ 契约**：`bili_common/rpc/` 统一收编；`bili_common.exceptions` 统一异常。
- **模型文件命名**：`app/models/db/` 各表模型统一 `_tbl` 后缀；包导出方式不变。
- **输出模型命名**：对外响应模型统一 `XxxOut` 后缀（对齐 FastAPI「输出模型过滤」语义）；字段可见性一律用 `Private()` 标记 + 序列化期上下文裁剪表达（见 §5.12），**不再用 Public/Private 继承**。
- **跳转契约**：后端只发前端路由名（`route:{name}?{query}`，枚举 `FrontendRouteEnum`），路径只在前端路由表写一次。
- **推送/服务标识配置单一来源**：`bili_common.core.push_settings.PushNotifySettingsMixin`（pydantic 片段，供 `BaseSettings` 混入）承载各服务共用的推送与会话标识字段——`message_config`（全局渠道配置，单 JSON 环境变量 `MESSAGE_CONFIG`）、`SERVER_NAME` / `SERVER_ADDRESS`、`hitokoto_api_url`、`pushme_url` / `pushplus_url`（渠道默认端点）、`rabbitmq_url`。
  - `be-message-service/app/core/config.py`、`RPA-Browser/app/config.py`、`be-bilibili-crawler/CONFIG.py` 的 `Settings` 统一写成 `class Settings(PushNotifySettingsMixin, BaseSettings)`：**mixin 必须排在 `BaseSettings` 之前**（pydantic 才能把基类注解收成字段，且环境变量 / `env_file` 覆盖行为不变）；服务各自的差异默认值在自己的类体里覆盖——`SERVER_NAME`（`rpa-browser` / `be-bilibili-crawler`）、be-message 的 `message_config = PushChannelConfig(hitokoto=False)`（本服务不拼随机句子）。`rabbitmq_url` 的默认值（`amqp://guest:guest@rabbitmq:5672/?heartbeat=180`）也收敛到 mixin，RPA-Browser 与 be-message-service 不再各自声明。
  - **禁止再复制渠道配置模型**：`PushChannelConfig` 单一来源为 `bili_common.models.push`（历史上 `bili_common` / `RPA-Browser` / `be-bilibili-crawler` 各有一份副本，已收敛）；RPA 侧 `app.config` 继续 re-export 以兼容存量 `from app.config import PushChannelConfig` 的引用。
  - 需要按 `host/port/user/password` 自行拼连接串的服务（crawler）不使用共享的 `rabbitmq_url`，其 `RabbitMQConfig.broker_url` 维持原拼接方式。
  - **服务标识前缀单一来源**：`[服务名@地址]` 的拼接收敛到 `bili_common.core.push_settings.build_server_label(settings)`——服务名取 `settings.SERVER_NAME`，被环境变量置空（模板里的 `SERVER_NAME=`）时回落**该类字段声明的默认值**（各服务 `Settings` 里写的服务名），最后 `unknown-service` 兜底；地址取 `settings.SERVER_ADDRESS`，缺省自动取本机 hostname。RPA-Browser 的 `app/services/message/push_msg.py` 与 be-bilibili-crawler 的 `Utils/推送/PushMe.py` 各自保留零参 `server_label()` 包装（历史调用点零改动），内部只委托一次，不再各写一遍逻辑。
- **日志**：loguru。

---

## 3. 数据模型（当前）

- MySQL 主库核心表按域：`msg_comment_*`（评论区/索引/内容/动作/at/report）、`msg_dm_*`（会话/索引/内容分片）、`msg_notify/msg_event`、`TMoment/TMomentTopic(+Rel)/TFavoriteFolder`、`TResourceFeed/TResourceLike/Dislike/Favorite/Report/AuditLog`、审核单 `TUserAvatarAudit/TFolderCoverAudit`、`TInteractionStat`、`moment_author_quality`、`TFeedImpression` 等。
- **通用资源型表抽象**：`ResourceBase`（pk+bizType+bizId+mid+时间戳）+ `ReportBase`（举报单结构）。任意资源以 `(bizType, bizId)` 唯一定位。
- **审核状态列统一**：各资源审核/单据状态列统一为 `ResourceAuditStatusEnum` 枚举列（见 §5.1）；`CommentIndex.auditStatus` / `DmMessageIndex.auditStatus` / `TMoment.auditStatus` / `TMomentTopic.auditStatus` / `TUserAvatarAudit.auditStatus` / `TFolderCoverAudit.auditStatus` / `TResourceFeed.auditStatus` 同源。
- **举报表**：`TResourceReport`（继承 ReportBase，bizType+bizId），dynamic/lottery/rpa_*/comment/user 共用一张；评论另有 `msg_comment_report`。

---

## 4. API 总览（当前，按功能域）

- **动态 Moment** `/api/v1/community`：发布/删除/转发/详情/互动（`thumb/dislike/share/report/repost/favorite`）/置顶/Feed（综合/话题/关注流/空间）。
- **评论** `/api/v1/comment`：发表/列表/楼中楼/赞踩/置顶/@/举报/管理端审核队列。
- **消息** `/api/v1/message`：`notify`（通知）/`event`（事件）/`dm`（私信，含 send/审核/置顶）/`setting`/`msg_feed`/`follow`/`push`（投递/测试/`feedback` 用户反馈，见 §5.11）/`admin`。
- **收藏夹** `/api/v1/favorite`。
- **用户中心** `/api/v1/user`：空间信息/资料更新（头像审核）/登录经验。
- **管理端**：评论/动态/话题/头像/封面/举报审核队列 + 统计。
- **RPC**（RabbitMQ 同步，非 HTTP）：`message.notify.rpc.publish_notify`、`message.push.rpc.*`、`message.pptr.rpc.*`（用户读写）、`message.geoip.rpc.resolve_ip_region`（IP 属地解析，见 §5.21），be-message 也作为 RPC 客户端调 RPA/lottery 详情。
- **RPC 调试**（管理端，root）：`/api/v1/message/admin/rpc-debug`（`methods` 列出可测契约方法、`invoke` 真实往返并回显信封，见 §5.22）。

### 4.1 关注 / 粉丝列表的可见性窗口（2026-10-08 新增）

**背景**：个人空间要新增「关注详情页 / 粉丝详情页」（头部「关注 N」「粉丝 N」可点进去）。B 站对**他人**的关注/粉丝列表只开放最新一小段（前端最多 5 页），只有本人可以翻到底；本项目对齐该行为，但把「窗口大小」放在**后端**强制，前端只负责不渲染第 6 页。

**接口变更**（`/api/v1/message/follow`，对标 B 站 `x/relation/followings` / `x/relation/fans`）：

| 接口 | 变更 |
|---|---|
| `GET /followings`（原 `/following/list`） | query 改为 **`vmid`**（StrInt，可选，缺省= 当前登录用户）+ **`pn`**（页码，从 1）+ **`ps`**（每页，1~100，默认 24）；`summary` 改为「关注列表」 |
| `GET /fans`（原 `/followers/list`） | 同上；`summary` 改为「粉丝列表」 |

- `vmid` 缺省时行为与改造前完全一致（我的关注 / 我的粉丝），**旧路径已重命名，无其它调用方**（前端 SDK 有 `listFollowing*` / `listFollowers*` 但从未被页面使用）；
- 响应结构沿用现有 `FollowListResp`（`items` / `total` / `page_num` / `page_size`），**不引入游标**；B 站的 `order=desc` / `order_type=attention` 本期不做（下轮补）；
- 访问者身份**不来自 query**：网关注入 `x-bili-mid` → `CurrentUser`，后端只需比较 `viewer == owner`。

**可见性窗口规则**（`FollowService` 内统一实现，API 层不写业务）：

- `viewer == owner`（看自己）：**不限制**，可一直翻页；
- `viewer != owner`（看他人 / 未登录访客按访客身份）：**只允许前 5 页**（默认 `ps=24` 时即最新 120 条）。`pn > 5` 时**直接返回空 `items`**，`total` 仍返回真实总数（前端据此显示「仅展示最新 N 条」提示，不显示空白页）；
- 空列表**不是错误**：`code=0`，与用户给的 B 站形状 `{"list": [], "offset": "", "re_version": 0, "total": N}` 语义一致（超出窗口即空列表），前端不需要 try/catch；
- 「TA 的粉丝」主页模块原有的 `show_fans_list` 隐私门控与 `SPACE_FANS_MAX=500` 截断**保持不变**，本次窗口规则只作用于 `following/list` 与 `followers/list` 两个接口。

**本期不做**（另开需求）：关注分组（建表 + 分组 CRUD + 打标签）、列表内关键词搜索、`sort` 排序参数（B 站的「最近关注 / 最常访问」）。排序当前硬编码 `created_at DESC`。

### 4.2 关注分组（tag，2026-10-08 已实现）

接口（对齐 B 站，`data` 直接是数组/对象，不套 `list`）：

| 接口 | 说明 |
| --- | --- |
| `GET /api/v1/message/follow/tags` | 我的分组列表（特别关注 → 默认分组 → 自建分组） |
| `POST /api/v1/message/follow/tags` | 新建分组 `{name, tip?}`（名称 1~20 字、不重名、最多 20 个） |
| `DELETE /api/v1/message/follow/tags/{tag_id}` | 删除自建分组（连带清关系；系统分组不可删） |
| `GET /api/v1/message/follow/tags/assigned?target_mid=` | 某用户当前所属的分组 id 列表（分组弹窗预填） |
| `POST /api/v1/message/follow/tags/assign` | 覆盖式设置某关注对象的分组 `{target_mid, tag_ids[]}`（空数组=移出全部分组） |
| `GET /api/v1/message/follow/followings?...&tagid=` | 关注列表新增 **`tagid`** 过滤（仅自己视角生效；`0`=未分组的默认分组） |

- **不需要 `kind` 参数**：B 站「关注 / 粉丝 / 分组」是**三个独立接口**，本项目同样按路径分流，不引入 `kind` 之类的分流字段；
- 分组响应形状（对齐 B 站 `x/relation/tags`）：
  ```json
  {"code": 0, "msg": "success", "data": [
    {"tagid": -10, "name": "特别关注", "count": 5, "tip": "第一时间收到该分组下用户更新稿件的通知"},
    {"tagid": 0, "name": "默认分组", "count": 3127, "tip": ""}
  ]}
  ```
  本项目用 `StandardResponse`（`code` / `msg` / `data`）包装，不引入 B 站的 `ttl` / `message` 字段。

**存储**（Alembic 迁移 `20261008_follow_tag`，仅 MySQL 主库）：

| 表 | 关键列 | 约束 |
| --- | --- | --- |
| `msg_user_follow_tag` | `mid` / `name(20)` / `tip(100)` | `uq(mid, name)`；`idx(mid, created_at)` |
| `msg_user_follow_tag_user` | `mid` / `tag_id` / `target_mid` | `uq(mid, tag_id, target_mid)`；`idx(tag_id)`、`idx(mid, target_mid)` |

- **关系表必须带 owner `mid`**：`tag_id = -10`（特别关注）是全用户共用的约定值，唯一键只取 `(tag_id, target_mid)` 会跨用户串号；
- **`msg_user_follow` 不加列**：分组是可解耦的附属标签，取关 / 拉黑时只删关系行（`FollowTagService.clear_target`，与关注关系变更同事务提交）；
- **系统分组不落定义表**：`-10` 特别关注的关系行落库但定义内置；`0` 默认分组不落关系行，`count = 关注总数 − 各分组 count 之和`；
- 分组只允许作用于**当前正在关注**的人（`assign` 校验），避免幽灵成员；
- **列表查询策略**：`GET /tags` 在**同一个 session 内顺序跑 3 条窄查询 + 应用层拼装**，采用**业内最常用的「多条简单查询」方式**（**有意不做 UNION / 巨型 JOIN 压缩**：计数与分组定义本就不同构，拆成 3 条各自都能稳定命中索引，简单直白的多条查询比缝成一条语句更易读、更易测、更好按需加索引）：
  1. `_tag_counts`：各分组计数（`GROUP BY tag_id`，含特别关注 `-10`）；
  2. `_count_default`：默认分组计数（`NOT EXISTS`）；
  3. `_list_tag_defs`：分组定义（含 0 成员的**空分组**，必须单列：计数只覆盖「有成员的分组」）；
  - 三条互相独立，索引 `idx_follow_tag_user_tag`、`idx_follow_target_status`、`idx_follow_tag_mid`，执行计划简单可测，后续加字段不用改一条缝在一起的巨型 SQL；
  - 默认分组**不用**「关注总数 − 各分组之和」：同一人可属多个分组，减法会算错，必须用 `NOT EXISTS`；
  - `AsyncSession` 非并发安全，**不能** `asyncio.gather` 并发跑这几条；同 session 顺序执行即复用同一连接；
  - 若要压到「一次查询」，业界通行做法是**冗余计数列**（`msg_user_follow_tag.member_count` 写时 ±1），读时只查定义表（B 站 `count` 即服务端缓存值），代价是计数可能短暂不一致 —— 本项目暂不引入。

**本期仍不做**：列表内关键词搜索、`order` / `order_type` 排序（「最近关注 / 最常访问」），排序硬编码 `created_at DESC`。

**可见性门控已统一（2026-10-08 补）**：`follow/followings` 与 `follow/fans` 在 `viewer != owner` 时按空间主人的 `show_follow_list` / `show_fans_list` 开关门控（`FollowService._ledger_visible_to_viewer`），关闭时返回**空列表且 `total = 0`**（整类不出现，连总数都不暴露）。本人视角恒可见。主页粉丝模块沿用的 `community/space/fans` 门控为同一开关，口径一致；其 `SPACE_FANS_MAX=500` 截断保留（主页模块只做概览）。

---

## 5. 核心机制

### 5.1 审核状态机（统一枚举 + 资源化 + 多审核环节）

- **统一枚举 `ResourceAuditStatusEnum`**（`app/models/enums.py`，`NORMAL=1` 基准）：
  `NORMAL=1 / AUDITING=2（待审，单据 PENDING 亦映射本值）/ REJECTED=3 / HIDDEN=4 / DELETED=5`。
  已收敛删除旧审核枚举：`MomentAuditStatusEnum`/`MomentTopicAuditStatusEnum`/`CommentStateEnum`/`DmAuditStateEnum`/`AvatarAuditStatusEnum`/`FolderCoverAuditStatusEnum`（旁路 `CommentSubjectStateEnum` 评论区开放态、`DmMsgStatusEnum` 消息撤回态独立保留，不并入）。
- **状态机骨架**（`app/services/moderation/`，纯新增）：`AuditStateMachine`（模板方法，显式 `TRANSITIONS` 迁移表 + `on_enter` 副作用钩子 + 统一写 `TResourceAuditLog`），非法流转在 `transition()` 单一入口抛 `StateTransitionError`。
- **多审核环节编排**（`flow.py`）：`AuditFlow` + `AuditFlowOrchestrator`——一个资源可挂多个审核环节（自动文本 / 人工内容 / 举报处置），**主状态**（资源 `auditStatus` 决定可见性）由各环节经编排器单一入口联动，环节自身 pending/reject 记流水/子表。举报单（`ReportAuditStatusEnum`）独立不并入主状态。
- **各资源规则要点**：
  - **动态**：`AUDITING→NORMAL/REJECTED/HIDDEN`；FORWARD 涉及源 `repostCount ±1`；驳回通知作者；失误过审可从 NORMAL 驳回。
  - **话题**：创建即 AUDITING；通过→NORMAL+pubTime（不发通知）；驳回→REJECTED+通知创建者；仅 NORMAL 话题可关联/入广场热搜。
  - **头像/封面（单据）**：提交 URL 校验→AUDITING；通过→写公开字段+通知；驳回→保持原值+通知；同用户至多一条 pending。
  - **评论**：DFA 敏感词同步拦截（高危 REJECTED、疑似 AUDITING）；审核中作者可见；过程态不通知，仅驳回/下架通知；互动通知仅对 NORMAL，恢复后补偿补发。
  - **私信**：管理端审核 `NORMAL/AUDITING/REJECTED/HIDDEN`，不可见态聊天窗过滤。
- **审核流水**：`TResourceAuditLog`（bizType+bizId）承载全部资源审核流转记录，管理端统一查询。

### 5.2 消息投递模型

- **通知（读扩散）**：发布即对目标可见，`/pull` 游标去重；可见性读取时过滤；`publish_at` 用 `func.now()`。**入口唯一** `NotifyService.create`（含幂等包装），管理端/RPC/系统触发均落到它。
- **事件（写扩散）**：`EventService.report` 组装 `dedup_key` 幂等；`biz_id` 落库并全链路出参。
- **@/回复黑名单闸门**：@ 本身允许落库渲染，但提醒绝不投递进黑名单用户；闸门收敛于 `BaseEvent.report` 一处。
- **私信（写扩散）**：会话/索引主库 + 正文异步分片（`content_ready` 兜底返回摘要）+ 死信补偿。
- **站内信 vs 第三方推送**：站内信（通知/事件/私信）由 DB 写路径保证送达，不经第三方；第三方推送仅 `/push` 站外提醒。

### 5.3 动态渲染与装配（对齐 B 站 Moment 模型）

- 卡片模块化渲染对齐 `DynModuleType`（author→extend→desc→dynamic→interaction），附加卡独立 `module_additional`。
- attach 卡只存 `bizType+bizId`，读取时 RPC 实时取详情，禁存快照。
- 富文本节点：WORDS/AT/TOPIC/LINK（外链图 `picMeta.renderAsImage`）。
- 卡片点击：正文文字不跳详情，跳转由显式入口触发；@/话题/资源节点各自跳转。
- **转发语 @**：FORWARD 动态（`/repost` 与 `POST /create`(scene=FORWARD) 双路径）正文 `AT` 节点与发布同源——落库渲染 + 触发 AT 事件，黑名单闸门同一处生效（`BaseEvent.report`）。

### 5.4 排序与计数

- **EdgeRank**：`Σ(w·log(count+1))·decay(pubTime)`；综合 Feed 扩展为多维打分 `content_quality·decay + author_signal + fresh_bonus + feedback_penalty + personalized/anon`；时间衰减基准用 `max(pubTime, 最后评论时间)`。
- **推荐流**：`sort=recommend` 无 page/offset，客户端 `last_showlist`（上限 100）去重；登录个性化（关注/互动作者/话题偏好加权）、未登录匿名随机扰动权重；候选五路召回（热门趋势/社交/内容标签/地理/协同过滤近似）并集去重后 `rank_feed` 精排。
- **候选召回去时间窗口硬约束（2.65.0）**：`edgerank_candidate_window_hours` 由**硬过滤**降级为**新鲜优先窗口**——窗口只决定「优先召回谁」，不再决定「内容能不能被看到」，新鲜度排序交给 EdgeRank `decay` 表达：
  - **互动 top 路**自带独立窗口 `edgerank_recall_hot_top_window_hours`（默认 0=不限）：高互动老内容可入池，避免「窗口内没互动、窗口外有爆款」的错配；
  - **兜底路**（`edgerank_recall_fallback_*`）：五路并集后候选不足**保底条数**（默认 = `page_size`）时，按 pubTime 倒序放宽窗口补全，保证低活跃 / 冷启动 / 存量数据场景 Feed 不见底（与曝光去重「尽力去重 + 自动降级」同一思路）。
- **重排层 Re-Rank（2.65.0）**：补上业界标准链路「召回 → 粗排 → 精排 → **重排**」缺失的最后一环，解决「纯按分排序 = 同质化 + 老内容没机会」：
  - **Thompson Sampling（EE 探索）**：`θ ~ Beta(1+pos, 1+neg)`（pos=互动数、neg=曝光未互动数），加分 `w·base·(θ − E[θ])`——数据少的（新内容 / 低曝光）后验宽、波动大 → 有冒头机会；数据多的收敛到真实互动率 → 稳定利用；**零曝光内容不参与**（θ 退化为先验 U(0,1)，纯噪声会盖掉时间序）。计数按 `edgerank_ts_max_count` 截断，防千万级曝光爆款把分布锁死；采样按 `(viewer_key, bizId)` 确定性派生，同一观众刷新不跳变。
  - **MMR 多样性打散**：`MR_i = λ·rel_i − (1−λ)·max_{j∈S} sim(i,j)`，rel 取批内 min-max 归一化，`sim` = 同作者 + 话题 Jaccard；只对精排 top-K 贪心重排，防整页被同一作者 / 同一话题刷屏；**只调顺序不改集合**。
- **机器学习推荐（2.66.0）**：在 2.65.0 的链路之上引入**传统机器学习**三件套（均为 CPU 可训练、无 GPU 依赖），EdgeRank 退为**兜底基线 / 对照组**，全链路开关可灰度：
  - **P0 行为埋点 `TFeedEventLog`**（一切 ML 的前提）：一次事件一行——`impression`（下发时服务端写，含 `position` / 下发分）/ `click`（前端上报进详情）/ `dwell`（前端上报停留毫秒）。事件表与 `TFeedImpression`（去重用的累计表）分离：前者是只追加的明细流水，后者是去重点查表。上报接口 `POST /api/v1/community/feed/events`（批量、匿名可报、单批上限 100）。
  - **样本构建 `scripts/build_feed_samples.py`**：把「一次曝光」与曝光后 `ml_label_window_hours` 内的互动明细（like/comment/favorite/repost）join 成样本，**graded label** = 0 无互动 / 1 点赞 / 2 评论 / 3 转发或收藏；负样本即「曝光了但没互动」。`groupId = (viewerKey, servedAt 截断到分钟)` 作为 LambdaRank 的 query 分组。产出 CSV 到 `data/ml/`。
  - **精排 `LightGBM LambdaRank`（`app/services/moment/ml_ranker.py`）**：传统 ML 里做排序的最优解（自动特征交叉、支持 listwise 排序目标、推理快、可解释）。特征三类——内容侧（作者、话题数、是否富媒体/转发、发布时间年龄、历史互动率、作者质量）、用户侧（关注关系、偏好话题命中）、上下文（时段、曝光位置）。**分数融合**用动态量纲对齐 `final = (1−w)·base + w·ml_scaled`（`ml_scaled` 按两列均值对齐到 base 量纲），避免硬编码量纲；`w` 即灰度权重。模型文件 `settings.ml_ranker_model_path`，按 mtime 热重载。
  - **召回 ALS 协同路（`app/services/moment/als_recall.py`）**：隐语义协同过滤（隐式反馈 ALS），离线训练脚本产出 user/item 因子，在线用「用户向量 · 物品向量」top-N 召回一路（未登录 / 冷启动用户跳过）。优先用 `implicit`，不可用则回退 numpy 版 ALS（避免编译依赖绑架部署）。
  - **探索 `LinUCB`（`app/services/moment/linucb.py`）**：带上下文特征的线性老虎机（传统在线学习），替代/叠加 2.65.0 的无特征 Thompson Sampling——`ucb = θᵀx + α·√(xᵀA⁻¹x)`，A/b 存 `TFeedBanditArm`，由定时任务回放事件离线更新（不在请求路径写），冷启动 arm 用单位阵。小样本友好。
  - **训练脚本与闸门**：`scripts/train_feed_ranker.py`（LambdaRank，产出 `data/ml/feed_ranker.txt` + 离线指标 `data/ml/metrics.json`，含与「按下发位次排」baseline 的 NDCG 对比，**打不赢 baseline 就不该上线**；正样本 < 50 直接拒绝产出模型）、`scripts/train_als_recall.py`（`implicit` ALS → `data/ml/feed_als.npz`）、`scripts/train_linucb.py`（回放事件重算 `A += xxᵀ, b += r·x` 覆写臂参数）；行为灌数 `scripts/seed_feed_behavior.py`（`--clean` 清数据并回滚互动计数）。
  - **开关与灰度（`feed_ml` 运行时配置）**：三件套的开关与权重登记为运行时配置项 **`feed_ml`**（值模型 `FeedMLConfig`），复用既有 `msg_sys_config` 配置中心——`GET/POST /api/v1/message/admin/sys-config` 即可热更新（进程内 TTL 缓存默认 10s，**无需重启**）；`ml_*` settings 仅作代码默认值 / 兜底。只读观测接口 `GET /api/v1/community/feed/ml-status` 返回生效配置 + 模型文件就绪状态 + 上次离线指标 + 臂参数行数 + 曝光样本量（样本 < 千条时模型不可信）。
  - **数据前提**：模型收益 ≈ f(数据量)。当前库内正样本仅个位数，故上线顺序固定为「先埋点攒数据 → 再训练 → 灰度放量」；`scripts/seed/` 灌行为数据用于跑通链路与离线评测（AUC / NDCG@K），**灌数只验证链路，不代表线上收益**。
- **曝光去重**：`TFeedImpression`（viewerKey+bizType+bizId+scene）TTL 24h 内不下发重复；尽力去重、候选不足逐级放宽保证 feed 不见底。
- **计数统一**：高频计数走「明细表 + 原子 ±1」（禁 COUNT），同事务保证一致，无定时对账；`TInteractionStat` 承载全互动计数；浏览去重 `TInteractionViewLog` 每用户每资源一行、跨自然日才 +1。
- **点踩负反馈闭环**：全局 `−w_dislike·dislike_ratio` 略降 + 对点踩者本人精排后大幅降权（`s'=s·scale−weight`）；点踩计数不外露。
- **通用资源 Feed 引擎**：`feed_engine`（FeedProvider 适配器）统一对任意 `bizType+bizId` 做 EdgeRank/去重/个性化；动态渲染回 `TMoment`，其他资源走 RPC 详情。

### 5.5 泛化互动与 RPC 详情

- 点赞/收藏/浏览/点踩/分享/举报/转发支持多资源；be-message 只存互动明细+计数，详情经 RPC 实时获取、失败降级。
- **资源为中心的统一操作模型**：`interaction_actions/` 以 `InteractionBizTypeEnum` 为主体（`BaseBiz` 资源类体系，见 §5.10），互动操作、举报、审核处置均为资源方法。
- **抽奖卡片详情 HTTP 接口（be-bilibili-crawler 侧）**：`POST /api/v1/lottery_database/bili/GetLotteryDetail`（body `{lottery_id}`）按 `dyndetail.lotdata.lottery_id` 返回完整卡片原始行（LotdataResp 形态）+ `t_lot_extra_info` 附加信息，供前端卡片详情页（`/app/lot-data/card-detail?id=`）按 id 拉取详情渲染，替代 localStorage 旧缓存传参。
- **互动资源 ID 口径（2.61.0 修正）**：
  - `lottery`（bizType=2）一律 `lotdata.lottery_id`；预约 sid / 天选 lot_id **不得**作为 lottery 的互动资源 ID，缺失 `lottery_id` 的旧数据前端禁用互动。
  - **第三方抽奖动态另立资源类型 `others_lot_dyn`（bizType=15，bizId=`biliopusdb.t_lotdyninfo.dynId`）**。原「第三方 dynId 不作为互动资源 ID」是**针对 lottery 命名空间**的约束（dynId 不是 `lottery_id`，拿它当 lottery 的 bizId 会被 `check_lottery_exist` 判不存在 → 点赞/收藏 400、详情/跳转定位失败）；本次按资源唯一性原则（`(bizType, bizId)` 唯一确定资源）为其单开命名空间，**不是**把 dynId 塞回 lottery，两条口径不冲突。
  - 因此第三方抽奖卡片的评论 / 收藏 / 点赞 / 举报 / 跳转一律用 `bizType=others_lot_dyn + bizId=dynId`；存在性经新增 RPC `check_others_lot_dyn_exist`（查 `t_lotdyninfo.dynId`）校验，与 lottery 的 `check_lottery_exist` 完全隔离。
  - 迁移注意：`others_lot_dyn` 上线前以 `lottery+dynId` 写下的评论（若已存在）落在 `type=2` 的评论区，与新 `type=15` 评论区不是同一个 `CommentSubject`，属历史脏数据（该路径此前必然 400，实际存量应为空），不做自动迁移。

### 5.6 通知可见性细节

- 受众解析 `resolve_target_mids`（按 `recv_notify`）；投放类型 ALL/CUSTOM/LEVEL/ROLE/VIP；免打扰由 `can_push_now` 判定。
- **读取即已读**：`/notify/pull` 等构造出参后批量 upsert 本页为已读，出参 `is_read` 是读取前快照；无 `/notify/read` 接口、无 `only_unread` 参数（翻页收缩跳条）。
- **网关匿名白名单（评论读接口）**：`GET /api/v1/comment/latest`（首页最新评论）与 `comment/main`、`comment/detail/{rpid}`、`comment/sub` 同口径放入 be-gateway jwtAuth `unless` 白名单——be-message 侧本就经 `resolve_optional_viewer` 允许匿名（匿名仅不回填点赞态），此前 latest 漏配导致未登录访问首页 401。评论写接口（add / reply / delete / audit 等）仍走 jwtAuth + 上游 RequiredUser。

### 5.7 seed 灌数（`scripts/seed_cli.py` 唯一入口 + `scripts/seed/` 功能分包）

- `uv run python scripts/seed_cli.py` 顺序跑全互动 + 大数据灌数两阶段；`seed_cli.py` 只做「sys.path 注入 → 调 `seed.cli.main()`」，CLI 参数与行为保持不变（禁止把逻辑回写进单文件）。
- 数据源只读真实库（动态/话题取 biliopusdb，用户取 pptr Postgres）；严禁直写 MySQL，统一经 HTTP 接口。
- `--dry-run` 覆盖全阶段（任何接口调用前短路）；tqdm 进度；单条失败软降级（私信撤回/删除断言响亮报错）。
- 参数：`--full-count`(默认1000)/`--full-concurrency`(默认50) 统一两阶段；`--base-url/--admin-mid/--skip-*`。
- **转发链路覆盖**：`seed_moment` 需覆盖 `/repost` 与 `POST /create`(scene=FORWARD) 双路径、转发语 @（详情回显 + AT 事件断言）、二级转发（源为 FORWARD，`repostDepth` 递增）与源动态 `repostCount +1` 状态机校验。

**目录结构（`scripts/seed/`，按功能分包）**

| 模块 | 职责 |
| --- | --- |
| `cli.py` | argparse 参数定义、两阶段编排（`_run_full` / `_run_bulk`）、`main()` |
| `config.py` | 超时（HTTP / 单请求 / 并发信号量）、举报原因、资源池容量等全局常量 |
| `helpers.py` | `x-bili-*` 请求头、@ 文本 / AT 节点、富文本正文构造 |
| `rr.py` | 确定性轮遍游标 `_rr` 与分布采样 `_sample` |
| `material.py` | 素材池（`_SENTENCES`/`_COMMENTS`/`_REPLIES`/`_IMG_URLS`/`_TOPIC_NAMES`）+ 外库加载 |
| `datasource.py` | 外库只读数据源（biliopusdb / bilidb / pptr 用户池 / 主库已有话题） |
| `probes.py` | be-message 只读探针（私信设置 / 会话关系 / 私信索引 / 私信配对） |
| `client.py` | `SeedClient`：按域分段的 HTTP 薄封装（动态/评论/收藏夹/关注/事件/私信/举报封禁/头像） |
| `verify.py` | @ 落库渲染、AT 事件、源动态转发计数断言 |
| `blocklist.py` | 黑名单归一（每人 ≤1 条）+ 私信配对避让 |
| `lottery.py` | 真实 lottery_id 获取 + 动态/lottery 混合资源池 |
| `full.py` | 阶段一编排 `seed()`：动态 → lottery → 评论 → 互动 → 黑名单归一 → 消息 |
| `scenarios/` | 阶段一场景：`moment` / `comment` / `interact` / `message` / `moderation`（通用计数·举报·封禁·头像审核） |
| `bulk/` | 阶段二大数据灌数：`config`（分布常量）/ `topics` / `comment`（评论套件）/ `dynamic` / `dm` / `runner` |
| `rpa/` | **待接入**：`action`（RPA 操作）/ `plugin`（RPA 插件）/ `approval`（提交审批） |

- **新增场景约定**：按功能在对应包内加模块 + 场景函数，再由 `cli.py` 增加 `--skip-*` 开关挂进编排；数据源/断言/客户端方法分别落在 `datasource.py` / `verify.py` / `client.py`，不新增平行工具模块。
- **RPA 扩展位**（`rpa/`，待实现）：覆盖 `InteractionBizTypeEnum.RPA_ACTION / RPA_PLUGIN / RPA_WORKFLOW` 三类资源——操作（创建/执行/日志）、插件（注册/安装）、提交审批（工作流提交 → 审批通过/驳回流转）；同样只走 HTTP 接口、不直写库。

### 5.8 biz_type 单一真相源

- `InteractionBizTypeEnum`（bili-common）是业务资源类型的唯一真相源；`SourceTypeEnum/CommentTypeEnum` 保留各自存储取值，语义经 `app/models/biz_type.py` 关联映射；展示名统一 `biz_type_label()`，禁止各模块自建「类型→中文名」字典。

### 5.9 资源为中心的统一操作模型（`BaseBiz` 类体系）

- **动作枚举唯一真相源 `InteractionActionTypeEnum`**（bili-common，取值 1~7 保既有、新增自 8 起：`LIKE=1/REPLY=2/AT=3/AUDIT_REJECT=4/HIDE=5/REPORT_REJECT=6/REPORT_RESOLVED=7/DISLIKE=8/FAVORITE=9/SHARE=10/REPOST=11/VIEW=12/REPORT=13/AUDIT_APPROVE=14`）。
- **`interaction_actions/` 以资源为主体**：`BaseBiz`（`base_biz.py`）把 `InteractionActionTypeEnum` 全成员声明为方法接口（默认抛"该资源不支持"），承载举报/审核/评论操作；每个资源一个类（`<resource>/biz.py`，声明 `_biz_type`）；通用资源共享 `GenericResourceBiz`；**继承即登记**（`__init_subclass__` 自动入表，无工厂映射）；权限用 `@biz_action(relation=[...], acl=[...])` 装饰器声明式集中校验。
- **权限原语**：`InteractionRelationScopeEnum`（FOLLOWING/NON_FOLLOWING/NOT_BLOCKED）+ `InteractionAclScopeEnum`（OWNER_ONLY/AUDITOR_ONLY）+ 注册表；`InteractionResource`（SQLModel）统一资源表示（bizType/bizId/authorMid/ownerMid/exists/interactable/title/cover）。
- **举报与管理路径**：`report()/resolve_accused()/hide()` 与 `report_reject()/report_resolved()` 均为 `BaseBiz` 方法（通用实现），资源只需声明 `model + resolve_accused + hide` 即得完整举报能力；`ReportService` 退化为纯协调器（无 bizType if/elif）；资源→表唯一真相源是资源类 `model`。
- **评论发布入口统一走资源类（2.63.0）**：`POST /comment/add` 不再直连 `CommentService.add`，改为经 `get_biz(...).reply()`——一级评论按目标资源（`dynamic` / `lottery` / `others_lot_dyn` / `rpa_*`…），楼中楼按根评论（`CommentBiz`）。由此：
  - 「该类型是否支持评论」由资源类自身表达能力（`BaseBiz.reply/at` 默认 `_unsupported`，支持者覆盖实现），**接口层禁止写类型白名单**；
  - 「资源是否存在 / 是否可互动」由 `@biz_action` 统一校验（**写路径严格，不做降级**），避免用不存在的 `oid` 造出 `msg_comment_subject` / `msg_comment_index` / `TInteractionStat` 脏行；
  - 频控 / 日限 / 审核 / 楼层 / @ / 通知仍是 `CommentService.add` 的单一实现，`ops.do_comment` 只做参数透传；
  - 客户端上下文（IP / UA / 属地 / 昵称）由路由注入资源实例（`biz.client_ip_v4` / `client_ip_v6` / `ip_location` / `ip_isp` / `actor_uname`，与动态发布既有的 `biz.client_ip` 注入方式一致），经 `ops.do_comment` 透传，保证 IP 属地与通知里的昵称不丢。
  - **`CommentBiz.reply/at` 定位修正**：评论区 subject 用**所属评论区** `(CommentIndex.oid, CommentIndex.type)` 定位，`root` 才是自身 rpid；原实现把 rpid 当 `oid` 传，会被 `_resolve_tree` 判「根评论不属于该评论区」，即该路径此前不可用。
- **DDL 约束**：`msg_event.event_type` 用原生 ENUM 存成员名（存量遗留，与 §2.3 不一致），新增枚举成员须同步 ALTER。**同理，`InteractionBizTypeEnum` 新增成员必须同步 ALTER 全部以 `SAEnum(InteractionBizTypeEnum)` 落库的列**（原生 ENUM 存成员名）：`msg_comment_subject.type`、`msg_comment_index.type`、`msg_comment_at.type`、`msg_event.source_type`、`TFeedImpression.bizType`、`TResourceFeed.bizType`、`ResourceBase.bizType`（`TResourceLike/Dislike/Favorite/Report/AuditLog`）、`TMoment.bizType`。否则写入新类型会因 ENUM 取值缺失报错（典型报错 `(1265, "Data truncated for column 'type' at row 1")`）。
  - **已提供迁移**：`be-message-service/alembic/versions/20260920_1300-others_lot_dyn_enum_.py`（`down_revision=1cb38c34aef9`）——按 `information_schema` 现有定义**幂等追加**缺失成员，已补齐 `OTHERS_LOT_DYN` 与**存量遗漏的 `RPA_TAG`**（模型早就在用、初始建表 ENUM 里没有）；非 `enum(` 开头的列（如 `TResourceReport.bizType` 实为 `int`）自动跳过。新增枚举成员时按同样方式补一份迁移即可。
- **资源类清单（2.61.0）**：`dynamic / lottery / comment / user / rpa_action / rpa_workflow / rpa_browser / rpa_plugin / rpa_tag` + **新增 `others_lot_dyn`（第三方抽奖动态，bizId=dynId）**。`others_lot_dyn` 继承 `GenericResourceBiz`（举报落 `TResourceReport`，作者回查取 `t_lotdyninfo.up_uid`），并覆盖 `hide()` 为 no-op（站外 B 站动态不由本站下架）。

### 5.13 统一审核动作（bizType + bizId）与审核结果通知

- **统一审核入口（新增）**：`POST /api/v1/audit/approve`、`POST /api/v1/audit/reject`（管理端鉴权同现有审核路由），入参 `AuditActionReq{bizType, bizId, remark?}` / `AuditRejectReq{bizType, bizId, rejectReason, remark?}`。路由层只做「`get_biz(bizType, session, bizId, actor)` → `audit_approve()/audit_reject()` → 装配」，与各资源专用路由（动态 dynId / 话题 topicId / 头像·封面 pk / 评论 rpid）**并存**，前端统一走新接口，专用路由逐步收敛。定位口径与 §5.9 一致：`(bizType, bizId)` 唯一确定资源。
- **审核动作下沉到资源类**：`BaseBiz.audit_approve/audit_reject` 从「接口声明（默认抛不支持）」升级为「各资源必须实现」：
  - `DynamicBiz`：沿用现有实现（含 `_notify_reject`、FORWARD 源计数状态机、AuditLog、Feed 同步）；
  - `CommentBiz`：**新增** `audit_approve/audit_reject`，复用 `CommentAdminService.set_state` 的状态流转与通知（`notify_audit_rejected` / `_notify_hidden`），入参统一为 rpid（comment 的 bizId 即 rpid）；
  - `UserBiz`：**新增** 头像审核结果处理（bizId=mid），通过/驳回均通知；
  - `GenericResourceBiz`（lottery / rpa_*）：`audit_approve/audit_reject` 在现有 RPC 审批之外补**站内通知**；`LotteryBiz.hide` 保持 no-op。
- **审核结果通知（弱依赖）**：`BaseBiz._notify_audit_result(*, author_mid, passed, reject_reason, remark)` 统一封装 `report_event_weakly`（`AUDIT_APPROVE` / `AUDIT_REJECT` 事件，携带 `source_type=bizType`、`source_id=bizId`、跳转目标），由各资源方法自行调用——**驳回必须通知作者**，通过按资源策略（动态默认不通知，头像/封面/评论已有的通知保持不变）。
- **流水**：统一写 `TResourceAuditLog`（`bizType + bizId` 定位），与 §5.1 状态机骨架一致。
- **通用审核统计**：`GET /api/v1/community/audit/statistics?bizType=<biz>` 按业务域返回审核概览（`{total, byStatus: {<状态名>: n}, byType: [{type: <子类型名>, <状态名>: n, …, total}]}`），bizType ∈ dynamic/topic/comment/dm/avatar/folder_cover/report，缺省 dynamic 向后兼容。各域统计源：dynamic=TMoment（dynType×auditStatus）、topic=TMomentTopic、comment=CommentIndex（type×auditStatus）、dm=DmMessageIndex（按 msgkey 去重计数）、avatar=TUserAvatarAudit、folder_cover=TFolderCoverAudit、report=TResourceReport（auditStatus：1=pending/2=resolved/3=rejected，byType 按 bizType 分组）。管理端各审核页顶部「审核总览」卡片统一消费该接口。**口径对齐**：report 域统计跨全部举报表（`_distinct_models()`，与 `report/admin/list` 无 biz_type 时的跨表口径一致，total 恒等）。**权限模型 v2（Linux 风格 per-biz_type 位掩码，整体重做，无兼容包袱）**：
- 操作位 `BizPermOp`（IntFlag，对齐 rwx 数值）：`BAN=1(x 处置：封禁/解封)`、`AUDIT=2(w 审核)`、`VIEW=4(r 查看)`；资源维度 = `InteractionBizTypeEnum`（类比「文件」）；每域权限字 0~7（`7`=rwx 全权、`4`=只读），按位检查 `biz_perms[biz] & op`；
- 存储：`msg_admin.biz_perms: dict[biz文本, 权限字]`（JSON）替代旧令牌列表；网关头 `x-bili-permissions` 同构（JSON dict），root 恒 `{"*": 7}`；内容明文 root 专属，不占权限位；
- 旧 `UserPermission / WIRE_TOKEN / ROOT_ONLY / sanitize_permissions / require_permission` 全部删除，新增 `require_biz_perm(biz, op)` 依赖工厂；账号角色（评论/私信/治理/超管）预设改为 `ROLE_BIZ_PERMS` 掩码并集；授权 API `grant` 入参与 `/me`、管理员列表响应均为 `biz_perms`；
- 前端：`messageAdmin.ts` 提供域行/操作位元数据与 `hasBizPerm / opsText / bizPermsText` 工具；权限管理页授予弹窗改为「资源域 × rwx 勾选矩阵」，管理员列表展示 `域:rwx` 文本；`canBan`（评论/私信/封禁弹窗）改按 `biz_perms` 位检查。
- **权限设置页独立**：管理端权限页从消息域拆出独立路由 `/app/admin/permission`（`ADMIN_PERMISSION`，组件 `views/admin/AdminPermissionView.vue`），侧边栏独立「权限设置」分组（isMessageRoot 可见），不再挂在「消息管理端」组下；路由名枚举同步为 `ADMIN_PERMISSION`。
- **通知管理区分系统通知 / 用户通知**：`NotifyMessage.target_type` 已有 ALL/ROLE/LEVEL/VIP/CUSTOM 五类（CUSTOM=逗号分隔 mid 的定向用户通知）；`GET /message/notify/admin/list` 加 `target_type` 筛选，列表 target 列用「系统通知 / 用户通知」tag 区分；发布表单选 CUSTOM 时以公共组件 `UserSearchPicker`（多选模式）搜索点选用户合成 target_value，不再手填 mid。`UserSearchPicker` 同时支持单选 / 多选两种模式。

**统计域枚举收口**：`/audit/statistics?bizType=` 直接复用 `bili_common.models.interaction.InteractionBizTypeEnum`（审核域补充成员 TOPIC=9 / DM=10 / AVATAR=11 / FOLDER_COVER=12 / REPORT=13，仅作审核统计与队列归属、不作为互动资源 ID），删除 be-message 侧自造的 `AuditStatsBizType`；非审核域成员（LOTTERY/RPA_*/USER）请求统计返回 400。**admin list 统一 `bizType` 参数名**：有资源子类型维度的审核 list 接口（动态 `/community/audit/list`（MomentTypeEnum）、评论 `/comment/admin/audit`（InteractionBizTypeEnum）、举报 `/report/admin/list`（InteractionBizTypeEnum））均以 `bizType` 筛选特定资源；无子类型维度的话题 / 头像 / 封面 / 私信不加。
- **私信审核页对齐（message-dm）**：顶部统一 `AdminAuditTabs`（单选状态 Tab，非 root 仅「待审核」），删除页头刷新与状态下拉、表格右上重复刷新按钮；表格新增行内操作列（状态机：待审核=通过/驳回、已过审=驳回撤回、已驳回=通过恢复、已下架=恢复），批量工具栏与封禁保留；统计卡网格修复（总览卡移出网格），`/message/dm/admin/stats` 的 `today_new` 改按 `msgkey` 去重与 `total_dm` 口径一致。
- **评论审核页对齐（message-comment）**：状态多选下拉收敛为 `AdminAuditTabs` 单选 Tab（待审核/已过审/已驳回/已下架，非 root 仅「待审核」，权限语义不变），页头标题并入 Tabs，保留评论区类型（bizType）筛选与统计卡；至此动态/话题/头像/封面/举报/私信/评论七个审核页全部为「上方统计总览 + 状态 Tab 切换」统一布局。

### 5.10 事件资源定位统一

- 事件跳转身份统一为 `(resource_type, resource_id)`（顶层 `InteractionBizTypeEnum` + oid/卡片 id）；后端下发 `jump_target`（`route:{name}?{query}`，含 rpid 锚点），前端只 `router.push(name)`。
- **跳转路由映射**：`jump_target_for` 的 `_JUMP_ROUTE_MAP` 按资源类型登记「前端路由名 + id 参数名」——`dynamic→MOMENT_DETAIL(momentId)`、`lottery→LOTTERY_CARD_DETAIL(id)`、**`others_lot_dyn→OTHERS_LOT_DYN_DETAIL(dynId)`（2.61.0 新增）**。第三方抽奖动态没有 `lottery_id`，因此**不能**复用 `LOTTERY_CARD_DETAIL`（该页按 `lottery_id` 拉详情必然失败）。
- 复用 `BaseBiz` 体系：各资源实现 `check_exists()/_load_meta()` 钩子，`get_resource()` 统一装配 `InteractionResource`，`batch_get_resources()` 为每类批量接口（一次 IN/RPC 防 N+1）；不存在返回 `exists=False` 空占位。
- 评论锚定事件（REPLY/AT）正文经 `CommentBiz.batch_get_resources` 批量回捞，出参带楼层作者 `source_mid/name` 等。

### 5.11 其余机制要点

- **互动接口通用化**：`/thumb /dislike /share /report` 一律 `bizType+bizId` 定位；路由层只做「`resolve_target` 归一 → `get_biz(...).动作()` → 装配」，防乱调/计数/装配在 service 层。
- **热门抽奖榜一次返回卡片数据（2.67.0 修正）**：`GET /community/interaction/hot-lotteries` 除热度计数外**直接下发抽奖卡片数据**（`HotLotteryItem.card`，形态与 crawler `GetLotteryDetail` 的 `raw` + `extra_info` 完全一致，前端可直接 `normalizeLotteryData` 渲染，无需二次回捞）。
  - 数据来源：be-message 经 crawler **只读查询服务**的 `GET /api/v1/lottery_database/bili/GetLotteryDetailList` 一次批量回捞（`app/services/infrastructure/crawler_query.py`；配置 `CRAWLER_QUERY_BASE_URL`，默认 `http://127.0.0.1:23336`，容器内指向 `be-bilibili-crawler-query:23336`；超时 `CRAWLER_QUERY_TIMEOUT`=3s + 弱依赖降级）；响应 data 用 `bili_common.rpc.lottery.LotteryCardList` 解析，crawler 侧固定 2 条 SQL（`lotdata IN (...)` + 批量 `t_lot_extra_info`），与 ID 数量无关。
  - **不走 RPC**：RPC 订阅者只在 crawler 完整爬虫角色（`SERVICE_ROLE=crawler`）里启动，`api` / `query` 角色都不消费 MQ——本地 dev 编排只有这两个容器，`FastapiApp.rpc.*` 会一直超时；只读查询服务在本地与生产都存在，与前端首页直连的查询服务同一口径。
  - **首页 / 榜单禁止再自行调用 `GetLotteryDetail` / `GetLotteryDetailList`**（detail 域接口）：榜单一次请求拿全量「热度 + 卡片」，避免首页为渲染榜单再打一轮 detail（原 `HotLotteryList.vue` 的 `getLotteryDetailListByIds` 调用已移除）。
  - 弱依赖：RPC 超时 / 未连接 / 卡片缺失时**服务端直接剔除该项**（`card` 字段保留可为 null 供前端防御），榜单只展示有卡片的热度项，不把下游抖动放大成 500。
  - 浏览记录口径不变：`TInteractionViewLog` 仍只由 detail 单资源 `GET /interaction/status/{bizId}` 投递（列表批量接口不累计浏览），榜单语义仍是「近 N 天真实详情浏览热度」，首页曝光不计浏览。
  - **首页「即将开奖」轮播同口径**（`UpcomingLotteryMarquee`，2.67.0）：crawler `GET /lottery_database/bili/GetLotteryDataSummary` 的 `upcoming` 明细**随卡片一次下发** `raw` + `extra_info`（`get_upcoming_lottery` 返回完整 lotdata 行 + 一次批量 `t_lot_extra_info`，无 N+1），前端直接渲染，**不再**调用 `GetLotteryDetailList` 回捞；互动态仍走批量 `/interaction/status`（只读，不累计浏览、不改互动计数）。首页因此不产生任何 detail 域请求，也不会给用户新增浏览记录或抽奖互动次数。
  - **即将开奖：24h 口径不变 + 明细改后端分页**（2.67.0 调整）：窗口仍为 24h（紧迫度语义，`SUMMARY_UPCOMING_HOURS=24`），**不再设置条数上限**——`GetLotteryDataSummary` 只保留统计行，**不再下发 `upcoming` 明细**；明细改由新增只读接口 `GET /lottery_database/bili/GetUpcomingLottery?page_num=&page_size=&key=&within_hours=24` 分页返回 `ResponsePaginationItems[UpcomingLotteryItem]`（`items` + `total`，固定 2 条 SQL：`count` + 分页查询 + 批量 `t_lot_extra_info`，无 N+1、无静默截断），与普通抽奖列表（`GetOfficialLottery` 等 `page_num` / `page_size`）**同一分页范式**。
  - 首页 `UpcomingLotteryMarquee`：`el-carousel` 自动滚动 → 统一 `BiliPagination`（`size="large"` / `background` / `pager-count=5` / `layout` 带 `total`，与 `BiliPaginationDataView` 同款外观），每页 = 列数 × 2 行（宽屏 4 列 8 张、窄屏 2 列 4 张）；页码 / 列数 / 抽奖类型变化时**只查当前页**（互动态也只查当前页），不再一次拉全量。
- **互动态读接口的存在性校验口径（2.63.0）**：校验只为「有副作用的路径」而设，读接口不替归属服务做存在性判定。
  - `GET /community/interaction/status`（批量，列表专用、**不累计浏览**）：**不做资源存在性校验**，直接读本地 `TInteractionStat` + 明细 + 评论/转发计数；资源没有互动态本就应返回 `isLike=false` / 计数 0，这是正确语义而非错误。原「任一缺失 → 整批 400」会把下游 RPC 的可用性抖动放大成整页互动态缺失（第三方抽奖列表踩到过），一并去除。
  - `GET /community/interaction/status/{bizId}`（detail 专用，登录后**投递浏览计数**，有写副作用）：**保留**校验（防任意 bizId 在 `TInteractionStat` / `TInteractionViewLog` 造脏行），但把「校验不通过 / 不可用」从 `400` 改为**降级**：不投递浏览、照常返回本地状态（全 0）。可用性问题不再伪装成业务错误。
  - 写接口（`thumb / dislike / favorite / report / share / repost`）仍严格校验（`@biz_action(require_resource=True)`），保证 `(bizType, bizId)` 指向真实资源。
  - 装配侧：`query_status_items` 的详情 RPC **仅对 RPA 系列类型**（`rpa_action / rpa_workflow / rpa_browser / rpa_plugin / rpa_tag`）发起——其余类型（含 `lottery` / `others_lot_dyn` / `comment` / `user`）原样白跑 N 次 RPC 且必然返回空。
- **浏览计数消费端二次兜底（2.63.0）**：`interaction.view` 消费者在写 `TInteractionViewLog` / `TInteractionStat` 前，用**三态存在性** `BaseBiz.check_exists_state()` 兜底——`False`（明确不存在：资源已删 / 脏消息）→ `ack` 丢弃，防止绕过投递端直接往队列塞任意 `bizId` 造脏行；`None`（校验不可用，如归属服务 RPC 失败）→ 按弱依赖继续计数，避免下游抖动静默吞掉真实浏览；真异常仍 `nack(requeue=True)` 重试、超最大次数 `ack` 丢弃（原策略不变）。`check_exists_state()` 默认复用 `check_exists()`（本地判定无「不可用」态），`LotteryBiz` / `OthersLotDynBiz` 覆盖为真实三态（`get_existing_*_ids` 的 `None` = 不可用）。
- **私信发送限制**：每日上限 `dm_daily_send_limit`(1000) + 陌生人单条闸门 `dm_stranger_gate_*`；超限分别回业务码 `4001/4002`，不落库。
- **陌生人私信分类（`DmSessionTypeEnum.STRANGER`，参考 B 站「陌生人消息」集合）**：
  - `DmSessionTypeEnum` 新增 `STRANGER=2`（与 `SINGLE=1` 并列）。`SINGLE` 走主 DM 列表；`STRANGER` 是被接收方「陌生人私信拦截」开关拦下的会话集合，**不进主列表**。
  - 拦截命中条件：`_is_stranger(receiver, sender)=True` 且 `SettingService.accept_stranger_dm(receiver)=False`；此时消息仍写扩散（双方索引 + 双方会话），但接收方会话的 `session_type=STRANGER`、`relation=STRANGER`，未读计入 STRANGER 分类而非主列表。
  - 会话行 `session_type` 在 upsert 的 `on_duplicate_key_update` 同步覆盖：一条被拦截的消息会让原 SINGLE 会话迁到 STRANGER，用户回复后下一条又迁回 SINGLE——分类始终反映「最新一条消息的分类」。
  - `DmInbox.list_sessions(session_type=...)` 支持过滤：`single` 取主列表、`stranger` 取陌生人分类；响应同时返回 `unread_total`（主列表未读，顶部红点用）、`stranger_unread` / `stranger_total`（STRANGER 聚合，分类条目用）、`stranger_dm_intercept_enabled`（当前用户是否开启拦截），与本次 `session_type` 过滤无关。
  - **聚合条展示条件**：`stranger_dm_intercept_enabled == true` **且** `stranger_total > 0` 才在「最近消息」顶部展示「陌生人私信」条目——开关没开、或开了但还没有被拦截的会话，都不展示。
  - `DmInbox.count_unread` 仅统计 `session_type=SINGLE`：被拦截消息归 STRANGER，顶部 DM 红点不包含它们。
  - 一旦接收方回复同一对话方，会话升级为 `relation=NORMAL`（`case` 表达式只升不降），`session_type` 同步迁回 SINGLE，「毕业」出陌生人分类。
- **内容发布每日上限**：评论/动态(WORD)/话题按当天创建行计数（软删仍算次数），上限配置化，超限回 `4101/4102/4103`。
- **评论冗余计数校准（2.64.0，按需工具）**：`msg_comment_subject.root_count / all_count` 与动态类型的 `TInteractionStat.commentCount` 由写路径同事务原子 ±1 维护（2.46.0 已移除定时对账任务，正常无需对账）；**但评论索引 / 正文行被外部删除、迁移或历史脏数据后计数会残留**，表现为「评论数 N 但列表为空」。此时用 `be-message-service/scripts/recount_comment_subject.py` 按 `msg_comment_index` 真实行数重算（口径与写路径一致：仅 `visible(NORMAL)`、`root_count` 只算 `root=0`、动态 `commentCount` 以评论区 `all_count` 为准；不动 `floor_seq`/`state`/`top_rpid`）。默认 dry-run，`--apply` 写回，`--oid` 限定单个评论区；**幂等**（先恢复备份数据再跑一次即可重新对齐）。
- **运行时配置中心（2.64.0）**：`msg_sys_config`（`key` 主键 + `value` JSON + `updatedBy`）承载**可热更新**的运营参数，由 `app/services/common/runtime_config.py` 提供读取器：各配置项在 `CONFIG_SPECS` 登记**值模型（SQLModel）+ settings 默认值提供者**，`get_config_model()` 把库里的 JSON 转成模型实例后返回——缺失字段补模型默认、多余字段忽略、类型不符则整体回落默认，业务侧拿到的**始终是校验过的强类型对象**（不接触裸 dict）；写入侧走同一模型的 `model_dump(mode="json")` 规范化后落库，脏配置进不了库。进程内 TTL 缓存（默认 10s）+ DB 权威 → 管理端改一次，写入实例立即生效、其余实例 ≤ TTL 自然刷新（**不引入 Redis**，与「所有数据落 MySQL」的项目约定一致）。DB 未建 / 查询失败 / 值非法一律回落 `settings` 默认值（不阻断业务）——**读取用 `SAVEPOINT`（`begin_nested`）包裹**，失败只回滚到保存点，绝不把调用方业务事务打成失败态（否则表未建时整个评论发布会连带崩）；写入要求管理员（`AdminUser`）+ pydantic 校验，非法值 400 不入库。**分层语义**：settings 只表示「代码默认值 / 兜底」，运行时可覆盖项按需接入（当前仅评论频率限制）。迁移：`alembic/versions/20260920_1500-msg_sys_config_.py`。**管理端界面**：`/app/admin/sys-config`（路由名 `ADMIN_SYS_CONFIG`，`requiresMessageRoot`，管理后台侧边栏「系统设置」组 + 首页卡片入口）；`GET /api/v1/message/admin/sys-config` 返回**全部已登记项**（未写入 DB 的项以 settings 默认值返回并标 `isDefault=true`，管理端因此能看到「当前生效值」），`POST .../update` 写入；评论限流用结构化表单（两档 × 规则行增删，实时显示规则效果），未登记的 / 未来新增项回退 JSON 编辑；前端调用走手写封装 `Vue3FrontEndDemoExercise/src/api/community/sys_config_api.ts`（不阻塞 hey-api SDK 重新生成，生成后可平滑替换）。**注意**：TTL 缓存意味着「改完配置到全实例一致」有 ≤ TTL 的窗口，限流阈值调整场景可接受；若将来要求秒级一致，可在既有 `message_exchange`（TOPIC）上加广播失效，不改变读取路径。
- **评论防刷屏（2.63.0；2.64.0 改为 DB 窗口计数 + 双档阈值 + 可热更新）**：三层窗口（同内容 / 总量短窗 / 总量长窗）的**求值逻辑唯一**，但**阈值按 scope 分两档**：
  - `root`（一级评论，广场刷屏的主要目标）：同内容 10s ≤ 2 次；总量 10s ≤ 3 次；总量 60s ≤ 15 次；
  - `reply`（楼中楼回复，连回多人属正常行为）：同内容 10s ≤ 3 次；总量 10s ≤ 6 次；总量 60s ≤ 30 次（沿用 2.63.0 原数值）；
  - 阈值可管理端热更新（见上条）：`msg_sys_config['comment_rate_limit']`（形如 `{"root":[...],"reply":[...]}`，两档同 key 保证原子更新），缺失时回落 `settings.comment_rate_root_rules` / `comment_rate_reply_rules`；规则字段 `{window_seconds, max_count, same_content}`，`[]` 表示关闭该档限流。
  - **计数源改为 MySQL `msg_comment_index`**（跨实例一致，取代原「各实例独立计数」的既有局限）：总量 = 窗口内该 mid 的创建行数（一级加 `root=0`、回复加 `root<>0`）；同内容 = 同窗口内 JOIN `msg_comment_content` 按 `message` 等值匹配。走 `idx_comment_user(mid, rpid)` + `created_at`，窗口内行数极少，成本可忽略。删除为软删（行保留），故被删评论仍计入窗口，与每日上限口径一致。
  - 命中任一规则统一回 400「操作过于频繁，请稍后再试」；被拒请求不落库、不计入窗口。与每日创建上限（`comment_daily_create_limit`）叠加：前者防秒级刷屏、后者防累计灌水；并发下两条同时通过计数可能超出阈值 1~2 条（阈值有余量 + 日上限兜底，可接受）。
  - **执行点唯一、求值逻辑唯一（阈值分档不违反本约束）**：限流只在 `CommentService.add` 一处执行（一级 `reply` 与楼中楼 `CommentBiz.reply` 的共同落点），按 `req.root`（`"0"` = 一级）选一档阈值后交给**同一个求值循环**；新增发布入口必须收敛到 `CommentService.add`，**禁止在路由层 / 资源类各自实现限流**（否则会出现两套计数源）。每日创建上限同样在同点共用（按 `CommentIndex.mid` 当天全部行计，含一级与楼中楼）。回归由 `tests/test_comment_rate_limit.py` 锁定。
- **动态不可编辑**（2.58.0 移除 `POST /edit`）；转发/发布/删除/置顶保留。
- **会话置顶**：`top_ts`（毫秒，0=未置顶）唯一真相源，列表 `top_ts DESC → last_msg_ts DESC`，可多会话置顶。
- **匿名可读互动态**：`interaction/status` 依赖降级 `OptionalUser`，匿名 `viewer_mid=0` → `isLike/isFavorite` 恒 false；浏览统计不匿名投递。
- **举报列表**：`ReportItem` 追加举报人/被举报人用户信息 + 资源快照 `resource`（一次批量回捞）。
- **用户反馈（`POST /api/v1/message/push/feedback`）**：只投给站长本人——不接收 per-user 渠道配置，固定回落全局 `MESSAGE_CONFIG`；推送标题为 `用户反馈|{source}` + 用户标签。
  - **`source` 由前端页面自己传入**：常量单一来源 `Vue3FrontEndDemoExercise/src/api/notify/message_feedback.ts` 的 `FEEDBACK_SOURCE`，各抽奖页把**具体抽奖类型**（官方抽奖 / 预约抽奖 / 充电抽奖 / 话题抽奖 / 第三方抽奖）经 `LotteryDataTableToolbar` 透传给 `SubmitFeedbackModal`，**不再一律落到笼统的「抽奖数据页」**（站长据此才能区分反馈来自哪种抽奖页面）。
  - **`contact` 长度上限** `FEEDBACK_CONTACT_MAX_LENGTH = 100`（`be-message-service/app/models/push.py`）：后端 `FeedbackRequest.contact` 用 `Field(max_length=...)` 做**最终校验**（超长由请求参数校验拦截），前端 `maxlength` + 表单 `max` 规则只做体验层拦截，两侧数值保持一致；前端提交失败优先展示后端 `msg`。

### 5.12 字段可见性：上下文感知序列化

**背景**：此前「用户简档」用 `UserBriefPublic`（基类）+ `UserBriefPrivate`（继承）+ `to_public()`
显式投影控制私密字段。实测（pydantic 2.13 / SQLModel 0.0.39）确认：

- private 实例赋给声明为 public 的字段时**不会被裁剪**（运行时类型仍是子类）；
- 只有按「字段声明类型」序列化（`response_model` / `model_dump`）才会裁剪；
- 直接 `private_obj.model_dump()`、塞进 `dict`/`Any`、MQ payload **会泄漏**。

即 `to_public()` 把「出口规则」变成了「调用点纪律」，漏一处即漏数据。

**新机制（松耦合，无继承、无调用点纪律）**：

- **单一输出模型**：公开 / 私密字段合并进同一个 `XxxOut` 模型，可见性不再靠继承表达；
- **字段级标记**：敏感字段声明为 `Annotated[T, Private()]`（`app/models/schemas/visibility.py`）；
- **序列化期裁剪**：模型经 `VisibilityMixin` 自带 `model_serializer(mode="wrap")`，
  按 `ViewerContext` 决定是否输出带 `Private()` 标记的字段；**嵌套模型自动生效**，外层无需干预；
- **安全默认**：取不到 context 时一律按「他人视角」裁剪；
- **context 传递**：`app/core/viewer_context.py` 的 `ContextVar`。FastAPI 0.141 的
  `serialize_response` 无 `context` 入参（`site-packages/fastapi/routing.py:329-338`，
  仅 include/exclude/by_alias/...），故不走框架参数，改用 ContextVar 注入（见 C15）。

**视角判定**：`viewer_mid == 对象归属 mid`（本人）或 `is_admin`（管理员）→ 输出全部；否则裁剪。
没有归属 mid 的模型（如评论 IP）退化为「仅管理员可见」。

**命名迁移**：`UserBriefPublic` → `UserBriefOut`；`UserBriefPrivate` **退役**
（其私密字段并入 `UserBriefOut` 并打 `Private()` 标记）；`to_public()` **废弃**，装配层不再投影。

**全量铺开范围**（含敏感字段的模型）：

| 模型 | 敏感字段 | 可见性 |
| --- | --- | --- |
| `UserBriefOut` | `vip_due_date` / `exp` / `role` / `email` | 本人 / 管理员 |
| `CommentAuditItem` | `ip_v4` / `ip_v6` | 仅管理员（C3：出参打码、管理员明文） |
| 审核单据类（`avatar_audit` / `folder_cover_audit` / moment 审核日志） | `auditReason` / `operatorMid` / `operatorRole` | 仅管理员 |

### 5.14 RPA 浏览器实例监管（治理闭环）

- **前提口径**：浏览器指纹 / 浏览器实例（`InteractionBizTypeEnum.RPA_BROWSER=5`，bizId=`browser_id`）是**用户私有资源**——不对外公开、无社区广场；可被点赞 / 收藏（走通用互动，`RpaBrowserBiz`），但**可互动 ≠ 可公开**。可公开的是 action / workflow / plugin 这类可执行资产（`is_public`）。
- **治理目标**：审核员可查看**运行中的浏览器实例**是否在跑恶意内容，并就地处置；处置动作只有**停止会话 / 通知 / 封号**三种，不引入「警告」中间态（短时封禁即 `ban_type=temporary` + `duration_minutes`）。
- **跨服务职责**：
  | 动作 | 落地位置 | 说明 |
  | --- | --- | --- |
  | 运行中实例列表、标签页只读、强制停止 | RPA-Browser 管理端接口（新增 `POST /api/admin/rpa/browser/monitors`、`/monitor/pages`、`/session/stop`） | 绕过 `verify_browser_ownership`，由 `require_permission(RPA_BROWSER, VIEW/BAN)` 把关；强制停止复用会话 `force_close` |
  | 封号 | RPA-Browser `POST /api/admin/rpa/ban/create` | `scope=rpa`（仅拦截 RPA 服务，不影响评论 / 私信）；`permanent` / `temporary` |
- **封禁边界（不联动）**：监管页封号**只封 RPA**（`rpa_user_ban`，由 RPA 侧 `ban_guard` 中间件本地拦截，封禁后清缓存即时生效）。评论 / 私信的封禁归 be-message 自管（`POST /api/v1/message/admin/ban`，`ban_services=comment/dm` → `msg_user_ban`），**不在监管页联动、也不新增跨服务 RPC**。三套封禁各自独立：RPA 封禁不写 be-message，反之亦然。
- **权限口径**：监管列表 / 停止用 `RPA_BROWSER` 域 VIEW / BAN 位；封号用 `USER` 域 BAN 位（`require_permission(USER, BizPermOp.BAN)`，沿用 `user_ban_router`），审核员需同时持有两类位才能完成「停止 + 封号」。
- **只读拉流的依赖放宽**：WebRTC（`offer` / `answer` / `ice-candidate` / `status` / `close`）原本一律 `verify_browser_ownership`（严格 owner），管理员无法观看。新增 `verify_browser_ownership_or_admin`：owner 走原校验；非 owner 时若调用方为 root 或持有 `RPA_BROWSER` 域 VIEW / BAN 位，则只校验浏览器实例存在后放行。普通用户行为不变。
- **只读边界（前端）**：监管页复用 `LiveBox` 的 `readonly` 模式——只拉流观看，**不调用** `/operation/*` 与 `/actions/execute`，标签页信息走监管专用只读接口，审核员不能代替用户操作浏览器。
  | 通知 | be-message `POST /api/v1/message/notify/admin/create` | `target_type=CUSTOM` + `target_value=<mid>` 定向通知被处置用户 |
  | 审计 | RPA-Browser `AdminAuditLog` | `browser:stop` / `browser:ban`，与 §5.13 治理审计同源 |
- **只读边界**：监管页复用 stream 页的 `LiveBox` 观看 WebRTC 流，但为 `readonly`——不调用任何 `/operation/*` 与 `/actions/execute`，审核员不能代替用户操作浏览器。
- **前端**：管理端新增「浏览器监管」页（`/app/admin/browser-monitor`，`AdminBrowserMonitorView.vue`），与封禁 / 审核 / 举报同域；列表用 `el-table-v2` + 分页（对齐 `docs/frontend-plan.md` §四 规范）。

### 5.15 RPA 浏览器会话闲置生命周期（三级软着陆）

- **背景问题**：闲置回收原本散落两处且口径不一致——WebRTC 流层每 10 分钟按「信令活跃」关流（只关流不关实例、不反映真实操作）；会话层每 5 分钟按 `is_idle` 判关实例，但 `status` 从不进入 `IDLE`、`last_activity` 也不随操作刷新，判定恒不成立（**失效死代码**）。
- **统一真相源**：以 `BrowserSessionEntry.last_activity` 为唯一活跃时间戳。所有「真实操作」统一调用 `LiveService.touch(mid, browser_id)`（HTTP 操作接口 / action 执行 / WebRTC 信令），**仅状态查询类接口不 touch**（避免前端轮询续命）。
- **三级软着陆**（扫描间隔 `browser_session_cleanup_interval`，默认 60s）：

  | 档位 | 闲置阈值（无 touch） | 动作 | 释放资源 |
  | --- | --- | --- | --- |
  | DEGRADED | ≥ `browser_stream_degrade_after`（120s） | 重启 screencast 降 `quality`（`browser_stream_degrade_quality`）+ 限帧（`browser_stream_degrade_max_fps`） | CPU / 带宽 |
  | SUSPENDED | ≥ `browser_stream_suspend_after`（300s） | `webrtc_manager.suspend_streams()` 关流、**保留浏览器实例**；`status=IDLE` | CPU（流） |
  | TERMINATING | ≥ `browser_session_max_idle_time`（1800s） | 先进 `browser_session_terminate_grace`（60s）宽限，到期 `release_browser_session()` 关实例出池 | 内存 / 进程 |

- **自动化占用（pin）**：`entry.pin_count` 在 `ExecutionEngine.execute_action / execute_steps` 进入 +1、退出 -1；`pin_count>0` 跳过一切降级/关闭，退出时刷新 `last_activity`（避免长任务刚结束即被判闲置）。
- **返回活跃**：任意 `touch` / `pin` 清空 `terminate_scheduled_at`、解除降级（恢复全速 screencast）、`status=RUNNING`；挂起后用户重新 `webrtc/offer` 自动重建流（`start_stream` 幂等）。
- **可观测**：`BrowserSessionStatusData` 新增 `idle_seconds / is_pinned / pending_termination_at`，供前端展示「已暂停 / 待关闭倒计时」。
- **部署**：`user_data_dir` 必须挂持久卷（`docker-compose.yml` 的 `rpa-browser` 增加 `./docker_vol/rpa/user_data_dir:/app/user_data_dir`），否则容器重建丢登录态。
- **边界**：仍为单体部署，不引入 worker 位分片 / 网关亲和路由 / 跨机 WebRTC（分布式方案暂缓）。

### 5.16 RPA 浏览器 WebRTC 帧生产者（screencast）优化

- **背景问题**：`VideoFrameProducer` 存在三类浪费/隐患——① `screencast.start()` 返回的是 `DisposableStub`（只有 `dispose()/close()`，**没有 `stop()`**），`await session.stop()` 必抛 `AttributeError` 被吞掉，**screencast 从未真正停止**，页面流关闭后浏览器仍在持续 JPEG 编码；② `max_fps` / `degrade_max_fps` 只写 `_last_emit` 从不读取，**限帧完全失效**（§5.15 的 DEGRADED 档位只降了 quality）；③ `get_next_frame()` 阻塞在 `queue.get()` 时 `stop()` 无法唤醒，且解码失败一次即返回 `None` 终止整条轨道。
- **帧节奏（背压式限帧）**：利用 CDP screencast 的 **ack 驱动**特性（未 ack 不发下一帧）——在 `on_frame` 回调内按 `1/max_fps` 做帧间隔对齐，**入队前**才 ack。既避免「丢弃 + 立即 ack」导致浏览器以 60fps 空转编码，也真正把降级 `degrade_max_fps` 落到实处（CPU / 带宽同步下降）。
- **解码路径**：① 帧进入解码前先**合并积压**（`qsize()>0` 时把旧帧全部丢弃，只解码最新一帧），落后时不再做无意义的 JPEG 解码；② 解码改投**模块级专用线程池**（`webrtc-frame-decode`），不再抢占 `asyncio.to_thread` 的默认全局执行器，避免多流互相拖慢事件循环；③ 奇数宽高对齐到偶数（yuv420p / H264 编码器要求）；④ 绿屏兜底帧按尺寸缓存复用，不再每帧新建 PIL Image。
- **分辨率降级**：降级态通过 screencast 的 `size` 参数在**浏览器侧**降分辨率（`browser_stream_degrade_frame_max_width/height`，默认 640×360），JPEG 编码 / CDP 传输 / Python 解码三端同时降载；正常态沿用浏览器默认（viewport 等比缩放到 800×800 内），不改动画面观感。
- **生命周期修正**：`stop()` 统一走 `session.dispose()`（回退 `page.screencast.stop()`），并向队列投递哨兵唤醒阻塞的 `get_next_frame()`，停止后清空队列与 `_last_frame` 释放帧缓冲；解码失败返回上一帧 / 绿屏而**不终止轨道**。`start()` / 降级重启共用同一个 `_start_screencast()`，去掉重复分支。
- **可观测**：新增 `dropped_frames` / `emitted_frames` 计数，`stats` 快照统一用 SQLModel `VideoFrameProducerStats`（丢帧率 = `dropped/(dropped+emitted)`），用于校验降级是否真正生效。
- **解码快路径（第二期）**：JPEG 解码由「PIL → RGB → av 转 yuv420p」改为 **libavcodec MJPEG 直接解到 YUV** 再 `reformat(yuv420p)`，省掉一次全画幅 RGB 中间转换与拷贝。实测（800×450，quality=80）：平坦图 5.5ms → 2.8ms（-50%），高熵图 6.9ms → 4.7ms（-32%），8 线程并发 -45%+；`CodecContext` 非线程安全，按 `threading.local()` 每线程各持一个，解码异常时丢弃重建并**回退 PIL 路径**（兼容 CMYK / 异常 JPEG）。
- **时间戳基准修正（第二期）**：`aiortc.VideoStreamTrack.next_timestamp()` 硬编码 `VIDEO_PTIME = 1/30` 递增 PTS 并按 30fps 睡眠——降级限帧真正生效后（5fps），PTS 仍按 33.3ms/帧推进，**时间轴与真实出帧节奏脱钩**。改为在 `WebRTCMediaTrack.recv()` 内用**墙钟时间**换算 PTS（严格单调递增），节流职责完全由生产者承担；轨道结束由 `raise StopIteration` 改为 `raise MediaStreamError`（aiortc 的 sender 只对 `MediaStreamError` 静默收尾，`StopIteration` 会被 asyncio 包装成 `RuntimeError` 走 warning 分支）。
- **解码失败语义（第二期）**：不再「一次失败即返回上一帧 / 绿屏」，改为**跳过该帧继续取下一帧**；仅当连续失败达阈值（`_MAX_DECODE_FAILURES=5`）才用绿屏保活。同时去掉 `start()` 预置的 640×480 死帧（消费者本就阻塞等队列，该帧永不生效），绿屏兜底尺寸跟随最近一次成功帧，避免尺寸突变触发 H264 编码器重配。

### 5.17 RPA 浏览器入口准入与执行期互斥

- **背景问题**：启动内存准入（§5.11 / `docs/frontend_requirements/浏览器启动内存排队.md`）落地后，各入口的「是否启动浏览器」「会话不存在时如何响应」口径不统一，并存在两处实现缺陷：
  1. `workflow_router.execute_workflow_step` 的 `except Exception` 会把业务异常 `BrowserNotStartedException`（`code=1007`）吞掉并降级成 **HTTP 500**，前端拿到的是「服务端故障」而非可操作状态（`execution_router` 只 catch `ValueError`，同场景正常返回 `1007`，两者不一致）；
  2. 两处 `_resolve_page` 中的 `if not entry: raise ValueError(...)` 是**死代码**——`get_browser_session_entry` 的返回类型非 Optional，找不到会话直接抛 `BrowserNotStartedException`，从不返回 `None`，该分支永不成立且会误导读者以为「会话不存在 = ValueError」。
- **入口分类（唯一口径）**：

  | 类别 | 入口 | 会话不存在时 |
  | --- | --- | --- |
  | **会启动** | `create`、`pages/*`、`webrtc/offer`、工作流执行 | 先 `would_queue_browser_session()` 前置；内存不足返 `2013`，否则自动启动并进入内存队列 |
  | **只消费** | 调试 / 单步执行（`/actions/execute`、`/actions/execute_step`、`/workflows/execute_step`） | 返回 `1007 BROWSER_NOT_STARTED`，由前端引导用户点「启动浏览器」 |

  **调试入口不承担启动职责**：单步执行是高频轻量操作，不应触发「启动浏览器」这一重操作，更不应把 HTTP 请求阻塞在最长 `browser_launch_queue_max_wait_time`（600s）的排队上。会话被闲置回收（§5.15）后，引导用户复用既有排队 UI 重新启动。
- **执行期互斥（工作流 ⇄ 调试）**：工作流执行期间**禁止**调试类接口操作同一会话，避免与工作流的页面操作相互干扰；但**允许直播**——WebRTC `offer` / `answer` / `ice-candidate` 属只读拉流，不影响自动化。
  - **判定不复用 `pin_count`**：`ExecutionEngine.execute_action`（单步调试自身）与 `execute_steps`（工作流）都会 `pin`（见 §5.15 自动化占用），无法据此区分「工作流在执行」与「用户自己在调试」，因此需要**独立的「工作流占用」标记**（如 `BrowserSessionEntry.workflow_run_id: str | None`，由 `WorkflowRunner.run_workflow` 进入时设置、退出时清空）。
  - **互斥响应**：命中时返回新增业务码（落 `bili_common.models.response_code`，语义「该浏览器正在执行工作流」），前端提示「浏览器正在执行工作流，请稍后重试」。
- **会话统一有头**：所有浏览器实例均为**有头模式**（`xvfb_enabled` 提供虚拟屏幕，见 §5.11），**不存在无头会话，定时任务也不例外**。
  - **已修正（本轮落地）**：`app/services/execution/workflow_runner.py` 原传 `headless=True`（该值会透传到 `Botright(headless=...)` 产生真正的无头 Chromium），现改为 `headless=False`。
  - **依据**：有头模式是反自动化检测的关键（见 `app/config.py` 中 `xvfb_enabled` 的注释——服务器无物理显示器，用 Xvfb 提供虚拟屏幕，浏览器仍是完整有头模式）。定时任务同样要访问 B 站页面，无头指纹会显著抬高被检测风险，不能因「无人值守」而降级为无头。
- **排队时长估算（ETA）**：`/browser/control/queue_status` 增加 `estimated_wait_seconds` + `estimate_reliable`，供前端展示「预计还需约 X 秒」。模型按「排队慢在哪」分两种情形：
  - **名额已释放**（`_admission_budget() > 0`）：剩余等待只来自放行冷却，估算 = 冷却剩余 + 前方人数 × 冷却周期，标记**可信**；
  - **名额不足**：时间主要花在「等别的会话释放内存」上，用**实测连续放行间隔**推算——内存越紧张、间隔越大，估算自动放大；但释放时机取决于其他会话的关闭时刻，无法预测，故标记**不可信**；样本不足时退化为冷却下限（偏乐观）。
  - **采样口径**：仅在「放行后队列仍有等待者」时记录放行时刻。该间隔由内存释放 + 冷却共同决定，才是排队时长的有效信号；队列排空后的间隔只反映空闲时长，纳入会严重高估。
  - **队首不返回 0**：名额不足时队首（前方 0 人）仍要等下一次放行，故按「前方人数 + 1」个间隔估算，避免「0 秒」误导。
  - **本质局限**：内存何时释放取决于其他会话的关闭时机，不可预测，因此该值只作参考、不作承诺，前端措辞必须区分可信 / 不可信两种口径。
  - 配置：`browser_launch_eta_sample_window`（默认 20）、`browser_launch_eta_min_samples`（默认 3）。

- **错误码语义（本节明确）**：

  | code | 语义 | 适用入口 |
  | --- | --- | --- |
  | `1007` | 浏览器未启动 / 已被闲置回收 | 调试 / 单步执行 |
  | `2013` | 内存不足，启动请求已进入排队 | 会启动的入口 |
  | 待新增 | 浏览器正在执行工作流 | 工作流执行期间的调试请求 |

- **前端需求**：见 `docs/frontend_requirements/浏览器调试接口准入与互斥.md`。

### 5.18 RPA 浏览器 WebRTC 清晰度档位与自动降载

- **背景问题**：§5.16 的清晰度控制只有**布尔两档**（`VideoFrameProducer.set_degraded(bool)`），且完全由后端闲置生命周期单向驱动（闲置降档、真实操作 `touch` 恢复）。两个缺口：① 用户无法主动选清晰度（弱网 / 小屏场景只能忍受默认画质）；② 前端把标签页切到后台时，画面仍按满帧编码传输，CPU / 带宽 / 电量纯属浪费。
- **档位定义**（`StreamQualityLevelEnum`，越省资源档位越低）：

  | 档位 | JPEG quality | 分辨率（浏览器侧） | 帧率 |
  | --- | --- | --- | --- |
  | `ultra` 超清 | 90 | 1920×1080 | 30fps |
  | `high` 高清（默认） | 80 | 浏览器自适应（≤800×800） | 30fps |
  | `medium` 标清 | 65 | 960×540 | 15fps |
  | `low` 流畅 | 50 | 640×360 | 5fps |

  `high` / `low` 与改造前的「正常档 / 降级档」参数完全一致，**行为向后兼容**；`medium` 为新增中间档。
- **「取最省」仲裁**：三个来源各自只表达「我想要哪一档」，最终生效档位取其中最省的一个，彼此无需感知对方：

  | 来源 | 表达 | 说明 |
  | --- | --- | --- |
  | 用户手动 | `user_level`（默认 `high`） | 前端清晰度选择器 |
  | 前端可见性 | `visibility_low`（bool） | 标签页切后台 / LiveBox 不可见 |
  | 后端闲置 | `idle_degraded`（bool，沿用既有 `set_degraded`） | §5.15 闲置生命周期驱动 |

  **生效档位 = `low` if (可见性低 or 闲置降级) else user_level**。
  这解决了两类冲突：闲置降级**始终生效**（省资源优先，用户选高清也不能阻止）；`touch` 恢复只解除闲置来源，**不解除可见性来源**（页面仍在后台时不该恢复满帧）。
- **接口**（均为控制类，不涉及 SDP 重协商）：

  | 接口 | body | 语义 |
  | --- | --- | --- |
  | `POST /browser/control/webrtc/quality` | `{ level }` | 设置用户档位，作用于本会话所有流 |
  | `POST /browser/control/webrtc/visibility` | `{ visible }` | 前端可见性信号：`false` 降档、`true` 恢复 |

  档位切换通过**重启 screencast**（`_restart_screencast`）生效，WebRTC 连接与轨道不变，前端画面自然衔接（切换瞬间可能丢 1~2 帧），**无需重连、无需重新 offer/answer**。
- **前端自动降载**：`LiveBox.vue` 同时监听两类不可见，任一不可见即 `visible=false`，全部恢复才 `visible=true`：
  - `document.visibilitychange`（标签页切后台 / 最小化）；
  - `IntersectionObserver`（LiveBox 被 `el-splitter` 折叠、被弹层遮挡、滚出视口）。

  **组件卸载 / 主动停流时需复位**，避免残留不可见状态把后续新流压在低档。
- **暂停 / 恢复**：`POST /browser/control/webrtc/pause`（body `{ paused }`）——用户主动暂停发送视频。
  - **暂停**：停止 screencast（浏览器侧不再做 JPEG 编码），并让轨道 `recv()` 挂起、不返回帧。效果：带宽归零、CPU 近乎归零；接收端画面停留在最后一帧（浏览器行为，非后端保证）。
  - **恢复**：重启 screencast，画面立即续上。**全程不重建 WebRTC 连接**，无需重新 offer/answer。
  - **与档位无关**：暂停是独立开关，优先级高于清晰度档位（暂停时不出帧，无论选了哪档），也**不参与**「取最省」仲裁。
  - **关键约束**：`recv()` 挂起期间**绝不能返回 `None`** —— 那会被 `WebRTCMediaTrack` 判定为「生产者已停止」而抛 `MediaStreamError`、直接结束轨道（连接随之结束）。因此 `stop()` 必须唤醒挂起的 `recv()`。
- **可观测**：`VideoFrameProducerStats` 增加 `level`（生效档位），便于校验降档是否真正生效。
- **前端需求**：见 `docs/frontend_requirements/WebRTC清晰度档位.md`。

### 5.19 等级指纹配额（浏览器数量上限）管理端配置

- **配置源**：`RPA-Browser/app/data/permissions.json` 的 `levels[].max_fingerprints`，由 `PermissionConfigService`（`app/services/RPA_browser/permission_config_service.py`）读写；文件缺失或读取异常时回落代码内 `DEFAULT_CONFIG`（缺失时按默认值自动生成该文件）。读取**每次都直接读文件、无进程内缓存**，改完即时生效、无需重启。
- **生效点**：`verify_fingerprint_limit`（`app/utils/depends/security_depends.py`）挂在「创建/更新浏览器指纹」接口上 —— 指纹数 ≥ 该等级 `max_fingerprints` 即拒绝；`root` 角色恒取 root 档（不受等级限制），未匹配到 `level_value` 时返回 0（不允许创建）。超限抛 `FingerprintLimitExceededException`（业务码 `2008`）。
- **管理端接口（仅 root）**：
  - `GET /api/admin/rpa/permission/levels`：返回各等级 `level_name` / `level_value` / `permissions` / `max_fingerprints`，并附带 `config_file`（实际读写路径，便于运维定位）。
  - `POST /api/admin/rpa/permission/update`：**只接受 `max_fingerprints`**，按 `level_name` 合并进磁盘现值后整体写回；`permissions` 与 `level_value` 一律以服务端现值为准——即使调用方伪造这两个字段也不会生效，避免经配额接口变相改功能权限位。未知 `level_name` 直接 400。
  - `POST /api/admin/rpa/permission/reset`：恢复为代码内 `DEFAULT_CONFIG` 并写回配置文件（同样 root-only + 审计），供误改 / 数据异常时一键回滚。
- **落地**：`app/controller/v1/admin/permission_router.py`（`require_root` + `log_admin_action("permission:update", ...)` 审计），业务逻辑在 `PermissionConfigService.update_max_fingerprints()`；路由路径常量在 `app/models/router/router_prefix.py` 的 `AdminPermissionRouterPath`，子路由在 `app/controller/v1/admin/__init__.py` 聚合。
- **Docker**：`docker-compose.yml` 的 `rpa-browser` 显式挂载 `./RPA-Browser/app/data:/app/app/data`（与既有 `chrome_app` 同一手法：更具体的挂载覆盖外层 `./RPA-Browser/app:/app/app`），避免将来去掉源码挂载后配额配置随容器重建丢失。
- **前端需求**：见 `docs/frontend_requirements/等级指纹配额管理页.md`。

---

### 5.20 WebRTC 观看端前提与前端自愈（2026-09-26 实测）

- **观看端浏览器必须能产出 ICE 候选**：本机实测「受控浏览器」（`RPA-Browser/botright/botright.py` 下发的 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`、`--webrtc-ip-handling-policy=disable_non_proxied_udp`，以及指纹里的 `mockWebRTC`）**产出 0 个候选**、`iceGatheringState` 立刻 complete。用它打开前端观看直播时：后端一个远端候选都收不到 → `ICE: checking` 永不推进 → 画面全黑（后端日志表现为 `Answer 内候选数=0`，且没有任何 `ICE Candidate 已添加`）。带 WebRTC 防护的指纹浏览器 / `WebRTC Network Limiter` 类扩展同理。
  - **看直播请用未启用 WebRTC 防护的浏览器**（普通 Chrome / Edge / Firefox 即可）；
  - 若要兼容这类客户端，唯一正解是部署 TURN：`disable_non_proxied_udp` 的语义是「只允许经代理 / TURN 的 UDP」，配了 TURN 才会产出 relay 候选（顺带解决远端 / NAT 场景）。
- **后端链路已实测正常**：用 aiortc 客户端（真实 host / srflx 候选）跑完整 offer/answer → `ICE completed`、`connection connected`、首帧 800×450 到达。因此「黑屏」优先排查**客户端候选**，而不是后端出帧。
- **前端自愈（`LiveBox.vue`）**：
  - 发 answer 前 `waitForIceGatheringComplete()`（3s 超时）并以 `pc.localDescription.sdp`（**自带候选**）提交，trickle 降级为「锦上添花」；
  - **候选上报必须晚于 answer**：Chrome 在 `setLocalDescription(answer)` 期间就回调候选，此时后端 PeerConnection 还没有 remote description，直接上报必然失败（实测该 POST 会拿到 **502**）。故 answer 提交前收集到的候选先**入队**，`answer` 返回 `code=0` 后再补发，并对 502 / 抖动重试一次；
  - 本端候选数为 0 → 报 `rpa.streamNoIceCandidate`（zh-CN / zh-TW / en / ja / ko 五语言）并中止，不再黑屏装死；
  - 只有 `connectionState === 'connected'` 才算「直播中」（`waitForPeerConnected`，10s 超时）；
  - 「已连接但连续 8s 零字节」看门狗、`connectionState === 'failed'` → 自动重建流（最多 3 次，超限如实停播，用户主动停播不触发）。
- **可观测（把静默失败变可诊断）**：offer 日志打 `本端候选数`、answer 日志打 `Answer 内候选数`、候选入库日志由 DEBUG 提到 INFO；`/webrtc/ice-candidate` 查不到流时打 **WARNING**（此前静默返回业务码，前端也不 throw，问题完全不可见）。

### 5.21 IP 属地解析 RPC（`message.geoip.rpc.resolve_ip_region`）

- **背景**：「谁在看」（RPA 直播观看者列表）需要把客户端 IP 显示成「属地 + 运营商」。
  这两项都依赖 GeoLite2 mmdb，而**库与下载 / 更新流程只在本服务**
  （`docker_vol/geoip/mmdb`，见 `scripts/download_geoip_mmdb.py`）；
  若让 RPA 也装 `geoip2` + 挂一份 66MB 的 City 库，等于一份库要更新 N 次。
- **做法**：本服务作为 RPC 服务端暴露 `resolve_ip_region`
  （`app/mq/rpc_geoip.py`，复用 `app/services/infrastructure/geo_ip.py::lookup`：
  **City 库出属地、ASN 库出运营商 / ISP**，一次调用一并返回，避免调用方查两次），
  约定与 `message.notify.rpc.*` / `message.push.rpc.*` 一致
  （TOPIC exchange `message_exchange`，队列名 = routing_key，durable，`@rpc_safe` 兜异常）。
- **契约**：`bili_common.rpc.geoip`（`ResolveIpRegionParams{ip}` →
  `ResolveIpRegionResult{region, isp}`），
  路由键前缀 `bili_common.rpc.base.GEOIP_RPC_ROUTING_KEY_PREFIX`。
- **语义**：`region=""` / `isp=""` 表示「没有可展示的值」（空 IP / 内网 / 未命中 / 库缺失），
  即 `lookup` 的「未知」与 `None` 在 RPC 边界被归一成空串 —— 文案由调用方决定
  （前端显示「未知属地」「未知运营商」），调用方不需要重试。
- **收益**：mmdb 单一来源 + 属地口径与评论 / 动态的 `lbsPoi` 完全一致
  （不会出现「动态显示浙江、观看者显示杭州」）；调用方零新增依赖。

### 5.23 用户空间属性的面向对象模型（2026-10-08）

**背景**：用户的「多维度可见性属性」原先散在四处各自为政 —— `update_flags` 逐字段抄 5 遍、
`apply_flags_to_info` 逐字段 `if not flags.x`、`FollowService._ledger_visible_to_viewer(..., flag_name: str)`
用**字符串**取开关（拼错只有运行时才炸）、`list_fans` / `SpaceTimelineService` 又各自内联 `flags.show_xxx`；
分组归属与统计数字还以裸 `dict` 传递。加一个维度要改 4~5 个文件，且规则容易分叉。

**落地：新增领域层 `app/services/user/space/`**

| 模块 | 内容 |
| --- | --- |
| `attributes.py` | `AttributeKey` / `AttributeScene`（profile_field / content_list / timeline_entry）/ `AttributeStorage`、`AttributeSpec`、`UserAttribute` 抽象基类与 6 个维度子类、注册表 `SPACE_ATTRIBUTES` + `attribute_of()` |
| `visibility.py` | `SpaceVisibility`（owner + viewer + flags），`can_view(key)` 是**唯一可见性判定出口**，`mask_profile(info)` 负责敏感原文裁剪 |
| `relation.py` | `FollowRelationState`：双向状态 → `mutual` / `blocked` 派生语义，`to_resp()` 出 DTO |
| `membership.py` | `TagCounts` / `TagMembership`：分组计数与归属值对象（替代裸 dict） |
| `stats.py` | `SpaceStatSummary`：关注/粉丝/互关/动态/获赞/被访问汇总，`to_follow_stat()` / `to_up_stat()` |
| `briefs.py` | `UserBriefs`：批量用户展示信息（显式区分「未覆盖」与「已注销」） |

**每个维度自己携带**：key（= DB 列名 = 响应字段名）、设置页 label/hint、适用场景、存储位置
（`TUserSpacePrivacy` 或 `TUserFavoriteSetting`）、缺省值，以及关闭时如何裁剪（`mask`）。
因此：

- `SpacePrivacyService.get_flags` / `update_flags` 改为**注册表驱动**（加维度只加一个类 + 注册一行）；
- 门控统一为 `visibility.can_view(AttributeKey.XXX)`（字符串开关名彻底移除）：
  `follow/followings` → `FOLLOW_LIST`、`follow/fans` 与主页粉丝模块 → `FANS_LIST`、
  时间线 → `FOLLOW_LIST` / `LIKE_LIST` / `FAVORITES`；
- `SpacePrivacyService.apply_flags_to_info` 删除，改由 `visibility.mask_profile(info)`；
- 路由层 `pptr_user_gateway` 用 `SpaceStatSummary` 聚合统计（来源跨关注 / 动态 / 访问计数三个域），
  不再在路由里拼两个 DTO。

**顺带修正两处「实现与契约不一致」**（行为变化，方向都是收紧）：

1. `show_personal_info` 关闭时现在**真的**裁剪 `sex` / `birthday`（此前只裁了 `email`，
   与字段描述「性别 / 生日 / 邮箱」不符）；
2. 行为时间线对**未登录访客**现在也按开关过滤（此前 `flags = None` 直接放行，
   未登录能绕过 `show_follow_list` / `show_like_list`，属漏过滤）；
   与 `space/fans`、`follow/*` 的口径至此完全一致。

### 5.23.1 「上次登录时间与 IP 属地」撤销隐私开关（2026-10-08）

与统计数字同一口径，**固定公开、不提供关闭入口**（需求文档 §0.1.1）：

- `AttributeKey.LOGIN_INFO` / `LoginInfoAttribute` 从属性注册表移除，`SPACE_ATTRIBUTES` 由 6 项降为 5 项；
- `SpacePrivacyFlags` / `SpacePrivacyUpdateReq` 删除 `show_login_info` 字段；
- `TUserSpacePrivacy.show_login_info` 列删除（新增一条 alembic 迁移）；
- `mask_profile` 不再裁剪 `last_login_at` / `ip_location`，路由层**无条件下发**。

> 契约变更（请求 / 响应模型去字段）→ 前端 hey-api SDK 需重新生成。

### 5.23.2 新增「时间线」公开开关（2026-10-08）

时间线此前只有按条目类型的 `show_follow_list` / `show_like_list`，缺少整条时间线的开关。
新增 `AttributeKey.TIMELINE = "show_timeline"`（`SPACE_ATTRIBUTES` 4 → 5 项）：

- 场景 `CONTENT_LIST`；`SpaceTimelineService.list` 最前面门控 —— 本人恒可见，他人开关关闭 → 空列表；
- 表列 `TUserSpacePrivacy.show_timeline`（**默认 1 = 开启**，与收藏的「缺省展示」同口径）+ alembic 迁移；
- `SpacePrivacyFlags` / `SpacePrivacyUpdateReq` 加该字段；
- 与 follow / like 的关系：`show_timeline` 是**总开关**，关闭即整条时间线不可见；打开后条目仍逐类过滤
  （关注 / 点赞按各自开关，收藏按逐夹 `is_public`）；
- 时间线 tab 仍恒展示（不因开关隐藏 tab）；
- 契约变更 → hey-api SDK **已重新生成**（2026-10-08）：前端切回生成的 `SpacePrivacyFlags` /
  `SpacePrivacyUpdateReq`，临时交叉类型与断言已删除。

### 5.26 关注 / 粉丝列表换用专用模型 `FollowUserBrief`（2026-10-09）

`FollowListItem.user` 由 `UserBriefOut` 改为新的 `FollowUserBrief`，只保留列表卡片需要的
`mid / name / face / sign / level / vip_status / vip_type`；装配由 `FollowUserBrief.from_brief()`
从 pptr 简档裁剪（仍一次 `PptrUser.get_many`，无 N+1）。前端关注 / 粉丝卡片据此展示「个性签名」。

- 契约变更 → hey-api SDK 需重新生成；
- 消费方（本人黑名单表格）字段从 `user.avatar` / `user.uname` 改为 `user.face` / `user.name`。

### 5.27 ruff 静态检查落地（2026-10-09）

**背景**：`be-message-service` 的 dev 组早已装了 `ruff`，但 `pyproject.toml` 里**没有 `[tool.ruff]`**
—— 没有项目配置时，检查结果取决于运行环境的默认/用户级配置，**不可复现**（本机实测：无配置时
默认只跑 `E4/E7/F`，但命令输出混入 SIM/UP/TRY 等 451 条，说明行为随环境漂移）。本次补齐配置并清零。

**配置**（`be-message-service/pyproject.toml`）：

```toml
[tool.ruff]
target-version = "py311"
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "B", "UP", "SIM", "RET", "C4", "RUF"]
ignore = ["E501", "B008", "RUF001", "RUF002", "RUF003"]
```

**ignore 的理由**（这几条是本项目必须豁免的，别在 review 里反复讨论）：

| 规则 | 为什么 ignore |
| --- | --- |
| `E501`（行太长） | 交给 formatter 处理，linter 不管宽度 |
| `E712`（`== True/False`） | **SQLModel / SQLAlchemy 列比较必须写 `col(X) == False`**：ruff 建议的 `not X` 在 SQL 表达式里语义不同，照它改会直接改坏查询条件 |
| `B008`（默认参数里调函数） | **FastAPI 依赖注入的基本写法**（`x: int = Query(...)` / `Depends(...)`），开了等于禁掉 FastAPI |
| `B024` / `B027` | Biz / 状态机基类用「默认空实现的钩子方法」做约定，子类按需覆盖，不是漏写 `@abstractmethod` |
| `RUF001/002/003`（歧义 Unicode 字符） | 本项目注释 / docstring 全中文，全角标点（，：（））会被判定为「歧义字符」，**单这一族就 2 万+ 条**，纯噪音 |
| `RUF012`（可变类属性默认值） | 本项目的类级容器都是**有意共享**的：注册表 `_registry`、常量映射 `ROLE_BIZ_PERMS` / `error_messages`、SQLModel `__table_args__`、测试记录器；逐处补 `ClassVar` 只有注解收益 |
| `SIM105` | `except: pass` → `contextlib.suppress` 属可读性偏好，不强改既有写法 |

另有 `per-file-ignores`：`alembic/env.py`（`E402`+`F403`，模板要求先 `sys.path` 再 `import *`）、
`scripts/*` 与 `tests/test_moment_interaction.py`（`E402`，先补 `sys.path` 再 import）。

**落地方式**：先 `uv run ruff check --fix .` 自动修可修项（`I001` import 排序、`F401` 未用导入、
`RUF100` 失效 noqa、`UP007/035/037/045`、`RUF022` 等），再人工清零剩余项。
**要求：`uv run ruff check .` 必须 0 报错**（否则 CI 加了等于没加）。

**边界（重要）**：ruff 是 **linter**，查的是「语法 / 风格 / 明显错误」，**查不出类型不匹配**。
例如 2026-10-09 那个 500（把裸字符串 `"show_fans_list"` 传给声明为 `AttributeKey` 的参数）ruff 一条都报不出来 ——
这类只能靠**类型检查器**：

```bash
uv run ty check          # Astral ty（已配 [tool.ty.environment]，快）
uv run mypy app          # 或 mypy（dev 组已装）
```

两者是**互补**关系：ruff 管「写得对不对」，类型检查管「类型对不对」。

### 5.28 主库 Alembic 版本管理重建（基线压缩，2026-10-11）

**背景**：`BiliMessageDB` 已与生产环境对齐（以生产库真实结构为准）。实测发现主库
`alembic_version` 停在 `20260920_stat_viewlog_enum`，而代码 head 是 `20261009_feed_event_log`——
**库落后 5 个版本**，且这 5 个迁移涉及的真实结构变更（`TUserSpacePrivacy`、
`msg_user_deactivation`、`msg_user_follow_tag*`、`TFeedEventLog`、`TFeedBanditArm` 建表，
`TUserFavoriteSetting` 删除 + `TFavoriteFolder.is_public` 新增）**在生产库一次都没落过**。
继续在旧链上追加迁移，等于让新环境从零重放 11 段历史 DDL，而这些历史本身已经和生产脱节。

**做法**：与 pptr 库（§ 见 `alembic_pptr/versions/` 的 `init_pptr_production_baseline`
+ `sync_models_to_production`）**保持同款口径**，把主库 `alembic/versions/` 压缩成两条：

| Revision | 文件 | 语义 |
| --- | --- | --- |
| `20261011_msg_prod_baseline` | `20261011_msg_prod_baseline.py`（**空 `upgrade()`**，`down_revision=None`） | **基线即生产库现状**，不做任何结构变更 |
| `sync_to_prod` | `20261011_sync_msg_to_prod.py`（结构性差异） | 生产库现状 → 代码模型的**唯一真实差异**，之后所有演进从这里 autogenerate |

> ⚠️ **revision id 必须 ≤ 32 字符**：`alembic_version.version_num` 是 `VARCHAR(32)`，
> 超长会在 `stamp` / `upgrade` 时直接报 `Data too long for column 'version_num'`。
> 首版曾用 `20261011_init_message_production_baseline`（39 字符）踩过此坑。

**基线是空 DDL，不做「从零建库」**：与 pptr 库
（`alembic_pptr/versions/20260810_1030-fda501cc07b2_init_pptr_production_baseline.py`）
同款口径——基线表达的是「库已经是生产结构」这个既成事实，`stamp` 即可视为已对齐。
本服务也不存在空库建表路径：私信正文分片本就由 `app/core/sharding.py` 运行时懒创建，
新环境一律从生产库快照恢复。

| 场景 | 行为 |
| --- | --- |
| 存量生产库 | `alembic stamp <基线>` → `alembic upgrade head` 执行 sync |
| 全新空库 | **不支持**（基线不含建表 DDL） |

**sync 的 DDL 由 `alembic revision --autogenerate` 生成**（未手写），生成后**手工删改**三处：

- 剔除 21 对已有表的复合排序索引重建（`created_at DESC` / `pubTime DESC` 等）——
  生产索引已能满足查询，基线同步不重排索引；
- 剔除 `drop_table_comment('msg_sys_config')` —— 注释非结构；
- 给 `TFavoriteFolder.is_public` 补 `server_default=1` —— 该列 `NOT NULL`，
  autogenerate 原样输出无默认值，在有存量行的表上会失败；带默认值使存量行回填「公开」，
  保持迁移前可见行为（§5.25）。

`downgrade()` 与 `upgrade()` 严格对称，只回退上述结构性变更。

**`bizId` 类型：模型改回 `BIGINT` 才让 autogenerate 干净**。原先 `ResourceBase.bizId`
（`base_tbl.py`）与 `bili-common` 的 `ReportBase.bizId`（`report.py`）声明为 `str` /
`VARCHAR(64)`，而生产库 7 张表（`TResourceFavorite/Like/Dislike/AuditLog`、`TUserReport`、
`msg_comment_report`）全是 `bigint`，导致每次 autogenerate 都报这 7 处虚假差异。
已改为 `int` / `sa_type=BIGINT`，**模型与库一致后该差异自动消失**，无需再靠 sync 剔除。
下游影响已排查：SQLModel lax 校验会把数字字符串自动转 int；RPA 系资源 id 全是纯数字雪花 id，
不存在非数字 bizId 的数据风险。

**原生 ENUM 的成员顺序：生产库并存两种历史尾序，sync 不去动它**。旧 `others_lot_dyn_enum`
用固定顺序 `["OTHERS_LOT_DYN", "RPA_TAG"]` 追加它负责的 11 列；而 `TInteractionStat` /
`TInteractionViewLog` **不在**该迁移清单内，直到 `stat_viewlog_enum` 才用枚举定义顺序补上，
尾序因此与那 11 列相反。成员集合一致、仅顺序不同，而顺序决定 MySQL ENUM 的内部索引值。
基线为空 DDL、sync 不含 `alter_column`，故**两列的历史尾序被原样保留**，不会与模型产生偏差；
**真要收敛这个历史不一致，应作为独立的数据迁移显式处理，不该混在基线压缩里**。

**幂等与存量数据**：

- `TFavoriteFolder.is_public` 为 `NOT NULL`，故**带 `server_default=1`** 新增，存量行回填公开，
  保持迁移前的可见行为（对应 §5.25「逐夹可见性」）；
- `TUserFavoriteSetting` 为**整表删除**（全局开关已被逐夹开关取代），无对应新建；
- 其余 6 张表生产库不存在，纯新建，无存量数据处理。

**验证**：生产库 `stamp` 到 head 后再跑一次 `autogenerate`，剩余差异为 21 对索引重建 +
1 处表注释 + `is_public` 的 `server_default` —— **无任何 `create_table` / `drop_table` /
`add_column` / `drop_column`**，即 sync 已完整覆盖「生产库 → 模型」的全部结构性变更。

**pptr 库不动**：实测仅缺 `TUserActInfoLog.idx_log_mid_created`（即 `20260905_act_log_idx`，
库停在 `d366ed68066f`），其余均为 `pk` Identity / `TUserInfo.uid` 自增 / `ip_info_id_fkey`
外键的反射噪音，正常走 `alembic -c alembic_pptr.ini upgrade head` 即可，无需重建版本链。

**已知残留（非缺陷，需知情）**：由于上表刻意剔除了已有表的索引重建与表注释，
后续每次 `alembic revision --autogenerate` 仍会**反复提出**这两类差异。
这是「基线同步只收结构变更」的既定代价：接受重复提案，但**不得**在无明确需求时
把它们顺手写进新迁移，否则等于绕过基线压缩的判断。真正要落地时，按类别单独出一条迁移。

### 5.29 pptr 库 Alembic 版本链压缩（3 条 → 2 条，2026-10-15）

**背景**：pptr 分支（`alembic_pptr/versions/`）当时是 3 条：

| Revision | 语义 |
| --- | --- |
| `fda501cc07b2` | `init_pptr_production_baseline`（空 DDL，`down_revision=None`） |
| `d366ed68066f` | `sync_models_to_production`（建 `TUserExpRecord` + 索引 + 唯一约束、drop 22 张孤儿表） |
| `20260905_act_log_idx` | `TUserActInfoLog.idx_log_mid_created`（head） |

而**生产 pptr 库的 `alembic_version` 停在 `d366ed68066f`**（sync 已应用，只差那个索引），
本地库已到 head。也就是说 `fda501cc07b2` 这条基线在真实环境里已经没有任何库停在上面，
继续留着只是让新库从零重放一段永远不会真实执行的历史。

**做法**：把 sync 那条**提升为新的根**，3 条压成 2 条：

| Revision | 文件 | 语义（压缩后） |
| --- | --- | --- |
| `d366ed68066f` | `20260810_1031-d366ed68066f_sync_models_to_production.py`（改：空 `upgrade()` / `downgrade()`，`down_revision=None`） | **基线**：「库已是 sync 之后的状态」这一既成事实 |
| `20260905_act_log_idx` | `20260905_act_log_idx_.py`（`down_revision=d366ed68066f`） | head：唯一未落生产的索引，原样保留 |

`fda501cc07b2` 文件**删除**。

**为什么保留 `d366ed68066f` 这个 id 而不是另起新 id**：生产库的版本号就是这个值，
保留它 → 生产只需 `alembic -c alembic_pptr.ini upgrade head` 补索引，**不需要 stamp**。
若换成新 id，生产库会立刻 `Can't locate revision`，且无法「部分 stamp」——
它处在「sync 已应用、索引未应用」的中间态，压缩后的链上不再有这个锚点，
任何 stamp 选择都会导致要么重放 sync（对象已存在报错）、要么跳过索引（永久缺失）。

**索引创建改为幂等**：`20260905_act_log_idx` 的 `create_index` 加 `if_not_exists=True`
（`drop_index` 加 `if_exists=True`）。生产库无法预先确认是否已手工建过该索引，
幂等后 `upgrade` 在两种情况下都不会失败。

**代价（需知情）**：sync 的 DDL 从版本链上消失，**不再支持「未 sync 的原始生产快照」
直接 `upgrade head`**（那样会缺 `TUserExpRecord` 与那条唯一约束）。
真遇到这种库：先手工 stamp 到 `d366ed68066f` 之前把 sync 的内容补跑，
或单独出一条迁移承接，不得把 sync 原文塞回基线（那会让已 sync 的库重放报错）。

| 场景 | 行为 |
| --- | --- |
| 生产库（停在 `d366ed68066f`） | `upgrade head` 补索引，零 stamp |
| 本地库（已在 `20260905_act_log_idx`） | `upgrade head` 无操作 |
| 停在已删除的 `fda501cc07b2` 的库 | 需人工介入（见上「代价」），不接受自动 stamp |

**验证**：`alembic -c alembic_pptr.ini history` 只剩两条；本地 `current` 仍为
`20260905_act_log_idx (head)`；`upgrade head` 无操作。

### 5.24 裸 dict 清理（2026-10-08）

**约定**：业务层**不得返回裸 `dict` / `list[dict]`**；外部系统（RPC / pptr）返回的 dict
只允许在**边界处转换一次**，进入业务层即为显式类型（dataclass / pydantic）。

**已完成（用户 / 空间域，100% 清零）**：

| 原裸 dict | 现值对象 |
| --- | --- |
| `PptrUser.get_many() -> dict[int, UserBriefOut]`（34 处调用点） | `UserBriefs`（`of_mid` / `has` / `pairs` / `Iterable`），调用点全部改 `of_mid()` |
| `SpaceTimelineService` 内部 `entries: list[dict]` | `TimelineEntry`（`follow()` / `resource()` / `with_folder()`，`is_dynamic` / `is_lottery` 派生） |
| `_load_moments() -> dict[int, MomentDetailResp]` | `MomentDetails`（`of_dyn()`） |
| `_load_lottery_details() -> dict[int, dict[str, str|None]]` | `LotteryResources.from_rpc()` + `LotteryResourceInfo`（RPC dict 仅在边界转换） |
| `space_view_history` 的 `titles: dict[int, str]` | `DynamicTitles`（`of_dyn()`） |
| `FollowTagService.tag_ids_of() -> dict[int, list[int]]` | `TagMembership`（`tag_ids` / `includes` / `without_system`） |
| `FollowTagService._tag_counts() -> dict[int, int]` | `TagCounts`（`count_of`） |
| `FollowService._briefs_of() -> dict[int, UserBriefOut]` | `UserBriefs` |
| `SpaceInfoResp` 统计内的临时 dict 拼装 | `SpaceStatSummary`（见 §5.23） |

**已完成（第二批：moment 域，100% 清零）**：

| 原裸 dict | 现值对象 |
| --- | --- |
| `_build_lottery_detail_map() -> dict[int, dict[str, str\|None]]` | `Indexed[ResourceDisplay]`（RPC dict 在 `ResourceDisplay.from_rpc` 转换一次） |
| `_load_stats() -> dict[int, TInteractionStat]` | `Indexed[TInteractionStat]` |
| `_load_comment_subjects() -> dict[int, CommentSubject]` | `Indexed[CommentSubject]` |
| `_load_like_states() -> dict[int, bool]` | `Indexed[bool]` |
| `_load_topic_rel_map() -> dict[int, list[int]]` | `Indexed[tuple[int, ...]]`（值容器也换成不可变 tuple） |
| `MomentStatService.batch_read_stats() -> dict[int, TInteractionStat]` | `Indexed[TInteractionStat]` |
| `get_dynamic_stat_counts() -> dict[int, dict[str, int]]` | `Indexed[ResourceCountPair]` |
| `MomentFeedService.get_upstat() -> dict[str, int]` | `MomentUpStat`（`dynamic_count` / `like_count`） |
| `moment_publish` 的 8 处 `-> dict[str, Any]`（发布 / 删除 / 置顶 / 转发 / 预校验回执） | `MomentCreateResp` / `MomentRemoveResp` / `MomentTopResp` / `MomentRepostResp` / `MomentCreateCheckResp`（路由层不再 `Resp(**dict)`） |
| `MomentCreateCheckResp.setting/permission: dict` | `MomentPublishSetting` / `MomentPublishPermission` 强类型占位模型 |
| `feed_engine._extra / rank_feed` 的 map 参数（`author_quality` / `report_counts` / `comment_subjects` / `counts`） | 全部改 `Indexed[...]`，`.get()` → `.value_of()` |
| `topic_feed` / `moment_feed` 内的 `author_q` / `report_counts` 局部 map | `Indexed[AuthorQualitySignal]` / `Indexed[ResourceReportCount]` |

> 顺带修正：旧 `_to_base_resp` 手写的 `"dynIdStr"` 键其实一直被 pydantic 丢弃
> （字符串版雪花 ID 字段名是 `dynId_str`），响应 JSON 契约本就如此，改造后保持一致。
>
> 时间线 / 浏览历史的批量回查（`MomentDetails` / `LotteryResources` / `DynamicTitles`）
> 进一步统一到通用 `Indexed[V]`，专用映射类已删除，只保留 `TimelineEntry`（真正的记录类型）。

**新增通用聚合**（`app/services/common/indexed.py`）：
`Indexed[V]`（不可变 `id → 值`：`of` / `empty` / `value_of` / `value_or` / `has` / `merge` /
`items` / `keys` / `values` / `__iter__` / `__contains__`）与 `ResourceDisplay`
（非 dynamic 资源展示信息，`from_rpc` 是唯一 dict 转换点）。
> 泛型用 `TypeVar` 而非 PEP 695 语法：ruff 的 target-version 由 `requires-python = ">=3.11"` 推断。

**第三批（2026-10-08，按「先边界、后业务」顺序推进）**：

| 域 | 结果 |
| --- | --- |
| `infrastructure`（3） | ✅ 清零：`lottery_rpc` 的 `get_lottery_detail` → `ResourceDisplay`、`get_lottery_details` → `Indexed[ResourceDisplay]`、`get_others_lot_dyn_details` → `Indexed[OthersLotDynDisplay]`（**RPC 边界内一次性转换**，`moment_feed` / `space_timeline` / `others_lot_dyn` 的本地转换全部删除） |
| `audit`（4） | ✅ 清零：`load_category_levels` → `Keyed[str, str]`、`match_categories` → `Keyed[str, CategoryMatch]`（新值对象 `CategoryMatch(level, words)`）、`match` → `Keyed[WordLevel, tuple[str, ...]]`、`mask_hits_by_category` → `Keyed[str, tuple[str, ...]]`；`AuditResult.hit_words` / `hit_categories` 同步改值对象（消费点仅 `all_hit_words` / `_hits_reason`） |

> 新增通用展示值对象 `OthersLotDynDisplay`（`common/indexed.py`）；
> 时间线 / Feed 侧的 lottery 详情不再各自转换，直接透传 RPC 返回值对象。

**仍待清理（18 处，按顺序推进）**：

`interaction_actions`（8，含 `folder.py` 的 `list[dict]` 需与 `FavoriteFolderResp` 对齐，是要设计 DTO 的一处）→
`message`（3）→ `admin`（3）→ `comment`（1）→ `core`（3，其中 `config` 的限流规则属配置模型，
建议改 pydantic Settings 模型）→ `common`（2，`runtime_config` 的校验入参/返回值）→ `consumers`（1，
AMQP headers 属消息边界，建议返回强类型 header 值对象）。

**第二批补充（2026-10-08）**：

- **规则固化**：新增规则 `.codebuddy/rules/领域值对象与装配分层.mdc`（RPA-Browser 侧同步一份），
  明确「禁止裸 dict（返回/参数/字段）」「值对象写法（frozen+slots / of / value_of / 语义方法）」
  「ORM 不许产 DTO（依赖方向只能 schemas → db；装配走 `DTO.from_row()` 或服务层 assembler）」
  「多维度属性用描述符 + 可见性上下文」以及提交前自检清单；
- **`_to_base_resp` 改为 `MomentBaseResp.from_row()`**：装配方法挂在 DTO 上（`TMoment` 通过
  `TYPE_CHECKING` 仅作类型引用），`moment_publish` 里 3 个调用点改为 `MomentCreateResp.from_row(dyn)`
  / `MomentRepostResp.from_row(dyn)`，模块级装配函数删除；
- **通用映射泛化**：`app/services/common/indexed.py` 新增 `Keyed[K, V]`（任意可哈希键），
  `Indexed[V]` 保留为 `Keyed[int, V]` 的语义化别名（既有用法零改动），
  供后续 `(bizType, bizId)` / 枚举 / 字符串键场景使用；`Keyed.merge()` 保持子类类型。

**第三批补充（2026-10-11）**：

- **规则固化**：新增规则 `.codebuddy/rules/unix-timestamp.mdc`，明确「对外 HTTP 出参的时间/日期字段一律为
  秒级 int32 时间戳（`UnixTime` / `OptionalUnixTime`），naive 时间按 `Asia/Shanghai` 解释，未设置为 `0`」，
  并划清边界：请求模型、DB 表模型、RPC 内部传输模型保持 `datetime`，仅在 HTTP 序列化边界转换；
- **工具落地**：新增 `bili-common/bili_common/core/time_utils.py`（`to_unix_timestamp` / `UnixTime` /
  `OptionalUnixTime`），出参模型不再出现 `datetime` 注解，也不再手工 `strftime` / `isoformat()`；
- **已改造出参**：`notify`、`comment`、`event`、`dm`、`ban`、`space`、`moment`、`follow`、`setting`、
  `sys_config`、`user_records`、`ml_status`；`GET /api/v1/user/user_info` 的 `birthday` 由 `%m-%d` 字符串
  改为秒级时间戳（`0` = 未设置）；
- **待办**：出参类型由 `string(date-time)` 变为 `integer`，需**用户手动重新生成前端 hey-api SDK**，
  之后同步前端消费点（生日回填 / 展示等）。

后续轮次需要先定两件事（`Keyed` 已就绪，第 1 条只剩落地）：

1. ~~tuple / str 键的映射~~ → **已就绪**：直接用 `Keyed[K, V]`（`admin/report`、`comment_admin`、
   `base_biz` 的复合键改用它即可）；
2. **边界类 dict**：`infrastructure/lottery_rpc` 的 RPC 返回值应直接返回 `Indexed[ResourceDisplay]`
   （让转换点前移到 RPC 客户端）；`core/config`（`list[dict]` 限流规则）属于配置模型，
   应改成 pydantic 设置模型而不是业务值对象。

**明确保留的两类「类字典」**：

1. `PptrUser.ROLE_BIZ_PERMS: dict[InteractionBizTypeEnum, int]` —— 权限位掩码**常量表**
   （不是返回值，改成语义对象只会让位运算更难读）；
2. `BanStatusResp.services: dict[str, BanServiceStatus]` —— 已进入 **API 契约**
   （改结构会破坏前端），如需改造须先改契约再同步前端。

**验证**：`import` 全量模块通过、`app.main` 可加载、值对象行为逐项实测、
本次改动文件 `ruff` 除既有 `DTZ005`（`datetime.now()` 无 tz，历史遗留）外无新增告警。

### 5.25 收藏夹逐夹可见性（去掉全局收藏开关，2026-10-08）

B 站用「合集 / 系列」做内容聚合，本项目没有，由「收藏」承担 —— 因此收藏不该有全局开关，
改为**每个收藏夹各自可选公开 / 隐藏**。需求见 `docs/frontend_requirements/个人空间收藏夹可见性.md`。

- `TFavoriteFolder` 新增 `is_public`（默认 1，存量回填公开；**默认收藏夹也可改**，但不可删除）；
- 收藏 tab **恒展示**（不再因「他人无公开夹」隐藏，避免额外判断 / 请求）；收藏弹窗
  `MomentFavoriteDialog` 逐项展示 名称 / 「默认」标记 / 公开·隐藏 / 描述 / 封面；
- **删除 `TUserFavoriteSetting` 表**与 `GET/POST /favorite/setting`（全局开关被逐夹开关取代）；
- `FavoriteFolderAction.list_public_folders` / `list_public_items` 去掉全局门控与 403，改为按
  `is_public` 过滤；本人 / 他人分流仍由前端 `isOwnSpace` 决定（公开接口不引入 viewer 参数）；
- 空间属性模型删除 `FavoritesAttribute` / `AttributeKey.FAVORITES` /
  `AttributeStorage.FAVORITE_SETTING`（`SPACE_ATTRIBUTES` 5 → 4 项）；
  `SpacePrivacyFlags` 去掉 `show_favorites`，`get_flags` 只读隐私表；
- 时间线收藏条目门槛改为「本人 OR 所属夹公开」（`space_timeline.py`）；
- 契约变更 → hey-api SDK 需重新生成（`FavoriteFolderResp` / `FavoriteFolderCreateReq` /
  `FavoriteFolderUpdateReq` / `SpacePrivacyFlags`，并移除 `FavoriteSetting*`）。

### 5.22 RPC 调试接口（管理端，root 专用）

- **背景**：RPC 走 RabbitMQ，没有现成的可视化调用入口 —— FastStream `/asyncapi` 文档页的
  「Try it out」默认走**内存 TestRabbitBroker** 且只按默认 exchange 匹配订阅者，本服务全部
  队列绑定在自定义 `message_exchange` 上，必然 404 `"{destination} destination not found."`；
  勾选 `sendToRealBroker` 也只是单向 `broker.publish`（不等待回包），都测不出 RPC 返回值。
  RabbitMQ 管理台虽可借「自建回包队列 + 手填 `reply_to`」测通，但每次要手填路由键与属性，太繁琐。
- **做法**：新增管理端 HTTP 调试接口，把「选方法 → 贴参数 → 发起真实 RPC → 回显信封」收敛成一次调用。
  - `GET /api/v1/message/admin/rpc-debug/methods`：列出**契约表里登记过**的全部可测方法
    （method_name / 归属系统 / routing_key / 参数模型名 / 参数 JSON Schema），前端据此渲染下拉与表单；
  - `POST /api/v1/message/admin/rpc-debug/invoke`：`{methodName, payloadJson, timeout}` →
    服务端 `json.loads` 后**用该方法契约的 params 模型严格校验**，再经
    `bili_common.rpc.client.RpcClient`（Direct Reply-To）真实往返，回显
    `{routingKey, durationMs, reply: StandardResponse}` 原始信封（成功与失败都回显，不吞错）。
- **安全边界**：
  - **仅 root**（`RootUser` 依赖，role=root）；
  - **路由键不接受任意字符串**：只能调契约表登记过的方法（`bili_common.rpc.*` 各 CONTRACT 表 +
    lottery `RPC_METHOD_PARAMS_MODEL_MAP`），杜绝把调试接口当任意 MQ 发布器用；
  - 超时默认 5s、上限 30s，避免长调用拖住事件循环；
  - 参数校验在 HTTP 边界完成，非法参数直接 400 回包，不会把坏消息投进 MQ。
- **实现**：`app/services/admin/rpc_debug.py`（`RpcDebugService`：契约注册表 + 真实往返，
  `RpcClient` 懒连接、进程内复用）；`app/api/rpc_debug.py`（路由）。契约新增
  `bili_common.rpc.geoip.GEOIP_RPC_CONTRACT`（与其余 RPC 模块对齐）。
- **前端**：管理端「RPC 调试」页（方法下拉 + 参数表单/JSON 文本域 + 结果信封展示），
  需求见 `docs/frontend_requirements/管理端RPC调试页.md`。

## 6. 关键约束与决策（当前有效）

| # | 决策项 | 结论 |
| --- | --- | --- |
| C1 | 存储 | 仅 MySQL（`BiliMessageDB`），不引入 Redis；私信按月分库+100 表；图片只存 URL |
| C2 | 评论归属 | Node 端评论代码与 Postgres 表就地冻结，新评论全由 be-message 承担 |
| C3 | IP 处理 | 只存原始 IP，出参打码，管理员明文 |
| C4 | 对外 ID | 雪花字符串出参；分钟短 ID 39 bits、`sequence_bits` 默认 4（限清库环境）；字符串版字段由 `@auto_str` 装饰器派生，后缀可配（默认 `Str`，snake_case 模型可设 `_str`） |
| C5 | 枚举落库 | `IntEnum` 落 SMALLINT 整数，禁原生 ENUM；**遗留例外**：`DmSessionTypeEnum` 仍以 MySQL 原生 ENUM 存储（先于本规则创建），新增值（如 `STRANGER=2`）通过 `ALTER ... MODIFY COLUMN` 在原生 ENUM 上追加；后续若治理统一，可单独迁移该列到 `IntEnum(SMALLINT)` |
| C6 | 站内信 | DB 写路径保证送达；第三方仅 `/push` 站外提醒 |
| C7 | 通知可见性 | 读时用 `func.now()`；受众精确过滤在读取侧 |
| C8 | 响应契约 | 失败一律非 200 HTTP（HTTP 状态与业务码解耦）；细分业务码仍在 body；未登录 -101 + HTTP 401 |
| C9 | 跳转契约 | 后端只发前端路由名，路径只在前端路由表写一次 |
| C10 | biz_type | `InteractionBizTypeEnum` 为业务类型唯一真相源 |
| C11 | 资源定位 | 举报/处置/事件等以 `(bizType, bizId)` 唯一定位，不引入二级分流字段 |
| C12 | 审核状态 | 统一 `ResourceAuditStatusEnum`（NORMAL=1 基准）；各资源审核/单据列统一枚举；旁路评论区/消息状态不并入 |
| C13 | 审核流水 | 全部资源审核流转写 `TResourceAuditLog`（bizType+bizId） |
| C14 | seed | 严禁直写 MySQL，统一走 HTTP API；`scripts/seed_cli.py` 唯一入口，实现按功能分包在 `scripts/seed/`（见 §5.7） |
| C15 | 字段可见性 | 单一 `XxxOut` 模型 + `Private()` 字段标记 + 序列化期按 `ViewerContext` 裁剪（ContextVar 注入）；**禁用** Public/Private 继承与 `to_public()`；安全默认=他人视角（见 §5.12） |

---

## 7. 当前完成度与遗留

### 7.1 已完成
- 消息（通知/事件/私信/设置/推送）、评论后端（发布/列表/楼中楼/赞踩/置顶/@/DFA 审核/管理端）、动态 Moment（发布/Feed/详情/话题/审核/收藏夹/互动）、通用资源 Feed 引擎 + 计数统一（`TInteractionStat`）。
- 互动操作对象化（`BaseBiz` 资源类，7 通用互动全 6 类型实现，审核/举报资源化）；评论锚定事件信息回捞；互动接口通用化；内容每日上限；会话置顶；匿名互动态；举报列表增强。
- **审核状态统一**（本次重构）：审核状态枚举收敛 `ResourceAuditStatusEnum`、审核列统一 `auditStatus`、审核状态机资源化 + 多审核环节编排骨架、审核流水 `TResourceAuditLog` 统一。
- 用户中心（空间/资料更新含头像审核/登录经验）、i18n 后端 5 语言、统一响应码/异常。
- EdgeRank 多维打分 + 个性化/匿名排序、多路召回、曝光去重。
- **字段可见性机制**（本次改造）：`to_public()` 与 Public/Private 继承退役，改为「单一 `XxxOut` 模型 + `Private()` 字段标记 + 序列化期按 `ViewerContext` 裁剪」；`UserBriefPublic/Private` → `UserBriefOut`，评论审核 IP、动态审核流水操作人纳入同一机制（见 §5.12）。

### 7.2 遗留 / 待办
- 评论前端组件接入、动态审核总统计、i18n 前端 Phase 5-11、评论性能优化。
- 内容审核统一引擎（敏感词+用户风控+链接域名+人工，见 §8）未实现。
- 中台流程（RPA 审批联动/举报审核/细粒度权限/操作审计）待跟进。
- seed RPA 资源（操作 `rpa/action`、插件 `rpa/plugin`、提交审批 `rpa/approval`）待接入（见 §5.7）。

---

## 8. 内容审核机制细化（规划设计草案，未实现）

> 目标：按不同资源设不同审核制度；文字统一走**敏感词 + 用户风控 + 链接域名 + 人工**四层；能自动审的自动审掉。词库 `fwwdn/sensitive-stop-words` 下载为仓库静态词表。

- **审核制度矩阵**：动态正文/话题/评论/私信摘要/收藏夹名/举报理由/RPA 资源文字按风险分级（命中低放行/中进人工/高拒）；头像/封面保留图片 URL 域名校验。
- **统一引擎 `AuditEngine`** 输出 `decision ∈ {PASS, REJECT, AUDIT}`：①敏感词（Trie，按高中低分档，中→AUDIT）②用户风控（封禁/被举报/违规累计从严）③链接域名（黑名单拒/白名单放/未知审）④综合（有 REJECT 即拒，全 PASS 才过，否则 AUDIT）。
- **自动优先流转**：PASS 直接放行（动态可跳过 AUDITING）；AUDIT 落人工队列复用 `TResourceAuditLog` 记流水；REJECT 直接拒并给作者原因。
- **分阶段**：P0 统一引擎+词库+单测 → P1 接入评论/动态正文 → P2 扩展话题/私信/收藏夹/举报/RPA → P3 治理闭环（通过/驳回命中词反馈词库）。
- **数据/契约**：新增 `services/audit/`（word_filter/link_checker/engine）；各资源创建入口发布前调引擎分流；评论 DFA 抽成共享 word_filter。
