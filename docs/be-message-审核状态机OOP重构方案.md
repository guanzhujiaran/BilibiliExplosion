# be-message 审核状态机 OOP 重构方案（定稿 v2）

> 状态：定稿（含全部评审决策）
> 适用范围：`be-message-service`
> 目标读者：负责 be-message 审核/互动/治理的开发者

> ⚠️ 依据项目 hook 规则（.codebuddy/rules/项目改动前hook.mdc）：**新增/修改功能必须先改计划书再改代码**。本文档即本次功能的设计定稿；落地前需将本方案并入权威计划书 `docs/be-message-统一计划书.md` 相关章节。

---

## 1. 背景与问题

"审核"逻辑复杂，源于**状态表达与流转缺乏统一约束**，而非单点逻辑难写：

| # | 病灶 | 表现 | 现状证据 |
|---|---|---|---|
| 1 | 同"审核态"多套枚举并存且**数值错位** | `MomentAuditStatusEnum`(动态/话题 AUDITING=1)、`CommentStateEnum`/`DmAuditStateEnum`(评论/私信 NORMAL=1)、`AvatarAuditStatusEnum`/`FolderCoverAuditStatusEnum`——同语义不同 int | `enums.py` |
| 2 | `TResourceFeed.auditStatus` 裸字符串 | 与主表 int 枚举两套表达并存，手动同步易漂移 | `resource_feed_tbl.py:56`；`_sync_resource_feed(audit_status="normal")` |
| 3 | 状态迁移无"允许表" | A→B 是否合法靠各方法手写判断，散落多处 | `DynamicBiz`、各专项 `approve/reject` |
| 4 | 从状态推副作用的逻辑分散 | Feed 同步 / FORWARD 计数 ±1 / 通知 / 可否入 Feed 多处各判一次 | `dynamic/biz.py`、`_load_interactable` |
| 5 | 审核流水表 `TResourceAuditLog` 只给动态用 | 评论/私信/头像/封面不写，审计口径不一、管理端无法统一查询 | `resource_tbl.py:94`；`moment_audit.py` 仅 bizType=DYNAMIC |

---

## 2. 目标与方向（评审定稿）

**目标**：把动态这套成熟的"资源化 + 统一审核流水"模式，复制推广到评论/私信/头像/封面等所有审核对象，做成类似动态的实现。业务实体各自保留表，不合并。

1. **业务实体表保留各自结构**（`TMoment`/`CommentIndex`/`DmMessageIndex`/`TUserAvatarAudit`/`TFolderCoverAudit`），不做物理合并。
2. **统一"状态迁移 + 副作用"骨架**：每个审核对象走同一个 `StateMachine` 模板 + 显式迁移表 + `on_enter` 钩子（对齐动态实现方式）。
3. **统一状态枚举表达**：一套 `ResourceAuditStatusEnum`（含单据语义，`NORMAL=1` 基准），各列值口径一致，杜绝数值错位。
4. **统一审核流水落库**：所有资源的审核流转都写现成的 `TResourceAuditLog`（`bizType+bizId` 通用定位），管理端统一查询。评论/私信/头像/封面补齐审核日志写入。
5. **资源定位遵循 `bizType+bizId` 唯一原则**（举报资源唯一性规则），不引入额外二级分流字段。

---

## 3. 建模边界（三种对象本质不同，不并表）

| 类型 | 对象 | 数据形态 | 状态在哪 |
|---|---|---|---|
| ① 业务实体·行内状态列 | 动态 `TMoment`、话题 `TMomentTopic`、评论 `CommentIndex`、私信 `DmMessageIndex` | 状态列写在**业务实体行**上，与业务内容同事务 | `auditStatus`/`state`/`audit_state` |
| ② 申请单据 | 头像 `TUserAvatarAudit`、封面 `TFolderCoverAudit` | 独立行，每用户多条历史，记录"换什么" | 申请单上的 `auditStatus` |
| ③ 审核流水/记录 | `TResourceAuditLog`（现成） | append-only 审计日志，`(bizType,bizId)` 定位 | `fromStatus/toStatus/actionType` |

- ① 的审核态是**实体行上的一列**，跟实体读写强耦合 → **不能抽走**，否则读实体要 join、写要双表。
- ② 生来独立。
- ③ 是**该统一的"记录"表**——目标是把所有资源的流转都写进来。

