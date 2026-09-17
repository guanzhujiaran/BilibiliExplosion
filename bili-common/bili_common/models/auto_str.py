"""通用「雪花 ID 自动派生字符串字段」工具类（bili-common 通用类）。

背景
----
雪花 ID 实际为 19 位十进制，超过 JS ``Number`` 安全整数 ``2^53-1``，前端以 number
传递 / 存储会**静默丢精度**。因此对外响应 DTO 必须把雪花 ID 同时以字符串形式暴露
（如 ``mid`` -> ``midStr``），前端只消费字符串版，避免精度丢失。

本模块自动为「雪花 ID 数值字段」注入 ``<field><suffix>`` 计算属性（suffix 默认
``Str``，可配 ``_str``）：

- **自动序列化**：``model_dump()`` 自动带上字符串版，无需手动赋值；
- **文档可见**：FastAPI 的 OpenAPI 响应 schema 会包含该字段（序列化模式）；
- **零冗余**：不需要在每个模型里手写 ``xxxStr: str = ...``；
- **通用**：仅依赖 pydantic，SQLModel 与纯 pydantic 响应模型都能用。

两种用法
--------
1. **类装饰器（推荐）**：::

       from bili_common.models.auto_str import auto_str

       @auto_str
       class FollowOpResp(SQLModel):
           mid: SnowflakeInt          # 标记 -> 自动生成 midStr
           target_mid: int            # 命中 mid 后缀 -> 自动生成 target_midStr
           like_count: int            # 非 ID -> 不生成

   ``@auto_str(suffix="_str")`` 切成 snake_case 风格。装饰器在**类创建完成之后**
   注入，因此类属性（含裸赋值）都能读到，**没有读取时机坑**。

2. **Mixin（遗留，仍可用）**：``class X(SQLModel, AutoStrMixin)``。注入发生在
   ``__init_subclass__``（pydantic 收集 decorators 之前），⚠️ 配置必须用
   ``ClassVar`` 标注，否则读不到，详见 :class:`AutoStrMixin` 文档。

实现说明（为什么装饰器要重建 decorators）
-----------------------------------------
``computed_field`` 是在类创建**之后**才 ``setattr`` 上去的，而 pydantic 的
``__pydantic_decorators__`` 在 ``ModelMetaclass.__new__`` 里只 build **一次**
（``pydantic/_internal/_model_construction.py``），``model_rebuild()`` 只重新生成
core schema，**不会**重新扫描类字典。实测：只 ``setattr`` + ``model_rebuild()``，
``model_dump()`` 与 OpenAPI 里都看不到新字段。因此必须：::

    model_cls.__pydantic_decorators__ = DecoratorInfos.build(model_cls)
    model_cls.model_rebuild(force=True)

命名
----
``<原字段名> + 后缀``，后缀优先级：装饰器 ``suffix=`` 参数 > 类属性
``_auto_str_suffix`` > 默认 ``"Str"``：

- 默认 ``"Str"``（与项目既有 ``dynIdStr`` / ``midStr`` 等 camelCase 约定一致）；
- 出参整体为 snake_case 的模型可用 ``"_str"``（``mid`` -> ``mid_str``）。

**同一接口内不得混用两种后缀**；默认后缀是全局破坏性开关，禁止为单个模型改默认值。

如何判定「哪些字段是雪花 ID」（避免误伤计数 / 时间戳 / 等级等非 ID 数值）：
0. 可选（``X | None``）字段按内层类型判定，同样派生，字符串版出参为 ``str | None``
   （如 ``bizId: StrInt | None`` -> ``bizIdStr: str | None``）；
1. 显式标记（推荐）：字段类型用 :data:`SnowflakeInt`，或装饰器传 ``marker_type``；
2. ``fields=`` 白名单（优先级高于命名兜底）；
3. 默认兜底：对所有 ``int`` / ``float`` 字段，仅当字段名命中 ID 命名模式（见
   ``_ID_NAME_SUFFIXES`` / ``_ID_NAME_EXACT``）且不在非 ID 黑名单（``_NON_ID_NAMES``）时生成。
"""

from __future__ import annotations

import inspect
import sys
import types
from typing import Annotated, Any, ClassVar, Union, get_args, get_origin, get_type_hints

from pydantic import Field as _PydField
from pydantic import computed_field

try:  # pydantic 私有 API：重建 decorators 的唯一入口（见模块文档「实现说明」）
    from pydantic._internal._decorators import DecoratorInfos
except ImportError:  # pragma: no cover - pydantic 内部结构变更时的显式报错
    DecoratorInfos = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# 雪花 ID 标记类型：仅作注解标记，运行时仍是 int，便于识别「这是雪花 ID」
