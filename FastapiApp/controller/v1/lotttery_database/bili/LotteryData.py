"""
单轮回复
"""

import time
from typing import List, Optional
from Models.lottery_database.bili.LotteryDataModels import EndpointFilterMeta
from fastapi import Query, Body, Request, Depends
from fastapi_cache.decorator import cache
from Models.common import CommonResponseModel, ResponsePaginationItems
from Models.lottery_database.bili.LotteryDataBaseQueryModels import (
    BiliLotDataQueryModel,
)
from Models.lottery_database.bili.LotteryDataModels import (
    AddDynamicLotteryResp,
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
    BulkAddTopicLotteryReq,
    BulkAddOthersLotDynReq,
    LotdataResp,
    SubmitFeedbackReq,
    OthersLotDynItem,
    OthersLotDynSortEnum,
    OthersLotDynSortOrderEnum,
    TimePresetEnum,
    LotteryFilterParamsResp,
    OthersLotPrizeInfo,
    LotExtraInfoResp,
)
from Models.lottery_database.bili.comm import (
    LotteryPaginationParams,
    LotterySearchPaginationParams,
    LotteryAdvancedQueryParams,
    OthersLotDynListFilterMetadata,
)
from Models.lottery_database.bili.LotteryDataModels import (
    pydantic_model_to_filter_params,
)
from Models.v1.background_service.background_service_model import AllLotScrapyStatusResp
from Service.BackgroundServiceStatus.GetScrapyStaus import get_scrapy_status
from Service.LangChainCompo.text_embed import (
    get_lottery_entity_num,
    search_lottery_text,
)
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.lottery_database.bili_lotterty import (
    get_reserve_lottery,
    get_official_lottery,
    get_all_lottery,
    get_charge_lottery,
    get_topic_lottery,
    get_live_lottery,
    add_dynamic_lottery_by_dynamic_id,
    add_topic_lottery,
    add_others_lot_dyn_by_dynamic_id,
    process_others_lot_dyn,
)
from Models.lottery_database.bili.comm import BiliLotDataStatusEnum, LotteryBusinessType
from Utils.通用.Common import asyncio_gather
from Utils.推送.PushMe import a_pushme
from Utils.网关.gateway_auth import require_gateway_login, GatewayUserInfo
from ApiRoutes import RouterPaths, RouterNames
from fastapi import BackgroundTasks
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper

from .base import new_router

router = new_router()


def _parse_status(status: Optional[str]) -> BiliLotDataStatusEnum | None:
    """将字符串状态转为 BiliLotDataStatusEnum，不传则返回 None（不过滤状态）"""
    if not status:
        return None
    status_map = {
        "unfinished": BiliLotDataStatusEnum.UNFINISHED,
        "finished": BiliLotDataStatusEnum.FINISHED,
        "canceled": BiliLotDataStatusEnum.CANCELED,
        "deleted": BiliLotDataStatusEnum.DELETED,
        "unknown": BiliLotDataStatusEnum.UNKNOWN,
    }
    return status_map.get(status.lower())


# region get方法
@router.post(
    RouterPaths.GET_RESERVE_LOTTERY,
    name=RouterNames.GET_RESERVE_LOTTERY,
    summary="获取必抽的预约抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ReserveInfoResp]],
    description="""获取必抽的预约抽奖数据，支持高级筛选。
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=180)
async def api_GetMustReserveLottery(
    pagination: LotteryAdvancedQueryParams, background_task: BackgroundTasks
):
    result_items, total = await get_reserve_lottery(
        q=BiliLotDataQueryModel(
            business_type=LotteryBusinessType.Reserve,
            status=_parse_status(pagination.status),
            page_num=pagination.page_num,
            page_size=pagination.page_size,
            start_ts=pagination.start_ts,
            end_ts=pagination.end_ts,
            sender_uid=pagination.sender_uid,
            min_participants=pagination.min_participants,
            max_participants=pagination.max_participants,
            keyword=pagination.keyword,
            created_at_preset=pagination.created_at_preset,
            pub_time_preset=pagination.pub_time_preset,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            is_grand_prize=pagination.is_grand_prize,
        ),
        background_task=background_task,
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[ReserveInfoResp](items=result_items, total=total)
    )


@router.post(
    RouterPaths.GET_OFFICIAL_LOTTERY,
    name=RouterNames.GET_OFFICIAL_LOTTERY,
    summary="获取必抽的官方抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[OfficialLotteryResp]],
    description="""获取必抽的官方抽奖数据，支持高级筛选。
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=180)
async def api_GetMustOfficialLottery(
    pagination: LotteryAdvancedQueryParams,
):
    result_items, total = await get_official_lottery(
        q=BiliLotDataQueryModel(
            business_type=LotteryBusinessType.Official,
            status=_parse_status(pagination.status),
            page_num=pagination.page_num,
            page_size=pagination.page_size,
            start_ts=pagination.start_ts,
            end_ts=pagination.end_ts,
            sender_uid=pagination.sender_uid,
            min_participants=pagination.min_participants,
            max_participants=pagination.max_participants,
            keyword=pagination.keyword,
            created_at_preset=pagination.created_at_preset,
            pub_time_preset=pagination.pub_time_preset,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            is_grand_prize=pagination.is_grand_prize,
        )
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[OfficialLotteryResp](
            items=result_items, total=total
        )
    )


