"""社区互动通用服务（收藏 / 点赞通用逻辑，2.18.0 统一收口到 bili-common）。

- `InteractionStatService`：非动态资源交互计数（likeCount / favoriteCount）原子 ±1、
  批量读取，操作**继承 `InteractionStatBase` 的计数表模型**（由业务系统子类绑定）。
- `InteractionResourceValidator`：按 `bizType` 注册式资源存在性校验，
  dynamic 等本系统资源由业务系统注册校验器；未注册的跨服务类型默认放行。
"""

from datetime import datetime
from typing import Awaitable, Callable

from sqlalchemy.dialects.mysql import insert as mysql_insert
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
        """确保存在计数行（惰性创建，首次交互时建行）。

        采用 MySQL 原子 upsert（``INSERT ... ON DUPLICATE KEY UPDATE`` 空更新）：
        消除并发首交互「先查后插」竞态 —— 多事务同时插入同一 ``(bizType, bizId)``
        行时，后提交者的 ``flush`` 会报 1062 主键冲突（Duplicate entry），
        upsert 幂等后不报错（已存在则按插入值空更新，不触发真实写入）。
        """
        bt = cls._coerce(biz_type)
        now = datetime.now()
        # Core insert 不走 ORM：`Field(default=0)` 的 Python 默认不生效，
        # 必须显式给计数列初始值 0，否则编译为 NULL（依赖 SQL_MODE，且 NULL+1=NULL
        # 会让计数永不增长）。用 _COUNT_FIELDS 白名单保证与子类列集一致。
        values: dict = {
            "bizType": bt,
            "bizId": biz_id,
            "created_at": now,
            "updated_at": now,
        }
        for f in cls._COUNT_FIELDS:
            values[f] = 0
        stmt = mysql_insert(cls.model).values(**values)
        stmt = stmt.on_duplicate_key_update(bizType=stmt.inserted.bizType)
        await session.exec(stmt)

    #: 2.36.0：通用计数列白名单（动态与非动态资源统一）
    _COUNT_FIELDS = frozenset(
        {
            "likeCount",
            "favoriteCount",
            "viewCount",
            "commentCount",
            "repostCount",
            "shareCount",
            "dislikeCount",
            "coinCount",
        }
    )

    @classmethod
    async def incr(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_id: int,
        field: str,
        delta: int,
    ) -> None:
        """对资源计数原子 ±delta（field ∈ 通用计数列白名单，2.36.0 全资源统一）。"""
        await cls._ensure_row(session, biz_type, biz_id)
        column = getattr(cls.model, field, None)
        if column is None or field not in cls._COUNT_FIELDS:
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
        """对资源计数 -1（默认 floor_zero 防负数）。"""
        await cls._ensure_row(session, biz_type, biz_id)
        column = getattr(cls.model, field, None)
        if column is None or field not in cls._COUNT_FIELDS:
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
        """批量读取某类型资源计数（biz_id → 全计数字段 dict，缺省 0）。

        字段：likeCount / favoriteCount / viewCount / commentCount / repostCount /
        shareCount / dislikeCount / coinCount（2.36.0 全资源统一）。
        """
        result: dict[int, dict[str, int]] = {
            b: {
                "likeCount": 0,
                "favoriteCount": 0,
                "viewCount": 0,
                "commentCount": 0,
                "repostCount": 0,
                "shareCount": 0,
                "dislikeCount": 0,
                "coinCount": 0,
            }
            for b in biz_ids
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
                "commentCount": int(row.commentCount),
                "repostCount": int(row.repostCount),
                "shareCount": int(row.shareCount),
                "dislikeCount": int(row.dislikeCount),
                "coinCount": int(row.coinCount),
            }
        return result

    @classmethod
    async def report_view(
        cls,
        session: AsyncSession,
        biz_type: InteractionBizTypeEnum | str | int,
        biz_id: int,
        mid: int,
    ) -> bool:
        """浏览去重上报（非动态资源）：每用户每资源一行，跨自然日再次访问才给 viewCount +1。

        2.42.0：明细表唯一约束 ``(bizType, bizId, mid)``（无按天行）——
        先查明细行，已存在且 ``lastViewAt`` 与当前时间同一自然日（同日重复访问）只累加
        明细行 viewCount + 刷新 lastViewAt（返回 False）；否则（首次访问 / 跨天再次访问）
        更新明细并原子 +1 ``TInteractionStat.viewCount``（返回 True）。
        调用方负责 ``session.commit()``。

        Returns:
            True=新计一次浏览量（Stat.viewCount +1）；False=同日重复浏览（仅累加明细行）。
        """
        bt = cls._coerce(biz_type)
        if cls.view_log_model is None:
            raise NotImplementedError("view_log_model 未绑定，无法上报浏览")
        now = datetime.now()
        exists = (
            await session.exec(
                select(cls.view_log_model).where(
                    col(cls.view_log_model.bizType) == bt,
                    col(cls.view_log_model.bizId) == biz_id,
                    col(cls.view_log_model.mid) == mid,
                )
            )
        ).one_or_none()
        if exists is not None:
            # 同日重复访问：仅累加明细行计数 + 刷新最后访问时间，不累加 Stat
            if exists.lastViewAt is not None and exists.lastViewAt.date() == now.date():
                await session.exec(
                    update(cls.view_log_model)
                    .where(col(cls.view_log_model.pk) == exists.pk)
                    .values(
                        viewCount=col(cls.view_log_model.viewCount) + 1,
                        lastViewAt=now,
                    )
                )
                return False
            # 跨天再次访问：新计一次浏览量
            await session.exec(
                update(cls.view_log_model)
                .where(col(cls.view_log_model.pk) == exists.pk)
                .values(
                    viewCount=col(cls.view_log_model.viewCount) + 1,
                    lastViewAt=now,
                )
            )
            await cls._ensure_row(session, bt, biz_id)
            await cls.incr(session, bt, biz_id, "viewCount", 1)
            return True
        session.add(
            cls.view_log_model(
                bizType=bt, bizId=biz_id, mid=mid, viewCount=1, lastViewAt=now
            )
        )
        await session.flush()
        await cls._ensure_row(session, bt, biz_id)
        await cls.incr(session, bt, biz_id, "viewCount", 1)
        return True


__all__ = [
    "DYNAMIC_BIZ_TYPE",
    "InteractionResourceValidator",
    "InteractionStatService",
]
