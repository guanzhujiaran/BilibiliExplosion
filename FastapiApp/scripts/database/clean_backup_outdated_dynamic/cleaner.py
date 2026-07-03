from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Service.GrpcModule.GrpcSrc.根据日期获取抽奖动态.getLotDynSortByDate import LotDynSortByDate
from Service.GrpcModule.Models.getLotDynSortByDate import MainConf
from Utils.通用.dynamic_id_caculate import dynamic_id_2_ts
import asyncio


async def do_clean():
    first_dyn = await grpc_sql_helper.get_rid_bili_dyn_detail(is_asc=True, is_available_data=True)
    latest_dyn = await grpc_sql_helper.get_rid_bili_dyn_detail(is_asc=False, is_available_data=True)
    if not latest_dyn:
        return
    lot_dyn_sort_by_date = LotDynSortByDate()
    latest_dyn_ts = dynamic_id_2_ts(latest_dyn.dynamic_id_int)
    first_dyn_ts = dynamic_id_2_ts(first_dyn.dynamic_id_int)
    between_ts = [first_dyn_ts - 10000, latest_dyn_ts - 10 * 24 * 60 * 60]
    print(f'between_ts: {between_ts}')
    await lot_dyn_sort_by_date.main(
        conf=MainConf(
            between_ts=between_ts,
            is_gen_zip=True,
            is_delete_generated_data=True
        )
    )


if __name__ == '__main__':
    asyncio.run(do_clean())
