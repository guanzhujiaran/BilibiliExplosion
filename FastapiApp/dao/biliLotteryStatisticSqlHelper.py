from typing import Sequence
import asyncio
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import select, func, Row
from CONFIG import CONFIG
from Models.lottery_database.bili.LotteryDataModels import (
    BiliLotStatisticLotTypeEnum,
    BiliLotStatisticRankDateTypeEnum,
    BiliLotStatisticRankTypeEnum,
    BiliUserInfoSimple,
)
from Service.GrpcModule.GrpcSrc.SQLObject.models import BiliUserInfo, BiliAtariInfo
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict
from dao.base.sqlHelperBase import SqlHelperBase
from log.base_log import official_lot_logger


class LotteryDataStatisticSqlHelper(SqlHelperBase):
    def __init__(self):
        super().__init__(mysql_db_url=CONFIG.database.MYSQL.dyn_detail_URI)
        self.log = official_lot_logger

    async def insert_lot_prize_count(self, bili_atari_info: BiliAtariInfo):
        stmt = insert(BiliUserInfo).values(
            sqlalchemy_model_2_dict(bili_atari_info.bili_user_info)
        )
        stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            face=stmt.inserted.face,
        )
        await self.execute(stmt)

        # 插入 BiliAtariInfo 数据
        stmt = insert(BiliAtariInfo).values(sqlalchemy_model_2_dict(bili_atari_info))
        stmt = stmt.on_duplicate_key_update(
            mid=stmt.inserted.mid, atari_lot_id=stmt.inserted.atari_lot_id
        )
        await self.execute(stmt)

    async def insert_lot_prize_count_bulk(
        self, bili_atari_info_list: list[BiliAtariInfo], chunk_size=10
    ):
        sorted_data = sorted(
            bili_atari_info_list,
            key=lambda x: (x.mid, x.atari_lot_id)
        )

        max_retries = 5
        for retry in range(max_retries):
            try:
                for i in range(0, len(sorted_data), chunk_size):
                    chunk = sorted_data[i : i + chunk_size]
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
                    stmt = stmt.on_duplicate_key_update(mid=stmt.inserted.mid)
                    await self.execute(stmt)
                self.log.info(f"成功插入 {len(bili_atari_info_list)} 条中奖记录")
                return
            except Exception as e:
                error_str = str(e)
                if ("Deadlock" in error_str or "1213" in error_str) and retry < max_retries - 1:
                    import random
                    wait_time = random.uniform(0.5, 2.0) * (retry + 1)
                    self.log.warning(f"检测到死锁，第{retry+1}/{max_retries}次重试，等待{wait_time:.2f}秒... 错误: {error_str[:100]}")
                    await asyncio.sleep(wait_time)
                else:
                    self.log.error(f"插入中奖记录失败，已达最大重试次数{max_retries}次或非死锁错误")
                    raise

    async def get_lot_prize_count(
        self,
        *,
        offset: int,
        limit: int = 10,
        date: BiliLotStatisticRankDateTypeEnum | None = None,
        lot_type: BiliLotStatisticLotTypeEnum | None = None,
        rank_type: BiliLotStatisticRankTypeEnum | None = None,
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
                    - atari_rank: 排名
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

        if atari_rank_enum := rank_type.rank_enum:
            where_clause.append(
                BiliAtariInfo.atari_lot_rank == atari_rank_enum,
            )
        if business_type := lot_type.business_type:
            where_clause.append(BiliAtariInfo.atari_lot_type == business_type)
        if date and date != BiliLotStatisticRankDateTypeEnum.total:
            start, end = date.get_start_end_datetime()
            where_clause.append(BiliAtariInfo.atari_timestamp.between(start, end))
        subq = (
            select(
                BiliAtariInfo.mid.label("user_id"),
                func.count(1).label("prize_count"),
                func.row_number()
                .over(order_by=func.count(1).desc())
                .label("atari_rank"),
            )
            .where(*where_clause)
            .group_by(BiliAtariInfo.mid)  # 按用户ID分组
            .subquery()
        )
        # 主查询：JOIN 用户信息表，获取完整用户资料
        query = (
            select(BiliUserInfo, subq.c.prize_count, subq.c.atari_rank)
            .join(subq, BiliUserInfo.uid == subq.c.user_id)
            .order_by(subq.c.atari_rank)
            .offset(offset)
            .limit(limit)
        )

        # 总数查询：统计满足条件的用户数（去重用户）
        total_stmt = select(func.count(1)).where(*where_clause)

        async with self.async_session() as session:
            total_result = await session.execute(total_stmt)
            result = await session.execute(query)
            total = total_result.scalar() or 0
            # 返回用户对象列表（封装成带 count 和 atari_rank 的 DTO）
            users_with_stats = result.fetchall()

            return users_with_stats, total

    async def get_bili_user_info(self, uid: int | str) -> BiliUserInfoSimple:
        async with self.async_session() as session:
            stmt = select(BiliUserInfo).where(BiliUserInfo.uid == uid)
            result = await session.execute(stmt)
            res = result.scalar_one_or_none()
            if res:
                return BiliUserInfoSimple(
                    uid=str(res.uid), name=res.name, face=res.face
                )
            return BiliUserInfoSimple(uid=str(uid), face="", name="")


lottery_data_statistic_sql_helper = LotteryDataStatisticSqlHelper()

if __name__ == "__main__":

    async def _test_get_lot_prize_count():
        lottery_data_statistic_sql_helper.engine.echo = True
        res = await lottery_data_statistic_sql_helper.get_lot_prize_count(
            offset=0,
            limit=10,
            date=BiliLotStatisticRankDateTypeEnum.year,
            lot_type=BiliLotStatisticLotTypeEnum.official,
            rank_type=BiliLotStatisticRankTypeEnum.first,
        )
        print(res)

    async def _test_get_bili_user_info():
        res = await lottery_data_statistic_sql_helper.get_bili_user_info(uid="4237378")
        print(res)

    asyncio.run(_test_get_lot_prize_count())
