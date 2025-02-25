from enum import Enum

from CONFIG import CONFIG
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankTypeEnum
from utl.redisTool.RedisManager import RedisManagerBase


class LotteryDataStatisticRedis(RedisManagerBase):
    class RedisMap(str, Enum):
        lot_type_rank = 'LotteryDataStatisticRedis:{lot_type}:{rank_type}_prize'  # 转发抽奖类
        lot_sync_ts = 'LotteryDataStatisticRedis:{lot_type}:sync_ts'

        @classmethod
        def get_lot_sync_ts(
                cls,
                lot_type: BiliLotStatisticLotTypeEnum):
            return cls.lot_sync_ts.format(lot_type=lot_type)

        @classmethod
        def get_lot_type_rank_name(
                cls,
                lot_type: BiliLotStatisticLotTypeEnum,
                rank_type: BiliLotStatisticRankTypeEnum):
            return cls.lot_type_rank.format(lot_type=lot_type, rank_type=rank_type)

    def __init__(self):
        super().__init__(db=CONFIG.database.lotDataRedisObj.db,
                         host=CONFIG.database.lotDataRedisObj.host,
                         port=CONFIG.database.lotDataRedisObj.port, )

    async def set_lot_prize_count(
            self,
            lot_type: BiliLotStatisticLotTypeEnum,
            rank_type: BiliLotStatisticRankTypeEnum,
            uid_atari_count_dict: dict):
        """设置抽奖统计信息"""
        return await self._zadd(self.RedisMap.get_lot_type_rank_name(
            lot_type=lot_type,
            rank_type=rank_type),
            uid_atari_count_dict)

    async def get_lot_prize_count(
            self,
            lot_type: BiliLotStatisticLotTypeEnum,
            rank_type: BiliLotStatisticRankTypeEnum,
            offset: int, limit: int = 10
    ):
        return await self._zget_range_with_score(
            self.RedisMap.get_lot_type_rank_name(
                lot_type=lot_type,
                rank_type=rank_type),
            offset=offset,
            num=limit
        )

    async def set_sync_ts(self, lot_type: BiliLotStatisticLotTypeEnum, ts: int):
        return await self._set(self.RedisMap.get_lot_sync_ts(lot_type=lot_type), ts)

    async def get_sync_ts(self, lot_type: BiliLotStatisticLotTypeEnum):
        if res := await self._get(self.RedisMap.get_lot_sync_ts(lot_type=lot_type)):
            return int(res)
        return 0


lottery_data_statistic_redis = LotteryDataStatisticRedis()
