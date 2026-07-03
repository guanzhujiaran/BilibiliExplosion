import json
import re
import time
from typing import List
from urllib.parse import quote
from Models.lottery_database.bili.LotteryDataBaseQueryModels import (
    BiliLotDataQueryModel,
)
from Models.lottery_database.bili.comm import BiliLotDataStatusEnum, LotteryBusinessType
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_lot_notice
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from dao.lotDataRedisObj import lot_data_redis
from Models.lottery_database.bili.LotteryDataModels import (
    AddDynamicLotteryResp,
    CommonLotteryResp,
    OfficialLotteryResp,
    AllLotteryResp,
    ChargeLotteryResp,
    ReserveInfoResp,
    TopicLotteryResp,
    LiveLotteryResp,
    LotdataResp,
    AddTopicLotteryResp,
    TimePresetEnum,
    LotExtraInfoResp,
)
from Models.lottery_database.redisModel.biliRedisModel import bili_live_lottery_redis
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper as bili_dynamic_sqlhelper
from Service.opus新版官方抽奖.Model.GenerateCvModel import CvTopicItem
from Service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import GenerateTopicLotCv
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import (
    topic_sqlhelper as bili_topic_sqlhelper,
)
from Service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from Service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from Service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import (
    grpc_sql_helper as bili_official_sqlhelper,
)
import asyncio
from fastapi import BackgroundTasks
from Service.GetOthersLotDyn.core.bili_dynamic_item import BiliDynamicItem

bds = bili_dynamic_sqlhelper  # 获取普通抽奖（主要是非官方的
brs = bili_reserve_sqlhelper
bos = bili_official_sqlhelper
bts = bili_topic_sqlhelper


async def get_common_lottery(
    round_num, offset: int = 0, page_size: int = 0
) -> list[CommonLotteryResp]:
    """
    获取非官方抽奖
    :param page_size:
    :param offset:
    :param round_num:
    :return:
    """
    result = await bds.getAllLotDynByLotRoundNum(round_num, offset, page_size)

    return [
        CommonLotteryResp(
            dynId=str(x.dynId),
            dynamicUrl=x.dynamicUrl,
            authorName=x.authorName,
            up_uid=x.up_uid,
            pubTime=x.pubTime,
            dynContent=x.dynContent,
            commentCount=x.commentCount,
            repostCount=x.repostCount,
            likeCount=x.likeCount,
            officialLotType=x.officialLotType,
            officialLotId=x.officialLotId,
            isOfficialAccount=x.isOfficialAccount,
            isManualReply=x.isManualReply,
            isLot=x.isLot,
            hashTag=x.hashTag,
        )
        for x in result
        if x.isLot == 1 and x.officialLotType != "官方抽奖"
    ]


async def update_lot_data(business_id: int, business_type: LotteryBusinessType):
    lot_notice = await get_lot_notice(
        business_type=business_type.value, business_id=business_id
    )
    await bos.upsert_lot_detail(lot_notice.get("data"))
    bos.log.info(f"update lot_data:{lot_notice}")


async def get_reserve_lottery(
    q: BiliLotDataQueryModel, background_task: BackgroundTasks | None = None
) -> tuple[list[ReserveInfoResp], int]:
    all_lots, total_num = await bos.query_lottery(q)
    reserve_info_list: list[tuple[TUpReserveRelationInfo, dict]] = (
        await reserve_robot.bulk_handle_fetch_reserve_info(
            [x.business_id for x in all_lots], False,background_task
        )
    )
    reserve_info_text_list: List[str] = [
        f"预约有奖：{x.first_prize_cmt}*{x.first_prize}份{f'、{str(x.second_prize_cmt)}' if x.second_prize_cmt else ''}{f'*{str(x.second_prize)}份' if x.second_prize else ''}{f'、{str(x.third_prize_cmt)}' if x.third_prize_cmt else ''}{f'*{str(x.third_prize)}' + '份' if x.third_prize else ''}"
        for x in all_lots
    ]
    ret_reserve_infos: List[ReserveInfoResp] = []
    for x,_ in reserve_info_list:
        if x.text is None:
            if background_task:
                background_task.add_task(
                    update_lot_data,
                    business_id=x.ids,
                    business_type=q.business_type,
                )
            else:
                await update_lot_data(
                    business_id=x.ids,
                    business_type=q.business_type,
                )
    for i, t in zip(all_lots,reserve_info_text_list):
        dynamic_id = None
        total = None
        for x,_ in reserve_info_list:
            if x.ids == i.business_id:
                dynamic_id = int(x.dynamicId) if x.dynamicId else None
                total = x.total or None
        reserve_info = ReserveInfoResp(
            app_sche=f"bilibili://space/{str(i.sender_uid)}",
            reserve_url=f"https://space.bilibili.com/{str(i.sender_uid)}/dynamic",
            etime=i.lottery_time,
            dynamic_id=dynamic_id,
            total=total,
            lottery_prize_info=t,
            jump_url=i.lottery_detail_url,
            reserve_sid=i.business_id,
            available=True,
            raw=None
        )
        ret_reserve_infos.append(reserve_info)
    return ret_reserve_infos, total_num


