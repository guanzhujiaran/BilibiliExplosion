from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import async_sessionmaker
from Utils.Common import log_sql_retry_wrapper
from Utils.SqlalchemyTool import sqlalchemy_session_factory, crawler_sqlalchemy_session_factory
from log.base_log import myfastapi_logger


class SqlHelperBase:
    """
    业务数据库操作基类
    使用业务连接池（pool_size=100, max_overflow=40）
    供 router/service 等业务代码使用
    """
    def __init__(self, mysql_db_url: str):
        async_session, engin = sqlalchemy_session_factory(mysql_db_url)
        self.async_session: async_sessionmaker = async_session
        self.engine = engin
        self.log = myfastapi_logger

    @log_sql_retry_wrapper()
    async def execute(self, stmt: Executable):
        async with self.async_session() as session:
            await session.execute(stmt)
            await session.commit()


class CrawlerSqlHelperBase:
    """
    爬虫数据库操作基类
    使用独立的爬虫连接池（pool_size=10, max_overflow=5）
    限制爬虫并发，防止影响业务请求的数据库连接
    """
    def __init__(self, mysql_db_url: str):
        async_session, engin = crawler_sqlalchemy_session_factory(mysql_db_url)
        self.async_session: async_sessionmaker = async_session
        self.engine = engin
        self.log = myfastapi_logger

    @log_sql_retry_wrapper()
    async def execute(self, stmt: Executable):
        async with self.async_session() as session:
            await session.execute(stmt)
            await session.commit()
