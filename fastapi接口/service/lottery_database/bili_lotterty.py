import json
import re
import time
from datetime import datetime
from typing import Tuple, List
from urllib.parse import quote

from fastapi接口.dao.lotDataRedisObj import lot_data_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import CommonLotteryResp, reserveInfo, \
    OfficialLotteryResp, AllLotteryResp, ChargeLotteryResp, ReserveInfoResp, TopicLotteryResp, LiveLotteryResp
from fastapi接口.models.lottery_database.redisModel.biliRedisModel import bili_live_lottery_redis
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from github.my_operator.get_others_lot.Tool.newSqlHelper.SqlHelper import SqlHelper as bili_dynamic_sqlhelper
from github.my_operator.get_others_lot.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from github.my_operator.get_others_lot.svmJudgeBigLot.judgeBigLot import big_lot_predict
from grpc获取动态.src.DynObjectClass import dynAllDetail
from grpc获取动态.src.getDynDetail import dyn_detail_scrapy
from opus新版官方抽奖.Model.GenerateCvModel import CvItem
from opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import TopicLotInfoSqlHelper as bili_topic_sqlhelper, GenerateTopicLotCv

from opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from grpc获取动态.src.SqlHelper import SQLHelper as bili_official_sqlhelper

import asyncio

bds = bili_dynamic_sqlhelper()
brs = bili_reserve_sqlhelper
bos = bili_official_sqlhelper()
bts = bili_topic_sqlhelper()
_lock = asyncio.Lock()

async def GetCommonLottery(round_num, offset: int = 0, page_size: int = 0) -> [CommonLotteryResp]:
    """
    获取非官方抽奖
    :param round_num:
    :return:
    """
    result = await bds.getAllLotDynByLotRoundNum(round_num, offset, page_size)

    return [CommonLotteryResp(**x.__dict__) for x in result if x.isLot == 1 and x.officialLotType != '官方抽奖']


async def GetMustReserveLottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[ReserveInfoResp], int]:
    all_lots, total_num = await brs.get_all_available_reserve_lotterys_by_time(limit_time, page_num, page_size)
    reserve_infos: list[str] = [x.text for x in all_lots]
    if page_num and page_size:
        is_lot_list = [1 for i in range(len(reserve_infos))]
    else:
        is_lot_list = big_reserve_predict(reserve_infos)
    ret_list = []
    for i in range(len(all_lots)):
        if is_lot_list[i] == 1:
            ret_list.append(all_lots[i])
    ret_reserve_infos: list[ReserveInfoResp] = []
    for i in ret_list:
        reserve_info = ReserveInfoResp(
            app_sche=f'bilibili://space/{str(i.upmid)}',
            reserve_url=f'https://space.bilibili.com/{str(i.upmid)}/dynamic',
            etime=i.etime,
            lottery_prize_info=i.text,
            jump_url=i.jumpUrl,
            reserve_sid=i.sid,
            available=True
        )
        ret_reserve_infos.append(reserve_info)
    return ret_reserve_infos, total_num


async def GetMustOfficialLottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[OfficialLotteryResp], int]:
    all_lots, total_num = await asyncio.to_thread(bos.query_official_lottery_by_timelimit_page_offset, limit_time,
                                                  page_num, page_size)
    all_official_lottery_resp_infos = [OfficialLotteryResp(
        dynId=str(x.get('business_id')),
        lottery_time=x.get('lottery_time'),
        sender_uid=str(x.get('sender_uid')),
        lottery_id=x.get('lottery_id'),
        lottery_text=' '.join(
            filter(lambda a: a, [x.get('first_prize_cmt'), x.get('second_prize_cmt'), x.get('third_prize_cmt')])),
        jump_url=f"https://www.bilibili.com/opus/{str(x.get('business_id'))}",
        app_sche=f"bilibili://opus/detail/{str(x.get('business_id'))}"
    ) for x in all_lots]
    ret_list = []
    official_texts = [x.lottery_text for x in all_official_lottery_resp_infos]
    if page_num and page_size:
        is_lot_list = [1 for i in range(len(official_texts))]
    else:
        is_lot_list = big_reserve_predict(official_texts)
    for i in range(len(all_official_lottery_resp_infos)):
        if is_lot_list[i] == 1:
            ret_list.append(all_official_lottery_resp_infos[i])
    return ret_list, total_num


