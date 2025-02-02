import json
from typing import Union, List, Sequence
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from CONFIG import CONFIG
from sqlalchemy.sql.expression import text
from sqlalchemy import select, update, func, and_, cast, DateTime, AsyncAdaptedQueuePool
from sqlalchemy.orm import joinedload

from fastapi接口.log.base_log import topic_lot_logger
from opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TClickAreaCard, TTopicCreator, TTopicItem, \
    TFunctionalCard, TTopDetails, TTopic, TCapsule
from opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TTrafficCard, TActivityLottery, TActivityMatchLottery, \
    TActivityMatchTask, TEraJika, TEraLottery, TEraTask, TEraVideo

log = topic_lot_logger


def lock_wrapper(__func):
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                return await __func(*args, **kwargs)
            except Exception as e:
                log.exception(e)
                await asyncio.sleep(3)

    return wrapper


class SqlHelper:
    def __init__(self):
        _SQLURI = CONFIG.database.MYSQL.bili_db_URI

        self._engine = create_async_engine(
            _SQLURI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self._session = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    # region a基础查询功能
    @lock_wrapper
    async def get_TTopic_by_topic_id(self, topic_id: str | int):
        async with self._session() as session:
            sql = select(TTopic).where(topic_id == TTopic.topic_id).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @lock_wrapper
    async def add_TTopic(self,
                         tTopic: TTopic,
                         tTopicItem: TTopicItem,
                         tTopicCreator: TTopicCreator,
                         tTopDetails: TTopDetails,
                         tFunctionalCard: TFunctionalCard,
                         tClickAreaCard: TClickAreaCard,
                         tTrafficCard: TTrafficCard,
                         tCapsules: List[TCapsule]
                         ):
        if tFunctionalCard and tTrafficCard:
            existed_functional_card = await self.get_functional_card_by_jump_url(tTrafficCard.jump_url)
            if not existed_functional_card:
                tFunctionalCard.traffic_card = tTrafficCard
                tTopic.functional_card = tFunctionalCard
            else:
                tTopic.functional_card = existed_functional_card
        if tFunctionalCard and tCapsules:
            tFunctionalCard.t_capsule = tCapsules
            tTopic.functional_card = tFunctionalCard

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
        limit = 2
        offset = 0
        async with self._session() as session:
            while 1:
                sql = select(TTopic.topic_id).filter(TTopic.topic_detail_id.isnot(None)).order_by(
                    TTopic.topic_id.desc()).limit(
                    limit).offset(offset)
                result = await session.execute(sql)
                data = result.scalars().all()
                if not data or len(data) < limit:
                    return 1000
                if data[0] - data[1] == 1:
                    return data[0]
                offset += 1

    @lock_wrapper
    async def get_capsules_by_jump_urls(self, jump_urls) -> Sequence[TCapsule]:
        async with self._session() as session:
            sql = select(TCapsule).filter(TTrafficCard.jump_url.in_(jump_urls)).order_by(
                TCapsule.pk.desc())
            result = await session.execute(sql)
            data = result.scalars().all()
            return data

    @lock_wrapper
    async def get_functional_card_by_jump_url(self, jump_url: str) -> Union[TFunctionalCard, None]:
        async with self._session() as session:
            sql = select(TFunctionalCard).join(TTrafficCard).filter(jump_url == TTrafficCard.jump_url).order_by(
                TFunctionalCard.id.desc()).limit(
                1)
            result = await session.execute(sql)
            data = result.scalars().first()
            return data

    @lock_wrapper
    async def get_recent_failed_topic_id(self, limit=1000) -> Sequence[int]:
        last_topic_with_detail_subquery = select(func.max(TTopic.topic_id)).where(
            TTopic.topic_detail_id.isnot(None)).scalar_subquery()
        sql = (select(TTopic.topic_id).where(
            and_(
                TTopic.topic_detail_id.is_(None),
                TTopic.topic_id < last_topic_with_detail_subquery
            )
        ).order_by(TTopic.topic_id.desc()).limit(limit))
        async with self._session() as session:
            result = await session.execute(sql)
            data = result.scalars().all()
            return data

    # endregion

    # region b查询抽奖信息功能
    @lock_wrapper
    async def get_all_available_traffic_info_by_page(self, page_num: int = 0, page_size: int = 0) -> tuple[
        Sequence[TTrafficCard], int]:
        sql = select(TTrafficCard).where(
            cast(func.date_format(TTrafficCard.card_desc, text("'%Y-%m-%d %H:%i:00截止'")), DateTime) > func.now()
        ).order_by(
            cast(func.date_format(TTrafficCard.card_desc, text("'%Y-%m-%d %H:%i:00截止'")), DateTime).asc()
        ).options(
            joinedload(TTrafficCard.t_activity_lottery),
            joinedload(TTrafficCard.t_activity_match_lottery),
            joinedload(TTrafficCard.t_activity_match_task),
            joinedload(TTrafficCard.t_era_jika),
            joinedload(TTrafficCard.t_era_lottery),
            joinedload(TTrafficCard.t_era_task),
            joinedload(TTrafficCard.t_era_video),
        )
        if page_num and page_size:
            offset_value = (page_num - 1) * page_size
            sql = sql.offset(offset_value).limit(page_size)
        count_sql = select(func.count(TTrafficCard.id)).where(
            cast(func.date_format(TTrafficCard.card_desc, text("'%Y-%m-%d %H:%i:00截止'")), DateTime) > func.now()
        )
        async with (self._session() as session):
            result = await session.execute(sql)
            data = result.scalars().unique().all()
            count_result = await session.execute(count_sql)
        return data, count_result.scalars().first()

    @lock_wrapper
    async def get_all_available_traffic_info(self) -> List[TTrafficCard]:
        async with (self._session() as session):
            sql = select(TTrafficCard).where(
                func.now() < func.date_format(TTrafficCard.card_desc, '%Y-%m-%d %H:%i截止')).order_by(
                TTrafficCard.id.desc()).options(
                joinedload(TTrafficCard.t_activity_lottery),
                joinedload(TTrafficCard.t_activity_match_lottery),
                joinedload(TTrafficCard.t_activity_match_task),
                joinedload(TTrafficCard.t_era_jika),
                joinedload(TTrafficCard.t_era_lottery),
                joinedload(TTrafficCard.t_era_task),
                joinedload(TTrafficCard.t_era_video),
            )
            result = await session.execute(sql)
            data = result.scalars().unique().all()
        return data

    @lock_wrapper
    async def get_all_available_traffic_info_by_status(self, status: Union[int, None]) -> Sequence[TTrafficCard]:
        async with (self._session() as session):
            sql = select(TTrafficCard).where(
                and_(
                    func.date_format(TTrafficCard.card_desc, '%Y-%m-%d %H:%i截止') > func.now()),
                status == TTrafficCard.my_activity_status
            ).order_by(
                TTrafficCard.id.desc())
            result = await session.execute(sql)
            data = result.scalars().all()
        return data

    @lock_wrapper
    async def update_traffic_card_status(self, stat: int, traffic_card_id: int):
        """

        :param stat:
        0：已成功查询
        1：未查询活动
        2：查询了，但获取到的活动为空
        3：查询出错了，去日志里查原因
        :param traffic_card_id:
        :return:
        """
        async with self._session() as session:
            sql = update(TTrafficCard).where(TTrafficCard.id == traffic_card_id).values(my_activity_status=stat)
            result = await session.execute(sql)

    @lock_wrapper
    async def add_activity_lottery(self, traffic_card_id, lotteryId: str, continueTimes, _list):
        async with self._session() as session:
            async with session.begin():
                activity_lottery = TActivityLottery(traffic_card_id=traffic_card_id, lotteryId=lotteryId,
                                                    continueTimes=continueTimes, list=_list)
                await session.merge(activity_lottery)

    @lock_wrapper
    async def add_activity_match_lottery(self, traffic_card_id, lottery_id: str, activity_id: str):
        async with self._session() as session:
            async with session.begin():
                activity_match_lottery = TActivityMatchLottery(traffic_card_id=traffic_card_id, lottery_id=lottery_id,
                                                               activity_id=activity_id)
                await session.merge(activity_match_lottery)

    @lock_wrapper
    async def add_activity_match_task(self, traffic_card_id, task_desc: str, interact_type, task_group_id,
                                      task_name: str, url: str):
        async with self._session() as session:
            async with session.begin():
                activity_match_task = TActivityMatchTask(
                    traffic_card_id=traffic_card_id,
                    task_desc=task_desc,
                    interact_type=interact_type,
                    task_group_id=task_group_id,
                    task_name=task_name,
                    url=url
                )
                await session.merge(activity_match_task)

    @lock_wrapper
    async def add_era_jika(self, traffic_card_id, activityUrl: str, jikaId: str, topId: int, topName: str):
        async with self._session() as session:
            async with session.begin():
                era_jika = TEraJika(
                    traffic_card_id=traffic_card_id,
                    activityUrl=activityUrl,
                    jikaId=jikaId,
                    topId=topId,
                    topName=topName,
                )
                await session.merge(era_jika)

    @lock_wrapper
    async def add_era_lottery(self, traffic_card_id, activity_id, gifts, icon, lottery_id, lottery_type, per_time,
                              point_name):
        async with self._session() as session:
            async with session.begin():
                era_lottery = TEraLottery(
                    traffic_card_id=traffic_card_id,
                    activity_id=activity_id,
                    gifts=gifts,
                    icon=icon,
                    lottery_id=lottery_id,
                    lottery_type=lottery_type,
                    per_time=per_time,
                    point_name=point_name
                )
                await session.merge(era_lottery)

    @lock_wrapper
    async def add_era_task(self, traffic_card_id, awardName, taskDes, taskId, taskName, taskType, topicID, topicName):
        async with self._session() as session:
            async with session.begin():
                era_task = TEraTask(
                    traffic_card_id=traffic_card_id,
                    awardName=awardName,
                    taskDes=taskDes,
                    taskId=taskId,
                    taskName=taskName,
                    taskType=taskType,
                    topicID=topicID,
                    topicName=topicName
                )
                await session.merge(era_task)

    @lock_wrapper
    async def add_era_video(self, traffic_card_id, poolList, topic_id, topic_name, videoSource_id):
        async with self._session() as session:
            async with session.begin():
                era_video = TEraVideo(
                    traffic_card_id=traffic_card_id,
                    poolList=poolList,
                    topic_id=topic_id,
                    topic_name=topic_name,
                    videoSource_id=videoSource_id,
                )
                await session.merge(era_video)
    # endregion


topic_sqlhelper = SqlHelper()


async def _test():
    b = await topic_sqlhelper.get_recent_failed_topic_id()
    print(b)


if __name__ == '__main__':
    asyncio.run(_test())
