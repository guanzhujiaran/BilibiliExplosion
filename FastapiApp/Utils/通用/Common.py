import asyncio
import concurrent.futures
from functools import wraps
from typing import Callable, TypeVar, Awaitable, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.exc import InternalError, TimeoutError, OperationalError
from pymysql.constants import CR
from log.base_log import myfastapi_logger, sql_log
import random

GLOBAL_SCHEDULER: AsyncIOScheduler = AsyncIOScheduler()
_comm_lock = asyncio.Lock()
# 全局线程池，避免重复创建
_global_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

TResult = TypeVar("TResult")
FuncT = TypeVar("FuncT", bound=Callable[..., Awaitable[Any]])


def sem_gen(sem_limit=100):
    return asyncio.Semaphore(sem_limit)


def ensure_asyncio_loop():
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # 当前没有运行的事件循环，创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


def comm_lock_wrapper(func):
    @wraps(func)
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


def lock_retry_wrapper(lock: asyncio.Lock):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            while 1:
                try:
                    async with lock:
                        res = await func(*args, **kwargs)
                        return res
                except Exception as e:
                    myfastapi_logger.exception(e)
                    await asyncio.sleep(10)

        return wrapper

    return decorator


def retry_wrapper(func, max_retries: int = -1, sleep_time: int = 10):
    """
    重试装饰器，支持最大重试次数配置

    Args:
        func: 要装饰的函数
        max_retries: 最大重试次数，-1表示无限重试
        sleep_time: 重试间隔时间(秒)
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        retry_count = 0
        while True:
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                if max_retries >= 0 and retry_count >= max_retries:
                    myfastapi_logger.error(
                        f"函数【{func.__name__}】重试{max_retries}次后仍失败，抛出异常"
                    )
                    raise

                retry_count += 1
                myfastapi_logger.exception(
                    f"函数【{func.__name__}】执行失败，第{retry_count}次重试: {e}"
                )
                await asyncio.sleep(sleep_time)

    return wrapper


async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(_global_executor, func, *args)
    return await future


async def handle_sql_operational_error(func, log, err: OperationalError)->bool:
    """
        返回是否需要继续重试
    """
    if '(pymysql.err.OperationalError) (1054,' in err.args[0]: # 数据操作错了
        return False
    match err.args[0]:
        case 1129:
            log.error(f"{func} \t{err}")
            await asyncio.sleep(120)
        case 1213:  # 死锁错误，随机等待后重试
            sleep_time = random.uniform(1, 5)  # 随机等待1-5秒
            log.error(f"{func} \t死锁错误: {err}, 将在{sleep_time:.2f}秒后重试")
            await asyncio.sleep(sleep_time)
        case CR.CR_SERVER_LOST:  # mysql并发太高了，等待一段时间再重试
            await asyncio.sleep(120)
        case CR.CR_CONN_HOST_ERROR:  # mysql配置不正确或者mysql暂时挂了，在重启
            log.error(f"{func} \t{err}")
            await asyncio.sleep(120)
        case _:  # 未知代码
            log.error(f"未知mysql错误代码：{func} \t{err}")
            await asyncio.sleep(120)

    return True

def sql_retry_wrapper(_func: FuncT) -> FuncT:
    @wraps(_func)
    async def wrapper(*args: Any, **kwargs: Any):
        while True:
            try:
                res = await _func(*args, **kwargs)
                return res
            except InternalError as internal_error:
                sql_log.error(internal_error)
                await asyncio.sleep(60)
                continue
            except OperationalError as operational_error:
                    if await handle_sql_operational_error(_func, log, operational_error):
                        continue
                    break
            except TimeoutError as timeout_error:  # 这个是超时了，可能mysql负载太高卡了
                await asyncio.sleep(60)
                continue
            except Exception as e:
                sql_log.critical(
                    f"函数：【{_func.__name__}】\targs：【{args}\t{kwargs}】\t报错：【{e}】"
                )
                await asyncio.sleep(60)
                continue

    return wrapper


def log_sql_retry_wrapper(log: "Logger" = myfastapi_logger):
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
                    if await handle_sql_operational_error(_func, log, operational_error):
                        continue
                    log.exception(operational_error)
                    raise  # 无法恢复时抛出异常，避免返回 None 导致调用方出现误导性 TypeError
                except Exception as e:
                    # 检查是否是死锁错误(已经在内层处理过重试)
                    error_str = str(e)
                    if "Deadlock" in error_str or "1213" in error_str:
                        log.error(
                            f"{_func.__name__} \t死锁错误(内层重试已耗尽): {error_str[:200]}"
                        )
                        await asyncio.sleep(5)  # 短暂等待后继续重试
                        continue
                    # 其他异常保持原有逻辑
                    log.exception(f"{args}\n{kwargs}\n{e}")
                    await asyncio.sleep(60)
                    continue

        return wrapper

    return _wrapper


async def asyncio_gather(
    *coros_or_futures, log: Optional["Logger"] = myfastapi_logger
):
    async def _handle_coroutine(coro):
        try:
            return await coro
        except Exception as e:
            log and log.exception(f"协程 [{coro.cr_code}] 执行失败.")

    coros_or_futures_wrapped = map(_handle_coroutine, coros_or_futures)
    results = await asyncio.gather(*coros_or_futures_wrapped, return_exceptions=True)
    return results


def log_max_count_retry_wrapper(
    *, log: "Logger" = myfastapi_logger, max_count: int = 3, sleep_time: int = 10
):
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
                    if 0 < max_count <= attempt:
                        log.error(
                            f"All {max_count + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        break

                    log.exception(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"{'Retrying...' if max_count <= 0 else f'Retrying... ({max_count - attempt} attempts left)'}"
                    )
                    await asyncio.sleep(sleep_time)  # Fixed backoff interval
                    attempt += 1
            raise last_exception

        return wrapper

    return decorator
