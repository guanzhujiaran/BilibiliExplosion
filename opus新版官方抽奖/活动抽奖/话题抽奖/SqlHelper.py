from typing import Callable, Union
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from opus新版官方抽奖.活动抽奖.log.base_log import  topic_lot_log as log
import CONFIG
from opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TClickAreaCard, TTopicCreator, TTopicItem, TTrafficCard, \
    TFunctionalCard, TTopDetails, TTopic



def lock_wrapper(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.exception(e)
                await asyncio.sleep(3)

    return wrapper


class sqlHelper:
    def __init__(self):
        _SQLURI = CONFIG.MYSQL.bili_db_URI

        self._engine = create_async_engine(_SQLURI)
        self._session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @lock_wrapper
    async def add_TTopic(self, tTopic: TTopic,
                         tTopicItem: TTopicItem,
                         tTopicCreator: TTopicCreator,
                         tTopDetails: TTopDetails,
                         tFunctionalCard: TFunctionalCard,
                         tClickAreaCard: TClickAreaCard,
                         tTrafficCard: TTrafficCard):
        if tFunctionalCard:
            existed_functional_card = await self.get_functional_card_by_jump_url(tTrafficCard.jump_url)
            if not existed_functional_card:
                tFunctionalCard.traffic_card = tTrafficCard
                tTopic.functional_card = tFunctionalCard
            else:
                tTopic.functional_card = existed_functional_card
        async with self._session() as session:
            async with session.begin():
                tTopic.click_area_card = tClickAreaCard
                if tTopDetails:
                    tTopDetails.topic_creator = tTopicCreator
                    tTopDetails.topic_item = tTopicItem
                    tTopic.topic_detail = tTopDetails
                await session.merge(tTopic)

    @lock_wrapper
    async def get_max_topic_id(self) -> int:
        async with self._session() as session:
            sql = select(TTopic.topic_id).filter(TTopic.topic_detail_id != None).order_by(TTopic.topic_id.desc()).limit(
                1)
            result = await session.execute(sql)
            data = result.scalars().first()
            if not data:
                return 1000
            return data

    @lock_wrapper
    async def get_functional_card_by_jump_url(self, jump_url: str) -> Union[TFunctionalCard, None]:
        async with self._session() as session:
            sql = select(TFunctionalCard).join(TTrafficCard).filter(TTrafficCard.jump_url == jump_url).order_by(
                TFunctionalCard.id.desc()).limit(
                1)
            result = await session.execute(sql)
            data = result.scalars().first()
            return data

    @lock_wrapper
    async def get_recent_failed_topic_id(self, limit=1000) -> list[int]:
        async with self._session() as session:
            sql = select(TTopic.topic_id).filter(TTopic.topic_detail_id == None).order_by(TTopic.topic_id.desc()).limit(
                limit)
            result = await session.execute(sql)
            data = result.scalars().all()
            return data


async def _test():
    a = sqlHelper()
    b = await a.get_functional_card_by_jump_url("https://www.bilibili.com/blackboard/era/WGzl8l4LJUO1cA4y.html")
    print(b.dict())


if __name__ == '__main__':
    asyncio.run(_test())
