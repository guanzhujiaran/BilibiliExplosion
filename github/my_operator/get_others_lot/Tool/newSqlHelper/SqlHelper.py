import asyncio
from datetime import datetime
import json
import random
import traceback
from typing import Union, Callable, Literal
from fastapi接口.log.base_log import get_others_lot_logger
from sqlalchemy import AsyncAdaptedQueuePool, select, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession,async_sessionmaker
from github.my_operator.get_others_lot.Tool.newSqlHelper.models import *

from CONFIG import CONFIG


def lock_wrapper(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                get_others_lot_logger.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


class __SqlHelper:
    def __init__(self):
        SQLITE_URI = CONFIG.database.MYSQL.get_other_lot_URI
        self.op_db_lock = asyncio.Lock()
        self._engine = create_async_engine(
            SQLITE_URI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self._session =  async_sessionmaker(self._engine,
                                     expire_on_commit=False,
                                     )

    # region 获取抽奖轮次信息相关
    @lock_wrapper
    async def getLatestRound(self) -> Union[TLotmaininfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotmaininfo).order_by(TLotmaininfo.lotRound_id.desc()).limit(1)
                res = await session.execute(sql)
                ret: TLotmaininfo = res.scalars().first()
                return ret

    @lock_wrapper
    async def addLotMainInfo(self, LotMainInfo: TLotmaininfo):
        async with self.op_db_lock:
            async with self._session() as session:
                async with session.begin():
                    sql = select(TLotmaininfo).filter(TLotmaininfo.lotRound_id == LotMainInfo.lotRound_id).limit(1)
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
    @lock_wrapper
    async def getAllDynInfo(self) -> list[TLotdyninfo]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotdyninfo).order_by(TLotdyninfo.dynId.desc())
                res = await session.execute(sql)
                ret = res.scalars().all()
                return ret

    @lock_wrapper
    async def getAllDynByLotRound(self, LotRound_id: int) -> list[TLotdyninfo]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotdyninfo).filter(TLotdyninfo.dynLotRound_id == LotRound_id).order_by(
                    TLotdyninfo.dynId.desc())
                res = await session.execute(sql)
                ret = res.scalars().all()
                return ret

    @lock_wrapper
    async def getAllLotDynByLotRoundNum(self, LotRoundNum: int, offset: int = 0, page_size=0) -> list[TLotdyninfo]:
        """
        根据轮次数量获取最新的抽奖信息
        :param LotRoundNum:
        :return:
        """

        last_round = await self.getLatestRound()
        if last_round:
            async with self.op_db_lock:
                async with self._session() as session:
                    last_round_id = last_round.lotRound_id if last_round.isRoundFinished else last_round.lotRound_id - 1
                    sql = select(TLotdyninfo).filter(and_(TLotdyninfo.dynLotRound_id > (last_round_id - LotRoundNum),
                                                          TLotdyninfo.isLot == 1)).order_by(
                        TLotdyninfo.dynId.desc())
                    if offset and page_size:
                        sql = sql.offset(offset).limit(page_size)
                    res = await session.execute(sql)
                    ret = res.scalars().all()
                    return ret
        else:
            return []

    @lock_wrapper
    async def isExistDynInfoByDynId(self, DynId: str) -> Union[TLotdyninfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotdyninfo).filter(TLotdyninfo.dynId == DynId).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()
                return ret

    @lock_wrapper
    async def getAlldyid(self, ret_limit=10000) -> list[str]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotdyninfo.dynId).order_by(TLotdyninfo.dynId.desc()).limit(ret_limit)
                res = await session.execute(sql)
                ret_list = res.scalars().all()
                return ret_list

    @lock_wrapper
    async def getAllLotdyid(self, ret_limit=10000) -> list[str]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotdyninfo.dynId).filter(TLotdyninfo.isLot == True).order_by(
                    TLotdyninfo.dynId.desc()).limit(
                    ret_limit)
                res = await session.execute(sql)
                ret_list = res.scalars().all()
                return ret_list

    @lock_wrapper
    async def addDynInfo(self, DynInfo: TLotdyninfo) -> None:
        """
        直接把最新的动态信息merge进去
        :param DynInfo:
        :return:
        """
        async with self.op_db_lock:
            async with self._session() as session:
                async with session.begin():
                    await session.merge(DynInfo)

    # endregion

    # region LotUserInfo增删改查
    @lock_wrapper
    async def getLotUserInfoByUid(self, uid: int) -> Union[TLotuserinfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserinfo).filter(TLotuserinfo.uid == uid).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()

                return ret

    @lock_wrapper
    async def addLotUserInfo(self, LotUserInfo: TLotuserinfo):
        async with self.op_db_lock:
            async with self._session() as session:
                async with session.begin():
                    await session.merge(LotUserInfo)

    # endregion

    # region 空间响应的增删改查
    @lock_wrapper
    async def getSpaceRespTillOffset(self, uid: Union[int, str], offset: Union[int, str]) -> list[dict]:
        """
        获取所有比offset值大的动态，也就是获取offset值之后发布的动态
        :param uid:
        :param offset:
        :return:
        """
        if offset is None:
            offset = ""
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserspaceresp).filter(and_(
                    TLotuserspaceresp.spaceUid == uid,
                    TLotuserspaceresp.spaceOffset >= offset
                )).order_by(TLotuserspaceresp.spaceOffset.desc())
                res = await session.execute(sql)
                ret: list[TLotuserspaceresp] = res.scalars().all()
                return [x.spaceRespJson for x in ret]

    @lock_wrapper
    async def addSpaceResp(self, LotUserSpaceResp: TLotuserspaceresp):
        async with self.op_db_lock:
            async with self._session() as session:
                async with session.begin():
                    await session.merge(LotUserSpaceResp)

    @lock_wrapper
    async def getOldestSpaceDynInfoByUid(self, uid: int) -> int:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserspaceresp).filter(TLotuserspaceresp.spaceUid == uid).order_by(
                    TLotuserspaceresp.spaceOffset.asc()).limit(1)
                res = await session.execute(sql)
                ret: TLotuserspaceresp = res.scalars().first()
                if ret:
                    return ret.spaceOffset
                else:
                    return 0

    @lock_wrapper
    async def getNewestSpaceDynInfoByUid(self, uid: int) -> int:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserspaceresp).filter(TLotuserspaceresp.spaceUid == uid).order_by(
                    TLotuserspaceresp.spaceOffset.desc()).limit(1)
                res = await session.execute(sql)
                ret: TLotuserspaceresp = res.scalars().first()
                if ret:
                    return ret.spaceOffset
                else:
                    return 0

    @lock_wrapper
    async def get_lot_user_info_updatetime_by_uid(self, uid: Union[int, str]) -> Union[datetime, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserinfo.updatetime).filter(TLotuserinfo.uid == uid).order_by(
                    TLotuserinfo.uid.desc()).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()
                return ret

    # endregion

    @lock_wrapper
    async def isExistSpaceInfoByDynId(self, dynamic_id) -> Union[TLotuserspaceresp, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotuserspaceresp).filter(TLotuserspaceresp.spaceOffset == str(dynamic_id)).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()
                return ret



SqlHelper = __SqlHelper()
async def __test__():

    result = await SqlHelper.getAllLotDynByLotRoundNum(
        1,1000,10
    )
    print([x.__dict__ for x in result])


if __name__ == '__main__':
    asyncio.run(__test__())
