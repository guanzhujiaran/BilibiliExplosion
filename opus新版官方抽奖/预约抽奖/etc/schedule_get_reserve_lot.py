# -*- coding: utf-8 -*-
import asyncio
import sys
from loguru import logger
from datetime import datetime
from opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import rid_get_dynamic
from opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import  submit_reserve__lot_main



logger.remove()
log = logger.bind(user="预约抽奖")
log.add(sys.stderr, level="DEBUG", filter=lambda record: record["extra"].get('user') == __name__ + "预约抽奖")


async def main():
    rid_run = rid_get_dynamic()
    await rid_run.init()
    await rid_run.get_dynamic_with_thread()

    await submit_reserve__lot_main(False)

    log.info('提交专栏完毕')
    log.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')


def sync_main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    log.info("任务结束，等待下一次执行。")


if __name__ == '__main__':
    schedule_mark = True
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        cron_str = '0 20 * * *'
        crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = BlockingScheduler()
        job = schedulers.add_job(sync_main, crontrigger, misfire_grace_time=3600)
        log.info(
            f'使用内置定时器,开启定时任务,等待时间（{crontrigger.get_next_fire_time(datetime.now(), datetime.now())}）到达后执行')
        schedulers.start()
    else:
        sync_main()
