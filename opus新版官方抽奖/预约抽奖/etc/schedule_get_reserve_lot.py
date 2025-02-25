# -*- coding: utf-8 -*-
import asyncio
import os
from datetime import datetime
from CONFIG import CONFIG
from fastapi接口.log.base_log import reserve_lot_logger
from opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import ReserveScrapyRobot
from opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import submit_reserve__lot_main
from utl.pushme.pushme import pushme_try_catch_decorator, async_pushme_try_catch_decorator

reserve_robot = None


async def main():
    global reserve_robot
    reserve_robot = ReserveScrapyRobot()
    await reserve_robot.get_dynamic_with_thread()
    await reserve_robot.refresh_not_drawn_lottery()
    await submit_reserve__lot_main(is_post=True)

    reserve_lot_logger.info('提交专栏完毕')
    reserve_lot_logger.info('今天这轮跑完了！使用内置定时器,开启定时任务,等待时间到达后执行')


@pushme_try_catch_decorator
def sync_main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    reserve_lot_logger.info("任务结束，等待下一次执行。")


@pushme_try_catch_decorator
def schedule_get_reserve_lot_main(schedule_mark: bool = True, show_log: bool = True):
    reserve_lot_logger.info('启动获取预约抽奖程序！！！')
    reserve_lot_logger.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_reserve_lot_log.log"),
                           level="WARNING",
                           encoding="utf-8",
                           enqueue=True,
                           rotation="500MB",
                           compression="zip",
                           retention="15 days",
                           filter=lambda record: record["extra"].get('user') == "预约抽奖",
                           )
    if schedule_mark:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        cron_str = '0 20 * * *'
        crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = BlockingScheduler()
        job = schedulers.add_job(sync_main, crontrigger, misfire_grace_time=3600)
        reserve_lot_logger.info(
            f'使用内置定时器,开启定时任务,等待时间（{crontrigger.get_next_fire_time(datetime.now(), datetime.now())}）到达后执行')
        schedulers.start()
    else:
        sync_main()


@async_pushme_try_catch_decorator
async def async_schedule_get_reserve_lot_main(schedule_mark: bool = True, show_log: bool = True):
    reserve_lot_logger.info('启动获取预约抽奖程序！！！')
    reserve_lot_logger.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_reserve_lot_log.log"),
                           level="WARNING",
                           encoding="utf-8",
                           enqueue=True,
                           rotation="500MB",
                           compression="zip",
                           retention="15 days",
                           filter=lambda record: record["extra"].get('user') == "预约抽奖",
                           )
    if schedule_mark:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        cron_str = '0 20 * * *'
        crontrigger = CronTrigger.from_crontab(cron_str)
        schedulers = AsyncIOScheduler()
        job = schedulers.add_job(main, crontrigger, misfire_grace_time=3600)
        reserve_lot_logger.info(
            f'使用内置定时器,开启定时任务,等待时间（{crontrigger.get_next_fire_time(datetime.now(), datetime.now())}）到达后执行')
        schedulers.start()
    else:
        await main()


if __name__ == '__main__':
    schedule_get_reserve_lot_main()
    # asyncio.run(main())
