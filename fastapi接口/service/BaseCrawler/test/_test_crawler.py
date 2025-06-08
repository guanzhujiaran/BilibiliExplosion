import asyncio
from typing import AsyncGenerator

from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler

import random

from fastapi接口.service.BaseCrawler.model.base import WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin, SequentialNullStopPlugin


class TestCrawler(UnlimitedCrawler):
    def __init__(self):
        stats_plugin = StatsPlugin(self)
        null_stop_plugin = SequentialNullStopPlugin(self)

        super().__init__(
            plugins=[null_stop_plugin, stats_plugin]
        )
        self._count = 0
        print('初始化')

    async def handle_fetch(self, params: int) -> WorkerStatus:
        print(params)
        self._count += 1
        await asyncio.sleep(random.random() * 100)

        return WorkerStatus.nullData

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        while 1:
            yield params
            params += 1

    async def is_stop(self) -> bool:
        if self._count > 150:
            return True
        return False

    async def on_run_end(self, end_param):
        print(f'结束参数：{end_param}')


async def _test():
    a = TestCrawler()
    await a.run(1)
    a._count = 0
    await a.run(900)


if __name__ == "__main__":
    asyncio.run(_test())
