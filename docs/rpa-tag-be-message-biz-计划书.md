# RPA 资源标签（rpa_tag）biz 化改造计划书

> 状态：**决策已确认，实施中** · 范围：be-message / RPA-Browser / bili-common / 前端
> 目标：把 RPA 的「资源标签」改造成与 `rpa_action / rpa_workflow / rpa_plugin / rpa_browser`
> 一致的 biz 对象，交由 be-message 统一管理，审核复用 be-message 的审核栈（模式上对齐 dynamic）。

---

## 1. 背景与现状

当前 RPA 标签（`app/admin/rpa/tag` 页面）CRUD 全部是管理员专用：

- [tag_router.py](RPA-Browser/app/controller/v1/admin/tag_router.py)：`/tag/create|update|delete|attach|detach|list|list-by-target`，除 `list` 外均为 `require_admin`。
- 数据模型 [ResourceTag / ResourceTagRel](RPA-Browser/app/models/database/admin/models.py#L52-L78)：存 `rpa_tag` / `rpa_tag_rel`（RPA 侧 MySQL），关联字段 `target_type` / `target_id`。
- 前端 [TagAdmin.vue](Vue3FrontEndDemoExercise/src/views/rpa-browser/admin/TagAdmin.vue) 直接调 RPA 的 `/api/admin/rpa/tag/*`。

已和产品对齐的下放方向：
- **创建 + 打标都下放**给登录用户；
- **共享池 + 后端审核**（审核用 be-message 那套）。
- 用户明确要求：**把 tag 设成一个 biz 对象，与 RPA 其它内容一致，通过 be-message 来管理。**

### 已有的同类基础设施（复用，不重复造轮子）

| 能力 | 现有实现 | 说明 |
|---|---|---|
| biz 类型枚举 | `InteractionBizTypeEnum`（[interaction.py](bili-common/bili_common/models/interaction.py)）：`RPA_ACTION=3, RPA_WORKFLOW=4, RPA_BROWSER=5, RPA_PLUGIN=6` | 无 `tag`，需新增 `RPA_TAG` |
| be-message 统一资源入口 | `GenericResourceBiz`（[generic_biz.py](be-message-service/app/services/interaction_actions/common/generic_biz.py#L34-L68)）：经 `rpa_rpc_client.get_resource_detail(biz_type, biz_id)` 拉详情并折叠为 `InteractionResource` | tag 接入此链路 |
| be-message 通用审核 API | `POST /api/v1/audit/approve` / `/reject`（[audit.py](be-message-service/app/api/audit.py#L39-L78)）→ 按 `bizType+bizId` 调 biz 的 `audit_approve/audit_reject` | tag 审核复用 |
| RPA 回调（RPC 服务端） | `rpa_rpc_client` ↔ RPA `rpc_server.py`：`get_resource_detail / hide_resource / review_resource` | 需为 tag 增加对应处理 |
| 审核状态机 | dynamic：`auditStatus: auditing/normal/rejected`，`pubTime` 审核通过前为 NULL | tag 对齐 |

---

## 2. 目标架构

`rpa_tag` 作为一个新的 biz 对象，纳入 be-message 的「资源管理 + 审核」闭环：

```
用户 / 管理员
   │  tag 相关请求（创建/打标/审核）都走 be-message API
   ▼
be-message（管理入口 + 审核栈）
   │  get_resource_detail / review_resource（RPC）
   ▼
RPA-Browser（存储 + 资源详情 + 审核落地）
   └── rpa_tag 表（+ auditStatus/pubTime）
```

### 审核状态机（对齐 dynamic / RPA 其它内容）
- 用户 `tag/create` → `rpa_tag.auditStatus = auditing`，`pubTime = NULL`，不入前台可用列表。
- be-message `/audit/approve`（bizType=rpa_tag）→ RPA 置 `auditStatus = normal`、`pubTime = now` → 标签对外可用。
- `/audit/reject` → 置 `rejected`（隐藏）；可配合事件通知（复用 `EventSubType=AUDIT_REJECT` 语义，先对齐 dynamic 的做法）。
- 打标 `tag/attach`：仅允许关联 `normal` 标签；打标动作本身即时生效（受控词表已由标签审核把关）。

---

## 3. 改动清单（按模块）

### 3.1 bili-common
- [interaction.py](bili-common/bili_common/models/interaction.py)：`InteractionBizTypeEnum` 新增 **`RPA_TAG = 14`**（实体资源 1~8、审核域 9~13 已占用，故用 14）`to_text='rpa_tag'`，已落地。

### 3.2 be-message-service（管理入口）
- tag 资源 biz：新增/扩展现有 RPA 资源 biz（如 `TagResourceBiz`，或 `GenericResourceBiz` 支持 `rpa_tag`）：
  - `get_resource_detail`：经 RPC 拉 RPA 标签详情，折叠为 `InteractionResource`。
  - `audit_approve / audit_reject`：`bizType=rpa_tag` 时经 RPC `review_resource` 落地到 RPA；仅允许对 `rpa_tag`。
- 用户侧接口（下放创建/打标）：
  - `POST /api/v1/rpa_tag/create`：登录用户提交标签名 → 落 `auditing`。
  - `POST /api/v1/rpa_tag/attach` / `detach`：登录用户对资源关联标签（仅 `normal` 标签）。
  - `POST /api/v1/rpa_tag/list`：普通用户只看 `normal`；管理端可看全状态 + 筛选。
- 审核链已验证可复用：`/api/v1/audit/approve` 与 `/reject` 无需新增路由，仅需 tag biz 支持 `rpa_tag`。
- 必要的状态/统计表（若沿用 `TInteractionStat`）：确认 tag 是否需要在 `TInteractionStat` 有对应记录（标签本身一般无点赞/举报，可能不落统计，仅走审核 + 资源详情）。

### 3.3 RPA-Browser（存储 + 详情 + 审核落地）
- 模型 [ResourceTag](RPA-Browser/app/models/database/admin/models.py)：新增 `audit_status`（`auditing/normal/rejected`）与 `pub_time`（可空）字段；RPA alembic 迁移。
- RPC 服务端 [rpc_server.py](RPA-Browser/app/services/mq/rpc_server.py)：
  - `get_resource_detail`：支持 `rpa_tag`（按 tag.id 查询详情）。
  - `review_resource`：支持 `rpa_tag`，落地 `audit_status` / `pub_time`。
  - 按需新增 `create_tag` / `list_tags` 存储回调（若创建/打标落在 RPA 存储）。
- 收敛/移除：管理端专用 `/tag/create|update|delete|attach` 旧的 `require_admin` 逻辑，若这些职责迁到 be-message，则 RPA 侧删除对应 admin 接口（改由 be-message 编排 + RPC 回调），`list` 保留给 be-message 拉取。

### 3.4 数据库 / 迁移
- be-message 主库（alembic）：若 tag 需在 be-message 侧建立资源/审核索引表，则加迁移。
- RPA 库（alembic_pptr 之外、RPA 自己的 mysql）：`rpa_tag` 加 `audit_status` / `pub_time`（可自由改）。

### 3.5 前端（Vue3FrontEndDemoExercise）
- [TagAdmin.vue](Vue3FrontEndDemoExercise/src/views/rpa-browser/admin/TagAdmin.vue) 改写为 be-message 管理端结构（对齐 moment-audit / admin 审核）：
  - `AdminAuditTabs + useAuditTabCache + el-table-v2 + LoadingWrap/EmptyState/PaginationBar`；
  - 增加「待审核 / 已通过 / 已驳回」筛选维度；
  - 待审核行提供「通过 / 驳回」操作（调 be-message `/audit/approve|reject`）。
- 若权限沿用 `hasRpaAdminPerm` / `hasReportAdminPerm`（messageAdmin.ts），保持一致。
- hey-api SDK：新增 `rpa_tag` 相关接口后重新生成（按 `前端hey-api.md` 规则由用户手动触发）。

---

## 4. 实施顺序（分步，逐步改）

阶段 0：**写计划书（本文件）**并评审 —— ✅ 完成
阶段 1：**bili-common** 加 `RPA_TAG=14` 枚举 —— ✅ 完成
阶段 2：**RPA 存储层** —— ✅ 完成
  - `ResourceTag` 加 `audit_status`/`pub_time` + 迁移 `9c3d4e5f6a7b_rpa_tag_audit.py`；
  - RPC `get_resource_detail` / `review_resource` 支持 `rpa_tag`；
  - 原 `/tag/create|attach|detach` 旧用户接口待撤（阶段4 迁移）。
阶段 3：**be-message biz**：`RpaTagBiz` 接入 `GenericResourceBiz`，`_rpa_review` 允许 `rpa_tag`，打通 `/audit/approve|reject` —— ✅ 完成
阶段 4：**be-message API + RPA RPC 回调** —— ✅ 完成（后端）
  - bili-common RPC 契约新增 `create_tag`/`attach_tag`/`detach_tag`/`list_tags`/`list_tags_by_target`；
  - RPA `rpc_server` 加对应 5 个回调 handler（落 `rpa_tag`/`rpa_tag_rel`）；
  - be-message `rpa_rpc_client` 加 5 个调用方法；
  - be-message 新增用户侧 `POST /api/v1/rpa_tag/create|attach|detach|list|list-by-target`（`rpa_tag.py`）；
  - RPA `tag_router.py` 撤掉用户 create/attach/detach/list/list-by-target，仅保留管理员 update/delete。
阶段 5：**前端 TagAdmin.vue** 重构为审核式管理页 + 用户侧打标入口。
阶段 6：**联调 + SDK 重生成 + 验证**。

---

## 5. 待确认决策（实现前敲定）—— 已全部确认

> 以下决策已与产品对齐并敲定，作为实施契约，不再变更。

1. **创建/打标的落库节点**：✅ **be-message 编排 + RPA 存储（走 RPC）**（与其他 RPA 内容一致）。
   - 用户侧 `/api/v1/rpa_tag/*` 由 be-message 负责，经 RPC 回调 RPA 落 `rpa_tag` / `rpa_tag_rel` 表。
   - RPA 侧原来对登录用户开放的 `/tag/create|attach|detach` 用户接口**撤掉**，RPA 改提供 `create_tag` / `attach_tag` / `detach_tag` / `list_tags` 等 RPC 存储回调（阶段4）。
2. **打标（attach/tag 关联）**：✅ **一并迁到 be-message**，RPA 只做 `list_by_target` 数据源（经 RPC）。
3. **驳回通知**：✅ **复用 be-message 事件通知（`AUDIT_REJECT`）给标签提交者（created_by）**，对齐 dynamic。
4. **tag 是否进 `TInteractionStat`**：✅ **不进**，标签本身无点赞/举报，仅走审核 + 资源详情。

## 6. 风险
- 跨服务链路长（前端 → be-message → RPC → RPA），需在阶段 6 统一联调。
- RPA 未上线、库可自由改，但 be-message 是否已上线需确认，避免动其存量表结构。
- 改动面大，禁止一次提交；按阶段合入并逐步验证。

（本计划书待评审后进入阶段 1 实施。）