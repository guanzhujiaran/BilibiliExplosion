"""
单轮回复
"""
import asyncio
from typing import Literal, Union

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.background_service.background_service_model import DynScrapyStatusResp, \
    TopicScrapyStatusResp, ReserveScrapyStatusResp, AllLotScrapyStatusResp
from .base import new_router

router = new_router()
dyn_detail_scrapy_class = None
topic_scrapy_class = None
reserve_scrapy_class = None


def start_background_service(show_log: bool):
    global dyn_detail_scrapy_class
    global topic_scrapy_class
    global reserve_scrapy_class
    back_ground_tasks = []
    from grpc获取动态.src.监控up动态.bili_dynamic_monitor import bili_space_monitor
    from opus新版官方抽奖.转发抽奖 import 定时获取所有动态以及发布充电和官方抽奖专栏
    dyn_detail_scrapy_class = 定时获取所有动态以及发布充电和官方抽奖专栏
    from opus新版官方抽奖.预约抽奖.etc import schedule_get_reserve_lot
    reserve_scrapy_class = schedule_get_reserve_lot
    from opus新版官方抽奖.活动抽奖 import 定时获取话题抽奖
    topic_scrapy_class = 定时获取话题抽奖
    from fastapi接口.scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
    from src.monitor import bili_live_async_monitor
    back_ground_tasks.append(asyncio.create_task(bili_space_monitor.main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(
        定时获取所有动态以及发布充电和官方抽奖专栏.async_schedule_get_official_lot_main(show_log=show_log)))
    back_ground_tasks.append(
        asyncio.create_task(schedule_get_reserve_lot.async_schedule_get_reserve_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(
        定时获取话题抽奖.async_schedule_get_topic_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(async_monitor_ipv6_address_changes()))
    back_ground_tasks.append(asyncio.create_task(bili_live_async_monitor.async_main(ShowLog=show_log)))
    from grpc获取动态.Utils.MQClient.VoucherMQClient import VoucherMQClient
    back_ground_tasks.extend([
        asyncio.create_task(asyncio.to_thread(VoucherMQClient().start_voucher_break_consumer)) for _ in range(5)
    ])
    # from fastapi接口.service.MQ.RunMQConsumer import run_mq_consumer
    # back_ground_tasks.extend(run_mq_consumer())

    return back_ground_tasks


def get_scrapy_status(type: Literal[
    'dyn', 'topic', 'reserve']) -> DynScrapyStatusResp | TopicScrapyStatusResp | ReserveScrapyStatusResp | None:
    match type:
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
                    is_running=dyn_detail_scrapy_class.dyn_detail_scrapy.is_running,
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
                    is_running=topic_scrapy_class.topic_robot.is_running,
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
                    succ_count=reserve_scrapy_class.reserve_robot.succ_counter.succ_count,
                    cur_stop_num=reserve_scrapy_class.reserve_robot.null_timer,
                    start_ts=reserve_scrapy_class.reserve_robot.succ_counter.start_ts,
                    freq=reserve_scrapy_class.reserve_robot.succ_counter.show_pace(),
                    is_running=reserve_scrapy_class.reserve_robot.is_running,
                    latest_succ_reserve_id=reserve_scrapy_class.reserve_robot.succ_counter.latest_succ_reserve_id,
                    first_reserve_id=reserve_scrapy_class.reserve_robot.succ_counter.first_reserve_id,
                    latest_reserve_id=reserve_scrapy_class.reserve_robot.succ_counter.latest_reserve_id,
                    update_ts=reserve_scrapy_class.reserve_robot.succ_counter.update_ts
                )
            else:
                return ReserveScrapyStatusResp()


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
            reserve_scrapy_status=get_scrapy_status('reserve')
        )
    )
