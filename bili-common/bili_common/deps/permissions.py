"""管理端细粒度权限定义（与 RPA `rpa_admin.permissions` 共用同一套字符串词表）。

设计要点：
- 权限以字符串标识，与 RPA-Browser 的 `rpa_admin.permissions` 共用同一套词表
  （`["*"]` 表示「全部权限」）。网关在转发登录态时，把当前用户被授予的权限列表
  写入 `x-bili-permissions` 请求头，下游微服务（be-message-service 等）据此做细粒度鉴权。
- `ROOT_ONLY_PERMISSIONS` 为「root 专属、不可授予其他管理员」的权限：
  查看全部评论/私信内容明文、设置过审/没过审。root 本身通过 `role=root` 隐式拥有全部权限，
  不需要也不会出现在某个管理员的 `permissions` 列表里。
- `sanitize_permissions` 供 RPA 授权接口落库前清洗，确保非 root 管理员永远拿不到
  root 专属权限（即使被授予 `["*"]` 也被 `AuthInfo.has_permission` 在鉴权时拦截）。
"""

from enum import StrEnum


class UserPermission(StrEnum):
    """管理端细粒度权限标识。"""

    # 评论管理端
    COMMENT_VIEW_QUEUE = "comment:view-queue"  # 查看评论审核队列（不含内容明文）
    COMMENT_VIEW_CONTENT = "comment:view-content"  # 查看评论内容明文（root 专属）
    COMMENT_AUDIT = "comment:audit"  # 设置过审/没过审（root 专属）

    # 私信管理端
    DM_VIEW_QUEUE = "dm:view-queue"  # 查看私信审核队列（不含内容明文）
    DM_VIEW_CONTENT = "dm:view-content"  # 查看私信内容明文（root 专属）
    DM_AUDIT = "dm:audit"  # 设置过审/没过审（root 专属）

    # 用户治理（封禁/解封，可授予其他管理员；按服务维度拆分：评论 / 私信）
    COMMENT_BAN = "comment:ban"  # 封禁 / 解封用户在评论服务
    DM_BAN = "dm:ban"  # 封禁 / 解封用户在私信服务
    USER_BAN = "user:ban"  # 封禁 / 解封用户（仅 RPA 服务，跨服务拦截）
    USER_BAN_VIEW = "user:ban-view"  # 查看封禁记录与封禁状态（跨服务）


# root 专属、不可授予其他管理员的权限集合
ROOT_ONLY_PERMISSIONS: frozenset[str] = frozenset(
    {
        UserPermission.COMMENT_VIEW_CONTENT,
        UserPermission.COMMENT_AUDIT,
        UserPermission.DM_VIEW_CONTENT,
        UserPermission.DM_AUDIT,
    }
)


# 可授予其他管理员的权限（供 RPA 授权接口 / 前端权限选择器使用）
GRANTABLE_PERMISSIONS: tuple[str, ...] = tuple(
    p.value for p in UserPermission if p.value not in ROOT_ONLY_PERMISSIONS
)


def sanitize_permissions(permissions: list[str] | None) -> list[str]:
    """剔除不可授予的 root 专属权限，返回安全的管理员权限列表。

    用于 RPA 授权接口落库前清洗，确保非 root 管理员永远不会拿到
    查看内容明文 / 设置审核的权限。
    """
    if not permissions:
        return []
    return [p for p in permissions if p not in ROOT_ONLY_PERMISSIONS]


__all__ = [
    "UserPermission",
    "ROOT_ONLY_PERMISSIONS",
    "GRANTABLE_PERMISSIONS",
    "sanitize_permissions",
]
