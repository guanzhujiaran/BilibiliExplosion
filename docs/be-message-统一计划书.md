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
- **枚举落库**：业务枚举一律标准库 `enum.IntEnum`，模型字段 `Field(sa_type=IntEnum(EnumCls))` 落 SMALLINT 整数；**禁用原生 ENUM**（存成员名会导致查询/过滤错乱）；列类型从 `bili_common.models.db_types` 导入 `IntEnum/StrEnum`。
- **鉴权**：身份来自网关注入 `x-bili-*` 头（微服务互信）；依赖注入 `CurrentUser/RequiredUser/AdminUser/RootUser`（管理端审核统一 `RootUser`）。
- **i18n**：后端 bili-common 层 fastapi-i18n + 延迟翻译；前端 vue-i18n + Accept-Language。
- **MQ 契约**：`bili_common/rpc/` 统一收编；`bili_common.exceptions` 统一异常。
- **模型文件命名**：`app/models/db/` 各表模型统一 `_tbl` 后缀；包导出方式不变。
- **输出模型命名**：对外响应模型统一 `XxxOut` 后缀（对齐 FastAPI「输出模型过滤」语义）；字段可见性一律用 `Private()` 标记 + 序列化期上下文裁剪表达（见 §5.12），**不再用 Public/Private 继承**。
- **跳转契约**：后端只发前端路由名（`route:{name}?{query}`，枚举 `FrontendRouteEnum`），路径只在前端路由表写一次。
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
- **消息** `/api/v1/message`：`notify`（通知）/`event`（事件）/`dm`（私信，含 send/审核/置顶）/`setting`/`msg_feed`/`follow`/`push`/`admin`。
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
- **抽奖卡片详情 HTTP 接口（be-bilibili-crawler 侧）**：`POST /api/v1/lottery_database/bili/GetLotteryDetail`（body `{lottery_id}`）按 `dyndetail.lotdata.lottery_id` 返回完整卡片原始行（LotdataResp 形态）+ `t_lot_extra_info` 附加信息，供前端卡片详情页（`/app/lot-data/card-detail?id=`）按 id 拉取详情渲染，替代 localStorage 旧缓存传参。互动资源 ID 口径不变：lottery 一律 `lotdata.lottery_id`（预约 sid / 天选 lot_id / 第三方 dynId 不作为互动资源 ID，缺失 lottery_id 的旧数据前端禁用互动）。

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
- **DDL 约束**：`msg_event.event_type` 用原生 ENUM 存成员名（存量遗留，与 §2.3 不一致），新增枚举成员须同步 ALTER。

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
- 复用 `BaseBiz` 体系：各资源实现 `check_exists()/_load_meta()` 钩子，`get_resource()` 统一装配 `InteractionResource`，`batch_get_resources()` 为每类批量接口（一次 IN/RPC 防 N+1）；不存在返回 `exists=False` 空占位。
- 评论锚定事件（REPLY/AT）正文经 `CommentBiz.batch_get_resources` 批量回捞，出参带楼层作者 `source_mid/name` 等。

### 5.11 其余机制要点

- **互动接口通用化**：`/thumb /dislike /share /report` 一律 `bizType+bizId` 定位；路由层只做「`resolve_target` 归一 → `get_biz(...).动作()` → 装配」，防乱调/计数/装配在 service 层。
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
- **动态不可编辑**（2.58.0 移除 `POST /edit`）；转发/发布/删除/置顶保留。
- **会话置顶**：`top_ts`（毫秒，0=未置顶）唯一真相源，列表 `top_ts DESC → last_msg_ts DESC`，可多会话置顶。
- **匿名可读互动态**：`interaction/status` 依赖降级 `OptionalUser`，匿名 `viewer_mid=0` → `isLike/isFavorite` 恒 false；浏览统计不匿名投递。
- **举报列表**：`ReportItem` 追加举报人/被举报人用户信息 + 资源快照 `resource`（一次批量回捞）。

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

---

## 6. 关键约束与决策（当前有效）

| # | 决策项 | 结论 |
| --- | --- | --- |
| C1 | 存储 | 仅 MySQL（`BiliMessageDB`），不引入 Redis；私信按月分库+100 表；图片只存 URL |
| C2 | 评论归属 | Node 端评论代码与 Postgres 表就地冻结，新评论全由 be-message 承担 |
| C3 | IP 处理 | 只存原始 IP，出参打码，管理员明文 |
| C4 | 对外 ID | 雪花字符串出参；分钟短 ID 39 bits、`sequence_bits` 默认 4（限清库环境） |
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