# ---------------------------------------------------------------------------
SnowflakeInt = Annotated[
    int, _PydField(description="雪花 ID（int，另自动提供 <field>Str 字符串版）")
]
"""注解标记：声明某 int 字段为雪花 ID（运行时仍是普通 int，另自动提供 ``*Str``）。"""

# SnowflakeInt 的 Annotated 元数据实例（全局唯一，用于按身份识别标记）
_SNOWFLAKE_META: Any = get_args(SnowflakeInt)[1]

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
    "id",  # 内部自增主键（裸 id），非对外雪花 ID
    "notify_id",  # 通知记录内部 id
    "create_time",
    "update_time",
    "created_at",
    "updated_at",
}

# 字符串版字段的常见后缀：命中则说明该字段本身就是某个 ID 的字符串版，不再二次生成
_STRING_FIELD_SUFFIXES = ("Str", "_str")


# ---------------------------------------------------------------------------
# 注解处理
# ---------------------------------------------------------------------------
def _unwrap_annotation(annotation: Any) -> Any:
    """剥掉 ``Annotated[...]`` 与 ``Optional[...]`` / ``X | None``，取底层类型。"""
    base = annotation
    if get_origin(base) is Annotated:
        args = get_args(base)
        if args:
            base = args[0]
    if get_origin(base) in (Union, types.UnionType):
        # 联合类型：只要某个成员（含嵌套 Annotated）是 int/float 就按数值处理
        # - ``int | None``        -> int
        # - ``StrInt``（Union[int, str]）-> int
        # - ``StrInt | None``     -> int（递归进 Annotated 再拆一层）
        # 派生出的字符串版本身就是 ``str | None``，可选 ID 同样适用
        for arg in get_args(base):
            if arg is type(None):
                continue
            unwrapped = _unwrap_annotation(arg)
            if unwrapped in (int, float):
                return unwrapped
        non_none = [a for a in get_args(base) if a is not type(None)]
        if non_none:
            base = non_none[0]
    return base


def _is_numeric(annotation: Any) -> bool:
    """是否数值字段（仅 int / float 会派生字符串版）。"""
    return _unwrap_annotation(annotation) in (int, float)


def _has_marker(annotation: Any, marker_type: Any) -> bool:
    """注解的 ``Annotated`` 元数据里是否带指定标记（支持嵌套 / Optional 递归）。"""
    origin = get_origin(annotation)

    if origin is Annotated:
        args = get_args(annotation)
        if not args:
            return False
        for metadata in args[1:]:
            if metadata is marker_type:
                return True
            try:
                if isinstance(metadata, marker_type):  # type: ignore[arg-type]
                    return True
            except TypeError:  # marker_type 不是类型（如某个实例标记）
                pass
        return _has_marker(args[0], marker_type)

    if origin in (Union, types.UnionType):
        return any(
            _has_marker(x, marker_type)
            for x in get_args(annotation)
            if x is not type(None)
        )

    return False


def _is_snowflake_marked(annotation: Any) -> bool:
    """是否用 :data:`SnowflakeInt` 显式标记（无论字段名是否像 ID）。"""
    if annotation is SnowflakeInt:
        return True
    return _has_marker(annotation, _SNOWFLAKE_META)


def _own_annotations(model_cls: type) -> dict[str, Any]:
    """取模型**自身**声明的注解；字符串注解（PEP 563）尽量解析成真实类型。

    只用自身注解、不用 ``get_type_hints`` 的全量结果：避免把基类字段也算进来，
    导致改造前后派生字段集合发生变化。
    """
    raw: dict[str, Any] = dict(inspect.get_annotations(model_cls))
    if not raw:
        return {}
    if not any(isinstance(v, str) for v in raw.values()):
        return raw
    try:
        resolved = get_type_hints(model_cls, include_extras=True)
    except (NameError, TypeError, AttributeError):
        # 前向引用 / TYPE_CHECKING 下的名字解析不了：退回原始注解（最坏情况少生成）
        return raw
    return {name: resolved.get(name, anno) for name, anno in raw.items()}


def _is_id_field(name: str) -> bool:
    """判断字段是否为雪花 ID（用于默认兜底模式）。"""
    if name.endswith(_STRING_FIELD_SUFFIXES):
        return False
    if name in _NON_ID_NAMES:
        return False
    if name in _ID_NAME_EXACT:
        return True
    # 大小写不敏感匹配以 id/Id/ID 结尾（item_id / topicId / bizId / commentId ...）
    if name.lower().endswith("id") and name != "id":
        return True
    return any(name.endswith(suf) for suf in _ID_NAME_SUFFIXES)


