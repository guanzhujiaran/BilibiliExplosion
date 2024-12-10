"""
单轮回复
"""
import asyncio

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.background_service.background_service_model import DynScrapyStatusResp
from .base import new_router

router = new_router()
dyn_detail_scrapy_class = None


def start_background_service(show_log: bool):
    global dyn_detail_scrapy_class

    back_ground_tasks = []
    from grpc获取动态.src.监控up动态.bili_dynamic_monitor import bili_space_monitor
    from opus新版官方抽奖.转发抽奖 import 定时获取所有动态以及发布充电和官方抽奖专栏
    dyn_detail_scrapy_class = 定时获取所有动态以及发布充电和官方抽奖专栏
    from opus新版官方抽奖.预约抽奖.etc.schedule_get_reserve_lot import async_schedule_get_reserve_lot_main
    from opus新版官方抽奖.活动抽奖.定时获取话题抽奖 import async_schedule_get_topic_lot_main
    from fastapi接口.scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
    from src.monitor import bili_live_async_monitor
    back_ground_tasks.append(asyncio.create_task(bili_space_monitor.main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(
        定时获取所有动态以及发布充电和官方抽奖专栏.async_schedule_get_official_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(async_schedule_get_reserve_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(async_schedule_get_topic_lot_main(show_log=show_log)))
    back_ground_tasks.append(asyncio.create_task(async_monitor_ipv6_address_changes()))
    back_ground_tasks.append(asyncio.create_task(bili_live_async_monitor.async_main(ShowLog=show_log)))
    from grpc获取动态.Utils.MQClient.VoucherMQClient import VoucherMQClient
    back_ground_tasks.extend([
        asyncio.create_task(asyncio.to_thread(VoucherMQClient().start_voucher_break_consumer)) for _ in range(5)
    ])
    from fastapi接口.service.MQ.RunMQConsumer import run_mq_consumer
    back_ground_tasks.extend(run_mq_consumer())

    return back_ground_tasks


@router.get('/GetDynamicScrapyStatus', description='获取动态爬虫状态',
            response_model=CommonResponseModel[DynScrapyStatusResp])
async def get_dynamic_scrapy_status():
    if dyn_detail_scrapy_class and dyn_detail_scrapy_class.dyn_detail_scrapy is not None:
        return CommonResponseModel(data=DynScrapyStatusResp(
            first_dyn_id=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.first_dyn_id,
            succ_count=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.succ_count,
            cur_stop_num=dyn_detail_scrapy_class.dyn_detail_scrapy.stop_counter.cur_stop_continuous_num,
            latest_rid=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.latest_rid,
            latest_succ_dyn_id=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.latest_succ_dyn_id,
            start_ts=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.start_ts,
            freq=dyn_detail_scrapy_class.dyn_detail_scrapy.succ_counter.show_pace(),
        ))
    else:
        return CommonResponseModel(data=DynScrapyStatusResp())
