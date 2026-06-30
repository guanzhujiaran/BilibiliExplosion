import asyncio
import datetime
import time
from typing import Sequence

from log.base_log import get_others_lot_logger as get_others_lot_log
from Service.GetOthersLotDyn.core.robot import GetOthersLotDynRobot
from Service.GetOthersLotDyn.filter.lottery_filter import is_need_lot, solve_return_lot
from Service.GetOthersLotDyn.Sql.models import TLotmaininfo
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper, get_other_lot_redis_manager
from Service.GetOthersLotDyn.svmJudgeBigLot.judgeBigLot import big_lot_predict
from Service.GetOthersLotDyn.svmJudgeBigReserve.judgeReserveLot import big_reserve_predict
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_reply_main
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from Service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper as mysq
from Utils.PushMe import a_pushme
from Utils.代理.mdoel.RequestConf import RequestConf

GET_LOT_DYN_TIME_LIMIT = 20 * 3600 * 24
MAX_USER_LIST_SIZE = 50
MIN_VALID_LOT_THRESHOLD = 5  # 有效抽奖数量低于此阈值的用户将被剔除


class GetOthersLotDyn:
    """
        获取更新的抽奖，如果时间在1天之内，那么直接读取文件获取结果，将结果返回回去
    """

    def __init__(self):
        self.is_getting_dyn_flag_lock = asyncio.Lock()
        self.is_getting_dyn_flag = False
        self.robot: GetOthersLotDynRobot | None = None
        self.get_dyn_ts = 0

    async def get_get_dyn_ts(self):
        get_dyn_ts = await get_other_lot_redis_manager.get_get_dyn_ts()
        if not get_dyn_ts:
            latest_round: TLotmaininfo | None = await SqlHelper.getLatestFinishedRound()
            if latest_round and latest_round.updated_at:
                return int(latest_round.updated_at.timestamp())
        return get_dyn_ts

    # region 主函数 （包括获取普通新抽奖，推送官方抽奖，推送大奖，推送预约抽奖）
    async def get_new_dyn(self) -> list[dict]:
        """
        主函数，获取一般最新的抽奖
        :return:
        """
        while 1:
            async with self.is_getting_dyn_flag_lock:
                if self.is_getting_dyn_flag:
                    await asyncio.sleep(30)
                    continue
                else:
                    self.is_getting_dyn_flag = True
                    break
        self.get_dyn_ts = await self.get_get_dyn_ts()
        get_others_lot_log.info(
            f'上次获取第三方抽奖动态时间：{datetime.datetime.fromtimestamp(self.get_dyn_ts)}')
        if int(time.time()) - self.get_dyn_ts >= 1 * 24 * 3600:  # 每隔1天获取一次
            self.robot = None
            self.robot = GetOthersLotDynRobot()
            await self.robot.main()
            await get_other_lot_redis_manager.set_get_dyn_ts(int(time.time()))
            await self._manage_user_list()
        self.is_getting_dyn_flag = False
        return await self.solve_return_lot()

    async def _get_user_from_latest_lot_dyn_comment(self) -> int | None:
        """从最新抽奖动态的评论中获取一个用户uid"""
        latest_lot = await SqlHelper.getLatestLotDyn()
        if not latest_lot:
            get_others_lot_log.warning('数据库中未找到最新的抽奖动态记录，无法从评论中获取用户')
            return None

        dyn_id = str(latest_lot.dynId)
        rid_type = await SqlHelper.getRidAndTypeByDynId(dyn_id)
        if not rid_type:
            get_others_lot_log.warning(f'动态dynamic_id={dyn_id}在数据库中未找到对应的rid和type，无法获取评论')
            return None

        rid, _type = rid_type
        try:
            reply = await get_reply_main(
                dyn_id, rid, 1, str(_type), 3,
                request_conf=RequestConf(is_use_available_proxy=True)
            )
            if reply and reply.get('code') == 0:
                replies = reply.get('data', {}).get('replies', [])
                if replies:
                    import random
                    chosen = random.choice(replies)
                    mid = chosen.get('mid')
                    get_others_lot_log.info(f'从抽奖动态dynamic_id={dyn_id}的评论中随机获取到用户mid={mid}')
                    return int(mid) if mid else None
        except Exception as e:
            get_others_lot_log.error(f'获取动态dynamic_id={dyn_id}的评论失败：{e}')

        return None

    async def _manage_user_list(self):
        """管理用户列表：固定长度，按阈值剔除低效用户，从最新抽奖动态评论补充新用户"""
        uid_list = await get_other_lot_redis_manager.get_target_uid_list()
        if not uid_list:
            get_others_lot_log.warning('用户列表为空，跳过管理')
            return

        original_len = len(uid_list)
        get_others_lot_log.info(f'用户列表管理前: {original_len}个用户')

        # 统计每个用户的有效抽奖数量
        valid_counts = await SqlHelper.countValidLotByUidList(uid_list)

        # 按阈值剔除：有效抽奖数量低于阈值的用户被移除
        removed = [u for u in uid_list if valid_counts.get(
            int(u), 0) <= MIN_VALID_LOT_THRESHOLD]
        if removed:
            uid_list = [u for u in uid_list if u not in removed]
            get_others_lot_log.info(
                f'按阈值({MIN_VALID_LOT_THRESHOLD})剔除用户: {removed}')

        # 如果列表长度不足，从最新抽奖动态评论中获取新用户
        while len(uid_list) < MAX_USER_LIST_SIZE:
            new_uid = await self._get_user_from_latest_lot_dyn_comment()
            if not new_uid or str(new_uid) in [str(u) for u in uid_list]:
                break  # 没有新用户或重复了，停止补充
            uid_list.append(new_uid)
            get_others_lot_log.info(f'添加新用户{new_uid}到列表')

        await get_other_lot_redis_manager.set_target_uid_list(uid_list)
        get_others_lot_log.info(f'用户列表管理后: {len(uid_list)}个用户')

    async def get_official_lot_dyn(self) -> list[str]:
        """
        返回官方抽奖信息，结尾是tab=1
        :return:
        """
        recent_official_lot_data: Sequence[Lotdata] = await grpc_sql_helper.query_official_lottery_by_timelimit(
            time_limit=30 * 24 * 3600,
            order_by_ts_desc=False
        )
        is_lot_list = await big_reserve_predict(
            [' '.join(
                [x.first_prize_cmt, x.second_prize_cmt if x.second_prize_cmt else '',
                 x.third_prize_cmt if x.third_prize_cmt else '']) for x
                in recent_official_lot_data]
        )
        ret_list = []
        for i in range(len(recent_official_lot_data)):
            if is_lot_list[i] == 1:
                # 忽略两天以内的
                if recent_official_lot_data[i].lottery_time - int(time.time()) < 2 * 3600 * 24:
                    continue
                ret_list.append(
                    f'https://t.bilibili.com/{recent_official_lot_data[i].business_id}?tab=1')
        if ret_list:
            await a_pushme(
                f"必抽的官方抽奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_Big_lot_dyn(self, time_limit: int = GET_LOT_DYN_TIME_LIMIT) -> list[str]:
        """
        获取必抽的大奖
        :return:
        """
        all_lot = await SqlHelper.getAllLotDynByTimeLimit()
        all_lot = [x for x in all_lot if is_need_lot(x, self.get_dyn_ts)]
        dyn_content_list = [x.dynContent for x in all_lot]
        is_lot_list = await big_lot_predict(dyn_content_list)
        ret_list = []
        for i in range(len(all_lot)):
            if is_lot_list[i] == 1:
                ret_list.append(all_lot[i].dynamicUrl)
        if ret_list:
            await a_pushme(
                f"必抽的大奖【{len(ret_list)}】条", '\n'.join(ret_list),
                'text'
            )
        return ret_list

    async def get_unignore_reserve_lot_space(self) -> list[TUpReserveRelationInfo]:
        all_lots = await mysq.get_all_available_reserve_lotterys()
        recent_lots: list[TUpReserveRelationInfo] = [x for x in all_lots if
                                                     x.etime and x.etime - int(time.time()) < 2 * 3600 * 24]
        reserve_infos: list[str] = [x.text for x in recent_lots]
        is_lot_list = await big_reserve_predict(reserve_infos)
        ret_list = []
        ret_info_list = []
        for i in range(len(recent_lots)):
            if is_lot_list[i] == 1:
                ret_info_list.append(
                    ' '.join([f'https://space.bilibili.com/{recent_lots[i].upmid}/dynamic', recent_lots[i].text]))
                ret_list.append(recent_lots[i])
        if ret_info_list:
            await a_pushme(
                f"必抽的预约抽奖【{len(ret_info_list)}】条", '\n'.join(ret_info_list),
                'text'
            )
        return ret_list

    # endregion

    # region 获取抽奖csv里的数据
    async def solve_return_lot(self, time_limit: int = GET_LOT_DYN_TIME_LIMIT) -> list[dict]:
        """
        解析并过滤抽奖，直接从数据库读取，按插入时间过滤，按动态发布时间排序
        委托给 lottery_filter.solve_return_lot 独立函数
        :return:
        """
        return await solve_return_lot(time_limit=time_limit, get_dyn_ts=self.get_dyn_ts)

    # endregion


get_others_lot_dyn = GetOthersLotDyn()

if __name__ == '__main__':
    async def _test_main():
        await get_others_lot_dyn.get_new_dyn()

    async def _test_get_target_uid_list():
        await get_other_lot_redis_manager.get_target_uid_list()

    asyncio.run(_test_main())
