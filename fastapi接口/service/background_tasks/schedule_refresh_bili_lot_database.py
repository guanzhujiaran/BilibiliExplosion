import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Union
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi接口.dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticRankDateTypeEnum
from fastapi接口.scripts.database.同步向量数据库.sync_bili_lottery_data import sync_bili_lottery_data, \
    del_outdated_bili_lottery_data
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import \
    grpc_sql_helper as bili_official_sqlhelper
from fastapi接口.log.base_log import background_task_logger
from fastapi接口.service.opus新版官方抽奖.转发抽奖.提交专栏信息 import ExtractOfficialLottery
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import ReserveScrapyRobot
from utl.pushme.pushme import async_pushme_try_catch_decorator, pushme

_scheduler_start_hour = 4  # 定时任务开始时间：凌晨4点
reserve_robot: ReserveScrapyRobot | None = None
extract_official_lottery: ExtractOfficialLottery | None = None


async def _get_next_run_date():
    dyn_lot_sync_ts: int | None = await lottery_data_statistic_redis.get_sync_ts(
        lot_type=BiliLotStatisticLotTypeEnum.official
    )
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


async def __sync_bili_user_info_simple():
    res = await bili_official_sqlhelper.get_all_bili_user_info()
    await lottery_data_statistic_redis.set_bili_user_info_bulk(res)


async def __sync_2_redis(_lot_type: BiliLotStatisticLotTypeEnum, sync_ts_flag: bool = True):
    _tasks = []
    # 遍历抽奖类型
    for j in BiliLotStatisticRankTypeEnum:
        for k in BiliLotStatisticRankDateTypeEnum:
            start_ts, end_ts = k.get_start_end_ts()
            _tasks.append(
                lottery_data_statistic_redis.set_lot_prize_count(
                    date=k,
                    lot_type=_lot_type,
                    rank_type=j,
                    uid_atari_count_dict=dict(
                        await bili_official_sqlhelper.get_all_lottery_result_rank(
                            start_ts=start_ts,
                            end_ts=end_ts,
                            business_type=BiliLotStatisticLotTypeEnum.lot_type_2_business_type(_lot_type),
                            rank_type=j
                        )
                    )
                )
            )
    # 并发执行任务
    await asyncio.gather(*_tasks)
    # 如果需要同步时间戳，则将当前时间戳存入Redis
    if sync_ts_flag:
        await lottery_data_statistic_redis.set_sync_ts(lot_type=_lot_type, ts=int(time.time()))


async def _refresh_bili_lot_database():
    """
    同步官方抽奖、充电抽奖和预约抽奖
    :return:
    """
    global reserve_robot
    global extract_official_lottery

    # 定义一个异步函数，用于同步抽奖数据到Redis

    # 创建任务列表，用于同步抽奖数据到Redis
    tasks = [__sync_2_redis(i, sync_ts_flag=False) for i in BiliLotStatisticLotTypeEnum]
    tasks.append(__sync_bili_user_info_simple())

    # 初始化预约抽奖机器人
    reserve_robot = ReserveScrapyRobot()
    # 初始化官方抽奖提取器
    extract_official_lottery = ExtractOfficialLottery()
    # 并发执行预约抽奖机器人和官方抽奖提取器的刷新任务
    await asyncio.gather(
        reserve_robot.refresh_not_drawn_lottery(),
        extract_official_lottery.get_all_lots(is_api_update=True)
    )
    # 创建任务列表，用于同步抽奖数据到Redis
    tasks.extend([__sync_2_redis(i) for i in BiliLotStatisticLotTypeEnum])
    tasks.append(__sync_bili_user_info_simple())
    # 并发执行任务
    await asyncio.gather(*tasks)


@async_pushme_try_catch_decorator
async def _async_run(schedulers: Union[None, AsyncIOScheduler] = None, schedule_mark: bool = False,
                     *args,
                     **kwargs):
    try:
        if schedulers and schedule_mark:
            background_task_logger.info(
                f'【刷新B站抽奖数据库】通过定时器开始执行任务！')
        await _refresh_bili_lot_database()
        await sync_bili_lottery_data()
        await del_outdated_bili_lottery_data()
    except Exception as e:
        background_task_logger.exception(e)
        await asyncio.to_thread(pushme, f'【刷新B站抽奖数据库】任务出错', f'{traceback.format_exc()}')
    if schedule_mark and schedulers:
        run_date = await _get_next_run_date()
        nextjob = schedulers.add_job(_async_run, args=(schedulers, schedule_mark), trigger='date',
                                     run_date=run_date)
        background_task_logger.info(f"【刷新B站抽奖数据库】任务结束，等待下一次{nextjob.trigger}执行。")


async def async_schedule_refresh_bili_lotdata_database(schedule_mark: bool = True):
    """
    模块主入口
    :param schedule_mark: 是否定时执行
    :return:
    """
    background_task_logger.info('启动【刷新B站抽奖数据库】程序！！！')
    if schedule_mark:
        schedulers = AsyncIOScheduler()
        run_date = await _get_next_run_date()
        job = schedulers.add_job(_async_run,
                                 args=(schedulers, schedule_mark),
                                 trigger='date',
                                 run_date=run_date,
                                 misfire_grace_time=360
                                 )
        background_task_logger.info(
            f'【刷新B站抽奖数据库】使用内置定时器,开启定时任务,等待时间（{job.trigger}）到达后执行')
        schedulers.start()
    else:
        await _async_run(None, schedule_mark)


if __name__ == "__main__":
    async def _test():
        await asyncio.gather(*[__sync_2_redis(i) for i in BiliLotStatisticLotTypeEnum])


    asyncio.run(_test())