> **"合并统一表"的正确对象是 ③ 审核流水，不是 ①② 业务实体。** 业务内容列各不相同（动态 JSON 富文本 / 评论树形 / 私信会话 / 头像新旧图），无公共列可合并，硬并只会退化成全 JSON 宽表、丢掉类型安全。

---

## 4. 统一语义与落库枚举

### 4.1 语义动作（流转的动词）

```python
class ModerationAction(str, Enum):
    APPROVE = "approve"    # 审核通过 / 单据通过
    REJECT  = "reject"     # 审核驳回 / 单据驳回
    HIDE    = "hide"       # 下架（实体类）
    # 评审：无申诉恢复场景，不引入 RESTORE；后续需要再加 TRANSITIONS
```

### 4.2 统一落库枚举（`NORMAL=1` 基准，实体类与单据可共同表达，DELETED 纳入）

```python
class ResourceAuditStatusEnum(IntEnum):
    NORMAL   = 1   # 通过/公开/已通过（可入 Feed、可互动；单据=已批准）
    AUDITING = 2   # 实体待审（先发后审）
    PENDING  = 2   # 单据待审（与 AUDITING 同位，语义按表区分；见 §5 取舍）
    REJECTED = 3   # 驳回（实体/单据）
    HIDDEN   = 4   # 下架（实体类）
    DELETED  = 5   # 软删（当前仅评论；动态软删走独立 deletedAt）
```

> ⚠️ **数值错位迁移**：动态/话题旧 `AUDITING=1`，评论/私信旧 `NORMAL=1`。统一为 `NORMAL=1` 基准时，迁移须按语义映射，不能只改类型（详见 §6 Alembic）。

---

## 5. ⚠️ 枚举统一的一个待决取舍（PENDING vs AUDITING 同值）

把实体待审（AUDITING=2）和单据待审（PENDING）都放同一枚举且数值相同，是一种**妥协**：它让实体与单据共用一套枚举列，但靠 `biz_type` 语义区分。两种选法：

- **方案甲（推荐）**：`ResourceAuditStatusEnum` 只保留一套 `AUDITING`（值 2）表示"待审"，单据在语义上把"待审"也映射为 `AUDITING`，`PENDING` 仅作为单据类型的**语义别名/注释**，不单设成员。落库列统一用同一枚举，最干净。
- **方案乙**：同时保留 `PENDING` 成员但数值必须与 `AUDITING` 相同（否则同类不同值），读取端统一按 `to_text/语义` 解释。

> 推荐方案甲：一套枚举列 + 单据/实体靠 `biz_type` 区分"待审"语义，避免一套列里两个成员同值造成混乱。此点已按方案甲在本文档落定，若你有异议请提出。

---

## 6. 统一列改造（维度：实体类状态列 → 统一枚举；Feed 字符串 → 枚举）

| 表 | 现列/类型 | 统一后 | 备注 |
|---|---|---|---|
| `TMoment` | `auditStatus` `MomentAuditStatusEnum` | `auditStatus` `ResourceAuditStatusEnum` | 语义映射迁移 |
| `TMomentTopic` | `auditStatus` `MomentTopicAuditStatusEnum` | 同上 | 话题无 HIDDEN/DELETED |
| `CommentIndex` | `state` `CommentStateEnum` | `auditStatus` `ResourceAuditStatusEnum` | 改列名；DELETED 并入 |
| `DmMessageIndex` | `audit_state` `DmAuditStateEnum` | `auditStatus` `ResourceAuditStatusEnum` | 并入 |
| `TResourceFeed` | `auditStatus` **裸字符串** | `auditStatus` int 枚举 | 字符串 `"normal"→1` 等；适配索引 |
| `TUserAvatarAudit`/`TFolderCoverAudit` | `auditStatus` `*AuditStatusEnum` | 同一 `ResourceAuditStatusEnum` | 单据表，语义映射 |

**Alembic 迁移要点（必须语义映射）**：先加新枚举列 → Python 数据迁移按 §4.2 语义改写 → 删旧列 → 断言脚本验证无"值错位"脏数据。

---

## 7. 统一状态机骨架（对齐动态实现，模板方法）

> 所有审核对象（含评论/私信/头像/封面）复用同一 `AuditStateMachine`；子类只声明三件事：`TRANSITIONS`、`native<->语义` 映射、`on_enter` 副作用。这就是"做成类似动态的实现"。

