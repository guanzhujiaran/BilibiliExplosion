# -*- coding: utf-8 -*-
"""
dyndetail (动态详情库) Alembic 异步环境配置
"""
import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

_current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_current_dir.parent.parent))

from Service.GrpcModule.GrpcSrc.SQLObject.models import Base
target_metadata = Base.metadata

from CONFIG import CONFIG
_DB_URL: str = CONFIG.database.MYSQL.dyn_detail_URI
# from sqlalchemy import *
# from sqlalchemy.schema import *
# engine = create_engine(_DB_URL.replace('aiomysql','pymysql'))
# target_metadata = MetaData()
# target_metadata.reflect(engine)


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