@router.post(
    RouterPaths.GET_CHARGE_LOTTERY,
    name=RouterNames.GET_CHARGE_LOTTERY,
    summary="获取必抽的充电抽奖数据",
    response_model=CommonResponseModel[ResponsePaginationItems[ChargeLotteryResp]],
    description="""获取必抽的充电抽奖数据，支持高级筛选。
当 page_num 和 page_size 任一为 0 时，返回 svm 判断过的必抽的数据
否则返回分页了的全部数据""",
    response_model_exclude_none=True,
)
@cache(expire=180)
async def api_GetChargeLottery(
    pagination: LotteryAdvancedQueryParams,
):
    result_items, total = await get_charge_lottery(
        q=BiliLotDataQueryModel(
            business_type=LotteryBusinessType.Charge,
            status=_parse_status(pagination.status),
            page_num=pagination.page_num,
            page_size=pagination.page_size,
            start_ts=pagination.start_ts,
            end_ts=pagination.end_ts,
            sender_uid=pagination.sender_uid,
            min_participants=pagination.min_participants,
            max_participants=pagination.max_participants,
            keyword=pagination.keyword,
            created_at_preset=pagination.created_at_preset,
            pub_time_preset=pagination.pub_time_preset,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            is_grand_prize=pagination.is_grand_prize,
        )
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[ChargeLotteryResp](items=result_items, total=total)
    )


@router.post(
    RouterPaths.GET_LIVE_LOTTERY,
    name=RouterNames.GET_LIVE_LOTTERY,
    summary="获取所有直播抽奖数据（分页）",
    response_model=CommonResponseModel[ResponsePaginationItems[LiveLotteryResp]],
    response_model_exclude_none=True,
)
@cache(expire=180)
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
    RouterPaths.GET_TOPIC_LOTTERY,
    name=RouterNames.GET_TOPIC_LOTTERY,
    summary="获取所有话题抽奖数据（分页+筛选）",
    response_model=CommonResponseModel[ResponsePaginationItems[TopicLotteryResp]],
    response_model_exclude_none=True,
)
@cache(expire=180)
async def api_GetTopicLottery(
    pagination: LotteryAdvancedQueryParams,
):
    result_items, total = await get_topic_lottery(
        pagination.page_num, pagination.page_size, keyword=pagination.keyword,
    )
    return CommonResponseModel(
        data=ResponsePaginationItems[TopicLotteryResp](items=result_items, total=total)
    )


