"""社区互动通用服务（收藏 / 点赞通用逻辑，2.18.0 统一收口到 bili-common）。

- `InteractionStatService`：非动态资源交互计数（likeCount / favoriteCount）原子 ±1、
  批量读取，操作**继承 `InteractionStatBase` 的计数表模型**（由业务系统子类绑定）。
- `InteractionResourceValidator`：按 `bizType` 注册式资源存在性校验，
  dynamic 等本系统资源由业务系统注册校验器；未注册的跨服务类型默认放行。
"""

from typing import Awaitable, Callable

from sqlmodel import col, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from bili_common.models.interaction import InteractionBizTypeEnum

DYNAMIC_BIZ_TYPE = InteractionBizTypeEnum.DYNAMIC


def _coerce_biz_type(biz_type: InteractionBizTypeEnum | str | int) -> InteractionBizTypeEnum:
    """把字符串 / 数字 / 枚举规范化为枚举成员；未知类型抛 ValueError。"""
    if isinstance(biz_type, InteractionBizTypeEnum):
        return biz_type
    try:
        return InteractionBizTypeEnum.from_text(biz_type)
    except (ValueError, KeyError):
        raise ValueError(f"不支持的资源类型: {biz_type}") from None


class InteractionResourceValidator:
    """按 bizType 注册的资源存在性校验器（注册式扩展，通用）。

    `register(biz_type, checker)`：checker 为 `async (session, biz_id) -> bool`。
    `validate(session, biz_type, biz_id)`：校验资源是否存在，不存在抛 ValueError。
    未注册的其它类型（跨服务资源）默认放行（存在性由调用方/前端保证）。
    注册表键统一用 `biz_type.value`（int，与 DB INT 列一致）。
    """

    _checkers: dict[int, Callable[[AsyncSession, int], Awaitable[bool]]] = {}

    @classmethod
    def register(
        cls,
        biz_type: InteractionBizTypeEnum | str | int,
        checker: Callable[[AsyncSession, int], Awaitable[bool]],
    ) -> None:
        """注册某资源类型的校验器（幂等覆盖）。"""
        cls._checkers[_coerce_biz_type(biz_type).value] = checker

    @classmethod
    async def validate(
        cls, session: AsyncSession, biz_type: InteractionBizTypeEnum | str | int, biz_id: int
    ) -> None:
        """校验 (biz_type, biz_id) 资源存在；不存在抛 ValueError。"""
        checker = cls._checkers.get(_coerce_biz_type(biz_type).value)
        if checker is None:
            # 未注册类型的资源默认放行（存在性由调用方/前端保证）
            return
        ok = await checker(session, biz_id)
        if not ok:
            raise ValueError("资源不存在")


