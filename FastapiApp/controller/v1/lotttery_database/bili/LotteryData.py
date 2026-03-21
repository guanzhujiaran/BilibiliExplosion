"""
单轮回复
"""

from typing import List

from fastapi import Query, Body
from fastapi_cache.decorator import cache
from Models.common import CommonResponseModel, ResponsePaginationItems
from Models.lottery_database.bili.LotteryDataModels import (
    AddDynamicLotteryResp,
    CommonLotteryResp,
    OfficialLotteryResp,
    AllLotteryResp,
    ChargeLotteryResp,
    ReserveInfoResp,
    TopicLotteryResp,
    LiveLotteryResp,
    AddDynamicLotteryReq,
    AddTopicLotteryReq,
    BulkAddDynamicLotteryReq,
    LotdataResp,
    AddTopicLotteryResp,
)
from Service.LangChainCompo.text_embed import search_lottery_text
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.lottery_database.bili_lotterty import (
    get_common_lottery,
    get_reserve_lottery,
    get_official_lottery,
    get_all_lottery,
    get_charge_lottery,
    get_topic_lottery,
    get_live_lottery,
    add_dynamic_lottery_by_dynamic_id,
    add_topic_lottery,
)
from Utils.Common import asyncio_gather
from .base import new_router

router = new_router()


# region get方法
@router.get(
    "/GetCommonLottery",
    summary="获取数据库里存放的一般抽奖",
    response_model=CommonResponseModel[list[CommonLotteryResp]],
    response_model_exclude_none=True,
)
@cache(1 * 3600)
async def api_GetCommonLottery(round_num: int = Query(ge=1, le=10, default=2)):
    result = await get_common_lottery(round_num)
    return CommonResponseModel(data=result)