@router.post(
    RouterPaths.GET_ALL_LOTTERY,
    name=RouterNames.GET_ALL_LOTTERY,
    summary="获取所有抽奖信息（按收录时间和发布时间过滤，支持分页）",
    response_model=CommonResponseModel[AllLotteryResp],
    description="""
获取svm判断过的必抽的预约抽奖数据和官方抽奖数据，按收录时间(created_at)和发布时间(pubTime)过滤普通抽奖
普通抽奖列表支持分页：page_num 从 0 开始，page_size 默认 1000（最大 1000），page_size=0 时返回全部
        """,
    response_model_exclude_none=True,
)
async def api_GetAllLottery(
    created_at_preset: TimePresetEnum | None = Query(
        default=None,
        description="收录时间快捷筛选: 1d/3d/5d/7d/14d/30d，默认不筛选",
    ),
    created_at_start: int | None = Query(
        default=None, ge=0, description="收录起始时间（Unix 秒），preset 优先级高于此字段"
    ),
    created_at_end: int | None = Query(
        default=None, ge=0, description="收录结束时间（Unix 秒）"
    ),
    pub_time_preset: TimePresetEnum | None = Query(
        default=None,
        description="发布时间快捷筛选: 1d/3d/5d/7d/14d/30d，默认不筛选",
    ),
    pub_time_start: int | None = Query(
        default=None, ge=0, description="发布起始时间（Unix 秒），preset 优先级高于此字段"
    ),
    pub_time_end: int | None = Query(
        default=None, ge=0, description="发布结束时间（Unix 秒）"
    ),
    page_num: int = Query(
        default=1, ge=1, description="页码，从 1 开始，最小值为 1"
    ),
    page_size: int = Query(
        default=1000, ge=1, le=1000,
        description="每页数量，最大 1000，默认 1000，最小值为 1",
    ),
):
    result = await get_all_lottery(
        created_at_preset=created_at_preset,
        created_at_start=created_at_start,
        created_at_end=created_at_end,
        pub_time_preset=pub_time_preset,
        pub_time_start=pub_time_start,
        pub_time_end=pub_time_end,
        page_num=page_num,
        page_size=page_size,
    )
    return CommonResponseModel(data=result)


# endregion


@router.post(
    RouterPaths.ADD_DYNAMIC_LOTTERY,
    name=RouterNames.ADD_DYNAMIC_LOTTERY,
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
    RouterPaths.BULK_ADD_DYNAMIC_LOTTERY,
    name=RouterNames.BULK_ADD_DYNAMIC_LOTTERY,
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
    RouterPaths.ADD_TOPIC_LOTTERY,
    name=RouterNames.ADD_TOPIC_LOTTERY,
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
    RouterPaths.BULK_ADD_TOPIC_LOTTERY,
    name=RouterNames.BULK_ADD_TOPIC_LOTTERY,
    summary="批量提交话题抽奖",
    response_model=CommonResponseModel[list[AddTopicLotteryResp]],
    response_model_exclude_none=True,
)
@cache(8 * 3600)
async def api_BulkAddTopicLottery(
    data: BulkAddTopicLotteryReq = Body(...),
):
    resp = await asyncio_gather(
        *[add_topic_lottery(tid) for tid in data.topic_ids]
    )
    return CommonResponseModel(data=resp)


@router.post(
    RouterPaths.ADD_OTHERS_LOT_DYN,
    name=RouterNames.ADD_OTHERS_LOT_DYN,
    summary="提交第三方抽奖动态，自动解析抽奖信息",
    response_model=CommonResponseModel[AddDynamicLotteryResp],
    response_model_exclude_none=True,
)
async def api_AddOthersLotDyn(
    data: AddDynamicLotteryReq = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: GatewayUserInfo = Depends(require_gateway_login),
):
    """提交第三方抽奖动态

    需要登录态：通过网关注入的 ``x-bili-*`` 头校验用户有效登录状态，
    未登录或校验失败则拒绝访问（HTTP 401）。

    校验动态ID并查重后，通过后台任务获取动态详情、解析并入库
    :param data: 包含 dynamic_id_or_url 的请求体
    :param background_tasks: FastAPI 后台任务
    :param user: 网关鉴权解析出的登录用户信息
    """
    resp, dynamic_id, lot_round_id = await add_others_lot_dyn_by_dynamic_id(
        data.dynamic_id_or_url
    )
    if dynamic_id is not None and lot_round_id is not None:
        background_tasks.add_task(process_others_lot_dyn, dynamic_id, lot_round_id)
    return CommonResponseModel(data=resp)


