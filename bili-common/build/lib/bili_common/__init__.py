"""bili-common: Bilibili 公共认证与统一响应模型包"""

from bili_common.models.response_code import ResponseCode
from bili_common.models.response_msg import ResponseMsg
from bili_common.models.response import StandardResponse
from bili_common.models.depends import AuthInfo
from bili_common.deps.auth import UserRole, get_auth_info_from_header

__all__ = [
    "ResponseCode",
    "ResponseMsg",
    "StandardResponse",
    "AuthInfo",
    "UserRole",
    "get_auth_info_from_header",
]
