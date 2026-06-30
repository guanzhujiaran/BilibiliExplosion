import asyncio
import contextlib
import os
import socket
import time
from argparse import Namespace
from pathlib import Path

from fastapi import FastAPI
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

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

    # 执行 alembic 数据库迁移（upgrade head）
    await run_alembic_migrations()

    # 测试各个服务的端口和 host 连通性
    await test_service_ports_and_hosts()
    
    # 检查 milvus 数据库集合
    await asyncio.sleep(3)  # 等 HTTP server ready
    myfastapi_logger.critical("检查 milvus 数据库集合")
    await milvus_sql_helper.ensure_collection_exists()  # 必须执行
    myfastapi_logger.critical("重试未处理的消息")
    await BiliLotDataPublisher.retry_pending_messages()  # 重试未处理的消息
    # RPC handler 由 mq_controller.py 末尾导入 lottery_data 模块触发 @rpc_subscriber 注册
    # broker 连接由 FastAPI 通过 app.include_router(MqController.router) 自动管理
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
            myfastapi_logger.info(f"正在测试数据库 '{db_name}' 连接...")
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
            raise SystemExit(f"数据库 '{db_name}' 连接失败：{e}") from e


# 所有需要执行迁移的数据库名称列表，与 alembic/env.py 中 DATABASE_CONFIGS 保持一致
ALL_DB_NAMES = [
    "biliopusdb",
    "bilidb",
    "bili_reserve",
    "dyndetail",
    "proxy_db",
    "samsclub",
]


def _get_alembic_config(alembic_ini_path: str | None = None) -> AlembicConfig:
    """
    获取 Alembic 配置对象（参考 RPA-Browser 的写法）

    Args:
        alembic_ini_path: alembic.ini 文件路径，默认为项目根目录下的 alembic.ini

    Returns:
        Alembic Config 对象
    """
    if alembic_ini_path is None:
        project_root = Path(__file__).resolve().parent.parent
        alembic_ini_path = str(project_root / "alembic.ini")

    alembic_cfg = AlembicConfig(alembic_ini_path)

    # 确保 script_location 被正确设置
    script_location = alembic_cfg.get_main_option("script_location")
    if not script_location:
        project_root = Path(__file__).resolve().parent.parent
        script_location = str(project_root / "alembic")
        alembic_cfg.set_main_option("script_location", script_location)
    return alembic_cfg


def _upgrade_or_recover(
    alembic_cfg: AlembicConfig, db_name: str, *, allow_stamp_base: bool = False
) -> None:
    """
    执行 alembic upgrade head，遇到 "Can't locate revision" 错误时处理。

    allow_stamp_base=True（仅限全新数据库，无迁移文件场景）：
        数据库可能残留之前的孤立版本记录，stamp base 清空后重新 upgrade 是安全的，
        因为新创建的空迁移只会 stamp 不会执行实际建表 SQL。

    allow_stamp_base=False（已有迁移文件但部分被误删）：
        拒绝自动 stamp base —— 这会丢失所有版本历史，导致现有迁移全部
        重新执行，大概率因 "Table already exists" 失败。
        应手动从 git 恢复被删文件，或手动清理 alembic_version 表中对应的记录。
    """
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        if "Can't locate revision" in str(e):
            if allow_stamp_base:
                myfastapi_logger.warning(
                    f"[{db_name}] 数据库存在孤立的版本记录，正在重置基线并重试..."
                )
                command.stamp(alembic_cfg, "base")
                command.upgrade(alembic_cfg, "head")
            else:
                myfastapi_logger.error(
                    f"[{db_name}] 数据库引用了不存在的迁移版本！\n"
                    f"  错误: {e}\n"
                    f"  可能原因: versions/{db_name}/ 中的某些迁移文件被误删。\n"
                    f"  修复方法:\n"
                    f"    1. 用 git 恢复被删文件: git checkout -- versions/{db_name}/\n"
                    f"    2. 如果无法恢复，手动连接数据库删除 alembic_version_{db_name} 表中"
                    f"对应记录，然后用 alembic -x db={db_name} stamp head 重标记"
                )
                raise RuntimeError(
                    f"[{db_name}] 迁移文件缺失，请从 git 恢复或手动处理。错误: {e}"
                ) from e
        else:
            raise


