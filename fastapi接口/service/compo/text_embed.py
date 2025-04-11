import asyncio
from typing import List

from fastapi_cache.decorator import cache
from openai import AsyncOpenAI
from fastapi接口.models.lottery_database.milvusModel.biliMilvusModel import BiliLotData
from fastapi接口.service.compo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from grpc获取动态.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from grpc获取动态.src.SQLObject.models import Lotdata

_client = AsyncOpenAI(base_url='http://127.0.0.1:1234/v1', api_key="your-api-key-here")

_model_name = 'text-embedding-multilingual-e5-base'

@cache(8 * 3600)
async def _create_embeddings(text: list[str | None], model: str = _model_name) -> list[list[float] | None]:
    resp = await _client.embeddings.create(input=[x for x in text if x and type(x) is str], model=model)
    ret_list = []
    for x in range(len(text)):
        if text[x] and type(text[x]) is str:
            ret_list.append(resp.data.pop(0).embedding)
        else:
            ret_list.append(None)
    return ret_list


async def save_bili_lot_data_embeddings(data_ls: List[BiliLotData]) -> list[list[float]]:
    return await milvus_sql_helper.upsert_bili_lot_data(data_ls)


async def lot_data_2_bili_lot_data_ls(x: Lotdata) -> List[BiliLotData]:
    """
    sqlalchemy的Lotdata转换成milvusdb的BiliLotData模型
    返回1-3个数据
    :return:
    """
    lottery_id = x.lottery_id
    first_prize_cmt = x.first_prize_cmt
    second_prize_cmt = x.second_prize_cmt
    third_prize_cmt = x.third_prize_cmt
    lottery_time = x.lottery_time
    embeddings = await _create_embeddings([first_prize_cmt, second_prize_cmt, third_prize_cmt])
    first_prize_vec, second_prize_vec, third_prize_vec = embeddings
    ret_list = [BiliLotData(
        pk=lottery_id * 10,
        lottery_id=lottery_id,
        prize_vec=first_prize_vec,
        prize_cmt=first_prize_cmt,
        lottery_time=lottery_time
    )]
    if second_prize_vec is not None:
        ret_list.append(BiliLotData(
            pk=lottery_id * 20,
            lottery_id=lottery_id,
            prize_vec=first_prize_vec,
            prize_cmt=first_prize_cmt,
            lottery_time=lottery_time
        ))
    if third_prize_vec is not None:
        ret_list.append(
            BiliLotData(
                pk=lottery_id * 30,
                lottery_id=lottery_id,
                prize_vec=first_prize_vec,
                prize_cmt=first_prize_cmt,
                lottery_time=lottery_time
            )
        )
    return ret_list


async def search_lottery_text(query_text: str, limit: int = 10) -> List[Lotdata]:
    query_vec = await _create_embeddings([query_text])
    res = await milvus_sql_helper.search_bili_lot_data(query_vec=query_vec[0], limit=limit)
    lottery_id_ls = [x.get('entity').get('lottery_id') for x in res[0]]
    lot_data_ls = await grpc_sql_helper.get_lotDetail_ls_by_lot_ids(lottery_id_ls)
    return lot_data_ls


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_create_embeddings('显卡'))
