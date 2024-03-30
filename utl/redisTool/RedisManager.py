import traceback

from typing import Union
from datetime import timedelta
from redis import asyncio as redis
from enum import Enum
from CONFIG import CONFIG


def retry(func: callable):
    def wrapper(*args, **kwargs):
        while 1:
            try:
                return func(*args, **kwargs)
            except:
                traceback.print_exc()

    return wrapper


class RedisManagerBase:
    class RedisMap(str, Enum):
        pass

    def __init__(self,host= CONFIG.database.proxyRedis.host,
                 port= CONFIG.database.proxyRedis.port,
                 db= CONFIG.database.proxyRedis.db
                 ):
        self.host =host
        self.port =port
        self.db =db
        self.pool = redis.ConnectionPool.from_url(
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True')

    @retry
    async def _get(self, key):
        """
        传入多个参数则使用pipeline批量获取
        :param key:
        :return:
        """
        async with redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for k in key:
                    await pipe.get(k)
                async with r.lock('Lock_' + key[0], timeout=5):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + key, timeout=5):
                    return await r.get(key)

    @retry
    async def _set(self, key, value):
        async with redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    await pipe.set(key[idx], value[idx])
                async with r.lock('Lock_' + key[0], timeout=5):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + key, timeout=5):
                    return await r.set(key, value)

    @retry
    async def _setex(self, key, value, _time: Union[int, timedelta]):
        async with redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    await pipe.setex(name=key[idx], value=value[idx], time=_time)
                async with r.lock('Lock_' + key[0], timeout=5):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + key, timeout=5):
                    return await r.setex(name=key, value=value, time=_time)
