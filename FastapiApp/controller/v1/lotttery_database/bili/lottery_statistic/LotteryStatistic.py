"""
抽奖数据库分析数据
"""
from typing import Literal, Optional

from fastapi import Query

from ApiRoutes import RouterPaths, RouterNames
from controller.v1.lotttery_database.bili.base import new_router
from Models.common import CommonResponseModel
from Models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum, BiliLotStatisticLotteryResultResp, \
    BiliLotStatisticRankDateTypeEnum
from Service.lottery_database.lottery_statistic import GetLotStatisticInfo, GetLotteryResult

router = new_router()


@router.get(RouterPaths.GET_LOTTERY_HOF,
            name=RouterNames.GET_LOTTERY_HOF,
            summary="获取官方抽奖统计信息",
            description='获取中奖数据的分析情况，返回[{uid:中奖数}...]',
            response_model=CommonResponseModel[BiliLotStatisticInfoResp]
            )
async def get_official_lottery_statistic(
        lot_type: BiliLotStatisticLotTypeEnum,
        rank_type: BiliLotStatisticRankTypeEnum = Query(...),
        offset: Optional[int] = Query(0, ge=0),
        limit: Optional[int] = Query(10, ge=10, le=10),
        date: BiliLotStatisticRankDateTypeEnum = BiliLotStatisticRankDateTypeEnum.total
):
    """获取官方抽奖统计信息"""

    return CommonResponseModel(
        data=await GetLotStatisticInfo(date=date, lot_type=lot_type, rank_type=rank_type, offset=offset, limit=limit)
    )


@router.get(RouterPaths.GET_LOTTERY_RESULT,
            name=RouterNames.GET_LOTTERY_RESULT,
            summary="获取uid中奖数据",
            description='根据uid获取某个b站用户的数据库中的中奖数据',
            response_model=CommonResponseModel[BiliLotStatisticLotteryResultResp]
            )
async def get_lottery_result(
        uid: int | str = Query(...),
        lot_type: BiliLotStatisticLotTypeEnum = Query(...),
        rank_type: BiliLotStatisticRankTypeEnum = Query(...),
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=10, le=50),
        date: BiliLotStatisticRankDateTypeEnum = BiliLotStatisticRankDateTypeEnum.total
):
    return CommonResponseModel(
        data=await GetLotteryResult(
            date=date,
            uid=uid,
            lot_type=lot_type,
            rank_type=rank_type,
            offset=offset,
            limit=limit)
    )
