import asyncio
import time
from typing import Union, List, AsyncGenerator

from fastapi接口.log.base_log import topic_lot_logger
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin, SequentialNullStopPlugin
from fastapi接口.service.grpc_module.grpc.bapi import biliapi
from fastapi接口.service.opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter
from fastapi接口.service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import ExtractTopicLottery
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import topic_sqlhelper
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TClickAreaCard, TTopicCreator, TTopicItem, \
    TTrafficCard, \
    TFunctionalCard, TTopDetails, TTopic, TCapsule
from utl.pushme.pushme import pushme


class SuccCounter(BaseSuccCounter):
    first_topic_id = 0
    latest_succ_topic_id: int = 0  # 最后获取成功的话题id
    latest_topic_id: int = 0  # 最后获取的话题id，不管是否成功

    def __init__(self):
        super().__init__()


class TopicRobot(UnlimitedCrawler[int]):
    async def is_stop(self) -> bool:
        return self._cur_stop_times >= self.__max_stop_times

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        if self.has_get_failed_topic_ids:
            while 1:
                yield params
                params += 1
        else:
            for i in self.get_failed_topic_ids:
                yield i
            return

    async def handle_fetch(self, params: int) -> WorkerStatus:
        return await self.pipeline(params)

    def __init__(self):
        self.sem_limit = 1
        self.start_topic_id = 1  # 开始的话题id
        self.min_sep_ts = 2 * 3600  # 最小的间隔时间
        self.__max_stop_times = 5  # 遇到超过时间的话题次数
        self._cur_stop_times: int = 0
        self._max_stop_count = 50
        self.sql = topic_sqlhelper
        self._latest_topic_id = 0
        self._traffic_card_lock = asyncio.Lock()  # 活动数据锁
        self.stats_plugin = StatsPlugin(self)
        self.null_counter_plugin = SequentialNullStopPlugin(self, max_consecutive_nulls=self._max_stop_count)
        super().__init__(
            max_sem=self.sem_limit,
            _logger=topic_lot_logger,
            plugins=[self.stats_plugin, self.null_counter_plugin],
        )

        self.has_get_failed_topic_ids = False
        self.get_failed_topic_ids = []

    @property
    def cur_stop_times(self):
        return self._cur_stop_times

    async def save_resp(self, topic_id: int, resp: dict) -> WorkerStatus:
        """
       保存话题字典
       :param topic_id:
       :param resp:
       :return:
       """
        tTopic: TTopic = TTopic(topic_id=topic_id, raw_JSON=resp)
        tTopicItem: Union[TTopicItem, None] = None
        tTopicCreator: Union[TTopicCreator, None] = None
        tTopDetails: Union[TTopDetails, None] = None
        tFunctionalCard: Union[TFunctionalCard, None] = None
        tClickAreaCard: Union[TClickAreaCard, None] = None
        tTrafficCard: Union[TTrafficCard, None] = None
        tCapsules: Union[List[TCapsule], None] = None
        if resp.get('code') == 0:
            if topic_id > self._latest_topic_id:
                self._latest_topic_id = topic_id
            da = resp.get('data')
            da_common_keys = ['click_area_card', 'functional_card', 'top_details']
            if extra_info := set(da_common_keys) & set(da.keys()) ^ set(da.keys()):
                topic_lot_logger.error(
                    f'data字段不匹配，topic_id:{topic_id}\ndata:{da}\n不匹配字段：{extra_info}')
            top_details = da.get('top_details')
            if top_details:
                allowed_keys = TTopDetails.__table__.columns.keys()
                allowed_keys.extend(['topic_item', 'topic_creator', 'operation_content'])
                if extra_info := set(allowed_keys) & set(top_details.keys()) ^ set(top_details.keys()):
                    topic_lot_logger.error(
                        f'top_details字段不匹配，topic_id:{topic_id}\ntop_details:{top_details}\n不匹配字段：{extra_info}')
                topic_creator = top_details.get('topic_creator')
                if topic_creator:
                    allowed_keys = TTopicCreator.__table__.columns.keys()
                    if extra_info := set(allowed_keys) & set(topic_creator.keys()) ^ set(topic_creator.keys()):
                        topic_lot_logger.error(
                            f'topic_creator字段不匹配，topic_id:{topic_id}\ntopic_creator:{topic_creator}\n不匹配字段：{extra_info}')
                    filtered_topic_creator = {key: value for key, value in topic_creator.items() if key in allowed_keys}
                    tTopicCreator = TTopicCreator(**filtered_topic_creator)
                topic_item = top_details.get('topic_item')
                if topic_item:
                    allowed_keys = TTopicItem.__table__.columns.keys()
                    if extra_info := set(allowed_keys) & set(topic_item.keys()) ^ set(topic_item.keys()):
                        topic_lot_logger.error(
                            f'topic_item字段不匹配，topic_id:{topic_id}\ntopic_item:{topic_item}\n不匹配字段：{extra_info}')
                    filtered_topic_item = {key: value for key, value in topic_item.items() if key in allowed_keys}
                    tTopicItem = TTopicItem(**filtered_topic_item)
                    if type(topic_item.get('ctime')) is int:
                        if int(time.time()) - topic_item.get('ctime') <= self.min_sep_ts:
                            self._cur_stop_times += 1
                            topic_lot_logger.info('到达最近时间，stop_times+=1！')
                tTopDetails = TTopDetails(
                    close_pub_layer_entry=top_details.get('close_pub_layer_entry'),
                    has_create_jurisdiction=top_details.get('has_create_jurisdiction'),
                    operation_content=top_details.get('operation_content'),
                    word_color=top_details.get('word_color'),
                )
            functional_card = da.get('functional_card')
            if functional_card:
                allowed_keys = TFunctionalCard.__table__.columns.keys()
                allowed_keys.extend(['traffic_card', 'capsules'])
                if extra_info := set(allowed_keys) & set(functional_card.keys()) ^ set(functional_card.keys()):
                    topic_lot_logger.error(
                        f'functional_card字段不匹配，topic_id:{topic_id}\nfunctional_card:{functional_card}\n不匹配字段：{extra_info}')
                tFunctionalCard = TFunctionalCard(
                    json_data=functional_card
                )
                traffic_card = functional_card.get('traffic_card')
                if traffic_card:
                    allowed_keys = TTrafficCard.__table__.columns.keys()
                    if extra_info := set(allowed_keys) & set(traffic_card.keys()) ^ set(traffic_card.keys()):
                        topic_lot_logger.error(
                            f'traffic_card字段不匹配，topic_id:{topic_id}\ntraffic_card:{traffic_card}\n不匹配字段：{extra_info}')
                    filtered_traffic_card = {key: value for key, value in traffic_card.items() if key in allowed_keys}
                    tTrafficCard = TTrafficCard(**filtered_traffic_card)

                capsules = functional_card.get('capsules')
                if capsules:
                    allowed_keys = TCapsule.__table__.columns.keys()
                    tCapsules = []
                    for capsule in capsules:
                        if extra_info := set(allowed_keys) & set(capsule.keys()) ^ set(capsule.keys()):
                            topic_lot_logger.error(
                                f'capsules字段不匹配，topic_id:{topic_id}\ncapsule:{capsule}\n不匹配字段：{extra_info}')
                        tCapsules.append(TCapsule(**capsule))
            click_area_card = da.get('click_area_card')
            if click_area_card:
                tClickAreaCard = TClickAreaCard(json_data=click_area_card)
        else:
            return WorkerStatus.nullData
        await self.sql.add_TTopic(
            tTopic,
            tTopicItem,
            tTopicCreator,
            tTopDetails,
            tFunctionalCard,
            tClickAreaCard,
            tTrafficCard,
            tCapsules
        )
        return WorkerStatus.complete

    async def pipeline(self, topic_id) -> WorkerStatus:
        try:
            resp_dict = await biliapi.get_web_topic(topic_id, use_custom_proxy=True)
            topic_lot_logger.debug(f'topic_id 【{topic_id}】 {resp_dict}')
            async with self._traffic_card_lock:
                return await self.save_resp(topic_id, resp_dict)
        except Exception as e:
            topic_lot_logger.exception(f'获取话题失败，topic_id:{topic_id}\n{e}')
            raise e

    async def main(self, start_topic_id=0):
        try:
            self.get_failed_topic_ids = await self.sql.get_recent_failed_topic_id(
                self._max_stop_count + self.sem_limit + 5000)
            await self.run(self.get_failed_topic_ids[0])

            self.has_get_failed_topic_ids = True  # 获取失败的话题完成
            self._cur_stop_times = 0
            if start_topic_id:
                self.start_topic_id = start_topic_id
            else:
                self.start_topic_id = await self.sql.get_max_topic_id()
            await self.run(self.start_topic_id)
            e = ExtractTopicLottery()
            await e.main()
        except Exception as e:
            topic_lot_logger.error(f'发生异常！{e}')
            pushme(title=f'爬取话题异常', content=str(e))



topic_robot = TopicRobot()

if __name__ == "__main__":
    a = TopicRobot()
    asyncio.run(a.main())
