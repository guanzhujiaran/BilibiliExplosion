import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi接口.log.base_log import myfastapi_logger

GLOBAL_SCHEDULER = AsyncIOScheduler()
_sem = asyncio.Semaphore(100)
_comm_lock = asyncio.Lock()
def ensure_asyncio_loop():
    if asyncio.get_event_loop():
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

def _comm_lock_wrapper(func):
    async def wrapper(*args, **kwargs):
        async with _comm_lock:
            res = await func(*args, **kwargs)
            return res
    return wrapper

def _comm_wrapper(func):
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        return res

    return wrapper

def _sem_wrapper(func):
    async def wrapper(*args, **kwargs):
        async with _sem:
            res = await func(*args, **kwargs)
            return res

    return wrapper

def _lock_retry_wrapper(func):
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

def _sem_retry_wrapper(func):
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                async with _sem:
                    res = await func(*args, **kwargs)
                    return res
            except Exception as e:
                myfastapi_logger.exception(e)
                await asyncio.sleep(10)
    return wrapper