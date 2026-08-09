"""
公共认证/业务异常（单一来源，供各后端统一使用）

设计约定（详见 docs/response-code-design.md）：
- 所有对外 HTTP 响应状态码恒为 200；
- 业务状态通过响应体 body 中的 `code` 字段表达（参考 B 站官方约定，
  例如未登录 code = -101）；
- 因此「未登录」等认证异常是「业务异常」（HTTP 200），而非 HTTP 401 异常。

本模块同时提供：
- `BaseException`：统一业务异常基类（HTTP 200 + {code, msg, data}）。
- 一批预置业务异常（如 `NotLoggedInException`）。
- `register_exception_handlers(app)`：一键注册统一异常处理器，
  让各后端以同一套契约对外返回。
"""

from typing import Any, Optional

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.responses import JSONResponse

from bili_common.models.response_code import ResponseCode


# ==========================================================================
# 业务异常基类（统一以 HTTP 200 返回，业务码在 body.code）
# ==========================================================================
class BaseException(Exception):
    """统一业务异常基类。

    约定：对外 HTTP 状态码恒为 200，业务状态由 body 的 `code` 表达。
    子类通过覆盖 `code` / `msg` / `data` / `status_code` 描述具体异常。
    """

    code: int = ResponseCode.SUCCESS
    msg: str = "ok"
    data: Any = None
    status_code: int = 200

    def __init__(
        self,
        msg: Optional[str] = None,
        data: Any = None,
        code: Optional[int] = None,
    ) -> None:
        if msg is not None:
            self.msg = msg
        if data is not None:
            self.data = data
        if code is not None:
            self.code = code
        super().__init__(self.msg)

    def to_response(self) -> dict:
        return {"code": self.code, "msg": self.msg, "data": self.data}


class NotLoggedInException(BaseException):
    """用户未登录（缺少 / 非法 x-bili-mid 请求头）。

    业务码 -101（B 站官方「未登录」约定），HTTP 状态码固定 200。
    全局异常处理器据此生成：
    {"code": -101, "msg": "未登录，请提供有效的x-bili-mid请求头", "data": null}
    """

    code = ResponseCode.NOT_LOGGED_IN  # -101
    msg = "未登录，请提供有效的x-bili-mid请求头"
    status_code = 200


# ==========================================================================
# HTTP 异常辅助类（用于需要携带 HTTP 状态码语义、但仍归一化为 {code,msg,data} 的场景）
# ==========================================================================
class BiliException(HTTPException):
    """基础 HTTP 异常，附带业务码 `code` 供异常处理器读取。"""

    code: int = ResponseCode.INTERNAL_ERROR

    def __init__(self, status_code: int, detail: str, code: int | None = None) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code if code is not None else status_code


class InvalidUIDException(BiliException):
    """无效的用户ID"""

    def __init__(self, uid: str | None = None):
        msg = f"uid 格式非法: {uid}" if uid else "uid 格式非法"
        super().__init__(status_code=400, detail=msg, code=ResponseCode.INVALID_PARAM)


class InvalidMidFormatException(BiliException):
    """无效的 MID 格式"""

    def __init__(self, mid: str | None = None):
        msg = f"mid 格式非法: {mid}" if mid else "mid 格式非法"
        super().__init__(status_code=400, detail=msg, code=ResponseCode.INVALID_PARAM)


class ResourceConflictException(BiliException):
    """资源冲突（HTTP 409）。

    用于业务上需要返回 409 的场景（如昵称已被占用）。自带 `code` 属性，
    供 RPC 边界（rpc_safe）与 HTTP 全局异常处理器还原为统一响应体的业务码。
    """

    def __init__(self, detail: str = "资源冲突"):
        super().__init__(status_code=409, detail=detail, code=409)


# ==========================================================================
# 统一异常处理器
# ==========================================================================
def _business_exception_handler(_: object, exc: BaseException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


def _http_exception_handler(_: object, exc: StarletteHTTPException) -> JSONResponse:
    # 业务码优先（异常自带 code），否则回退到 HTTP 状态码；
    # 无论如何 HTTP 状态码统一为 200，业务状态在 body.code 表达。
    code = getattr(exc, "code", None) or exc.status_code
    return JSONResponse(
        status_code=200,
        content={"code": code, "msg": str(exc.detail), "data": None},
    )


def _validation_exception_handler(_: object, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": ResponseCode.INVALID_PARAM,
            "msg": "请求参数校验失败",
            "data": exc.errors(),
        },
    )


def register_exception_handlers(app) -> None:
    """在 FastAPI 应用上注册 bili_common 统一异常处理。

    统一契约：业务异常 / HTTP 异常 / 参数校验 均返回 HTTP 200 + {code, msg, data}。
    适用于以 bili_common 为唯一异常来源的后端（如 be-message-service）。

    注意：若后端已有自己覆盖 StarletteHTTPException / RequestValidationError
    的处理器（例如 RPA-Browser），请勿调用本函数，改用
    register_business_exception_handlers 仅注册业务异常处理器。
    """
    app.add_exception_handler(BaseException, _business_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)


def register_business_exception_handlers(app) -> None:
    """仅注册 bili_common 业务异常处理器（BaseException）。

    用于后端已自行处理 StarletteHTTPException / RequestValidationError，
    但仍希望 bili_common 业务异常（如 NotLoggedInException）以统一契约
    （HTTP 200 + {code, msg, data}）返回的场景（例如 RPA-Browser）。
    """
    app.add_exception_handler(BaseException, _business_exception_handler)


__all__ = [
    "BaseException",
    "NotLoggedInException",
    "BiliException",
    "InvalidUIDException",
    "InvalidMidFormatException",
    "ResourceConflictException",
    "register_exception_handlers",
    "register_business_exception_handlers",
]
