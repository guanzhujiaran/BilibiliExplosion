"""
公共认证/业务异常（单一来源，供各后端统一使用）

设计约定（详见 docs/response-code-design.md）：
- 除参数校验失败（HTTP 400）外，所有对外 HTTP 响应状态码恒为 200；
- 业务状态通过响应体 body 中的 `code` 字段表达（参考 B 站官方约定，
  例如未登录 code = -101）；
- 因此「未登录」等认证异常是「业务异常」（HTTP 200），而非 HTTP 401 异常。

本模块同时提供：
- `BaseException`：统一业务异常基类（HTTP 200 + {code, msg, data}）。
- 一批预置业务异常（如 `NotLoggedInException`）。
- `register_exception_handlers(app)`：一键注册统一异常处理器，
  让各后端以同一套契约对外返回（含全局兜底 Exception 处理器）。
"""

import traceback
import uuid
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from bili_common.i18n import _
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
        # 延迟翻译：在请求上下文执行期才调用 _()，按当前语言翻译 msg
        return {"code": self.code, "msg": _(self.msg), "data": self.data}


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
        msg = _("uid 格式非法: {uid}") if uid else _("uid 格式非法")
        if uid:
            msg = msg.format(uid=uid)
        super().__init__(status_code=400, detail=msg, code=ResponseCode.INVALID_PARAM)


class InvalidMidFormatException(BiliException):
    """无效的 MID 格式"""

    def __init__(self, mid: str | None = None):
        msg = _("mid 格式非法: {mid}") if mid else _("mid 格式非法")
        if mid:
            msg = msg.format(mid=mid)
        super().__init__(status_code=400, detail=msg, code=ResponseCode.INVALID_PARAM)


class ResourceConflictException(BiliException):
    """资源冲突（HTTP 409）。

    用于业务上需要返回 409 的场景（如昵称已被占用）。自带 `code` 属性，
    供 RPC 边界（rpc_safe）与 HTTP 全局异常处理器还原为统一响应体的业务码。
    """

    def __init__(self, detail: str = "资源冲突"):
        super().__init__(status_code=409, detail=_(detail), code=409)


# ==========================================================================
# 统一异常处理器（HTTP 状态码契约，全项目唯一标准）
# ==========================================================================
# 约定（各后端统一遵循，勿在业务代码里覆盖 status_code）：
# - 业务类异常（BaseException）：HTTP 状态码一律为 200（业务状态在 body.code 表达），
#   严禁将业务异常 status_code 设为非 200 —— 否则网关/监控会把它误判为协议层错误；
# - HTTP 请求类异常（StarletteHTTPException）：HTTP 状态码使用**原异常的 status_code**
#   （必须为非 200，如 404/405 等），仅响应体 body 仍保持 {code, msg, data} 统一契约；
# - 参数校验失败（RequestValidationError）：HTTP 400（与业务码 INVALID_PARAM=400 一致）；
# - 其他未捕获异常（Exception，全局兜底）：HTTP 500 + error_id。
# ==========================================================================
def _business_exception_handler(_req: object, exc: BaseException) -> JSONResponse:
    # 业务类异常：HTTP 状态码恒为 200（默认/显式），不得改非 200
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


def _http_exception_handler(
    _req: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # HTTP 请求类异常：HTTP 状态码 = 原异常的 status_code（必须非 200），
    # 仅 body 包装为统一 {code, msg, data} 契约。
    code = getattr(exc, "code", None) or exc.status_code
    # 5xx 属服务器错误，打印日志便于排查；4xx 为客户端错误，warning 级提示
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} error: {exc.detail}")
    else:
        logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "msg": _(str(exc.detail)), "data": None},
    )


def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # 参数校验失败：HTTP 状态码固定 400（与业务码 INVALID_PARAM=400 保持一致），
    # 便于网关/监控/前端 axios 按状态码归类错误。
    # 打印校验失败明细（含路由 + 缺失/非法字段），便于排查调用方传参问题。
    path = getattr(request, "url", None)
    method = getattr(request, "method", None)
    route_info = f" [{method} {path}]" if (path and method) else ""
    logger.warning(f"Validation error{route_info}: {exc.errors()}")
    return JSONResponse(
        status_code=ResponseCode.INVALID_PARAM,
        content={
            "code": ResponseCode.INVALID_PARAM,
            "msg": _("请求参数校验失败"),
            "data": exc.errors(),
        },
    )


def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局兜底：处理所有未捕获异常（非 BaseException / HTTPException / 参数校验）。

    统一契约（HTTP 500 + {code: 500, msg, data}）：
    - 生成 `error_id` 便于日志与响应关联追踪；
    - 完整 traceback 记录到服务端日志；
    - DEV 环境把错误详情放入 `data` 便于本地排查，生产仅返回 error_id。
    """
    error_id = str(uuid.uuid4())
    tb = traceback.format_exc()
    logger.error(f"Unhandled error (ID: {error_id}) {type(exc).__name__}: {exc}\n{tb}")

    # 尽力带上路由信息（异常上下文拿不到时可缺省）
    path = getattr(request, "url", None)
    method = getattr(request, "method", None)
    route_info = f" [{method} {path}]" if (path and method) else ""

    # DEV 判定：优先 FastAPI 实例 debug 标志（app.debug），其次 app.state.debug
    is_dev = bool(
        getattr(request.app, "debug", False)
        or getattr(getattr(request.app, "state", None), "debug", False)
    )
    data: Any = None
    if is_dev:
        data = {
            "error_id": error_id,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": tb,
            "route": route_info.strip() or None,
        }

    return JSONResponse(
        status_code=int(ResponseCode.INTERNAL_ERROR),
        content={
            "code": int(ResponseCode.INTERNAL_ERROR),
            "msg": _("服务器内部错误 (错误ID: {error_id})").format(error_id=error_id),
            "data": data,
        },
    )


def register_exception_handlers(app) -> None:
    """在 FastAPI 应用上注册 bili_common 统一异常处理（全项目统一标准）。

    统一契约：
    - 业务异常（BaseException）→ HTTP 200 + {code, msg, data}；
    - HTTP 异常（StarletteHTTPException）→ HTTP 200 + {code, msg, data}（业务码在 body.code）；
    - 参数校验失败（RequestValidationError）→ HTTP 400 + {code: 400, msg, data}（与业务码一致）；
    - 未捕获异常（Exception，全局兜底）→ HTTP 500 + {code: 500, msg, data}（含 error_id，DEV 带 traceback）。

    各后端（be-message-service / be-bilibili-crawler / RPA-Browser 等）统一调用本函数即可，
    避免各项目各自实现一套错误处理中间件导致契约不一致。
    """
    app.add_exception_handler(BaseException, _business_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)


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
