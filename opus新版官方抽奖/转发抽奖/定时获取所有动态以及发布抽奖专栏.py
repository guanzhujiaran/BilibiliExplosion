# -*- coding: utf-8 -*-
import asyncio
import time

from loguru import logger

from grpc获取动态.src.根据日期获取抽奖动态.getLotDynSortByDate import LotDynSortByDate
from opus新版官方抽奖.转发抽奖.获取官方抽奖信息 import exctract_official_lottery
from grpc获取动态.src.getDynDetail import DynDetailScrapy

log = logger.bind(user="预约抽奖")


def main():
    d = DynDetailScrapy()
    d.main()  #####

    e = exctract_official_lottery()
    e.main()

    g = LotDynSortByDate()
    g.main([int(time.time()) - 3600 * 24, int(time.time())])

    log.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')


if __name__ == "__main__":
    schedule_mark = True
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        log.info('使用内置定时器,开启定时任务,等待时间到达后执行')
        schedulers = BlockingScheduler()
        schedulers.add_job(main, CronTrigger.from_crontab('0 0 * * *'), misfire_grace_time=3600)
        schedulers.start()
    else:
        main()
