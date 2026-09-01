"""通用「雪花 ID 自动生成 *Str 字符串字段」Mixin（bili-common 通用类）。

背景
----
雪花 ID 实际为 19 位十进制，超过 JS ``Number`` 安全整数 ``2^53-1``，前端以 number
传递 / 存储会**静默丢精度**。因此对外响应 DTO 必须把雪花 ID 同时以字符串形式暴露
（如 ``mid`` -> ``midStr``），前端只消费字符串版，避免精度丢失。

本 Mixin 通过 Pydantic V2 的 ``computed_field`` + ``__init_subclass__``，在类定义时
自动为「雪花 ID 数值字段」注入 ``<field>Str`` 计算属性：

- **自动序列化**：``model_dump()`` 自动带上 ``*Str``，无需手动赋值；
- **文档可见**：FastAPI 的 OpenAPI 响应 schema 会包含 ``*Str``（已验证）；
- **零冗余**：不需要在每个模型里手写 ``xxxStr: str = ...``；
- **通用**：仅依赖 pydantic，不依赖 SQLModel，因此 SQLModel 与纯 pydantic 响应模型均可继承。

命名
----
``<原字段名> + "Str"``（与项目既有 ``dynIdStr`` / ``midStr`` 等约定一致），不用下划线。

如何判定「哪些字段是雪花 ID」（避免误伤计数 / 时间戳 / 等级等非 ID 数值）：
1. 显式标记（推荐）：字段类型用 :data:`SnowflakeInt`；
2. 子类用类属性 ``_auto_str`` 指定白名单；
3. 默认兜底：对所有 ``int`` / ``float`` 字段，仅当字段名命中 ID 命名模式（见
   ``_ID_NAME_SUFFIXES`` / ``_ID_NAME_EXACT``）且不在非 ID 黑名单（``_NON_ID_NAMES``）时生成。

示例
----
::

    from sqlmodel import SQLModel
    from bili_common.models.auto_str import AutoStrMixin, SnowflakeInt

    class FollowOpResp(SQLModel, AutoStrMixin):
        mid: SnowflakeInt          # 标记 -> 自动生成 midStr
        target_mid: int            # 命中 mid 后缀 -> 自动生成 target_midStr
        like_count: int            # 非 ID -> 不生成
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, get_args, get_origin

from pydantic import Field as _PydField
from pydantic import computed_field

# ---------------------------------------------------------------------------
# 雪花 ID 标记类型：仅作注解标记，运行时仍是 int，便于基类识别「这是雪花 ID」
# ---------------------------------------------------------------------------
SnowflakeInt = Annotated[int, _PydField(description="雪花 ID（int，另自动提供 <field>Str 字符串版）")]
"""注解标记：声明某 int 字段为雪花 ID（运行时仍是普通 int，另自动提供 ``*Str``）。"""

# ---------------------------------------------------------------------------
# 命名模式：命中这些名字的 int/float 字段视为雪花 ID（兜底，默认开启）
# ---------------------------------------------------------------------------
_ID_NAME_SUFFIXES = (
    "mid",
    "uid",
    "oid",
    "rpid",
    "msgkey",
    "dialog",
)
_ID_NAME_EXACT = {
    "parent",
    "root",
    "talker_mid",
    "sender_mid",
    "receiver_mid",
    "target_mid",
    "operator_mid",
    "actor_mid",
    "creator_mid",
    "up_mid",
}

# 非 ID 数值字段（计数 / 时间戳 / 等级 / 经验 / 分页等保持 number，不生成 *Str）
_NON_ID_NAMES = {
    "count",
    "total",
    "timestamp",
    "ts",
    "level",
    "exp",
    "page",
    "page_num",
    "page_size",
    "pagesize",
    "ps",
    "size",
    "limit",
    "offset",
    "floor",
    "rcount",
    "unread",
    "code",
    "status",
    "duration_days",
    "msg_ts",
    "like_count",
    "hate_count",
    "following_count",
    "follower_count",
    "mutual_count",
    "seq",
    "version",
    "pk",
    "id",            # 内部自增主键（裸 id），非对外雪花 ID
    "notify_id",     # 通知记录内部 id
    "create_time",
    "update_time",
    "created_at",
    "updated_at",
}


def _is_id_field(name: str, annotation: Any) -> bool:
    """判断字段是否为雪花 ID（用于默认兜底模式）。"""
    if name.endswith("Str"):
        return False
    if name in _NON_ID_NAMES:
        return False
    if name in _ID_NAME_EXACT:
        return True
    # 大小写不敏感匹配以 id/Id/ID 结尾（item_id / topicId / bizId / commentId ...）
    if name.lower().endswith("id") and name != "id":
        return True
    if any(name.endswith(suf) for suf in _ID_NAME_SUFFIXES):
        return True
    return False


class AutoStrMixin:
    """为响应模型自动注入 ``*Str`` 计算字段的基类。

    子类只需 ``class X(SQLModel, AutoStrMixin)``（或 ``class X(BaseModel, AutoStrMixin)``）
    并照常声明 ID 字段即可。可通过类属性微调行为：

    - ``_auto_str``：仅对这些字段名生成（白名单，优先级最高）；
    - ``_auto_str_skip``：跳过这些字段名（黑名单）；
    - ``_auto_str_all``：``True`` 时对所有 int/float 生成（不推荐，可能命中非 ID 数值）。
    """

    # 这些由子类选择性覆盖；基类置空避免实例属性冲突
    _auto_str: ClassVar[list[str]] = []
    _auto_str_skip: ClassVar[set[str]] = set()
    _auto_str_all: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # __annotations__ 在 __init_subclass__ 时已填充，且比 model_fields 可靠
        # （pydantic 的 ModelMetaclass 在 __init_subclass__ 之后才填充 model_fields）
        annotations: dict[str, Any] = dict(getattr(cls, "__annotations__", {}))

        auto_str: list[str] = list(getattr(cls, "_auto_str", []) or [])
        skip: set[str] = set(getattr(cls, "_auto_str_skip", []) or [])
        all_mode: bool = bool(getattr(cls, "_auto_str_all", False))

        for fname, fanno in annotations.items():
            if fname.endswith("Str"):
                continue
            if fname in skip:
                continue

            # 拆包取底层数值类型：支持 Annotated[...] 与 Optional[...]/Union[...]
            base_type = fanno
            if get_origin(fanno) is Annotated:
                _args = get_args(fanno)
                base_type = _args[0] if _args else fanno
            _origin = get_origin(base_type)
            if _origin is not None and _origin is not Annotated:
                # Optional[X] / Union[...] -> 取第一个非 None 的参数
                _union_args = [a for a in get_args(base_type) if a is not type(None)]
                if _union_args:
                    base_type = _union_args[0]

            # 标记类型（SnowflakeInt）无论命名都生成
            is_marked = fanno is SnowflakeInt

            explicit = fname in auto_str
            default_ok = all_mode or _is_id_field(fname, base_type)
            # 仅对数值（int/float）生成
            is_numeric = base_type in (int, float)

            if not is_numeric:
                continue
            if not (is_marked or explicit or default_ok):
                continue

            str_name = f"{fname}Str"
            # 若该类或其父类已显式声明过同名 *Str 字段（如既有手动 bizIdStr），
            # 则跳过自动注入，避免与既有字段冲突（保留手动字段）
            if hasattr(cls, str_name):
                continue

            def _make_prop(src_name: str) -> Any:
                @computed_field
                @property
                def _prop(self: Any) -> str | None:
                    val = getattr(self, src_name)
                    return str(val) if val is not None else None

                return _prop

            setattr(cls, str_name, _make_prop(fname))


__all__ = ["AutoStrMixin", "SnowflakeInt"]
