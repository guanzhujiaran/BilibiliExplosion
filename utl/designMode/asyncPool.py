import asyncio
import inspect
from dataclasses import dataclass
from typing import List, Callable, Any

from loguru import logger


class BaseAsyncPool:
    @dataclass
    class TargetObjWrapper:
        target_obj: Any
        is_using: bool

    def __init__(self, max_workers: int, target_obj: Any, target_func_name: str):
        self.max_workers = max_workers
        self.target_func_name = target_func_name
        self.sem = asyncio.Semaphore(max_workers)
        self.lock_using = asyncio.Lock()
        self.target_obj_sets: List[BaseAsyncPool.TargetObjWrapper] = [
            self.TargetObjWrapper(target_obj=target_obj(), is_using=False) for _ in range(max_workers)]

    async def do(self, *args, **kwargs):
        async with self.sem:
            while 1:
                for target_obj in self.target_obj_sets:
                    async with self.lock_using:
                        if target_obj.is_using:
                            continue
                        target_obj.is_using = True
                    try:
                        func = getattr(target_obj.target_obj, self.target_func_name)
                        if inspect.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return await asyncio.to_thread(func, *args, **kwargs)
                    except Exception as e:
                        logger.exception(e)
                        break
                    finally:
                        async with self.lock_using:
                            target_obj.is_using = False
