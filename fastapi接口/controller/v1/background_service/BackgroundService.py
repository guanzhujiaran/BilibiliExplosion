import asyncio
from typing import Literal, Union, Any

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.background_service.background_service_model import DynScrapyStatusResp, \
    TopicScrapyStatusResp, ReserveScrapyStatusResp, AllLotScrapyStatusResp, ProgressStatusResp, ProxyStatusResp
from fastapi接口.scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
from fastapi接口.service.BaseCrawler.launcher.scheduler_launcher import GenericCrawlerScheduler
from fastapi接口.service.bili_live_monitor.src.monitor import bili_live_async_monitor
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import get_others_lot_dyn as other_lot_class
from fastapi接口.service.grpc_module.Utils.MQClient.VoucherMQClient import VoucherMQClient
from fastapi接口.service.grpc_module.src.getDynDetail import dyn_detail_scrapy
from fastapi接口.service.grpc_module.src.监控up动态.bili_dynamic_monitor import bili_space_monitor
from fastapi接口.service.opus新版官方抽奖.bili_lottery_api.refresh_bili_lot_database import \
    refresh_bili_lot_database_crawler
from fastapi接口.service.opus新版官方抽奖.bili_lottery_api.scrapyLotteryDataFromBapi import lottery_api_robot_dyn, \
    lottery_api_robot_reserve
from fastapi接口.service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from fastapi接口.service.samsclub.main import sams_club_crawler
from fastapi接口.utils.Common import GLOBAL_SCHEDULER
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from .base import new_router

router = new_router()


