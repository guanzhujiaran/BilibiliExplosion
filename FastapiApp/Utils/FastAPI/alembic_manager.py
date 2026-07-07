# -*- coding: utf-8 -*-
"""Schema 一致性校验：启动时检查 DB 表结构是否与 ORM 模型一致，不一致则拒绝启动。"""

import asyncio
import importlib
import re
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from CONFIG import CONFIG
from log.base_log import myfastapi_logger


# 项目根目录（alembic.ini 所在位置），确保运行 alembic 命令时能正确导入 Service / CONFIG
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# ================================================================
# 公开入口
# ================================================================

async def run_alembic_upgrade_head() -> bool:
    """对所有数据库执行一次 alembic upgrade head（增量迁移），全部成功返回 True"""
    myfastapi_logger.critical("===== 开始执行 alembic upgrade head =====")
    success = True
    alembic_ini = _project_root / "alembic.ini"
    for db_name in _DB_URL_MAP:
        try:
            cfg = AlembicConfig(str(alembic_ini), ini_section=db_name)
            myfastapi_logger.info(f"[{db_name}] 正在执行 alembic upgrade head...")
            # env.py 内部会 asyncio.run，需在独立线程中执行以避免与当前事件循环冲突
            await asyncio.to_thread(command.upgrade, cfg, "head")
            myfastapi_logger.info(f"[{db_name}] alembic upgrade head 完成")
        except Exception as e:
            myfastapi_logger.error(f"[{db_name}] alembic upgrade head 失败: {e}")
            success = False
    if success:
        myfastapi_logger.critical("===== alembic upgrade head 全部执行完成 =====")
    else:
        myfastapi_logger.error("===== 部分数据库 alembic upgrade head 执行失败 =====")
    return success


async def check_schemas() -> bool:
    """检查所有数据库的 Schema 是否与模型一致，不一致返回 False"""
    return await _check_all_schemas_match()


# ================================================================
# Schema 一致性校验
# ================================================================

def _normalize_column_type(col_type_str: str) -> str:
    """将 SQLAlchemy 列类型字符串归一化，便于跨驱动比较"""
    s = col_type_str.upper().strip()
    s = re.sub(r"\s+COLLATE\s+.*$", "", s)
    s = re.sub(r"\(.*\)", "", s)
    aliases = {
        "LONGTEXT": "TEXT", "MEDIUMTEXT": "TEXT", "TINYTEXT": "TEXT",
        "INTEGER": "INT",
        "TIMESTAMP": "DATETIME",
        "BOOL": "TINYINT", "BOOLEAN": "TINYINT",
    }
    return aliases.get(s, s)


def _is_type_compatible(model_type: str, db_type: str) -> bool:
    """判断两个归一化后的类型是否兼容"""
    if model_type == db_type:
        return True
    text_types = {"VARCHAR", "CHAR", "TEXT", "LONGTEXT", "MEDIUMTEXT", "TINYTEXT"}
    if model_type in text_types and db_type in text_types:
        return True
    int_types = {"TINYINT", "SMALLINT", "INT", "BIGINT", "INTEGER"}
    if model_type in int_types and db_type in int_types:
        return True
    if {model_type, db_type} <= {"DATETIME", "TIMESTAMP"}:
        return True
    if model_type == "JSON" and db_type in ("TEXT", "LONGTEXT"):
        return True
    return False


