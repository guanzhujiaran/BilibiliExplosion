"""通用 IntEnum 基类（bili-common 自包含，不依赖具体业务项目）。

所有对外枚举（出现在响应 / 请求 DTO 的枚举）都应继承 :class:`IntEnumAutoDoc`，
从而 Swagger / OpenAPI 自动展示「枚举选项：name: value」列表，**无需在每个枚举上
重复手写 description**。

仅依赖标准库 ``enum`` 与 pydantic 约定的 ``__get_pydantic_json_schema__`` 方法，
自包含、不依赖任何业务模型，避免与 ``bili_common.models`` 产生循环依赖。
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class StrEnumAutoDoc(StrEnum):
    """StrEnum 基类：自动把枚举选项写入 OpenAPI / JSON Schema 的 description。

    与 :class:`IntEnumAutoDoc` 一致，子类直接 ``class Foo(StrEnumAutoDoc): A = "a"`` 即可，
    Swagger 会自动渲染：

        枚举选项：
        - A: a
        - B: b
    """

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        # 先获取默认的 schema
        schema = handler(core_schema)
        # 添加包含键值对的描述
        schema["description"] = "枚举选项：\n" + "\n".join(
            [f"- {item.name}: {item.value}" for item in cls]
        )
        schema["x-enum-varnames"] = [choice.name for choice in cls]
        return schema


class IntEnumAutoDoc(IntEnum):
    """IntEnum 基类：自动把枚举选项写入 OpenAPI / JSON Schema 的 description。

    子类直接 ``class Foo(IntEnumAutoDoc): A = 1`` 即可，Swagger 会自动渲染：

        枚举选项：
        - A: 1
        - B: 2
    """

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        # 先获取默认的 schema
        schema = handler(core_schema)
        # 添加包含键值对的描述
        schema["description"] = "枚举选项：\n" + "\n".join(
            [f"- {item.name}: {item.value}" for item in cls]
        )
        schema["x-enum-varnames"] = [choice.name for choice in cls]

        return schema


__all__ = ["IntEnumAutoDoc", "StrEnumAutoDoc"]