async def get_official_lottery(
    q: BiliLotDataQueryModel,
) -> tuple[list[OfficialLotteryResp], int]:
    # 先查主表 lotdata，再通过独立批量查询获取 extra_info，与主表解耦
    all_lots, total_num = await bos.query_official_lottery_by_timelimit_page_offset(q)
    extra_map = await bos.get_extra_info_map(
        [x.lottery_id for x in all_lots]
    )
    ret_list = [
        OfficialLotteryResp(
            dynId=(
                str(x.business_id)
                if x.business_id and len(str(x.business_id)) > 10
                else x.bilidyndetail.dynamic_id if x.bilidyndetail else "-1"
            ),
            lottery_time=x.lottery_time,
            sender_uid=str(x.sender_uid),
            lottery_id=x.lottery_id,
            lottery_text=" ".join(
                filter(
                    lambda a: a,
                    [x.first_prize_cmt, x.second_prize_cmt, x.third_prize_cmt],
                )
            ).strip(),
            jump_url=f"https://www.bilibili.com/opus/{str(x.business_id)}",
            app_sche=f"bilibili://opus/detail/{str(x.business_id)}",
            extra_info=LotExtraInfoResp(
                is_grand_prize=bool(extra_map[x.lottery_id].is_grand_prize),
                need_comment=False,
                need_repost=True,
            ) if x.lottery_id in extra_map else LotExtraInfoResp(
                is_grand_prize=False,
                need_comment=False,
                need_repost=True,
            ),
            raw=LotdataResp.model_validate(x),
        )
        for x in all_lots
    ]
    return ret_list, total_num


async def get_charge_lottery(
    q: BiliLotDataQueryModel,
) -> tuple[list[ChargeLotteryResp], int]:
    # 先查主表 lotdata，再通过独立批量查询获取 extra_info，与主表解耦
    all_lots, total_num = await bos.query_charge_lottery_by_timelimit_page_offset(q)
    extra_map = await bos.get_extra_info_map(
        [x.lottery_id for x in all_lots]
    )
    ret_list = []
    for x in all_lots:
        try:
            # 安全解析 exclusive_level JSON 字段
            upower_level_str = ""
            if x.exclusive_level:
                try:
                    exclusive_level_dict = json.loads(x.exclusive_level)
                    upower_level_str = exclusive_level_dict.get("upower_level_str", "")
                except (json.JSONDecodeError, TypeError):
                    # JSON解析失败，使用默认值
                    pass

            charge_lottery_resp = ChargeLotteryResp(
                dynId=str(x.business_id),
                lottery_time=x.lottery_time,
                sender_uid=str(x.sender_uid),
                lottery_id=x.lottery_id,
                lottery_text=" ".join(
                    filter(
                        lambda a: a,
                        [x.first_prize_cmt, x.second_prize_cmt, x.third_prize_cmt],
                    )
                ).strip(),
                upower_level_str=upower_level_str,
                extra_info=LotExtraInfoResp(
                    is_grand_prize=bool(extra_map[x.lottery_id].is_grand_prize),
                    need_comment=bool(extra_map[x.lottery_id].need_comment),
                    need_repost=bool(extra_map[x.lottery_id].need_repost),
                ) if x.lottery_id in extra_map else None,
                jump_url=f"https://www.bilibili.com/opus/{str(x.business_id)}",
                app_sche=f"bilibili://opus/detail/{str(x.business_id)}",
                raw=LotdataResp.model_validate(x),
            )
            ret_list.append(charge_lottery_resp)
        except Exception as e:
            # 跳过解析失败的记录，避免影响整个列表
            continue
    return ret_list, total_num


