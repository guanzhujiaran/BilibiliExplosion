"""管理后台：当前登录用户的角色/权限状态（通用响应模型）。

RPA 后台（`/api/admin/rpa/role/me`）与统一消息服务
（`/api/v1/message/admin/me`）都返回"是否管理员 + 权限 + 当前登录用户 mid"，
因此把该结构抽到 bili-common，避免两边各自定义、字段不一致。
"""

from typing import List

from sqlmodel import Field, SQLModel


class AdminStatusResponse(SQLModel):
    """当前登录用户的角色/权限状态（任意登录用户可查）。"""

    is_root: bool = False
    is_admin: bool = False
    permissions: List[str] = Field(default_factory=list)
    mid: int = 0
