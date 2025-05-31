# -*- coding: utf-8 -*-
import asyncio
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi接口.log.base_log import reserve_lot_logger
from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import ReserveScrapyRobot
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import submit_reserve__lot_main
from utl.pushme.pushme import pushme, async_pushme_try_catch_decorator


class pubArticleInfo(CustomBaseModel):
    lastPubDate: Union[datetime, None] = None
    shouldPubHour: int = 20  # 每天发布的专栏的事件
    start_ts: int = int(time.time())

    def __init__(self):
        super().__init__()
        setting_path = os.path.join(os.path.dirname(__file__), 'log/')
        if not os.path.exists(setting_path):
            os.mkdir(setting_path)
        try:
            with open(os.path.join(setting_path, 'lastPubTs.txt'), 'r', encoding='utf-8') as f:
                contents = f.read().strip()
                self.lastPubDate = datetime.fromtimestamp(int(contents))
                reserve_lot_logger.info(
                    f"获取到上一次发布专栏的时间是：{self.lastPubDate.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            reserve_lot_logger.exception(f"获取到上一次发布专栏的时间失败！使用0时间！")
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
            reserve_lot_logger.exception(e)

    def is_need_to_publish(self):
        if self.lastPubDate:
            now = datetime.now()
            if self.lastPubDate.day != now.day:  # 上次发布日期不在同一天
                # if now.hour >= self.shouldPubHour or now.timestamp() - self.lastPubDate.timestamp() >= 15 * 3600:  # 如果当前时间在20点之后或者距离上次发布超过了15小时，则直接发布
                if now.timestamp() - self.lastPubDate.timestamp() >= 2 * 3600:
                    reserve_lot_logger.error(f'满足发布专栏文章条件，发布专栏！\t上次发布时间：{self.lastPubDate}')
                    return True
            else:  # 上次发布日期在同一天
                if now.timestamp() - self.lastPubDate.timestamp() >= 24 * 3600:  # 同一天只要满足超过24小时，就直接发布
                    reserve_lot_logger.error(f'满足发布专栏文章条件，发布专栏！\t上次发布时间：{self.lastPubDate}')
                    return True
        else:
            now = datetime.now()
            self.lastPubDate = now - timedelta(days=1)
        reserve_lot_logger.error(f'不满足发布专栏文章条件，不发布专栏！\t上次发布时间：{self.lastPubDate}')
        return False


reserve_robot = None


@async_pushme_try_catch_decorator
async def async_run(schedulers: Union[None, AsyncIOScheduler], pub_article_info: pubArticleInfo, schedule_mark: bool,
                    *args, **kwargs):
    delta_hour = 8
    try:
        await main(pub_article_info, schedule_mark)
    except Exception as e:
        reserve_lot_logger.exception(e)
        delta_hour = 24
        pushme(f'定时发布预约抽奖专栏任务出错', f'{traceback.format_exc()}')
    if schedule_mark and schedulers:
        next_job = schedulers.add_job(async_run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                      run_date=datetime.now() + timedelta(hours=delta_hour))
        reserve_lot_logger.info(f"任务结束，等待下一次{next_job.trigger}执行。")


@async_pushme_try_catch_decorator
async def main(pub_article_info: pubArticleInfo, schedule_mark: bool):
    global reserve_robot
    reserve_robot = ReserveScrapyRobot()
    try:
        await reserve_robot.get_reserve_concurrency()
        await reserve_robot.refresh_not_drawn_lottery()
    except Exception as e:
        reserve_lot_logger.exception(f'获取预约抽奖信息失败！{e}')
    reserve_lot_logger.error('这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')
    if not schedule_mark or pub_article_info.is_need_to_publish():
        await submit_reserve__lot_main(is_post=True)
        update_time: int = int(time.time()) - int(pub_article_info.lastPubDate.timestamp()) - 1800  # 这段逻辑关乎更新抽奖的数量！！！
        # 空闲中间的半个小时就是上一次发布之后休息的事件，可以往小调，但决不能是+一个时间段！！！
        reserve_lot_logger.error(f'\n上次发布专栏时间：{pub_article_info.lastPubDate}'
                                 f'\n更新抽奖时间为：{round(update_time / 3600, 2)}小时！')
        pub_article_info.start_ts = int(time.time())
        pub_article_info.save_lastPubTs()


@async_pushme_try_catch_decorator
async def async_schedule_get_reserve_lot_main(schedule_mark: bool = True, show_log: bool = True):
    reserve_lot_logger.info('启动获取B站预约抽奖程序！！！')
    pub_article_info = pubArticleInfo()
    if schedule_mark:
        schedulers = AsyncIOScheduler()
        job = schedulers.add_job(async_run, args=(schedulers, pub_article_info, schedule_mark), trigger='date',
                                 run_date=(pub_article_info.lastPubDate + timedelta(
                                     hours=8)) if pub_article_info.lastPubDate and (
                                         pub_article_info.lastPubDate + timedelta(
                                     hours=8)) > datetime.now() else datetime.now() + timedelta(minutes=1),
                                 misfire_grace_time=360)
        reserve_lot_logger.info(
            f'【B站预约抽奖】使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        await async_run(None, pub_article_info, schedule_mark)
