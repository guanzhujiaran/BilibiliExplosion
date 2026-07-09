import asyncio
from typing import List

from langchain_openai import OpenAIEmbeddings

import Models.lottery_database.milvusModel.biliMilvusModel as biliMilvusModel
import Service.LangChainCompo.lottery_data_vec_sql.sql_helper as sql_helper
import Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer as DynDetailSqlHelperMysqlVer
import Service.GrpcModule.GrpcSrc.SQLObject.models as models
from CONFIG import CONFIG, ModelName
from Utils.通用.Common import log_max_count_retry_wrapper

_embeddings = OpenAIEmbeddings(
    model=ModelName.TEXT_EMBEDDING_MULTILINGUAL_E5_BASE,
    openai_api_base=CONFIG.llama_url,
    openai_api_key="1",
)

_embedding_lock = asyncio.Lock()  # 防止并发请求，服务器性能太弱了


async def _create_embedding(
    text: str | None,
) -> list[float] | None:
    async with _embedding_lock:
        if type(text) is not str:
            return None
        if not text.strip():
            return None
        return await _embeddings.aembed_query(text)


@log_max_count_retry_wrapper()
async def save_bili_lot_data_embeddings(
    data_ls: List[biliMilvusModel.BiliLotData],
) -> list[list[float]]:
    return await sql_helper.milvus_sql_helper.upsert_bili_lot_data(
        [x for x in data_ls if x.prize_vec]
    )  # 保存的时候确保vec是存在的


@log_max_count_retry_wrapper()
async def lot_data_2_bili_lot_data_ls(
    x: models.Lotdata,
) -> List[biliMilvusModel.BiliLotData]:
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
        _create_embedding(third_prize_cmt),
    )
    first_prize_vec, second_prize_vec, third_prize_vec = embeddings
    ret_list = [
        biliMilvusModel.BiliLotData(
            pk=lottery_id * 10,
            lottery_id=lottery_id,
            prize_vec=first_prize_vec,
            prize_cmt=first_prize_cmt,
            lottery_time=lottery_time,
        )
    ]
    if second_prize_vec is not None:
        ret_list.append(
            biliMilvusModel.BiliLotData(
                pk=lottery_id * 20,
                lottery_id=lottery_id,
                prize_vec=second_prize_vec,
                prize_cmt=second_prize_cmt,
                lottery_time=lottery_time,
            )
        )
    if third_prize_vec is not None:
        ret_list.append(
            biliMilvusModel.BiliLotData(
                pk=lottery_id * 30,
                lottery_id=lottery_id,
                prize_vec=third_prize_vec,
                prize_cmt=third_prize_cmt,
                lottery_time=lottery_time,
            )
        )
    return ret_list


async def search_lottery_text(
    query_text: str, limit: int = 10, offset=0
) -> List[models.Lotdata]:
    query_text = query_text.strip()
    if not query_text:
        return []
    if query_vec := await _create_embedding(query_text):
        res = await sql_helper.milvus_sql_helper.search_bili_lot_data(
            query_vec=query_vec, limit=limit, offset=offset
        )
        lottery_id_ls = [x.get("entity").get("lottery_id") for x in res[0]]
        lot_data_ls = await DynDetailSqlHelperMysqlVer.grpc_sql_helper.get_lotDetail_ls_by_lot_ids(
            lottery_id_ls
        )
        return list(lot_data_ls)
    return []


async def get_lottery_entity_num() -> int:
    if res := await sql_helper.milvus_sql_helper.get_bili_lot_data_collection_stats():
        return res.get("row_count") or 0
    return 0

if __name__ == "__main__":
    result = asyncio.run(_create_embedding("你好"))
    print(result)