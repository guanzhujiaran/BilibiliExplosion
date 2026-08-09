"""整型字段字符串互转 mixin（应对 Node.js Number 精度问题）。

- 反序列化（JS -> Python）：before-validator 把字符串 "87" 解析为 int 87，
  JS 端可用字符串传大整数而不丢精度；
- 序列化（Python -> JS）：field_serializer('*') 把 int 字段再转回字符串，网络上
  始终以字符串传输，JS 端用 String 接收，不会被 Number 截断。

用法：让模型继承本 mixin，并声明类属性 `_int_fields_: ClassVar[tuple[str, ...]]`
列出所有整型字段名。
"""

from typing import ClassVar

from pydantic import field_serializer, model_validator
from sqlmodel import SQLModel


class _IntStrMixin(SQLModel):
    """整型字段在 (反) 序列化时与字符串互转的 mixin。"""

    _int_fields_: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="before")
    def _coerce_ints(cls, data):  # noqa: N805
        int_fields = getattr(cls, "_int_fields_", ())
        if isinstance(data, dict):
            for f in int_fields:
                if f in data and data[f] not in (None, ""):
                    try:
                        data[f] = int(str(data[f]).strip())
                    except (TypeError, ValueError):
                        pass
        return data

    @field_serializer("*")
    def _serialize_ints(self, value, _info):
        if _info.field_name in getattr(type(self), "_int_fields_", ()) and isinstance(value, int):
            return str(value)
        return value
