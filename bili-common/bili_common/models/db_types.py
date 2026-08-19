"""通用 SQLAlchemy 列类型工具（枚举列映射，避免各业务系统重复实现）。"""

from enum import IntEnum, StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator


def str_enum_type(enum_cls: type[StrEnum], length: int = 16) -> SAEnum:
    """把 StrEnum 映射成 VARCHAR 列（通用，2.18.0 统一收口到 bili-common）。

    用 SQLModel 默认行为会生成 MySQL 原生 ENUM 且存成员名（`LIKE`），新增枚举值要改表结构、
    库内字面量与接口对不上。这里统一处理：

    - `native_enum=False`：落成 `VARCHAR(length)`，加枚举值不需要 DDL；
    - `values_callable`：存枚举的 **value**（如 `like`），与接口层一致；
    - 读取时 SQLAlchemy 仍还原成枚举成员，业务代码可放心用 `is` 比较。
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )


class _IntEnumColumn(TypeDecorator):
    """把 IntEnum 映射成 INTEGER 列，存其 **value**（1/2/3…）。

    注意：SQLModel / SQLAlchemy 对 IntEnum 字段的**默认**映射是 `Enum`（VARCHAR 存成员名，
    如 `DYNAMIC`），并非 int。要落 INTEGER 存 value 必须显式使用本类型（2.23.0 起
    `InteractionBizTypeEnum` 等交互资源类型统一走此映射，DB 存 int 减小存储空间）。

    - `impl = Integer`：落库为整数，加枚举值无需 DDL；
    - 读写经 `value` 互转，业务侧仍拿到枚举成员，可用 `is` 比较。
    """

    impl = Integer

    # 类型状态固定、可安全进入 SQLAlchemy 语句缓存（消除 cache_ok 警告）
    cache_ok = True

    def __init__(self, enum_cls: type[IntEnum], **kw):
        self.enum_cls = enum_cls
        super().__init__(**kw)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value if isinstance(value, IntEnum) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # MySQL 驱动对 INTEGER 列可能返回 str（如 '1'），统一 int 化后再按值还原枚举成员
        return self.enum_cls(int(value))


def int_enum_type(enum_cls: type[IntEnum]) -> _IntEnumColumn:
    """构造一个存 IntEnum value 的 INTEGER 列类型。"""
    return _IntEnumColumn(enum_cls)


__all__ = ["int_enum_type", "str_enum_type"]
