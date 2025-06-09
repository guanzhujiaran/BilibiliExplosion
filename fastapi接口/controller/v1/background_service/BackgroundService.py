import asyncio
from typing import Literal, Union
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.background_service.background_service_model import DynScrapyStatusResp, \
    TopicScrapyStatusResp, ReserveScrapyStatusResp, AllLotScrapyStatusResp, OthersLotStatusResp, ProxyStatusResp
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from .base import new_router
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import get_others_lot_dyn as other_lot_class
from fastapi接口.service.background_tasks import schedule_refresh_bili_lot_database
from fastapi接口.service.grpc_module.src.监控up动态.bili_dynamic_monitor import bili_space_monitor
from fastapi接口.service.opus新版官方抽奖.转发抽奖 import \
    定时获取所有动态以及发布充电和官方抽奖专栏 as dyn_detail_scrapy_class
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc import schedule_get_reserve_lot as reserve_scrapy_class
from fastapi接口.service.opus新版官方抽奖.活动抽奖 import 定时获取话题抽奖 as topic_scrapy_class
from fastapi接口.scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
from fastapi接口.service.bili_live_monitor.src.monitor import bili_live_async_monitor
from fastapi接口.service.grpc_module.Utils.MQClient.VoucherMQClient import VoucherMQClient

router = new_router()