class InteractionStatService:
    """非动态资源交互计数服务（通用）。

    子类需绑定 `model`（继承 `InteractionStatBase` 的计数表）与
    `view_log_model`（继承 `InteractionViewLogBase` 的浏览去重表，2.23.0）。
    """

    #: 计数表模型（子类绑定）
    model = None
    #: 浏览去重明细表模型（子类绑定；2.23.0 起 report_view 使用）
    view_log_model = None

    @staticmethod
    def is_dynamic(biz_type: InteractionBizTypeEnum | str | int) -> bool:
        return _coerce_biz_type(biz_type) == DYNAMIC_BIZ_TYPE

    @classmethod
    def _coerce(cls, biz_type: InteractionBizTypeEnum | str | int) -> InteractionBizTypeEnum:
        """把字符串 / 数字 / 枚举规范化为枚举成员；未知类型抛 ValueError。"""
        return _coerce_biz_type(biz_type)

    @classmethod
    async def _get_row(
        cls, session: AsyncSession, biz_type: InteractionBizTypeEnum | str | int, biz_id: int
    ):
        bt = cls._coerce(biz_type)
        return (
            await session.exec(
                select(cls.model).where(
                    col(cls.model.bizType) == bt,
                    col(cls.model.bizId) == biz_id,
                )
            )
        ).one_or_none()

    @classmethod
    async def _ensure_row(
        cls, session: AsyncSession, biz_type: InteractionBizTypeEnum | str | int, biz_id: int
    ) -> None:
        """确保存在计数行（惰性创建，首次交互时建行）。"""
        row = await cls._get_row(session, biz_type, biz_id)
        if row is None:
            session.add(cls.model(bizType=cls._coerce(biz_type), bizId=biz_id))
            await session.flush()

    @classmethod
    async def incr(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_id: int,
        field: str,
        delta: int,
    ) -> None:
        """对非动态资源计数原子 ±delta（field ∈ {likeCount, favoriteCount, viewCount}）。"""
        await cls._ensure_row(session, biz_type, biz_id)
        column = getattr(cls.model, field, None)
        if column is None or field not in {"likeCount", "favoriteCount", "viewCount"}:
            raise ValueError(f"不支持的计数列: {field}")
        await session.exec(
            update(cls.model)
            .where(
                col(cls.model.bizType) == cls._coerce(biz_type),
                col(cls.model.bizId) == biz_id,
            )
            .values({column: col(column) + delta})
        )

    @classmethod
    async def decr(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_id: int,
        field: str,
        *,
        floor_zero: bool = True,
    ) -> None:
        """对非动态资源计数 -1（默认 floor_zero 防负数）。"""
        await cls._ensure_row(session, biz_type, biz_id)
        column = getattr(cls.model, field, None)
        if column is None or field not in {"likeCount", "favoriteCount"}:
            raise ValueError(f"不支持的计数列: {field}")
        stmt = (
            update(cls.model)
            .where(
                col(cls.model.bizType) == cls._coerce(biz_type),
                col(cls.model.bizId) == biz_id,
            )
            .values({column: col(column) - 1})
        )
        if floor_zero:
            stmt = stmt.where(col(column) > 0)
        await session.exec(stmt)

    @classmethod
    async def batch_get_counts(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_ids: list[int],
    ) -> dict[int, dict[str, int]]:
        """批量读取某类型资源计数（biz_id → {likeCount, favoriteCount, viewCount}，缺省 0）。"""
        result: dict[int, dict[str, int]] = {
            b: {"likeCount": 0, "favoriteCount": 0, "viewCount": 0} for b in biz_ids
        }
        if not biz_ids:
            return result
        bt = cls._coerce(biz_type)
        rows = (
            await session.exec(
                select(cls.model).where(
                    col(cls.model.bizType) == bt,
                    col(cls.model.bizId).in_(biz_ids),
                )
            )
        ).all()
        for row in rows:
            result[row.bizId] = {
                "likeCount": int(row.likeCount),
                "favoriteCount": int(row.favoriteCount),
                "viewCount": int(row.viewCount),
            }
        return result

    @classmethod
    async def report_view(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_id: int,
        mid: int,
        ref_date: str,
    ) -> bool:
        """浏览去重上报（非动态资源）：仅首次（bizType+bizId+mid+refDate 无明细）时给 viewCount +1。

        完全对标 `MomentStatService.report_view`（动态）：「明细表唯一约束幂等 + 计数原子 ±1」——
        先查 `TInteractionViewLog`，已存在当日明细只累加明细行 viewCount（返回 False）；
        不存在则插入明细（viewCount=1）并原子 +1 `TInteractionStat.viewCount`（返回 True）。
        调用方负责 `session.commit()`。

        Returns:
            True=首次浏览（Stat.viewCount +1）；False=当日重复浏览（仅累加明细行）。
        """
        bt = cls._coerce(biz_type)
        if cls.view_log_model is None:
            raise NotImplementedError("view_log_model 未绑定，无法上报浏览")
        exists = (
            await session.exec(
                select(cls.view_log_model).where(
                    col(cls.view_log_model.bizType) == bt,
                    col(cls.view_log_model.bizId) == biz_id,
                    col(cls.view_log_model.mid) == mid,
                    col(cls.view_log_model.refDate) == ref_date,
                )
            )
        ).one_or_none()
        if exists is not None:
            await session.exec(
                update(cls.view_log_model)
                .where(col(cls.view_log_model.pk) == exists.pk)
                .values(viewCount=col(cls.view_log_model.viewCount) + 1)
            )
            return False
        session.add(cls.view_log_model(bizType=bt, bizId=biz_id, mid=mid, refDate=ref_date, viewCount=1))
        await session.flush()
        await cls._ensure_row(session, bt, biz_id)
        await cls.incr(session, bt, biz_id, "viewCount", 1)
        return True


__all__ = [
    "DYNAMIC_BIZ_TYPE",
    "InteractionResourceValidator",
    "InteractionStatService",
]
