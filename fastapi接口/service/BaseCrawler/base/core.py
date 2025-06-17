import asyncio
from abc import ABC, abstractmethod
from typing import TypeVar, Any, Generic

from loguru._logger import Logger
from loguru import logger

from fastapi接口.service.BaseCrawler.model.base import WorkerModel, ParamsType
from fastapi接口.utils.Common import sem_gen



class BaseCrawler(ABC, Generic[ParamsType]):
    def __init__(self, max_sem: int = 100, _logger: Logger = logger):
        self.log = _logger
        self.max_sem = max_sem
        self.task_queue: asyncio.Queue[WorkerModel] = asyncio.Queue(1)  # 只要有一个就可以了
        self.sem = sem_gen(max_sem)
        self._is_pause = False

    @abstractmethod
    async def worker(self):
        """
        里面丢一个自己实现的获取数据然后存进去的函数
        :return:
        """
        ...

    @abstractmethod
    async def run(self, *args, **kwargs):
        ...


    async def start(self):
        self.log.info("UnlimitedCrawler start method called.")
        self._is_pause = False

    async def pause(self):
        self.log.info("UnlimitedCrawler pause method called.")
        self._is_pause = True