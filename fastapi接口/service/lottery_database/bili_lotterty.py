import json
import re
from datetime import datetime
from typing import List
from urllib.parse import quote
from fastapi接口.dao.lotDataRedisObj import lot_data_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import CommonLotteryResp, \
    OfficialLotteryResp, AllLotteryResp, ChargeLotteryResp, ReserveInfoResp, TopicLotteryResp, LiveLotteryResp, \
    TUpReserveRelationInfoResp, LotdataResp
from fastapi接口.models.lottery_database.redisModel.biliRedisModel import bili_live_lottery_redis
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.get_others_lot_dyn.Sql.sql_helper import SqlHelper as bili_dynamic_sqlhelper
from fastapi接口.service.get_others_lot_dyn.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from fastapi接口.service.get_others_lot_dyn.svmJudgeBigLot.judgeBigLot import big_lot_predict
from fastapi接口.service.opus新版官方抽奖.Model.GenerateCvModel import CvItem
from fastapi接口.service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import GenerateTopicLotCv
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import topic_sqlhelper as bili_topic_sqlhelper
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper as bili_official_sqlhelper
import asyncio

bds = bili_dynamic_sqlhelper  # 获取普通抽奖（主要是非官方的
brs = bili_reserve_sqlhelper
bos = bili_official_sqlhelper
bts = bili_topic_sqlhelper


async def get_common_lottery(round_num, offset: int = 0, page_size: int = 0) -> [CommonLotteryResp]:
    """
    获取非官方抽奖
    :param page_size:
    :param offset:
    :param round_num:
    :return:
    """
    result = await bds.getAllLotDynByLotRoundNum(round_num, offset, page_size)

    return [CommonLotteryResp(
        dynId=str(x.dynId),
        dynamicUrl=x.dynamicUrl,
        authorName=x.authorName,
        up_uid=x.up_uid,
        pubTime=x.pubTime,
        dynContent=x.dynContent,
        commentCount=x.commentCount,
        repostCount=x.repostCount,
        highlightWords=x.highlightWords,
        officialLotType=x.officialLotType,
        officialLotId=x.officialLotId,
        isOfficialAccount=x.isOfficialAccount,
        isManualReply=x.isManualReply,
        isFollowed=x.isFollowed,
        isLot=x.isLot,
        hashTag=x.hashTag,
    ) for x in result if
        x.isLot == 1 and x.officialLotType != '官方抽奖']


async def get_reserve_lottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[ReserveInfoResp], int]:
    all_lots, total_num = await brs.get_all_available_reserve_lotterys_by_time(limit_time, page_num, page_size)
    reserve_infos: List[str] = [x.text for x in all_lots]
    if page_num and page_size:
        ret_list: List[TUpReserveRelationInfo] = all_lots
    else:
        is_lot_list = big_reserve_predict(reserve_infos)
        ret_list: List[TUpReserveRelationInfo] = []
        for i in range(len(all_lots)):
            if is_lot_list[i] == 1:
                ret_list.append(all_lots[i])
    ret_reserve_infos: List[ReserveInfoResp] = []
    for i in ret_list:
        reserve_info = ReserveInfoResp(
            app_sche=f'bilibili://space/{str(i.upmid)}',
            reserve_url=f'https://space.bilibili.com/{str(i.upmid)}/dynamic',
            etime=i.etime,
            lottery_prize_info=i.text,
            jump_url=i.jumpUrl,
            reserve_sid=i.sid,
            available=True,
            raw=TUpReserveRelationInfoResp.model_validate(i)
        )
        ret_reserve_infos.append(reserve_info)
    return ret_reserve_infos, total_num


