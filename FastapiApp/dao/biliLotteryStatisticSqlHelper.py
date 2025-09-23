from typing import Sequence, Any, Coroutine
import asyncio
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import select, func, distinct, Row
from CONFIG import CONFIG
from Models.lottery_database.bili.LotteryDataModels import AtariLotRankEnum, BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankDateTypeEnum, BiliLotStatisticRankTypeEnum, BiliUserInfoSimple
from Service.GrpcModule.GrpcSrc.SQLObject.models import BiliUserInfo, BiliAtariInfo
from Utils.Common import asyncio_gather
from Utils.SqlalchemyTool import sqlalchemy_model_2_dict
from dao.base.sqlHelperBase import SqlHelperBase
from log.base_log import official_lot_logger


class LotteryDataStatisticSqlHelper(SqlHelperBase):
    def __init__(self):
        super().__init__(MysqlDbUrl=CONFIG.database.MYSQL.dyn_detail)
        self.log = official_lot_logger

    async def insert_lot_prize_count(
            self,
            bili_atari_info: BiliAtariInfo
    ):
        stmt = insert(BiliUserInfo).values(
            sqlalchemy_model_2_dict(bili_atari_info.bili_user_info)
        )
        stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            face=stmt.inserted.face,
        )
        await self.execute(stmt)

        # 插入 BiliAtariInfo 数据
        stmt = insert(BiliAtariInfo).values(
            sqlalchemy_model_2_dict(bili_atari_info)
        )
        stmt = stmt.on_duplicate_key_update(
            mid=stmt.inserted.mid
        )
        await self.execute(stmt)

    async def insert_lot_prize_count_bulk(self, bili_atari_info_list: list[BiliAtariInfo], chunk_size=100):
        for i in range(0, len(bili_atari_info_list), chunk_size):
            chunk = bili_atari_info_list[i:i + chunk_size]
            # 插入 BiliUserInfo 数据
            stmt = insert(BiliUserInfo).values(
                [sqlalchemy_model_2_dict(x.bili_user_info) for x in chunk]
            )
            stmt = stmt.on_duplicate_key_update(
                name=stmt.inserted.name,
                face=stmt.inserted.face,
            )
            await self.execute(stmt)

            # 插入 BiliAtariInfo 数据
            stmt = insert(BiliAtariInfo).values(
                [sqlalchemy_model_2_dict(x) for x in chunk]
            )
            stmt = stmt.on_duplicate_key_update(
                mid=stmt.inserted.mid
            )
            await self.execute(stmt)

    async def get_lot_prize_count(
            self,
            *,
            offset: int,
            limit: int = 10,
            date: BiliLotStatisticRankDateTypeEnum | None = None,
            lot_type: BiliLotStatisticLotTypeEnum | None = None,
            rank_type: AtariLotRankEnum | None = None,
    ) -> tuple[Sequence[Row[tuple[BiliUserInfo, int, int]]], int]:
        """
        获取抽奖奖品统计信息

        参数:
            offset (int): 分页偏移量
            limit (int, optional): 每页数量，默认为10
            date (BiliLotStatisticRankDateTypeEnum | None, optional): 日期范围枚举，默认为None
            lot_type (BiliLotStatisticLotTypeEnum | None, optional): 抽奖类型枚举，默认为None
            rank_type (AtariLotRankEnum | None, optional): 奖品等级枚举，默认为None

        返回值:
            tuple[list[Row], int]: 包含两个元素的元组
                - 第一个元素是用户信息列表，每个元素是一个Row对象，包含以下字段:
                    - BiliUserInfo: 用户信息对象
                    - prize_count: 奖品数量
                    - rank: 排名
                - 第二个元素是满足条件的总用户数

        示例:
            ```python
            users_with_stats, total = await get_lot_prize_count(
            ...     offset=0,
            ...     limit=10,
            ...     date=BiliLotStatisticRankDateTypeEnum.total,
            ...     lot_type=BiliLotStatisticLotTypeEnum.official,
            ...     rank_type=AtariLotRankEnum.first_prize
            ... )
            ```
        """
        where_clause = []
        if lot_type:
            where_clause.append(
                BiliAtariInfo.atari_lot_type == BiliLotStatisticLotTypeEnum.lot_type_2_business_type(
                    lot_type
                )
            )
        if rank_type:
            where_clause.append(
                BiliAtariInfo.atari_lot_rank == rank_type.value,
            )
        if date and date != BiliLotStatisticRankDateTypeEnum.total:
            start, end = date.get_start_end_ts()
            where_clause.append(
                BiliAtariInfo.atari_timestamp.between(
                    start, end
                )
            )
        subq = (
            select(
                BiliAtariInfo.mid.label('user_id'),
                func.count(1).label('prize_count'),
                func.row_number().over(order_by=func.count(1).desc()).label('rank')
            )
            .where(*where_clause)
            .group_by(BiliAtariInfo.mid)  # 按用户ID分组
            .subquery()
        )
        # 主查询：JOIN 用户信息表，获取完整用户资料
        query = (
            select(
                BiliUserInfo,
                subq.c.prize_count,
                subq.c.rank
            )
            .join(subq, BiliUserInfo.uid == subq.c.user_id)
            .order_by(subq.c.rank)
            .offset(offset)
            .limit(limit)
        )

        # 总数查询：统计满足条件的用户数（去重用户）
        total_stmt = (
            select(func.count(1))
            .where(*where_clause)
        )

        async with self.async_session() as session:
            total_result = await session.execute(total_stmt)
            result = await session.execute(query)
            total = total_result.scalar() or 0
            # 返回用户对象列表（封装成带 count 和 rank 的 DTO）
            users_with_stats = result.fetchall()

            return users_with_stats, total

    async def get_bili_user_info(self,uid:int|str)->BiliUserInfoSimple:
        async  with self.async_session() as session:
            stmt = select(BiliUserInfo).where(BiliUserInfo.uid == uid)
            result = await session.execute(stmt)
            res = result.scalar_one_or_none()
            if res:
                return BiliUserInfoSimple(
                    uid=str(res.uid),
                    name=res.name,
                    face=res.face
                )
            return BiliUserInfoSimple(uid=str(uid), face='', name='')


lottery_data_statistic_sql_helper = LotteryDataStatisticSqlHelper()

if __name__ == '__main__':
    async def _test_get_lot_prize_count():
        res = await lottery_data_statistic_sql_helper.get_lot_prize_count(
            offset=0,
            limit=10,
            date=BiliLotStatisticRankDateTypeEnum.total,
            lot_type=BiliLotStatisticLotTypeEnum.official,
            rank_type=AtariLotRankEnum.first_prize
        )
        print(res)

    async def _test_get_bili_user_info():
        res = await lottery_data_statistic_sql_helper.get_bili_user_info(uid='4237378')
        print(res)

    asyncio.run(_test_get_bili_user_info())
