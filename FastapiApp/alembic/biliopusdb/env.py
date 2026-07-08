# -*- coding: utf-8 -*-
"""
biliopusdb (第三方抽奖动态库) Alembic 异步环境配置
"""

import asyncio
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# ---- sys.path ----
_current_dir = Path(__file__).resolve().parent  # alembic/biliopusdb/
_fastapi_root = _current_dir.parent.parent       # FastapiApp/
sys.path.insert(0, str(_fastapi_root))

# ---- 目标元数据 ----
from Service.GetOthersLotDyn.Sql.models import Base
target_metadata = Base.metadata

# ---- 数据库 URL ----
from CONFIG import CONFIG
_DB_URL: str = CONFIG.database.MYSQL.get_other_lot_URI
# from sqlalchemy import *
# from sqlalchemy.schema import *
# engine = create_engine(_DB_URL.replace('aiomysql','pymysql'))
# target_metadata = MetaData()
# target_metadata.reflect(engine)
# ---- Alembic Config ----
config = context.config
config.set_main_option("sqlalchemy.url", _DB_URL)


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = create_async_engine(_DB_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_offline() -> None:
    url = _DB_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
