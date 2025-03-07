import time
import asyncio
from typing import Union, List
from CONFIG import CONFIG
from fastapi接口.log.base_log import topic_lot_logger
from opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter, BaseStopCounter
from opus新版官方抽奖.活动抽奖.话题抽奖.SqlHelper import topic_sqlhelper
from opus新版官方抽奖.活动抽奖.话题抽奖.db.models import TClickAreaCard, TTopicCreator, TTopicItem, TTrafficCard, \
    TFunctionalCard, TTopDetails, TTopic, TCapsule
from utl.pushme.pushme import pushme
from utl.代理.request_with_proxy import request_with_proxy


class StopCounter(BaseStopCounter):
    def __init__(self):
        super().__init__(300)


class SuccCounter(BaseSuccCounter):
    first_topic_id = 0
    latest_succ_topic_id: int = 0  # 最后获取成功的话题id
    latest_topic_id: int = 0  # 最后获取的话题id，不管是否成功

    def __init__(self):
        super().__init__()


class TopicRobot:
    def __init__(self):
        self.start_topic_id = 1  # 开始的话题id
        self.min_sep_ts = 2 * 3600  # 最小的间隔时间
        self.baseurl = 'https://app.bilibili.com/x/topic/web/details/top'
        self.req = request_with_proxy()
        self.stop_counter = StopCounter()
        self.succ_counter = SuccCounter()
        self.__max_stop_times = 5  # 遇到超过时间的话题次数
        self._cur_stop_times: int = 0
        self.sql = topic_sqlhelper
        self.sem_limit = 10
        self.sem = asyncio.Semaphore(self.sem_limit)
        self._stop_counter = 0  # 连续遇到没有的就加1
        self._max_stop_count = 300
        self._max_stop_timestamp = 4 * 3600  # 距离当前时间超过12小时就停止
        self._latest_topic_id = 0
        self._traffic_card_lock = asyncio.Lock()  # 活动数据锁

    @property
    def cur_stop_times(self):
        return self._cur_stop_times

    @property
    def stop_flag(self) -> bool:
        if self._cur_stop_times >= self.__max_stop_times:
            return True
        else:
            return False

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
                                                 headers={'user-agent': CONFIG.rand_ua},
                                                 hybrid="1"
                                                 )
        return resp

    async def save_resp(self, topic_id: int, resp: dict, is_get_recent_failed_topic=False):
        """
       保存话题字典
        :param is_get_recent_failed_topic:
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
            self.succ_counter.latest_succ_topic_id = topic_id
            if topic_id > self._latest_topic_id:
                self._latest_topic_id = topic_id
                self.succ_counter.latest_topic_id = topic_id
                self._stop_counter = 0
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
                            self.stop_counter.cur_stop_continuous_num += 1
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
            if topic_id > self._latest_topic_id and not is_get_recent_failed_topic:
                self._stop_counter += 1
        return await self.sql.add_TTopic(
            tTopic,
            tTopicItem,
            tTopicCreator,
            tTopDetails,
            tFunctionalCard,
            tClickAreaCard,
            tTrafficCard,
            tCapsules
        )

    async def pipeline(self, topic_id, is_get_recent_failed_topic=False, use_sem=True):
        try:
            resp_dict = await self.scrapy_topic_dict(topic_id)
            self.succ_counter.succ_count += 1
            topic_lot_logger.debug(f'topic_id 【{topic_id}】 {resp_dict}')
            if self._stop_counter >= self._max_stop_count and not is_get_recent_failed_topic:
                self._cur_stop_times += 1
                self.stop_counter.cur_stop_continuous_num += 1
                topic_lot_logger.info('到达最大无效值，stop_times+1！')
            async with self._traffic_card_lock:
                await self.save_resp(topic_id, resp_dict, is_get_recent_failed_topic)
        except Exception as e:
            topic_lot_logger.exception(f'获取话题失败，topic_id:{topic_id}\n{e}')
            raise e
        if use_sem:
            self.sem.release()

    async def main(self, start_topic_id=0):
        # region 重新获取获取失败的数据
        try:
            self.succ_counter.is_running = True
            get_failed_topic_ids = await self.sql.get_recent_failed_topic_id(
                self._max_stop_count + self.sem_limit + 5000)
            _task_list = set()
            for i in get_failed_topic_ids:
                await self.sem.acquire()
                task = asyncio.create_task(self.pipeline(i, is_get_recent_failed_topic=True))
                _task_list.add(task)
                task.add_done_callback(_task_list.discard)
            await asyncio.gather(*_task_list)
            if start_topic_id:
                self.start_topic_id = start_topic_id
            else:
                self.start_topic_id = await self.sql.get_max_topic_id()
            # endregion
            topic_lot_logger.info(f'开始从{self.start_topic_id + 1}开始获取话题！')
            self.succ_counter.first_topic_id = self.start_topic_id + 1
            task_list = set()
            while not self.stop_flag:
                self.start_topic_id += 1
                await self.sem.acquire()
                task = asyncio.create_task(self.pipeline(self.start_topic_id),name=str(self.start_topic_id))
                task_list.add(task)
                task.add_done_callback(task_list.discard)
                while [i for i in task_list if int(i.get_name()) < self.start_topic_id - self.sem_limit]:
                    await asyncio.sleep(1)
                # await asyncio.gather(*last_sem_list)
            topic_lot_logger.info(f'获取完成！等待任务列表剩余【{len([x for x in task_list if not x.done()])}】个任务！')
            await asyncio.gather(*task_list)
        except Exception as e:
            topic_lot_logger.error(f'发生异常！{e}')
            pushme(title=f'爬取话题异常', content=str(e))
        finally:
            self.succ_counter.is_running = False


def run():
    a = TopicRobot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(a.main())


async def _test_get_topic_info():
    topic_id = 1258933
    _a = TopicRobot()
    await _a.pipeline(topic_id)


if __name__ == "__main__":
    asyncio.run(_test_get_topic_info())
