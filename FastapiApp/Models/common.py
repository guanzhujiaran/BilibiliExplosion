from typing import TypeVar, Generic, Optional
from pydantic import Field
from Models.base.custom_pydantic import CustomBaseModel

T = TypeVar("T")  # 泛型类型 T


class CommonResponseModel(CustomBaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T | None = None


class ResponsePaginationItems(CustomBaseModel, Generic[T]):
    items: list[T]
    total: int


class RequestPaginationParams(CustomBaseModel):
    """基于页码的分页请求参数"""

    page_num: int = Field(
        default=1, ge=1, description="页码，从 1 开始，最小值为 1",
        json_schema_extra={
            "filter_display_name": "页码",
            "filter_widget": "number",
            "filter_description": "分页页码，从 1 开始",
            "filter_placeholder": "输入页码",
        },
    )  # 页码，默认第 1 页，从 1 开始，最小值为 1
    page_size: int = Field(
        default=10, ge=1, description="每页数量，最小值为 1",
        json_schema_extra={
            "filter_display_name": "每页条数",
            "filter_widget": "number",
            "filter_description": "每页返回数量",
            "filter_placeholder": "输入每页条数",
        },
    )  # 每页数量，默认 10 条，最小值为 1


class RequestCursorParams(CustomBaseModel):
    """基于游标的分页请求参数"""

    cursor: Optional[str] = Field(
        default=None, description="游标值，用于定位下一页起始位置"
    )  # 游标值，用于定位下一页起始位置
    size: int = Field(
        default=20, ge=1, description="每页数量，最小值为 1"
    )  # 每页数量，默认 20 条，最小值为 1


class RequestOffsetLimitParams(CustomBaseModel):
    """基于偏移量的分页请求参数"""

    offset: int = Field(
        default=0, ge=0, description="偏移量，最小值为 0"
    )  # 偏移量，默认从 0 开始，最小值为 0
    limit: int = Field(
        default=20, ge=1, description="限制返回数量，最小值为 1"
    )  # 限制返回数量，默认 20 条，最小值为 1
