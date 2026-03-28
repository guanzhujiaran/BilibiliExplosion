"""
单轮回复
"""

from typing import List, Optional

from fastapi import Query, Body, Request
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
    AddTopicLotteryResp,
    BulkAddDynamicLotteryReq,
    LotdataResp,
    SubmitFeedbackReq,
)
from Models.lottery_database.bili.comm import (
    LotteryPaginationParams,
    LotteryWithLimitTimePaginationParams,
    LotterySearchPaginationParams,
)
from Service.LangChainCompo.text_embed import (
    get_lottery_entity_num,
    search_lottery_text,
)
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
from Utils.PushMe import a_pushme
from .base import new_router

router = new_router()


# region get方法
@router.post(
    "/GetCommonLottery",
    summary="获取数据库里存放的一般抽奖",
    response_model=CommonResponseModel[list[CommonLotteryResp]],
    response_model_exclude_none=True,
)
@cache(1 * 3600)
async def api_GetCommonLottery(round_num: int = Query(ge=1, le=10, default=2)):
    result = await get_common_lottery(round_num)
    return CommonResponseModel(data=result)


@router.post(
    "/GetReserveLottery",
    summary="获取必抽的预约抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ReserveInfoResp]],
    description="""获取必抽的预约抽奖数据
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=30)
async def api_GetMustReserveLottery(
    pagination: LotteryWithLimitTimePaginationParams,
):
    """
    获取必抽的预约抽奖数据
    当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
    否则返回分页了的全部数据
    :param pagination:
    :return:
    """
    result_items, total = await get_reserve_lottery(
        pagination.limit_time, pagination.page_num, pagination.page_size
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[ReserveInfoResp](items=result_items, total=total)
    )


@router.post(
    "/GetOfficialLottery",
    summary="获取必抽的官方抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[OfficialLotteryResp]],
    description="""获取必抽的官方抽奖数据
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=30)
async def api_GetMustOfficialLottery(
    pagination: LotteryWithLimitTimePaginationParams,
):
    """
    获取必抽的官方抽奖数据
    当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
    否则返回分页了的全部数据
    :param pagination:
    :return:
    """
    result_items, total = await get_official_lottery(
        pagination.limit_time, pagination.page_num, pagination.page_size
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[OfficialLotteryResp](
            items=result_items, total=total
        )
    )


@router.post(
    "/GetChargeLottery",
    summary="获取必抽的充电抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ChargeLotteryResp]],
    description="""获取必抽的官方抽奖数据
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=30)
async def api_GetChargeLottery(
    pagination: LotteryWithLimitTimePaginationParams,
):
    """
    获取必抽的官方抽奖数据
    当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
    否则返回分页了的全部数据
    :param pagination:
    :return:
    """
    result_items, total = await get_charge_lottery(
        pagination.limit_time, pagination.page_num, pagination.page_size
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[ChargeLotteryResp](items=result_items, total=total)
    )


@router.post(
    "/GetLiveLottery",
    summary="获取所有直播抽奖数据（分页）",
    response_model=CommonResponseModel[ResponsePaginationItems[LiveLotteryResp]],
    response_model_exclude_none=True,
)
@cache(expire=30)
async def api_GetLiveLottery(
    pagination: LotteryPaginationParams,
):
    result_items, total = await get_live_lottery(
        pagination.page_num, pagination.page_size
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[LiveLotteryResp](items=result_items, total=total)
    )


@router.post(
    "/GetTopicLottery",
    summary="获取所有话题抽奖数据（分页）",
    response_model=CommonResponseModel[ResponsePaginationItems[TopicLotteryResp]],
    response_model_exclude_none=True,
)
@cache(expire=30)
async def api_GetTopicLottery(
    pagination: LotteryPaginationParams,
):
    result_items, total = await get_topic_lottery(
        pagination.page_num, pagination.page_size
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[TopicLotteryResp](items=result_items, total=total)
    )


@router.post(
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


@router.post(
    "/SearchLotteryByKeyword",
    summary="根据关键词搜索抽奖信息",
    response_model=CommonResponseModel[ResponsePaginationItems[LotdataResp]],
    response_model_exclude_none=True,
)
async def api_Search(
    pagination: LotterySearchPaginationParams,
):
    # 转换为 offset-limit 形式传递给底层函数
    offset = (pagination.page_num - 1) * pagination.page_size
    result: List[Lotdata] = await search_lottery_text(
        pagination.keyword, limit=pagination.page_size, offset=offset
    )
    total = await get_lottery_entity_num()
    return CommonResponseModel(data=ResponsePaginationItems(items=result, total=total))


@router.post(
    "/SubmitFeedback",
    summary="提交反馈信息到 PushMe",
    response_model=CommonResponseModel[dict],
    response_model_exclude_none=True,
)
async def api_SubmitFeedback(
    request: Request,
    data: SubmitFeedbackReq,
):
    """
    提交反馈信息到 PushMe
    会自动从请求头中获取 uid 信息
    :param request: FastAPI Request 对象
    :param data: 反馈请求体，包含 message 字段
    :return: 推送结果
    """
    # 从 header 中获取 uid，支持多种可能的 header 名称
    uid = (
        request.headers.get("x-bili-uid")
        or request.headers.get("x-bili-mid")
        or request.headers.get("uid")
        or "unknown"
    )

    title = f"抽奖数据库反馈 - UID: {uid}"

    try:
        resp = await a_pushme(title=title, content=data.message, push_type="text")
        if resp.status_code == 200:
            return CommonResponseModel(
                code=0,
                msg="success",
                data={
                    "status": "success",
                    "message": "反馈已提交",
                    "uid": uid,
                },
            )
        else:
            return CommonResponseModel(
                code=resp.status_code,
                msg="推送失败",
                data={
                    "status": "failed",
                    "message": f"反馈提交失败：HTTP {resp.status_code}",
                    "uid": uid,
                },
            )
    except Exception as e:
        return CommonResponseModel(
            code=-1,
            msg="异常错误",
            data={
                "status": "error",
                "message": f"提交失败：{str(e)}",
                "uid": uid,
            },
        )


# endregion
