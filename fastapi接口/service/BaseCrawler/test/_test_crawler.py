import asyncio
import random
from typing import AsyncGenerator

from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
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
        self.params_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
        self.mode = True

    async def handle_fetch(self, params: int) -> WorkerStatus:
        print(params)
        self._count += 1
        await asyncio.sleep(random.random() * 100)

        return WorkerStatus.nullData

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        if self.mode:
            for i in self.params_arr:
                yield i
            return
        else:
            while 1:
                yield params
                params += 1

    async def is_stop(self) -> bool:
        if self._count > 150:
            return True
        return False

    async def on_run_end(self, end_param):
        print(f'结束参数：{end_param}')

    async def main(self):
        await self.run(self.params_arr[0])
        self.mode = False
        await self.run(114514)


async def _test():
    a = TestCrawler()
    await a.main()


if __name__ == "__main__":
    asyncio.run(_test())
