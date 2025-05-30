from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from CONFIG import CONFIG


def sqlalchemy_model_2_dict(instance):
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


def sqlalchemy_session_factory(dburl: str):
    engine = create_async_engine(
        dburl,
        **CONFIG.sql_alchemy_config.engine_config
    )
    session = async_sessionmaker(
        engine,
        **CONFIG.sql_alchemy_config.session_config
    )  # 每次操作的时候将session实例化一下
    return session
