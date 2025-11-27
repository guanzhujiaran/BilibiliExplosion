import asyncio
import contextlib

from fastapi import FastAPI

from CONFIG import settings
from Service.LangChainCompo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Utils.Common import GLOBAL_SCHEDULER, asyncio_gather
from controller.v1.background_service import BackgroundServiceController
from log.base_log import myfastapi_logger


@contextlib.asynccontextmanager
async def life_span(app: FastAPI):
    # 确保向量数据库集合存在
    await asyncio.sleep(3)  # 等 HTTP server ready
    myfastapi_logger.critical("确保milvus数据库集合存在")
    await milvus_sql_helper.ensure_collection_exists()  # 必须执行
    myfastapi_logger.critical("重试未处理的消息")
    await BiliLotDataPublisher.retry_pending_messages()  # 重试未处理的消息
    myfastapi_logger.critical("开启其他服务")
    show_log = False
    back_ground_tasks = []
    if settings.IS_DEV:
        myfastapi_logger.critical("开发环境不启动定时任务喵~")
    else:
        GLOBAL_SCHEDULER.start()
        back_ground_tasks = BackgroundServiceController.start_background_service(show_log=show_log)
        myfastapi_logger.critical("其他服务已开启！可以开启服务了喵~")
    yield
    myfastapi_logger.critical("正在取消其他服务")
    [
        x.cancel() for x in back_ground_tasks
    ]
    await asyncio_gather(*back_ground_tasks, log=myfastapi_logger)
    myfastapi_logger.critical("其他服务已取消")


__all__ = [
    "life_span"
]
