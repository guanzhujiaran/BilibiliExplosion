import asyncio
from typing import List

from openai import AsyncOpenAI

import fastapi接口.models.lottery_database.milvusModel.biliMilvusModel as biliMilvusModel
import fastapi接口.service.compo.lottery_data_vec_sql.sql_helper as sql_helper
import fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer as DynDetailSqlHelperMysqlVer
import fastapi接口.service.grpc_module.src.SQLObject.models as models
from CONFIG import CONFIG

_client = AsyncOpenAI(base_url=f'{CONFIG.lm_studio_url}/v1', api_key="your-api-key-here")

_model_name = 'text-embedding-multilingual-e5-base'


async def _create_embedding(text: str | None, model: str = _model_name) -> list[float] | None:
    if type(text) is not str:
        return None
    if not text.strip():
        return None
    resp = await _client.embeddings.create(input=text, model=model)
    if resp.data:
        return resp.data[0].embedding
    return None


async def save_bili_lot_data_embeddings(data_ls: List[biliMilvusModel.BiliLotData]) -> list[list[float]]:
    return await sql_helper.milvus_sql_helper.upsert_bili_lot_data(
        [x for x in data_ls if x.prize_vec])  # 保存的时候确保vec是存在的


async def lot_data_2_bili_lot_data_ls(x: models.Lotdata) -> List[biliMilvusModel.BiliLotData]:
    """
    sqlalchemy的Lotdata转换成milvusdb的biliMilvusModel.BiliLotData模型
    返回1-3个数据
    :return:
    """
    lottery_id = x.lottery_id
    first_prize_cmt = x.first_prize_cmt
    second_prize_cmt = x.second_prize_cmt
    third_prize_cmt = x.third_prize_cmt
    lottery_time = x.lottery_time
    embeddings = await asyncio.gather(
        _create_embedding(first_prize_cmt),
        _create_embedding(second_prize_cmt),
        _create_embedding(third_prize_cmt)
    )
    first_prize_vec, second_prize_vec, third_prize_vec = embeddings
    ret_list = [biliMilvusModel.BiliLotData(
        pk=lottery_id * 10,
        lottery_id=lottery_id,
        prize_vec=first_prize_vec,
        prize_cmt=first_prize_cmt,
        lottery_time=lottery_time
    )]
    if second_prize_vec is not None:
        ret_list.append(biliMilvusModel.BiliLotData(
            pk=lottery_id * 20,
            lottery_id=lottery_id,
            prize_vec=first_prize_vec,
            prize_cmt=first_prize_cmt,
            lottery_time=lottery_time
        ))
    if third_prize_vec is not None:
        ret_list.append(
            biliMilvusModel.BiliLotData(
                pk=lottery_id * 30,
                lottery_id=lottery_id,
                prize_vec=first_prize_vec,
                prize_cmt=first_prize_cmt,
                lottery_time=lottery_time
            )
        )
    return ret_list


async def search_lottery_text(query_text: str, limit: int = 10) -> List[models.Lotdata]:
    query_text = query_text.strip()
    if not query_text:
        return []
    query_vec = await _create_embedding(query_text)
    res = await sql_helper.milvus_sql_helper.search_bili_lot_data(query_vec=query_vec, limit=limit)
    lottery_id_ls = [x.get('entity').get('lottery_id') for x in res[0]]
    lot_data_ls = await DynDetailSqlHelperMysqlVer.grpc_sql_helper.get_lotDetail_ls_by_lot_ids(lottery_id_ls)
    return lot_data_ls


if __name__ == '__main__':
    print(asyncio.run(_create_embedding('站周边蓝牙耳机')))
