"""社区互动通用计数表基类（2.18.0 统一收口到 bili-common）。

`InteractionStatBase` 定义非动态资源（lottery / rpa_*）收藏 / 点赞 / 浏览计数的通用字段，
各业务系统继承并 `table=True` 建立物理表（be-message 的 `TInteractionStat`）。
`InteractionViewLogBase` 定义通用浏览去重明细（对标动态 `TMomentViewLog`）。

遵循「明细表幂等 + 计数原子 ±1」范式：仅存数字计数，禁止请求热路径 COUNT 聚合。
"""

from sqlalchemy import BIGINT
from sqlmodel import Field, SQLModel

from bili_common.models.db_types import int_enum_type
from bili_common.models.interaction import InteractionBizTypeEnum


class InteractionStatBase(SQLModel):
    """非动态资源交互计数表字段基类（非表模型，业务系统子类继承建表）。"""

    bizType: InteractionBizTypeEnum = Field(
        default=None,
        primary_key=True,
        sa_type=int_enum_type(InteractionBizTypeEnum),
        sa_column_kwargs={"autoincrement": False},
        description="资源类型（IntEnum 落库 INT）：2=lottery,3=rpa_action,4=rpa_workflow,5=rpa_browser,6=rpa_plugin",
    )
    bizId: int = Field(
        default=None,
        primary_key=True,
        sa_type=BIGINT,
        sa_column_kwargs={"autoincrement": False},
        description="资源id",
    )
    likeCount: int = Field(default=0, sa_type=BIGINT, description="点赞数（明细表 + 原子 ±1）")
    favoriteCount: int = Field(default=0, sa_type=BIGINT, description="收藏数（明细表 + 原子 ±1）")
    viewCount: int = Field(default=0, sa_type=BIGINT, description="浏览数（TInteractionViewLog 去重 + 首次原子 +1；2.23.0）")


class InteractionViewLogBase(SQLModel):
    """通用浏览去重明细字段基类（2.23.0；非表模型，业务系统子类继承建表）。

    完全对标动态 `TMomentViewLog`：「同一用户同一资源同一天只计一次 Stat 浏览量」——
    先 upsert 本表，仅首次插入才给 `TInteractionStat.viewCount` +1；
    同日重复只累加本表 `viewCount`，不累加 Stat。
    """

    pk: int = Field(default=None, primary_key=True, sa_type=BIGINT, sa_column_kwargs={"autoincrement": True})
    bizType: InteractionBizTypeEnum = Field(
        default=None,
        nullable=False,
        sa_type=int_enum_type(InteractionBizTypeEnum),
        description="资源类型（IntEnum 落库 INT）：2=lottery,...",
    )
    bizId: int = Field(default=None, nullable=False, sa_type=BIGINT, description="资源id（雪花id）")
    mid: int = Field(default=None, nullable=False, sa_type=BIGINT, description="浏览者 UID")
    refDate: str = Field(default=None, nullable=False, max_length=10, description="日期 YYYY-MM-DD")
    viewCount: int = Field(default=1, description="当日浏览次数（首次为 1）")


__all__ = ["InteractionStatBase", "InteractionViewLogBase"]
