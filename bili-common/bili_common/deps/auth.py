"""
Mid 相关依赖注入函数（公共认证入口，自包含）
"""

import json
from enum import Enum, IntEnum
from typing import Annotated, List
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import SQLModel

from bili_common.models.depends import AuthInfo
from bili_common.exceptions import (
    NotLoggedInException,
    InvalidUIDException,
    InvalidMidFormatException,
)


class UserRole(str, Enum):
    """用户角色枚举"""

    ROOT = "root"
    NORMAL = "normal"


class UserLevel(IntEnum):
    """用户等级枚举"""

    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6

    @classmethod
    def from_string(cls, level_str: str) -> "UserLevel":
        """从字符串解析等级"""
        level_map = {
            "0": cls.LEVEL_0,
            "1": cls.LEVEL_1,
            "2": cls.LEVEL_2,
            "3": cls.LEVEL_3,
            "4": cls.LEVEL_4,
            "5": cls.LEVEL_5,
            "6": cls.LEVEL_6,
        }
        return level_map.get(level_str.lower(), cls.LEVEL_0)  # 默认为最低等级


class Permission(IntEnum):
    """权限枚举"""

    PERMISSION_0 = 0
    PERMISSION_1 = 1
    PERMISSION_2 = 2
    PERMISSION_3 = 3
    PERMISSION_4 = 4
    PERMISSION_5 = 5
    PERMISSION_6 = 6


class LevelPermissions:
    """等级权限映射"""

    LEVEL_0: List[int] = [0, 1, 2, 3, 4, 5, 6]
    LEVEL_1: List[int] = [1, 2, 3, 4, 5, 6]
    LEVEL_2: List[int] = [2, 3, 4, 5, 6]
    LEVEL_3: List[int] = [3, 4, 5, 6]
    LEVEL_4: List[int] = [4, 5, 6]
    LEVEL_5: List[int] = [5, 6]
    LEVEL_6: List[int] = [6]

    @staticmethod
    def get_permissions(level: int) -> List[int]:
        """获取指定等级的权限列表"""
        if level == 0:
            return LevelPermissions.LEVEL_0
        elif level == 1:
            return LevelPermissions.LEVEL_1
        elif level == 2:
            return LevelPermissions.LEVEL_2
        elif level == 3:
            return LevelPermissions.LEVEL_3
        elif level == 4:
            return LevelPermissions.LEVEL_4
        elif level == 5:
            return LevelPermissions.LEVEL_5
        elif level == 6:
            return LevelPermissions.LEVEL_6
        else:
            return LevelPermissions.LEVEL_0  # 默认最低权限


def get_auth_info_from_header(
    x_bili_mid: str | None = Header(default=None),
    x_bili_level: str | None = Header(default=None),
    x_bili_role: str = Header(default="normal"),
    x_bili_permissions: str | None = Header(default=None),
    x_bili_user_name: str = Header(default=None),
    x_bili_uname: str = Header(default=None),
    x_bili_sign: str = Header(default=None),
    x_bili_sex: str = Header(default=None),
    x_bili_email: str = Header(default=None),
    x_bili_vip_status: str = Header(default=None),
    x_bili_vip_type: str = Header(default=None),
) -> AuthInfo:
    """
    从请求头中获取认证信息并验证用户是否已登录

    Args:
        x_bili_mid: 请求头中的x-bili-mid字段（必填）
        x_bili_level: 请求头中的x-bili-level字段（字符串格式，如 "level0", "level1"）
        x_bili_role: 请求头中的x-bili-role字段（角色标识，如 "root", "normal"）
        x_bili_permissions: 请求头中的x-bili-permissions字段（权限列表 JSON 字符串，
            与 RPA rpa_admin.permissions 同一套词表，`["*"]` 表示全部；由网关转发）
        x_bili_user_name/uname/sign/sex/email/vip_status/vip_type: pptr 转发的其他用户信息头

    Returns:
        AuthInfo: 包含 pptr 转发头全部字段的统一认证信息对象

    Raises:
        NotLoggedInException: 当用户未登录时抛出
        InvalidUIDException: 当用户ID无效时抛出
        InvalidMidFormatException: 当mid格式无效时抛出
    """
    if not x_bili_mid:
        raise NotLoggedInException()

    # 验证mid是否为有效的数字字符串并转换为int
    try:
        mid_int = int(x_bili_mid)
    except ValueError as e:
        raise InvalidMidFormatException() from e

    # 解析level字符串（如 "level0" -> UserLevel.LEVEL_0）
    level_enum = (
        UserLevel.from_string(x_bili_level) if x_bili_level else UserLevel.LEVEL_0
    )
    level_int = level_enum.value

    # 解析role，仅允许已定义的角色值，其余一律视为普通用户
    role = x_bili_role.strip().lower() if x_bili_role else UserRole.NORMAL.value
    if role != UserRole.ROOT.value:
        role = UserRole.NORMAL.value

    # 解析细粒度权限列表（由网关经 x-bili-permissions 转发）
    permissions: list[str] = []
    if x_bili_permissions:
        try:
            parsed = json.loads(x_bili_permissions)
            if isinstance(parsed, list):
                permissions = [str(p) for p in parsed]
        except (json.JSONDecodeError, TypeError, ValueError):
            permissions = []
    # root 恒拥有全部权限
    if role == UserRole.ROOT.value and "*" not in permissions:
        permissions = ["*"]

    return AuthInfo(
        mid=mid_int,
        level=level_int,
        role=role,
        permissions=permissions,
        user_name=x_bili_user_name,
        uname=x_bili_uname,
        sign=x_bili_sign,
        sex=x_bili_sex,
        email=x_bili_email,
        vip_status=x_bili_vip_status,
        vip_type=x_bili_vip_type,
    )


def get_admin_user(
    auth: Annotated[AuthInfo, Depends(get_auth_info_from_header)],
) -> AuthInfo:
    """管理员依赖：仅 role=root 可访问。

    先经通用解析拿到已登录用户（缺 x-bili-mid 即抛 401），再叠加管理员角色校验。
    """
    if auth.role != UserRole.ROOT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行该操作"
        )
    return auth


# 路由函数签名中直接使用的依赖注解类型
AdminUser = Annotated[AuthInfo, Depends(get_admin_user)]


def require_root(
    auth: Annotated[AuthInfo, Depends(get_auth_info_from_header)],
) -> AuthInfo:
    """root 专属依赖：仅 role=root 可访问。

    用于「查看全部评论/私信内容明文」「设置过审/没过审」等敏感操作，
    其余管理员（即使被授予其他细粒度权限）一律 403。
    """
    if not auth.is_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅 root 管理员可执行该操作",
        )
    return auth


def require_admin(
    auth: Annotated[AuthInfo, Depends(get_auth_info_from_header)],
) -> AuthInfo:
    """管理员依赖：root 或拥有任一被授予细粒度权限的管理员可访问。

    用于审核队列 / 统计等「非敏感」管理端能力；查看内容明文与设置审核仍需 root 专属权限。
    """
    if auth.is_root or auth.permissions:
        return auth
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要管理员权限",
    )


def require_permission(*perms: str):
    """细粒度权限依赖工厂：当前用户需拥有 perms 中至少一个权限（root 恒通过）。

    用法：
        user: Annotated[AuthInfo, Depends(require_permission("comment:audit"))]
    """

    def _dep(
        auth: Annotated[AuthInfo, Depends(get_auth_info_from_header)],
    ) -> AuthInfo:
        if auth.has_any_permission(*perms):
            return auth
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )

    return _dep
