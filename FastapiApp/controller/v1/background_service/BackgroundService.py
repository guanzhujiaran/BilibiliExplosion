import asyncio
import inspect
from typing import Literal, Union, Any

from Models.common import CommonResponseModel
from Models.v1.background_service.background_service_model import AllLotScrapyStatusResp, \
    ProgressStatusResp, ProxyStatusResp
from scripts.database.clean_backup_outdated_dynamic import cleaner
from scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
from Service.BaseCrawler.launcher.scheduler_launcher import GenericCrawlerScheduler, BaseScheduler
from Service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from Service.GetOthersLotDyn.get_other_lot_main import get_others_lot_dyn as other_lot_class
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy
from Service.GrpcModule.GrpcSrc.监控up动态.bili_dynamic_monitor import bili_space_monitor
from Service.GrpcModule.GrpcSrc.获取取关对象.GetRmFollowingListV2 import gmflv2
from Service.opus新版官方抽奖.bili_lottery_api.refresh_bili_lot_database import \
    refresh_bili_lot_database_crawler
from Service.opus新版官方抽奖.bili_lottery_api.scrapyLotteryDataFromBapi import lottery_api_robot_dyn, \
    lottery_api_robot_reserve
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from Service.samsclub.main import sams_club_crawler, sams_club_SPU_detail_crawler
from Utils.Common import GLOBAL_SCHEDULER
from Utils.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from Utils.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from .base import new_router

router = new_router()


class BackgroundService:
    dyn_detail_database_cleaner = BaseScheduler(
        func=cleaner.do_clean,
        cron_expr="0 0 * * *",
        default_interval_seconds=2 * 3600,
    )
    get_proxy_methods_scheduler = GenericCrawlerScheduler(
        crawler=get_proxy_methods,
        cron_expr="0 */5 * * *",
        default_interval_seconds=12 * 3600,
    )
    samsclub_scheduler = GenericCrawlerScheduler(
        crawler=sams_club_crawler,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    samsclub_spu_detail_scheduler = GenericCrawlerScheduler(
        crawler=sams_club_SPU_detail_crawler,
        cron_expr="0 4 * * *",
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
        crawler_name='lottery_api_robot_dyn'
    )
    lottery_api_robot_reserve_scheduler = GenericCrawlerScheduler(
        crawler=lottery_api_robot_reserve,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
        crawler_name='lottery_api_robot_reserve'
    )
    gmflv2_scheduler = GenericCrawlerScheduler(
        crawler=gmflv2,
        cron_expr="0 0 * * *",
        default_interval_seconds=1,
        crawler_name='gmflv2'
    )


def start_background_service(show_log: bool):
    back_ground_tasks = [asyncio.create_task(bili_space_monitor.main(show_log=show_log)),
                         asyncio.create_task(async_monitor_ipv6_address_changes()),
                         ]
    # back_ground_tasks.append(
    # asyncio.create_task(schedule_refresh_bili_lot_database.async_schedule_refresh_bili_lotdata_database(True)))

    return back_ground_tasks


def get_scrapy_status(scrapy_type: Literal[
    'dyn', 'topic', 'reserve',
    'other_space', 'other_dyn',
    'refresh_bili_official', 'refresh_bili_reserve'
]) -> Any | dict | ProgressStatusResp | None:
    match scrapy_type:
        case 'dyn':
            if dyn_detail_scrapy is not None:
                return dyn_detail_scrapy.status_plugin.get_all_status()
            else:
                return dict()
        case 'topic':
            if topic_robot is not None:
                return topic_robot.stats_plugin.get_all_status()
            else:
                return dict()
        case 'reserve':
            if reserve_robot is not None:
                return reserve_robot.stats_plugin.get_all_status()
            else:
                return dict()
        case 'other_space':
            if other_lot_class and other_lot_class.robot:
                return ProgressStatusResp(
                    succ_count=other_lot_class.robot.space_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.space_succ_counter.start_ts,
                    total_num=other_lot_class.robot.space_succ_counter.total_num,
                    progress=other_lot_class.robot.space_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.space_succ_counter.is_running,
                    update_ts=other_lot_class.robot.space_succ_counter.update_ts,
                    running_params=other_lot_class.robot.space_succ_counter.running_params
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
                    update_ts=other_lot_class.robot.dyn_succ_counter.update_ts,
                    running_params=other_lot_class.robot.dyn_succ_counter.running_params
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
            response_model=CommonResponseModel[Union[Any, None]],
            response_model_exclude_none=True)
def get_dynamic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('dyn'))


@router.get('/GetTopicScrapyStatus', description='获取话题爬虫状态',
            response_model=CommonResponseModel[Union[Any, None]],
            response_model_exclude_none=True)
def get_topic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('topic'))


@router.get('/GetReserveScrapyStatus', description='获取预约爬虫状态',
            response_model=CommonResponseModel[Union[Any, None]],
            response_model_exclude_none=True)
def get_reserve_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status('reserve'))


@router.get('/GetAllLotScrapyStatus', description='获取所有爬虫状态',
            response_model=CommonResponseModel[Union[AllLotScrapyStatusResp, None]],
            response_model_exclude_none=True
            )
def get_all_scrapy_status():
    return CommonResponseModel(
        data=AllLotScrapyStatusResp(
            dyn_scrapy_status=get_scrapy_status('dyn'),
            topic_scrapy_status=get_scrapy_status('topic'),
            reserve_scrapy_status=get_scrapy_status('reserve'),
        )
    )


@router.get('/GetOthersLotSpaceStatus', description='获取其他人空间爬虫的状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
def get_others_lot_space_status():
    return CommonResponseModel(data=get_scrapy_status('other_space'))


@router.get('/GetOthersLotDynStatus', description='获取其他人动态爬虫的状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
def get_others_lot_dyn_status():
    return CommonResponseModel(data=get_scrapy_status('other_dyn'))


@router.get('/GetRefreshBiliOfficialStatus', description='获取刷新B站官方和充电抽奖结果状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
def get_refresh_bili_official_status():
    return CommonResponseModel(data=get_scrapy_status('refresh_bili_official'))


@router.get('/GetRefreshBiliReserveStatus', description='获取刷新B站预约抽奖结果状态',
            response_model=CommonResponseModel[Union[ProgressStatusResp, None]])
def get_refresh_bili_reserve_status():
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
def global_schedule():
    ret = []
    for job in GLOBAL_SCHEDULER.get_jobs():
        ret.append(str(job))
    return CommonResponseModel(data=ret)


@router.get('/BackgroundService/AllStat', description='后台服务状态', response_model=CommonResponseModel[Any],
            response_model_exclude_none=True)
def background_service_status():
    ret_list = []
    members = inspect.getmembers(BackgroundService)
    for name, value in members:
        if isinstance(value, GenericCrawlerScheduler):
            for plugin in value.crawler.plugins:
                if isinstance(plugin, StatsPlugin):
                    ret_list.append(
                        {
                            f'{name}': {
                                StatsPlugin.__name__: plugin.get_all_status(),
                                'last_exec_time': value.exec_info.last_exec_time
                            }
                        }
                    )
    return CommonResponseModel(data=ret_list)
