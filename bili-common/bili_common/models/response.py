"""
Response 模块 - 统一响应模型和辅助函数（使用 sqlmodel 替代 pydantic）
"""

from typing import Any, Generic, TypeVar
from sqlmodel import SQLModel
from bili_common.models.response_code import ResponseCode

DataT = TypeVar("DataT")


class StandardResponse(SQLModel, Generic[DataT]):
    """统一响应格式"""

    code: int = 0
    msg: str = "success"
    data: DataT | None = None


def success_response(data: Any = None, msg: str = "success") -> StandardResponse[Any]:
    """
    构建成功响应

    Args:
        data: 响应数据
        msg: 响应消息

    Returns:
        StandardResponse: 标准成功响应对象
    """
    return StandardResponse(code=ResponseCode.SUCCESS, data=data, msg=msg)


def error_response(
    code: ResponseCode | int, msg: str, data: Any = None
) -> StandardResponse[Any]:
    """
    构建错误响应

    Args:
        code: 错误码，推荐使用 ResponseCode 枚举
        msg: 错误消息
        data: 错误数据

    Returns:
        StandardResponse: 标准错误响应对象
    """
    # 如果传入的是枚举，转换为 int
    code_value = code.value if isinstance(code, ResponseCode) else code
    return StandardResponse(code=code_value, data=data, msg=msg)


def custom_response(
    code: ResponseCode | int, msg: str, data: Any = None
) -> StandardResponse[Any]:
    """
    构建自定义响应

    Args:
        code: 响应码，推荐使用 ResponseCode 枚举
        msg: 响应消息
        data: 响应数据

    Returns:
        StandardResponse: 标准响应对象
    """
    # 如果传入的是枚举，转换为 int
    code_value = code.value if isinstance(code, ResponseCode) else code
    return StandardResponse(code=code_value, data=data, msg=msg)


__all__ = [
    "StandardResponse",
    "success_response",
    "error_response",
    "custom_response",
    "DataT",
]
