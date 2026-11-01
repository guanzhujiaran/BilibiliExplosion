"""雪花 ID 入参统一类型：StrInt。

业务含义：对外雪花 ID（19 位十进制）在 JSON 中一律以**字符串**传递（前端避免
JS ``Number`` 精度丢失），后端在入口处统一归一为 ``int``（Python 任意精度无损），
避免每个 router / service 手写 ``int(...)``。

- 输入 ``str``（如 ``"134236897319"``）→ 自动 ``int(...)`` 归一
- 输入 ``int`` → 原样（兼容内部调用方与历史存量客户端）
- 输出（序列化）始终为 ``int``

与 :mod:`bili_common.models.auto_str` 的分工：

- **入参**（前端 → 后端）：用 ``StrInt``，接收字符串，归一为 int；
- **出参**（后端 → 前端）：用 ``@auto_str`` 声明 int 字段 + 自动派生 ``xxx_str``
  字符串版，前端只消费字符串版。

⚠️ **路由参数必须用 ``Annotated[StrInt, Query(...)]`` 形式声明**：写成默认值形式
``x: StrInt = Query(...)`` 时，FastAPI 会**丢掉 BeforeValidator**，查询参数的字符串
会原样透传给 handler，``if mid <= 0`` 直接抛
``TypeError: '<=' not supported between instances of 'str' and 'int'`` → 500
（HTTP 查询参数在线上永远是字符串，即这类路由任何调用都会 500）。两种写法的
OpenAPI schema 完全一致（均为 ``anyOf[int, str]``），改写不影响已生成的前端 SDK。
路径参数（``x: StrInt``）与 pydantic 模型字段（``x: StrInt = Field(...)``）不受影响。
回归测试见 ``be-message-service/tests/test_str_int_route_params.py``。
"""

from typing import Annotated, Union

from pydantic import BeforeValidator


def _coerce_snowflake(v):
    # bool 是 int 子类，但绝不可能是合法雪花 ID，显式拒绝避免误判
    if isinstance(v, bool):
        raise ValueError("bool is not a valid snowflake id")
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError(f"invalid snowflake id string: {v!r}")
    if isinstance(v, float):
        return int(v)
    raise ValueError(f"cannot coerce {type(v).__name__} to snowflake id")


StrInt = Annotated[Union[int, str], BeforeValidator(_coerce_snowflake)]

__all__ = ["StrInt"]
