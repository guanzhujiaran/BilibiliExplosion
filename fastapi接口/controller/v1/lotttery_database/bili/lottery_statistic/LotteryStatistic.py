"""
抽奖数据库分析数据
"""
from typing import Literal, Optional

from fastapi import Query

from fastapi接口.controller.v1.lotttery_database.bili.base import new_router
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum, BiliLotStatisticLotteryResultResp
from fastapi接口.service.lottery_database.lottery_statistic import GetLotStatisticInfo, GetLotteryResult

router = new_router()


@router.get('/{lot_type}',
            description='获取中奖数据的分析情况，返回[{uid:中奖数}...]',
            response_model=CommonResponseModel[BiliLotStatisticInfoResp])
async def get_official_lottery_statistic(
        lot_type: BiliLotStatisticLotTypeEnum,
        rank_type: BiliLotStatisticRankTypeEnum = Query(...),
        offset: Optional[int] = Query(0, ge=0),
        limit: Optional[int] = Query(10,ge=10, le=10)
):
    """获取官方抽奖统计信息"""

    return CommonResponseModel(data=await GetLotStatisticInfo(lot_type, rank_type, offset=offset, limit=limit))


@router.get('/lottery_result',
            description='根据uid获取某个b站用户的数据库中的中奖数据',
            response_model=CommonResponseModel[BiliLotStatisticLotteryResultResp])
async def get_lottery_result(
        uid: int | str = Query(...),
        lot_type: BiliLotStatisticLotTypeEnum = Query(...),
        rank_type: BiliLotStatisticRankTypeEnum = Query(...),
        offset: Optional[int] = Query(0, ge=0),
        limit: Optional[int] = Query(10, ge=10, le=10)
):
    return CommonResponseModel(data=await GetLotteryResult(uid, lot_type, rank_type, offset=offset, limit=limit))
