import asyncio

from fastapi接口.service.compo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from fastapi接口.service.compo.text_embed import save_bili_lot_data_embeddings, lot_data_2_bili_lot_data_ls
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper

async def sync_bili_lottery_data():
    all_lot_data = await grpc_sql_helper.get_all_lot_before_lottery_time()
    for x in all_lot_data:
        da = await lot_data_2_bili_lot_data_ls(x)
        await save_bili_lot_data_embeddings(data_ls=da)

async def del_outdated_bili_lottery_data():
    await milvus_sql_helper.del_outdated_bili_lottery_data()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sync_bili_lottery_data())
