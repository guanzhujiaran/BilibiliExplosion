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

logger.remove()
log = logger.bind(user='topic_lottery')
log.add(sys.stderr, level="DEBUG", filter=lambda record: record["extra"].get('user') == 'topic_lottery')


class TopicRobot:
    def __init__(self):
        self.min_sep_ts = 2 * 3600  # 最小的间隔时间
        self.baseurl = 'https://app.bilibili.com/x/topic/web/details/top'
        self.req = request_with_proxy()
        self.stop_flag = False
        self.sql = sqlHelper()
        self.sem = asyncio.Semaphore(40)
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
                                                 headers={'user-agent': random.choice(CONFIG.UA_LIST)})
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
                    tTopicCreator = TTopicCreator(**topic_creator)
                topic_item = top_details.get('topic_item')
                if topic_item:
                    tTopicItem = TTopicItem(**topic_item)
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
                    tTrafficCard = TTrafficCard(**traffic_card)
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
        log.debug(f'topic_id{topic_id}:{resp_dict}')
        if self._stop_counter >= self._max_stop_count:
            self.stop_flag = True
            log.info('到达最大无效值，退出！')
        await self.save_resp(topic_id, resp_dict)
        self.sem.release()

    async def main(self):
        self.start_topic_id = await self.sql.get_max_topic_id()
        log.info(f'开始从{self.start_topic_id + 1}开始获取话题！')
        task_list=[]
        while not self.stop_flag:
            self.start_topic_id += 1
            await self.sem.acquire()
            task = asyncio.create_task(self.pipeline(self.start_topic_id))
            task_list.append(task)
            task_list = [i for i in task_list if not i.done()]
        await asyncio.gather(*task_list)
async def test():
    a = TopicRobot()
    resp1 = """{
  "code": 0,
  "message": "0",
  "ttl": 1,
  "data": {
    "top_details": {
      "topic_item": {
        "id": 8995,
        "name": "寒假不咕咕",
        "view": 488338287,
        "discuss": 642172,
        "fav": 45,
        "dynamics": 38483,
        "jump_url": "https://m.bilibili.com/topic-detail?topic_id=8995",
        "back_color": "#6188FF",
        "description": "寒假不做鸽子精，这次一定！分享寒假日常就从现在开始",
        "share_pic": "http://i0.hdslb.com/bfs/vc/7701fba940e721ceb756cc73694ebb8f510fe0cc.png",
        "share": 1,
        "like": 136,
        "share_url": "https://m.bilibili.com/topic-detail?topic_id=8995",
        "ctime": 1641380305
      },
      "topic_creator": {
        "uid": 32708726,
        "face": "https://i2.hdslb.com/bfs/face/92c24db539b6531277aae69c422fded520f758ac.jpg",
        "name": "傲娇的时尚喵"
      },
      "operation_content": {},
      "has_create_jurisdiction": true,
      "word_color": 0,
      "close_pub_layer_entry": false
    },
    "functional_card": {},
    "click_area_card": {}
  }
}"""
    resp_dict1 = json.loads(resp1)
    resp2 = """{
      "code": 0,
      "message": "0",
      "ttl": 1,
      "data": {
        "top_details": {
          "topic_item": {
            "id": 9000,
            "name": "红红火火穿搭指南",
            "view": 236251827,
            "discuss": 282841,
            "fav": 76,
            "dynamics": 5989,
            "jump_url": "https://m.bilibili.com/topic-detail?topic_id=9000",
            "back_color": "#6188FF",
            "description": "新年焕新衣当然要整起来！拜年穿搭、新年断舍离、2022大改造、年度单品...这里应有尽有",
            "share_pic": "http://i0.hdslb.com/bfs/vc/7701fba940e721ceb756cc73694ebb8f510fe0cc.png",
            "share": 3,
            "like": 52,
            "share_url": "https://m.bilibili.com/topic-detail?topic_id=9000",
            "ctime": 1641382505
          },
          "topic_creator": {
            "uid": 32708726,
            "face": "https://i2.hdslb.com/bfs/face/92c24db539b6531277aae69c422fded520f758ac.jpg",
            "name": "傲娇的时尚喵"
          },
          "operation_content": {},
          "has_create_jurisdiction": true,
          "word_color": 0,
          "close_pub_layer_entry": false
        },
        "functional_card": {
          "traffic_card": {
            "name": "红红火火穿搭指南",
            "jump_url": "https://www.bilibili.com/blackboard/dynamic/170580",
            "icon_url": "https://i0.hdslb.com/bfs/activity-plat/static/20211019/4c5b6134e2def772efe20dabcca1f6e1/vGqnSBjy8N.png",
            "benefit_point": "有奖征稿",
            "card_desc": "活动已结束",
            "jump_title": "立即参加"
          }
        },
        "click_area_card": {}
      }
    }"""
    resp_dict2 = json.loads(resp2)
    resp3 = """{
  "code": 4401031,
  "message": "话题不存在",
  "ttl": 1,
  "data": null
}"""
    resp_dict3 = json.loads(resp3)
    await a.save_resp(9000, resp_dict3)
    await a.save_resp(8995, resp_dict1)
    await a.save_resp(9000, resp_dict2)


def run():
    a = TopicRobot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(a.main())


if __name__ == "__main__":
    run()
