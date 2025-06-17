import asyncio
import time
from enum import StrEnum
from CONFIG import CONFIG
from utl.redisTool.RedisManager import RedisManagerBase


class LotDataRedisObj(RedisManagerBase):
    class RedisMap(StrEnum):
        add_dynamic_lottery_queue = "add_dynamic_lottery_queue"

    def __init__(self):
        super().__init__(
            db=CONFIG.database.lotDataRedisObj.db,
            host=CONFIG.database.lotDataRedisObj.host,
            port=CONFIG.database.lotDataRedisObj.port,
        )

    async def set_add_dynamic_lottery(self, dynamic_id: str):
        return await self._zadd(self.RedisMap.add_dynamic_lottery_queue.value,
                                {dynamic_id: int(time.time())})

    async def is_exist_add_dynamic_lottery(self, dynamic_id: str | int) -> 0 | 1:
        if delete_obj := await self._zget_range_by_score(
                key=self.RedisMap.add_dynamic_lottery_queue.value,
                min_score=0,
                max_score=int(time.time()) - 60 * 10
        ):
            await self._zdel_elements(self.RedisMap.add_dynamic_lottery_queue.value, *delete_obj)
        return await self._z_exist(self.RedisMap.add_dynamic_lottery_queue.value, dynamic_id)


lot_data_redis = LotDataRedisObj()

if __name__ == "__main__":
    async def _test():
        ret = await lot_data_redis.set_add_dynamic_lottery("123")
        print(ret)
        print(await lot_data_redis.is_exist_add_dynamic_lottery(123))
        print(await lot_data_redis.is_exist_add_dynamic_lottery('123'))


    asyncio.run(_test())
