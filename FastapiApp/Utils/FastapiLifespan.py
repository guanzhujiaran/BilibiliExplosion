import asyncio
import contextlib
import importlib
import os
import socket
import time
from argparse import Namespace
from pathlib import Path

from fastapi import FastAPI
import httpx
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
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
        # 启动时预填充一轮用户列表
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

# 收集需要手动执行 alembic revision --autogenerate + upgrade head 的数据库
# 格式: {db_name: reason}
_MANUAL_FIX_REQUIRED: dict[str, str] = {}


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


# 这些错误表示迁移要执行的操作已经完成了（比如表/列/索引已存在）
_ALREADY_APPLIED_PATTERNS = (
    "already exists",
    "Duplicate column name",
    "Duplicate key name",
    "Can't DROP",
    "check that column/key exists",
)


def _upgrade_or_recover(
    alembic_cfg: AlembicConfig, db_name: str, *, allow_stamp_base: bool = False
) -> None:
    """
    执行 alembic upgrade head，遇到以下错误时自动恢复：

    1. "Can't locate revision" —— 数据库版本表引用了不存在的迁移文件
       - allow_stamp_base=True: stamp base 后重新 upgrade（全新数据库场景）
       - allow_stamp_base=False: 拒绝操作，提示手动修复

    2. "Table already exists" / "Duplicate column" 等 —— 迁移已在数据库层面
       完成但版本表未记录（常见于从生产库恢复/同步结构到开发库的场景）
       - 自动 stamp head，后续 autogenerate 会检测并补齐差异
    """
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        err_str = str(e)

        if "multiple heads" in err_str.lower():
            myfastapi_logger.warning(
                f"[{db_name}] 检测到多个 head 分支，尝试自动合并..."
            )
            try:
                command.merge(alembic_cfg, revisions="heads", message="merge heads")
                myfastapi_logger.info(f"[{db_name}] 分支已合并，正在重新 upgrade head...")
                command.upgrade(alembic_cfg, "head")
            except Exception as merge_e:
                myfastapi_logger.critical(
                    f"[{db_name}] 自动合并分支失败: {merge_e}\n"
                    f"  请手动执行: alembic -x db={db_name} merge heads"
                )
                raise
        elif "Can't locate revision" in err_str:
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
        elif any(pat in err_str for pat in _ALREADY_APPLIED_PATTERNS):
            myfastapi_logger.warning(
                f"[{db_name}] 数据库结构已存在（迁移已在外部完成），"
                f"自动 stamp head 跳过重复迁移..."
            )
            command.stamp(alembic_cfg, "head")
            myfastapi_logger.info(f"[{db_name}] stamp head 完成，后续将检查模型差异")
        else:
            raise


