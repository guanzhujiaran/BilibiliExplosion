"""通用「等待回退（backoff）」重试工具（各微服务共用）。

设计参考 `backoff <https://pypi.org/project/backoff/>`_，并按本仓库的约定做了收敛：

- **异步优先**：被重试的对象基本都是 ``async def``（MQ 消费、HTTP 请求、LLM 调用），
  因此核心入口 :func:`run_with_backoff` 直接 ``await``，不再提供同步版本；
- **回调可自定义，且支持协程函数**：``on_backoff``（每次失败等待前）、
  ``on_giveup``（重试彻底耗尽，即「自定义错误回调」）、``on_success``（最终成功）
  三者既可以是普通函数，也可以是 ``async def``。典型用法是把 ``on_giveup``
  接到推送服务，把「重试耗尽」的上下文发出去告警；
- **上下文用 dataclass 表达**：回调收到的 :class:`BackoffContext` 是强类型 dataclass，
  不传 ``dict``，避免魔法字段；
- **不再依赖第三方 backoff 包**：等待策略（constant / expo / fibo）、抖动（jitter）、
  放弃条件（giveup）都在本模块内实现，避免再引入一个运行期依赖。

最简用法::

    from bili_common.core.backoff import BackoffConfig, expo_wait, run_with_backoff

    result = await run_with_backoff(
        fetch_something, url,
        config=BackoffConfig(max_tries=5, wait_gen=expo_wait(base=2, max_value=60)),
    )

自定义错误回调（重试耗尽时推送告警）::

    async def on_giveup(ctx: BackoffContext) -> None:
        await push_error(f"{ctx.target} 重试 {ctx.attempt} 次后失败: {ctx.exception}")

    await run_with_backoff(
        fetch_something, url,
        config=BackoffConfig(max_tries=5, on_giveup=on_giveup),
    )
"""

import asyncio
import inspect
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")

#: 等待时间生成器：入参为「已失败的次数」（从 1 开始），返回下一次重试前的等待秒数
WaitGenerator = Callable[[int], float]
#: 抖动函数：入参为生成器算出的等待秒数，返回抖动后的等待秒数
Jitter = Callable[[float], float]
#: 放弃条件：返回 True 表示不再重试（直接走 giveup 分支）
GiveupPredicate = Callable[[Exception], bool]
#: 回调：普通函数或协程函数均可
Callback = Callable[["BackoffContext"], Awaitable[None] | None]


@dataclass(slots=True, frozen=True)
class BackoffContext:
    """一次重试上下文（传给 ``on_backoff`` / ``on_giveup`` / ``on_success``）。

    Attributes:
        target: 被重试对象的名字（``__qualname__``，便于告警里定位）。
        attempt: 已经执行的次数（首次执行为 1；``on_backoff`` 中表示第几次失败）。
        wait: 本次回退需要等待的秒数（抖动后）；``on_giveup`` 中为最后一次计算出的等待值。
        elapsed: 从第一次执行到现在的总耗时（秒）。
        exception: 触发本次回退的异常；``on_success`` 时为 ``None``。
    """

    target: str
    attempt: int
    wait: float
    elapsed: float
    exception: Exception | None = None


def constant_wait(wait: float = 1.0) -> WaitGenerator:
    """恒定等待：每次失败都等待 ``wait`` 秒。"""

    def _wait(_attempt: int) -> float:
        return wait

    return _wait


def expo_wait(
    base: float = 2.0,
    factor: float = 1.0,
    max_value: float | None = None,
) -> WaitGenerator:
    """指数等待：第 n 次失败的等待为 ``factor * base ** n``，可设上限。

    Args:
        base: 指数底数（默认 2，即 2s / 4s / 8s …）。
        factor: 起始倍数（默认 1）。
        max_value: 单次等待上限（秒），``None`` 表示不封顶。
    """
    if base <= 0:
        raise ValueError("base 必须大于 0")
    if factor <= 0:
        raise ValueError("factor 必须大于 0")

    def _wait(attempt: int) -> float:
        value = factor * (base**attempt)
        if max_value is not None:
            value = min(value, max_value)
        return value

    return _wait


def fibo_wait(
    base: float = 1.0,
    factor: float = 1.0,
    max_value: float | None = None,
) -> WaitGenerator:
    """斐波那契等待：第 n 次失败的等待为 ``factor * base * fib(n)``（1, 1, 2, 3, 5 …）。"""
    if base <= 0:
        raise ValueError("base 必须大于 0")
    if factor <= 0:
        raise ValueError("factor 必须大于 0")

    def _wait(attempt: int) -> float:
        a, b = 1, 1
        for _ in range(max(0, attempt - 1)):
            a, b = b, a + b
        value = factor * base * a
        if max_value is not None:
            value = min(value, max_value)
        return value

    return _wait


def full_jitter(value: float) -> float:
    """满抖动：在 ``[0, value]`` 内均匀取值（backoff 库 ``random_jitter`` 语义）。

    适合大量客户端同时重试的场景，可有效打散「惊群」。
    """
    return random.uniform(0, value)


def equal_jitter(value: float) -> float:
    """等抖动：``value / 2 + U(0, value / 2)``，保证至少等到一半时间。"""
    half = value / 2
    return half + random.uniform(0, half)