async def GetChargeLottery(limit_time: int, page_num: int = 0, page_size: int = 0) -> tuple[
    list[ChargeLotteryResp], int]:
    all_lots, total_num = await asyncio.to_thread(bos.query_charge_lottery_by_timelimit_page_offset, limit_time,
                                                  page_num, page_size)
    all_charge_lottery_resp_infos = [ChargeLotteryResp(
        dynId=str(x.get('business_id')),
        lottery_time=x.get('lottery_time'),
        sender_uid=str(x.get('sender_uid')),
        lottery_id=x.get('lottery_id'),
        lottery_text=' '.join(
            filter(lambda a: a, [x.get('first_prize_cmt'), x.get('second_prize_cmt'), x.get('third_prize_cmt')])),
        upower_level_str=json.loads(x.get('exclusive_level')).get('upower_level_str', ''),
        jump_url=f"https://www.bilibili.com/opus/{str(x.get('business_id'))}",
        app_sche=f"bilibili://opus/detail/{str(x.get('business_id'))}"
    ) for x in all_lots]
    ret_list = []
    charge_texts = [x.lottery_text for x in all_charge_lottery_resp_infos]
    if page_num and page_size:
        is_lot_list = [1 for i in range(len(charge_texts))]
    else:
        is_lot_list = big_reserve_predict(charge_texts)
    for i in range(len(all_charge_lottery_resp_infos)):
        if is_lot_list[i] == 1:
            ret_list.append(all_charge_lottery_resp_infos[i])
    return ret_list, total_num


async def GetTopicLottery(page_num: int = 0, page_size: int = 0) -> tuple[list[TopicLotteryResp], int]:
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
            lot_type_text=' | '.join([y.value for y in x.lot_type_list] if x.lot_type_list else []),
            lottery_pool_text=' | '.join(x.lottery_pool if x.lottery_pool else []),
            lottery_sid=x.lottery_sid,
        )
        for x in all_charge_lottery_resp_infos
    ]
    return ret_list, total_num


async def GetLiveLottery(page_num: int = 0, page_size: int = 0) -> tuple[list[LiveLotteryResp], int]:
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


async def GetAllLottery(limit_time, round_num) -> AllLotteryResp:
    # 获取所有抽奖动态
    common_lotterys = await bds.getAllLotDynByLotRoundNum(round_num)
    comon_lottery_resp = [CommonLotteryResp(**x.__dict__) for x in common_lotterys if
                          x.isLot == 1 and x.officialLotType != '官方抽奖' and (datetime.now() - x.pubTime).days < 15]
    comon_lottery_dyn_content = [x.dynContent for x in comon_lottery_resp]
    comon_lottery_dyn_content_judge = big_lot_predict(comon_lottery_dyn_content)
    must_join_common_lottery = [x for idx, x in enumerate(comon_lottery_resp)
                                if comon_lottery_dyn_content_judge[idx] == 1]
    word_official_lotterys = [CommonLotteryResp(**x.__dict__) for x in common_lotterys if
                              x.isLot == 1 and x.officialLotType == '官方抽奖' and x.rawJsonStr.get(
                                  'type') != 'DYNAMIC_TYPE_DRAW']

    # 获取所有预约抽奖动态
    reserve_lottery_resp_infos, reserve_lottery_total = await GetMustReserveLottery(limit_time=0)
    # 获取所有官方抽奖动态
    official_lottery_resp_infos, official_lottery_total = await GetMustOfficialLottery(limit_time=0)

    # 合并
    return AllLotteryResp(
        common_lottery=comon_lottery_resp,
        must_join_common_lottery=must_join_common_lottery,
        reserve_lottery=reserve_lottery_resp_infos,
        official_lottery=official_lottery_resp_infos
    )


async def AddDynamicLotteryByDynamicId(dynamic_id_or_url: str) -> tuple[str, bool]:
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
    async with _lock:
        if await lot_data_redis.is_exist_add_dynamic_lottery(dynamic_id):  # 查询是否正在查询中
            return '近期已查询', True
        await lot_data_redis.set_add_dynamic_lottery(str(dynamic_id))  # 查询过的也加入进去，省得查数据库消耗大
    my_official_charge_lot_data = await asyncio.to_thread(bos.query_lot_data_by_business_id, dynamic_id)  # 查询充电和官方抽奖
    if my_official_charge_lot_data:
        return '已经存在', True
    my_dynamic_detail: dynAllDetail.__dict__ = await asyncio.to_thread(bos.get_all_dynamic_detail_by_dynamic_id,dynamic_id)  # 查询是否是查过的动态
    if my_dynamic_detail.get('dynData') or my_dynamic_detail.get('lot_id'):
        return '此条动态已经查询过了', True
    my_reserve_dyn_detail = await brs.get_reserve_by_dynamic_id(dynamic_id)  # 查询预约抽奖
    if my_reserve_dyn_detail:
        return '预约抽奖已经存在', True

    await BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id(
        dynamic_id,
        extra_routing_key='fastapi.controller.AddDynamicLotteryByDynamicId'
    )
    return '成功添加进后台任务队列', True


if __name__ == '__main__':
    async def _test():
        a = await BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id('994477347862216711')
        print(a)


    asyncio.run(_test())
