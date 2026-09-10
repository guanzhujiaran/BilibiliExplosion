"""middlewares: 公共 HTTP 中间件（统一响应契约相关）"""

from bili_common.middlewares.error_status import (
    ErrorStatusMiddleware,
    add_error_status_middleware,
)

__all__ = ["ErrorStatusMiddleware", "add_error_status_middleware"]
