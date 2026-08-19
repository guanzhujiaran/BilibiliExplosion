"""
Response Code 模块 - 统一响应码定义（单一来源）
"""

from enum import IntEnum


class ResponseCode(IntEnum):
    """
    统一响应码枚举类
    """
    # 成功
    SUCCESS = 0

    # 未登录：采用 B 站官方约定业务码 -101（注意不是 HTTP 401）。
    # 所有对外 HTTP 响应状态码恒为 200，业务状态通过 body 中的 `code` 表达，
    # 前端据此判断未登录并跳转登录页。详见 docs/response-code-design.md。
    NOT_LOGGED_IN = -101

    # 通用错误码
    BAD_REQUEST = 400
    INVALID_PARAM = 400  # 请求参数非法（与 BAD_REQUEST 同值，语义区分）
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    TOO_MANY_REQUESTS = 429

    # 服务器错误
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    # 自定义业务错误码
    BUSINESS_ERROR = 1000
    VALIDATION_ERROR = 1001
    DATABASE_ERROR = 1002
    NETWORK_ERROR = 1003
    MID_NOT_FOUND = 1004
    BROWSER_ID_NOT_FOUND = 1005
    SESSION_NOT_FOUND = 1006
    BROWSER_NOT_STARTED = 1007
    USER_NOT_FOUND = 1008  # 目标用户不存在（空间资料等单用户读接口返回，替代空列表/0/404 兜底）

    # WebRTC 相关错误码
    WEBRTC_OFFER_FAILED = 2001
    WEBRTC_ANSWER_FAILED = 2002
    WEBRTC_ICE_CANDIDATE_FAILED = 2003
    WEBRTC_CLOSE_FAILED = 2004
    WEBRTC_CONNECTION_FAILED = 2005
    WEBRTC_STATUS_FAILED = 2006
    WEBRTC_STREAM_NOT_ACTIVE = 2009

    # 截图相关错误码
    SCREENSHOT_FAILED = 2007
    PAGE_CLOSED = 2007

    # 指纹数量限制错误码
    FINGERPRINT_LIMIT_EXCEEDED = 2008

    # 浏览器/页面相关错误码
    GET_BROWSER_INFO_FAILED = 2010
    PAGE_NAVIGATION_FAILED = 2011

    # Casdoor OAuth 相关错误码
    CASDOOR_OAUTH_ERROR = 3001       # Casdoor 返回错误（如 code 过期、invalid_grant）
    CASDOOR_ENDPOINT_NOT_CONFIGURED = 3002  # Casdoor endpoint 未配置
    CASDOOR_TOKEN_PARSE_FAILED = 3003  # JWT 解析失败
    CASDOOR_USER_NOT_FOUND = 3004     # Casdoor 用户不存在
    CASDOOR_CREATE_USER_FAILED = 3005  # 创建本地用户失败


__all__ = ["ResponseCode"]
