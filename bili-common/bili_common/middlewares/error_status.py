"""错误响应 HTTP 状态码归一化中间件。

背景：业务代码里大量使用「返回响应体 + 非 0 业务码」表达失败，例如
`return StandardResponse(code=400, msg="...")`；FastAPI 默认仍以 HTTP 200 返回，
与「失败一律返回非 200」的契约不一致。逐处改写成 JSONResponse 成本过高，
故由本中间件在**响应出口统一兜底**：

- 仅处理 2xx 且 content-type 为 JSON 的响应；
- 解析 body 顶层 `code`，`code == 0`（成功）原样返回；
- `code != 0` → 按 `http_status_for_code()` 推导 HTTP 状态码（400~599 沿用、
  -101 → 401、其余业务码 → 400），重写状态码后返回，body 内容不变。

这样：异常路径（异常处理器）+ 手写返回路径（StandardResponse）两条链路
对外表现一致，前端/网关可只按 HTTP 状态码判断是否失败。
"""

import json
from typing import Iterable, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from bili_common.exceptions import http_status_for_code
from bili_common.models.response_code import ResponseCode

# 默认跳过：文档 / schema / 健康检查等不承载业务码的端点
DEFAULT_SKIP_PATHS: Set[str] = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/docs/oauth2-redirect",
    "/health",
}
# 只对小于该体积的响应做 JSON 解析，避免大列表被反复序列化
DEFAULT_MAX_BODY_SIZE = 1 << 20  # 1MB


class ErrorStatusMiddleware(BaseHTTPMiddleware):
    """把「HTTP 2xx 但 body.code != 0」的响应改写为对应的非 200 状态码。"""

    def __init__(
        self,
        app: ASGIApp,
        *,
        skip_paths: Optional[Iterable[str]] = None,
        skip_prefixes: Optional[Iterable[str]] = None,
        max_body_size: int = DEFAULT_MAX_BODY_SIZE,
    ) -> None:
        super().__init__(app)
        self.skip_paths = set(skip_paths) if skip_paths else set(DEFAULT_SKIP_PATHS)
        self.skip_prefixes = tuple(skip_prefixes or ())
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path
        if path in self.skip_paths or path.startswith(self.skip_prefixes):
            return response
        # 只处理「成功」响应：失败响应已由异常处理器带上非 200 状态码
        if not (200 <= response.status_code < 300):
            return response
        if "application/json" not in response.headers.get("content-type", ""):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
            if len(body) > self.max_body_size:
                return self._rebuild(response, body, response.status_code)

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._rebuild(response, body, response.status_code)

        if not isinstance(payload, dict):
            return self._rebuild(response, body, response.status_code)

        code = payload.get("code")
        if not isinstance(code, int) or isinstance(code, bool):
            return self._rebuild(response, body, response.status_code)
        if code == ResponseCode.SUCCESS:
            return self._rebuild(response, body, response.status_code)

        return self._rebuild(response, body, http_status_for_code(code))

    @staticmethod
    def _rebuild(response: Response, body: bytes, status_code: int) -> Response:
        """用原 headers 重建响应（body 未变，仅可改状态码）。"""
        headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in ("content-length", "transfer-encoding")
        }
        return Response(
            content=body,
            status_code=status_code,
            headers=headers,
            media_type=response.media_type,
        )


def add_error_status_middleware(app, **kwargs) -> None:
    """在 FastAPI/Starlette 应用上挂载 `ErrorStatusMiddleware`。

    注意：Starlette 的 `add_middleware` 把中间件插在最外层，若服务还有其他
    HTTP 中间件（如 GZipMiddleware），请按需调整挂载顺序。
    """
    app.add_middleware(ErrorStatusMiddleware, **kwargs)