def _auto_detect_model_changes(
    alembic_cfg: AlembicConfig, db_name: str, old_head: str
) -> None:
    """
    在 upgrade head 之后，检测 ORM 模型是否还有未迁移的变更。
    如果有差异，自动生成新的迁移文件并立即执行 upgrade head 应用。

    这是对初始设计（只自动生成首次迁移）的增强（best-effort）：
    - 开发者修改了 ORM 模型但忘记手动运行 `alembic revision --autogenerate` 时，
      本次启动会自动补齐迁移并应用到数据库。
    - 任何异常都不会导致启动失败，只会记录日志。
    """
    myfastapi_logger.info(f"[{db_name}] 检查是否有未迁移的 ORM 模型变更...")
    try:
        command.revision(
            alembic_cfg,
            message="auto detect model changes",
            autogenerate=True,
        )
    except Exception as e:
        # autogenerate 无变更时 alembic 会抛出异常，这是正常情况
        err_msg = str(e)
        if "no changes" in err_msg.lower() or "nothing to" in err_msg.lower():
            myfastapi_logger.info(f"[{db_name}] 模型与数据库一致，无需迁移")
        else:
            myfastapi_logger.warning(
                f"[{db_name}] autogenerate 跳过 (可能已同步或无变更): {e}"
            )
        return

    # 检查是否产生了新的迁移文件
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        new_head = script.get_current_head()
    except Exception as e:
        myfastapi_logger.warning(
            f"[{db_name}] 无法读取迁移版本目录: {e}"
        )
        return

    if new_head is None or new_head == old_head:
        myfastapi_logger.info(f"[{db_name}] 模型与数据库一致，无需迁移")
        return

    # 有新迁移，检查是否安全可自动应用
    rev = _get_revision(alembic_cfg, new_head)
    rev_path = rev.path if rev else None

    if rev_path and _migration_has_destructive_ops(rev_path):
        # 包含 drop_column / drop_table 等操作，可能是 DB 有多余表/列（如从生产库复制），
        # 也可能是真的破坏性变更。不自动应用，交由后续 _repair_version_table_mismatch 处理。
        os.remove(rev_path)
        myfastapi_logger.warning(
            f"[{db_name}] autogenerate 检测到结构差异 (含 drop/modify)，"
            f"跳过自动迁移，后续一致性检查将尝试重新 autogenerate 修复"
        )
        _MANUAL_FIX_REQUIRED[db_name] = (
            f"{db_name} 存在含 drop_column / drop_table 的结构差异，需人工确认后手动执行迁移"
        )
        return

    # 检查迁移是否为空（无实际 schema/data 变更），空迁移会导致多余的 head 分支
    if rev_path and _migration_is_empty(rev_path):
        os.remove(rev_path)
        myfastapi_logger.info(
            f"[{db_name}] autogenerate 生成的迁移为空（无实际变更），已自动清理"
        )
        return

    myfastapi_logger.warning(
        f"[{db_name}] ⚠ 检测到未迁移的 ORM 模型变更！"
        f" 已自动生成迁移 {new_head}，正在应用到数据库..."
    )
    try:
        _upgrade_or_recover(alembic_cfg, db_name, allow_stamp_base=False)
        myfastapi_logger.warning(f"[{db_name}] 自动迁移 {new_head} 已成功应用")
    except Exception as e:
        # 应用失败：清理刚生成的迁移文件，避免残留导致下次启动也失败
        _cleanup_broken_migration(alembic_cfg, new_head, db_name)
        myfastapi_logger.critical(
            f"[{db_name}] 自动迁移 {new_head} 应用失败 (已清理残留文件) —— "
            f"请手动检查并执行: alembic -x db={db_name} upgrade head\n"
            f"  错误: {e}"
        )
        # 不 re-raise：自动检测是增强功能，不应阻塞启动


def _get_revision(
    alembic_cfg: AlembicConfig, revision_id: str
):
    """安全获取指定 revision 的 Script 对象，失败返回 None。"""
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        return script.get_revision(revision_id)
    except Exception:
        return None


def _extract_upgrade_content(content: str) -> str:
    """从迁移文件内容中提取 schema_upgrades() 函数体，排除 schema_downgrades()。
    
    避免将 downgrade 中的 drop_table/drop_column 误判为破坏性操作。
    """
    import re
    # 匹配 def schema_upgrades() 到下一个顶级 def（或文件末尾）
    m = re.search(r'def schema_upgrades\(\)[^:]*:(.*?)(?=\n(?:def |# end))', content, re.DOTALL)
    return m.group(1) if m else content


def _migration_has_destructive_ops(migration_path: str) -> bool:
    """检查迁移文件的 schema_upgrades() 中是否包含破坏性操作（drop_column / drop_table）。
    
    只检查 upgrade 函数体，不检查 downgrade（downgrade 必然会包含反向 drop 操作）。
    """
    try:
        with open(migration_path) as f:
            content = f.read()
        upgrade_body = _extract_upgrade_content(content)
        return (
            "op.drop_column" in upgrade_body
            or "op.drop_table" in upgrade_body
        )
    except OSError:
        return True  # 读不到文件就当有风险，不自动应用


