"""SQLModel 数据库表模型公共基类。

供各微服务（be-message / RPA-Browser 等）的建表模型继承，避免每个项目各自重复
定义 `created_at` / `updated_at` 时间戳字段。统一约定：

- `created_at`：创建时间，`index=True`（便于按时间排序/过滤查询复用索引）；
- `updated_at`：更新时间，行变化时由 SQLAlchemy 自动刷为当前时间（`onupdate`）。

本模块内的类均为 `table=False` 的 mixin，业务子表 `table=True` 继承并建表。
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseTimestamp(SQLModel):
    """统一创建 / 更新时间字段 mixin（`table=False`，业务子表 `table=True` 继承）。"""

    created_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        index=True,
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.now},
        description="更新时间",
    )


__all__ = ["BaseTimestamp"]