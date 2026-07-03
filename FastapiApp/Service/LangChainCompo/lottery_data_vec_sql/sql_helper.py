import time
from enum import StrEnum
from typing import Dict, List

from pymilvus.milvus_client import IndexParams

from CONFIG import settings
from log.base_log import milvus_db_logger
from Models.lottery_database.milvusModel.biliMilvusModel import BiliLotData
from Utils.通用.Common import lock_retry_wrapper
from pymilvus import (
    AsyncMilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
    Collection,
)
import asyncio

_milvus_lock = asyncio.Lock()


class Sqlhelper:
    class CollectionNameEnum(StrEnum):
        bili_lot_data = "bili_lot_data"

    __client: AsyncMilvusClient | None = None

    def __init__(self):
        self._lock = asyncio.Lock()

    @property
    def _client(self) -> AsyncMilvusClient:
        if self.__client is None:
            self.__client = AsyncMilvusClient(
                uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}", timeout=10
            )
        return self.__client

    # region 初始化集合
    async def _create_bili_lot_data_collection(self):
        """
        创建bili_lot_data集合
        """
        # 定义集合字段
        fields = [
            FieldSchema(
                name="pk",
                dtype=DataType.INT64,
                is_primary=True,
            ),
            FieldSchema(
                name="lottery_id",
                dtype=DataType.INT64,
            ),
            FieldSchema(name="prize_vec", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="prize_cmt", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="lottery_time", dtype=DataType.INT64),
        ]

        # 创建集合schema
        schema = CollectionSchema(
            fields=fields, description="Bilibili lottery data with embeddings"
        )
        # 创建集合
        await self._client.create_collection(
            collection_name=self.CollectionNameEnum.bili_lot_data, schema=schema
        )

        # 创建索引
        index_params = IndexParams()
        index_params.add_index(
            index_name="prize_vec_index",
            field_name="prize_vec",
            index_type="FLAT",
            metric_type="COSINE",
        )
        await self._client.create_index(
            collection_name=self.CollectionNameEnum.bili_lot_data,
            index_params=index_params,
        )

        # 加载集合
        await self._client.load_collection(
            collection_name=self.CollectionNameEnum.bili_lot_data
        )

        milvus_db_logger.info(
            f"Collection {self.CollectionNameEnum.bili_lot_data} created successfully"
        )

    @lock_retry_wrapper(_milvus_lock)
    async def ensure_collection_exists(self):
        """
        确保集合存在，如果不存在则创建
        """
        # 检查集合是否存在
        collections = await self._client.list_collections()
        if self.CollectionNameEnum.bili_lot_data not in collections:
            await self._create_bili_lot_data_collection()
        else:
            # 集合已存在，检查是否已加载
            try:
                # 尝试获取集合统计信息来确认它是否已加载
                await self._client.get_collection_stats(
                    collection_name=self.CollectionNameEnum.bili_lot_data
                )
                milvus_db_logger.info(
                    f"Collection {self.CollectionNameEnum.bili_lot_data} already exists and is loaded"
                )
            except Exception:
                # 集合存在但未加载，加载它
                await self._client.load_collection(
                    collection_name=self.CollectionNameEnum.bili_lot_data
                )
                milvus_db_logger.info(
                    f"Collection {self.CollectionNameEnum.bili_lot_data} loaded successfully"
                )

    # endregion

    @lock_retry_wrapper(_milvus_lock)
    async def upsert_bili_lot_data(self, data_ls: List[BiliLotData]):
        data = [x.model_dump(exclude_none=True) for x in data_ls]
        return await self._client.upsert(
            collection_name=self.CollectionNameEnum.bili_lot_data, data=data
        )

    @lock_retry_wrapper(_milvus_lock)
    async def search_bili_lot_data(
        self, query_vec: list[float], limit: int, offset: int
    ) -> List[List[dict]]:
        # 确保集合存在
        res = await self._client.search(
            collection_name=self.CollectionNameEnum.bili_lot_data,
            anns_field="prize_vec",
            data=[query_vec],
            group_by_field="lottery_id",
            filter=f"lottery_time >= {int(time.time())}",
            limit=limit,
            output_fields=["lottery_id", "prize_cmt", "lottery_time"],
            offset=10,
        )
        return res

    @lock_retry_wrapper(_milvus_lock)
    async def get_bili_lot_data_collection_stats(
        self,
    ) -> Dict:
        """
        获取哔哩哔哩抽奖数据集合的统计信息

        Returns:
            Dict: 包含集合统计信息的字典，例如 {'row_count': int}
        """
        res = await self._client.get_collection_stats(
            collection_name=self.CollectionNameEnum.bili_lot_data,
        )
        print(res)
        return res

    @lock_retry_wrapper(_milvus_lock)
    async def del_outdated_bili_lottery_data(self):
        # 确保集合存在
        result = await self._client.delete(
            collection_name=self.CollectionNameEnum.bili_lot_data,
            filter=f"lottery_time < {int(time.time())}",
        )
        milvus_db_logger.info(f"delete {result} outdated bili lottery data")
        return result


milvus_sql_helper = Sqlhelper()

if __name__ == "__main__":
    print(settings)
    asyncio.run(milvus_sql_helper.get_bili_lot_data_collection_stats())
