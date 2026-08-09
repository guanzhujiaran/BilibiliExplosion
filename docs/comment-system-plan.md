# B 站式评论系统开发计划书（集成至 be-message-service）

> 参考：[B站评论系统架构设计 - 哔哩哔哩技术](https://www.bilibili.com/opus/737531797122842865)（2022-12-09）
> 落地载体：`be-message-service`（FastAPI + FastStream(RabbitMQ) + SQLModel + Alembic + APScheduler）
> 存储：**仅 MySQL**（`BiliMessageDB`），不引入 Redis
> 环境与运行：**全程 uv**（`uv sync` / `uv run ...`）
> 文档状态：决策已确认，待启动第一阶段编码

---

## 进度看板（实现了就在这里打勾）

- [x] **Phase 1** — 数据模型与基础架构：表结构 + 枚举 + 骨架分层 + 基础 CRUD ✅（2026-08-03）
- [x] **Phase 2** — 核心功能：发布（文本/表情/图片/@）、列表（热度/时间）、楼中楼、点赞 ✅（2026-08-03）
- [x] **Phase 3** — 互动与通知：@搜索、事件通知复用、排序切换、置顶 ✅（2026-08-03）
- [ ] **Phase 4** — 前端组件：输入框 / 列表 / 楼中楼 / 评论卡片 ⛔ **阻塞**：`.gitmodules` 无前端仓库，无法落地（见 Phase 4 前置阻塞说明）
- [x] **Phase 5** — 优化与完善：审核 / 统计 / 异常兜底 / 计数对账已落地；性能验证（EXPLAIN、游标分页）与网关路由待补 ⚠️（2026-08-03）

> 每阶段下有细项勾选框，完成一项勾一项；阶段整体完成后再勾总看板。
>
> **本轮交付说明（2026-08-03）**：PHASE 1–3 与 PHASE 5 后端全部落地（数据模型、CRUD、发布/列表/楼中楼/点赞、@搜索/通知/排序/置顶、DFA 敏感词审核、管理端审核队列+明文 IP+统计、热度重算与计数对账定时任务），新增 `tests/test_comment_crud.py`、`tests/test_phase_e_enums.py`、`tests/test_comment_phase23.py`，全量 26 用例通过（2 跳过）。期间修复了两处既有「库表有列、模型缺失」的 schema 漂移（`msg_event.pushed` / `msg_user_activity.pending_push_count`），使事件通知链路与用户活跃度写入可正常工作。Phase 4 因缺前端仓库无法实施。

---

## 零、已确认的关键决策

| 编号 | 决策项 | 结论 | 落地影响 |
| --- | --- | --- | --- |
| **D0** | 与 Node 端评论系统的关系 | **由本服务替代**。`puppeteer_Bili` 今后只做网关，不再承担评论业务逻辑。**已有的 Node 评论代码与 Postgres 表原样保留、就地冻结**：不删除、不改造、不做数据迁移 | 新前端全部对接 `/api/v1/comment/*`；Node 的 `/api/v1/feedback/comment/*` 停止演进，作为历史遗留只读存在 |
| **D1** | 是否引入 Redis | **不引入**。当前用户量小，直接查 MySQL 足够 | 不做缓存层；性能靠**冗余计数列 + 覆盖索引 + 批量装配**保证；预留后续升级位但本期不实现 |
| **D2** | 图片存储 | **只存 URL，禁止落本地**（服务器空间有限），不接 MinIO | 不提供上传接口；服务端只做「数量 ≤9 + 域名白名单 + URL 长度」校验 |
| **D3** | IP 处理 | **只存原始 IPv4 / IPv6，不做属地解析**；出参**打码**保护隐私；前端**优先显示 IPv6** | 不引入 ip2region 等离线库；新增打码工具函数与管理员明文查看权限 |
| **D4** | 路由前缀 | **`/api/v1/comment/*`**（独立业务域，非 `/api/v1/message` 下） | 便于后续把评论拆成独立微服务 |
| **D5** | 评论 `type` 白名单 | **后端为唯一真相源**。`CommentTypeEnum` 定义全部合法 type；前端只消费、不发明；传入枚举外的值，后端**必须 422 拒绝**（FastAPI `Query` / Pydantic 模型已强制）。**严禁「前端自定义 type、后端再补」的反向耦合** | 前后端协作一律以该枚举为准，新增 type 必须「先改后端枚举 → 同步前端常量 → 再使用」 |

---

## 一、现状盘点（决定复用边界）

| 项 | 现状 | 对本项目的影响 |
| --- | --- | --- |
| 分层约定 | `app/api`（Controller）→ `app/services`（Service，兼数据访问）→ `app/models/db`（表）/ `app/models/schemas`（DTO）；**无独立 Repository 层** | 评论模块沿用，不新增分层 |
| ID 生成 | `app/core/sharding.py` 已有雪花 ID（`msgkey`），并约定 **64 位 ID 一律以字符串出参**（避免 JS `Number.MAX_SAFE_INTEGER` 精度丢失） | `rpid` 复用同一生成器，全链路字符串出参 |
| 枚举落库 | `app/models/db/base.py` 提供 `str_enum_type()`（VARCHAR 存 value）、`int_enum_type()`（INTEGER 存 value）；**禁用 MySQL 原生 ENUM**，有回归测试 `tests/test_phase_e_enums.py` 守约 | 评论所有枚举遵守，并补充对应回归用例 |
| 通知能力 | `EventService.report()` 已实现 like / reply / at 三类提醒的完整链路：消息设置闸门 → 自赞过滤 → `dedup_key` 幂等 → 活跃度分流（实时 / 批量）→ 推送；`SourceTypeEnum` **已含 `COMMENT`**；`EventReportReq.biz_id` 注释即写着「如评论 id」 | **Phase 3 的通知部分 80% 已存在**，评论侧同进程直接调用 Service，不走 HTTP |
| 鉴权 | `RequiredUser` / `AdminUser`（`bili_common.deps.auth`），身份来自网关注入的 `x-bili-*` 头，微服务互信、不校验 JWT；`AuthInfo` 含 `mid / uname / level / role / vip_status`，**无头像字段** | 直接复用；头像等展示字段需靠「用户快照表」补齐 |
| 响应体 | 统一 `StandardResponse[T]{code, data, msg}` | 沿用 |
| 定时任务 | `app/tasks/scheduler.py` 已有 4 个任务，受 `SCHEDULER_ENABLED` 总开关控制 | 评论的热度刷新 / 计数对账追加到同一调度器 |
| MQ | `app/core/broker.py` 单 TOPIC exchange `message_exchange`，按 routing_key 分流独立队列 | 评论新增 3 个队列，与私信 / 推送物理隔离 |
| 前端 | `.gitmodules` 中**无前端仓库**；SDK 由 `openapi.json` 经 `@hey-api/vite-plugin` 生成 | Phase 4 前需先确认并接入前端工程 |

---

## 二、总体架构

参考文章的四层模型（`reply-interface` / `reply-service` / `reply-job` / `reply-admin`），在**单服务内以模块内分层**落地——体量不足以拆进程，但边界按四层预留，未来可平移拆分。

```
app/api/comment.py             ← reply-interface：视图组装、并发编排、弱依赖降级
app/api/comment_admin.py       ← reply-admin：审核、置顶、下架、明文 IP 查看
app/services/comment.py        ← reply-service：发布 / 删除 原子能力
app/services/comment_read.py   ← reply-service：列表读、楼中楼批量装配、热度
app/services/comment_action.py ← reply-service：点赞 / 点踩 幂等
app/services/comment_at.py     ← @ 提及解析、用户搜索
app/services/comment_audit.py  ← 敏感词 / 审核
app/services/user_profile.py   ← 用户快照 upsert 与批量读取
app/consumers/comment.py       ← reply-job：通知派发、楼层发号、异步审核
app/tasks/scheduler.py（扩展）  ← reply-job：热度刷新、计数对账、审核超时兜底
app/models/db/comment.py       ← 表模型
app/models/schemas/comment.py  ← 请求 / 响应 DTO
app/models/enums.py（扩展）     ← 评论相关枚举
app/utils/ip_mask.py           ← IP 提取与打码（D3）
```

### MQ 扩展（`app/core/broker.py`）

| routing_key | queue | 用途 |
| --- | --- | --- |
| `message.comment.notify` | `message_comment_notify_queue` | 回复 / 点赞 / @ → `EventService.report()` |
| `message.comment.audit` | `message_comment_audit_queue` | 异步内容审核 |
| `message.comment.count` | `message_comment_count_queue` | 楼层发号与计数削峰（串行化，防写倾斜） |

### 依赖强弱划分（对齐文章「可用性设计」）

- **强依赖**：MySQL、内容审核同步拦截 —— 失败则发评失败。
- **弱依赖**：通知投递、用户快照刷新、异步 AI 复审 —— 失败只告警，**不阻断发评主流程**。

---

## 三、Phase 1 — 数据模型与基础架构

> 目标：表结构落地 + 分层骨架 + 基础 CRUD 闭环。
> **里程碑：`POST /add` → `GET /main` 跑通，`uv run alembic upgrade head` 可重复执行。**

### 3.1 表设计（`app/models/db/comment.py`，均继承 `TimestampMixin`）

采用文章的**三表分离**（评论区 / 索引 / 正文）：正文大字段独立成表，列表查询只扫索引表，不被 TEXT 拖慢。

#### ① `msg_comment_subject` — 评论区

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | PK auto | |
| `oid` | BIGINT | 业务实体 id（动态 / 文章 / 抽奖 …） |
| `type` | VARCHAR(16) | `CommentTypeEnum`，与 `oid` 共同定位评论区 |
| `up_mid` | BIGINT | 内容作者 mid（决定谁能置顶） |
| `root_count` | INT | 一级评论数 |
| `all_count` | INT | 含楼中楼的总数 |
| `state` | VARCHAR(16) | `normal` / `closed`（关闭评论区） |
| `top_rpid` | BIGINT NULL | 置顶评论 id，全区唯一一条 |

索引：`uq_subject(oid, type)`

#### ② `msg_comment_index` — 评论索引（列表查询主表）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `rpid` | BIGINT PK | 雪花 ID，**出参字符串** |
| `oid` / `type` | BIGINT / VARCHAR(16) | 所属评论区 |
| `mid` | BIGINT | 评论者 |
| `root` | BIGINT | 根评论 rpid，0 = 一级评论 |
| `parent` | BIGINT | 直接父评论 rpid，0 = 一级评论 |
| `dialog` | BIGINT | 同一楼中楼会话串 id（B 站语义，便于「只看该对话」） |
| `floor` | INT | 楼层号，由 MQ 串行发号 |
| `like_count` / `hate_count` | INT | 冗余计数 |
| `rcount` | INT | 子评论数 |
| `hot_score` | DOUBLE | **冗余热度分**，排序直接吃索引 |
| `state` | VARCHAR(16) | `CommentStateEnum` |
| `attr` | INT | 位图：置顶 / 精选 / UP 主赞过 |
| `reply_to_mid` | BIGINT | 被回复者（楼中楼展示「回复 @xxx」） |

索引：
- `idx_hot(oid, type, root, state, hot_score, rpid)` — 热度排序
- `idx_time(oid, type, root, state, rpid)` — 时间排序
- `idx_sub(root, state, rpid)` — 楼中楼批量拉取
- `idx_user(mid, rpid)` — 用户维度（统计 / 管理）

#### ③ `msg_comment_content` — 评论正文

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `rpid` | BIGINT PK | 与索引表 1:1 |
| `message` | TEXT | 正文，`@{mid}` 以占位符存储 |
| `pictures` | JSON | 图片 URL 数组，**≤9 且只存 URL**（D2） |
| `at_mids` | JSON | 被 @ 的 mid 列表（渲染期展开） |
| `emote_meta` | JSON NULL | 表情包元信息 |
| `ip_v4` | VARCHAR(15) NULL | 原始 IPv4，**仅管理员可见明文**（D3） |
| `ip_v6` | VARCHAR(45) NULL | 原始 IPv6，**仅管理员可见明文**（D3） |
| `plat` / `device` | VARCHAR(32) NULL | 来源平台 |

#### ④ `msg_comment_action` — 点赞 / 点踩

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | PK auto | |
| `rpid` / `mid` | BIGINT | |
| `action` | INTEGER | `CommentActionEnum`：0 无 / 1 赞 / 2 踩 |

索引：`uq_action(rpid, mid)` — **重复点赞由数据库唯一约束兜底**

#### ⑤ `msg_comment_at` — @ 提及关系

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | PK auto | |
| `rpid` / `oid` / `type` | | 定位评论 |
| `from_mid` / `at_mid` | BIGINT | 发起者 / 被 @ 者 |
| `notified` | BOOL | 是否已投递通知（补偿用） |

索引：`uq_at(rpid, at_mid)`、`idx_at_mid(at_mid)`

#### ⑥ `msg_user_profile` — 用户展示快照

> **不建用户主表**：用户主数据在网关 Postgres（`TUserInfo` / `TUserDetail`），跨库 JOIN 不可行。
> 本表只是**展示快照**，发评 / 访问时按 `x-bili-*` 头 upsert，过期由定时任务回源刷新。
> 目的：评论列表一次查询即可拿齐昵称头像，杜绝 N+1 与跨服务调用。

| 字段 | 类型 |
| --- | --- |
| `mid` BIGINT（`uq_profile_mid`）、`uname` VARCHAR(64)、`avatar` VARCHAR(512)、`level` INT、`vip_status` VARCHAR(8)、`refreshed_at` DATETIME |

### 3.2 枚举扩展（`app/models/enums.py`）

严格遵守既有落库约定（`str_enum_type` / `int_enum_type`，禁用原生 ENUM）：

- `CommentTypeEnum(StrEnum)`：`dynamic` / `article` / `lottery` / `feedback` / `other`
- `CommentStateEnum(StrEnum)`：`normal` / `auditing` / `rejected` / `hidden` / `deleted`
- `CommentActionEnum(IntEnum)`：`NONE=0` / `LIKE=1` / `HATE=2`
- `CommentSortEnum(StrEnum)`：`hot` / `time`
- `CommentSubjectStateEnum(StrEnum)`：`normal` / `closed`
- `CommentAttrBit`：`TOP=1` / `ESSENCE=2` / `UP_LIKED=4`（位图常量，非枚举列）

### 3.3 IP 提取与打码（D3，`app/utils/ip_mask.py`）

- **提取顺序**：`x-bili-ip`（若网关已注入）→ `X-Forwarded-For` 首段 → `X-Real-IP` → `request.client.host`。
  同一请求通常只会命中 v4 或 v6 之一，按格式判定写入 `ip_v4` 或 `ip_v6`。
- **不做属地转换**，不引入任何 IP 库。
- **出参打码规则**（普通用户视角）：
  - IPv4：`203.0.113.45` → `203.0.*.*`（保留前 2 段）
  - IPv6：`2408:8207:78d2:1a00::1` → `2408:8207:*`（保留前 2 组）
- **响应字段**：`ip_v4_masked` / `ip_v6_masked` 同时返回，**前端优先展示 v6**，无 v6 时回落 v4，两者皆空则不展示。
- **明文**：仅 `AdminUser` 通过 `/api/v1/comment/admin/*` 可见。
- **依赖网关**：需在 nginx / `puppeteer_Bili` 侧确认真实客户端 IP 已透传（一行配置），否则只能拿到网关内网 IP。

### 3.4 Phase 1 任务清单

- [x] **1.1** 新建 `app/models/db/comment.py`（6 张表），在 `app/models/db/__init__.py` 导出（Alembic autogenerate 依赖此导出）
- [x] **1.2** `app/models/enums.py` 扩展评论枚举
- [x] **1.3** 新建 `app/models/schemas/comment.py`：`CommentAddReq` / `CommentDelReq` / `CommentItem` / `CommentListResp` / `CommentSubListResp` / `CommentActionReq` / `CommentCountResp`（含 Phase 2+ 扩展 DTO）
- [x] **1.4** `app/utils/ip_mask.py`：IP 提取 + 打码
- [x] **1.5** `app/services/comment.py` 骨架（发布 / 删除 / 单条读）+ `app/services/user_profile.py`
- [x] **1.6** `app/api/comment.py` 路由，`app/main.py` 注册 `include_router`
- [x] **1.7** 生成并核对 Alembic 迁移：`uv run alembic revision --autogenerate -m "add comment schema"`，**人工检查枚举列是 VARCHAR 而非原生 ENUM**（另含 `floor_seq` 增量迁移）
- [x] **1.8** 测试 `tests/test_comment_crud.py` + 枚举回归用例追加到 `tests/test_phase_e_enums.py`

### 3.5 Phase 1 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/comment/add` | 发表评论（`RequiredUser`） |
| POST | `/api/v1/comment/del` | 删除评论（本人或 `AdminUser` 或内容作者） |
| GET | `/api/v1/comment/main` | 一级评论列表 |
| GET | `/api/v1/comment/detail/{rpid}` | 单条详情 |
| GET | `/api/v1/comment/count` | 评论区计数 |

**验收标准**：迁移可重复执行；CRUD 单测全绿；`rpid` 全部以字符串出参；枚举库内为 value 字面量。

---

## 四、Phase 2 — 核心功能实现

> **里程碑：一条评论从发布到楼中楼展示、点赞的完整体验对齐 B 站。**

### 4.1 评论发布

- [x] **2.1** 事务内完成：写 `index` + `content` → 原子 `UPDATE subject SET all_count = all_count + 1`（一级评论同时 `root_count + 1`）→ 若为楼中楼再 `UPDATE index SET rcount = rcount + 1 WHERE rpid = root`
- [x] **2.2** 图片校验（D2）：数量 ≤9、每个 URL ≤512 字符、**域名白名单**（配置项 `comment_picture_domains`），不下载不转存
- [x] **2.3** @ 解析：正文中的 `@{mid}` 占位符提取 → 落 `msg_comment_at`（`uq(rpid, at_mid)` 幂等），单条上限 10 个
- [x] **2.4** 楼层号 `floor`：采用 DB 原子 `floor_seq + 1` 回读发号（等价串行、更简单且正确；`message.comment.count` 队列仍保留为预留削峰通道）
- [x] **2.5** IP 写入（D3）+ 用户快照 upsert（弱依赖，失败不影响发评）
- [x] **2.6** 防刷：同用户同内容 10s 内 ≤3 次（进程内近似限流），超限返回业务错误码

### 4.2 评论列表读

- [x] **2.7** 排序：`sort=hot|time`。**热度必须走冗余列 `hot_score`**，禁止 `ORDER BY` 表达式（会导致索引失效）
- [x] **2.8** 置顶：`subject.top_rpid` 单独查出后拼到列表首位，主查询排除该 rpid，避免分页错位
- [x] **2.9** 用户信息装配：收集本页 `mid` 集合后单次 `WHERE mid IN (...)` 查 `msg_user_profile`，**杜绝 N+1**
- [x] **2.10** 当前用户点赞态：单次 `WHERE rpid IN (...) AND mid = ?` 查 `msg_comment_action`
- [x] **2.11** 出参组装：九宫格图片数组、计数、`ip_*_masked`、`attr` 解析为布尔标记

### 4.3 楼中楼（子评论）

- [x] **2.12** 一级列表内嵌预览 **3 条**：拿到本页 `root_ids` 后**单次批量查询** `WHERE root IN (...)`，应用层按 root 分组截断——查询次数与一级评论条数**无关**
- [x] **2.13** 展开接口 `GET /reply?root=&page_num=&page_size=`，支持收起 / 加载更多
- [x] **2.14** 楼中楼展示「回复 @xxx」：用 `reply_to_mid` 装配

### 4.4 点赞 / 点踩

- [x] **2.15** `INSERT ... ON DUPLICATE KEY UPDATE` + `uq(rpid, mid)` 保证幂等，重复点赞不重复计数
- [x] **2.16** 状态翻转（赞 → 踩 / 取消）在同一事务内修正两个冗余计数
- [x] **2.17** 同步更新 `hot_score`（增量式）

### 4.5 Phase 2 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/comment/main` | 一级列表（`oid`/`type`/`sort`/`page_num`/`page_size`，内嵌 3 条子评论） |
| GET | `/api/v1/comment/reply` | 楼中楼展开分页 |
| POST | `/api/v1/comment/action` | 点赞 / 点踩 / 取消 |

**验收标准**：9 图上限与白名单生效；并发 100 次点赞计数精确无偏差；楼中楼固定 SQL 次数（一级列表整体 ≤4 次查询）。

---

## 五、Phase 3 — 互动与通知

> **最大复用点：`EventService.report()` 已具备闸门 / 幂等 / 活跃度分流 / 推送，评论侧只需组装 `EventReportReq`。**

- [x] **3.1 @ 用户搜索**：`GET /api/v1/comment/at/search?keyword=`，查 `msg_user_profile.uname` 前缀，返回 ≤10 条（`mid` / `uname` / `avatar`）
- [x] **3.2 @ 存储与渲染**：正文存 `@{mid}` 占位符（昵称变更不失效），出参时用快照展开为 `{mid, uname}`，前端渲染成链接
- [x] **3.3 通知投递**（异步，弱依赖）：
  - 回复他人 → `event_type=reply`
  - 被点赞 → `event_type=like`
  - 被 @ → `event_type=at`
  - 统一 `source_type=SourceTypeEnum.COMMENT`、`source_id=oid`、**`biz_id=rpid`**
    （`biz_id` 保证：多条回复各记一条；反复点赞取消只记一条）
  - 通知走**独立会话**投递，失败只告警、绝不污染发评/点赞主事务
- [x] **3.4 排序切换**：`hot_score = like_count - hate_count * 1.5 + rcount * 0.5 + 时间衰减`；写时增量更新 + 定时任务批量重算（`comment_hot_score_job`）
- [x] **3.5 置顶**：内容作者（`subject.up_mid`）或 `AdminUser` 可置顶；写 `subject.top_rpid` + `index.attr |= TOP`，同评论区互斥单条；取消置顶同步清位
- [x] **3.6 新增 MQ 消费者** `app/consumers/comment.py`（`handle_comment_notify/audit/count`），`AckPolicy.MANUAL`，幂等由 `dedup_key` / `uq_*` 在数据库层兜底；当前作为预留校验通道（无生产者接入）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/comment/at/search` | @ 用户搜索 |
| POST | `/api/v1/comment/top` | 置顶 / 取消置顶 |

**验收标准**：被回复 / 点赞 / @ 后，`GET /api/v1/message/event/aggregate` 能看到对应聚合卡片；重复上报返回 `duplicated=true`；通知失败不影响发评成功。

---

## 六、Phase 4 — 前端组件开发

> **⛔ 状态：阻塞（CONFIRMED 2026-08-03）。** 当前 `.gitmodules` 中**无前端仓库**，无法落地任何 Vue/Tailwind 组件；且本仓库规则强制「主题/组件必须落在前端工程」，后端服务侧无可实施入口。需先确认并接入前端工程（workspace）后才能启动 4.1–4.4。后端 `openapi.json` 已就绪，可作为 SDK 生成源。

### 技术约束（项目规则，强制）

- Vue + **Tailwind 原子类**；**禁止 `<style>` 块、禁止 `:style` 内联样式**
- 主题变量统一定义在 `src/assets/theme.css`，模板中**只用语义化 Tailwind class**（如 `text-info-light-3`、`bg-primary`）；**禁止手写 `var()` / `text-[var(--x)]`**
- 优先 Element Plus 组件（`el-text` 代替 `p`、`el-button` 代替 `button`）；**尺寸只用 `large` / `default`，禁用 `small`**
- 每个功能元素必须带业务语义 class（BEM，如 `comment-card__avatar`），禁止纯样式类作为唯一标识
- API 调用一律使用 `openapi.json` 经 `@hey-api/vite-plugin` 生成的 SDK，**不手写请求**

### 评论 `type` 白名单协作规范（强制，对应决策 D5）

> **核心原则：后端先定义，前端照着写，后端对非白名单一律报错。**
> 评论区的 `type` 是定位评论区的业务维度（`oid` + `type` 唯一确定一个评论区），必须由后端枚举收口，绝不允许前端随手传任意字符串、再让后端去兼容。

**① 后端（唯一真相源，已落地）**

- `app/models/enums.py` 的 `CommentTypeEnum(StrEnum)` 是全部合法 type 的白名单：
  `dynamic` / `article` / `lottery` / `feedback` / `other`。
- 所有入口强制校验，传入枚举外的值后端**直接 422 拒绝**：
  - Query 接口（`/main`、`/count`、`/reply`、`/top`）：`type: CommentTypeEnum = Query(...)`。
  - Body 接口（`/add`、`/top`）：`CommentAddReq.type` / `CommentTopReq.type` 为 `CommentTypeEnum`（Pydantic 校验）。
- 若某天需要开放新类型，第一步永远是**改后端枚举**并补充回归用例，而不是先在前端用起来。

**② 前端（只消费，从编译期杜绝非法值）**

- 后端枚举的前端镜像集中在 `src/api/lottery_comment.ts`：
  - 导出常量对象 `COMMENT_TYPE`（成员与 `CommentTypeEnum` 一一对应）；
  - 导出联合类型 `CommentType = (typeof COMMENT_TYPE)[keyof typeof COMMENT_TYPE]`。
- 所有涉及 type 的地方必须引用 `COMMENT_TYPE.*`，**禁止硬编码裸字符串**：
  - API 方法（`listMain` / `listReply` / `add` …）的 `type` 参数类型一律为 `CommentType`；
  - 组件 prop（如 `LotteryCommentSection` 的 `type`）类型同样为 `CommentType`；
  - 业务常量（如 `LOTTERY_COMMENT_TYPE`）通过 `COMMENT_TYPE.LOTTERY` 引用，不再写 `'lottery'`。
- 传入一个不在 `COMMENT_TYPE` 里的字符串，TypeScript 编译期即报错，从源头避免打到后端的 422。

**③ 新增 / 修改 type 的标准流程（必须按顺序）**

1. **后端**：在 `CommentTypeEnum` 增加成员，并补 `tests/test_phase_e_enums.py` 类回归用例，确认 `uv run pytest` 通过、迁移能正确落 VARCHAR 而非原生 ENUM。
2. **前端**：同步把新成员加入 `COMMENT_TYPE`，使联合类型 `CommentType` 自动包含它。
3. **使用**：业务侧再通过 `COMMENT_TYPE.新成员` 引用。

> 反例（禁止）：前端先写 `type: 'my_new_thing'` 调接口，再回头求后端「帮我加个 `my_new_thing`」——这会让白名单形同虚设，应予以拒绝。

### 组件清单

- [ ] **4.1 `CommentEditor`**：自适应高度、表情面板、图片 URL 预览九宫格（排序 / 删除，**无本地上传**）、`@` 触发用户搜索浮层、提交按钮
- [ ] **4.2 `CommentList`**：排序切换 Tab、上拉加载更多、长列表虚拟滚动、骨架屏与空态
- [ ] **4.3 `CommentSubList`**：嵌套 3 条预览、「共 N 条回复」展开、收起
- [ ] **4.4 `CommentCard`**：用户信息（头像 / 昵称 / 等级）、富文本渲染（表情 / 图片 / @ 链接）、操作条（点赞 / 点踩 / 回复 / 举报 / 删除）、置顶标签、**IP 展示（优先 v6 打码值）**

**验收标准**：1000 条评论滚动流畅；无 `<style>` 块；无硬编码色值；组件均带业务 class。

---

## 七、Phase 5 — 优化与完善

### 5.1 评论审核

- [x] **5.1** DFA Trie 敏感词匹配（词库进程内热加载，`reload_words()`），**同步拦截**：命中高危直接 `rejected`，疑似置 `auditing`（当前对外不可见，作者可见性待前端配合）
- [ ] **5.2** 可选：接 compose 内已有的 `llama_cpp` 做异步 AI 复审（弱依赖，超时兜底放行 + 告警）— *本轮未实施（可选）*
- [x] **5.3** 管理端 `/api/v1/comment/admin/audit`：人工审核队列、通过 / 驳回、下架、明文 IP 查看；`/admin/stats` 全局统计

### 5.2 性能（D1 约束：无 Redis）

- [x] **5.4** 全部计数走冗余列，**任何列表接口禁止 `COUNT(*)` 扫描**（管理端低频统计除外）
- [ ] **5.5** `EXPLAIN` 逐条验证 `idx_hot` / `idx_time` / `idx_sub` 覆盖，杜绝 filesort — *待补验证步骤*
- [ ] **5.6** 深翻页改**游标分页**（`rpid` 游标），避免大 offset — *本期仍为 offset 分页，待补*
- [x] **5.7** 批量装配复查：单次列表请求 SQL 次数固定（主列表 ≤4 次），不随数据量增长

> 备注：本期**不做任何缓存层**。若后续 QPS 增长导致 MySQL 压力显现，再评估「进程内 TTL 缓存」或引入 Redis，作为独立议题。

### 5.3 数据统计

- [x] **5.8** 评论总数、日新增、用户评论排行；`CommentAdminService.get_stats` 输出，前端可经 SDK 调用

### 5.4 兜底与异常

- [x] **5.9** 空数据态、超长内容截断、父评论被删后的楼中楼孤儿处理（软删占位「该评论已删除」）；弱依赖（通知/快照）失败只告警不阻断
- [x] **5.10** **计数对账定时任务** `comment_reconcile_job`：定期校准 `root_count` / `all_count` / `rcount` / `like_count`（仅 NORMAL 可见态计入，与列表口径一致）
- [ ] **5.11** 前端路由切换：网关 `/api/v1/comment/*` 反代到 `be-message-service`；Node 端旧评论路由保持原样不动（D0）— *需运维/网关配合，超出后端代码范围*

---

## 八、里程碑与工作量估算

| 阶段 | 交付 | 预估 | 依赖 |
| --- | --- | --- | --- |
| Phase 1 | 表 + 骨架 + CRUD | 2–3 天 | 无（决策已定） |
| Phase 2 | 发布 / 列表 / 楼中楼 / 点赞 | 3–4 天 | Phase 1 |
| Phase 3 | @ / 通知 / 排序 / 置顶 | 2 天 | Phase 2 |
| Phase 4 | 前端 4 组件 | 4–5 天 | **前端仓库接入** |
| Phase 5 | 审核 / 性能 / 统计 / 兜底 | 3–4 天 | Phase 2–3 |

---

## 九、风险登记

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 新旧评论数据割裂（D0 不迁移） | 旧 Node 评论与新评论不互通 | 已确认可接受：旧数据就地冻结只读，新业务只用新系统；若后续需要合并再单独立项 |
| 无缓存下的热点读（D1） | 热门内容集中访问时 MySQL 压力上升 | 冗余计数 + 覆盖索引 + 游标分页；建立慢查询监控，超阈值再评估缓存 |
| 图片 URL 外链失效 / 盗链（D2） | 图片 404、被刷外链 | 域名白名单 + 前端加载失败占位图 |
| 真实客户端 IP 未透传（D3） | 只能拿到网关内网 IP，属地信息无意义 | Phase 1 先在网关侧验证透传链路，未透传则该字段留空不展示 |
| `rpid` 64 位精度 | 前端串号 | 全链路字符串出参（沿用 `msgkey` 既有先例） |
| 计数不准（写倾斜） | 用户可感知，属舆论风险 | MQ 串行发号 + 计数对账定时任务 |
| 楼中楼 N+1 | 列表接口随数据量劣化 | 批量查询 + 应用层分组，单测断言 SQL 次数 |

---

## 十、开发与验证命令

```bash
cd /home/minato/BilibiliExplosion/be-message-service

# 环境
uv sync

# 生成 / 应用迁移
uv run alembic revision --autogenerate -m "add comment schema"
uv run alembic upgrade head

# 本地启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 18739

# 测试（本机直连容器映射的 MySQL）
MYSQL_MESSAGE_URL='mysql+aiomysql://root:<pwd>@127.0.0.1:10000/BiliMessageDB?charset=utf8mb4' \
  uv run pytest -q

# 接口文档
# http://localhost:18739/docs
```

---

**下一步**：Phase 1 编码启动。首个提交范围为 §3.4 中的 1.1 – 1.8。
