# -*- coding: utf-8 -*-
import sys

import asyncio
import time
from datetime import datetime
from loguru import logger
from grpc获取动态.src.根据日期获取抽奖动态.getLotDynSortByDate import LotDynSortByDate
from opus新版官方抽奖.转发抽奖.获取官方抽奖信息 import exctract_official_lottery
from grpc获取动态.src.getDynDetail import DynDetailScrapy

logger.remove()
log = logger.bind(user=__name__ + "官方抽奖")
logger.add(sys.stderr, level="INFO", filter=lambda record: record["extra"].get('user') == __name__ + "官方抽奖")


async def main():
    d = DynDetailScrapy()
    await d.main()  #####

    e = exctract_official_lottery()
    await e.main()

    g = LotDynSortByDate()
    g.main([int(time.time()) - 3600 * 24, int(time.time())])

    log.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')


def run(*args, **kwargs):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    log.info("任务结束，等待下一次执行。")


if __name__ == "__main__":
    schedule_mark = True
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        cron_str = '0 20 * * *'
        crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = BlockingScheduler()
        job = schedulers.add_job(run, crontrigger, misfire_grace_time=3600)
        log.info(
            f'使用内置定时器,开启定时任务,等待时间（{crontrigger.get_next_fire_time(datetime.now(), datetime.now())}）到达后执行')
        schedulers.start()
    else:
        run()