def _migration_is_empty(migration_path: str) -> bool:
    """检查迁移文件的 schema_upgrades() 是否为空（无实际 schema/data 变更）。
    
    空迁移只包含 pass 语句，没有实际的 alter_column/add_column/create_table 等操作，
    这种迁移不应该保留，否则会造成多余的 head 分支。
    """
    try:
        with open(migration_path) as f:
            content = f.read()
        upgrade_body = _extract_upgrade_content(content)
        has_schema_ops = any(
            keyword in upgrade_body for keyword in (
                "op.create_table",
                "op.add_column",
                "op.alter_column",
                "op.create_index",
                "op.create_unique_constraint",
                "op.create_primary_key",
                "op.create_foreign_key",
                "op.bulk_insert",
                "op.execute",
            )
        )
        return not has_schema_ops
    except OSError:
        return False  # 读不到文件就当非空，保守处理


def _cleanup_broken_migration(
    alembic_cfg: AlembicConfig, bad_revision: str, db_name: str
) -> None:
    """删除自动生成但应用失败的迁移文件，避免残留干扰后续启动。"""
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        rev = script.get_revision(bad_revision)
        if rev and rev.path:
            os.remove(rev.path)
            myfastapi_logger.info(
                f"[{db_name}] 已删除失败的自动迁移文件: {rev.path}"
            )
    except Exception as cleanup_err:
        myfastapi_logger.warning(
            f"[{db_name}] 清理失败迁移文件时出错 (可忽略): {cleanup_err}"
        )


def _repair_version_table_mismatch(
    alembic_cfg: AlembicConfig, db_name: str
) -> None:
    """
    最终兜底检查：compare_metadata 确认模型与数据库完全一致。
    不一致时，如果 _auto_detect_model_changes 已因破坏性操作跳过，
    则标记为需手动处理；不修改任何 DB 版本表或迁移文件，保持干净状态
    以便用户直接执行:
        alembic -x db=xxx revision --autogenerate -m 'fix schema'
        alembic -x db=xxx upgrade head
    """
    myfastapi_logger.info(
        f"[{db_name}] 最终一致性检查：compare_metadata 确认模型与数据库完全匹配..."
    )

    target_metadata = _get_metadata_for_db(db_name)
    if target_metadata is None:
        myfastapi_logger.warning(f"[{db_name}] 无法获取模型 metadata，跳过一致性检查")
        return

    sync_url = _get_sync_url_for_db(db_name)
    if sync_url is None:
        return

    engine: Engine | None = None
    try:
        engine = create_engine(sync_url, echo=False)
        with engine.connect() as conn:
            migration_context = MigrationContext.configure(conn)
            diff = compare_metadata(migration_context, target_metadata)
    except Exception as e:
        myfastapi_logger.warning(
            f"[{db_name}] 一致性检查失败（不影响启动）: {e}"
        )
        return
    finally:
        if engine:
            engine.dispose()

    # 过滤 false positive：alembic_version_* 表永远不应被迁移系统修改
    def _is_alembic_version_diff(op_tuple) -> bool:
        if not isinstance(op_tuple, tuple) or len(op_tuple) < 2:
            return False
        op_type = op_tuple[0]
        if op_type == "remove_table" and hasattr(op_tuple[1], "name"):
            return str(op_tuple[1].name).startswith("alembic_version")
        if op_type in ("add_table",):
            return hasattr(op_tuple[1], "name") and str(op_tuple[1].name).startswith("alembic_version")
        return False

    _real_diff = [d for d in diff if not _is_alembic_version_diff(d)]

    if not _real_diff:
        myfastapi_logger.info(
            f"[{db_name}] ✅ 最终一致性检查通过，结构完全匹配"
            f"{' (忽略 alembic_version 表差异)' if len(diff) > len(_real_diff) else ''}"
        )
        return

    # 有真实结构差异 —— 如果 _auto_detect_model_changes 已标记为需手动处理
    # （含破坏性操作），不再重复尝试自动修复，保持 DB 版本表 / 迁移文件原样。
    if db_name in _MANUAL_FIX_REQUIRED:
        myfastapi_logger.warning(
            f"[{db_name}] ⚠ 检测到 {len(_real_diff)} 处结构差异，"
            f"因含 drop_column/drop_table 已标记为需手动修复"
        )
        for op in _real_diff:
            myfastapi_logger.warning(f"    - {op}")
        return

    # 不到达这里：如果 _auto_detect_model_changes 成功但因某种原因
    # compare_metadata 仍报告差异（autogenerate 与 compare_metadata 逻辑不一致）
    myfastapi_logger.warning(
        f"[{db_name}] ⚠ 检测到 {len(_real_diff)} 处结构差异，"
        f"但 autogenerate 未报告。差异详情:"
    )
    for op in _real_diff:
        myfastapi_logger.warning(f"    - {op}")
    _MANUAL_FIX_REQUIRED[db_name] = (
        f"{db_name} 存在 compare_metadata 差异但 autogenerate 未检测到，请手动排查"
    )


