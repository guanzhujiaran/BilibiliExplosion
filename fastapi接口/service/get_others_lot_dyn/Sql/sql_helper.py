import ast
import asyncio
import json
from datetime import datetime
import random
from enum import Enum
from typing import Union, Callable, List, Sequence

from sqlalchemy.exc import IntegrityError, InternalError

from fastapi接口.log.base_log import get_others_lot_logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotmaininfo, TLotuserinfo, TLotdyninfo, \
    TLotuserspaceresp, TRiddynid

from CONFIG import CONFIG
from utl.redisTool.RedisManager import RedisManagerBase


def lock_wrapper(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await func(*args, **kwargs)
                return res
            except (IntegrityError, InternalError) as e:
                get_others_lot_logger.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue
            except Exception as e:
                get_others_lot_logger.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


class GetOtherLotRedisManager(RedisManagerBase):
    class RedisMap(str, Enum):
        target_uid_list = 'get_other_lot_redis_manager:target_uid_list'
        get_dyn_ts = 'get_other_lot_redis_manager:get_dyn_ts'

    def __init__(self):
        super().__init__(
            host=CONFIG.database.getOtherLotRedis.host,
            port=CONFIG.database.getOtherLotRedis.port,
            db=CONFIG.database.getOtherLotRedis.db)

    async def set_target_uid_list(self, uid_list: List[int | str]):
        await self._set(self.RedisMap.target_uid_list.value, json.dumps(uid_list))

    async def get_target_uid_list(self) -> List[int | str]:
        if val := await self._get(self.RedisMap.target_uid_list.value):
            return ast.literal_eval(val)
        else:
            return []

    async def get_get_dyn_ts(self) -> int:
        get_dyn_ts = await self._get(self.RedisMap.get_dyn_ts.value)
        return int(get_dyn_ts if get_dyn_ts else 0)

    async def set_get_dyn_ts(self, get_dyn_ts: int):
        await self._set(self.RedisMap.get_dyn_ts.value, get_dyn_ts)


class __SqlHelper:
    def __init__(self):
        SQLITE_URI = CONFIG.database.MYSQL.get_other_lot_URI
        self._engine = create_async_engine(
            SQLITE_URI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self._session = async_sessionmaker(self._engine,
            **CONFIG.sql_alchemy_config.session_config
                                           )

    @lock_wrapper
    async def getDynIdByRidType(self, rid: int, dynamic_type: int) -> Union[int, None]:
        async with self._session() as session:
            sql = select(TRiddynid.dynamic_id).filter(
                and_(TRiddynid.rid == rid, TRiddynid.dynamic_type == dynamic_type)).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret if ret else 0

    @lock_wrapper
    async def setDynIdByRidType(self, dynamic_id: int, rid: int, dynamic_type: int):
        async with self._session() as session:
            await session.merge(TRiddynid(
                dynamic_id=int(dynamic_id),
                rid=int(rid),
                dynamic_type=int(dynamic_type)
            ))
            await session.commit()
    # region 获取抽奖轮次信息相关
    @lock_wrapper
    async def getLatestFinishedRound(self) -> Union[TLotmaininfo, None]:
        async with self._session() as session:
            sql = select(TLotmaininfo).where(TLotmaininfo.isRoundFinished == 1).order_by(
                TLotmaininfo.lotRound_id.desc()).limit(1)
            res = await session.execute(sql)
            ret: TLotmaininfo = res.scalars().first()
            return ret

    @lock_wrapper
    async def getLatestRound(self) -> Union[TLotmaininfo, None]:
        async with self._session() as session:
            sql = select(TLotmaininfo).order_by(TLotmaininfo.lotRound_id.desc()).limit(1)
            res = await session.execute(sql)
            ret: TLotmaininfo = res.scalars().first()
            return ret

    @lock_wrapper
    async def addLotMainInfo(self, LotMainInfo: TLotmaininfo):
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
    async def getAllDynInfo(self) -> Sequence[TLotdyninfo]:
        async with self._session() as session:
            sql = select(TLotdyninfo).order_by(TLotdyninfo.dynId.desc())
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @lock_wrapper
    async def getAllDynByLotRound(self, LotRound_id: int) -> Sequence[TLotdyninfo]:
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
        :param page_size: 当page_size为0时，获取本轮全部内容
        :param offset: 只有当page_size有效时生效
        :param LotRoundNum:
        :return:
        """

        async with self._session() as session:
            sql = select(TLotdyninfo).filter(and_(TLotdyninfo.dynLotRound_id == LotRoundNum,
                                                  TLotdyninfo.isLot == 1)).order_by(
                TLotdyninfo.dynId.desc())
            if page_size:
                sql = sql.offset(offset).limit(page_size)
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @lock_wrapper
    async def getAllLotDynInfoByRoundNum(self, LotRoundNum: int) -> Sequence[TLotdyninfo]:
        async with self._session() as session:
            sql = select(TLotdyninfo).filter(TLotdyninfo.dynLotRound_id == LotRoundNum).order_by(
                TLotdyninfo.dynId.desc())
            res = await session.execute(sql)
            ret = res.scalars().all()
            return ret

    @lock_wrapper
    async def isExistDynInfoByDynId(self, DynId: str) -> Union[TLotdyninfo, None]:
        async with self._session() as session:
            sql = select(TLotdyninfo).filter(TLotdyninfo.dynId == DynId).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    @lock_wrapper
    async def getAlldyid(self, ret_limit=10000) -> list[str]:
        async with self._session() as session:
            sql = select(TLotdyninfo.dynId).order_by(TLotdyninfo.dynId.desc()).limit(ret_limit)
            res = await session.execute(sql)
            ret_list = res.scalars().all()
            return ret_list

    @lock_wrapper
    async def getAllLotdyid(self, ret_limit=10000) -> list[str]:
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
        async with self._session() as session:
            await session.merge(DynInfo)
            await session.commit()

    @lock_wrapper
    async def getDynInfoByDynamicId(self, dynamic_id: int | str) -> TLotdyninfo | None:
        """
        直接把最新的动态信息merge进去
        :param dynamic_id:
        :return:
        """
        async with self._session() as session:
            sql = select(TLotdyninfo).filter(TLotdyninfo.dynId == dynamic_id).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()

            return ret

    # endregion

    # region LotUserInfo增删改查
    @lock_wrapper
    async def getLotUserInfoByUid(self, uid: int) -> Union[TLotuserinfo, None]:
        async with self._session() as session:
            sql = select(TLotuserinfo).filter(TLotuserinfo.uid == uid).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()

            return ret

    @lock_wrapper
    async def addLotUserInfo(self, LotUserInfo: TLotuserinfo):
        async with self._session() as session:
            await session.merge(LotUserInfo)
            await session.commit()
    # endregion

    # region 空间响应的增删改查
    @lock_wrapper
    async def getSpaceRespByRoundId(self, round_id: int | str) -> Sequence[TLotuserspaceresp]:
        """
        获取所有比offset值大的动态，也就是获取offset值之后发布的动态
        :param uid:
        :param offset:
        :return:
        """
        async with self._session() as session:
            sql = select(TLotuserspaceresp).filter(
                TLotuserspaceresp.dynLotRound_id == round_id
            ).order_by(TLotuserspaceresp.spaceOffset.desc())
            res = await session.execute(sql)
            ret= res.scalars().all()
            return ret

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
        async with self._session() as session:
            await session.merge(LotUserSpaceResp)
            await session.commit()
    @lock_wrapper
    async def getOldestSpaceDynInfoByUid(self, uid: int) -> int:
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
    async def getOldestSpaceOffsetByUidRoundId(self, uid: int, round_id: int) -> int:
        async with self._session() as session:
            sql = select(TLotuserspaceresp).filter(
                and_(
                    TLotuserspaceresp.spaceUid == uid,
                    TLotuserspaceresp.dynLotRound_id == round_id)).order_by(
                TLotuserspaceresp.spaceOffset.asc()).limit(1)
            res = await session.execute(sql)
            ret: TLotuserspaceresp = res.scalars().first()
            if ret:
                return ret.spaceOffset
            else:
                return 0

    @lock_wrapper
    async def get_lot_user_info_updatetime_by_uid(self, uid: Union[int, str]) -> Union[datetime, None]:
        async with self._session() as session:
            sql = select(TLotuserinfo.updatetime).filter(TLotuserinfo.uid == uid).order_by(
                TLotuserinfo.uid.desc()).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret

    # endregion

    @lock_wrapper
    async def isExistSpaceInfoByDynId(self, dynamic_id) -> Union[TLotuserspaceresp, None]:
        async with self._session() as session:
            sql = select(TLotuserspaceresp).filter(TLotuserspaceresp.spaceOffset == str(dynamic_id)).limit(1)
            res = await session.execute(sql)
            ret = res.scalars().first()
            return ret


get_other_lot_redis_manager = GetOtherLotRedisManager()

SqlHelper = __SqlHelper()


async def __test__():
    result = await SqlHelper.addDynInfo(TLotdyninfo(
        dynId=114514
    ))
    print(result)


if __name__ == '__main__':
    asyncio.run(__test__())
