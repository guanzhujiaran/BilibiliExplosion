import asyncio
import time
import traceback
from typing import Union, Any, List, Callable
from datetime import timedelta
from redis import asyncio as redis
from enum import Enum
from CONFIG import CONFIG
import redis as sync_redis

from fastapi接口.log.base_log import redis_logger


def retry(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                redis_logger.exception(e)
                await asyncio.sleep(3)

    return wrapper


def sync_retry(func):
    def wrapper(*args, **kwargs):
        while 1:
            try:
                return func(*args, **kwargs)
            except:
                traceback.print_exc()
                time.sleep(3)

    return wrapper


class SyncRedisManagerBase:
    """
    同步的Redis管理基类
    RedisMap: 枚举Redis的key
    """

    class RedisMap(str, Enum):
        pass

    def __init__(self, host: str = CONFIG.database.proxyRedis.host,
                 port: int = CONFIG.database.proxyRedis.port,
                 db: int = CONFIG.database.proxyRedis.db
                 ):
        self.host = host
        self.port = port
        self.db = db
        self.pool = sync_redis.connection.ConnectionPool.from_url(
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True')
        self.RedisTimeout = 30

    @sync_retry
    def _get(self, key: Union[Any, List[Any]]):
        """
        传入多个参数则使用pipeline批量获取
        :param key:
        :return:
        """
        with sync_redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for k in key:
                    pipe.get(k)
                with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return pipe.execute()
            else:
                with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return r.get(key)

    @sync_retry
    def _set(self, key: Union[Any, List[Any]], value: Union[Any, List[Any]]):
        with sync_redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    pipe.set(key[idx], value[idx])
                with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return pipe.execute()
            else:
                with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return r.set(key, value)

    @sync_retry
    def _setex(self, key: Union[Any, List[Any]], value: Union[Any, List[Any]], _time: Union[int, timedelta]):
        with sync_redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    pipe.setex(name=key[idx], value=value[idx], time=_time)
                with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return pipe.execute()
            else:
                with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return r.setex(name=key, value=value, time=_time)

    @sync_retry
    def exists(self, key: Any) -> int:
        """

        :param key:
        :return: 返回1存在 0不存在
        """
        with sync_redis.Redis(connection_pool=self.pool) as r:
            return r.exists(key)


class RedisManagerBase:
    class RedisMap(str, Enum):
        pass

    def __init__(self, host: str = CONFIG.database.proxyRedis.host,
                 port: int = CONFIG.database.proxyRedis.port,
                 db: int = CONFIG.database.proxyRedis.db
                 ):
        self.host = host
        self.port = port
        self.db = db
        self.pool = redis.ConnectionPool.from_url(
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True')
        self.RedisTimeout = 30

    # region 字符串操作
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
                async with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return await r.get(key)

    @retry
    async def _set(self, key, value):
        async with redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    await pipe.set(key[idx], value[idx])
                async with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return await r.set(key, value)

    @retry
    async def _setex(self, key, value, _time: Union[int, timedelta]):
        async with redis.Redis(connection_pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    await pipe.setex(name=key[idx], value=value[idx], time=_time)
                async with r.lock('Lock_' + str(key[0]), timeout=self.RedisTimeout):
                    return await pipe.execute()
            else:
                async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                    return await r.setex(name=key, value=value, time=_time)

    # endregion

    # region 集合Set操作
    @retry
    async def _sadd(self, set_name, val):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.sadd(set_name, val)

    @retry
    async def _sisexist(self, set_name, val):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.sismember(set_name, val)

    @retry
    async def _sget_rand(self, set_name):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return r.srandmember(set_name)

    @retry
    async def _scount(self, set_name):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.scard(set_name)

    @retry
    async def _sget_all(self, set_name):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.smembers(set_name)

    @retry
    async def _srem(self, set_name, *val):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.srem(set_name, *val)

    # endregion

    # region 有序集合ZSet操作

    @retry
    async def _z_exist(self, key, element):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zscore(key, element) is not None

    @retry
    async def _zadd(self, key, mapping: dict):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zadd(key, mapping,)

    @retry
    async def _zscore_change(self, key, element, score_change: int):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zincrby(key, score_change, element)

    @retry
    async def _zget_range(self, key, start: int, end: int, num: int = None, offset: int = None):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zrange(key, start, end, num=num, offset=offset)

    @retry
    async def _zget_range_by_score(self, key, min_score: int, max_score: int, start: int = None, num: int = None):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zrangebyscore(key, min_score, max_score, start=start, num=num, )

    @retry
    async def _zdel_elements(self, key, *elements_to_remove):
        if not elements_to_remove:
            return
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zrem(key, *elements_to_remove)

    @retry
    async def _zdel_range(self, key, start: int, end: int):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zremrangebyrank(key, start, end)

    # endregion

    @retry
    async def _hmset(self, name, field_values):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(name), timeout=self.RedisTimeout):
                return await r.hset(name=name, mapping=field_values)

    @retry
    async def _hmgetall(self, name, ):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(name), timeout=self.RedisTimeout):
                return await r.hgetall(name=name)

    @retry
    async def _hmdel(self, name):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(name), timeout=self.RedisTimeout):
                return await r.delete(name)
