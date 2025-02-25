"""
抽奖数据库分析数据
"""
from typing import Literal

from fastapi import Query

from fastapi接口.controller.v1.lotttery_database.bili.base import new_router
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticInfoResp, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticLotTypeEnum
from fastapi接口.service.lottery_database.lottery_statistic import GetLotStatisticInfo

router = new_router()


@router.get('/{lot_type}', response_model=CommonResponseModel[BiliLotStatisticInfoResp])
async def get_official_lottery_statistic(
        lot_type: BiliLotStatisticLotTypeEnum,
        rank_type: BiliLotStatisticRankTypeEnum = Query(...),
        offset: int = Query(ge=1),
        limit: int = Query(ge=10, le=10)):
    """获取官方抽奖统计信息"""

    return CommonResponseModel(data=await GetLotStatisticInfo(lot_type, rank_type, offset=offset - 1, limit=limit))
