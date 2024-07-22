import pydantic
import time

import sys

import asyncio

from typing import Union

import json

import random

from CONFIG import CONFIG
from opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import sqlHelper
from opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TClickAreaCard, TTopicCreator, TTopicItem, TTrafficCard, \
    TFunctionalCard, TTopDetails, TTopic
from utl.代理.request_with_proxy import request_with_proxy
from loguru import logger

# logger.remove()
log = logger.bind(user='topic_lottery')


# log.add(sys.stderr, level="DEBUG", filter=lambda record: record["extra"].get('user') == 'topic_lottery')
# logger.add(sys.stderr, level="ERROR", filter=lambda record: record["extra"].get('user') =="MYREQ")


class TopicRobot:
    def __init__(self):
        self.min_sep_ts = 2 * 3600  # 最小的间隔时间
        self.baseurl = 'https://app.bilibili.com/x/topic/web/details/top'
        self.req = request_with_proxy()
        self.stop_flag = False
        self.sql = sqlHelper()
        self.sem_limit = 40
        self.sem = asyncio.Semaphore(self.sem_limit)
        self._stop_counter = 0
        self._max_stop_count = 1000
        self._latest_topic_id = 0

    async def scrapy_topic_dict(self, topic_id: int) -> dict:
        """
        爬取话题字典
        :return:
        """
        params = {
            'topic_id': topic_id,
            'source': 'Web'
        }
        resp = await self.req.request_with_proxy(url=self.baseurl, method='get', params=params,
                                                 headers={'user-agent': random.choice(CONFIG.UA_LIST)}
                                                 )
        return resp

    async def save_resp(self, topic_id: int, resp: dict):
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

        if resp.get('code') == 0:
            if topic_id > self._latest_topic_id:
                self._latest_topic_id = topic_id
                self._stop_counter = 0
            da = resp.get('data')
            top_details = da.get('top_details')
            if top_details:
                topic_creator = top_details.get('topic_creator')
                if topic_creator:
                    allowed_keys = TTopicCreator.__table__.columns.keys()
                    filtered_topic_creator = {key: value for key, value in topic_creator.items() if key in allowed_keys}
                    tTopicCreator = TTopicCreator(**filtered_topic_creator)
                topic_item = top_details.get('topic_item')
                if topic_item:
                    allowed_keys = TTopicItem.__table__.columns.keys()
                    filtered_topic_item = {key: value for key, value in topic_item.items() if key in allowed_keys}
                    tTopicItem = TTopicItem(**filtered_topic_item)
                    if type(topic_item.get('ctime')) is int:
                        if int(time.time()) - topic_item.get('ctime') <= self.min_sep_ts:
                            self.stop_flag = True
                            log.info('到达最近时间，退出')
                tTopDetails = TTopDetails(
                    close_pub_layer_entry=top_details.get('close_pub_layer_entry'),
                    has_create_jurisdiction=top_details.get('has_create_jurisdiction'),
                    operation_content=top_details.get('operation_content'),
                    word_color=top_details.get('word_color'),
                )
            functional_card = da.get('functional_card')
            if functional_card:

                tFunctionalCard = TFunctionalCard(
                    json_data=functional_card
                )
                traffic_card = functional_card.get('traffic_card')
                if traffic_card:
                    allowed_keys = TTrafficCard.__table__.columns.keys()
                    filtered_traffic_card = {key: value for key, value in traffic_card.items() if key in allowed_keys}
                    tTrafficCard = TTrafficCard(**filtered_traffic_card)
            click_area_card = da.get('click_area_card')
            if click_area_card:
                tClickAreaCard = TClickAreaCard(json_data=click_area_card)
        else:
            if topic_id > self._latest_topic_id:
                self._stop_counter += 1

        return await self.sql.add_TTopic(
            tTopic,
            tTopicItem,
            tTopicCreator,
            tTopDetails,
            tFunctionalCard,
            tClickAreaCard,
            tTrafficCard
        )

    async def pipeline(self, topic_id):
        resp_dict = await self.scrapy_topic_dict(topic_id)
        log.debug(f'topic_id 【{topic_id}】 {resp_dict}')
        if self._stop_counter >= self._max_stop_count:
            self.stop_flag = True
            log.info('到达最大无效值，退出！')
        await self.save_resp(topic_id, resp_dict)
        self.sem.release()

    async def main(self):
        get_failed_topic_ids = await self.sql.get_recent_failed_topic_id(self._max_stop_count)
        task_list = set()
        for i in get_failed_topic_ids:
            await self.sem.acquire()
            task = asyncio.create_task(self.pipeline(i))
            task_list.add(task)
            task.add_done_callback(task_list.discard)
        self.start_topic_id = await self.sql.get_max_topic_id()
        log.info(f'开始从{self.start_topic_id + 1}开始获取话题！')
        task_list = set()
        while not self.stop_flag:
            self.start_topic_id += 1
            await self.sem.acquire()
            task = asyncio.create_task(self.pipeline(self.start_topic_id))
            task.set_name(str(self.start_topic_id))
            task_list.add(task)
            task.add_done_callback(task_list.discard)
            last_sem_list = [i for i in task_list if int(i.get_name()) < self.start_topic_id - self.sem_limit]
            await asyncio.gather(*last_sem_list)
        await asyncio.gather(*task_list)


def run():
    a = TopicRobot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(a.main())


if __name__ == "__main__":
    run()
