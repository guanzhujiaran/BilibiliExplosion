"""
公共认证相关异常（自包含，不依赖具体业务项目的 BaseException 体系）

get_auth_info_from_header 需要能够抛出这些异常，因此公共包自带最小集合。
"""

from fastapi import HTTPException


class NotLoggedInException(HTTPException):
    """用户未登录"""

    def __init__(self):
        super().__init__(status_code=401, detail="未登录，请提供有效的x-bili-mid请求头")


class InvalidUIDException(HTTPException):
    """无效的用户ID"""

    def __init__(self):
        super().__init__(status_code=400, detail="无效的用户ID，请重新登录")


class InvalidMidFormatException(HTTPException):
    """无效的 MID 格式"""

    def __init__(self):
        super().__init__(status_code=400, detail="Invalid mid format in x-bili-mid header")


__all__ = [
    "NotLoggedInException",
    "InvalidUIDException",
    "InvalidMidFormatException",
]