def start_background_service(show_log: bool):
    back_ground_tasks = []

    back_ground_tasks.append(asyncio.create_task(bili_space_monitor.main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(
        dyn_detail_scrapy_class.async_schedule_get_official_lot_main(show_log=show_log)))
    back_ground_tasks.append(
        asyncio.create_task(reserve_scrapy_class.async_schedule_get_reserve_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(
        topic_scrapy_class.async_schedule_get_topic_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(async_monitor_ipv6_address_changes()))
    back_ground_tasks.append(asyncio.create_task(bili_live_async_monitor.async_main(ShowLog=show_log)))
    back_ground_tasks.append(
        asyncio.create_task(schedule_refresh_bili_lot_database.async_schedule_refresh_bili_lotdata_database(True)))
    back_ground_tasks.append(
        asyncio.create_task(asyncio.to_thread(VoucherMQClient().start_voucher_break_consumer))
    )

    return back_ground_tasks


def get_scrapy_status(scrapy_type: Literal[
    'dyn', 'topic', 'reserve',
    'other_space', 'other_dyn',
    'refresh_bili_official', 'refresh_bili_reserve'
]) -> DynScrapyStatusResp | TopicScrapyStatusResp | ReserveScrapyStatusResp | OthersLotStatusResp | None:
    match scrapy_type:
        case 'dyn':
            if dyn_detail_scrapy_class and dyn_detail_scrapy_class.dyn_detail_scrapy is not None:
                return DynScrapyStatusResp(
                    first_dyn_id=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.first_dyn_id,
                    succ_count=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.succ_count,
                    cur_stop_num=dyn_detail_scrapy_class.dyn_detail_scrapy.stop_counter.cur_stop_continuous_num,
                    latest_rid=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.latest_rid,
                    latest_succ_dyn_id=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.latest_succ_dyn_id,
                    start_ts=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.start_ts,
                    freq=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.show_pace(),
                    is_running=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.is_running,
                    update_ts=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.update_ts
                )
            else:
                return DynScrapyStatusResp()
        case 'topic':
            if topic_scrapy_class and topic_scrapy_class.topic_robot is not None:
                return TopicScrapyStatusResp(
                    succ_count=topic_scrapy_class.topic_robot.succ_counter.succ_count,
                    cur_stop_num=topic_scrapy_class.topic_robot.cur_stop_times,
                    start_ts=topic_scrapy_class.topic_robot.succ_counter.start_ts,
                    freq=topic_scrapy_class.topic_robot.succ_counter.show_pace(),
                    is_running=topic_scrapy_class.topic_robot.succ_counter.is_running,
                    latest_succ_topic_id=topic_scrapy_class.topic_robot.succ_counter.latest_succ_topic_id,
                    first_topic_id=topic_scrapy_class.topic_robot.succ_counter.first_topic_id,
                    latest_topic_id=topic_scrapy_class.topic_robot.succ_counter.latest_topic_id,
                    update_ts=topic_scrapy_class.topic_robot.succ_counter.update_ts
                )
            else:
                return TopicScrapyStatusResp()
        case 'reserve':
            if reserve_scrapy_class and reserve_scrapy_class.reserve_robot is not None:
                return ReserveScrapyStatusResp(
                    succ_count=reserve_scrapy_class.reserve_robot.stats_plugin.processed_items_count,
                    cur_stop_num=reserve_scrapy_class.reserve_robot.null_stop_plugin.sequential_null_count,
                    start_ts=int(reserve_scrapy_class.reserve_robot.stats_plugin.start_time),
                    freq=reserve_scrapy_class.reserve_robot.stats_plugin.crawling_speed,
                    is_running=reserve_scrapy_class.reserve_robot.stats_plugin.is_running,
                    latest_succ_reserve_id=reserve_scrapy_class.reserve_robot.stats_plugin.end_success_params,
                    first_reserve_id=reserve_scrapy_class.reserve_robot.stats_plugin.init_params,
                    latest_reserve_id=reserve_scrapy_class.reserve_robot.stats_plugin.end_params,
                    update_ts=int(reserve_scrapy_class.reserve_robot.stats_plugin.last_update_time)
                )
            else:
                return ReserveScrapyStatusResp()
        case 'other_space':
            if other_lot_class and other_lot_class.robot:
                return OthersLotStatusResp(
                    succ_count=other_lot_class.robot.space_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.space_succ_counter.start_ts,
                    total_num=other_lot_class.robot.space_succ_counter.total_num,
                    progress=other_lot_class.robot.space_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.space_succ_counter.is_running,
                    update_ts=other_lot_class.robot.space_succ_counter.update_ts
                )
            else:
                return OthersLotStatusResp()
        case 'other_dyn':
            if other_lot_class and other_lot_class.robot:
                return OthersLotStatusResp(
                    succ_count=other_lot_class.robot.dyn_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.dyn_succ_counter.start_ts,
                    total_num=other_lot_class.robot.dyn_succ_counter.total_num,
                    progress=other_lot_class.robot.dyn_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.dyn_succ_counter.is_running,
                    update_ts=other_lot_class.robot.dyn_succ_counter.update_ts
                )
            else:
                return OthersLotStatusResp()
        case 'refresh_bili_official':
            if schedule_refresh_bili_lot_database.extract_official_lottery \
                    and schedule_refresh_bili_lot_database.extract_official_lottery.refresh_official_lot_progress:
                _progress = schedule_refresh_bili_lot_database.extract_official_lottery.refresh_official_lot_progress
                return OthersLotStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts
                )
            else:
                return OthersLotStatusResp()
        case 'refresh_bili_reserve':
            if schedule_refresh_bili_lot_database.reserve_robot \
                    and schedule_refresh_bili_lot_database.reserve_robot.refresh_progress_counter:
                _progress = schedule_refresh_bili_lot_database.reserve_robot.refresh_progress_counter
                return OthersLotStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts
                )
            else:
                return OthersLotStatusResp()


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
            response_model=CommonResponseModel[Union[OthersLotStatusResp, None]])
async def get_others_lot_space_status():
    return CommonResponseModel(data=get_scrapy_status('other_space'))


@router.get('/GetOthersLotDynStatus', description='获取其他人动态爬虫的状态',
            response_model=CommonResponseModel[Union[OthersLotStatusResp, None]])
async def get_others_lot_dyn_status():
    return CommonResponseModel(data=get_scrapy_status('other_dyn'))


@router.get('/GetRefreshBiliOfficialStatus', description='获取刷新B站官方和充电抽奖结果状态',
            response_model=CommonResponseModel[Union[OthersLotStatusResp, None]])
async def get_refresh_bili_official_status():
    return CommonResponseModel(data=get_scrapy_status('refresh_bili_official'))


@router.get('/GetRefreshBiliReserveStatus', description='获取刷新B站预约抽奖结果状态',
            response_model=CommonResponseModel[Union[OthersLotStatusResp, None]])
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

if __name__ == "__main__":
    async def _test():
        tasks = start_background_service(True)
        await asyncio.gather(*tasks)
    asyncio.run(_test())