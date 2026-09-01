"""统一举报通用模型（多服务共享，bili-common）。

设计：**同一结构的举报 SQLModel** 定义在 bili-common，各业务（动态 / 评论 / 用户空间）
在各自服务里继承 `ReportBase`（`table=True`）生成自己的表模型，字段结构完全一致；
举报的通用逻辑（幂等写 / 列表 / 审核 / 阈值联动触发）由
`bili_common.services.report.ReportBaseService` 实现，操作 `ReportBase` 类型。

本模块定义：
- `ReportBase`：通用举报记录抽象基类（`table=False`，各业务表继承复用同构字段）；
- `ReportBizTypeEnum`：举报来源类型（dynamic/comment/user）；
- `ReportReasonEnum`：统一举报原因（对齐 B 站，1-6 与既有 `MomentReportReasonEnum` 兼容）；
- `ReportAuditStatusEnum`：统一举报审核状态；
- `ReportReviewDecisionEnum`：统一管理端处置动作；
- `ReportEvent`：举报事件消息（写入举报记录后发布到 MQ，由消费者异步做阈值联动）。
"""

from datetime import datetime
from bili_common.models import IntEnumAutoDoc

from sqlalchemy import BIGINT
from sqlmodel import Field, SQLModel


class ReportBizTypeEnum(IntEnumAutoDoc):
    """举报来源类型（落 INT）。

    注意：值已改为整数编码，原字符串值（dynamic/comment/user/resource）不再使用，
    既有数据需配套迁移（bizType 列 VARCHAR -> BIGINT/INT，旧字符串值改写为对应编码）。
    """

    DYNAMIC = 1  # 动态举报（bizId = dynId）
    COMMENT = 2  # 评论举报（bizId = rpid）
    USER = 3  # 用户空间举报（bizId = mid）
    # 2.39.0：通用资源举报（bizId = 资源 id；resourceType 标识具体资源类型：lottery/rpa_*）
    RESOURCE = 4


class ReportReasonEnum(IntEnumAutoDoc):
    """统一举报原因类型（对齐 B 站举报弹窗，落 INT）。

    1-6 与既有 `MomentReportReasonEnum` 取值一致（跨表迁移不丢值）。
    """

    FAKE_INFO = 1  # 虚假不实信息
    ILLEGAL = 2  # 违法违规
    PERSONAL_ATTACK = 3  # 人身攻击
    PORN = 4  # 色情低俗
    FRAUD = 5  # 诈骗/欺诈
    OTHER = 6  # 其他
    AD = 7  # 垃圾广告
    FLAME = 8  # 引战
    POLITICAL_RUMOR = 9  # 涉政谣言
    ILLEGAL_LINK = 10  # 违法信息外链


class ReportAuditStatusEnum(IntEnumAutoDoc):
    """统一举报审核状态（落 INT）。"""

    PENDING = 1
    RESOLVED = 2
    REJECTED = 3


class ReportReviewDecisionEnum(IntEnumAutoDoc):
    """统一举报管理端处置动作（落 INT）。"""

    RESOLVE = 1  # 属实，已处理
    REJECT = 2  # 不属实，驳回


class ReportBase(SQLModel):
    """通用举报记录结构（抽象基类，`table=False`，各业务表继承同构字段）。

    各业务在各自服务里做：
    ```python
    class TMomentReport(ReportBase, table=True):
        __tablename__ = "TMomentReport"
        # 继承全部通用字段，可追加业务专属字段
    ```
    通用逻辑（`ReportBaseService`）以本基类类型操作，因此对任意子表行为一致。
    """

    pk: int | None = Field(
        default=None, primary_key=True, sa_type=BIGINT, sa_column_kwargs={"autoincrement": True}
    )
    bizType: int = Field(default=None, index=True, description="举报来源类型（ReportBizTypeEnum 值）：1=dynamic,2=comment,3=user,4=resource")
    bizId: int = Field(default=None, index=True, sa_type=BIGINT, description="被举报对象 id：dynamic→dynId，comment→rpid，user→mid")
    # 2.37.0：被举报对象所属资源类型（InteractionBizTypeEnum 值落 INT）。
    # dynamic 举报自动填充 1；lottery/rpa_* 等资源举报显式传入；None = 仅来源类型。
    # 供通用 EdgeRank 举报数降权按 resourceType+bizId 统计（全资源通用）。
    resourceType: int | None = Field(
        default=None,
        index=True,
        sa_type=BIGINT,
        description="被举报对象所属资源类型（InteractionBizTypeEnum 值）：dynamic=1，lottery/rpa_* 显式传；可空",
    )
    accusedMid: int = Field(default=None, sa_type=BIGINT, description="被举报用户 mid")
    reportMid: int = Field(default=None, index=True, sa_type=BIGINT, description="举报人 mid")
    reasonType: int = Field(default=None, description="统一举报原因（ReportReasonEnum 值）：1-10")
    reasonDesc: str | None = Field(default=None, max_length=500, description="补充描述（选填）")
    pics: str | None = Field(default=None, description="举报证据图片 URL 列表（JSON 数组字符串，最多 3 张，http(s)）")
    auditStatus: int = Field(default=ReportAuditStatusEnum.PENDING, description="举报审核状态（ReportAuditStatusEnum 值）：1=pending,2=resolved,3=rejected")
    auditRemark: str | None = Field(default=None, max_length=500, description="审核处理备注")
    auditAdminMid: int | None = Field(default=None, sa_type=BIGINT, description="处理管理员 MID")
    created_at: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime | None = Field(default_factory=datetime.now, description="更新时间")


class ReportEvent(SQLModel):
    """举报事件消息（fire-and-forget）。

    举报记录写入（各业务表，由 `ReportBaseService.record_report` 触发）后发布到 MQ，
    消费者按 `bizType` 异步处理（累计有效举报数、达阈值把被举报对象转审核、通知等），
    与记录写入解耦。
    """

    bizType: ReportBizTypeEnum
    bizId: int  # dynamic→dynId / comment→rpid / user→mid
    reportMid: int  # 举报人
    reasonType: ReportReasonEnum
    reportPk: int | None = None  # 各业务表举报记录主键（可选）


__all__ = [
    "ReportBase",
    "ReportBizTypeEnum",
    "ReportReasonEnum",
    "ReportAuditStatusEnum",
    "ReportReviewDecisionEnum",
    "ReportEvent",
]
