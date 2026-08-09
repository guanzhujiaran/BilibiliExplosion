"""
分页请求参数与分页响应模型（统一公共定义，基于 sqlmodel）

各微服务（如 be-bilibili-crawler）的分页入参与分页结果统一复用此模块，
避免各项目重复定义导致字段/校验不一致。
"""

from typing import Generic, TypeVar

from sqlmodel import SQLModel, Field

T = TypeVar("T")  # 泛型类型 T


class ResponsePaginationItems(SQLModel, Generic[T]):
    """分页响应：数据列表与总记录数"""

    items: list[T]
    total: int


class RequestPaginationParams(SQLModel):
    """基于页码的分页请求参数"""

    page_num: int = Field(
        default=1, ge=1, description="页码，从 1 开始，最小值为 1",
        schema_extra={
            "filter_display_name": "页码",
            "filter_widget": "number",
            "filter_description": "分页页码，从 1 开始",
            "filter_placeholder": "输入页码",
        },
    )  # 页码，默认第 1 页，从 1 开始，最小值为 1
    page_size: int = Field(
        default=10, ge=1, description="每页数量，最小值为 1",
        schema_extra={
            "filter_display_name": "每页条数",
            "filter_widget": "number",
            "filter_description": "每页返回数量",
            "filter_placeholder": "输入每页条数",
        },
    )  # 每页数量，默认 10 条，最小值为 1


class RequestCursorParams(SQLModel):
    """基于游标的分页请求参数"""

    cursor: str | None = Field(
        default=None, description="游标值，用于定位下一页起始位置"
    )  # 游标值，用于定位下一页起始位置
    size: int = Field(
        default=20, ge=1, description="每页数量，最小值为 1"
    )  # 每页数量，默认 20 条，最小值为 1


class RequestOffsetLimitParams(SQLModel, Generic[T]):
    """基于偏移量的分页请求参数（泛型，可携带额外的过滤条件类型 T）"""

    offset: int = Field(
        default=0, ge=0, description="偏移量，最小值为 0"
    )  # 偏移量，默认从 0 开始，最小值为 0
    limit: int = Field(
        default=20, ge=1, description="限制返回数量，最小值为 1"
    )  # 限制返回数量，默认 20 条，最小值为 1


__all__ = [
    "ResponsePaginationItems",
    "RequestPaginationParams",
    "RequestCursorParams",
    "RequestOffsetLimitParams",
]
