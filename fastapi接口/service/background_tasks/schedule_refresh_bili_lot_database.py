import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi接口.dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankTypeEnum
from grpc获取动态.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper as bili_official_sqlhelper
from fastapi接口.log.base_log import background_task_logger
from opus新版官方抽奖.转发抽奖.提交专栏信息 import ExtractOfficialLottery
from opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import ReserveScrapyRobot
from utl.pushme.pushme import async_pushme_try_catch_decorator, pushme

_scheduler_start_hour = 4  # 定时任务开始时间：凌晨4点


async def _get_next_run_date():
    dyn_lot_sync_ts: int | None = await lottery_data_statistic_redis.get_dyn_lot_sync_ts()
    if not dyn_lot_sync_ts:
        return datetime.now()
    latest_sync_datetime = datetime.fromtimestamp(dyn_lot_sync_ts)
    if latest_sync_datetime - datetime.now() < timedelta(hours=24):
        now = datetime.now()
        today_four_am = now.replace(hour=4, minute=0, second=0, microsecond=0)

        if now > today_four_am:
            # 如果现在时间已经超过今天的4点了，则计算明天4点的时间
            target_time = today_four_am + timedelta(days=1)
        else:
            # 如果还没有超过今天的4点，则目标时间为今天的4点
            target_time = today_four_am
        return target_time
    else:  # 如果距离上次同步时间超过24小时，则立即同步
        return datetime.now()


async def _refresh_bili_lot_database():
    """
    同步官方抽奖、充电抽奖和预约抽奖
    :return:
    """

    async def sync_2_redis(_lot_type: BiliLotStatisticLotTypeEnum):
        for j in BiliLotStatisticRankTypeEnum:
            tasks.append(
                lottery_data_statistic_redis.set_lot_prize_count(
                    lot_type=_lot_type,
                    rank_type=j,
                    uid_atari_count_dict=dict(
                        await bili_official_sqlhelper.get_all_lottery_result_rank(
                            business_type=BiliLotStatisticLotTypeEnum.lot_type_2_business_type(_lot_type),
                            rank_type=j
                        )
                    )
                )
            )

        await asyncio.gather(*tasks)
        await lottery_data_statistic_redis.set_sync_ts(lot_type=_lot_type, ts=int(time.time()))

    # 先同步一遍
    tasks = [sync_2_redis(i) for i in BiliLotStatisticLotTypeEnum]
    await asyncio.gather(*tasks)

    reserve_robot = ReserveScrapyRobot()
    e = ExtractOfficialLottery()
    await asyncio.gather(
        reserve_robot.refresh_not_drawn_lottery(),
        e.get_all_lots(is_api_update=True)
    )
    tasks = [sync_2_redis(i) for i in BiliLotStatisticLotTypeEnum]
    await asyncio.gather(*tasks)


@async_pushme_try_catch_decorator
async def _async_run(schedulers: Union[None, AsyncIOScheduler] = None, schedule_mark: bool = False,
                     *args,
                     **kwargs):
    try:
        await _refresh_bili_lot_database()
    except Exception as e:
        background_task_logger.exception(e)
        await asyncio.to_thread(pushme, f'【刷新B站抽奖数据库】任务出错', f'{traceback.format_exc()}')
    if schedule_mark and schedulers:
        run_date = await _get_next_run_date()
        nextjob = schedulers.add_job(_async_run, args=(schedulers, schedule_mark), trigger='date',
                                     run_date=run_date)
        background_task_logger.info(f"【刷新B站抽奖数据库】任务结束，等待下一次{nextjob.trigger}执行。")


async def async_schedule_get_topic_lot_main(schedule_mark: bool = True):
    """
    模块主入口
    :param schedule_mark: 是否定时执行
    :return:
    """
    background_task_logger.info('启动【刷新B站抽奖数据库】程序！！！')
    if schedule_mark:
        schedulers = AsyncIOScheduler()
        run_date = await _get_next_run_date()
        job = schedulers.add_job(_async_run, args=(schedulers, schedule_mark), trigger='date',
                                 run_date=run_date,
                                 misfire_grace_time=360)
        background_task_logger.critical(
            f'【刷新B站抽奖数据库】使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        await _async_run(None, schedule_mark)


if __name__ == "__main__":
    asyncio.run(_async_run())
