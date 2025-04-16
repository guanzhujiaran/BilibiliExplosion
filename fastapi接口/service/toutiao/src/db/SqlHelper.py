from typing import Union

from fastapi接口.log.base_log import toutiao_api_logger
from fastapi接口.service.toutiao.src.Tools.Common.ZlibToos import BlobToStr
from fastapi接口.service.toutiao.src.ToutiaoSetting import CONFIG
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

from fastapi接口.service.toutiao.src.db.models import TFEEDDATA


def retry_on_error(delay=10):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while 1:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    toutiao_api_logger.exception(
                        f"An error occurred: {e}. Retrying in {delay} seconds.\nNow retry times:{retries}")
                    await asyncio.sleep(delay)
                    retries += 1

        return wrapper

    return decorator


class SqlHelperSpaceFeedDataDb:
    def __init__(self):
        SQLITE_URI = CONFIG.DBSetting.AIO_SpaceFeedDataDb
        engine = create_async_engine(
            SQLITE_URI,
            echo=False,  # 是否打印sql日志
            future=True
        )
        self.AsyncSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False,
                                         autoflush=True)  # 每次操作的时候将session实例化一下

    @retry_on_error()
    async def add_feed_data(self, data: TFEEDDATA):
        async with self.AsyncSession() as session:
            async with session.begin():
                session.add(data)
                await session.commit()

    @retry_on_error()
    async def get_feed_data_by_id(self, id_: int) -> Union[TFEEDDATA, None]:
        async with self.AsyncSession() as session:
            stmt = select(TFEEDDATA).where(TFEEDDATA.id == id_)
            result = await session.execute(stmt)
            return result.scalars().first()

    @retry_on_error()
    async def update_feed_data(self, id_: int, new_data: TFEEDDATA) -> None:
        async with self.AsyncSession() as session:
            stmt = update(TFEEDDATA).where(TFEEDDATA.id == id_).values(new_data)
            await session.execute(stmt)
            await session.commit()

    @retry_on_error()
    async def is_id_exists(self, id_: int) -> bool:
        async with self.AsyncSession() as session:
            stmt = select(TFEEDDATA.id).where(TFEEDDATA.id == id_)
            result = await session.execute(stmt)
            return bool(result.scalar_one_or_none())


async def __test():
    import json
    a = SqlHelperSpaceFeedDataDb()
    b: TFEEDDATA = await a.get_feed_data_by_id(7335747280924132148)
    print(b.zippedData)
    c = BlobToStr(b.zippedData)
    print(c)
    print(json.loads(c))


if __name__ == '__main__':
    asyncio.run(__test())
