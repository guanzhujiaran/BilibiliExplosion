import asyncio

from log.base_log import milvus_db_logger
from Service.LangChainCompo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from Service.LangChainCompo.text_embed import save_bili_lot_data_embeddings, lot_data_2_bili_lot_data_ls
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Utils.通用.Common import log_max_count_retry_wrapper


@log_max_count_retry_wrapper()
async def sync_bili_lottery_data():
    all_lot_data = await grpc_sql_helper.get_all_lot_before_lottery_time()
    milvus_db_logger.debug(f"开始同步数据，数据量：{len(all_lot_data)}")
    for x in all_lot_data:
        milvus_db_logger.debug(f"开始同步数据：{x}")
        da = await lot_data_2_bili_lot_data_ls(x)
        await save_bili_lot_data_embeddings(data_ls=da)


async def del_outdated_bili_lottery_data():
    await milvus_sql_helper.del_outdated_bili_lottery_data()


if __name__ == "__main__":
    async def _test():
        await sync_bili_lottery_data()
        await del_outdated_bili_lottery_data()


    asyncio.run(_test())
