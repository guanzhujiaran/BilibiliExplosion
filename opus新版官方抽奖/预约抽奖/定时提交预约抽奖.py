# -*- coding: utf-8 -*-

import sys
from loguru import logger

sys.path.append('C:/pythontest/')
import b站cookie.b站cookie_
import b站cookie.globalvar as gl

from 获取直播预约json import rid_get_dynamic

from 查找并生成预约抽奖信息 import *

from 提交预约抽奖专栏 import generate_cv

log = logger.bind(user="预约抽奖")


def main():
    rid_run = rid_get_dynamic()
    rid_run.init()
    rid_run.get_dynamic_with_thread()
    log.info('获取预约信息完毕')
    Search_generate_reserve_lottery()
    log.info('获取预约抽奖信息完毕')

    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
    cookie3 = gl.get_value('cookie3')
    buvid3 = gl.get_value('buvid3_3')
    if cookie3 and csrf3 and ua3 and buvid3:
        gc = generate_cv(cookie3, ua3, csrf3, buvid3)
        gc.reserve_lottery()
    else:
        print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)

    log.info('提交专栏完毕')
    log.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')
    rid_run=None


if __name__ == '__main__':
    schedule_mark = False
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        log.info('使用内置定时器,开启定时任务,等待时间到达后执行')
        schedulers = BlockingScheduler()
        schedulers.add_job(main, CronTrigger.from_crontab('0 0 * * *'), misfire_grace_time=3600)
        schedulers.start()
    else:
        main()