async def get_topic_lottery(
    page_num: int = 0, page_size: int = 0, keyword: str | None = None,
) -> tuple[list[TopicLotteryResp], int]:
    all_lots, total_num = await bts.get_all_available_traffic_info_by_page(
        page_num, page_size, keyword=keyword,
    )
    all_charge_lottery_resp_infos: List[CvTopicItem] = [
        GenerateTopicLotCv.gen_cv_item(x) for x in all_lots
    ]
    ret_list = [
        TopicLotteryResp(
            jump_url=x.jumpUrl,
            app_sche=f"bilibili://browser?url={quote(x.jumpUrl, safe=':[],')}",
            title=x.title,
            end_date_str=x.end_date_str,
            lot_type_text=" | ".join(
                [y.value for y in x.lot_type_list] if x.lot_type_list else []
            ).strip(),
            lottery_pool_text=" | ".join(
                x.lottery_pool if x.lottery_pool else []
            ).strip(),
            lottery_sid=x.lottery_sid,
        )
        for x in all_charge_lottery_resp_infos
    ]
    return ret_list, total_num


async def get_live_lottery(
    page_num: int = 0, page_size: int = 0
) -> tuple[list[LiveLotteryResp], int]:
    result_items, total = await bili_live_lottery_redis.get_live_lottery(
        page_num, page_size
    )
    ret_list = []
    for x in result_items:
        try:
            # 提取基本信息，避免重复访问字典
            live_room_url = x.get("live_room_url", "")
            app_schema = x.get("app_schema", "")

            # 处理奖项名称
            award_name = x.get("award_name")
            if not award_name:
                total_price_str = str(x.get("total_price", ""))
                if total_price_str and total_price_str != "0":
                    award_name = f"{total_price_str}电池（总计）"
                else:
                    award_name = "未知奖品"

            # 处理类型和结束时间
            _type = x.get("type", "")
            end_time = x.get("end_time", 0)

            # 计算总价
            gift_num = x.get("gift_num", 0)
            gift_price = x.get("gift_price", 0)
            if gift_num and gift_price:
                total_price = int(gift_num * gift_price / 1e3)
            else:
                total_price = 0

            # 提取其他字段
            danmu = x.get("danmu", "")
            anchor_uid = x.get("anchor_uid", 0)
            room_id = x.get("room_id", "")
            lot_id = x.get("lot_id", 0)
            require_type = x.get("require_type", 0)

            ret_list.append(
                LiveLotteryResp(
                    live_room_url=live_room_url,
                    app_schema=app_schema,
                    award_name=award_name,
                    type=_type,
                    end_time=end_time,
                    total_price=total_price,
                    danmu=danmu,
                    anchor_uid=anchor_uid,
                    room_id=room_id,
                    lot_id=lot_id,
                    require_type=require_type,
                )
            )
        except Exception as e:
            # 跳过解析失败的记录，避免影响整个列表
            continue
    return ret_list, total


