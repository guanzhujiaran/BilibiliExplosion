"""
单轮回复
"""
from typing import Any
from fastapi import Query
from fastapi接口.models.common import CommonResponseModel, ResponsePaginationItems
from fastapi接口.models.lottery_database.redisModel.biliRedisModel import bili_live_lottery_redis
from .base import new_router
from fastapi接口.models.lottery_database.bili.LotteryDataModels import CommonLotteryResp, reserveInfo, \
    OfficialLotteryResp, AllLotteryResp, ChargeLotteryResp, ReserveInfoResp, TopicLotteryResp, LiveLotteryResp
from fastapi_cache.decorator import cache
from fastapi接口.service.lottery_database.bili_lotterty import GetCommonLottery, GetMustReserveLottery, \
    GetMustOfficialLottery, GetAllLottery, GetChargeLottery, GetTopicLottery, GetLiveLottery

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
            response_model=CommonResponseModel[
                ResponsePaginationItems[
                    ReserveInfoResp
                ]
            ],
            description="""获取必抽的预约抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据""")
@cache(1 * 3600)
async def api_GetMustReserveLottery(
        limit_time: int = Query(
            ge=0,
            le=2 ** 128,
            default=3 * 24 * 3600
        ),
        page_num: int = Query(ge=0, default=0, description='当前页数'),
        page_size: int = Query(ge=0, default=0, description='每页的条数')
):
    """
    获取必抽的预约抽奖数据
    当page_num和page_size任一为0时，返回svm判断过的必抽的数据
    否则返回分页了的全部数据
    :param page_num:
    :param page_size:
    :param limit_time:
    :return:
    """
    result_items, total = await GetMustReserveLottery(limit_time, page_num, page_size)
    return CommonResponseModel(data=ResponsePaginationItems[ReserveInfoResp](
        items=result_items,
        total=total
    ))


@router.get('/GetOfficialLottery', summary='获取必抽的官方抽奖数据',
            response_model=CommonResponseModel[
                ResponsePaginationItems[
                    OfficialLotteryResp
                ]
            ],
            description=
            """获取必抽的官方抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据"""
            )
@cache(1 * 3600)
async def api_GetMustOfficialLottery(
        limit_time: int = Query(
            ge=0,
            le=2 ** 128,
            default=3 * 24 * 3600
        ),
        page_num: int = Query(ge=0, default=0, description='当前页数'),
        page_size: int = Query(ge=0, default=0, description='每页的条数')
):
    """
    获取必抽的官方抽奖数据
    当page_num和page_size任一为0时，返回svm判断过的必抽的数据
    否则返回分页了的全部数据
    :param limit_time:
    :return:
    """
    result_items, total = await GetMustOfficialLottery(limit_time, page_num, page_size)
    return CommonResponseModel(data=ResponsePaginationItems[OfficialLotteryResp](
        items=result_items,
        total=total
    ))


@router.get('/GetChargeLottery', summary='获取必抽的充电抽奖数据',
            response_model=CommonResponseModel[
                ResponsePaginationItems[
                    ChargeLotteryResp
                ]
            ],
            description=
            """获取必抽的官方抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据"""
            )
@cache(1 * 3600)
async def api_GetChargeLottery(
        limit_time: int = Query(
            ge=0,
            le=2 ** 128,
            default=3 * 24 * 3600
        ),
        page_num: int = Query(ge=0, default=0, description='当前页数'),
        page_size: int = Query(ge=0, default=0, description='每页的条数')
):
    """
    获取必抽的官方抽奖数据
    当page_num和page_size任一为0时，返回svm判断过的必抽的数据
    否则返回分页了的全部数据
    :param limit_time:
    :return:
    """
    result_items, total = await GetChargeLottery(limit_time, page_num, page_size)
    return CommonResponseModel(data=ResponsePaginationItems[ChargeLotteryResp](
        items=result_items,
        total=total
    ))


@router.get('/GetLiveLottery', summary='获取所有直播抽奖数据（分页）',
            response_model=CommonResponseModel[ResponsePaginationItems[LiveLotteryResp]]
            )
async def api_GetLiveLottery(
        page_num: int = Query(ge=0, default=0, description='当前页数'),
        page_size: int = Query(ge=0, default=0, description='每页的条数')
):
    result_items, total = await GetLiveLottery(page_num, page_size)
    return CommonResponseModel(data=ResponsePaginationItems[LiveLotteryResp](
        items=result_items,
        total=total
    ))


@router.get('/GetTopicLottery', summary='获取所有话题抽奖数据（分页）',
            response_model=CommonResponseModel[ResponsePaginationItems[TopicLotteryResp]]
            )
async def api_GetTopicLottery(
        page_num: int = Query(ge=0, default=0, description='当前页数'),
        page_size: int = Query(ge=0, default=0, description='每页的条数')
):
    result_items, total = await GetTopicLottery(page_num, page_size)
    return CommonResponseModel(data=ResponsePaginationItems[TopicLotteryResp](
        items=result_items,
        total=total
    ))


@router.get('/GetAllLottery', summary="获取一轮的所有抽奖信息",
            response_model=CommonResponseModel[AllLotteryResp], description=
            """
获取svm判断过的必抽的预约抽奖数据和官方抽奖数据    
        """)
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