# 数据库名 -> CONFIG URL lambda，与 env.py 的 DATABASE_CONFIGS 保持一致
_DB_URL_MAP = {
    "biliopusdb": lambda: CONFIG.database.MYSQL.get_other_lot_URI,
    "bilidb": lambda: CONFIG.database.MYSQL.bili_db_URI,
    "bili_reserve": lambda: CONFIG.database.MYSQL.bili_reserve_URI,
    "dyndetail": lambda: CONFIG.database.MYSQL.dyn_detail_URI,
    "proxy_db": lambda: CONFIG.database.MYSQL.proxy_db_URI,
    "samsclub": lambda: CONFIG.database.MYSQL.sams_club_URI,
}

# 数据库名 -> ORM 模型导入路径，与 env.py 的 DATABASE_CONFIGS 保持一致
# 用于 _repair_version_table_mismatch 的 compare_metadata
_DB_MODEL_IMPORT_MAP = {
    "biliopusdb": "Service.GetOthersLotDyn.Sql.models",
    "bilidb": "Service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models",
    "bili_reserve": "Service.opus新版官方抽奖.预约抽奖.db.models",
    "dyndetail": "Service.GrpcModule.GrpcSrc.SQLObject.models",
    "proxy_db": "Utils.代理.数据库操作.SqlAlcheyObj.ProxyModel",
    "samsclub": "Service.samsclub.Sql.models",
}

# metadata 缓存，避免每次重复 import
_metadata_cache: dict[str, object] = {}


def _get_metadata_for_db(db_name: str):
    """获取指定数据库的 ORM 模型 metadata（带缓存）。"""
    if db_name in _metadata_cache:
        return _metadata_cache[db_name]

    import_path = _DB_MODEL_IMPORT_MAP.get(db_name)
    if import_path is None:
        myfastapi_logger.warning(f"[{db_name}] 未找到模型导入路径")
        return None

    try:
        mod = importlib.import_module(import_path)
        metadata = mod.Base.metadata
        _metadata_cache[db_name] = metadata
        return metadata
    except Exception as e:
        myfastapi_logger.warning(
            f"[{db_name}] 无法导入模型模块 '{import_path}': {e}"
        )
        return None


def _get_sync_url_for_db(db_name: str) -> str | None:
    """获取指定数据库的 pymysql 同步连接 URL。"""
    url_getter = _DB_URL_MAP.get(db_name)
    if url_getter is None:
        return None
    url = url_getter()
    return url.replace("mysql+aiomysql://", "mysql+pymysql://")


