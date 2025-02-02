import json
from enum import Enum
from typing import List
from utl.redisTool.RedisManager import RedisManagerBase
from CONFIG import CONFIG
_reids_port = CONFIG.database.proxyRedis.port
_reids_host = CONFIG.database.proxyRedis.host


class BiliRedisDbEnum(Enum):
    LiveLottery = 0
    Semantic = 1


class BiliLiveLotteryRedis(RedisManagerBase):
    class RedisMap(str, Enum):
        all_live_lot = 'all_live_lot'

    def __init__(self):
        super().__init__(
            host=_reids_host,
            port=_reids_port,
            db=BiliRedisDbEnum.LiveLottery.value
        )

    async def get_live_lottery(self, page_num: int = 0, page_size: int = 0) -> tuple[List[any], int]:
        all_lot_infos = json.loads(await self._get(BiliLiveLotteryRedis.RedisMap.all_live_lot.value))
        total_num = len(all_lot_infos)
        if page_num and page_size:
            start_index = (page_num - 1) * page_size
            end_index = start_index + page_size
            all_lot_infos = all_lot_infos[start_index:end_index]
        return all_lot_infos, total_num


bili_live_lottery_redis = BiliLiveLotteryRedis()

if __name__ == '__main__':
    import asyncio
    a,b = asyncio.run(bili_live_lottery_redis.get_live_lottery(3,10))
    print(a,len(a),b)