async def get_official_lottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[OfficialLotteryResp], int]:
    all_lots, total_num = await bos.query_official_lottery_by_timelimit_page_offset(limit_time,
                                                                                    page_num, page_size)
    all_official_lottery_resp_infos = [OfficialLotteryResp(
        dynId=str(x.business_id) if x.business_id and len(
            str(x.business_id)) > 10 else x.bilidyndetail.dynamic_id if x.bilidyndetail else "-1",
        lottery_time=x.lottery_time,
        sender_uid=str(x.sender_uid),
        lottery_id=x.lottery_id,
        lottery_text=' '.join(
            filter(lambda a: a, [x.first_prize_cmt, x.second_prize_cmt, x.third_prize_cmt])).strip(),
        jump_url=f"https://www.bilibili.com/opus/{str(x.business_id)}",
        app_sche=f"bilibili://opus/detail/{str(x.business_id)}",
        raw=LotdataResp.model_validate(x)
    ) for x in all_lots]
    ret_list = []
    official_texts = [x.lottery_text for x in all_official_lottery_resp_infos]
    if page_num and page_size:
        is_lot_list = [1 for i in range(len(official_texts))]
    else:
        is_lot_list = await asyncio.to_thread(big_reserve_predict, official_texts)
    for i in range(len(all_official_lottery_resp_infos)):
        if is_lot_list[i] == 1:
            ret_list.append(all_official_lottery_resp_infos[i])
    return ret_list, total_num


async def get_charge_lottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[ChargeLotteryResp], int]:
    all_lots, total_num = await bos.query_charge_lottery_by_timelimit_page_offset(limit_time,
                                                                                  page_num, page_size)
    all_charge_lottery_resp_infos = [ChargeLotteryResp(
        dynId=str(x.business_id),
        lottery_time=x.lottery_time,
        sender_uid=str(x.sender_uid),
        lottery_id=x.lottery_id,
        lottery_text=' '.join(
            filter(lambda a: a, [x.first_prize_cmt, x.second_prize_cmt, x.third_prize_cmt])).strip(),
        upower_level_str=json.loads(x.exclusive_level).get('upower_level_str', ''),
        jump_url=f"https://www.bilibili.com/opus/{str(x.business_id)}",
        app_sche=f"bilibili://opus/detail/{str(x.business_id)}",
        raw=LotdataResp.model_validate(x)
    ) for x in all_lots]
    ret_list = []
    charge_texts = [x.lottery_text for x in all_charge_lottery_resp_infos]
    if page_num and page_size:
        is_lot_list = [1 for i in range(len(charge_texts))]
    else:
        is_lot_list = await asyncio.to_thread(big_reserve_predict, charge_texts)
    for i in range(len(all_charge_lottery_resp_infos)):
        if is_lot_list[i] == 1:
            ret_list.append(all_charge_lottery_resp_infos[i])
    return ret_list, total_num


async def get_topic_lottery(page_num: int = 0, page_size: int = 0) -> tuple[list[TopicLotteryResp], int]:
    all_lots, total_num = await bts.get_all_available_traffic_info_by_page(page_num, page_size)
    all_charge_lottery_resp_infos: List[CvItem] = [GenerateTopicLotCv.gen_cv_item(
        x
    ) for x in all_lots]
    ret_list = [
        TopicLotteryResp(
            jump_url=x.jumpUrl,
            app_sche=f"bilibili://browser?url={quote(x.jumpUrl, safe=':[],')}",
            title=x.title,
            end_date_str=x.end_date_str,
            lot_type_text=' | '.join([y.value for y in x.lot_type_list] if x.lot_type_list else []).strip(),
            lottery_pool_text=' | '.join(x.lottery_pool if x.lottery_pool else []).strip(),
            lottery_sid=x.lottery_sid,
        )
        for x in all_charge_lottery_resp_infos
    ]
    return ret_list, total_num


async def get_live_lottery(page_num: int = 0, page_size: int = 0) -> tuple[list[LiveLotteryResp], int]:
    result_items, total = await bili_live_lottery_redis.get_live_lottery(page_num, page_size)
    ret_list = []
    for x in result_items:
        live_room_url = x.get('live_room_url', '')
        app_schema = x.get('app_schema')
        if award_name := x.get('award_name'):
            pass
        elif award_name := str(x.get('total_price', '')):
            award_name += '电池（总计）'
        else:
            award_name = '未知奖品'
        _type = x.get('type')
        end_time = x.get('end_time')
        if gift_num := x.get('gift_num'):
            if gift_price := x.get('gift_price'):
                total_price = int(gift_num * gift_price / 1e3)
            else:
                total_price = 0
        else:
            total_price = 0
        danmu = x.get('danmu', '')
        anchor_uid = x.get('anchor_uid', 0)
        room_id = x.get('room_id', '')
        lot_id = x.get('lot_id', 0)
        require_type = x.get('require_type', 0)
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
    return ret_list, total