def _make_property(src_name: str) -> Any:
    """生成返回字符串版 ID 的 ``computed_field`` 属性。"""

    @computed_field
    @property
    def _auto_str_prop(self: Any) -> str | None:
        val = getattr(self, src_name)
        return str(val) if val is not None else None

    return _auto_str_prop


# ---------------------------------------------------------------------------
# 注入核心（装饰器与 mixin 共用）
# ---------------------------------------------------------------------------
def _inject_str_fields(
    model_cls: type,
    *,
    fields: set[str],
    skip: set[str],
    all_numeric: bool,
    suffix: str,
    marker_type: Any,
) -> bool:
    """为 ``model_cls`` 注入字符串版计算字段，返回是否发生了注入。"""
    changed = False

    for name, annotation in _own_annotations(model_cls).items():
        if name.startswith("_"):
            continue
        if name.endswith(_STRING_FIELD_SUFFIXES):
            continue
        if name in skip:
            continue
        if not _is_numeric(annotation):
            continue

        marked = _is_snowflake_marked(annotation) or (
            marker_type is not None and _has_marker(annotation, marker_type)
        )
        if not (marked or name in fields or all_numeric or _is_id_field(name)):
            continue

        str_name = f"{name}{suffix}"
        # 若该类或其父类已声明过同名字段（如既有手动 bizIdStr），跳过自动注入。
        # ⚠️ 除 hasattr 外还查 model_fields：pydantic 建类时会把字段属性从类字典里
        # delattr 掉，装饰器（类创建之后）只看 hasattr 会漏判，进而用 computed_field
        # 覆盖真实字段 —— 子类再继承时 pydantic 会直接抛
        # "Field ... overrides symbol of same name in a parent class"。
        if str_name in _declared_fields(model_cls) or hasattr(model_cls, str_name):
            continue

        setattr(model_cls, str_name, _make_property(name))
        changed = True

    return changed


# DecoratorInfos 的分类容器名（重建后需把既有 decorator 合并回去）
_DECORATOR_CATEGORIES = (
    "validators",
    "field_validators",
    "root_validators",
    "field_serializers",
    "model_serializers",
    "model_validators",
    "computed_fields",
)


def _rebuild_decorators(model_cls: type) -> Any:
    """重建 ``__pydantic_decorators__``，并**保留**类创建时已收集的 decorator。

    为什么不能直接 ``DecoratorInfos.build(model_cls)``：pydantic 首次 build 时用了
    ``replace_wrapped_methods=True``，会把类字典里的 ``PydanticDescriptorProxy``
    换回原始函数/property。之后再 build 只能扫到我们新注入的 computed_field，
    类体里手写的 ``@computed_field`` / 校验器会**全部丢失**（实测会丢）。
    所以这里以既有 decorators 为底，补上本次新注入的。
    """
    fresh = DecoratorInfos.build(model_cls, replace_wrapped_methods=False)
    existing = getattr(model_cls, "__pydantic_decorators__", None)
    if existing is not None:
        for category in _DECORATOR_CATEGORIES:
            merged = getattr(fresh, category, None)
            previous = getattr(existing, category, None)
            if merged is not None and previous:
                merged.update(previous)
    return fresh


def _declared_fields(model_cls: type) -> dict[str, Any]:
    """模型已声明的字段（``model_fields``），用于判断字符串版字段是否已被占用。"""
    fields = getattr(model_cls, "model_fields", None)
    return fields if isinstance(fields, dict) else {}


def _module_namespace(model_cls: type) -> dict[str, Any] | None:
    """模型所属模块的全局命名空间（供 ``model_rebuild`` 解析前向引用）。"""
    module = sys.modules.get(getattr(model_cls, "__module__", "") or "")
    ns = getattr(module, "__dict__", None)
    return ns if isinstance(ns, dict) else None


def _resolve_suffix(model_cls: type, suffix: str | None) -> str:
    """后缀优先级：装饰器参数 > 类属性 ``_auto_str_suffix`` > 默认 ``"Str"``。"""
    if suffix:
        return suffix
    raw = getattr(model_cls, "_auto_str_suffix", "")
    if isinstance(raw, str):
        return raw or "Str"
    # 未用 ClassVar 标注时 pydantic 会把它收成 private attribute（ModelPrivateAttr），
    # 真正的值在 .default 上
    default = getattr(raw, "default", None)
    return default if isinstance(default, str) and default else "Str"


