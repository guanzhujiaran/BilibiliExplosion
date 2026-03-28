import asyncio
import contextlib
import socket

from fastapi import FastAPI
import httpx
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
    
    # 测试各个服务的端口和 host 连通性
    await test_service_ports_and_hosts()
    
    # 检查 milvus 数据库集合
    await asyncio.sleep(3)  # 等 HTTP server ready
    myfastapi_logger.critical("检查 milvus 数据库集合")
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
        back_ground_tasks = BackgroundServiceController.start_monitor_tasks(show_log=show_log)
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
            myfastapi_logger.critical(f"数据库 '{db_name}' 连接失败：{e}")
            raise SystemExit(f"数据库 '{db_name}' 连接失败：{e}")


async def test_port_connectivity(host: str, port: int, service_name: str, timeout: float = 5.0) -> bool:
    """
    测试指定 host 和 port 的连通性
    
    Args:
        host: 主机地址
        port: 端口号
        service_name: 服务名称
        timeout: 超时时间（秒）
    
    Returns:
        bool: 是否连接成功
    """
    try:
        # 使用 asyncio 创建 socket 连接
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
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
    """
    测试 HTTP 端点的连通性
    
    Args:
        url: HTTP 端点 URL
        service_name: 服务名称
        timeout: 超时时间（秒）
    
    Returns:
        bool: 是否连接成功
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            # 只要能收到响应就认为连接成功，不关心状态码
            myfastapi_logger.info(f"HTTP 服务 '{service_name}' ({url}) 连接成功，状态码：{response.status_code}")
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
    """
    测试 CONFIG 中设置的所有服务的端口和 host 连通性
    """
    myfastapi_logger.critical("开始测试各服务端口和 host 连通性...")
    
    failed_services = []
    
    # 定义要测试的服务列表
    services_to_test = [
        # MySQL (通过 socket 测试)
        ("MySQL", settings.MYSQL_HOST, int(settings.MYSQL_PORT)),
        
        # Redis (通过 socket 测试)
        ("Redis", settings.REDIS_HOST, int(settings.REDIS_PORT)),
        
        # RabbitMQ (通过 socket 测试)
        ("RabbitMQ", settings.RABBITMQ_HOST, int(settings.RABBITMQ_PORT)),
        
        # Unidbg (通过 HTTP 测试)
        ("Unidbg", None, int(settings.UNIDBG_PORT), settings.UNIDBG_HOST),
        
        # V2Ray (通过 socket 测试)
        ("V2Ray", settings.V2RAY_HOST, int(settings.V2RAY_PORT)),
        
        # LM Studio (通过 HTTP 测试)
        ("LM Studio", None, int(settings.LMSTUDIO_PORT), settings.LMSTUDIO_HOST),
        
        # Milvus (通过 socket 测试)
        ("Milvus", settings.MILVUS_HOST, int(settings.MILVUS_PORT)),
    ]
    
    for service_info in services_to_test:
        if len(service_info) == 3:
            # Socket 测试服务
            service_name, host, port = service_info
            success = await test_port_connectivity(host, port, service_name)
            if not success:
                failed_services.append(f"{service_name} ({host}:{port})")
        else:
            # HTTP 测试服务
            service_name, _, port, host = service_info
            url = f"http://{host}:{port}"
            success = await test_http_endpoint(url, service_name)
            if not success:
                failed_services.append(f"{service_name} ({url})")
    
    if failed_services:
        myfastapi_logger.critical("=" * 60)
        myfastapi_logger.critical("以下服务连接失败:")
        for failed_service in failed_services:
            myfastapi_logger.critical(f"  ❌ {failed_service}")
        myfastapi_logger.critical("=" * 60)
        # 可以选择是否要继续启动或抛出异常
        # myfastapi_logger.warning("部分服务不可用，但将继续启动应用...")
        # 如果需要严格检查，取消下面注释
        # raise SystemExit(f"以下服务连接失败：{', '.join(failed_services)}")
    else:
        myfastapi_logger.critical("✅ 所有服务端口和 host 连通性测试通过!")


__all__ = [
    "life_span"
]
if __name__ == '__main__':
    asyncio.run(test_database_connections())
