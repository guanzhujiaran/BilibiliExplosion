import ast
import asyncio
import json
import time
from datetime import datetime
from enum import StrEnum
from typing import Union, List, Sequence

from sqlalchemy import select, and_, func
from sqlalchemy.dialects.mysql import insert as mysql_insert

from CONFIG import CONFIG
from Utils.dynamic_id_caculate import ts_2_fake_dynamic_id
from Service.GetOthersLotDyn.Sql.models import (
    TLotmaininfo,
    TLotuserinfo,
    TLotdyninfo,
    TLotuserspaceresp,
    TRiddynid,
    TOthersLotInfo,
)
from Utils.Common import sql_retry_wrapper
from Utils.redisTool.RedisManager import RedisManagerBase
from dao.base.sqlHelperBase import SqlHelperBase


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

    async def set_target_uid_list(self, uid_list: List[int | str]):
        await self._set(self.RedisMap.target_uid_list.value, json.dumps(uid_list))

    async def get_target_uid_list(self) -> List[int | str]:
        if val := await self._get(self.RedisMap.target_uid_list.value):
            return json.loads(val)
        else:
            return []

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

    @sql_retry_wrapper
    async def getDynIdByRidType(self, rid: int, dynamic_type: int) -> Union[int, None]:
        async with self.async_session() as session:
            sql = (
                select(TRiddynid.dynamic_id)
                .filter(
                    and_(TRiddynid.rid == rid, TRiddynid.dynamic_type == dynamic_type)
                )
                .limit(1)
            )
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret if ret else 0

    @sql_retry_wrapper
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
    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def getLatestRound(self) -> Union[TLotmaininfo, None]:
        async with self.async_session() as session:
            sql = (
                select(TLotmaininfo).order_by(TLotmaininfo.lotRound_id.desc()).limit(1)
            )
            res = await session.execute(sql)
            ret: TLotmaininfo = res.scalars().first()
            return ret

    @sql_retry_wrapper
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
    @sql_retry_wrapper
    async def getAllDynInfo(self) -> Sequence[TLotdyninfo]:
        async with self.async_session() as session:
            sql = select(TLotdyninfo).order_by(TLotdyninfo.dynId.desc())
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def getAllLotDynByTimeLimit(self, time_limit: int = 20 * 3600 * 24):
        target_dyn_id = ts_2_fake_dynamic_id(int(time.time()) - time_limit)
        stmt = select(TLotdyninfo).filter(
            and_(TLotdyninfo.isLot == True, TLotdyninfo.dynId >= target_dyn_id)
        )
        async with self.async_session() as session:
            res = await session.execute(stmt)
            ret = res.scalars().all()
            return ret

    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def countValidLotByUidList(
        self, uid_list: list[int | str]
    ) -> dict[int, int]:
        """统计每个用户的有效抽奖数量"""
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

    @sql_retry_wrapper
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
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def isExistDynInfoByDynId(self, DynId: str) -> Union[TLotdyninfo, None]:
        async with self.async_session() as session:
            sql = select(TLotdyninfo).filter(TLotdyninfo.dynId == DynId).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

        # 爬取阶段同步提取奖品信息并存入数据库
        if DynInfo.dynContent and DynInfo.dynId:
            try:
                from Service.GetOthersLotDyn.parser.prize_extractor import (
                    extract_prize_names, extract_lottery_time)

                prize_names = await extract_prize_names(DynInfo.dynContent)
                lottery_time = await extract_lottery_time(DynInfo.dynContent)
                if prize_names or lottery_time:
                    await self.save_prize(DynInfo.dynId, prize_names, lottery_time)
            except Exception:
                pass  # 提取失败不影响主流程，接口端会做保险

    @sql_retry_wrapper
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
    @sql_retry_wrapper
    async def getLotUserInfoByUid(self, uid: int) -> Union[TLotuserinfo, None]:
        async with self.async_session() as session:
            sql = select(TLotuserinfo).filter(TLotuserinfo.uid == uid).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()

            return ret

    @sql_retry_wrapper
    async def addLotUserInfo(self, LotUserInfo: TLotuserinfo):
        async with self.async_session() as session:
            await session.merge(LotUserInfo)
            await session.commit()

    # endregion

    # region 空间响应的增删改查
    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def addSpaceResp(self, LotUserSpaceResp: TLotuserspaceresp):
        async with self.async_session() as session:
            await session.merge(LotUserSpaceResp)
            await session.commit()

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
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

    @sql_retry_wrapper
    async def getRidAndTypeByDynId(self, dyn_id: int | str) -> tuple[int, int] | None:
        """根据动态ID获取rid和type"""
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

    @sql_retry_wrapper
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
            # 基础查询
            stmt = select(TLotdyninfo)
            if is_lot is not None:
                stmt = stmt.filter(TLotdyninfo.isLot == is_lot)
            if pub_time_start is not None:
                stmt = stmt.filter(TLotdyninfo.pubTime >= datetime.fromtimestamp(pub_time_start))
            if pub_time_end is not None:
                stmt = stmt.filter(TLotdyninfo.pubTime <= datetime.fromtimestamp(pub_time_end))
            if created_at_start is not None:
                stmt = stmt.filter(TLotdyninfo.created_at >= datetime.fromtimestamp(created_at_start))
            if created_at_end is not None:
                stmt = stmt.filter(TLotdyninfo.created_at <= datetime.fromtimestamp(created_at_end))

            # 获取总数
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_res = await session.execute(count_stmt)
            total = total_res.scalar() or 0

            # 排序
            sort_column = getattr(TLotdyninfo, sort_by, TLotdyninfo.pubTime)
            if sort_order == "asc":
                stmt = stmt.order_by(sort_column.asc())
            else:
                stmt = stmt.order_by(sort_column.desc())

            # 分页
            offset = (page_num - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            res = await session.execute(stmt)
            items = res.scalars().all()
            return list(items), total

    # region 第三方抽奖奖品缓存
    @sql_retry_wrapper
    async def get_prize_by_dyn_id(self, dyn_id: int | str) -> TOthersLotInfo | None:
        """根据 dynId 获取已缓存的提取信息"""
        async with self.async_session() as session:
            sql = select(TOthersLotInfo).filter(TOthersLotInfo.dynId == int(dyn_id)).limit(1)
            res = await session.execute(sql)
            return res.scalars().first()

    @sql_retry_wrapper
    async def get_prizes_by_dyn_ids(self, dyn_ids: list[int]) -> dict[int, TOthersLotInfo]:
        """批量获取多个 dynId 的提取信息缓存"""
        if not dyn_ids:
            return {}
        async with self.async_session() as session:
            sql = select(TOthersLotInfo).filter(TOthersLotInfo.dynId.in_(dyn_ids))
            res = await session.execute(sql)
            rows = res.scalars().all()
            return {row.dynId: row for row in rows}

    @sql_retry_wrapper
    async def save_prize(self, dyn_id: int, prize_names: list[str],
                        lottery_time: str | None = None) -> None:
        """保存 ModelScope 提取的奖品信息（原子 upsert，避免并发重复插入）"""
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


get_other_lot_redis_manager = GetOtherLotRedisManager()

SqlHelper = __SqlHelper()

if __name__ == "__main__":

    async def __test__():
        result = await SqlHelper.getLatestLotDynInfoByUidList(
            [3546740766541963, 114514]
        )
        print(result)

    asyncio.run(__test__())