async def get_all_lottery(
    created_at_preset: TimePresetEnum | None = None,
    created_at_start: int | None = None,
    created_at_end: int | None = None,
    pub_time_preset: TimePresetEnum | None = None,
    pub_time_start: int | None = None,
    pub_time_end: int | None = None,
    page_num: int = 1,
    page_size: int = 1000,
) -> AllLotteryResp:
    # 收录时间快捷筛选：优先级高于 created_at_start；不给值时默认 30 天
    effective_created_at_start = created_at_start
    if created_at_preset is not None:
        days = int(created_at_preset.value.replace("d", ""))
        effective_created_at_start = int(time.time() - days * 86400)
    elif effective_created_at_start is None:
        effective_created_at_start = int(time.time() - 30 * 86400)

    # 发布时间快捷筛选：优先级高于 pub_time_start；不给值时默认 30 天
    effective_pub_time_start = pub_time_start
    if pub_time_preset is not None:
        days = int(pub_time_preset.value.replace("d", ""))
        effective_pub_time_start = int(time.time() - days * 86400)
    elif effective_pub_time_start is None:
        effective_pub_time_start = int(time.time() - 30 * 86400)

    # 三个查询并行执行：普通抽奖 / 预约抽奖 / 官方抽奖
    common_lotterys, (reserve_lottery_resp_infos, _), (official_lottery_resp_infos, _) = await asyncio.gather(
        bds.getAllLotDynByInsertTimeRange(
            created_at_start=effective_created_at_start,
            created_at_end=created_at_end,
            pub_time_start=effective_pub_time_start,
            pub_time_end=pub_time_end,
        ),
        get_reserve_lottery(
            q=BiliLotDataQueryModel(
                business_type=LotteryBusinessType.Reserve,
                status=BiliLotDataStatusEnum.UNFINISHED,
                page_num=0,
                page_size=0,
                start_ts=None,
                end_ts=None,
                sender_uid=None,
                min_participants=None,
                max_participants=None,
            )
        ),
        get_official_lottery(
            q=BiliLotDataQueryModel(
                business_type=LotteryBusinessType.Official,
                status=BiliLotDataStatusEnum.UNFINISHED,
                page_num=0,
                page_size=0,
            )
        ),
    )

    # 构造普通抽奖响应列表（先做业务过滤：isLot==1 且非官方抽奖）
    comon_lottery_resp = [
        CommonLotteryResp(
            dynId=str(x.dynId),
            dynamicUrl=x.dynamicUrl,
            authorName=x.authorName,
            up_uid=x.up_uid,
            pubTime=x.pubTime,
            dynContent=x.dynContent,
            commentCount=x.commentCount,
            repostCount=x.repostCount,
            likeCount=x.likeCount,
            officialLotType=x.officialLotType,
            officialLotId=x.officialLotId,
            isOfficialAccount=x.isOfficialAccount,
            isManualReply=x.isManualReply,
            isLot=x.isLot,
            hashTag=x.hashTag,
        )
        for x in common_lotterys
        if x.isLot == 1 and x.officialLotType != "官方抽奖"
    ]

    # 分页：page_num 从 1 开始，offset = (page_num - 1) * page_size
    common_lottery_total = len(comon_lottery_resp)
    if page_size > 0:
        start = (page_num - 1) * page_size
        end = start + page_size
        paged_common_lottery = comon_lottery_resp[start:end]
    else:
        # 未给分页参数时默认只返回前 1000 条，避免全量返回
        paged_common_lottery = comon_lottery_resp[:1000]

    # 直接从数据库大奖 flag 子表读取（仅查询当前页，减少查询量）
    dyn_ids = [int(x.dynId) for x in paged_common_lottery]
    grand_prize_flags = await bds.get_extra_info_by_ref_ids(dyn_ids, "common")
    must_join_common_lottery = []
    for x in paged_common_lottery:
        x.isBigLot = grand_prize_flags.get(int(x.dynId), 0)
        if x.isBigLot == 1:
            must_join_common_lottery.append(x)

    # 合并
    return AllLotteryResp(
        common_lottery=paged_common_lottery,
        common_lottery_total=common_lottery_total,
        must_join_common_lottery=must_join_common_lottery,
        reserve_lottery=reserve_lottery_resp_infos,
        official_lottery=official_lottery_resp_infos,
    )


async def add_dynamic_lottery_by_dynamic_id(
    dynamic_id_or_url: str,
) -> AddDynamicLotteryResp:
    """
    通过动态id添加抽奖信息
    :param dynamic_id:
    :return: True - 添加成功，False - 添加失败
    """
    dynamic_id_re = [x for x in re.findall(r"\d+", dynamic_id_or_url) if len(x) > 10]
    if not dynamic_id_re:
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=False,
            msg="动态格式错误",
        )
    dynamic_id = dynamic_id_re[0]
    if len(str(dynamic_id)) < 18:
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=False,
            msg="动态格式错误，动态dynamic_id长度不正确",
        )
    if await lot_data_redis.is_exist_add_dynamic_lottery(
        dynamic_id
    ):  # 查询是否正在查询中
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=True,
            msg="近期已查询",
        )
    await lot_data_redis.set_add_dynamic_lottery(
        str(dynamic_id)
    )  # 查询过的也加入进去，省得查数据库消耗大

    my_official_charge_lot_data = await bos.query_lot_data_by_business_id(
        dynamic_id
    )  # 查询充电和官方抽奖
    if my_official_charge_lot_data:
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=True,
            msg="充电/官方抽奖已经存在",
        )
    my_dynamic_detail = await bos.get_all_dynamic_detail_by_dynamic_id(
        dynamic_id
    )  # 查询是否是查过的动态
    if my_dynamic_detail and (my_dynamic_detail.dynData or my_dynamic_detail.lot_id):
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=True,
            msg="此条动态已经查询过了",
        )
    my_reserve_dyn_detail = await brs.get_reserve_by_dynamic_id(
        dynamic_id
    )  # 查询预约抽奖
    if my_reserve_dyn_detail:
        return AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=False,
            is_succ=True,
            msg="预约抽奖已经存在",
        )

    await BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id(
        dynamic_id, extra_routing_key="fastapi.controller.AddDynamicLotteryByDynamicId"
    )
    return AddDynamicLotteryResp(
        dynamic_id_or_url=dynamic_id_or_url,
        is_new=True,
        is_succ=True,
        msg="成功添加进后台任务队列查询",
    )


