from typing import Any, Dict

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from CONFIG import CONFIG


def sqlalchemy_model_2_dict(instance) -> dict:
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


AsyncSessionLocal: Dict[str, Any] = dict()


def sqlalchemy_session_factory(dburl: str) -> tuple[async_sessionmaker, AsyncEngine]:
    """
    创建并返回一个SQLAlchemy异步会话工厂

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