@dataclass(slots=True)
class BackoffConfig:
    """重试策略配置（对应 backoff 库 ``on_exception`` 的参数）。

    Attributes:
        max_tries: 最大执行次数（含首次）；``None`` 表示不限次数。
        max_time: 总耗时上限（秒）；``None`` 表示不限。
        wait_gen: 等待时间生成器，见 :func:`constant_wait` / :func:`expo_wait` / :func:`fibo_wait`。
        jitter: 抖动函数；``None`` 表示不抖动。
        giveup: 放弃条件，命中即不再重试（优于 ``max_tries`` / ``max_time``）。
        on_backoff: 每次失败、等待前调用（记日志 / 埋点）。
        on_giveup: 重试耗尽时调用，即「自定义错误回调」（推送告警等）。
        on_success: 最终成功时调用（可选，用于「恢复通知」）。
        raise_on_giveup: 耗尽后是否把最后一次异常抛出；``False`` 时返回 ``None``。
    """

    max_tries: int | None = 5
    max_time: float | None = None
    wait_gen: WaitGenerator = field(default_factory=lambda: expo_wait(2.0, 1.0, 60.0))
    jitter: Jitter | None = full_jitter
    giveup: GiveupPredicate | None = None
    on_backoff: Callback | None = None
    on_giveup: Callback | None = None
    on_success: Callback | None = None
    raise_on_giveup: bool = True

    def __post_init__(self) -> None:
        if self.max_tries is not None and self.max_tries < 1:
            raise ValueError("max_tries 必须 >= 1（含首次执行），或不限次数请传 None")
        if self.max_time is not None and self.max_time <= 0:
            raise ValueError("max_time 必须大于 0")


def _target_name(func: Callable[..., Any]) -> str:
    return getattr(func, "__qualname__", None) or repr(func)


async def _invoke(callback: Callback | None, ctx: BackoffContext) -> None:
    """调用回调：普通函数直接调用，协程函数 ``await``。"""
    if callback is None:
        return
    result = callback(ctx)
    if inspect.isawaitable(result):
        await result


def _should_giveup(
    config: BackoffConfig,
    exc: Exception,
    attempt: int,
    elapsed: float,
) -> bool:
    if config.giveup is not None and config.giveup(exc):
        return True
    if config.max_tries is not None and attempt >= config.max_tries:
        return True
    if config.max_time is not None and elapsed >= config.max_time:
        return True
    return False


async def run_with_backoff(
    func: Callable[..., Awaitable[R]],
    *args: Any,
    config: BackoffConfig | None = None,
    **kwargs: Any,
) -> R | None:
    """执行 ``func``，失败时按「等待回退」策略重试。

    Args:
        func: 需要执行的协程函数。
        *args: 透传给 ``func`` 的位置参数。
        config: 重试策略；``None`` 时使用 :class:`BackoffConfig` 默认值
            （最多执行 5 次，指数等待 2s 起步、上限 60s，满抖动）。
        **kwargs: 透传给 ``func`` 的关键字参数。

    Returns:
        ``func`` 的返回值；仅当耗尽重试且 ``config.raise_on_giveup=False`` 时返回 ``None``。

    Raises:
        Exception: 重试耗尽（或 ``giveup`` 命中）时，抛出最后一次异常（默认行为）。
    """
    cfg = config or BackoffConfig()
    target = _target_name(func)
    started_at = time.monotonic()
    attempt = 0

    while True:
        attempt += 1
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - 重试包装需捕获所有异常再决定是否重试
            elapsed = time.monotonic() - started_at
            if _should_giveup(cfg, exc, attempt, elapsed):
                await _invoke(
                    cfg.on_giveup,
                    BackoffContext(
                        target=target,
                        attempt=attempt,
                        wait=0.0,
                        elapsed=elapsed,
                        exception=exc,
                    ),
                )
                if cfg.raise_on_giveup:
                    raise
                return None

            wait = cfg.wait_gen(attempt)
            if cfg.jitter is not None:
                wait = cfg.jitter(wait)
            # 不让单次等待超出剩余预算（max_time 场景下的收尾重试）
            if cfg.max_time is not None:
                wait = max(0.0, min(wait, cfg.max_time - elapsed))
            await _invoke(
                cfg.on_backoff,
                BackoffContext(
                    target=target,
                    attempt=attempt,
                    wait=wait,
                    elapsed=elapsed,
                    exception=exc,
                ),
            )
            await asyncio.sleep(wait)
        else:
            await _invoke(
                cfg.on_success,
                BackoffContext(
                    target=target,
                    attempt=attempt,
                    wait=0.0,
                    elapsed=time.monotonic() - started_at,
                    exception=None,
                ),
            )
            return result


def with_backoff(
    **config_kwargs: Any,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """装饰器写法：``@with_backoff(max_tries=3, ...)``，参数同 :class:`BackoffConfig`。

    注意：被装饰函数不能再有名为 ``config`` 的形参（该名字被重试入口占用）。
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        cfg = BackoffConfig(**config_kwargs)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = await run_with_backoff(func, *args, config=cfg, **kwargs)
            # 默认 raise_on_giveup=True，耗尽重试时会直接抛异常，不会返回 None
            return cast(R, result)

        return wrapper

    return decorator


__all__ = [
    "BackoffConfig",
    "BackoffContext",
    "Callback",
    "GiveupPredicate",
    "Jitter",
    "WaitGenerator",
    "constant_wait",
    "equal_jitter",
    "expo_wait",
    "fibo_wait",
    "full_jitter",
    "run_with_backoff",
    "with_backoff",
]