@router.post(
    RouterPaths.BULK_ADD_OTHERS_LOT_DYN,
    name=RouterNames.BULK_ADD_OTHERS_LOT_DYN,
    summary="批量提交第三方抽奖动态，自动解析抽奖信息",
    response_model=CommonResponseModel[list[AddDynamicLotteryResp]],
    response_model_exclude_none=True,
)
async def api_BulkAddOthersLotDyn(
    data: BulkAddOthersLotDynReq = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: GatewayUserInfo = Depends(require_gateway_login),
):
    """批量提交第三方抽奖动态

    需要登录态：通过网关注入的 ``x-bili-*`` 头校验用户有效登录状态，
    未登录或校验失败则拒绝访问（HTTP 401）。

    并行校验所有动态ID并查重，对通过校验的项通过后台任务获取动态详情、解析并入库
    :param data: 包含 dynamic_id_or_urls 的请求体
    :param background_tasks: FastAPI 后台任务
    :param user: 网关鉴权解析出的登录用户信息
    """
    results = await asyncio_gather(
        *[add_others_lot_dyn_by_dynamic_id(url) for url in data.dynamic_id_or_urls]
    )
    for resp, dynamic_id, lot_round_id in results:
        if dynamic_id is not None and lot_round_id is not None:
            background_tasks.add_task(process_others_lot_dyn, dynamic_id, lot_round_id)
    return CommonResponseModel(data=[r[0] for r in results])


@router.post(
    RouterPaths.SEARCH_LOTTERY_BY_KEYWORD,
    name=RouterNames.SEARCH_LOTTERY_BY_KEYWORD,
    summary="根据关键词搜索抽奖信息",
    response_model=CommonResponseModel[ResponsePaginationItems[LotdataResp]],
    response_model_exclude_none=True,
)
async def api_Search(
    pagination: LotterySearchPaginationParams,
):
    # 转换为 offset-limit 形式传递给底层函数
    # max(0, ...) 防止 page_num=0 时 offset 为负数导致 SQL 语法错误
    offset = max(0, (pagination.page_num - 1) * pagination.page_size)
    result: List[Lotdata] = await search_lottery_text(
        pagination.keyword, limit=pagination.page_size, offset=offset
    )
    total = await get_lottery_entity_num()
    return CommonResponseModel(data=ResponsePaginationItems(items=result, total=total))


