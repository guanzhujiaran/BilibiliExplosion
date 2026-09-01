"""
Depends 模块 - 认证相关模型（基于 sqlmodel，自包含）

用于安全校验和参数验证的模型定义。
AuthInfo 为 pptr 转发 x-bili-* 请求头的统一模型（各微服务共用同一结构）。
"""

from sqlmodel import SQLModel, Field
from pydantic import field_validator
from bili_common.core.browser import BaseBrowserId, BaseUserMid
from bili_common.deps.permissions import (
    ROOT_ONLY_PERMISSIONS,
    UserPermission,
    resolve_permission_value,
)


class AuthInfo(SQLModel):
    """认证信息（来自 pptr 转发的 x-bili-* 请求头，统一模型）

    字段与 RPA-Browser / nodejs-pptr ProxyEndPort.setUserHeaders 注入的请求头一一对应。

    细粒度权限 `permissions` 与 RPA-Browser 的 `rpa_admin.permissions` 共用同一套词表
    （`["*"]` 表示全部权限），由网关经 `x-bili-permissions` 请求头转发；root 恒为 `["*"]`。
    """

    # 用户唯一 ID（B 站 mid）
    mid: int
    # 用户等级
    level: int = 0
    # 角色：root / normal
    role: str = "normal"
    # 细粒度权限列表（与 RPA rpa_admin.permissions 同一套词表，`["*"]` 表示全部）。
    # 由网关经 x-bili-permissions 请求头转发；root 恒为 ["*"]。
    permissions: list[str] = Field(default_factory=list)
    # 登录用户名
    user_name: str | None = None
    # 用户昵称（uname）
    uname: str | None = None
    # 个性签名
    sign: str | None = None
    # 性别
    sex: str | None = None
    # 邮箱
    email: str | None = None
    # 大会员状态
    vip_status: str | None = None
    # 大会员类型
    vip_type: str | None = None

    @field_validator("mid", "level", mode="before")
    @classmethod
    def _coerce_int(cls, v):
        """容错：字符串形式的 mid / level 自动转为 int"""
        if v is None or v == "":
            return v
        return int(v)

    @property
    def is_root(self) -> bool:
        """是否为 root 管理员（role=root）。"""
        return self.role == "root"

    def has_permission(self, perm: "str | int | UserPermission") -> bool:
        """是否拥有某权限。

        - root 恒拥有全部权限；
        - root 专属权限（`ROOT_ONLY_PERMISSIONS`）即使持有 `*` 也只对 root 放行；
        - 其余按 `permissions` 列表判断（`*` 通配）。

        `perm` 支持三种形式：线令牌字符串（如 ``"comment:audit"``）、
        ``UserPermission`` 枚举成员、或整数枚举值（如 ``3``）；统一经
        ``resolve_permission_value`` 归一为整数值再比对。
        """
        if self.is_root:
            return True
        value = resolve_permission_value(perm)
        if value is None:
            return False
        if value in ROOT_ONLY_PERMISSIONS:
            return False
        perms = self.permissions or []
        if "*" in perms:
            return True
        granted = {resolve_permission_value(p) for p in perms}
        return value in granted

    def has_any_permission(self, *perms: "str | int | UserPermission") -> bool:
        return any(self.has_permission(p) for p in perms)


class VerifyBrowserDependsReq(BaseBrowserId):
    """验证浏览器所有权的请求模型"""

    ...


class BrowserReqInfo(BaseUserMid, BaseBrowserId):
    """浏览器请求信息模型"""

    ...


class BrowserReqAuthInfo(BaseBrowserId):
    auth_info: AuthInfo


class VerifyPluginDependsReq(VerifyBrowserDependsReq):
    """验证插件所有权的请求模型"""

    plugin_id: int | str

    @field_validator("plugin_id", mode="before")
    @classmethod
    def validate_plugin_id(cls, v):
        """将字符串类型的plugin_id转换为整数"""
        if isinstance(v, str):
            return int(v)
        return v


class BrowserPluginReqInfo(BrowserReqInfo):
    """浏览器插件请求信息模型"""

    plugin_id: int