async def _check_single_db_schema(db_key: str) -> tuple[list[str], list[str]]:
    """
    返回 (critical, non_critical)
    critical: 缺失表、缺失列、类型不匹配
    non_critical: DB 多余列
    """
    critical: list[str] = []
    non_critical: list[str] = []

    try:
        mod = importlib.import_module(_DB_MODEL_IMPORT_MAP[db_key])
    except Exception as e:
        return [f"{db_key}: 无法导入模型模块 {_DB_MODEL_IMPORT_MAP[db_key]}: {e}"], []

    metadata = mod.Base.metadata
    db_url: str = _DB_URL_MAP[db_key]()
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as connection:

            def _inspect_sync(sync_conn):
                inspector = inspect(sync_conn)
                db_tables = set(inspector.get_table_names())
                model_tables = set(metadata.tables.keys())

                # 模型中声明但 DB 不存在的表
                missing_tables = model_tables - db_tables
                if missing_tables:
                    critical.append(f"模型中声明但数据库中不存在的表: {sorted(missing_tables)}")

                for table_name in sorted(model_tables & db_tables):
                    db_cols = {
                        col["name"]: _normalize_column_type(str(col["type"]))
                        for col in inspector.get_columns(table_name)
                    }
                    model_cols = {
                        col.name: _normalize_column_type(str(col.type))
                        for col in metadata.tables[table_name].columns
                    }
                    mcs, dcs = set(model_cols), set(db_cols)
                    # 模型中存在但 DB 缺少的列
                    for col in sorted(mcs - dcs):
                        critical.append(f"{table_name}: 模型中存在但DB缺少列 '{col}' ({model_cols[col]})")
                    # DB 中存在但模型未声明的列
                    for col in sorted(dcs - mcs):
                        non_critical.append(f"{table_name}: DB中存在但模型中未声明的列 '{col}' ({db_cols[col]})")
                    # 类型不匹配
                    for col in sorted(mcs & dcs):
                        mt, dt = model_cols[col], db_cols[col]
                        if mt != dt and not _is_type_compatible(mt, dt):
                            critical.append(f"{table_name}.{col}: 类型不匹配 模型={mt}, DB={dt}")

            await connection.run_sync(_inspect_sync)
    except Exception as e:
        return [f"无法连接数据库: {e}"], []
    finally:
        await engine.dispose()

    return critical, non_critical


async def _check_all_schemas_match() -> bool:
    """遍历所有数据库，关键差异返回 False 阻塞启动"""
    myfastapi_logger.critical("===== 开始 Schema 一致性校验 =====")

    all_critical: dict[str, list[str]] = {}
    all_non_critical: dict[str, list[str]] = {}

    try:
        for db_key in _DB_URL_MAP:
            critical, non_critical = await _check_single_db_schema(db_key)
            if critical:
                all_critical[db_key] = critical
            if non_critical:
                all_non_critical[db_key] = non_critical
    except Exception as e:
        myfastapi_logger.critical(f"Schema 校验异常: {e}")
        return False

    if all_non_critical:
        myfastapi_logger.warning("=" * 60)
        myfastapi_logger.warning("⚠ Schema 非关键差异 (不阻塞启动):")
        for db_key, warns in all_non_critical.items():
            myfastapi_logger.warning(f"--- {db_key} ---")
            for w in warns:
                myfastapi_logger.warning(f"  {w}")
        myfastapi_logger.warning("=" * 60)

    if all_critical:
        myfastapi_logger.error("=" * 60)
        myfastapi_logger.error("✗ Schema 不一致，拒绝启动:")
        for db_key, warns in all_critical.items():
            myfastapi_logger.error(f"--- {db_key} ---")
            for w in warns:
                myfastapi_logger.error(f"  {w}")
        myfastapi_logger.error("=" * 60)
        myfastapi_logger.error("请先执行 alembic upgrade head 同步 Schema")
        return False

    myfastapi_logger.critical("===== Schema 一致性校验全部通过 =====")
    return True


# ---- 配置 ----

_DB_URL_MAP = {
    "biliopusdb": lambda: CONFIG.database.MYSQL.get_other_lot_URI,
    "bilidb": lambda: CONFIG.database.MYSQL.bili_db_URI,
    "bili_reserve": lambda: CONFIG.database.MYSQL.bili_reserve_URI,
    "dyndetail": lambda: CONFIG.database.MYSQL.dyn_detail_URI,
    "proxy_db": lambda: CONFIG.database.MYSQL.proxy_db_URI,
    "samsclub": lambda: CONFIG.database.MYSQL.sams_club_URI,
}

_DB_MODEL_IMPORT_MAP = {
    "biliopusdb": "Service.GetOthersLotDyn.Sql.models",
    "bilidb": "Service.opus新版官方抽奖.活动抽奖.话题抽奖.db.models",
    "bili_reserve": "Service.opus新版官方抽奖.预约抽奖.db.models",
    "dyndetail": "Service.GrpcModule.GrpcSrc.SQLObject.models",
    "proxy_db": "Utils.代理.数据库操作.SqlAlcheyObj.ProxyModel",
    "samsclub": "Service.samsclub.Sql.models",
}
