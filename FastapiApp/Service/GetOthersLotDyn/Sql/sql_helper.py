import ast
import asyncio
import json
import time
from datetime import datetime
from enum import StrEnum
from typing import Union, List, Sequence, Optional

from pydantic import BaseModel

from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info
from sqlalchemy import select, and_, func, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import selectinload
from CONFIG import CONFIG
from Utils.通用.dynamic_id_caculate import ts_2_fake_dynamic_id
from Service.GetOthersLotDyn.Sql.models import (
    TLotmaininfo,
    TLotuserinfo,
    TLotdyninfo,
    TLotuserspaceresp,
    TRiddynid,
    TOthersLotInfo,
    TLotExtraInfo,
)
from Utils.通用.Common import log_sql_retry_wrapper
from Utils.redisTool.RedisManager import RedisManagerBase
from dao.base.sqlHelperBase import SqlHelperBase


class TargetUserItem(BaseModel):
    """Redis 中存储的每个目标用户信息"""
    uid: int
    uname: str = ""                                 # 用户名
    last_dyn_pub_ts: int = 0                        # 最后一条抽奖动态发布时间(Unix)
    last_dyn_pub_datetime: datetime | None = None    # 最后一条抽奖动态发布时间(人类可读)
    last_round_lot_count: int = 0                   # 最后一轮有效抽奖次数
    last_round_total_count: int = 0                 # 最后一轮总动态数


class GetOtherLotRedisManager(RedisManagerBase):
    class RedisMap(StrEnum):
        target_uid_list = "get_other_lot_redis_manager:target_uid_list"
        get_dyn_ts = "get_other_lot_redis_manager:get_dyn_ts"

    def __init__(self):
        super().__init__(
            host=CONFIG.database.getOtherLotRedis.host,
            port=CONFIG.database.getOtherLotRedis.port,
            db=CONFIG.database.getOtherLotRedis.db,
        )

    async def set_target_uid_list(
        self, uid_list: list[TargetUserItem]
    ):
        """保存用户列表，序列化为 JSON"""
        await self._set(
            self.RedisMap.target_uid_list.value,
            json.dumps([item.model_dump(mode='json') for item in uid_list]),
        )

    async def get_target_uid_list(self) -> list[TargetUserItem]:
        """获取用户列表，自动兼容旧版 List[int|str] 和旧版 dict 格式并迁移"""
        val = await self._get(self.RedisMap.target_uid_list.value)
        if not val:
            return []

        data = json.loads(val)
        if not data:
            return []

        first = data[0]
        if isinstance(first, dict):
            # 旧版 dict 或新版 TargetUserItem 的 dict 格式，统一用 model_validate
            return [TargetUserItem.model_validate(item) for item in data]

        # 最旧版 List[int|str] 格式，自动迁移
        return [
            TargetUserItem(uid=int(uid))
            for uid in data
        ]

    async def get_target_uid_set(self) -> set[int]:
        """便捷方法：直接获取 uid 集合"""
        return {item.uid for item in await self.get_target_uid_list()}

    async def get_get_dyn_ts(self) -> int:
        get_dyn_ts = await self._get(self.RedisMap.get_dyn_ts.value)
        return int(get_dyn_ts if get_dyn_ts else 0)

    async def set_get_dyn_ts(self, get_dyn_ts: int):
        await self._set(self.RedisMap.get_dyn_ts.value, get_dyn_ts)


