"""通用举报服务（bili-common，多服务共享）。

`ReportBaseService` 以 `ReportBase` 类型的子表（各业务继承 `ReportBase` 的 SQLModel）
作为操作对象，提供举报记录写入 / 列表 / 审核的**通用逻辑**；各业务在调用时传入
自己的子表模型类即可，逻辑一致。

写入成功后通过可选回调 `on_recorded` 把 `ReportEvent` 发布到 MQ（fire-and-forget），
由消息消费者按 `bizType` 异步做阈值联动（累计 / 转审核 / 通知），与记录写入解耦。
"""

from sqlalchemy import func
from sqlmodel import col, select

from bili_common.models.report import (
    ReportAuditStatusEnum,
    ReportBase,
    ReportReviewDecisionEnum,
)


class ReportBaseService:
    """通用举报服务（静态方法集合，无状态；`session` 由调用方提供）。"""

    @staticmethod
    async def record_report(
        session,
        model,
        *,
        reporter_mid: int,
        biz_type: str,
        biz_id: int,
        accused_mid: int,
        reason_type: int,
        reason_desc: str | None = None,
        pics: str | None = None,
        resource_type: int | None = None,
        on_recorded=None,
    ) -> tuple[bool, int | None]:
        """幂等写入一条举报记录到指定子表（一人对同一对象只记一次）。

        Args:
            session: 数据库会话（AsyncSession）。
            model: 继承 `ReportBase` 的举报子表模型类（表达表名，逻辑一致）。
            resource_type: 2.37.0 被举报对象所属资源类型（InteractionBizTypeEnum 值），
                供通用 EdgeRank 举报数降权按 resourceType+bizId 统计；可空。
            on_recorded: 可选回调 `on_recorded(record)`，在记录写入并 commit 后调用
                （典型用于把 `ReportEvent` 发布到 MQ）。

        Returns:
            (created, record_pk)：created 表示本次是否新增；record_pk 为记录主键
            （重复举报时为 None）。
        """
        exists = (
            await session.exec(
                select(model.pk).where(
                    model.reportMid == reporter_mid,
                    model.bizType == biz_type,
                    model.bizId == biz_id,
                )
            )
        ).first()
        if exists is not None:
            await session.commit()
            return False, None

        rec = model(
            bizType=biz_type,
            bizId=biz_id,
            resourceType=resource_type,
            accusedMid=accused_mid,
            reportMid=reporter_mid,
            reasonType=reason_type,
            reasonDesc=reason_desc,
            pics=pics,
        )
        session.add(rec)
        await session.flush()
        pk = int(rec.pk)
        await session.commit()
        if on_recorded is not None:
            on_recorded(rec)
        return True, pk

    @staticmethod
    async def list_reports(
        session,
        model,
        *,
        biz_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list, int]:
        """通用分页列表（按创建时间倒序），返回 (items, total)。"""
        page = max(1, page)
        page_size = min(max(1, page_size), 50)
        conds = []
        if biz_type:
            conds.append(model.bizType == biz_type)
        if status:
            conds.append(model.auditStatus == status)

        total = int(
            (
                await session.exec(select(func.count()).select_from(model).where(*conds))
            ).one()
            or 0
        )
        items = (
            await session.exec(
                select(model)
                .where(*conds)
                .order_by(col(model.created_at).desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return list(items), total

    @staticmethod
    async def review(
        session,
        model,
        *,
        report_pk: int,
        admin_mid: int,
        decision: str,
        remark: str | None = None,
    ) -> None:
        """通用审核：resolve（属实已处理）/ reject（驳回）。"""
        rec = (
            await session.exec(select(model).where(model.pk == report_pk))
        ).one_or_none()
        if rec is None:
            raise ValueError("举报记录不存在")
        decision_enum = ReportReviewDecisionEnum(decision)
        rec.auditStatus = (
            ReportAuditStatusEnum.RESOLVED
            if decision_enum is ReportReviewDecisionEnum.RESOLVE
            else ReportAuditStatusEnum.REJECTED
        )
        rec.auditRemark = remark
        rec.auditAdminMid = admin_mid
        session.add(rec)
        await session.commit()


__all__ = ["ReportBaseService"]
