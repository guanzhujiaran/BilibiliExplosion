import asyncio
from abc import abstractmethod
from typing import Any, AsyncGenerator, Optional, List

from fastapi接口.service.BaseCrawler.base.core import BaseCrawler, ParamsType
from fastapi接口.service.BaseCrawler.model.base import WorkerModel, WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.base import CrawlerPlugin
from fastapi接口.utils.Common import asyncio_gather


class UnlimitedCrawler(BaseCrawler[ParamsType]):
    _plugins: List[CrawlerPlugin[ParamsType]]

    def __init__(self,
                 plugins: List[CrawlerPlugin[ParamsType]] = None,
                 *args, **kwargs
                 ):
        if plugins is None:
            plugins = []
        super().__init__(*args, **kwargs)
        self._plugins = []
        for plugin in plugins:
            self.__register_plugin(plugin)

    @property
    def plugins(self) -> List[CrawlerPlugin[ParamsType]]:
        return self._plugins


    def __register_plugin(self, plugin: CrawlerPlugin[ParamsType]):
        if plugin not in self._plugins:
            self._plugins.append(plugin)
            plugin.on_plugin_register()
            self.log.debug(f"Plugin {plugin.__class__.__name__} registered to {self.__class__.__name__}.")

    @abstractmethod
    async def is_stop(self) -> bool:
        ...

    @abstractmethod
    async def key_params_gen(self, params: Any) -> AsyncGenerator[ParamsType, None]:
        yield params

    @abstractmethod
    async def handle_fetch(self, params: ParamsType) -> WorkerStatus | Any:
        ...

    @abstractmethod
    async def main(self, *args, **kwargs):
        """
        运行的主函数的逻辑，可以加一些乱七八糟的函数进去
        """

    async def on_worker_end(self, worker_model: WorkerModel):
        await asyncio_gather(*[x.on_worker_end(worker_model) for x in self._plugins], log=self.log)

    async def on_run_end(self, end_param: ParamsType):
        await asyncio_gather(*[x.on_run_end(end_param) for x in self._plugins], log=self.log)

    async def worker(self):
        async with self.sem:
            worker_model: WorkerModel = await self.task_queue.get()
            try:
                fetch_result = await self.handle_fetch(worker_model.params)
            except Exception as e:
                self.log.exception(f'爬取异常：{e}')
                fetch_result = WorkerStatus.fail
                await asyncio.sleep(100)
            if not isinstance(fetch_result, WorkerStatus):
                worker_model.fetchStatus = WorkerStatus.complete
            else:
                worker_model.fetchStatus = fetch_result
        await self.on_worker_end(worker_model)

    async def run(self, init_params: ParamsType):
        self.log.info(f"Crawler {self.__class__.__name__} starting with init_params: {init_params}")
        await asyncio_gather(*[x.on_run_start(init_params) for x in self._plugins], log=self.log)
        task_set = set()
        last_param_yielded: Optional[ParamsType] = None
        seqId = 0
        async for param in self.key_params_gen(init_params):
            worker_model = WorkerModel(
                params=param,
                seqId=seqId
            )
            seqId += 1
            await self.task_queue.put(worker_model)  # 这个必须在最前面
            last_param_yielded = param

            if await self.is_stop():
                self.log.info('触发终止条件，停止生成新任务。')
                break

            if True in await asyncio_gather(*[x.should_stop_check() for x in self._plugins], log=self.log):
                self.log.info('触发终止条件，停止生成新任务。')
                break
            if self._is_pause:
                while self._is_pause:
                    await asyncio.sleep(10)

            task = asyncio.create_task(self.worker())
            task_set.add(task)
            task.add_done_callback(task_set.discard)
            self.log.debug(f'当前线程存活数量：{len(task_set)}，队列大小：{self.task_queue.qsize()}，添加任务：{param}')

        self.log.info(f'任务生成完成。正在等待剩余线程完成任务，当前存活线程数量：{len(task_set)}')
        await asyncio_gather(*task_set, log=self.log)
        self.log.info(f'所有任务已完成。')

        await self.on_run_end(last_param_yielded if last_param_yielded is not None else init_params)

        for plugin in self._plugins:
            await plugin.on_run_end(last_param_yielded if last_param_yielded is not None else init_params)

        self.log.info(f"Crawler {self.__class__.__name__} run finished.")
        while not self.task_queue.empty():
            await self.task_queue.get()
