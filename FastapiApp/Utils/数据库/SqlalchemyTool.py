from typing import Any, Dict

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from CONFIG import CONFIG


def sqlalchemy_model_2_dict(instance) -> dict:
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


def sqlalchemy_session_factory(dburl: str, is_crawler: bool = False) -> tuple[async_sessionmaker, AsyncEngine]:
    """
    创建并返回一个SQLAlchemy异步会话工厂
    
    Args:
        dburl (str): 数据库连接URL
        is_crawler (bool): 是否为爬虫专用连接池（使用较小的连接数）

    Returns:
        tuple[async_sessionmaker, AsyncEngine]: 配置好的会话工厂和引擎
    """
    config = CONFIG.crawler_sql_alchemy_config if is_crawler else CONFIG.sql_alchemy_config
    engine = create_async_engine(dburl, **config.engine_config)
    session = async_sessionmaker(
        engine, **config.session_config
    )
    return session, engine