@router.post(
    RouterPaths.SUBMIT_FEEDBACK,
    name=RouterNames.SUBMIT_FEEDBACK,
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


@router.get(
    RouterPaths.GET_ALL_LOT_SCRAPY_STATUS,
    name=RouterNames.GET_ALL_LOT_SCRAPY_STATUS,
    description="获取所有爬虫状态",
    response_model=CommonResponseModel[AllLotScrapyStatusResp | None],
    response_model_exclude_none=True,
)
def get_all_scrapy_status():
    return CommonResponseModel(
        data=AllLotScrapyStatusResp(
            dyn_scrapy_status=get_scrapy_status("dyn"),
            topic_scrapy_status=get_scrapy_status("topic"),
            reserve_scrapy_status=get_scrapy_status("reserve"),
        )
    )


@router.post(
    RouterPaths.GET_OTHERS_LOT_DYN_LIST,
    name=RouterNames.GET_OTHERS_LOT_DYN_LIST,
    summary="获取第三方抽奖动态列表（分页+排序+时间筛选）",
    response_model=CommonResponseModel[ResponsePaginationItems[OthersLotDynItem]],
    response_model_exclude_none=True,
)
@cache(expire=180)
async def api_GetOthersLotDynList(
    pagination: LotteryPaginationParams,
    sort_by: OthersLotDynSortEnum = OthersLotDynSortEnum.created_at,
    sort_order: OthersLotDynSortOrderEnum = OthersLotDynSortOrderEnum.desc,
    is_lot: bool | None = None,
    created_at_preset: TimePresetEnum | None = None,
    pub_time_preset: TimePresetEnum | None = None,
    pub_time_start: int | None = None,
    pub_time_end: int | None = None,
    created_at_start: int | None = None,
    created_at_end: int | None = None,
    user: GatewayUserInfo = Depends(require_gateway_login),
):
    """获取第三方抽奖动态列表，支持分页、排序和时间筛选

    需要登录态：通过网关注入的 ``x-bili-*`` 头校验用户有效登录状态，
    未登录或校验失败则拒绝访问（HTTP 401）。

    :param pagination: 分页参数
    :param sort_by: 排序字段，pubTime 或 created_at
    :param sort_order: 排序方向，asc 或 desc
    :param is_lot: 是否只返回抽奖动态，None 表示不过滤
    :param created_at_preset: 收录时间快捷筛选（1d/3d/5d/7d/14d/30d），优先级高于 created_at_start
    :param pub_time_preset: 发布时间快捷筛选（1d/3d/5d/7d/14d/30d），优先级高于 pub_time_start
    :param pub_time_start: 发布时间起始（Unix 时间戳，秒）
    :param pub_time_end: 发布时间截止（Unix 时间戳，秒）
    :param created_at_start: 数据库收录时间起始（Unix 时间戳，秒）
    :param created_at_end: 数据库收录时间截止（Unix 时间戳，秒）
    :param user: 网关鉴权解析出的登录用户信息
    """
    # 时间快捷筛选处理
    if created_at_preset is not None:
        days = int(created_at_preset.value.replace("d", ""))
        created_at_start = int(time.time() - days * 86400)
    if pub_time_preset is not None:
        days = int(pub_time_preset.value.replace("d", ""))
        pub_time_start = int(time.time() - days * 86400)

    # 单个 session 内完成主分页查询 + 奖品关联查询，减少数据库往返
    items, total, cached_infos = await SqlHelper.getLotDynListPaginatedWithPrizes(
        page_num=pagination.page_num,
        page_size=pagination.page_size,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        is_lot=is_lot,
        pub_time_start=pub_time_start,
        pub_time_end=pub_time_end,
        created_at_start=created_at_start,
        created_at_end=created_at_end,
    )

    # 构建响应，附加 prize_info 和 extra_info（仅使用已有缓存）
    result_items: list[OthersLotDynItem] = []
    for item in items:
        obj = OthersLotDynItem.model_validate(item)
        cached = cached_infos.get(item.dynId)
        if cached:
            obj.prize_info = OthersLotPrizeInfo(
                prize_names=cached.prize_names or [],
                lottery_time=cached.lottery_time,
            )
            if cached.extra_info:
                obj.extra_info = LotExtraInfoResp(
                    is_grand_prize=bool(cached.extra_info.is_grand_prize),
                    need_comment=bool(cached.extra_info.need_comment),
                    need_repost=bool(cached.extra_info.need_repost),
                )
        result_items.append(obj)

    return CommonResponseModel(
        data=ResponsePaginationItems[OthersLotDynItem](
            items=result_items,
            total=total,
        )
    )


@router.get(
    RouterPaths.GET_LOTTERY_FILTER_PARAMS,
    name=RouterNames.GET_LOTTERY_FILTER_PARAMS,
    summary="获取各抽奖查询接口的筛选参数元数据（供前端动态生成筛选UI）",
    response_model=CommonResponseModel[LotteryFilterParamsResp],
    response_model_exclude_none=True,
)
async def api_GetLotteryFilterParams():
    """返回各抽奖查询接口的筛选参数元数据。
    元数据直接从对应的 Pydantic 筛选模型自省生成，
    与端点处理函数实际接收的参数完全一致（单一来源）。
    """

    endpoints = [
        EndpointFilterMeta(
            endpoint_path="GetReserveLottery",
            display_name="预约抽奖",
            params=pydantic_model_to_filter_params(LotteryAdvancedQueryParams),
        ),
        EndpointFilterMeta(
            endpoint_path="GetOfficialLottery",
            display_name="官方抽奖",
            params=pydantic_model_to_filter_params(LotteryAdvancedQueryParams),
        ),
        EndpointFilterMeta(
            endpoint_path="GetChargeLottery",
            display_name="充电抽奖",
            params=pydantic_model_to_filter_params(LotteryAdvancedQueryParams),
        ),
        EndpointFilterMeta(
            endpoint_path="GetTopicLottery",
            display_name="话题抽奖",
            params=pydantic_model_to_filter_params(LotteryAdvancedQueryParams),
        ),
        EndpointFilterMeta(
            endpoint_path="GetOthersLotDynList",
            display_name="第三方抽奖动态列表",
            params=pydantic_model_to_filter_params(OthersLotDynListFilterMetadata),
        ),
    ]
    return CommonResponseModel(data=LotteryFilterParamsResp(endpoints=endpoints))

