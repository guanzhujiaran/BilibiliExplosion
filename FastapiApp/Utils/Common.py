import asyncio
import concurrent.futures
from functools import wraps
from typing import Callable, TypeVar, Awaitable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import _logger
from sqlalchemy.exc import InternalError, OperationalError

from log.base_log import myfastapi_logger, sql_log

GLOBAL_SCHEDULER: AsyncIOScheduler = AsyncIOScheduler()
_comm_lock = asyncio.Lock()

TResult = TypeVar("TResult")
FuncT = TypeVar("FuncT", bound=Callable[..., Awaitable[Any]])


def sem_gen(sem_limit=100):
    return asyncio.Semaphore(sem_limit)


def ensure_asyncio_loop():
    if asyncio.get_event_loop():
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


def comm_lock_wrapper(func):
    async def wrapper(*args, **kwargs):
        async with _comm_lock:
            res = await func(*args, **kwargs)
            return res

    return wrapper


def comm_wrapper(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        return res

    return wrapper


def lock_retry_wrapper(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                async with _comm_lock:
                    res = await func(*args, **kwargs)
                    return res
            except Exception as e:
                myfastapi_logger.exception(e)
                await asyncio.sleep(10)

    return wrapper


def retry_wrapper(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                myfastapi_logger.exception(e)
                await asyncio.sleep(10)

    return wrapper


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = loop.run_in_executor(pool, func, *args)
        return await future


def sql_retry_wrapper(_func: FuncT) -> FuncT:
    @wraps(_func)
    async def wrapper(*args: Any, **kwargs: Any) -> TResult:
        while True:
            try:
                res = await _func(*args, **kwargs)
                return res
            except InternalError as internal_error:
                sql_log.error(internal_error)
                await asyncio.sleep(60)
                continue
            except OperationalError as operational_error:
                if 1129 == operational_error.code:
                    sql_log.error(operational_error)
                    await asyncio.sleep(120)
                    continue
                sql_log.error(f'{_func} \t{operational_error}')
                await asyncio.sleep(60)
                continue
            except Exception as e:
                sql_log.exception(f'{args}\n{kwargs}\n{e}')
                await asyncio.sleep(60)
                continue

    return wrapper


def log_sql_retry_wrapper(log: _logger = myfastapi_logger):
    def _wrapper(_func: FuncT) -> FuncT:
        @wraps(_func)
        async def wrapper(*args: Any, **kwargs: Any) -> TResult:
            while True:
                try:
                    res = await _func(*args, **kwargs)
                    return res
                except InternalError as internal_error:
                    log.error(internal_error)
                    await asyncio.sleep(60)
                    continue
                except OperationalError as operational_error:
                    if 1129 == operational_error.code:
                        log.error(operational_error)
                        await asyncio.sleep(120)
                        continue
                    log.error(f'{_func} \t{operational_error}')
                    await asyncio.sleep(60)
                    continue
                except Exception as e:
                    log.exception(f'{args}\n{kwargs}\n{e}')
                    await asyncio.sleep(60)
                    continue

        return wrapper

    return _wrapper


async def asyncio_gather(*coros_or_futures, log: _logger.Logger | None = myfastapi_logger):
    async def _handle_coroutine(coro):
        try:
            return await coro
        except Exception as e:
            log and log.exception(f"协程 [{coro.cr_code}] 执行失败.")

    coros_or_futures_wrapped = map(_handle_coroutine, coros_or_futures)
    results = await asyncio.gather(*coros_or_futures_wrapped, return_exceptions=True)
    return results


def log_max_count_retry_wrapper(*, log: _logger = myfastapi_logger, max_count: int = 3, sleep_time: int = 10):
    """
    Decorator factory that creates a retry decorator with logging.

    Args:
        log: Logger instance to use (default: myfastapi_logger)
        max_count: Maximum number of retry attempts (default: 3)
                  If max_count <= 0, retry infinitely
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            attempt = 0
            while True:  # Infinite loop for retrying
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if max_count > 0 and attempt >= max_count:
                        log.error(
                            f"All {max_count + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        break

                    log.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"{'Retrying...' if max_count <= 0 else f'Retrying... ({max_count - attempt} attempts left)'}"
                    )
                    await asyncio.sleep(sleep_time)  # Exponential backoff
                    attempt += 1
            raise last_exception

        return wrapper

    return decorator
