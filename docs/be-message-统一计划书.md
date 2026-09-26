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
- **RPC**（RabbitMQ 同步，非 HTTP）：`message.notify.rpc.publish_notify`、`message.push.rpc.*`、`message.pptr.rpc.*`（用户读写），be-message 也作为 RPC 客户端调 RPA/lottery 详情。

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
