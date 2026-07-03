import asyncio
from abc import ABC, abstractmethod
from typing import Generic
from log.base_log import myfastapi_logger
from Service.BaseCrawler.model.base import WorkerModel, ParamsType
from Utils.通用.Common import sem_gen


class BaseCrawler(ABC, Generic[ParamsType]):
    def __init__(self, max_sem: int = 10, _logger=myfastapi_logger):
        self.log = _logger
        self.max_sem: int = max_sem
        # 队列大小设置为 max_sem + 1，以避免死锁问题
        # 原因：需要同时容纳大量的失败任务(无限重试场景)和新任务
        # 使用更大的队列可以避免队列满导致任务生成器阻塞
        self.task_queue: asyncio.Queue[WorkerModel | None] = asyncio.Queue()
        self.sem = sem_gen(max_sem)
        self._is_pause: bool = False

    def format_log(self, msg: str) -> str:
        return f"[{self.__class__.__name__}] {msg}"

    @abstractmethod
    async def worker(self) -> WorkerModel:
        """
        里面丢一个自己实现的获取数据然后存进去的函数
        :return:
        """
        ...

    @abstractmethod
    async def run(self, *args, **kwargs): ...

    async def start(self):
        self.log.info("UnlimitedCrawler start method called.")
        self._is_pause = False

    async def pause(self):
        self.log.info("UnlimitedCrawler pause method called.")
        self._is_pause = True
