import asyncio
from typing import List

from openai import AsyncOpenAI

import fastapi接口.models.lottery_database.milvusModel.biliMilvusModel as biliMilvusModel
import fastapi接口.Service.LangChainCompo.lottery_data_vec_sql.sql_helper as sql_helper
import fastapi接口.Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer as DynDetailSqlHelperMysqlVer
import fastapi接口.Service.GrpcModule.GrpcSrc.SQLObject.models as models
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
    async def _test_lot_data_2_bili_lot_data_ls():
        lot_data =  models.Lotdata(**{'lottery_id': 88643, 'business_id': 534667, 'status': 2, 'lottery_time': 1648814400, 'lottery_at_num': 0, 'lottery_feed_limit': 0, 'first_prize': 1, 'second_prize': 2, 'third_prize': 5, 'lottery_result': '{"first_prize_result": [{"uid": 327405750, "name": "周一鸡", "face": "https://i0.hdslb.com/bfs/face/38c05d446ccd369e5577eae5b0412d12975a2f79.jpg", "hongbao_money": 0}], "second_prize_result": [{"uid": 919401, "name": "-several-", "face": "https://i0.hdslb.com/bfs/face/9db3469aa10d4a9667d38bc11c1081ee56efab74.jpg", "hongbao_money": 0}, {"uid": 1647448420, "name": "初叶未央", "face": "https://i1.hdslb.com/bfs/face/f6283626d0bed65a9dde913fef656bb5a4daba79.jpg", "hongbao_money": 0}], "third_prize_result": [{"uid": 140892283, "name": "测啛啛喳喳", "face": "https://i1.hdslb.com/bfs/face/8f7ca97ba1729aa5d79a1836a199a0acd55a22ab.jpg", "hongbao_money": 0}, {"uid": 153734214, "name": "灼灼_aiorlove", "face": "https://i0.hdslb.com/bfs/face/c8e9c1eba9f3842a4e6704f55ff7bdb6eaeafe78.jpg", "hongbao_money": 0}, {"uid": 162959479, "name": "依赖成折磨12138", "face": "https://i1.hdslb.com/bfs/face/f3c97588bcc642e1ce9e74f4cfcf23829695236c.jpg", "hongbao_money": 0}, {"uid": 226365744, "name": "研究魔法的工程师", "face": "http://i0.hdslb.com/bfs/face/9036f03d125df2e74dfb3b1d48e196e1e10930bf.jpg", "hongbao_money": 0}, {"uid": 315605858, "name": "柠檬时常换名字", "face": "https://i2.hdslb.com/bfs/face/390046a5b0da27a0482c4b4b93efe346ea29fe04.jpg", "hongbao_money": 0}]}', 'first_prize_cmt': '现金66', 'second_prize_cmt': '现金33', 'third_prize_cmt': '现金11', 'first_prize_pic': '', 'second_prize_pic': '', 'third_prize_pic': '', 'need_post': 0, 'business_type': 10, 'sender_uid': 42231128, 'prize_type_first': '{"type": 0, "value": {"stype": 0, "count": 0}}', 'prize_type_second': '{"type": 0, "value": {"stype": 0, "count": 0}}', 'prize_type_third': '{"type": 0, "value": {"stype": 0, "count": 0}}', 'pay_status': None, 'ts': 1756615130, '_gt_': None, 'has_charge_right': False, 'lottery_detail_url': 'https://www.bilibili.com/h5/lottery/result?business_id=534667&business_type=10&lottery_id=88643', 'participants': 0, 'participated': False, 'vip_batch_sign': '', 'exclusive_level': None, 'followed': False, 'reposted': False, 'custom_extra_key': '{"vip_redirect_url": "", "upower_redirect_url": ""}', 'created_at': None, 'updated_at': None}
)
        da = await lot_data_2_bili_lot_data_ls(lot_data)
        print(da)
    asyncio.run(_test_lot_data_2_bili_lot_data_ls())