```python
# app/services/moderation/state_machine.py
@dataclass(frozen=True)
class Transition:
    from_state: ResourceAuditStatusEnum   # 或语义态
    action: ModerationAction
    to_state: ResourceAuditStatusEnum

class AuditStateMachine(ABC):
    TRANSITIONS: tuple[Transition, ...] = ()
    state_attr: str = "auditStatus"

    @abstractmethod
    def to_native(self, state): ...
    @abstractmethod
    def native_state_of(self, row): ...

    async def on_enter(self, session, row, new_state, *, action, actor_mid, reason, remark) -> None:
        """副作用钩子（默认空）：Feed 同步 / FORWARD 计数 / 通知 / 写公开头像等差异显式化。"""

    async def transition(self, session, row, *, action, actor_mid, reason=None, remark=None):
        cur = self.native_state_of(row)
        rule = self._rule(cur, action)
        if rule is None:
            raise StateTransitionError(cur, action)      # 非法流转唯一拦截点
        setattr(row, self.state_attr, self.to_native(rule.to_state))
        await self.on_enter(session, row, rule.to_state, action=action,
                            actor_mid=actor_mid, reason=reason, remark=remark)
        await self._write_audit_log(session, row, cur, rule.to_state, action,
                                    actor_mid, reason, remark)   # 统一写 TResourceAuditLog
        return rule.to_state
```

---

## 8. 统一审核流水落库（`TResourceAuditLog` 推广）

`transition()` 内 `_write_audit_log` 统一写 `TResourceAuditLog`（现成表，`resource_tbl.py:94`，`(bizType,bizId)` 定位，字段 `fromStatus/toStatus/actionType/operatorRole/rejectReason/remark/clientIp/userAgent`）。

- 动态已写（`moment_audit._build_audit_log`）→ 收编进状态机。
- **评论/私信/头像/封面补齐**：审核/处置动作一律写本表，`bizType` 用对应 `InteractionBizTypeEnum`（评论=comment，头像/封面若尚未有枚举成员则按举报资源唯一性规则追加/登记）。
- 管理端待审/已办/流水统一查询本表。

> 遵守"举报资源唯一性"：可被审核/定位的资源统一用 `InteractionBizTypeEnum` 的 int 值做 `bizType`，不另造来源枚举。

---

## 9. 多审核环节编排（评审定稿：一个资源可有多个审核流程）

### 9.1 核心模型：主状态 + 多环节子状态

一个资源在生命周期内会经历**多个顺序/并列的审核环节**（如动态 = ① 自动文本审核 → ② 人工内容审核 → ③ 举报处置；头像 = ① URL/图片合规审核 等）。每环节是**一个独立 `AuditStateMachine`**，各自声明 `TRANSITIONS` / 规则 / 副作用。

资源"当前能不能公开/互动"（可见性）由**一个主状态**决定，主状态由各环节共同推出：

```
资源主表（TMoment/CommentIndex/...）
  ├── auditStatus        # ★ 主状态：决定当前可见性（NORMAL/AUDITING/REJECTED/HIDDEN/DELETED）
  └── 环节自身状态        # 不冗余在主表；落 TResourceAuditLog / 举报单 / 各环节表
        环节1 自动文本审核   -> TResourceAuditLog(actionType, from/to)
        环节2 人工内容审核   -> TResourceAuditLog + 主表 auditStatus 联动
        环节3 举报处置       -> TResourceReport（举报单独立，不并入主状态）
```

### 9.2 环节注册：资源类挂多个 `AuditMachine`

`AuditStateMachine` 增加"多环节"能力——子类不再只能声明一条 `TRANSITIONS`，而是可挂多个环节：

```python
class AuditStateMachine(ABC):
    # 主状态可见性迁移（当前"该不该公开/能否互动"的总状态）
    TRANSITIONS: tuple[Transition, ...] = ()

    # 本资源支持的所有审核环节（每环节一个独立子机）
    @classmethod
    def flows(cls) -> tuple[AuditFlow, ...]:
        """该资源经历的所有审核环节（可顺序/并列）。"""

@dataclass(frozen=True)
class AuditFlow:
    """一个审核环节：独立的迁移表 + 规则 + 副作用，链到主状态输出。"""
    name: str                       # 如 "text_auto" / "content_manual" / "report"
    machine: type[AuditStateMachine]  # 本环节自己的状态机（独立 TRANSITIONS）
    affects_primary: bool           # 该环节结果是否联动主状态 auditStatus
    when_primary: dict              # 环节结果 -> 主状态应置为什么（或给出推导函数）
```

