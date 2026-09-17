"""管理后台：当前登录用户的角色/权限状态（通用响应模型）。

RPA 后台（`/api/admin/rpa/role/me`）与统一消息服务
（`/api/v1/message/admin/me`）都返回"是否管理员 + 权限 + 当前登录用户 mid"，
因此把该结构抽到 bili-common，避免两边各自定义、字段不一致。
"""

from typing import ClassVar

from sqlmodel import Field, SQLModel

from bili_common.models.auto_str import auto_str


@auto_str
class AdminStatusResponse(SQLModel):
    """当前登录用户的角色/权限状态（任意登录用户可查）。

    继承 ``AutoStrMixin``：``mid``（雪花 ID）除数值形式外自动附带字符串版
    ``mid_str``，前端统一消费 ``mid_str`` 避免 JS Number 精度丢失。
    """

    # 本模型出参整体为 snake_case（is_root / biz_perms / mid），故字符串版 ID 用
    # `_str` 后缀而非默认的 camelCase `Str`
    _auto_str_suffix: ClassVar[str] = "_str"

    is_root: bool = False
    is_admin: bool = False
    # 管理端权限（per-biz 位掩码权限字）：键=资源域文本，值=0~7；root 恒 {"*": 7}
    biz_perms: dict[str, int] = Field(default_factory=dict)
    mid: int = 0