async def get_all_lottery(round_num) -> AllLotteryResp:
    # 获取所有抽奖动态
    common_lotterys = await bds.getAllLotDynByLotRoundNum(round_num)
    comon_lottery_resp = [CommonLotteryResp(
        dynId=str(x.dynId),
        dynamicUrl=x.dynamicUrl,
        authorName=x.authorName,
        up_uid=x.up_uid,
        pubTime=x.pubTime,
        dynContent=x.dynContent,
        commentCount=x.commentCount,
        repostCount=x.repostCount,
        highlightWords=x.highlightWords,
        officialLotType=x.officialLotType,
        officialLotId=x.officialLotId,
        isOfficialAccount=x.isOfficialAccount,
        isManualReply=x.isManualReply,
        isFollowed=x.isFollowed,
        isLot=x.isLot,
        hashTag=x.hashTag,
    ) for x in common_lotterys if
        x.isLot == 1 and x.officialLotType != '官方抽奖' and (datetime.now() - x.pubTime).days < 15]
    comon_lottery_dyn_content = [x.dynContent for x in comon_lottery_resp]
    comon_lottery_dyn_content_judge = big_lot_predict(comon_lottery_dyn_content)
    must_join_common_lottery = [x for idx, x in enumerate(comon_lottery_resp)
                                if comon_lottery_dyn_content_judge[idx] == 1]

    # 获取所有预约抽奖动态
    reserve_lottery_resp_infos, reserve_lottery_total = await get_reserve_lottery(limit_time=0)
    # 获取所有官方抽奖动态
    official_lottery_resp_infos, official_lottery_total = await get_official_lottery(limit_time=0)

    # 合并
    return AllLotteryResp(
        common_lottery=comon_lottery_resp,
        must_join_common_lottery=must_join_common_lottery,
        reserve_lottery=reserve_lottery_resp_infos,
        official_lottery=official_lottery_resp_infos
    )


async def add_dynamic_lottery_by_dynamic_id(dynamic_id_or_url: str) -> tuple[str, bool]:
    """
    通过动态id添加抽奖信息
    :param dynamic_id:
    :return: True - 添加成功，False - 添加失败
    """
    dynamic_id_re = [x for x in re.findall(r'\d+', dynamic_id_or_url) if len(x) > 10]
    if not dynamic_id_re:
        return '动态格式错误', False
    dynamic_id = dynamic_id_re[0]
    if len(str(dynamic_id)) < 18:
        return '动态格式错误', False
    if await lot_data_redis.is_exist_add_dynamic_lottery(dynamic_id):  # 查询是否正在查询中
        return '近期已查询', True
    await lot_data_redis.set_add_dynamic_lottery(str(dynamic_id))  # 查询过的也加入进去，省得查数据库消耗大

    my_official_charge_lot_data = await bos.query_lot_data_by_business_id(dynamic_id)  # 查询充电和官方抽奖
    if my_official_charge_lot_data:
        return '已经存在', True
    my_dynamic_detail = await bos.get_all_dynamic_detail_by_dynamic_id(
        dynamic_id)  # 查询是否是查过的动态
    if my_dynamic_detail and my_dynamic_detail.dynData or my_dynamic_detail.lot_id:
        return '此条动态已经查询过了', True
    my_reserve_dyn_detail = await brs.get_reserve_by_dynamic_id(dynamic_id)  # 查询预约抽奖
    if my_reserve_dyn_detail:
        return '预约抽奖已经存在', True

    await BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id(
        dynamic_id,
        extra_routing_key='fastapi.controller.AddDynamicLotteryByDynamicId'
    )
    return '成功添加进后台任务队列', True


async def add_topic_lottery(topic_id: str | int):
    if database_data := await bts.get_TTopic_by_topic_id(topic_id):
        if database_data.functional_card_id:
            return '已经存在', True
    await BiliLotDataPublisher.pub_upsert_topic_lot(topic_id=topic_id)
    return '成功添加进后台任务队列', True


if __name__ == "__main__":
    async def _test():
        result = await get_official_lottery(page_num=1, page_size=10)
        print(result)


    asyncio.run(_test())