@router.get(
    "/GetReserveLottery",
    summary="获取必抽的预约抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ReserveInfoResp]],
    description="""获取必抽的预约抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
async def api_GetMustReserveLottery(
    limit_time: int = Query(ge=0, le=2**128, default=3 * 24 * 3600),
    page_num: int = Query(ge=0, default=0, description="当前页数"),
    page_size: int = Query(ge=0, default=0, description="每页的条数"),
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
    result_items, total = await get_reserve_lottery(limit_time, page_num, page_size)
    return CommonResponseModel(
        data=ResponsePaginationItems[ReserveInfoResp](items=result_items, total=total)
    )


@router.get(
    "/GetOfficialLottery",
    summary="获取必抽的官方抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[OfficialLotteryResp]],
    description="""获取必抽的官方抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
async def api_GetMustOfficialLottery(
    limit_time: int = Query(ge=0, le=2**128, default=3 * 24 * 3600),
    page_num: int = Query(ge=0, default=0, description="当前页数"),
    page_size: int = Query(ge=0, default=0, description="每页的条数"),
):
    """
    获取必抽的官方抽奖数据
    当page_num和page_size任一为0时，返回svm判断过的必抽的数据
    否则返回分页了的全部数据
    :param limit_time:
    :return:
    """
    result_items, total = await get_official_lottery(limit_time, page_num, page_size)
    return CommonResponseModel(
        data=ResponsePaginationItems[OfficialLotteryResp](
            items=result_items, total=total
        )
    )


@router.get(
    "/GetChargeLottery",
    summary="获取必抽的充电抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ChargeLotteryResp]],
    description="""获取必抽的官方抽奖数据
当page_num和page_size任一为0时，返回svm判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
async def api_GetChargeLottery(
    limit_time: int = Query(ge=0, le=2**128, default=3 * 24 * 3600),
    page_num: int = Query(ge=0, default=0, description="当前页数"),
    page_size: int = Query(ge=0, default=0, description="每页的条数"),
):
    """
    获取必抽的官方抽奖数据
    当page_num和page_size任一为0时，返回svm判断过的必抽的数据
    否则返回分页了的全部数据
    :param limit_time:
    :return:
    """
    result_items, total = await get_charge_lottery(limit_time, page_num, page_size)
    return CommonResponseModel(
        data=ResponsePaginationItems[ChargeLotteryResp](items=result_items, total=total)
    )


@router.get(
    "/GetLiveLottery",
    summary="获取所有直播抽奖数据（分页）",
    response_model=CommonResponseModel[ResponsePaginationItems[LiveLotteryResp]],
    response_model_exclude_none=True,
)
async def api_GetLiveLottery(
    page_num: int = Query(ge=0, default=0, description="当前页数"),
    page_size: int = Query(ge=0, default=0, description="每页的条数"),
):
    result_items, total = await get_live_lottery(page_num, page_size)
    return CommonResponseModel(
        data=ResponsePaginationItems[LiveLotteryResp](items=result_items, total=total)
    )


@router.get(
    "/GetTopicLottery",
    summary="获取所有话题抽奖数据（分页）",
    response_model=CommonResponseModel[ResponsePaginationItems[TopicLotteryResp]],
    response_model_exclude_none=True,
)
async def api_GetTopicLottery(
    page_num: int = Query(ge=0, default=0, description="当前页数"),
    page_size: int = Query(ge=0, default=0, description="每页的条数"),
):
    result_items, total = await get_topic_lottery(page_num, page_size)
    return CommonResponseModel(
        data=ResponsePaginationItems[TopicLotteryResp](items=result_items, total=total)
    )


@router.get(
    "/GetAllLottery",
    summary="获取一轮的所有抽奖信息",
    response_model=CommonResponseModel[AllLotteryResp],
    description="""
获取svm判断过的必抽的预约抽奖数据和官方抽奖数据    
        """,
    response_model_exclude_none=True,
)
async def api_GetAllLottery(
    round_num: int = Query(
        ge=1,
    )
):
    result = await get_all_lottery(round_num)
    return CommonResponseModel(data=result)


# endregion


# region a添加抽奖
@router.post(
    "/AddDynamicLottery",
    summary="提交抽奖动态(官抽，预约，充电)，自动解析抽奖信息",
    response_model=CommonResponseModel[AddDynamicLotteryResp],
    response_model_exclude_none=True,
)
@cache(8 * 3600)
async def api_AddLottery(
    data: AddDynamicLotteryReq = Body(...),
):
    resp: AddDynamicLotteryResp = await add_dynamic_lottery_by_dynamic_id(
        data.dynamic_id_or_url
    )
    return CommonResponseModel(data=resp)


@router.post(
    "/BulkAddDynamicLottery",
    summary="批量提交抽奖动态(官抽，预约，充电)，自动解析抽奖信息",
    response_model=CommonResponseModel[list[AddDynamicLotteryResp]],
    response_model_exclude_none=True,
)
@cache(8 * 3600)
async def api_BulkAddLottery(
    data: BulkAddDynamicLotteryReq = Body(...),
):
    resp = await asyncio_gather(
        *[add_dynamic_lottery_by_dynamic_id(d) for d in data.dynamic_id_or_urls]
    )
    return CommonResponseModel(data=resp)


@router.post(
    "/AddTopicLottery",
    summary="提交话题抽奖",
    response_model=CommonResponseModel[AddTopicLotteryResp],
    response_model_exclude_none=True,
)
@cache(8 * 3600)
async def api_AddTopicLottery(
    data: AddTopicLotteryReq = Body(...),
):
    resp: AddTopicLotteryResp = await add_topic_lottery(
        data.topic_id
    )  # 先同步执行一次，看看能不能成功，如果不成功就不加入后台任务了
    return CommonResponseModel(data=resp)


@router.get(
    "/SearchLotteryByKeyword",
    summary="根据关键词搜索抽奖信息",
    response_model=CommonResponseModel[List[LotdataResp]],
    response_model_exclude_none=True,
)
async def api_Search(
    keyword: str = Query(..., min_length=1),
):
    result: List[Lotdata] = await search_lottery_text(keyword)
    return CommonResponseModel(data=result)


# endregion
