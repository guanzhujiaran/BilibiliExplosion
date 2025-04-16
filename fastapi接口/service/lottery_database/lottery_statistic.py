import asyncio

from fastapi接口.dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, WinnerInfo, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum, BiliLotStatisticLotteryResultResp, \
    BiliLotStatisticRankDateTypeEnum
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper


async def GetLotStatisticInfo(
        date: BiliLotStatisticRankDateTypeEnum,
        lot_type: BiliLotStatisticLotTypeEnum, rank_type: BiliLotStatisticRankTypeEnum,
        offset: int,
        limit: int = 10) -> BiliLotStatisticInfoResp:
    """
    获取所有转发抽奖的中奖情况统计
    :param date:
    :param lot_type:
    :param rank_type:
    :param offset:
    :param limit:
    :return:
    """
    uid_count_list = await lottery_data_statistic_redis.get_lot_prize_count(
        date=date,
        lot_type=lot_type,
        rank_type=rank_type,
        offset=offset,
        limit=limit
    )
    uid_count_dict = dict(uid_count_list)
    uid_list = list(uid_count_dict.keys())
    users, dyn_lot_sync_ts, rank_dict, total = await asyncio.gather(
        lottery_data_statistic_redis.get_bili_user_info_bulk(uid_list),
        lottery_data_statistic_redis.get_sync_ts(lot_type),
        lottery_data_statistic_redis.get_lot_prize_rank_bulk(date=date, lot_type=lot_type, rank_type=rank_type,
                                                             uid_arr=uid_list),
        lottery_data_statistic_redis.get_lot_prize_total(date=date, lot_type=lot_type, rank_type=rank_type)
    )
    users_dict = {user.uid: user for user in users}

    return BiliLotStatisticInfoResp(
        winners=[WinnerInfo(user=users_dict.get(uid), count=count, rank=rank_dict.get(uid) + 1) for uid, count in
                 uid_count_list
                 ],
        sync_ts=dyn_lot_sync_ts,
        total=total
    )


async def GetLotteryResult(
        uid: int | str,
        date: BiliLotStatisticRankDateTypeEnum = BiliLotStatisticRankDateTypeEnum.total,
        lot_type: BiliLotStatisticLotTypeEnum = None,
        rank_type: BiliLotStatisticRankTypeEnum = None,
        offset: int = None,
        limit: int = None
) -> BiliLotStatisticLotteryResultResp:
    uid = int(uid)
    start_ts, end_ts = date.get_start_end_ts()
    (prize_result, total), user = await asyncio.gather(
        grpc_sql_helper.get_lottery_result(
            uid=uid,
            business_type=BiliLotStatisticLotTypeEnum.lot_type_2_business_type(lot_type),
            rank_type=rank_type,
            offset=offset,
            limit=limit,
            start_ts=start_ts,
            end_ts=end_ts
        ),
        lottery_data_statistic_redis.get_bili_user_info(uid)
    )
    return BiliLotStatisticLotteryResultResp(
        user=user,
        prize_result=[grpc_sql_helper.preprocess_ret_data(
            sqlalchemy_model_2_dict(x)
        ) for x in prize_result],
        total=total
    )


if __name__ == '__main__':
    from fastapi接口.log.base_log import myfastapi_logger


    async def _test():
        myfastapi_logger.info(1)
        a = await GetLotteryResult(
            355911360,
            BiliLotStatisticLotTypeEnum.official,
            BiliLotStatisticRankTypeEnum.first,
            offset=0,
            limit=10
        )
        myfastapi_logger.info(a)


    asyncio.run(_test())
