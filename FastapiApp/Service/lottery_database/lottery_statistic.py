from dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from dao.biliLotteryStatisticSqlHelper import lottery_data_statistic_sql_helper
from log.base_log import myfastapi_logger
from Models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, WinnerInfo, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum, BiliLotStatisticLotteryResultResp, \
    BiliLotStatisticRankDateTypeEnum, BiliUserInfoSimple
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Utils.通用.Common import asyncio_gather
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict


async def GetLotStatisticInfo(
        date: BiliLotStatisticRankDateTypeEnum,
        lot_type: BiliLotStatisticLotTypeEnum,
        rank_type: BiliLotStatisticRankTypeEnum,
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
    dyn_lot_sync_ts = await lottery_data_statistic_redis.get_sync_ts(lot_type)
    bili_user_info_list, total = await lottery_data_statistic_sql_helper.get_lot_prize_count(
        offset=offset,
        limit=limit,
        date=date,
        lot_type=lot_type,
        rank_type=rank_type
    )
    return BiliLotStatisticInfoResp(
        winners=[
            WinnerInfo(
                user=BiliUserInfoSimple(
                    uid=str(x.BiliUserInfo.uid),
                    name=x.BiliUserInfo.name,
                    face=x.BiliUserInfo.face
                ), count=x.prize_count,
                rank=x.atari_rank
            )
            for x in bili_user_info_list
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
    (prize_result, total), user = await asyncio_gather(
        grpc_sql_helper.get_lottery_result(
            uid=uid,
            business_type=lot_type.business_type,
            rank_type=rank_type,
            offset=offset,
            limit=limit,
            start_ts=start_ts,
            end_ts=end_ts
        ),
        lottery_data_statistic_sql_helper.get_bili_user_info(uid),
        log=myfastapi_logger
    )
    return BiliLotStatisticLotteryResultResp(
        user=user,
        prize_result=[grpc_sql_helper.preprocess_ret_data(
            sqlalchemy_model_2_dict(x)
        ) for x in prize_result],
        total=total
    )


if __name__ == '__main__':
    import asyncio


    async def _test_GetLotStatisticInfo():
        lottery_data_statistic_sql_helper.engine.echo = True
        for i in BiliLotStatisticRankDateTypeEnum:
            for j in BiliLotStatisticLotTypeEnum:
                for l in BiliLotStatisticRankTypeEnum:
                    ret = await GetLotStatisticInfo(
                        date=i,
                        lot_type=j,
                        rank_type=l,
                        offset=0,
                        limit=10
                    )
                    print(ret)
                    assert len(
                        ret.winners) == 10 or i in (BiliLotStatisticRankDateTypeEnum.month,
                                                    BiliLotStatisticRankDateTypeEnum.pre_month)


    asyncio.run(_test_GetLotStatisticInfo())
