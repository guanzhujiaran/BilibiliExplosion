from typing import Any, Dict

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from CONFIG import CONFIG


def sqlalchemy_model_2_dict(instance) -> dict:
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


# 业务连接池缓存
AsyncSessionLocal: Dict[str, Any] = dict()
# 爬虫连接池缓存
CrawlerSessionLocal: Dict[str, Any] = dict()


def sqlalchemy_session_factory(dburl: str) -> tuple[async_sessionmaker, AsyncEngine]:
    """
    创建并返回一个SQLAlchemy异步会话工厂（业务连接池）

    Args:
        dburl (str): 数据库连接URL

    Returns:
        async_sessionmaker: 配置好的SQLAlchemy异步会话工厂，使用时需要实例化
    """
    if AsyncSessionLocal.get(dburl) is not None:
        return AsyncSessionLocal.get(dburl)
    engine = create_async_engine(dburl, **CONFIG.sql_alchemy_config.engine_config)
    session = async_sessionmaker(
        engine, **CONFIG.sql_alchemy_config.session_config
    )  # 每次操作的时候将session实例化一下
    AsyncSessionLocal.update({dburl: (session, engine)})
    return session, engine


def crawler_sqlalchemy_session_factory(dburl: str) -> tuple[async_sessionmaker, AsyncEngine]:
    """
    创建并返回一个SQLAlchemy异步会话工厂（爬虫专用小池）

    使用独立的连接池配置，限制爬虫并发，防止影响业务请求

    Args:
        dburl (str): 数据库连接URL

    Returns:
        tuple[async_sessionmaker, AsyncEngine]: 配置好的会话工厂和引擎
    """
    cache_key = f"crawler_{dburl}"
    if CrawlerSessionLocal.get(cache_key) is not None:
        return CrawlerSessionLocal.get(cache_key)
    engine = create_async_engine(dburl, **CONFIG.crawler_sql_alchemy_config.engine_config)
    session = async_sessionmaker(
        engine, **CONFIG.crawler_sql_alchemy_config.session_config
    )
    CrawlerSessionLocal.update({cache_key: (session, engine)})
    return session, engine
