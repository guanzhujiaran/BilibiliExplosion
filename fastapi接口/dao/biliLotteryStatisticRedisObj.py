import ast
import json
from enum import Enum
from typing import List
from CONFIG import CONFIG
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankTypeEnum, BiliUserInfoSimple, BiliLotStatisticRankDateTypeEnum
from utl.redisTool.RedisManager import RedisManagerBase
import asyncio


class LotteryDataStatisticRedis(RedisManagerBase):
    class RedisMap(str, Enum):
        lot_type_rank = 'LotteryDataStatisticRedis:{date}:{lot_type}:{rank_type}_prize'  # 转发抽奖类
        lot_sync_ts = 'LotteryDataStatisticRedis:{lot_type}:sync_ts'
        bili_user_uid_face_name = 'LotteryDataStatisticRedis:user_info'

        @classmethod
        def get_lot_sync_ts(
                cls,
                lot_type: BiliLotStatisticLotTypeEnum):
            return cls.lot_sync_ts.format(lot_type=lot_type)

        @classmethod
        def get_lot_type_rank_name(
                cls,
                date: BiliLotStatisticRankDateTypeEnum,
                lot_type: BiliLotStatisticLotTypeEnum,
                rank_type: BiliLotStatisticRankTypeEnum):
            return cls.lot_type_rank.format(date=date, lot_type=lot_type, rank_type=rank_type)

    def __init__(self):
        super().__init__(db=CONFIG.database.lotDataRedisObj.db,
                         host=CONFIG.database.lotDataRedisObj.host,
                         port=CONFIG.database.lotDataRedisObj.port, )

    async def set_lot_prize_count(
            self,
            date: BiliLotStatisticRankDateTypeEnum,
            lot_type: BiliLotStatisticLotTypeEnum,
            rank_type: BiliLotStatisticRankTypeEnum,
            uid_atari_count_dict: dict):
        """
        设置抽奖统计信息，每次设置之前先清除上一轮的
        :param date:
        :param lot_type:
        :param rank_type:
        :param uid_atari_count_dict:
        :return:
        """
        await self._del(
            self.RedisMap.get_lot_type_rank_name(
                date=date,
                lot_type=lot_type,
                rank_type=rank_type)
        )
        return await self._zadd(self.RedisMap.get_lot_type_rank_name(
            date=date,
            lot_type=lot_type,
            rank_type=rank_type),
            uid_atari_count_dict)

    async def get_lot_prize_count(
            self,
            date: BiliLotStatisticRankDateTypeEnum,
            lot_type: BiliLotStatisticLotTypeEnum,
            rank_type: BiliLotStatisticRankTypeEnum,
            offset: int = 0,
            limit: int = 10
    ):
        return await self._zget_range_with_score(
            self.RedisMap.get_lot_type_rank_name(
                date=date,
                lot_type=lot_type,
                rank_type=rank_type),
            offset=offset,
            num=limit
        )

    async def get_lot_prize_rank(self,
                                 date: BiliLotStatisticRankDateTypeEnum,
                                 lot_type: BiliLotStatisticLotTypeEnum,
                                 rank_type: BiliLotStatisticRankTypeEnum,
                                 uid: int | str
                                 ) -> int:
        """
        返回一个从0开始计数的排名，真实排名**需要+1**
        :param date:
        :param lot_type:
        :param rank_type:
        :param uid:
        :return:
        """
        return await self._zget_rank(
            self.RedisMap.get_lot_type_rank_name(
                date=date,
                lot_type=lot_type,
                rank_type=rank_type),
            uid
        )

    async def get_lot_prize_rank_bulk(self,
                                      date: BiliLotStatisticRankDateTypeEnum,
                                      lot_type: BiliLotStatisticLotTypeEnum,
                                      rank_type: BiliLotStatisticRankTypeEnum,
                                      uid_arr: List[int | str]) -> dict[int | str, int]:

        """
        返回一个从0开始计数的排名，真实排名**需要+1**
        :param uid_arr:
        :param date:
        :param lot_type:
        :param rank_type:
        :return:
        """

        async def __do_task(__uid):
            return await self._zget_rank(self.RedisMap.get_lot_type_rank_name(
                date=date,
                lot_type=lot_type,
                rank_type=rank_type), __uid
            )

        ret_dict = {}
        tasks = [__do_task(uid) for uid in uid_arr]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for uid, rank in zip(uid_arr, results):
            if rank is not None:  # 确保结果不是异常
                ret_dict[uid] = rank
            else:
                ret_dict[uid] = -99
        return ret_dict

    async def get_lot_prize_total(self, date: BiliLotStatisticRankDateTypeEnum, lot_type: BiliLotStatisticLotTypeEnum,
                                  rank_type: BiliLotStatisticRankTypeEnum,
                                  ) -> int:
        if res := await self._zcard(
                self.RedisMap.get_lot_type_rank_name(date=date, lot_type=lot_type, rank_type=rank_type)):
            return res
        return -1

    async def set_sync_ts(self, lot_type: BiliLotStatisticLotTypeEnum, ts: int):
        return await self._set(self.RedisMap.get_lot_sync_ts(lot_type=lot_type), ts)

    async def get_sync_ts(self, lot_type: BiliLotStatisticLotTypeEnum):
        if res := await self._get(self.RedisMap.get_lot_sync_ts(lot_type=lot_type)):
            return int(res)
        return 0

    # region b用户信息的region
    async def set_bili_user_info_bulk(self, user_infos: List[BiliUserInfoSimple]):
        await self._hmset_bulk_batch(
            hm_name=self.RedisMap.bili_user_uid_face_name,
            hm_k_v_List=[
                {x.uid: json.dumps({'name': x.name, 'face': x.face}, ensure_ascii=False)}
                for x in user_infos]
        )

    async def get_bili_user_info(self, uid: int | str) -> BiliUserInfoSimple:
        if res := await self._hmget(self.RedisMap.bili_user_uid_face_name, uid):
            return BiliUserInfoSimple(uid=str(uid), **ast.literal_eval(res))
        return BiliUserInfoSimple(uid=str(uid), face='', name='')

    async def get_bili_user_info_bulk(self, uid_arr: [int | str]) -> List[BiliUserInfoSimple]:
        if res := await self._hmget_bulk(self.RedisMap.bili_user_uid_face_name, uid_arr):
            return [
                BiliUserInfoSimple(uid=uid_arr[idx], **ast.literal_eval(res[idx])) if res[idx] else BiliUserInfoSimple(
                    uid=uid_arr[idx], face='', name='')
                for idx in range(len(uid_arr))
            ]
        return [BiliUserInfoSimple(uid=str(uid), face='', name='') for uid in uid_arr]
    # endregion


lottery_data_statistic_redis = LotteryDataStatisticRedis()

if __name__ == '__main__':
    async def _test():
        res = await lottery_data_statistic_redis.get_bili_user_info(
            '4127378'
        )
        print(res)


    asyncio.run(_test())
