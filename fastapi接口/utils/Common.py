import asyncio
import concurrent.futures
from typing import Callable, TypeVar, Awaitable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import _logger
from sqlalchemy.exc import InternalError, OperationalError

from fastapi接口.log.base_log import myfastapi_logger, sql_log

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
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        return res

    return wrapper


def lock_retry_wrapper(func):
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


async def asyncio_gather(*coros_or_futures, log: _logger = myfastapi_logger):
    results = await asyncio.gather(*coros_or_futures, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            log.opt(exception=True).exception(result)
    return results
