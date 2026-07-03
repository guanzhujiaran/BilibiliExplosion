from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import async_sessionmaker
from Utils.通用.Common import log_sql_retry_wrapper
from Utils.数据库.SqlalchemyTool import sqlalchemy_session_factory
from log.base_log import myfastapi_logger


class SqlHelperBase:
    """
    数据库操作基类
    每次实例化都会创建独立的 Engine 和 Session，实现连接池隔离
    """
    def __init__(self, mysql_db_url: str, is_crawler: bool = False):
        async_session, engin = sqlalchemy_session_factory(mysql_db_url, is_crawler=is_crawler)
        self.async_session: async_sessionmaker = async_session
        self.engine = engin
        self.log = myfastapi_logger

    @log_sql_retry_wrapper()
    async def execute(self, stmt: Executable):
        async with self.async_session() as session:
            await session.execute(stmt)
            await session.commit()
