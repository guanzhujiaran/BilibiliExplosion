"""RPC 服务端公共装饰器：把 handler 异常翻译成 `error_response` 回包。

FastStream 0.7.1 在 RPC handler 抛异常时不会向 reply_to 发送任何响应，
导致客户端（如 be-gateway 的 amqplib）永久等待直至超时（RpcTimeoutError）。
为维持请求/响应契约，服务端必须在边界捕获异常并返回结构化错误信封
（而非吞错），客户端据此立即得到错误结果而非超时。

注意：业务 / service 层仍保持「直接抛错、不静默」的约定；此处只是在
RPC 传输边界把异常翻译成回包，不构成错误屏蔽。

使用方需自行保证环境具备 loguru（be-message-service / be-bilibili-crawler
等 RPC 服务端均已依赖）。
"""

import traceback
from functools import wraps

from bili_common.models.response import error_response
from loguru import logger


def rpc_safe(func):
    """RPC 边界：捕获 handler 异常并转为 error_response 回包。"""

    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            # 打印完整 traceback 与详细错误信息，便于定位。
            # 注意：Pydantic 的 ValidationError 默认 str 仅显示首个错误字段，
            # 过于简略，这里额外展开 errors() 拿到完整的字段 / 类型 / 原因列表。
            # 堆栈用 traceback.format_exc() 显式获取并字符串化，避免依赖 loguru 的
            # exception=True（在 async / 事件循环上下文中可能拿不到活跃异常而丢堆栈）。
            detail = str(e)
            _errors = getattr(e, "errors", None)
            if callable(_errors):
                try:
                    detail = f"{detail} | errors={_errors()}"
                except Exception:  # noqa: BLE001
                    pass
            stack = traceback.format_exc()
            logger.error(
                "RPC {} 失败: {}: {}\n{}\n------ traceback ------\n{}",
                func.__name__,
                type(e).__name__,
                e,
                detail,
                stack,
            )
            # 业务异常若自带 code（如 ResourceConflictException 的 409），优先保留其业务码，
            # 其余异常统一归为 500，避免前端拿到 500 却实为「昵称冲突」等可识别错误。
            code = getattr(e, "code", None) or 500
            return error_response(code=code, msg=f"{type(e).__name__}: {e}")

    return _wrapper


__all__ = ["rpc_safe"]
