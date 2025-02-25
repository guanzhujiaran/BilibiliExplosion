import asyncio
import random
import time
import traceback
from typing import Union, Any, List, Callable
from datetime import timedelta
from redis import asyncio as redis
from enum import Enum
from redis.typing import KeyT
from CONFIG import CONFIG
import redis as sync_redis
from fastapi接口.log.base_log import redis_logger

_sem = asyncio.Semaphore(1024)

def retry(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while 1:
            async with _sem:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    redis_logger.exception(e)
                    await asyncio.sleep(30)

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
    """
    异步版本redis基类
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
        self.pool = redis.ConnectionPool.from_url(
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True')
        self.RedisTimeout = 30

    @retry
    async def __get_keys_with_prefix(self, prefix, count=100) -> List[Any]:
        cursor = '0'
        matched_keys = []
        async with redis.Redis(connection_pool=self.pool) as r:
            while cursor:
                cursor, keys = await r.scan(cursor=cursor, match=f'{prefix}:*',
                                            count=count)
                if keys:
                    matched_keys.extend(keys)

        return matched_keys

    async def _del_keys_with_prefix(self, prefix: str):
        keys = await self.__get_keys_with_prefix(prefix)
        if not keys:
            return []
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.pipeline() as pipe:
                for key in keys:
                    await pipe.delete(key)
                values = await pipe.execute()
        return values

    @retry
    async def _get_all_val_with_prefix(self, prefix: str) -> List[Any]:
        keys = await self.__get_keys_with_prefix(prefix)
        if not keys:
            return []
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.pipeline() as pipe:
                for key in keys:
                    await pipe.get(key)
                values = await pipe.execute()
        return values

    @retry
    async def exists(self, key: Any) -> int:
        """

        :param key:
        :return: 返回1存在 0不存在
        """
        async with redis.Redis(connection_pool=self.pool) as r:
            return await r.exists(key)

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
                async with r.pipeline() as pipe:
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
    async def _del(self, *set_name: KeyT):
        """
        Delete one or more keys specified by ``names``
        :param set_name:
        :return: 0-删除失败 1-删除成功
        """
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(set_name), timeout=self.RedisTimeout):
                return await r.delete(*set_name)

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
                return await r.zadd(key, mapping, )

    @retry
    async def _zscore_change(self, key, element, score_change: int):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zincrby(key, score_change, element)

    @retry
    async def _zget_range(self, key, start: int = 0, end: int = -1, num: int = None, offset: int = None):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zrange(key, start=start, end=end, num=num, offset=offset)

    @retry
    async def _zget_range_with_score(self, key, num: int = None, offset: int = None):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                return await r.zrevrangebyscore(name=key, min='-inf', max='inf', num=num,
                                                start=offset, withscores=True)

    @retry
    async def _zget_top_score(self, key, rand=False):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                end = 0 if not rand else 20
                if members := await r.zrevrange(key, 0, 0):
                    return random.choice(members)
                else:
                    return None

    @retry
    async def _zget_bottom_score(self, key):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                if members := await r.zrange(key, 0, 0):
                    return members[0]
                else:
                    return None

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

    @retry
    async def _zrand(self, key, count: int = None):
        async with redis.Redis(connection_pool=self.pool) as r:
            async with r.lock('Lock_' + str(key), timeout=self.RedisTimeout):
                total = await r.zcard(key)
                if total == 0:
                    return None
                count = 1 if not count else count
                count = total if count > total else count
                if count > 1:
                    random_nums = random.sample(range(total), count)
                    async with r.pipeline() as pipe:
                        await asyncio.gather(*[pipe.zrange(key, i, i) for i in random_nums])
                    values = await pipe.execute()
                    return values
                else:
                    random_num = random.randint(0, total - 1)
                    return (await r.zrange(key, random_num, random_num))[0]

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


if __name__ == "__main__":
    async def _test():
        __ = RedisManagerBase()
        ___ = await __.exists('ip_list')
        print(___)


    asyncio.run(_test())
