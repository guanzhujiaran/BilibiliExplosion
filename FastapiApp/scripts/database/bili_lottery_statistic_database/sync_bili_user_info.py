from Models.lottery_database.bili.LotteryDataModels import BiliLotStatisticRankTypeEnum
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
import asyncio


async def main():
    await grpc_sql_helper.sync_all_lottery_result_2_bili_user_info()


if __name__ == '__main__':
    asyncio.run(main())
