"""deps: 依赖注入函数（FastAPI Header 等）"""

from bili_common.deps.auth import get_auth_info_from_header

__all__ = ["get_auth_info_from_header"]