async def add_others_lot_dyn_by_dynamic_id(
    dynamic_id_or_url: str,
) -> tuple[AddDynamicLotteryResp, str | None, int | None]:
    """
    通过动态id添加第三方抽奖动态信息
    与官抽提交类似，校验动态ID后查重，查重通过则返回 dynamic_id 和 lotRound_id 供后台任务处理
    :param dynamic_id_or_url: 动态ID或URL
    :return: (响应, dynamic_id, lotRound_id)，后两者为 None 表示无需后台处理
    """
    dynamic_id_re = [x for x in re.findall(r"\d+", dynamic_id_or_url) if len(x) > 10]
    if not dynamic_id_re:
        return (
            AddDynamicLotteryResp(
                dynamic_id_or_url=dynamic_id_or_url,
                is_new=False,
                is_succ=False,
                msg="动态格式错误",
            ),
            None,
            None,
        )
    dynamic_id = dynamic_id_re[0]
    if len(str(dynamic_id)) < 18:
        return (
            AddDynamicLotteryResp(
                dynamic_id_or_url=dynamic_id_or_url,
                is_new=False,
                is_succ=False,
                msg="动态格式错误，动态dynamic_id长度不正确",
            ),
            None,
            None,
        )

    # 查询是否已存在
    existing = await bds.isExistDynInfoByDynId(dynamic_id)
    if existing:
        return (
            AddDynamicLotteryResp(
                dynamic_id_or_url=dynamic_id_or_url,
                is_new=False,
                is_succ=True,
                msg="该动态已经存在",
            ),
            None,
            None,
        )

    # 获取最新轮次，没有则创建
    latest_round = await bds.getLatestRound()
    if not latest_round:
        from Service.GetOthersLotDyn.Sql.models import TLotmaininfo

        latest_round = TLotmaininfo(
            lotRound_id=1,
            allNum=0,
            lotNum=0,
            uselessNum=0,
            isRoundFinished=False,
        )
        await bds.addLotMainInfo(latest_round)

    return (
        AddDynamicLotteryResp(
            dynamic_id_or_url=dynamic_id_or_url,
            is_new=True,
            is_succ=True,
            msg="成功添加进后台任务队列查询",
        ),
        dynamic_id,
        latest_round.lotRound_id,
    )


async def process_others_lot_dyn(dynamic_id: str, lot_round_id: int) -> None:
    """
    后台处理第三方抽奖动态：获取动态详情、解析并入库
    :param dynamic_id: 动态ID
    :param lot_round_id: 抽奖轮次ID
    """

    item = BiliDynamicItem(dynamic_id=dynamic_id)
    await item.judge_lottery(lotRound_id=lot_round_id)


async def add_topic_lottery(topic_id: str | int) -> AddTopicLotteryResp:
    """
    通过话题ID添加抽奖信息
    :param topic_id: 话题ID
    :return: AddTopicLotteryResp 响应对象
    """
    try:
        # 验证 topic_id 格式
        if not topic_id or not str(topic_id).isdigit():
            return AddTopicLotteryResp(
                topic_id=topic_id,
                is_new=False,
                is_succ=False,
                msg="话题ID格式错误",
            )

        topic_id = int(topic_id)

        # 检查是否已存在
        if database_data := await bts.get_TTopic_by_topic_id(topic_id):
            if database_data.functional_card_id:
                return AddTopicLotteryResp(
                    topic_id=topic_id,
                    is_new=False,
                    is_succ=True,
                    msg="已经存在",
                )

        # 发布到后台任务队列
        await BiliLotDataPublisher.pub_upsert_topic_lot(topic_id=topic_id)
        return AddTopicLotteryResp(
            topic_id=topic_id,
            is_new=True,
            is_succ=True,
            msg="成功添加进后台任务队列",
        )
    except Exception as e:
        # 记录异常并返回错误响应
        return AddTopicLotteryResp(
            topic_id=topic_id,
            is_new=False,
            is_succ=False,
            msg=f"处理失败: {str(e)}",
        )
