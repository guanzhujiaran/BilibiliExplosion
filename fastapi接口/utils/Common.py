import asyncio
import random
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.exc import InternalError
from fastapi接口.log.base_log import myfastapi_logger, sql_log
import concurrent.futures

GLOBAL_SCHEDULER = AsyncIOScheduler()
GLOBAL_SEM_LIMIT_NUM = 500
GLOBAL_SEM = asyncio.Semaphore(GLOBAL_SEM_LIMIT_NUM)
_comm_lock = asyncio.Lock()


def sem_gen(sem_limit=500):
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


def comm_sem_wrapper(sem_limit=100):
    sem = sem_gen(sem_limit)
    def wrapper_outter(func):
        async def wrapper(*args, **kwargs):
            async with sem:
                res = await func(*args, **kwargs)
                return res

        return wrapper
    return wrapper_outter

def sem_wrapper(func):
    async def wrapper(*args, **kwargs):
        async with GLOBAL_SEM:
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


def sem_retry_wrapper(func):
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                async with GLOBAL_SEM:
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


def sql_retry_wrapper(_func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await _func(*args, **kwargs)
                return res
            except InternalError as internal_error:
                sql_log.error(internal_error)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue
            except Exception as e:
                sql_log.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper
