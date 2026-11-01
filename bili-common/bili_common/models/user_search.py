"""用户搜索接口：请求参数与响应模型（统一管理，供各微服务复用）。

与 bili_common 其他公共模型（pagination / response）保持一致，**统一使用 SQLModel**。

- 请求参数 `UserSearchParams`：继承泛型分页基类 `RequestOffsetLimitParams[T]`，
  复用 `offset` / `limit` 分页字段，并补充 `keyword` 关键字；
- 响应模型 `PptrUserSearchItem` 及其子结构，结构对齐 pptr 网关 `GET /api/v1/user/search`
  的返回，但统一走 `StandardResponse`（`code=0`）。bigint（mid / uid）出参为 int 数值 +
  `@auto_str` 自动派生的 `_str` 字符串版（后缀 `_str`），前端只用字符串版，避免 JS 端
  Number 精度丢失；等级 / 经验 / 大会员等普通数值保持 number。

这些模型被 be-message-service 的 `GET /api/v1/message/admin/user/search` 使用，
该接口经由 pptr 网关转发，仅系统管理员(root)可调用。

关于 OpenAPI：SQLModel 模型**作为 FastAPI query 依赖（Depends(模型类)）** 时，
SQLModel 的 `Field` 元数据会触发 `TypeError: unhashable type: 'FieldInfoMetadata'`
（SQLModel + pydantic v2 + FastAPI 的已知兼容问题）。因此路由侧改用函数依赖
（`Query` 参数解析后构造 `UserSearchParams`），不会触碰该 bug；而响应模型使用
`SQLModel` 是安全的（FastAPI 对 response_model 的 schema 生成无此问题）。
"""

from typing import ClassVar

from sqlmodel import SQLModel, Field

from bili_common.models.auto_str import auto_str
from bili_common.models.pagination import RequestOffsetLimitParams


class UserSearchParams(RequestOffsetLimitParams):
    """用户搜索请求参数：关键字 + offset/limit 分页。

    继承泛型分页基类 `RequestOffsetLimitParams`，复用 `offset` / `limit`。
    经 pptr 网关（/api/v1/message/admin/user/search）转发到 be-message-service。
    """

    keyword: str = Field(
        default="",
        description="搜索关键字：昵称 / 注册名 / mid / 邮箱",
    )


class PptrUserRoleInfo(SQLModel):
    """角色信息（对齐 pptr search 出参）。"""

    role_name: str = Field(default="", description="角色标识，如 level0..level6 / root")
    role_description: str = Field(default="", description="角色中文描述")


@auto_str(suffix="_str")
class PptrUserLevelInfo(SQLModel):
    """成长等级信息（对齐 pptr search 出参）。

    此为 pptr 等级信息的唯一权威定义，pptr_user_rpc 同样复用本类（rpc 场景下会
    额外传入 uid / updated_at）。

    雪花 ID（uid）出参为 int + 自动派生的 `uid_str`（防 JS Number 精度丢失）；
    等级 / 经验是普通数值，出参保持 number，由前端自行按需格式化。
    Python 侧一律拿到 int 做计算。
    """

    _auto_str_suffix: ClassVar[str] = "_str"

    uid: int | None = Field(
        default=None, description="用户 UID（可空，search 场景无需；前端请用 uid_str）"
    )
    current_level: int = Field(default=0, description="当前等级")
    current_exp: int = Field(default=0, description="当前累积经验")
    current_min: int = Field(default=0, description="当前等级起始经验")
    next_exp: int = Field(
        default=0,
        description="距下一级还需经验（下一级门槛经验 - 当前累积经验），满级为 0",
    )
    updated_at: str = Field(
        default="", description="TUserLevel.updatedAt（ISO），用于每日经验幂等判断"
    )


@auto_str(suffix="_str")
class PptrUserVipInfo(SQLModel):
    """大会员信息（对齐 pptr search 出参）。

    vip_* 均为状态枚举 / 秒级时间戳，不是雪花 ID，出参保持 number。
    保留装饰器是为了后续新增雪花 ID 字段时自动派生字符串版。
    """

    _auto_str_suffix: ClassVar[str] = "_str"

    vip_status: int = Field(default=0, description="0非vip / 1vip / 2过期")
    vip_type: int = Field(default=0, description="0非vip / 1月 / 2年 / 3十年 / 4百年")
    vip_due_date: int = Field(default=0, description="到期时间戳(ms)")
    vip_pay_type: int = Field(default=0, description="充值渠道")


@auto_str(suffix="_str")
class PptrUserSearchItem(SQLModel):
    """搜索用户返回的单条记录（对齐前端 PptrUserSearchItem）。

    `mid` 与 `uid` 是同一个雪花 ID（BIGINT），出参为 int 数值 + 自动派生的
    `mid_str` / `uid_str` 字符串版；**前端只能用字符串版**，避免 JS 精度丢失。
    `regtime` 是毫秒时间戳，保持 number。
    """

    _auto_str_suffix: ClassVar[str] = "_str"

    mid: int = Field(
        default=0, description="用户ID（int 内部使用，前端请用 mid_str 字符串版）"
    )
    uid: int = Field(
        default=0, description="用户ID（同 mid；前端请用 uid_str 字符串版）"
    )
    user_name: str | None = Field(default=None, description="注册默认名")
    uname: str | None = Field(default=None, description="昵称")
    email: str | None = Field(default=None, description="邮箱（脱敏）")
    avatar: str | None = Field(default=None, description="头像URL")
    sign: str | None = Field(default=None, description="个性签名")
    sex: str | None = Field(default=None, description="性别")
    regtime: int | None = Field(default=None, description="注册时间(ms)")
    level_info: PptrUserLevelInfo = Field(default_factory=PptrUserLevelInfo)
    vip: PptrUserVipInfo = Field(default_factory=PptrUserVipInfo)
    role_info: PptrUserRoleInfo = Field(default_factory=PptrUserRoleInfo)


class PptrUserSearchResult(SQLModel):
    """用户搜索接口的响应体：当前页列表 + 是否还有更多。

    采用 cursor（offset）分页：前端根据 `has_more` 自行决定是否继续下拉加载，
    无需服务端统计 total。
    """

    items: list[PptrUserSearchItem] = Field(
        default_factory=list, description="当前页用户列表"
    )
    has_more: bool = Field(
        default=False, description="是否还有下一页，前端据此下拉加载更多"
    )


__all__ = [
    "UserSearchParams",
    "PptrUserRoleInfo",
    "PptrUserLevelInfo",
    "PptrUserVipInfo",
    "PptrUserSearchItem",
    "PptrUserSearchResult",
]
