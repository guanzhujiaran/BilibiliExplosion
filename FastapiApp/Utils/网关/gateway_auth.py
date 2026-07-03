# -*- coding: utf-8 -*-
"""
网关用户鉴权依赖模块

Puppeteer 网关（ExpressServerEnd/Controller/ProxyEndPort.js）在转发请求到
后端子服务前，会先清除客户端传入的不可信 ``x-bili-*`` 头，再根据 JWT 解析出的
登录态重新注入可信的用户信息头（见 MiddleWare/PrefetchUserInfo.js）。

因此后端可以直接信任这些头信息来判断用户登录状态：
- 已登录：``x-bili-mid`` 为用户 UID（非空字符串）
- 未登录：``x-bili-mid`` 为空字符串

本模块提供 FastAPI 依赖，用于校验网关注入的用户信息头，确认用户有效登录态。
未登录或校验失败则拒绝访问（HTTP 401）。
"""
from typing import Dict

from fastapi import HTTPException, Request, status
from pydantic import Field
from urllib.parse import unquote

from Models.base.custom_pydantic import CustomBaseModel
from log.base_log import myfastapi_logger


class GatewayUserInfo(CustomBaseModel):
    """网关注入的用户信息（来源于 ``x-bili-*`` 请求头）"""

    mid: str = Field(default="", description="用户 UID，登录态的核心标识")
    user_name: str = Field(default="", description="用户名")
    uname: str = Field(default="", description="用户昵称")
    level: str = Field(default="", description="用户等级")
    role: str = Field(default="", description="用户角色")
    sign: str = Field(default="", description="用户签名")
    sex: str = Field(default="", description="用户性别")
    email: str = Field(default="", description="用户邮箱")
    vip_status: str = Field(default="", description="大会员状态")
    vip_type: str = Field(default="", description="大会员类型")

    @property
    def is_logged_in(self) -> bool:
        """是否处于有效登录态（mid 非空即为已登录）"""
        return bool(self.mid and self.mid.strip())


# 网关注入的用户信息头名称映射：字段名 -> 请求头名
_GATEWAY_USER_HEADER_MAP: Dict[str, str] = {
    "mid": "x-bili-mid",
    "user_name": "x-bili-user-name",
    "uname": "x-bili-uname",
    "level": "x-bili-level",
    "role": "x-bili-role",
    "sign": "x-bili-sign",
    "sex": "x-bili-sex",
    "email": "x-bili-email",
    "vip_status": "x-bili-vip-status",
    "vip_type": "x-bili-vip-type",
}

# 网关侧经过 encodeURIComponent 编码的字段，后端需做对应解码
_ENCODED_FIELDS = frozenset({"user_name", "uname", "sign", "sex", "email"})


def parse_gateway_user(request: Request) -> GatewayUserInfo:
    """从请求头中解析网关注入的用户信息。

    网关对 user_name / uname / sign / sex / email 做了 ``encodeURIComponent``
    编码，这里需要做对应的解码（``unquote``）。

    :param request: FastAPI Request 对象
    :return: 解析出的用户信息
    """
    raw: Dict[str, str] = {}
    for field_name, header_name in _GATEWAY_USER_HEADER_MAP.items():
        value = request.headers.get(header_name)
        if value is None:
            value = ""
        if field_name in _ENCODED_FIELDS and value:
            try:
                value = unquote(value)
            except Exception:
                # 解码失败时保留原始值，避免影响主流程
                pass
        raw[field_name] = value
    return GatewayUserInfo(**raw)


def require_gateway_login(request: Request) -> GatewayUserInfo:
    """FastAPI 依赖：校验网关注入的用户登录态。

    Puppeteer 网关在转发请求前会清除客户端伪造的 ``x-bili-*`` 头并重新注入
    可信用户信息。当用户未登录时，``x-bili-mid`` 为空字符串；已登录时为用户
    UID。本依赖据此判断登录态。

    用法::

        from Utils.网关.gateway_auth import require_gateway_login, GatewayUserInfo
        from fastapi import Depends

        @router.post("/xxx")
        async def some_api(user: GatewayUserInfo = Depends(require_gateway_login)):
            ...

    :param request: FastAPI Request 对象
    :return: 解析出的用户信息
    :raises HTTPException: 未登录或校验失败时抛出 401
    """
    user_info = parse_gateway_user(request)

    if not user_info.is_logged_in:
        client_ip = request.client.host if request.client else "unknown"
        myfastapi_logger.warning(
            f"网关鉴权失败：未检测到有效登录态，"
            f"路径={request.url.path} 方法={request.method} IP={client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="该接口需要登录后才能访问，请先登录",
        )

    return user_info
