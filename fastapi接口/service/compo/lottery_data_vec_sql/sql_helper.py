import asyncio
import time
from enum import Enum
from typing import List
from fastapi接口.log.base_log import milvus_db_logger
from fastapi接口.models.lottery_database.milvusModel.biliMilvusModel import BiliLotData
__lock = asyncio.Lock()

def lock_wrapper(func):
    async def wrapper(*args, **kwargs):
        while 1:
            async with __lock:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    milvus_db_logger.exception(e)
                    await asyncio.sleep(30)

    return wrapper


class Sqlhelper:
    class Collections(str, Enum):
        bili_lot_data = 'bili_lot_data'

    def __init__(self):
        self.__client = None

    @property
    def _client(self):
        if not self.__client:
            from pymilvus import AsyncMilvusClient
            self.__client = AsyncMilvusClient(db_name='default')
        return self.__client

    @lock_wrapper
    async def upsert_bili_lot_data(self, data_ls: List[BiliLotData]):
        return await self._client.upsert(collection_name=self.Collections.bili_lot_data,
                                         data=[x.model_dump() for x in data_ls])

    @lock_wrapper
    async def search_bili_lot_data(self, query_vec: list[float], limit: int = 10):
        res = await self._client.search(
            collection_name=self.Collections.bili_lot_data,  # 用你的集合的实际名称替换
            anns_field='prize_vec',
            # 用你的查询向量替换
            data=[query_vec],
            group_by_field="lottery_id",
            filter=f'lottery_time >= {int(time.time())}',
            limit=limit,  # 返回的搜索结果的最大数量
            output_fields=['lottery_id', 'prize_cmt', 'lottery_time'],
        )
        return res

    @lock_wrapper
    async def del_outdated_bili_lottery_data(self):
        result = await self._client.delete(
            collection_name=self.Collections.bili_lot_data,
            filter=f'lottery_time < {int(time.time())}'
        )
        milvus_db_logger.info(f'delete {result} outdated bili lottery data')
        return result


milvus_sql_helper = Sqlhelper()
