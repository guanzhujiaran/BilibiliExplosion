import time
from enum import StrEnum
from typing import List
from log.base_log import milvus_db_logger
from Models.lottery_database.milvusModel.biliMilvusModel import BiliLotData
from Utils.Common import lock_retry_wrapper
from pymilvus import AsyncMilvusClient


class Sqlhelper:
    class Collections(StrEnum):
        bili_lot_data = 'bili_lot_data'

    def __init__(self):
        self.__client = AsyncMilvusClient(db_name='default')

    @property
    def _client(self):
        return self.__client

    @lock_retry_wrapper
    async def upsert_bili_lot_data(self, data_ls: List[BiliLotData]):
        return await self._client.upsert(collection_name=self.Collections.bili_lot_data,data=[x.model_dump() for x in data_ls])

    @lock_retry_wrapper
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

    @lock_retry_wrapper
    async def del_outdated_bili_lottery_data(self):
        result = await self._client.delete(
            collection_name=self.Collections.bili_lot_data,
            filter=f'lottery_time < {int(time.time())}'
        )
        milvus_db_logger.info(f'delete {result} outdated bili lottery data')
        return result


milvus_sql_helper = Sqlhelper()
