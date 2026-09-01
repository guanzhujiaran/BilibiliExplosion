"""管理端细粒度权限定义（与 RPA `rpa_admin.permissions` 共用同一套字符串词表）。

设计要点：
- ``UserPermission`` 为**整数枚举**（`IntEnumAutoDoc`），每个权限对应一个稳定 int 值，
  便于落库 / 比对 / 序列化，且 Swagger 自动渲染「枚举选项：name: value」；
- 网关 / RPA 在线上仍使用「字符串令牌」（如 ``comment:audit``）互通，由本模块的
  ``WIRE_TOKEN`` 在字符串令牌与整数枚举值之间双向映射；
- ``ROOT_ONLY_PERMISSIONS`` 为「root 专属、不可授予其他管理员」的权限（按 int 值）；
- ``sanitize_permissions`` 供 RPA 授权接口落库前清洗，入参 / 出参均为字符串令牌列表，
  确保非 root 管理员永远拿不到 root 专属权限（即使被授予 ``["*"]`` 也被拦截）。
"""

from typing import Iterable

from bili_common.models import IntEnumAutoDoc


class UserPermission(IntEnumAutoDoc):
    """管理端细粒度权限标识（整数枚举）。"""

    # 评论管理端
    COMMENT_VIEW_QUEUE = 1  # 查看评论审核队列（不含内容明文）
    COMMENT_VIEW_CONTENT = 2  # 查看评论内容明文（root 专属）
    COMMENT_AUDIT = 3  # 设置过审/没过审（root 专属）

    # 私信管理端
    DM_VIEW_QUEUE = 4  # 查看私信审核队列（不含内容明文）
    DM_VIEW_CONTENT = 5  # 查看私信内容明文（root 专属）
    DM_AUDIT = 6  # 设置过审/没过审（root 专属）

    # 用户治理（封禁/解封，可授予其他管理员；按服务维度拆分：评论 / 私信）
    COMMENT_BAN = 7  # 封禁 / 解封用户在评论服务
    DM_BAN = 8  # 封禁 / 解封用户在私信服务
    USER_BAN = 9  # 封禁 / 解封用户（仅 RPA 服务，跨服务拦截）
    USER_BAN_VIEW = 10  # 查看封禁记录与封禁状态（跨服务）


# 线令牌 ↔ 枚举成员 映射：网关 / RPA 在线使用字符串令牌，内部逻辑使用整数枚举值。
WIRE_TOKEN: dict[str, UserPermission] = {
    "comment:view-queue": UserPermission.COMMENT_VIEW_QUEUE,
    "comment:view-content": UserPermission.COMMENT_VIEW_CONTENT,
    "comment:audit": UserPermission.COMMENT_AUDIT,
    "dm:view-queue": UserPermission.DM_VIEW_QUEUE,
    "dm:view-content": UserPermission.DM_VIEW_CONTENT,
    "dm:audit": UserPermission.DM_AUDIT,
    "comment:ban": UserPermission.COMMENT_BAN,
    "dm:ban": UserPermission.DM_BAN,
    "user:ban": UserPermission.USER_BAN,
    "user:ban-view": UserPermission.USER_BAN_VIEW,
}


def resolve_permission_value(perm: "str | int | UserPermission") -> int | None:
    """把任意形式的权限描述归一为整数枚举值。

    - ``UserPermission`` 成员 → 其 ``.value``；
    - ``int`` → 若为合法枚举值则原样返回；
    - ``str`` → 匹配 ``WIRE_TOKEN`` 线令牌；无法识别返回 ``None``。
    """
    if isinstance(perm, UserPermission):
        return int(perm.value)
    if isinstance(perm, int):
        try:
            return int(UserPermission(perm).value)
        except ValueError:
            return None
    if isinstance(perm, str):
        mapped = WIRE_TOKEN.get(perm)
        return int(mapped.value) if mapped is not None else None
    return None


# root 专属、不可授予其他管理员的权限集合（按 int 值）
ROOT_ONLY_PERMISSIONS: frozenset[int] = frozenset(
    {
        UserPermission.COMMENT_VIEW_CONTENT.value,
        UserPermission.COMMENT_AUDIT.value,
        UserPermission.DM_VIEW_CONTENT.value,
        UserPermission.DM_AUDIT.value,
    }
)


# 可授予其他管理员的权限（供 RPA 授权接口 / 前端权限选择器使用），返回整数枚举值
GRANTABLE_PERMISSIONS: tuple[int, ...] = tuple(
    p.value for p in UserPermission if p.value not in ROOT_ONLY_PERMISSIONS
)


def sanitize_permissions(permissions: list[str] | None) -> list[str]:
    """剔除不可授予的 root 专属权限，返回安全的管理员权限列表（线令牌格式）。

    用于 RPA 授权接口落库前清洗，确保非 root 管理员永远不会拿到
    查看内容明文 / 设置审核的权限。入参 / 出参均为线令牌字符串。
    """
    if not permissions:
        return []
    safe: list[str] = []
    for token in permissions:
        value = resolve_permission_value(token)
        if value is None or value in ROOT_ONLY_PERMISSIONS:
            continue
        safe.append(token)
    return safe


__all__ = [
    "UserPermission",
    "WIRE_TOKEN",
    "resolve_permission_value",
    "ROOT_ONLY_PERMISSIONS",
    "GRANTABLE_PERMISSIONS",
    "sanitize_permissions",
]
