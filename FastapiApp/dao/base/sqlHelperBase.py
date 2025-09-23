from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import async_sessionmaker
from Utils.Common import log_sql_retry_wrapper
from Utils.SqlalchemyTool import sqlalchemy_session_factory
from log.base_log import myfastapi_logger


class SqlHelperBase:
    def __init__(self, MysqlDbUrl: str):
        self.async_session: async_sessionmaker = sqlalchemy_session_factory(MysqlDbUrl)
        self.log = myfastapi_logger

    @log_sql_retry_wrapper()
    async def execute(self, stmt: Executable):
        async with self.async_session() as session:
            await session.execute(stmt)
            await session.commit()
