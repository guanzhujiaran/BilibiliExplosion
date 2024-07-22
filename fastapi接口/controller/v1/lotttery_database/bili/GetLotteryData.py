"""
单轮回复
"""
from fastapi import Query
from fastapi接口.models.common import CommonResponseModel
from .base import new_router
from fastapi接口.models.lottery_database.bili.LotteryDataModels import CommonLotteryResp, reserveInfo, \
    OfficialLotteryResp, AllLotteryResp
from fastapi_cache.decorator import cache
from fastapi接口.service.lottery_database.bili_lotterty import GetCommonLottery, GetMustReserveLottery, \
    GetMustOfficialLottery, GetAllLottery

router = new_router()


@router.get('/GetCommonLottery', summary='获取数据库里存放的一般抽奖',
            response_model=CommonResponseModel[list[CommonLotteryResp]])
@cache(8 * 3600)
async def api_GetCommonLottery(round_num: int = Query(
    ge=1,
    le=10,
    default=2
)):
    """
    获取极验点击中心
    :param round_num:
    :return:
    """
    result = await GetCommonLottery(round_num)
    return CommonResponseModel(data=result)


@router.get('/GetReserveLottery', summary='获取必抽的预约抽奖数据',
            response_model=CommonResponseModel[list[reserveInfo]])
@cache(8 * 3600)
async def api_GetMustReserveLottery(limit_time: int = Query(
    ge=8 * 3600,
    le=2 ** 128,
    default=3 * 24 * 3600
)):
    """
    获取极验点击中心
    :param limit_time:
    :return:
    """
    result = await GetMustReserveLottery(limit_time)
    return CommonResponseModel(data=result)


@router.get('/GetOfficialLottery', summary='获取必抽的官方抽奖数据',
            response_model=CommonResponseModel[list[OfficialLotteryResp]])
@cache(8 * 3600)
async def api_GetMustOfficialLottery(limit_time: int = Query(
    ge=8 * 3600,
    le=2 ** 128,
    default=3 * 24 * 3600
)):
    """
    获取极验点击中心
    :param limit_time:
    :return:
    """
    result = await GetMustOfficialLottery(limit_time)
    return CommonResponseModel(data=result)


@router.get('/GetAllLottery', summary="获取一轮的所有抽奖信息",
            response_model=CommonResponseModel[AllLotteryResp])
@cache(8 * 3600)
async def api_GetAllLottery(
        limit_time: int = Query(
            ge=8 * 3600,
            le=2 ** 128,
            default=3 * 24 * 3600
        ),
        round_num: int = Query(
            ge=1,
            le=10,
            default=2
        )
):
    result = await GetAllLottery(limit_time, round_num)
    return CommonResponseModel(data=result)
