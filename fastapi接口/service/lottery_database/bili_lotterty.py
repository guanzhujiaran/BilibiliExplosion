import time
from datetime import datetime

from fastapi接口.models.lottery_database.bili.LotteryDataModels import CommonLotteryResp, reserveInfo, \
    OfficialLotteryResp, AllLotteryResp
from github.my_operator.get_others_lot.Tool.newSqlHelper.SqlHelper import SqlHelper as bili_dynamic_sqlhelper
from github.my_operator.get_others_lot.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from github.my_operator.get_others_lot.svmJudgeBigLot.judgeBigLot import big_lot_predict

from opus新版官方抽奖.预约抽奖.db.sqlHelper import SqlHelper as bili_reserve_sqlhelper
from grpc获取动态.src.SqlHelper import SQLHelper as bili_official_sqlhelper
import asyncio

bds = bili_dynamic_sqlhelper()
brs = bili_reserve_sqlhelper()
bos = bili_official_sqlhelper()


async def GetCommonLottery(round_num) -> [CommonLotteryResp]:
    """
    获取非官方抽奖
    :param round_num:
    :return:
    """
    result = await bds.getAllLotDynByLotRoundNum(round_num)

    return [CommonLotteryResp(**x.__dict__) for x in result if x.isLot == 1 and x.officialLotType != '官方抽奖']


async def GetMustReserveLottery(limit_time: int):
    all_lots = await brs.get_all_available_reserve_lotterys_by_time(limit_time)
    reserve_infos: list[str] = [x.text for x in all_lots]
    is_lot_list = big_reserve_predict(reserve_infos)
    ret_list = []
    for i in range(len(all_lots)):
        if is_lot_list[i] == 1:
            ret_list.append(all_lots[i])
    ret_reserve_infos: list[reserveInfo] = []
    for i in ret_list:
        reserve_info = reserveInfo(
            reserve_url=f'https://space.bilibili.com/{str(i.upmid)}/dynamic',
            etime=i.etime,
            lottery_prize_info=i.text,
            jump_url=i.jumpUrl,
            reserve_sid=i.sid,
            available=True
        )
        ret_reserve_infos.append(reserve_info)
    return ret_reserve_infos


async def GetMustOfficialLottery(limit_time: int) -> list[OfficialLotteryResp]:
    resp = await asyncio.get_event_loop().run_in_executor(None, bos.query_official_lottery_by_timelimit, limit_time)
    all_official_lottery_resp_infos = [OfficialLotteryResp(
        dynId=str(x.get('business_id')),
        lottery_time=x.get('lottery_time'),
        sender_uid=str(x.get('sender_uid')),
        lottery_id=x.get('lottery_id'),
        lottery_text=' '.join(
            filter(lambda a: a, [x.get('first_prize_cmt'), x.get('second_prize_cmt'), x.get('third_prize_cmt')]))
    ) for x in resp]
    ret_list = []
    official_texts = [x.lottery_text for x in all_official_lottery_resp_infos]
    is_lot_list = big_reserve_predict(official_texts)
    for i in range(len(all_official_lottery_resp_infos)):
        if is_lot_list[i] == 1:
            ret_list.append(all_official_lottery_resp_infos[i])
    return ret_list


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
    reserve_lottery_resp_infos = await GetMustReserveLottery(limit_time)
    # 获取所有官方抽奖动态
    official_lottery_resp_infos = await GetMustOfficialLottery(limit_time)

    # 合并
    return AllLotteryResp(
        common_lottery=comon_lottery_resp,
        must_join_common_lottery=must_join_common_lottery,
        reserve_lottery=reserve_lottery_resp_infos,
        official_lottery=official_lottery_resp_infos
    )


if __name__ == '__main__':
    async def _test():
        a = await GetAllLottery(3600 * 7 * 24, 1)
        print(a)


    asyncio.run(_test())
