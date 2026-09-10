"""
公共认证/业务异常（单一来源，供各后端统一使用）

设计约定（HTTP 状态码契约）：
- **失败一律返回非 200 的 HTTP 状态码**，成功才返回 2xx（HTTP 状态码只表达
  「大类」，不要求与业务码 `body.code` 同值）；
- 业务状态仍通过响应体 body 中的 `code` 字段表达（参考 B 站官方约定，
  例如未登录 code = -101），前端按 `body.code` 做业务分支；
- HTTP 状态码由 `http_status_for_code()` 从业务码推导：
  400~599 直接沿用；-101（未登录）→ 401；其余自定义业务码（1000+/2000+/4001+ 等）
  统一 400；未捕获异常 500。

本模块同时提供：
- `BaseException`：统一业务异常基类（非 200 HTTP + {code, msg, data}）。
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
# 业务码 → HTTP 状态码映射（HTTP 状态只表达错误大类，无需与业务码同值）
# ==========================================================================
# 业务异常的默认 HTTP 状态码（自定义业务码如 1004 / 2008 / 4001 / 4101 等，
# 语义上都是「请求被拒」，统一按 400 处理）。
DEFAULT_ERROR_HTTP_STATUS = 400


def http_status_for_code(code: Any, default: int = DEFAULT_ERROR_HTTP_STATUS) -> int:
    """由业务码推导对外 HTTP 状态码（保证非 2xx，且落在合法 HTTP 区间）。

    规则：
    - `code` 为 0/None（成功语义）→ 200；
    - `-101`（未登录）→ 401；其余负数码 → 400；
    - 400~599 → 直接沿用（与 HTTP 语义天然一致，如 404/409/429/500/503）；
    - 其他自定义业务码（1000+ / 2001+ / 4001+ / 4101+ …）→ `default`（默认 400）。
    """
    try:
        code_int = int(code)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if code_int == ResponseCode.SUCCESS:
        return 200
    if code_int == ResponseCode.NOT_LOGGED_IN:
        return 401
    if 400 <= code_int <= 599:
        return code_int
    return default


# ==========================================================================
# 业务异常基类（统一以「非 200 HTTP + body.code」返回）
# ==========================================================================
class BaseException(Exception):
    """统一业务异常基类。

    约定：对外 HTTP 状态码**必须非 200**（由 `http_status` 指定，缺省则按
    `http_status_for_code(code)` 推导），业务状态仍由 body 的 `code` 表达。
    子类通过覆盖 `code` / `msg` / `data` / `http_status` 描述具体异常。
    """

    code: int = ResponseCode.SUCCESS
    msg: str = "ok"
    data: Any = None
    #: 对外 HTTP 状态码；None 表示按 code 推导（见 `http_status_for_code`）
    http_status: Optional[int] = None

    def __init__(
        self,
        msg: Optional[str] = None,
        data: Any = None,
        code: Optional[int] = None,
        http_status: Optional[int] = None,
    ) -> None:
        if msg is not None:
            self.msg = msg
        if data is not None:
            self.data = data
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.msg)

    @property
    def status_code(self) -> int:
        """对外 HTTP 状态码（兼容旧引用；保证非 200）。"""
        status = (
            self.http_status
            if self.http_status is not None
            else http_status_for_code(self.code)
        )
        # 业务异常代表失败：推导结果若仍是 2xx，一律回退为 400
        return status if status >= 400 else DEFAULT_ERROR_HTTP_STATUS

    def to_response(self) -> dict:
        # 延迟翻译：在请求上下文执行期才调用 _()，按当前语言翻译 msg
        return {"code": self.code, "msg": _(self.msg), "data": self.data}


class NotLoggedInException(BaseException):
    """用户未登录（缺少 / 非法 x-bili-mid 请求头）。

    业务码 -101（B 站官方「未登录」约定），HTTP 状态码 401。
    全局异常处理器据此生成：
    HTTP 401 {"code": -101, "msg": "未登录，请提供有效的x-bili-mid请求头", "data": null}
    """

    code = ResponseCode.NOT_LOGGED_IN  # -101
    msg = "未登录，请提供有效的x-bili-mid请求头"
    http_status = 401


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
# 约定（各后端统一遵循，勿在业务代码里把错误响应压回 200）：
# - **失败一律非 200**：HTTP 状态码只表达错误大类，无需与 body.code 同值；
# - 业务类异常（BaseException）：HTTP 状态码 = `http_status`（缺省按 code 推导，
#   兜底 400），body 仍为 {code, msg, data}；
# - HTTP 请求类异常（StarletteHTTPException）：HTTP 状态码 = 原异常的 status_code
#   （本身即为非 200，如 401/403/404/405 等），body 仍为 {code, msg, data}；
# - 参数校验失败（RequestValidationError）：HTTP 400；
# - 其他未捕获异常（Exception，全局兜底）：HTTP 500 + error_id。
# ==========================================================================
def _business_exception_handler(_req: object, exc: BaseException) -> JSONResponse:
    # 业务类异常：HTTP 状态码非 200（显式 http_status 优先，否则按 code 推导）
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


def _http_exception_handler(
    _req: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # HTTP 请求类异常：HTTP 状态码 = 原异常的 status_code（非 200），
    # 仅 body 包装为统一 {code, msg, data} 契约。
    code = getattr(exc, "code", None) or exc.status_code
    # 日志分级：5xx 才打 error + 堆栈（需排查），4xx（404/401/403 …）属客户端错误，
    # 仅打一行 warning，避免探测请求/未登录场景刷屏。
    # 注意：loguru 的 sink 默认 format 不含 {exception}，传 exc_info 也不会打印堆栈，
    # 因此这里手动 format_exception 拼进 message（对所有服务生效，不依赖日志配置）。
    if exc.status_code >= 500:
        tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(
            f"HTTP {exc.status_code} error: {exc.detail} "
            f"[{_req.method} {_req.url.path}]\n{tb_text}"
        )
    else:
        logger.warning(
            f"HTTP {exc.status_code} error: {exc.detail} "
            f"[{_req.method} {_req.url.path}]"
        )
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
    # 注意：不能用 traceback.format_exc()（依赖 sys.exc_info()）——在 Starlette/FastAPI 中
    # 异常跨 await 边界传播到处理器时 sys.exc_info() 已为空，会打印出 "NoneType: None" 丢堆栈；
    # 必须基于异常对象自身的 __traceback__ 显式构造。
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(
        f"Unhandled error (ID: {error_id}) {type(exc).__name__}: {exc} "
        f"route={getattr(request, 'method', '')} {getattr(request, 'url', '')}\n{tb}"
    )

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

    统一契约（失败一律非 200）：
    - 业务异常（BaseException）→ 非 200（http_status 或按 code 推导，兜底 400）+ {code, msg, data}；
    - HTTP 异常（StarletteHTTPException）→ 原 status_code（401/403/404/…）+ {code, msg, data}；
    - 参数校验失败（RequestValidationError）→ HTTP 400 + {code: 400, msg, data}；
    - 未捕获异常（Exception，全局兜底）→ HTTP 500 + {code: 500, msg, data}（含 error_id，DEV 带 traceback）。

    各后端（be-message-service / be-bilibili-crawler / RPA-Browser 等）统一调用本函数即可，
    避免各项目各自实现一套错误处理中间件导致契约不一致。
    """
    app.add_exception_handler(BaseException, _business_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)


def register_http_exception_handlers(app) -> None:
    """仅注册 HTTP 请求类异常的处理器（StarletteHTTPException / 参数校验）。

    用于后端已有自己的 `Exception` 兜底处理器（如 be-bilibili-crawler 带告警推送），
    只希望把 401/403/404 等 HTTP 异常与参数校验失败归一化为
    {code, msg, data} + 非 200 状态码的场景。
    """
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(BaseException, _business_exception_handler)


def register_business_exception_handlers(app) -> None:
    """仅注册 bili_common 业务异常处理器（BaseException）。

    用于后端已自行处理 StarletteHTTPException / RequestValidationError，
    但仍希望 bili_common 业务异常（如 NotLoggedInException → HTTP 401 +
    code -101）以统一契约 {code, msg, data} 返回的场景（例如 RPA-Browser）。
    """
    app.add_exception_handler(BaseException, _business_exception_handler)


__all__ = [
    "BaseException",
    "NotLoggedInException",
    "BiliException",
    "InvalidUIDException",
    "InvalidMidFormatException",
    "ResourceConflictException",
    "http_status_for_code",
    "DEFAULT_ERROR_HTTP_STATUS",
    "register_exception_handlers",
    "register_http_exception_handlers",
    "register_business_exception_handlers",
]
