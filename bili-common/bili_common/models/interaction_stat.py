"""社区互动通用计数表基类（2.18.0 统一收口到 bili-common）。

`InteractionStatBase` 定义非动态资源（lottery / rpa_*）收藏 / 点赞 / 浏览计数的通用字段，
各业务系统继承并 `table=True` 建立物理表（be-message 的 `TInteractionStat`）。
`InteractionViewLogBase` 定义通用浏览去重明细（2.42.0 起每用户每资源一行，对标已删除的动态 `TMomentViewLog`）。

遵循「明细表幂等 + 计数原子 ±1」范式：仅存数字计数，禁止请求热路径 COUNT 聚合。
"""

from datetime import datetime

from sqlalchemy import BIGINT, text
from sqlmodel import Field, SQLModel

from sqlalchemy import Enum as SAEnum
from bili_common.models.interaction import InteractionBizTypeEnum


class InteractionStatBase(SQLModel):
    """非动态资源交互计数表字段基类（非表模型，业务系统子类继承建表）。"""

    bizType: InteractionBizTypeEnum = Field(
        default=None,
        primary_key=True,
        sa_type=SAEnum(InteractionBizTypeEnum),
        sa_column_kwargs={"autoincrement": False},
        description="资源类型（IntEnum 经 sqlalchemy.Enum 落库 MySQL 原生 ENUM，存成员名）：2=lottery,3=rpa_action,4=rpa_workflow,5=rpa_browser,6=rpa_plugin",
    )
    bizId: int = Field(
        default=None,
        primary_key=True,
        sa_type=BIGINT,
        sa_column_kwargs={"autoincrement": False},
        description="资源id",
    )
    likeCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="点赞数（明细表 + 原子 ±1）")
    favoriteCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="收藏数（明细表 + 原子 ±1）")
    viewCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="浏览数（TInteractionViewLog 去重 + 首次原子 +1；2.23.0）")
    # ---- 2.36.0：动态资源计数并入本表（消除 TMomentStat 双轨），全资源统一 ----
    commentCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="评论数（CommentSubject 回调原子 ±1 / 读取时优先评论系统实时计数）")
    repostCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="转发数（动态特有；非动态资源恒 0）")
    shareCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="分享数（分享上报原子 +1；2.35.0）")
    dislikeCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="点踩数（TMomentDislike 明细 + 原子 ±1；2.35.0）")
    coinCount: int = Field(default=0, sa_type=BIGINT, sa_column_kwargs={"server_default": text("0")}, description="投币数（预留）")


class InteractionViewLogBase(SQLModel):
    """通用浏览去重明细字段基类（2.23.0；非表模型，业务系统子类继承建表）。

    2.42.0：**每用户每资源一行**（唯一约束 ``(bizType, bizId, mid)``，无按天明细）——
    「同一用户同一资源同一天只计一次 Stat 浏览量」由 ``lastViewAt`` 与当前时间
    是否同一自然日判断（跨天再次访问才 +1）；明细行 ``viewCount`` 累计该用户
    对该资源的浏览次数，``lastViewAt`` 记录最后访问时间（用户浏览历史点查即用）。
    """

    pk: int = Field(default=None, primary_key=True, sa_type=BIGINT, sa_column_kwargs={"autoincrement": True})
    bizType: InteractionBizTypeEnum = Field(
        default=None,
        nullable=False,
        sa_type=SAEnum(InteractionBizTypeEnum),
        description="资源类型（IntEnum 经 sqlalchemy.Enum 落库 MySQL 原生 ENUM，存成员名）：2=lottery,...",
    )
    bizId: int = Field(default=None, nullable=False, sa_type=BIGINT, description="资源id（雪花id）")
    mid: int = Field(default=None, nullable=False, sa_type=BIGINT, description="浏览者 UID")
    viewCount: int = Field(default=1, description="累计浏览次数（跨天浏览递增）")
    lastViewAt: datetime = Field(
        default=None,
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="最后访问时间（每次浏览刷新；同日重复仅刷新，不重复计 Stat）",
    )


__all__ = ["InteractionStatBase", "InteractionViewLogBase"]
