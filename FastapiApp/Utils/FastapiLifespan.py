import asyncio
import contextlib

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from CONFIG import settings, CONFIG
from Service.LangChainCompo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Utils.Common import GLOBAL_SCHEDULER, asyncio_gather
from controller.v1.background_service import BackgroundServiceController
from log.base_log import myfastapi_logger


@contextlib.asynccontextmanager
async def life_span(app: FastAPI):
    # 测试数据库连接
    await test_database_connections()
    
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


async def test_database_connections():
    """
    测试所有数据库连接，如果连接失败直接报错退出
    """
    databases = {
        "proxy_db": CONFIG.database.MYSQL.proxy_db_URI,
        "bilidb": CONFIG.database.MYSQL.bili_db_URI,
        "bili_reserve": CONFIG.database.MYSQL.bili_reserve_URI,
        "get_other_lot": CONFIG.database.MYSQL.get_other_lot_URI,
        "dyndetail": CONFIG.database.MYSQL.dyn_detail_URI,
        "sams_club": CONFIG.database.MYSQL.sams_club_URI,
    }
    
    for db_name, db_uri in databases.items():
        try:
            # 创建引擎
            engine = create_async_engine(db_uri)
            
            # 尝试连接数据库
            async with engine.connect() as conn:
                # 执行简单查询以确认连接正常
                await conn.execute(text("SELECT 1"))
                
            # dispose engine
            await engine.dispose()
            
            myfastapi_logger.info(f"数据库 '{db_name}' 连接成功")
        except Exception as e:
            myfastapi_logger.critical(f"数据库 '{db_name}' 连接失败: {e}")
            raise SystemExit(f"数据库 '{db_name}' 连接失败: {e}")


__all__ = [
    "life_span"
]
if __name__ == '__main__':
    asyncio.run(test_database_connections())