def _is_db_restored_from_external(alembic_cfg: AlembicConfig, db_name: str) -> bool:
    """
    检测数据库是否从外部恢复/同步，即：版本表 alembic_version_{db_name} 为空
    但数据库中已存在业务表（说明表结构是外部导入的，不需要重新执行历史迁移）。
    """
    # 优先从 alembic_cfg 读取 URL（env.py 可能已经设置了），
    # 若未设置则从 CONFIG 构建同步连接 URL
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    if not url and db_name in _DB_URL_MAP:
        url = _DB_URL_MAP[db_name]().replace("mysql+aiomysql://", "mysql+pymysql://")
    if not url:
        return False

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            version_table = f"alembic_version_{db_name}"
            inspector = inspect(engine)

            # 版本表不存在或为空
            if version_table not in inspector.get_table_names():
                has_version = False
            else:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {version_table}"))
                has_version = result.scalar() > 0

            if has_version:
                # 版本表有记录，正常迁移
                return False

            # 版本表为空，检查是否有业务表（排除 alembic_version 表）
            all_tables = inspector.get_table_names()
            business_tables = [
                t for t in all_tables if not t.startswith("alembic_version")
            ]
            if business_tables:
                myfastapi_logger.info(
                    f"[{db_name}] 数据库已有 {len(business_tables)} 张业务表"
                    f"但版本表为空，判定为外部恢复"
                )
                return True
    except Exception as e:
        myfastapi_logger.warning(f"[{db_name}] 检测数据库状态失败，将继续尝试迁移: {e}")
    finally:
        engine.dispose()

    return False