class __SqlHelper(SqlHelperBase):
    """
    爬虫用获取其他抽奖数据库操作类
    使用独立的爬虫连接池，限制并发
    """

    def __init__(self):
        mysql_db_url = CONFIG.database.MYSQL.get_other_lot_URI
        super().__init__(mysql_db_url=mysql_db_url)
        self.add_dyn_info_lock = asyncio.Lock()

    @log_sql_retry_wrapper()
    async def getDynIdByRidType(self, rid: int, dynamic_type: int) -> Union[int, None]:
        async with self.async_session() as session:
            sql = (
                select(TRiddynid.dynamic_id)
                .filter(
                    and_(TRiddynid.rid == rid,
                         TRiddynid.dynamic_type == dynamic_type)
                )
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret if ret else 0

    @log_sql_retry_wrapper()
    async def setDynIdByRidType(self, dynamic_id: int, rid: int, dynamic_type: int):
        async with self.async_session() as session:
            await session.merge(
                TRiddynid(
                    dynamic_id=int(dynamic_id),
                    rid=int(rid),
                    dynamic_type=int(dynamic_type),
                )
            )
            await session.commit()

    # region 获取抽奖轮次信息相关
    @log_sql_retry_wrapper()
    async def getLatestFinishedRound(self) -> Union[TLotmaininfo, None]:
        async with self.async_session() as session:
            sql = (
                select(TLotmaininfo)
                .where(TLotmaininfo.isRoundFinished == 1)
                .order_by(TLotmaininfo.lotRound_id.desc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret: TLotmaininfo = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def getLatestRound(self) -> Union[TLotmaininfo, None]:
        async with self.async_session() as session:
            sql = (
                select(TLotmaininfo).order_by(
                    TLotmaininfo.lotRound_id.desc()).limit(1)
            )
            res = await session.execute(sql)
            ret: TLotmaininfo = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def addLotMainInfo(self, LotMainInfo: TLotmaininfo):
        async with self.async_session() as session:
            async with session.begin():
                sql = (
                    select(TLotmaininfo)
                    .filter(TLotmaininfo.lotRound_id == LotMainInfo.lotRound_id)
                    .limit(1)
                )
                res = await session.execute(sql)
                ret: TLotmaininfo = res.scalars().first()
                if ret:
                    ret.lotNum = LotMainInfo.lotNum
                    ret.allNum = LotMainInfo.allNum
                    ret.uselessNum = LotMainInfo.uselessNum
                    ret.isRoundFinished = LotMainInfo.isRoundFinished
                    await session.flush()
                else:
                    session.add(LotMainInfo)
                    await session.flush()

    # endregion

    # region 抽奖动态相关
    @log_sql_retry_wrapper()
    async def getAllDynInfo(self) -> Sequence[TLotdyninfo]:
        async with self.async_session() as session:
            sql = select(TLotdyninfo).order_by(TLotdyninfo.dynId.desc())
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getAllDynByLotRound(self, LotRound_id: int) -> Sequence[TLotdyninfo]:
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(TLotdyninfo.dynLotRound_id == LotRound_id)
                .order_by(TLotdyninfo.dynId.desc())
            )
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getAllLotDynByTimeLimit(self, time_limit: int = 20 * 3600 * 24):
        target_dyn_id = ts_2_fake_dynamic_id(int(time.time()) - time_limit)
        stmt = select(TLotdyninfo).filter(
            and_(TLotdyninfo.isLot == True, TLotdyninfo.dynId >= target_dyn_id)
        )
        async with self.async_session() as session:
            res = await session.execute(stmt)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getAllLotDynByInsertTime(
        self, time_limit: int = 20 * 3600 * 24
    ) -> Sequence[TLotdyninfo]:
        """按插入时间(created_at)过滤抽奖动态，替代按dynId过滤"""
        cutoff_time = datetime.fromtimestamp(int(time.time()) - time_limit)
        stmt = (
            select(TLotdyninfo)
            .filter(
                and_(
                    TLotdyninfo.isLot == True,
                    TLotdyninfo.created_at >= cutoff_time,
                )
            )
            .order_by(TLotdyninfo.pubTime.desc())
        )
        async with self.async_session() as session:
            res = await session.execute(stmt)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getAllLotDynByInsertTimeRange(
        self,
        created_at_start: int | None = None,
        created_at_end: int | None = None,
        pub_time_start: int | None = None,
        pub_time_end: int | None = None,
    ) -> Sequence[TLotdyninfo]:
        """按收录时间(created_at)和发布时间(pubTime)范围过滤抽奖动态

        :param created_at_start: 收录起始时间（Unix 秒），None 表示不限制下界
        :param created_at_end: 收录结束时间（Unix 秒），None 表示不限制上界
        :param pub_time_start: 发布起始时间（Unix 秒），None 表示不限制下界
        :param pub_time_end: 发布结束时间（Unix 秒），None 表示不限制上界
        """
        conditions = [TLotdyninfo.isLot == True]
        if created_at_start is not None:
            conditions.append(
                TLotdyninfo.created_at >= datetime.fromtimestamp(
                    created_at_start)
            )
        if created_at_end is not None:
            conditions.append(
                TLotdyninfo.created_at <= datetime.fromtimestamp(
                    created_at_end)
            )
        if pub_time_start is not None:
            conditions.append(
                TLotdyninfo.pubTime >= datetime.fromtimestamp(pub_time_start)
            )
        if pub_time_end is not None:
            conditions.append(
                TLotdyninfo.pubTime <= datetime.fromtimestamp(pub_time_end)
            )
        stmt = (
            select(TLotdyninfo)
            .filter(and_(*conditions))
            .order_by(TLotdyninfo.pubTime.desc())
        )
        async with self.async_session() as session:
            res = await session.execute(stmt)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def countValidLotByUidList(
        self, uid_list: list[int | str]
    ) -> dict[int, int]:
        """统计每个用户的有效抽奖数量（全量历史）"""
        async with self.async_session() as session:
            stmt = (
                select(TLotdyninfo.up_uid, func.count(TLotdyninfo.dynId))
                .filter(
                    and_(
                        TLotdyninfo.up_uid.in_(uid_list),
                        TLotdyninfo.isLot == True,
                    )
                )
                .group_by(TLotdyninfo.up_uid)
            )
            res = await session.execute(stmt)
            rows = res.all()
            return {int(row[0]): row[1] for row in rows}

    @log_sql_retry_wrapper()
    async def countValidLotByUidInTimeRange(
        self, uid_list: list[int | str], days: int = 14
    ) -> dict[int, int]:
        """统计每个用户在指定天数内发布的有效抽奖动态数量，用于剔除低活跃用户"""
        cutoff_time = datetime.fromtimestamp(int(time.time()) - days * 86400)
        async with self.async_session() as session:
            stmt = (
                select(TLotdyninfo.up_uid, func.count(TLotdyninfo.dynId))
                .filter(
                    and_(
                        TLotdyninfo.up_uid.in_(uid_list),
                        TLotdyninfo.isLot == True,
                        TLotdyninfo.pubTime >= cutoff_time,
                    )
                )
                .group_by(TLotdyninfo.up_uid)
            )
            res = await session.execute(stmt)
            rows = res.all()
            return {int(row[0]): row[1] for row in rows}

    @log_sql_retry_wrapper()
    async def getUserLotStatsByRound(
        self, uid_list: list[int | str], lot_round_id: int
    ) -> dict[int, dict]:
        """获取指定轮次中每个用户的抽奖统计：{uid: {'total': int, 'lot_count': int}}"""
        async with self.async_session() as session:
            stmt = (
                select(
                    TLotdyninfo.up_uid,
                    func.count(TLotdyninfo.dynId).label('total'),
                    func.sum(TLotdyninfo.isLot).label('lot_count'),
                )
                .filter(
                    and_(
                        TLotdyninfo.up_uid.in_(uid_list),
                        TLotdyninfo.dynLotRound_id == lot_round_id,
                    )
                )
                .group_by(TLotdyninfo.up_uid)
            )
            res = await session.execute(stmt)
            rows = res.all()
            return {
                int(row[0]): {
                    'total': row[1],
                    'lot_count': row[2] or 0,
                }
                for row in rows
            }

    @log_sql_retry_wrapper()
    async def getAllLotDynByLotRoundNum(
        self, LotRoundNum: int, offset: int = 0, page_size=0
    ) -> list[TLotdyninfo]:
        """
        根据轮次数量获取最新的抽奖信息
        :param page_size: 当page_size为0时，获取本轮全部内容
        :param offset: 只有当page_size有效时生效
        :param LotRoundNum:
        :return:
        """

        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(
                    and_(
                        TLotdyninfo.dynLotRound_id == LotRoundNum,
                        TLotdyninfo.isLot == 1,
                    )
                )
                .order_by(TLotdyninfo.dynId.desc())
            )
            if page_size:
                sql = sql.offset(offset).limit(page_size)
            else:
                # 未给 page_size 时默认 limit 1000，避免全量返回
                sql = sql.limit(1000)
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getAllLotDynInfoByRoundNum(
        self, LotRoundNum: int
    ) -> Sequence[TLotdyninfo]:
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(TLotdyninfo.dynLotRound_id == LotRoundNum)
                .order_by(TLotdyninfo.dynId.desc())
            )
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def isExistDynInfoByDynId(self, DynId: str) -> Union[TLotdyninfo, None]:
        async with self.async_session() as session:
            sql = select(TLotdyninfo).filter(
                TLotdyninfo.dynId == DynId).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def getAlldyid(self, ret_limit=10000) -> list[str]:
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo.dynId)
                .order_by(TLotdyninfo.dynId.desc())
                .limit(ret_limit)
            )
            res = await session.execute(sql)
            ret_list = res.scalars().all()
            return ret_list

    @log_sql_retry_wrapper()
    async def getAllLotdyid(self, ret_limit=10000) -> list[str]:
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo.dynId)
                .filter(TLotdyninfo.isLot == True)
                .order_by(TLotdyninfo.dynId.desc())
                .limit(ret_limit)
            )
            res = await session.execute(sql)
            ret_list = res.scalars().all()
            return ret_list

    @log_sql_retry_wrapper()
    async def addDynInfo(self, DynInfo: TLotdyninfo) -> None:
        """
        直接把最新的动态信息merge进去，同时提取奖品信息
        :param DynInfo:
        :return:
        """
        async with self.add_dyn_info_lock:
            async with self.async_session() as session:
                await session.merge(DynInfo)
                await session.commit()

        if DynInfo.dynContent and DynInfo.dynId:
            extract_result = await extract_prize_info(dyn_content=DynInfo.dynContent)
            if extract_result.result.prize_names or extract_result.result.lottery_time:
                await self.save_prize(DynInfo.dynId, extract_result.result.prize_names, extract_result.result.lottery_time)
            if extract_result.result.is_grand_prize:
                await self.save_extra_info(
                    ref_id=DynInfo.dynId,
                    lot_type="common",
                    is_grand_prize=int(extract_result.result.is_grand_prize),
                    need_comment=int(DynInfo.isManualReply) if DynInfo.isManualReply is not None else 0,
                    need_repost=0,
                )
    

    @log_sql_retry_wrapper()
    async def getDynInfoByDynamicId(self, dynamic_id: int | str) -> TLotdyninfo | None:
        """
        直接把最新的动态信息merge进去
        :param dynamic_id:
        :return:
        """
        async with self.async_session() as session:
            sql = select(TLotdyninfo).filter(TLotdyninfo.dynId == dynamic_id).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()

            return ret

    # endregion

    # region LotUserInfo增删改查
    @log_sql_retry_wrapper()
    async def getLotUserInfoByUid(self, uid: int) -> Union[TLotuserinfo, None]:
        async with self.async_session() as session:
            sql = select(TLotuserinfo).filter(TLotuserinfo.uid == uid).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()

            return ret

    @log_sql_retry_wrapper()
    async def getLotUserInfoByUidList(
        self, uid_list: list[int | str]
    ) -> dict[int, TLotuserinfo]:
        """批量获取用户的 TLotuserinfo，返回 {uid: TLotuserinfo}"""
        if not uid_list:
            return {}
        async with self.async_session() as session:
            sql = select(TLotuserinfo).filter(TLotuserinfo.uid.in_(uid_list))
            res = await session.execute(sql)
            rows = res.scalars().all()
            return {int(row.uid): row for row in rows}

    @log_sql_retry_wrapper()
    async def addLotUserInfo(self, LotUserInfo: TLotuserinfo):
        async with self.async_session() as session:
            await session.merge(LotUserInfo)
            await session.commit()

    # endregion

    # region 空间响应的增删改查
    @log_sql_retry_wrapper()
    async def getSpaceRespByRoundId(
        self, round_id: int | str
    ) -> Sequence[TLotuserspaceresp]:
        """
        获取所有比offset值大的动态，也就是获取offset值之后发布的动态
        :param uid:
        :param offset:
        :return:
        """
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(TLotuserspaceresp.dynLotRound_id == round_id)
                .order_by(TLotuserspaceresp.spaceOffset.desc())
            )
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @log_sql_retry_wrapper()
    async def getSpaceRespTillOffset(
        self, uid: Union[int, str], offset: Union[int, str]
    ) -> list[dict]:
        """
        获取所有比offset值大的动态，也就是获取offset值之后发布的动态
        :param uid:
        :param offset:
        :return:
        """
        if offset is None:
            offset = ""
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(
                    and_(
                        TLotuserspaceresp.spaceUid == uid,
                        TLotuserspaceresp.spaceOffset >= offset,
                    )
                )
                .order_by(TLotuserspaceresp.spaceOffset.desc())
            )
            res = await session.execute(sql)
            ret: list[TLotuserspaceresp] = res.scalars().all()
            return [x.spaceRespJson for x in ret]

    @log_sql_retry_wrapper()
    async def addSpaceResp(self, LotUserSpaceResp: TLotuserspaceresp):
        async with self.async_session() as session:
            await session.merge(LotUserSpaceResp)
            await session.commit()

    @log_sql_retry_wrapper()
    async def getOldestSpaceDynInfoByUid(self, uid: int) -> int:
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(TLotuserspaceresp.spaceUid == uid)
                .order_by(TLotuserspaceresp.spaceOffset.asc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret: TLotuserspaceresp = res.scalars().first()
            if ret:
                return ret.spaceOffset
            else:
                return 0

    @log_sql_retry_wrapper()
    async def getNewestSpaceDynInfoByUid(self, uid: int) -> int:
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(TLotuserspaceresp.spaceUid == uid)
                .order_by(TLotuserspaceresp.spaceOffset.desc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret: TLotuserspaceresp = res.scalars().first()
            if ret:
                return ret.spaceOffset
            else:
                return 0

    @log_sql_retry_wrapper()
    async def getOldestSpaceOffsetByUidRoundId(self, uid: int, round_id: int) -> int:
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(
                    and_(
                        TLotuserspaceresp.spaceUid == uid,
                        TLotuserspaceresp.dynLotRound_id == round_id,
                    )
                )
                .order_by(TLotuserspaceresp.spaceOffset.asc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret: TLotuserspaceresp = res.scalars().first()
            if ret:
                return ret.spaceOffset
            else:
                return 0

    @log_sql_retry_wrapper()
    async def get_lot_user_info_updatetime_by_uid(
        self, uid: Union[int, str]
    ) -> Union[datetime, None]:
        async with self.async_session() as session:
            sql = (
                select(TLotuserinfo.updatetime)
                .filter(TLotuserinfo.uid == uid)
                .order_by(TLotuserinfo.uid.desc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    # endregion

    @log_sql_retry_wrapper()
    async def isExistSpaceInfoByDynId(
        self, dynamic_id
    ) -> Union[TLotuserspaceresp, None]:
        async with self.async_session() as session:
            sql = (
                select(TLotuserspaceresp)
                .filter(TLotuserspaceresp.spaceOffset == str(dynamic_id))
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def getLatestLotDynInfoByUid(self, uid: int | str) -> TLotdyninfo | None:
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(and_(TLotdyninfo.up_uid == uid, TLotdyninfo.isLot == True))
                .order_by(TLotdyninfo.dynId.desc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def getLatestLotDynInfoByUidList(
        self, uid_list: list[int | str]
    ) -> Sequence[TLotdyninfo]:
        async with self.async_session() as session:
            subq = (
                select(func.max(TLotdyninfo.dynId))
                .where(TLotdyninfo.up_uid.in_(uid_list), TLotdyninfo.isLot == True)
                .group_by(TLotdyninfo.up_uid)
                .scalar_subquery()  # 返回单个列的值
            )

            # 主查询：获取这些 dynId 对应的完整记录
            stmt = select(TLotdyninfo).where(TLotdyninfo.dynId.in_(subq))

            result = await session.execute(stmt)
            records = result.scalars().all()
            return records

    @log_sql_retry_wrapper()
    async def getLatestLotDyn(self) -> TLotdyninfo | None:
        """获取最新的一条抽奖动态"""
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(TLotdyninfo.isLot == True)
                .order_by(TLotdyninfo.pubTime.desc())
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @log_sql_retry_wrapper()
    async def getRecentHotLotDyns(
        self, days: int = 7, top_n: int = 10
    ) -> Sequence[TLotdyninfo]:
        """获取最近 N 天内互动数（评论+转发）最高的 top_n 条抽奖动态。
        用于从高热度抽奖动态的评论区挖掘潜在抽奖用户。

        :param days: 时间范围（天）
        :param top_n: 返回条数
        """
        cutoff_time = datetime.fromtimestamp(int(time.time()) - days * 86400)
        async with self.async_session() as session:
            sql = (
                select(TLotdyninfo)
                .filter(
                    and_(
                        TLotdyninfo.isLot == True,
                        TLotdyninfo.pubTime >= cutoff_time,
                        TLotdyninfo.commentCount > 0,
                    )
                )
                .order_by(
                    (TLotdyninfo.commentCount + TLotdyninfo.repostCount).desc()
                )
                .limit(top_n)
            )
            res = await session.execute(sql)
            return res.scalars().all()

    @log_sql_retry_wrapper()
    async def getRidAndTypeByDynId(self, dyn_id: int | str) -> tuple[int, int] | None:
        """查询特殊动态（视频/转发等）的 rid 与 dynamic_type 映射。
        t_riddynid 表仅记录非纯文本动态（如 type=8 视频、type=4 转发）的
        rid -> dynamic_id 对应关系，用于通过 rid+type 反查 dynamic_id 或根据
        dynamic_id 获取评论区所需的 rid+type。纯文本动态不在此表中。
        """
        async with self.async_session() as session:
            sql = (
                select(TRiddynid)
                .filter(TRiddynid.dynamic_id == int(dyn_id))
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            if ret:
                return ret.rid, ret.dynamic_type
            return None

    @log_sql_retry_wrapper()
    async def getLotDynListPaginated(
        self,
        page_num: int = 1,
        page_size: int = 20,
        sort_by: str = "pubTime",
        sort_order: str = "desc",
        is_lot: bool | None = True,
        pub_time_start: int | None = None,
        pub_time_end: int | None = None,
        created_at_start: int | None = None,
        created_at_end: int | None = None,
    ) -> tuple[list[TLotdyninfo], int]:
        """分页获取抽奖动态列表，支持排序和时间筛选

        :param page_num: 页码，从1开始
        :param page_size: 每页数量
        :param sort_by: 排序字段，支持 pubTime / created_at
        :param sort_order: 排序方向，asc / desc
        :param is_lot: 筛选是否抽奖，None 表示不过滤
        :param pub_time_start: 发布时间起始（Unix 时间戳，秒）
        :param pub_time_end: 发布时间截止（Unix 时间戳，秒）
        :param created_at_start: 创建时间起始（Unix 时间戳，秒）
        :param created_at_end: 创建时间截止（Unix 时间戳，秒）
        :return: (items, total)
        """
        async with self.async_session() as session:
            conditions = []
            if is_lot is not None:
                conditions.append(TLotdyninfo.isLot == is_lot)
            if pub_time_start is not None:
                conditions.append(TLotdyninfo.pubTime >= datetime.fromtimestamp(pub_time_start))
            if pub_time_end is not None:
                conditions.append(TLotdyninfo.pubTime <= datetime.fromtimestamp(pub_time_end))
            if created_at_start is not None:
                conditions.append(TLotdyninfo.created_at >= datetime.fromtimestamp(created_at_start))
            if created_at_end is not None:
                conditions.append(TLotdyninfo.created_at <= datetime.fromtimestamp(created_at_end))

            sort_column = getattr(TLotdyninfo, sort_by, TLotdyninfo.pubTime)
            order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
            offset = max(0, (page_num - 1) * page_size)

            # 分为 COUNT + DATA 两条独立查询：COUNT 走索引覆盖，DATA 仅扫 LIMIT 行
            total = (await session.execute(
                select(func.count(TLotdyninfo.dynId)).where(*conditions)
            )).scalar() or 0

            data_stmt = (
                select(TLotdyninfo)
                .where(*conditions)
                .order_by(order_clause)
                .offset(offset)
                .limit(page_size)
            )
            data_res = await session.execute(data_stmt)
            items = list(data_res.scalars().all())

            return items, total

    @log_sql_retry_wrapper()
    async def getLotDynListPaginatedWithPrizes(
        self,
        page_num: int = 1,
        page_size: int = 20,
        sort_by: str = "pubTime",
        sort_order: str = "desc",
        is_lot: bool | None = True,
        pub_time_start: int | None = None,
        pub_time_end: int | None = None,
        created_at_start: int | None = None,
        created_at_end: int | None = None,
    ) -> tuple[list[TLotdyninfo], int, dict[int, TOthersLotInfo]]:
        """分页获取抽奖动态列表，并在同一 session 内附带返回已缓存的奖品信息

        合并原先 getLotDynListPaginated + get_prizes_by_dyn_ids 两次独立查询为一次 session，
        减少数据库连接开销和网络往返。

        :return: (items, total, prize_map)
        """
        async with self.async_session() as session:
            # --- 构建共用筛选条件 ---
            conditions = []
            if is_lot is not None:
                conditions.append(TLotdyninfo.isLot == is_lot)
            if pub_time_start is not None:
                conditions.append(TLotdyninfo.pubTime >= datetime.fromtimestamp(pub_time_start))
            if pub_time_end is not None:
                conditions.append(TLotdyninfo.pubTime <= datetime.fromtimestamp(pub_time_end))
            if created_at_start is not None:
                conditions.append(TLotdyninfo.created_at >= datetime.fromtimestamp(created_at_start))
            if created_at_end is not None:
                conditions.append(TLotdyninfo.created_at <= datetime.fromtimestamp(created_at_end))

            sort_column = getattr(TLotdyninfo, sort_by, TLotdyninfo.pubTime)
            order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
            offset = max(0, (page_num - 1) * page_size)

            # --- 1. COUNT 查询：索引覆盖扫描，不读数据行 ---
            total = (await session.execute(
                select(func.count(TLotdyninfo.dynId)).where(*conditions)
            )).scalar() or 0

            # --- 2. 分页数据查询 ---
            data_stmt = (
                select(TLotdyninfo)
                .where(*conditions)
                .order_by(order_clause)
                .offset(offset)
                .limit(page_size)
            )
            data_res = await session.execute(data_stmt)
            items = list(data_res.scalars().all())

            # --- 3. 批量获取已缓存的奖品信息 ---
            dyn_ids = [item.dynId for item in items]
            prize_map: dict[int, TOthersLotInfo] = {}
            if dyn_ids:
                prize_sql = (
                    select(TOthersLotInfo)
                    .options(selectinload(TOthersLotInfo.extra_info))
                    .filter(TOthersLotInfo.dynId.in_(dyn_ids))
                )
                prize_res = await session.execute(prize_sql)
                prize_map = {row.dynId: row for row in prize_res.scalars().all()}

            return items, total, prize_map

    # region 第三方抽奖奖品缓存
    @log_sql_retry_wrapper()
    async def get_prize_by_dyn_id(self, dyn_id: int | str) -> TOthersLotInfo | None:
        """根据 dynId 获取已缓存的提取信息"""
        async with self.async_session() as session:
            sql = select(TOthersLotInfo).filter(TOthersLotInfo.dynId == int(dyn_id)).limit(1)
            res = await session.execute(sql)
            return res.scalars().first()

    @log_sql_retry_wrapper()
    async def get_prizes_by_dyn_ids(self, dyn_ids: list[int]) -> dict[int, TOthersLotInfo]:
        """批量获取多个 dynId 的提取信息缓存（含 extra_info）"""
        if not dyn_ids:
            return {}
        async with self.async_session() as session:
            sql = (
                select(TOthersLotInfo)
                .options(selectinload(TOthersLotInfo.extra_info))
                .filter(TOthersLotInfo.dynId.in_(dyn_ids))
            )
            res = await session.execute(sql)
            rows = res.scalars().all()
            return {row.dynId: row for row in rows}

    @log_sql_retry_wrapper()
    async def save_prize(self, dyn_id: int, prize_names: list[str],
                        lottery_time: str | None = None) -> None:
        """保存 UIE 提取的奖品信息（原子 upsert，避免并发重复插入）"""
        async with self.async_session() as session:
            stmt = mysql_insert(TOthersLotInfo).values(
                dynId=int(dyn_id),
                prize_names=prize_names,
                lottery_time=lottery_time,
            )
            stmt = stmt.on_duplicate_key_update(
                prize_names=stmt.inserted.prize_names,
                lottery_time=stmt.inserted.lottery_time,
            )
            await session.execute(stmt)
            await session.commit()
    # endregion

    # region 大奖SVM判断结果子表
    @log_sql_retry_wrapper()
    async def save_extra_info(
        self,
        ref_id: int,
        lot_type: str,
        is_grand_prize: int = 0,
        need_comment: int | None = None,
        need_repost: int | None = None,
    ) -> None:
        """保存或更新抽奖附加信息（原子 upsert）

        :param need_comment: 是否需要评论，None 表示不更新该字段
        :param need_repost: 是否需要转发，None 表示不更新该字段
        """
        async with self.async_session() as session:
            insert_values = {
                "ref_id": ref_id,
                "lot_type": lot_type,
                "is_grand_prize": is_grand_prize,
            }
            update_values = {
                "is_grand_prize": is_grand_prize,
                "predicted_at": text('CURRENT_TIMESTAMP'),
            }
            if need_comment is not None:
                insert_values["need_comment"] = need_comment
                update_values["need_comment"] = need_comment
            if need_repost is not None:
                insert_values["need_repost"] = need_repost
                update_values["need_repost"] = need_repost

            stmt = mysql_insert(TLotExtraInfo).values(**insert_values)
            stmt = stmt.on_duplicate_key_update(**update_values)
            await session.execute(stmt)
            await session.commit()

    @log_sql_retry_wrapper()
    async def get_extra_info_by_ref_ids(
        self, ref_ids: list[int], lot_type: str
    ) -> dict[int, int]:
        """批量查询大奖SVM判断结果，返回 {ref_id: is_grand_prize}"""
        if not ref_ids:
            return {}
        async with self.async_session() as session:
            stmt = select(TLotExtraInfo).filter(
                and_(
                    TLotExtraInfo.ref_id.in_(ref_ids),
                    TLotExtraInfo.lot_type == lot_type,
                )
            )
            res = await session.execute(stmt)
            rows = res.scalars().all()
            return {row.ref_id: row.is_grand_prize for row in rows}

    @log_sql_retry_wrapper()
    async def get_ref_ids_without_extra_info(
        self, lot_type: str, limit: int = 5000
    ) -> list[int]:
        """查询未做过SVM判断的记录ID列表（用于手动回填脚本）
        limit=0 表示不限制数量，查询全部记录"""
        async with self.async_session() as session:
            # 找出所有抽奖动态的dynId，排除已有extra_info的
            if lot_type == "common":
                subq = select(TLotExtraInfo.ref_id).filter(
                    TLotExtraInfo.lot_type == "common"
                )
                stmt = (
                    select(TLotdyninfo.dynId)
                    .filter(
                        and_(
                            TLotdyninfo.isLot == 1,
                            TLotdyninfo.dynContent.isnot(None),
                            TLotdyninfo.dynContent != "",
                            TLotdyninfo.dynId.notin_(subq),
                        )
                    )
                )
                if limit > 0:
                    stmt = stmt.limit(limit)
            else:
                return []  # 其他类型暂不支持批量查询
            res = await session.execute(stmt)
            return [row[0] for row in res.all()]

    @log_sql_retry_wrapper()
    async def get_all_common_lot_dyn_ids(self, limit: int = 10000) -> list[int]:
        """获取所有普通抽奖动态的dynId（用于全量SVM判断脚本）
        limit=0 表示不限制数量，查询全部记录"""
        async with self.async_session() as session:
            stmt = (
                select(TLotdyninfo.dynId)
                .filter(
                    and_(
                        TLotdyninfo.isLot == 1,
                        TLotdyninfo.dynContent.isnot(None),
                        TLotdyninfo.dynContent != "",
                    )
                )
            )
            if limit > 0:
                stmt = stmt.limit(limit)
            res = await session.execute(stmt)
            return [row[0] for row in res.all()]

    @log_sql_retry_wrapper()
    async def get_dyn_info_batch(self, dyn_ids: list[int]) -> dict[int, str]:
        """批量获取动态内容，返回 {dynId: dynContent}"""
        if not dyn_ids:
            return {}
        async with self.async_session() as session:
            stmt = select(TLotdyninfo.dynId, TLotdyninfo.dynContent).filter(
                TLotdyninfo.dynId.in_(dyn_ids)
            )
            res = await session.execute(stmt)
            rows = res.all()
            return {row[0]: row[1] for row in rows if row[1]}
    # endregion


get_other_lot_redis_manager = GetOtherLotRedisManager()

SqlHelper = __SqlHelper()

if __name__ == "__main__":

    async def __test__():
        result = await SqlHelper.getLatestLotDynInfoByUidList(
            [3546740766541963, 114514]
        )
        print(result)

    asyncio.run(__test__())