### 9.3 主状态由环节共同推出（编排器）

新增一个轻量编排入口，按当前环节状态推导/联动主 `auditStatus`：

```python
class AuditFlowOrchestrator:
    """把多个审核环节接到一个资源主状态上的编排器。"""

    def __init__(self, resource, primary: ResourceAuditStatusEnum, flows: list[AuditFlow]):
        ...

    async def run_flow(self, session, flow_name, *, action, actor_mid, reason, remark):
        """执行某个环节的状态迁移（该环节自己的 TRANSITIONS 校验），
        若 affects_primary 则按 when_primary 联动主表 auditStatus。"""
        flow = self._flow(flow_name)
        to = await flow.machine().transition(session, self.resource, action=action, ...)
        if flow.affects_primary:
            primary = flow.when_primary.get(to)
            if primary:
                setattr(self.resource, "auditStatus", primary)   # 唯一写主状态处
        return to

    async def derive_primary(self) -> ResourceAuditStatusEnum:
        """（可选）从各环节当前状态反推主状态：如某环节 REJECTED -> 主 REJECTED；
        所有环节都 NORMAL 才 NORMAL；有环节 HIDDEN -> HIDDEN。规则可配置。"""
```

> 主状态是"当前可见性"，各环节是"过程"。主状态由环节**编排**得出 / 联动置位，不是每个环节各改各的、互相打架。

### 9.4 各资源的多环节示例（评审定稿方向）

| 资源 | 环节(Flow) | 是否联动主 auditStatus |
|---|---|---|
| 动态 | text_auto(自动文本) → content_manual(人工) | text_auto PASS 不阻断；content_manual REJECTED → 主 REJECTED；HIDE → 主 HIDDEN |
| 评论 | text_auto(自动) / content_manual(人工) | 自动 REJECTED → 主 REJECTED；审核中主 AUDITING |
| 私信 | content_manual(人工审核) | REJECTED/HIDDEN → 主 REJECTED/HIDDEN（不可见） |
| 头像 | url_check(URL/合规) | APPROVE → 主 NORMAL(公开新头像)；REJECT → 主 REJECTED |
| 话题 | content_manual | NORMAL → 主 NORMAL；REJECT → 主 REJECTED |
| 举报 | report(举报处置) | **独立**，不并入主 auditStatus（举报成立仅作为"触发下架"外因） |

### 9.5 与阶段一单状态机骨架的关系

阶段一已落地的 `AuditStateMachine` 是**单个环节**的状态机基础单元（一个 Flow 内部的一次流转）。多环节编排（本 §9）是**在其之上的编排层**：把多个 Flow 挂到一个资源、由 Orchestrator 联动主状态。两者不冲突——先有环节内迁移，再有环节间编排。

---

## 10. 分步落地计划

### 阶段一：铺状态机骨架 + 多环节编排层（纯新增，不改存量行为）
1. 新增 `app/models/moderation.py`（`ModerationAction`；统一枚举 `ResourceAuditStatusEnum` 收口于此或 `enums.py`）。
2. 新增 `app/services/moderation/state_machine.py`（`Transition`/`AuditStateMachine`/`StateTransitionError`）。
3. 新增 `app/services/moderation/flow.py`（`AuditFlow`：多环节描述；`AuditFlowOrchestrator`：主状态 + 环节编排联动，见 §9）。
4. 新增 `app/services/moderation/mapping.py`（`resource_status_of`/`native_state_of`）。
5. 单测：环节内迁移表校验 / 非法流转拦截 / 钩子顺序 + 编排器多环节联动主状态推导。

### 阶段二：统一枚举 + 列（动 DB，未上线可直接改）
6. `enums.py` 收敛 `ResourceAuditStatusEnum`，旧审核枚举删除；列名统一 `auditStatus`（`CommentIndex.state`、`DmMessageIndex.audit_state` → `auditStatus`）。
7. 各 ORM 模型审核列类型换统一枚举（`TResourceFeed.auditStatus` 字符串→int 枚举）；头像/封面 `PENDING→AUDITING`、`APPROVED→NORMAL` 语义映射。
8. 适配 feed 引擎/索引/列名改名牵连的查询代码。
> 未上线：不做历史数据迁移；模型改后重启即按新定义建表。