# ---------------------------------------------------------------------------
# 对外 API：类装饰器
# ---------------------------------------------------------------------------
def auto_str(
    cls: type | None = None,
    *,
    fields: list[str] | tuple[str, ...] = (),
    skip: set[str] | frozenset[str] = frozenset(),
    all_numeric: bool = False,
    suffix: str | None = None,
    marker_type: Any = None,
):
    """给响应模型自动派生雪花 ID 的字符串版字段（推荐用法）。

    既可裸用 ``@auto_str``，也可带参 ``@auto_str(suffix="_str")``。

    Args:
        cls: 被装饰的模型类（装饰器语法下由 Python 传入）。
        fields: 白名单，这些字段无论命名都生成。
        skip: 黑名单，跳过这些字段。
        all_numeric: ``True`` 时对所有 int/float 生成（不推荐，易命中非 ID 数值）。
        suffix: 字符串版字段后缀；``None`` 时取类属性 ``_auto_str_suffix``，
            再回落 ``"Str"``。
        marker_type: 自定义标记类型（``Annotated[int, marker]`` 中的 marker）；
            内置的 :data:`SnowflakeInt` 始终生效，无需传入。

    Raises:
        RuntimeError: pydantic 内部结构变更，无法重建 decorators。
    """

    def decorate(model_cls: type):
        if not _inject_str_fields(
            model_cls,
            fields=set(fields),
            skip=set(skip),
            all_numeric=all_numeric,
            suffix=_resolve_suffix(model_cls, suffix),
            marker_type=marker_type,
        ):
            return model_cls

        if DecoratorInfos is None:  # pragma: no cover - 仅 pydantic 结构变更时触发
            raise RuntimeError(
                "pydantic._internal._decorators.DecoratorInfos 不可用："
                "无法为后置注入的 computed_field 重建 decorators，请检查 pydantic 版本"
            )

        # pydantic 在类创建时已 build 过一次 decorators，后置注入必须重建，
        # 否则新字段不会进入 model_dump() / OpenAPI schema。
        model_cls.__pydantic_decorators__ = _rebuild_decorators(model_cls)  # type: ignore[attr-defined]
        # force=True：强制重建 core schema 与 serializer。
        # - _types_namespace 必须显式给：rebuild 默认取**调用方**帧的命名空间，而调用方是
        #   本模块，解析不到模型所在模块的名字（如 ban.py 的 BanServiceStatus）。
        # - raise_errors=False：模型里可能有「指向本模块后面才定义的类」的前向引用，
        #   此刻解析不了。交给 pydantic 装 MockValSer，首次使用时自动重试（那时模块已加载完）。
        model_cls.model_rebuild(
            force=True,
            _types_namespace=_module_namespace(model_cls),
            raise_errors=False,
        )
        return model_cls

    if cls is None:
        return decorate
    return decorate(cls)


# ---------------------------------------------------------------------------
# 对外 API：Mixin（遗留写法，仍支持）
# ---------------------------------------------------------------------------
class AutoStrMixin:
    """为响应模型自动注入字符串版计算字段的基类（**遗留写法**，新代码用 ``@auto_str``）。

    子类只需 ``class X(SQLModel, AutoStrMixin)`` 并照常声明 ID 字段即可。可通过类属性
    微调行为：

    - ``_auto_str``：仅对这些字段名生成（白名单，优先级最高）；
    - ``_auto_str_skip``：跳过这些字段名（黑名单）；
    - ``_auto_str_all``：``True`` 时对所有 int/float 生成（不推荐，可能命中非 ID 数值）；
    - ``_auto_str_suffix``：字符串版字段后缀，默认 ``"Str"``（``mid`` -> ``midStr``）；
      snake_case 出参模型可覆盖为 ``"_str"``（``mid`` -> ``mid_str``）。

      ⚠️ **必须用 ``ClassVar[str]`` 标注**：写成裸赋值 ``_auto_str_suffix = "_str"`` 时，
      SQLModel 会在 ``__init_subclass__`` 之后才把该属性写进类字典，本 mixin 读不到，
      会静默回落默认后缀 ``"Str"``。用 ``@auto_str`` 装饰器则无此问题。
    """

    # 这些由子类选择性覆盖；基类置空避免实例属性冲突
    _auto_str: ClassVar[list[str]] = []
    _auto_str_skip: ClassVar[set[str]] = set()
    _auto_str_all: ClassVar[bool] = False
    _auto_str_suffix: ClassVar[str] = "Str"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # 这里跑在 pydantic 收集 decorators 之前，注入的 computed_field 会被正常收集，
        # 因此**不需要** model_rebuild（与装饰器路径不同）。
        _inject_str_fields(
            cls,
            fields=set(getattr(cls, "_auto_str", []) or []),
            skip=set(getattr(cls, "_auto_str_skip", []) or []),
            all_numeric=bool(getattr(cls, "_auto_str_all", False)),
            suffix=_resolve_suffix(cls, None),
            marker_type=None,
        )


__all__ = ["AutoStrMixin", "SnowflakeInt", "auto_str"]
