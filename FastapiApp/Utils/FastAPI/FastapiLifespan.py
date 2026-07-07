import asyncio
import contextlib
import socket

from fastapi import FastAPI
import httpx
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine
from CONFIG import settings, CONFIG
from Service.LangChainCompo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Utils.FastAPI.alembic_manager import check_schemas
from Utils.通用.Common import GLOBAL_SCHEDULER, asyncio_gather
from controller.v1.background_service import BackgroundServiceController
from log.base_log import myfastapi_logger


@contextlib.asynccontextmanager
async def life_span(app: FastAPI):
    # 测试数据库连接
    try:
        await test_database_connections()
    except OperationalError as e:
        myfastapi_logger.critical(f"数据库连接测试失败: {e}")
        raise SystemExit(1)
    # 测试各个服务的端口和 host 连通性
    await test_service_ports_and_hosts()

    # ---- Schema 一致性校验：不一致则拒绝启动 ----
    if not await check_schemas():
        raise RuntimeError("数据库 Schema 与模型不一致，请先手动执行 alembic upgrade head")

    # 检查 milvus 数据库集合
    await asyncio.sleep(3)
    myfastapi_logger.critical("检查 milvus 数据库集合")
    await milvus_sql_helper.ensure_collection_exists()
    myfastapi_logger.critical("重试未处理的消息")
    await BiliLotDataPublisher.retry_pending_messages()
    # RPC handler 由 mq_controller.py 末尾导入 lottery_data 模块触发 @rpc_subscriber 注册
    # broker 连接由 FastAPI 通过 app.include_router(MqController.router) 自动管理
    myfastapi_logger.critical("开启其他服务")
    back_ground_tasks = []
    if settings.IS_DEV:
        myfastapi_logger.critical("开发环境不启动定时任务喵~")
    else:
        show_log = False
        GLOBAL_SCHEDULER.start()
        back_ground_tasks = BackgroundServiceController.start_monitor_tasks(
            show_log=show_log)
        myfastapi_logger.critical("其他服务已开启！可以开启服务了喵~")
        try:
            from Service.GetOthersLotDyn.core.get_others_lot_dyn import get_others_lot_dyn
            myfastapi_logger.critical("启动时预填充用户列表...")
            supp_summary = await get_others_lot_dyn._supplement_users()
            myfastapi_logger.critical(
                f"启动补充完成: {supp_summary['before_count']} -> {supp_summary['after_count']}个用户"
            )
        except Exception as e:
            myfastapi_logger.error(f"启动时补充用户列表失败: {e}")
    yield
    myfastapi_logger.critical("正在取消其他服务")
    [x.cancel() for x in back_ground_tasks]
    await asyncio_gather(*back_ground_tasks, log=myfastapi_logger)
    myfastapi_logger.critical("其他服务已取消")


async def test_database_connections():
    """测试所有数据库连接，如果连接失败直接报错退出"""
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
            myfastapi_logger.info(f"正在测试数据库 '{db_name}' 连接...")
            engine = create_async_engine(db_uri)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            myfastapi_logger.info(f"数据库 '{db_name}' 连接成功")
        except OperationalError as e:
            myfastapi_logger.critical(f"数据库 '{db_name}' 连接失败 | URI={db_uri} | 错误: {e}")
            raise
        except Exception as e:
            myfastapi_logger.critical(f"数据库 '{db_name}' 连接失败 | URI={db_uri} | 错误: {e}")
            raise SystemExit(f"数据库 '{db_name}' 连接失败") from e


async def test_port_connectivity(host: str, port: int, service_name: str, timeout: float = 5.0) -> bool:
    """测试指定 host 和 port 的连通性"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        myfastapi_logger.info(f"服务 '{service_name}' ({host}:{port}) 连接成功")
        return True
    except asyncio.TimeoutError:
        myfastapi_logger.error(f"服务 '{service_name}' ({host}:{port}) 连接超时")
        return False
    except ConnectionRefusedError:
        myfastapi_logger.error(f"服务 '{service_name}' ({host}:{port}) 连接被拒绝")
        return False
    except OSError as e:
        myfastapi_logger.error(f"服务 '{service_name}' ({host}:{port}) 连接失败：{e}")
        return False
    except Exception as e:
        myfastapi_logger.error(f"服务 '{service_name}' ({host}:{port}) 连接异常：{e}")
        return False


async def test_http_endpoint(url: str, service_name: str, timeout: float = 5.0) -> bool:
    """测试 HTTP 端点的连通性"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            myfastapi_logger.info(
                f"HTTP 服务 '{service_name}' ({url}) 连接成功，状态码：{response.status_code}")
            return True
    except httpx.TimeoutException:
        myfastapi_logger.error(f"HTTP 服务 '{service_name}' ({url}) 连接超时")
        return False
    except httpx.RequestError as e:
        myfastapi_logger.error(f"HTTP 服务 '{service_name}' ({url}) 连接失败：{e}")
        return False
    except Exception as e:
        myfastapi_logger.error(f"HTTP 服务 '{service_name}' ({url}) 连接异常：{e}")
        return False


async def test_service_ports_and_hosts():
    """测试 CONFIG 中设置的所有服务的端口和 host 连通性"""
    myfastapi_logger.critical("开始测试各服务端口和 host 连通性...")

    failed_services = []
    services_to_test = [
        ("MySQL", settings.MYSQL_HOST, int(settings.MYSQL_PORT)),
        ("Redis", settings.REDIS_HOST, int(settings.REDIS_PORT)),
        ("RabbitMQ", settings.RABBITMQ_HOST, int(settings.RABBITMQ_PORT)),
        ("Unidbg", None, int(settings.UNIDBG_PORT), settings.UNIDBG_HOST),
        ("V2Ray", settings.V2RAY_HOST, int(settings.V2RAY_PORT)),
        ("LM Studio", None, int(settings.LMSTUDIO_PORT), settings.LMSTUDIO_HOST),
        ("Milvus", settings.MILVUS_HOST, int(settings.MILVUS_PORT)),
    ]

    for service_info in services_to_test:
        if len(service_info) == 3:
            service_name, host, port = service_info
            if not await test_port_connectivity(host, port, service_name):
                failed_services.append(f"{service_name} ({host}:{port})")
        else:
            service_name, _, port, host = service_info
            url = f"http://{host}:{port}"
            if not await test_http_endpoint(url, service_name):
                failed_services.append(f"{service_name} ({url})")

    if failed_services:
        myfastapi_logger.critical("=" * 60)
        myfastapi_logger.critical("以下服务连接失败:")
        for failed_service in failed_services:
            myfastapi_logger.critical(f"  ❌ {failed_service}")
        myfastapi_logger.critical("=" * 60)
    else:
        myfastapi_logger.critical("✅ 所有服务端口和 host 连通性测试通过!")


__all__ = ["life_span"]

if __name__ == '__main__':
    asyncio.run(test_database_connections())