### 阶段三：迁移存量调用到编排层 + 补齐流水
9. 先动低风险：头像/封面/话题 `approve/reject` → 各资源 `AuditStateMachine` + `AuditFlow`；顺带统一 pending_list 列表骨架。
10. 再动高风险：`DynamicBiz.audit_approve/reject/hide` 改薄封装并挂多环节（text_auto/content_manual）；评论/私信状态写入切统一映射器；补齐各资源 `TResourceAuditLog` 写入。

### 阶段四：收尾
11. 清理裸字符串/旧枚举引用，全走映射器。
12. 删除被收编的重复枚举，并入权威计划书 `docs/be-message-统一计划书.md`。

---

## 11. 风险与规避

| 风险 | 规避 |
|---|---|
| 存量 int 数值错位（AUDITING/NORMAL 相反） | §6 强制语义映射 + 断言脚本（未上线则删旧清库） |
| 评论/私信并入统一枚举/改列名（`state`/`audit_state`→`auditStatus`）回归 | 逐表核对可见性逻辑 + 索引改名 + 全部引用同步 |
| FORWARD 源计数 ±1 反复横跳 | 阶段三第 10 步前补状态机+计数全路径单测 |
| Feed 字符串列改枚举破坏 feed 引擎 | 同步适配读取与 `idx_resfeed_status_pubtime`，补 feed 单测 |
| 把 ①② 业务实体误并表 | §3 已边界化：只统一③流水，①②保留各自表 |
| `PENDING`/`AUDITING` 同值混淆 | 方案甲：只保留 `AUDITING`，单据待审语义靠 `biz_type`/环节区分 |
| **多环节主状态推导错乱**（多个环节都想改主 auditStatus 互相打架） | 主状态**只由 `AuditFlowOrchestrator` 单一入口联动**（§9.3），环节 affects_primary + when_primary 显式声明；单测覆盖「环节 REJECT → 主 REJECT」等组合 |
| **误删非审核态枚举/列**（`CommentSubject.state` 评论区开放态、`DmMsgStatusEnum.msg_status` 撤回态） | 旁路枚举独立保留（见 §3 边界）；重构只动审核态枚举，不碰评论区开放态/消息撤回态 |

---

## 12. 评审已定决策存档

1. **业务实体表不合并**（动态/评论/私信/头像/封面各自保留），状态列统一为 `ResourceAuditStatusEnum`。
2. **统一审核流水落 `TResourceAuditLog`**（推广到评论/私信/头像/封面），管理端统一查询。
3. **对象"资源化"**：各审核对象做成类似动态的 `AuditStateMachine` 实现（迁移表 + 副作用钩子），业务实体仍各自表。
4. `TResourceFeed.auditStatus` 直接改 int 枚举列。
5. 评论/私信并入统一枚举（`state`/`audit_state` → `auditStatus`）；评论 DELETED 并入，动态软删走独立 deletedAt。
6. 不引入 RESTORE。
7. `PENDING` 不单设成员（方案甲），统一用 `AUDITING` 表示"待审"，单据待审靠 `biz_type` 语义区分。
8. **一个资源可有多个审核流程**：资源经历多个顺序/并列审核环节（自动文本 / 人工内容 / 举报处置等），每环节是独立 `AuditStateMachine`；在 `AuditStateMachine` 之上加 `AuditFlow` + `AuditFlowOrchestrator` 编排层（见 §9）。
9. **主状态 + 多环节子状态**：资源主表 `auditStatus` 存总可见性状态，由各环节经 Orchestrator 联动/推导；环节自身 pending/reject 记 `TResourceAuditLog` / 举报单，不在主表冗余。举报单独立不并入主状态。
10. 旧审核枚举**直接删除**（不留别名），全部以 `ResourceAuditStatusEnum`（NORMAL=1）为准；动态/话题等错位数值随删随清。
11. 头像/封面单据语义映射进统一枚举：`PENDING→AUDITING(2)`、`APPROVED→NORMAL(1)`、`REJECTED→REJECTED(3)`；评论/私信/私信审核列名统一为 `auditStatus`。
