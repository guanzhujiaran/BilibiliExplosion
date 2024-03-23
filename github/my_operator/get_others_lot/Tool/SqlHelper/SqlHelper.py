import asyncio
import datetime
import json
import random
import traceback
from typing import Union

from loguru import logger
from sqlalchemy import AsyncAdaptedQueuePool, select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from github.my_operator.get_others_lot.Tool.SqlHelper.models import *

from CONFIG import CONFIG



def lock_wrapper(func: callable) -> callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                logger.critical(traceback.format_exc())
                logger.critical(f'{args} {kwargs}')
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


class SqlHelper:
    def __init__(self):
        SQLITE_URI = CONFIG.database.get_other_lotDb.DB_URI
        self.op_db_lock = asyncio.Lock()
        self._engine = create_async_engine(
            SQLITE_URI,
            echo=False,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=100,
            max_overflow=100,
            pool_recycle=3600,
            future=True,
            pool_pre_ping=True,

        )
        self._session = sessionmaker(self._engine,
                                     class_=AsyncSession,
                                     expire_on_commit=False,
                                     )

    # region 获取抽奖轮次信息相关
    @lock_wrapper
    async def getLatestRound(self) -> Union[TLotMainInfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotMainInfo).order_by(TLotMainInfo.lotRound.desc()).limit(1)
                res = await session.execute(sql)
                ret: TLotMainInfo = res.scalars().first()
                return ret

    @lock_wrapper
    async def addLotMainInfo(self, LotMainInfo: TLotMainInfo):
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotMainInfo).filter(TLotMainInfo.lotRound == LotMainInfo.lotRound)
                res = await session.execute(sql)
                ret: TLotMainInfo = res.scalars().first()
                if ret:
                    ret.lotRound = LotMainInfo.lotRound
                    ret.isRoundFinished = LotMainInfo.isRoundFinished
                    ret.lotNum = LotMainInfo.lotNum
                    ret.allNum = LotMainInfo.allNum
                    ret.uselessNum = LotMainInfo.uselessNum
                    await session.flush()
                    await session.commit()
                else:
                    session.add(LotMainInfo)
                    await session.commit()

    # endregion

    # region 抽奖动态相关
    @lock_wrapper
    async def getAllDynInfo(self) -> list[TLotDynInfo]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo).order_by(TLotDynInfo.dynId.desc())
                res = await session.execute(sql)
                ret = res.scalars().all()
                return ret

    @lock_wrapper
    async def getAllDynByLotRound(self, LotRound: int) -> list[TLotDynInfo]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo).filter(TLotDynInfo.dynLotRound == LotRound).order_by(TLotDynInfo.dynId.desc())
                res = await session.execute(sql)
                ret = res.scalars().all()
                return ret

    @lock_wrapper
    async def isExistDynInfoByDynId(self, DynId: str) -> Union[TLotDynInfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo).filter(TLotDynInfo.dynId == DynId).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()
                return ret

    @lock_wrapper
    async def getAlldyid(self, ret_limit=10000) -> list[str]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo.dynId).order_by(TLotDynInfo.dynId.desc()).limit(ret_limit)
                res = await session.execute(sql)
                ret_list = res.scalars().all()
                return ret_list

    @lock_wrapper
    async def getAllLotdyid(self, ret_limit=10000) -> list[str]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo.dynId).filter(TLotDynInfo.isLot == 1).order_by(TLotDynInfo.dynId.desc()).limit(
                    ret_limit)
                res = await session.execute(sql)
                ret_list = res.scalars().all()
                return ret_list

    @lock_wrapper
    async def addDynInfo(self, DynInfo: TLotDynInfo) -> None:
        """
        如果存在就是去更新，否则就是新增一个
        :param DynInfo:
        :return:
        """
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotDynInfo).filter(TLotDynInfo.dynId == DynInfo.dynId)
                res = await session.execute(sql)
                ret: TLotDynInfo = res.scalars().first()
                if ret:
                    ret.pubTime = DynInfo.pubTime
                    ret.dynContent = DynInfo.dynContent
                    ret.authorName = DynInfo.authorName
                    ret.commentCount = DynInfo.commentCount
                    ret.dynamicUrl = DynInfo.dynamicUrl
                    ret.dynLotRound = DynInfo.dynLotRound
                    ret.hashTag = DynInfo.hashTag
                    ret.highlightWords = DynInfo.highlightWords
                    ret.isFollowed = DynInfo.isFollowed
                    ret.isManualReply = DynInfo.isManualReply
                    ret.officialLotId = DynInfo.officialLotId
                    ret.officialLotType = DynInfo.officialLotType
                    ret.rawJsonStr = DynInfo.rawJsonStr
                    ret.repostCount = DynInfo.repostCount
                    ret.up_uid = DynInfo.up_uid
                    ret.isOfficialAccount = DynInfo.isOfficialAccount
                    ret.isLot = DynInfo.isLot
                    await session.flush()
                    await session.commit()
                else:
                    session.add(DynInfo)
                    await session.commit()

    # endregion

    # region LotUserInfo增删改查
    @lock_wrapper
    async def getLotUserInfoByUid(self, uid: int) -> Union[TLotUserInfo, None]:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserInfo).filter(TLotUserInfo.uid == uid).limit(1)
                res = await session.execute(sql)
                ret = res.scalars().first()

                return ret

    @lock_wrapper
    async def addLotUserInfo(self, LotUserInfo: TLotUserInfo):
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserInfo).filter(TLotUserInfo.uid == LotUserInfo.uid).limit(1)
                res = await session.execute(sql)
                ret: TLotUserInfo = res.scalars().first()
                if ret:
                    ret.offset = LotUserInfo.offset
                    ret.isUserSpaceFinished = LotUserInfo.isUserSpaceFinished
                    ret.uname = LotUserInfo.uname
                    ret.updateNum = LotUserInfo.updateNum
                    ret.updatetime = LotUserInfo.updatetime
                    ret.latestFinishedOffset = LotUserInfo.latestFinishedOffset
                    await session.flush()
                    await session.commit()
                else:
                    session.add(LotUserInfo)
                    await session.commit()

    # endregion
    # region 空间响应的增删改查
    @lock_wrapper
    async def getSpaceRespTillOffset(self, uid: int, offset: int) -> list[dict]:
        """
        获取所有比offset值大的动态，也就是获取offset值之后发布的动态
        :param uid:
        :param offset:
        :return:
        """
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserSpaceResp).filter(and_(
                    TLotUserSpaceResp.spaceUid == uid,
                    TLotUserSpaceResp.spaceOffset >= offset
                )).order_by(TLotUserSpaceResp.spaceOffset.desc())
                res = await session.execute(sql)
                ret: list[TLotUserSpaceResp] = res.scalars().all()
                return [json.loads(x.spaceRespJson) for x in ret]

    @lock_wrapper
    async def addSpaceResp(self, LotUserSpaceResp: TLotUserSpaceResp):
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserSpaceResp).filter(and_(TLotUserSpaceResp.spaceUid == LotUserSpaceResp.spaceUid,
                                                            TLotUserSpaceResp.spaceOffset == LotUserSpaceResp.spaceOffset)).limit(
                    1)
                res = await session.execute(sql)
                ret: TLotUserSpaceResp = res.scalars().first()
                if ret:
                    ret.spaceUid = LotUserSpaceResp.spaceUid
                    ret.spaceOffset = LotUserSpaceResp.spaceOffset
                    ret.spaceRespJson = LotUserSpaceResp.spaceRespJson
                    await session.flush()
                    await session.commit()
                else:
                    session.add(LotUserSpaceResp)
                    await session.commit()

    @lock_wrapper
    async def getOldestSpaceDynInfoByUid(self,uid:int)->int:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserSpaceResp).filter(TLotUserSpaceResp.spaceUid ==uid).order_by(TLotUserSpaceResp.spaceOffset.asc()).limit(1)
                res = await session.execute(sql)
                ret:TLotUserSpaceResp = res.scalars().first()
                if ret:
                    return ret.spaceOffset
                else:
                    return 0

    @lock_wrapper
    async def getNewestSpaceDynInfoByUid(self, uid: int) -> int:
        async with self.op_db_lock:
            async with self._session() as session:
                sql = select(TLotUserSpaceResp).filter(TLotUserSpaceResp.spaceUid == uid).order_by(
                    TLotUserSpaceResp.spaceOffset.desc()).limit(1)
                res = await session.execute(sql)
                ret:TLotUserSpaceResp = res.scalars().first()
                if ret:
                    return ret.spaceOffset
                else:
                    return 0
    # endregion


async def __test__():
    a = SqlHelper()

    result = await a.addDynInfo(
        TLotDynInfo(
            dynId=str(1),
            dynamicUrl=1,
            authorName=114514,
            up_uid=1,
            pubTime=datetime.datetime.fromtimestamp(1),
            dynContent=1,
            commentCount=1,
            repostCount=1,
            highlightWords=';',
            officialLotType=1,
            officialLotId=str(None),
            isOfficialAccount=int(1),
            isManualReply=1,
            isFollowed=int(bool(1)),
            isLot=1,
            hashTag='',
            dynLotRound=2,
            rawJsonStr='1'
        )
    )
    print(result)


if __name__ == '__main__':
    asyncio.run(__test__())
