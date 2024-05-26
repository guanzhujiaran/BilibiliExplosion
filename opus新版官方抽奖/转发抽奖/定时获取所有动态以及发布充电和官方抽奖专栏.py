# -*- coding: utf-8 -*-
import os.path

from typing import Union

import pydantic
import sys
import asyncio
import time
from datetime import datetime, timedelta
from loguru import logger

from CONFIG import CONFIG
from grpc获取动态.src.根据日期获取抽奖动态.getLotDynSortByDate import LotDynSortByDate
from opus新版官方抽奖.转发抽奖.获取官方抽奖信息 import exctract_official_lottery
from grpc获取动态.src.getDynDetail import DynDetailScrapy

logger.remove()
log = logger.bind(user=__name__ + "官方抽奖")
logger.add(sys.stderr, level="INFO",
#            filter=lambda record: record["extra"].get('user') in [
#     '全局日志',
#     'doc_id转dynamic_id日志',
#     'unknown_module',
#     'unknown_card',
#     'common_error_log',
#     'additional_module_log'
# ]
           )
# logger.add(sys.stderr, level="INFO", filter=lambda record: record["extra"].get('user') == __name__ + "官方抽奖")
# logger.add(sys.stderr, level="ERROR", filter=lambda record: record["extra"].get('user') =="MYREQ")
logger.add(
    "log/error_log.log",
    encoding="utf-8",
    enqueue=True,
    rotation="500MB",
    compression="zip",
    retention="15 days",
    filter=lambda record: record["extra"].get('user') == "error_log"
)


class pubArticleInfo(pydantic.BaseModel):
    lastPubDate: Union[datetime, None] = None
    shouldPubHour: int = 20  # 每天发布的专栏的事件
    start_ts: int = int(time.time())

    def __init__(self):
        super().__init__()
        settingPath = CONFIG.root_dir + 'opus新版官方抽奖/转发抽奖/log/'
        if not os.path.exists(settingPath):
            os.mkdir(settingPath)
        try:
            with open(settingPath + 'lastPubTs.txt', 'r', encoding='utf-8') as f:
                contents = f.read().strip()
                self.lastPubDate = datetime.fromtimestamp(int(contents))
                log.info(f"获取到上一次发布专栏的时间是：{self.lastPubDate.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            log.warning(f"获取到上一次发布专栏的时间失败")

    def save_lastPubTs(self):
        try:
            settingPath = CONFIG.root_dir + 'opus新版官方抽奖/转发抽奖/log/'
            with open(settingPath + 'lastPubTs.txt', 'w', encoding='utf-8') as f:
                f.write(str(int(self.lastPubDate.timestamp())))
        except Exception as e:
            log.exception(e)

    def is_need_to_publish(self):
        if self.lastPubDate:
            now = datetime.now()
            if self.lastPubDate.day != now.day:
                if now.hour >= self.shouldPubHour or now.timestamp() - self.lastPubDate.timestamp() >= 24 * 3600:
                    self.lastPubDate = now
                    log.info('满足发布专栏文章条件，发布专栏！')
                    return True
        else:
            now = datetime.now()
            self.lastPubDate = now - timedelta(days=1)
        log.debug('不满足发布专栏文章条件，不发布专栏！')
        return False


async def main():
    d = DynDetailScrapy()
    await d.main()
    if not schedule_mark or pub_article_info.is_need_to_publish():
        e = exctract_official_lottery()
        await e.main()

        g = LotDynSortByDate()
        g.main([pub_article_info.start_ts, int(time.time())])
        pub_article_info.start_ts = int(time.time())
        pub_article_info.save_lastPubTs()
        log.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')


def run(*args, **kwargs):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())

    if schedule_mark:
        nextjob = schedulers.add_job(run, trigger='date', run_date=datetime.now() + timedelta(hours=1))
        log.info(f"任务结束，等待下一次{nextjob.trigger}执行。")


if __name__ == "__main__":
    schedule_mark = True
    pub_article_info = pubArticleInfo()
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler

        # from apscheduler.triggers.cron import CronTrigger

        # cron_str = '0 20 * * *'
        # crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = BlockingScheduler()
        job = schedulers.add_job(run, trigger='date', run_date=datetime.now(), misfire_grace_time=360)
        log.info(
            f'使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        run()
