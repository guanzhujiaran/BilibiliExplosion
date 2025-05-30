import asyncio
from typing import AsyncGenerator

from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler, ParamsType

import random
class TestCrawler(UnlimitedCrawler):
    def __init__(self):
        super().__init__()
        self._count=0

    async def handle_fetch(self, params: int):
        print(params)
        self._count += 1
        await asyncio.sleep(random.randint(1,10))

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        while 1:
            yield params
            params += 1

    async def is_stop(self) -> bool:
        if self._count > 1000:
            return True
        return False

if __name__=="__main__":
    a = TestCrawler()
    asyncio.run(a.run(1))