def start_background_service(show_log: bool):
    samsclub_scheduler = GenericCrawlerScheduler(
        crawler=sams_club_crawler,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_reserve_lot = GenericCrawlerScheduler(
        crawler=reserve_robot,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_dyn = GenericCrawlerScheduler(
        crawler=dyn_detail_scrapy,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_topic = GenericCrawlerScheduler(
        crawler=topic_robot,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    refresh_bili_lotdata_database = GenericCrawlerScheduler(
        crawler=refresh_bili_lot_database_crawler,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    lottery_api_robot_dyn_scheduler = GenericCrawlerScheduler(
        crawler=lottery_api_robot_dyn,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    lottery_api_robot_reserve_scheduler = GenericCrawlerScheduler(
        crawler=lottery_api_robot_reserve,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    back_ground_tasks = [asyncio.create_task(bili_space_monitor.main(show_log=show_log)),
                         asyncio.create_task(async_monitor_ipv6_address_changes()),
                         asyncio.create_task(bili_live_async_monitor.async_main(ShowLog=show_log)),
                         asyncio.create_task(asyncio.to_thread(VoucherMQClient().start_voucher_break_consumer))]
    # back_ground_tasks.append(
    # asyncio.create_task(schedule_refresh_bili_lot_database.async_schedule_refresh_bili_lotdata_database(True)))

    return back_ground_tasks


def get_scrapy_status(scrapy_type: Literal[
    'dyn', 'topic', 'reserve',
    'other_space', 'other_dyn',
    'refresh_bili_official', 'refresh_bili_reserve'
]) -> DynScrapyStatusResp | TopicScrapyStatusResp | ReserveScrapyStatusResp | ProgressStatusResp | None:
    match scrapy_type:
        case 'dyn':
            if dyn_detail_scrapy is not None:
                return DynScrapyStatusResp(
                    first_dyn_id=dyn_detail_scrapy.succ_counter.first_dyn_id or 0,
                    succ_count=dyn_detail_scrapy.status_plugin.succ_count or 0,
                    cur_stop_num=dyn_detail_scrapy.stop_counter.cur_stop_continuous_num or 0,
                    latest_rid=dyn_detail_scrapy.status_plugin.end_params or 0,
                    latest_succ_dyn_id=dyn_detail_scrapy.succ_counter.latest_succ_dyn_id or 0,
                    start_ts=int(dyn_detail_scrapy.status_plugin.start_time),
                    freq=dyn_detail_scrapy.status_plugin.crawling_speed,
                    is_running=dyn_detail_scrapy.status_plugin.is_running,
                    update_ts=int(dyn_detail_scrapy.status_plugin.last_update_time)
                )
            else:
                return DynScrapyStatusResp()
        case 'topic':
            if topic_robot is not None:
                return TopicScrapyStatusResp(
                    succ_count=topic_robot.stats_plugin.succ_count,
                    cur_stop_num=topic_robot.cur_stop_times or 0,
                    start_ts=int(topic_robot.stats_plugin.start_time),
                    freq=topic_robot.stats_plugin.crawling_speed,
                    is_running=topic_robot.stats_plugin.is_running,
                    latest_succ_topic_id=topic_robot.stats_plugin.end_success_params or 0,
                    first_topic_id=topic_robot.stats_plugin.init_params or 0,
                    latest_topic_id=topic_robot.stats_plugin.end_params or 0,
                    update_ts=int(topic_robot.stats_plugin.last_update_time)
                )
            else:
                return TopicScrapyStatusResp()
        case 'reserve':
            if reserve_robot is not None:
                return ReserveScrapyStatusResp(
                    succ_count=reserve_robot.stats_plugin.processed_items_count,
                    cur_stop_num=reserve_robot.null_stop_plugin.sequential_null_count or 0,
                    start_ts=int(reserve_robot.stats_plugin.start_time),
                    freq=reserve_robot.stats_plugin.crawling_speed,
                    is_running=reserve_robot.stats_plugin.is_running,
                    latest_succ_reserve_id=reserve_robot.stats_plugin.end_success_params or 0,
                    first_reserve_id=reserve_robot.stats_plugin.init_params or 0,
                    latest_reserve_id=reserve_robot.stats_plugin.end_params or 0,
                    update_ts=int(reserve_robot.stats_plugin.last_update_time)
                )
            else:
                return ReserveScrapyStatusResp()
        case 'other_space':
            if other_lot_class and other_lot_class.robot:
                return ProgressStatusResp(
                    succ_count=other_lot_class.robot.space_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.space_succ_counter.start_ts,
                    total_num=other_lot_class.robot.space_succ_counter.total_num,
                    progress=other_lot_class.robot.space_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.space_succ_counter.is_running,
                    update_ts=other_lot_class.robot.space_succ_counter.update_ts
                )
            else:
                return ProgressStatusResp()
        case 'other_dyn':
            if other_lot_class and other_lot_class.robot:
                return ProgressStatusResp(
                    succ_count=other_lot_class.robot.dyn_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.dyn_succ_counter.start_ts,
                    total_num=other_lot_class.robot.dyn_succ_counter.total_num,
                    progress=other_lot_class.robot.dyn_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.dyn_succ_counter.is_running,
                    update_ts=other_lot_class.robot.dyn_succ_counter.update_ts
                )
            else:
                return ProgressStatusResp()
        case 'refresh_bili_official':
            if refresh_bili_lot_database_crawler.extract_official_lottery \
                    and refresh_bili_lot_database_crawler.extract_official_lottery.refresh_official_lot_progress:
                _progress = refresh_bili_lot_database_crawler.extract_official_lottery.refresh_official_lot_progress
                return ProgressStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts
                )
            else:
                return ProgressStatusResp()
        case 'refresh_bili_reserve':
            if refresh_bili_lot_database_crawler.reserve_robot \
                    and refresh_bili_lot_database_crawler.reserve_robot.refresh_progress_counter:
                _progress = refresh_bili_lot_database_crawler.reserve_robot.refresh_progress_counter
                return ProgressStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts
                )
            else:
                return ProgressStatusResp()


@router.get('/GetDynamicScrapyStatus', description='获取动态爬虫状态',
            response_model=CommonResponseModel[Union[DynScrapyStatusResp, None]])
async def get_dynamic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('dyn'))


@router.get('/GetTopicScrapyStatus', description='获取话题爬虫状态',
            response_model=CommonResponseModel[Union[TopicScrapyStatusResp, None]])
async def get_topic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('topic'))


@router.get('/GetReserveScrapyStatus', description='获取预约爬虫状态',
            response_model=CommonResponseModel[Union[ReserveScrapyStatusResp, None]])
async def get_reserve_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('reserve'))


@router.get('/GetAllLotScrapyStatus', description='获取所有爬虫状态',
            response_model=CommonResponseModel[Union[AllLotScrapyStatusResp, None]])
async def get_all_scrapy_status():
    return CommonResponseModel(
        data=AllLotScrapyStatusResp(
            dyn_scrapy_status=get_scrapy_status('dyn'),
            topic_scrapy_status=get_scrapy_status('topic'),
            reserve_scrapy_status=get_scrapy_status('reserve'),
        )
    )


@router.get('/GetOthersLotSpaceStatus', description='获取其他人空间爬虫的状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
async def get_others_lot_space_status():
    return CommonResponseModel(data=get_scrapy_status('other_space'))


@router.get('/GetOthersLotDynStatus', description='获取其他人动态爬虫的状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
async def get_others_lot_dyn_status():
    return CommonResponseModel(data=get_scrapy_status('other_dyn'))


@router.get('/GetRefreshBiliOfficialStatus', description='获取刷新B站官方和充电抽奖结果状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
async def get_refresh_bili_official_status():
    return CommonResponseModel(data=get_scrapy_status('refresh_bili_official'))


@router.get('/GetRefreshBiliReserveStatus', description='获取刷新B站预约抽奖结果状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
async def get_refresh_bili_reserve_status():
    return CommonResponseModel(data=get_scrapy_status('refresh_bili_reserve'))


@router.get('/GetProxyStatus',
            description='获取代理状态',
            response_model=CommonResponseModel[Union[ProxyStatusResp, None]]
            )
async def get_proxy_status():
    return CommonResponseModel(data=
                               await SQLHelper.get_proxy_database_redis()
                               )


@router.get('/GlobalSchedule/get_jobs', description='全局定时任务', response_model=CommonResponseModel[Any])
async def global_schedule():
    ret = []
    for job in GLOBAL_SCHEDULER.get_jobs():
        ret.append(str(job))
    return CommonResponseModel(data=ret)
