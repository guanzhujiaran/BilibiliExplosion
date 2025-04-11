# -*- coding: utf-8 -*-
import os.path
import traceback
from typing import Union
import asyncio
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi接口.log.base_log import topic_lot_logger
from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import ExtractTopicLottery
from opus新版官方抽奖.活动抽奖.话题抽奖.robot import TopicRobot
from utl.pushme.pushme import pushme, pushme_try_catch_decorator, async_pushme_try_catch_decorator
from apscheduler.schedulers.blocking import BlockingScheduler

log = topic_lot_logger

topic_robot: TopicRobot | None = None


class pubArticleInfo(CustomBaseModel):
    lastPubDate: Union[datetime, None] = None
    shouldPubHour: int = 20  # 每天发布的专栏的事件
    start_ts: int = int(time.time())

    def __init__(self):
        super().__init__()
        setting_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log/')
        if not os.path.exists(setting_path):
            os.mkdir(setting_path)
        try:
            with open(os.path.join(setting_path, 'lastPubTs.txt'), 'r', encoding='utf-8') as f:
                contents = f.read().strip()
                self.lastPubDate = datetime.fromtimestamp(int(contents))
                log.info(f"获取到上一次发布专栏的时间是：{self.lastPubDate.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            log.warning(f"获取到上一次发布专栏的时间失败！使用0时间！")
            self.lastPubDate = datetime.fromtimestamp(86400)

    def save_lastPubTs(self):
        try:
            now = datetime.now()
            self.lastPubDate = now
            setting_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log/')
            if not os.path.exists(setting_path):
                os.mkdir(setting_path)
            with open(os.path.join(setting_path, 'lastPubTs.txt'), 'w', encoding='utf-8') as f:
                f.write(str(int(self.lastPubDate.timestamp())))
        except Exception as e:
            log.exception(e)

    def is_need_to_publish(self):
        if self.lastPubDate:
            now = datetime.now()
            if self.lastPubDate.day != now.day:  # 上次发布日期不在同一天
                # if now.hour >= self.shouldPubHour or now.timestamp() - self.lastPubDate.timestamp() >= 15 * 3600:  # 如果当前时间在20点之后或者距离上次发布超过了15小时，则直接发布
                if now.timestamp() - self.lastPubDate.timestamp() >= 2 * 3600:
                    log.error(f'满足发布专栏文章条件，发布专栏！\t上次发布时间：{self.lastPubDate}')
                    return True
            else:  # 上次发布日期在同一天
                if now.timestamp() - self.lastPubDate.timestamp() >= 24 * 3600:  # 同一天只要满足超过24小时，就直接发布
                    log.error(f'满足发布专栏文章条件，发布专栏！\t上次发布时间：{self.lastPubDate}')
                    return True
        else:
            now = datetime.now()
            self.lastPubDate = now - timedelta(days=1)
        log.error(f'不满足发布专栏文章条件，不发布专栏！\t上次发布时间：{self.lastPubDate}')
        return False


@async_pushme_try_catch_decorator
async def main(pub_article_info: pubArticleInfo, schedule_mark: bool):
    '''
    :param pub_article_info:
    :param schedule_mark:
    :return:
    '''
    global topic_robot
    topic_robot = TopicRobot()
    if time.time() - pub_article_info.lastPubDate.timestamp() > 1 * 24 * 3600:
        topic_robot.sem = asyncio.Semaphore(30)
    else:
        topic_robot.sem = asyncio.Semaphore(15)
    await topic_robot.main()
    log.error('这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')
    if not schedule_mark or pub_article_info.is_need_to_publish():
        e = ExtractTopicLottery()
        update_time: int = int(time.time()) - int(pub_article_info.lastPubDate.timestamp()) - 1800  # 这段逻辑关乎更新抽奖的数量！！！
        # 空闲中间的半个小时就是上一次发布之后休息的事件，可以往小调，但决不能是+一个时间段！！！
        await e.main()
        log.error(f'\n上次发布专栏时间：{pub_article_info.lastPubDate}'
                  f'\n更新抽奖时间为：{round(update_time / 3600, 2)}小时！')
        pub_article_info.start_ts = int(time.time())
        pub_article_info.save_lastPubTs()


@pushme_try_catch_decorator
def run(schedulers: Union[None, BlockingScheduler], pub_article_info: pubArticleInfo, schedule_mark: bool, *args,
        **kwargs):
    delta_hour = 8
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main(pub_article_info, schedule_mark))
    except Exception as e:
        log.exception(e)
        delta_hour = 24
        pushme(f'定时发布话题抽奖专栏任务出错', f'{traceback.format_exc()}')
    if schedule_mark and schedulers:
        nextjob = schedulers.add_job(run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                     run_date=datetime.now() + timedelta(hours=delta_hour))
        log.info(f"任务结束，等待下一次{nextjob.trigger}执行。")
        """
            每隔三个小时获取一次全部图片动态
        """


@async_pushme_try_catch_decorator
async def async_run(schedulers: Union[None, AsyncIOScheduler], pub_article_info: pubArticleInfo, schedule_mark: bool,
                    *args, **kwargs):
    delta_hour = 8
    try:
        await main(pub_article_info, schedule_mark)
    except Exception as e:
        log.exception(e)
        delta_hour = 24
        pushme(f'定时发布话题抽奖专栏任务出错', f'{traceback.format_exc()}')
    if schedule_mark and schedulers:
        next_job = schedulers.add_job(async_run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                      run_date=datetime.now() + timedelta(hours=delta_hour))
        log.info(f"任务结束，等待下一次{next_job.trigger}执行。")
        """
            每隔三个小时获取一次全部图片动态
        """


@pushme_try_catch_decorator
def schedule_get_topic_lot_main(schedule_mark: bool = True, show_log: bool = True):
    """
    模块主入口
    :param schedule_mark: 是否定时执行
    :param show_log: 是否打印日志
    :return:
    """
    log.info('启动获取B站话题抽奖程序！！！')
    pub_article_info = pubArticleInfo()
    if schedule_mark:
        # from apscheduler.triggers.cron import CronTrigger
        # cron_str = '0 20 * * *'
        # crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = BlockingScheduler()
        job = schedulers.add_job(async_run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                 run_date=(pub_article_info.lastPubDate + timedelta(
                                     hours=8)) if pub_article_info.lastPubDate and (
                                         pub_article_info.lastPubDate + timedelta(
                                     hours=8)) > datetime.now() else datetime.now() + timedelta(hours=2),
                                 misfire_grace_time=360)
        log.info(
            f'使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        run(None, pub_article_info, schedule_mark)


async def async_schedule_get_topic_lot_main(schedule_mark: bool = True, show_log: bool = True):
    """
    模块主入口
    :param schedule_mark: 是否定时执行
    :param show_log: 是否打印日志
    :return:
    """
    log.info('启动获取B站话题抽奖程序！！！')
    pub_article_info = pubArticleInfo()
    if schedule_mark:
        # from apscheduler.triggers.cron import CronTrigger
        # cron_str = '0 20 * * *'
        # crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = AsyncIOScheduler()
        job = schedulers.add_job(async_run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                 run_date=(pub_article_info.lastPubDate + timedelta(
                                     hours=8)) if pub_article_info.lastPubDate and (
                                         pub_article_info.lastPubDate + timedelta(
                                     hours=8)) > datetime.now() else datetime.now() + timedelta(minutes=1),
                                 misfire_grace_time=360)
        log.info(
            f'【B站话题抽奖】使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        await async_run(None, pub_article_info, schedule_mark)


if __name__ == '__main__':
    schedule_get_topic_lot_main()
