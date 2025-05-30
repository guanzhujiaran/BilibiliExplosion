import asyncio
from abc import abstractmethod
from typing import TypeVar, Any, AsyncGenerator

from fastapi接口.service.BaseCrawler.base.core import BaseCrawler

ParamsType = TypeVar("ParamsType", bound=Any)


class UnlimitedCrawler(BaseCrawler):
    @abstractmethod
    async def is_stop(self) -> bool:
        """
        终止条件
        :return:
        """
        ...

    @abstractmethod
    async def key_params_gen(self, params: ParamsType) -> AsyncGenerator[ParamsType, None]:
        yield 1

    @abstractmethod
    async def handle_fetch(self, params: ParamsType):
        """
        这个里面写具体的处理逻辑
        :return:
        """
        ...

    async def worker(self):
        async with self.sem:
            params = await self.task_queue.get()
            await self.handle_fetch(params)

    async def run(self, params: ParamsType):
        task_set = set()
        async for params in self.key_params_gen(params):
            if await self.is_stop():
                self.log.debug('触发终止条件')
                break
            await self.task_queue.put(params)
            task = asyncio.create_task(self.worker())
            task_set.add(task)
            task.add_done_callback(
                lambda _t: task_set.remove(_t)
            )
            self.log.debug(f'当前线程存活数量：{len(task_set)}\n添加任务：{params}')
        self.log.debug(f'任务已经完成，当前线程存活数量：{len(task_set)}，正在等待剩余线程完成任务')
        await asyncio.gather(*task_set)

