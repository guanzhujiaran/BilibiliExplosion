import asyncio

from pymilvus import AsyncMilvusClient, DataType
from pymilvus.milvus_client import IndexParams
from timm.utils import is_primary

from fastapi接口.service.compo.lottery_data_vec_sql.sql_helper import milvus_sql_helper


async def create_collection():
    index_params = IndexParams()
    index_params.add_index(
        field_name='pk',
        index_type='',
        index_name=''
    )
    index_params.add_index(
        field_name='lottery_time',
        index_type='',
        index_name=''
    )
    index_params.add_index(
        field_name='prize_vec',
        index_type='',
        index_name=''
    )
    index_params.add_index(
        field_name='lottery_id',
        index_type='',
        index_name=''
    )
    index_params.add_index(
        field_name='prize_cmt',
        index_type='',
        index_name=''
    )
    schema = AsyncMilvusClient.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )
    schema.add_field(
        field_name='pk',
        datatype=DataType.INT64,
        description="lottery_id * 奖项等级 * 10",
        is_primary=True
    )
    schema.add_field(
        field_name='lottery_id',
        datatype=DataType.INT64,
    )
    schema.add_field(
        field_name='prize_vec',
        datatype=DataType.FLOAT_VECTOR,
        dim=768,
    )
    schema.add_field(
        field_name='prize_cmt',
        datatype=DataType.VARCHAR,
        max_length=256,
        enable_analyzer=True,
        analyzer_params={
            "type": "chinese"
        }
    )
    schema.add_field(
        field_name='lottery_time',
        datatype=DataType.INT64,
    )
    await milvus_sql_helper._client.create_collection(
        collection_name=milvus_sql_helper.Collections.bili_lot_data,
        schema=schema,
        index_params=index_params
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_collection())