def _run_alembic_upgrade_head(db_name: str) -> None:
    """
    同步执行 alembic upgrade head（在线模式），针对指定数据库。

    逻辑：
    1. 没有迁移文件 -> 自动生成初始迁移（autogenerate=True，检测 ORM 与 DB 差异）
    2. 有迁移文件 -> 正常 upgrade head
    """
    start_time = time.time()

    alembic_cfg = _get_alembic_config()
    # 通过 -x db=xxx 传递给 env.py，使其选择对应的数据库配置
    alembic_cfg.cmd_opts = Namespace(x=[f"db={db_name}"])

    # 在创建 ScriptDirectory 之前，先设置每个数据库独立的 version_locations
    # 避免从 versions/ 根目录错误加载不属于当前数据库的迁移文件
    # （每个数据库的迁移文件存放在 versions/{db_name}/ 子目录）
    project_root = Path(__file__).resolve().parent.parent
    version_path = str(project_root / "alembic" / "versions" / db_name)
    alembic_cfg.set_main_option("version_locations", version_path)

    myfastapi_logger.info(f"[{db_name}] 开始检查数据库迁移状态...")

    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()

    if head_rev is None:
        # 没有任何迁移文件，自动生成初始基准迁移
        # autogenerate=True 会检测 ORM 模型与实际数据库之间的差异，
        # 生成 ALTER/CREATE 语句来对齐两者（env.py 中已过滤旧的 alembic_version 表）
        myfastapi_logger.warning(
            f"[{db_name}] 没有可用的迁移文件，自动生成初始迁移（autogenerate）..."
        )
        command.revision(
            alembic_cfg,
            message="initial migration",
            autogenerate=True,
        )
        # 重新加载 script 获取新生成的 head
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        myfastapi_logger.info(f"[{db_name}] 初始迁移已创建，head: {head_rev}")

        # upgrade head：应用初始迁移，对齐模型与数据库结构
        myfastapi_logger.info(f"[{db_name}] upgrade head（应用初始迁移对齐数据库结构）...")
        # 新数据库，空迁移，允许 stamp base 清孤立记录
        _upgrade_or_recover(alembic_cfg, db_name, allow_stamp_base=True)

        elapsed = time.time() - start_time
        myfastapi_logger.info(f"[{db_name}] 初始迁移完成，耗时: {elapsed:.2f}s")
        return

    # 有迁移文件，正常执行 upgrade
    myfastapi_logger.info(f"[{db_name}] 正在应用数据库迁移 (upgrade to head)...")
    # 有迁移文件场景，不允许自动 stamp base（会丢失版本历史）
    _upgrade_or_recover(alembic_cfg, db_name, allow_stamp_base=False)

    elapsed = time.time() - start_time
    myfastapi_logger.info(f"[{db_name}] 数据库迁移完成，耗时: {elapsed:.2f}s")


async def run_alembic_migrations() -> None:
    """
    对所有数据库执行 alembic upgrade head。
    每个数据库通过 -x db=xxx 参数独立迁移。
    alembic 使用同步 SQLAlchemy，通过 to_thread 放入线程执行以避免阻塞事件循环。

    对于没有迁移文件的数据库，会自动生成初始基线迁移并 stamp head。
    """
    myfastapi_logger.critical("开始执行 alembic 数据库迁移（upgrade head）")
    failed_dbs: list[str] = []
    for db_name in ALL_DB_NAMES:
        try:
            myfastapi_logger.info(f"  -> 迁移数据库: {db_name}")
            await asyncio.to_thread(_run_alembic_upgrade_head, db_name)
        except Exception as e:
            myfastapi_logger.critical(f"  -> {db_name} 迁移失败: {e}")
            failed_dbs.append(db_name)

    if failed_dbs:
        myfastapi_logger.critical(
            f"以下数据库迁移失败，应用将退出: {', '.join(failed_dbs)}"
        )
        raise SystemExit(f"数据库迁移失败: {', '.join(failed_dbs)}")
    else:
        myfastapi_logger.critical("所有数据库 alembic 迁移完成")


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