def _run_alembic_upgrade_head(db_name: str) -> None:
    """
    同步执行 alembic upgrade head（在线模式），针对指定数据库。

    逻辑：
    1. 没有迁移文件 + DB 为空（全新部署）
       → autogenerate=True 生成完整初始迁移 + upgrade head 应用
    2. 没有迁移文件 + DB 已有表（外部恢复）
       → 创建空基准迁移 + stamp head，然后继续走 3、4 检测模型差异
    3. 有迁移文件 → 正常 upgrade head，应用已有迁移
    4. upgrade 之后 → autogenerate 检测是否有未迁移的 ORM 模型变更，
       如有则自动生成新迁移并立即应用（防止开发者改模型后忘记 run revision）
    5. 最终兜底 → compare_metadata 确认模型与数据库完全一致，
       不一致时 stamp base + autogenerate + upgrade head 修复
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
        # 没有任何迁移文件 —— 分两种情况处理：
        #   a) 数据库已有表（外部创建或从备份恢复）→ 创建空迁移并 stamp head，
        #      然后继续走后续 auto_detect / repair 检测模型差异
        #   b) 数据库为空（全新部署）→ autogenerate 生成完整初始迁移并直接返回
        if _is_db_restored_from_external(alembic_cfg, db_name):
            myfastapi_logger.warning(
                f"[{db_name}] 没有迁移文件但数据库已有表，"
                f"创建空基准迁移并 stamp head..."
            )
            command.revision(
                alembic_cfg,
                message="initial migration",
                autogenerate=False,
            )
            script = ScriptDirectory.from_config(alembic_cfg)
            head_rev = script.get_current_head()
            command.stamp(alembic_cfg, "head")
            myfastapi_logger.info(
                f"[{db_name}] 空基准迁移已创建并 stamp head: {head_rev}，"
                f"将继续检查模型与数据库是否匹配..."
            )
            # 不 return，继续走下方 auto_detect / repair 检测 ORM 模型差异
        else:
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
            myfastapi_logger.info(
                f"[{db_name}] upgrade head（应用初始迁移对齐数据库结构）..."
            )
            # 新数据库，允许 stamp base 清孤立记录
            _upgrade_or_recover(alembic_cfg, db_name, allow_stamp_base=True)

            elapsed = time.time() - start_time
            myfastapi_logger.info(f"[{db_name}] 初始迁移完成，耗时: {elapsed:.2f}s")
            return

    # 有迁移文件，正常执行 upgrade
    myfastapi_logger.info(f"[{db_name}] 正在应用数据库迁移 (upgrade to head)...")

    # 如果 alembic_version 表为空但数据库已有实际表结构（比如从生产库恢复），
    # 直接 stamp head 跳过历史迁移，交由后续 autogenerate 补齐差异
    if _is_db_restored_from_external(alembic_cfg, db_name):
        myfastapi_logger.warning(
            f"[{db_name}] 检测到数据库结构已存在但版本表为空"
            f"（可能是从外部恢复/同步了数据库），跳过历史迁移直接 stamp head..."
        )
        command.stamp(alembic_cfg, "head")
    else:
        _upgrade_or_recover(alembic_cfg, db_name, allow_stamp_base=False)

    # ── 增强：检测是否有 ORM 模型变更尚未被任何迁移文件覆盖 ──
    _auto_detect_model_changes(alembic_cfg, db_name, head_rev)

    # ── 最终兜底：版本表说已同步，但实际 DB 结构仍落后于模型 ──
    # 典型场景：从生产库复制到开发库，版本表有记录但表结构是旧版本
    _repair_version_table_mismatch(alembic_cfg, db_name)

    elapsed = time.time() - start_time
    myfastapi_logger.info(f"[{db_name}] 数据库迁移完成，耗时: {elapsed:.2f}s")


async def run_alembic_migrations() -> None:
    """
    对所有数据库执行 alembic upgrade head。
    每个数据库通过 -x db=xxx 参数独立迁移。
    alembic 使用同步 SQLAlchemy，通过 to_thread 放入线程执行以避免阻塞事件循环。

    对于没有迁移文件的数据库:
      - DB 为空 → autogenerate 生成初始迁移 + upgrade head
      - DB 有表（外部恢复）→ 创建空基线 + stamp head，然后走 autogenerate 检测差异
    对于已有迁移文件的数据库，upgrade head 之后会:
      1. autogenerate 检测是否有未迁移的 ORM 模型变更并自动应用
      2. compare_metadata 最终一致性检查，不一致时 stamp base + autogenerate + upgrade
    """
    myfastapi_logger.critical("开始执行 alembic 数据库迁移（upgrade head）")
    _MANUAL_FIX_REQUIRED.clear()
    failed_dbs: list[str] = []
    for db_name in ALL_DB_NAMES:
        try:
            myfastapi_logger.info(f"  -> 迁移数据库: {db_name}")
            await asyncio.to_thread(_run_alembic_upgrade_head, db_name)
        except Exception as e:
            myfastapi_logger.critical(f"  -> {db_name} 迁移失败: {e}")
            failed_dbs.append(db_name)
            _MANUAL_FIX_REQUIRED[db_name] = f"{db_name} 迁移异常，请检查日志后手动执行"

    # ── 汇总：需要手动执行迁移的数据库 ──
    if _MANUAL_FIX_REQUIRED:
        lines = ["=" * 60,
                 "⚠⚠⚠  以下数据库需要手动执行 alembic 迁移  ⚠⚠⚠",
                 "=" * 60]
        for db_name, reason in _MANUAL_FIX_REQUIRED.items():
            cmd = (
                f"cd FastapiApp && uv run python -c \""
                f"from alembic.config import Config; from alembic import command; "
                f"from argparse import Namespace; "
                f"c=Config('alembic.ini'); "
                f"c.set_main_option('version_locations','alembic/versions/{db_name}'); "
                f"c.cmd_opts=Namespace(x=['db={db_name}']); "
                f"command.revision(c,message='fix schema',autogenerate=True); "
                f"command.upgrade(c,'head')\""
            )
            lines.append(f"  [{db_name}] {reason}")
            lines.append(f"    {cmd}")
        lines.append("=" * 60)
        for line in lines:
            myfastapi_logger.critical(line)

    if failed_dbs:
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
