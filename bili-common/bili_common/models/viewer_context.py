"""序列化期「当前访问者」上下文。

由 :func:`bili_common.models.auto_str` 的私域字段裁剪功能消费：打上
``@auto_str(private=...)`` 标记的字段，在序列化时按「当前是谁在看」决定
返回真值还是 ``None``。

为什么用 ContextVar 而不是 FastAPI 的序列化参数：
    FastAPI 的 ``serialize_response`` 没有 ``context`` 入参（只有 include /
    exclude / by_alias / exclude_unset / exclude_defaults / exclude_none），
    无法把「当前是谁在看」传进 Pydantic 的序列化钩子。

    因此改由 ContextVar 承载：请求进入时由中间件 :func:`bind_viewer` 写入，
    序列化时读 :func:`get_viewer`。好处是**模型完全不依赖 FastAPI**，同一个
    模型在 HTTP 响应、MQ payload、定时任务、单元测试里都能正确裁剪。

安全默认：
    取不到上下文时返回匿名访客（``mid=0, is_admin=False``），即最小可见。
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ViewerContext:
    """一次响应序列化时的访问者身份。

    Attributes:
        mid: 访问者 mid；``0`` 表示匿名（未登录）。
        is_admin: 是否为管理员（root）。管理员对任何对象都可见私域字段。
    """

    mid: int = 0
    is_admin: bool = False

    def can_see(self, owner_mid: int | None, *, admin_only: bool) -> bool:
        """判断该访问者能否看到某个私域字段。

        Args:
            owner_mid: 字段所属对象的归属 mid；``None`` 表示无归属（如系统级字段）。
            admin_only: 该字段是否**仅管理员**可见（本人也不可见）。

        Returns:
            可见返回 ``True``；否则 ``False``。
        """
        if self.is_admin:
            return True
        if admin_only or not owner_mid:
            return False
        return owner_mid == self.mid


_ANONYMOUS = ViewerContext()

_current_viewer: ContextVar[ViewerContext | None] = ContextVar(
    "bili_message_viewer", default=None
)


def get_viewer() -> ViewerContext:
    """取当前访问者；未绑定时为匿名（最小可见）。"""
    return _current_viewer.get() or _ANONYMOUS


def bind_viewer(mid: int = 0, is_admin: bool = False) -> Token:
    """绑定当前访问者，返回用于恢复的 ``Token``。

    典型用法是中间件里 ``token = bind_viewer(...)``，在 ``finally`` 中
    :func:`reset_viewer` 复位，避免上下文污染到下一个请求。
    """
    return _current_viewer.set(
        ViewerContext(mid=int(mid or 0), is_admin=bool(is_admin))
    )


def reset_viewer(token: Token | None) -> None:
    """复位到绑定前的上下文（中间件 ``finally`` 中调用）。"""
    if token is not None:
        _current_viewer.reset(token)


__all__ = ["ViewerContext", "bind_viewer", "get_viewer", "reset_viewer"]
