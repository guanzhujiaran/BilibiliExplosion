import asyncio
from fastapi接口.dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, WinnerInfo, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum


async def GetLotStatisticInfo(lot_type: BiliLotStatisticLotTypeEnum, rank_type: BiliLotStatisticRankTypeEnum,
                              offset: int,
                              limit: int = 10) -> BiliLotStatisticInfoResp:
    """
    获取所有转发抽奖的中奖情况统计
    :param lot_type:
    :param rank_type:
    :param offset:
    :param limit:
    :return:
    """
    dyn_lot_sync_ts = await lottery_data_statistic_redis.get_sync_ts(lot_type)
    return BiliLotStatisticInfoResp(winners=[WinnerInfo(uid=uid, count=count) for uid, count in
                                             await lottery_data_statistic_redis.get_lot_prize_count(lot_type, rank_type,
                                                                                                    offset, limit)],
                                    sync_ts=dyn_lot_sync_ts)


if __name__ == '__main__':
    async def _test():
        a = await GetLotStatisticInfo("total", offset=0, limit=10)
        print(a)


    asyncio.run(_test())
