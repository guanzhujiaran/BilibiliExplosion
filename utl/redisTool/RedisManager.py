import asyncio
import random
import time
import traceback
from typing import Union, Any, List, Dict, AsyncIterator
from datetime import timedelta
from redis import asyncio as redis
from enum import Enum
from redis.typing import KeyT
from redis.exceptions import ConnectionError, BusyLoadingError
from CONFIG import CONFIG
import redis as sync_redis
from fastapi接口.log.base_log import redis_logger

_MAX_SEM_NUM = 1024
_sem = asyncio.Semaphore(_MAX_SEM_NUM)
def retry_async_generator(func):
    """
    装饰器，用于重试异步生成器函数。
    如果在迭代过程中发生指定错误，会从头开始重试整个生成过程。
    """
    async def wrapper_generator(*args, **kwargs):
        while True: # 外层循环用于重试整个生成过程
            async with _sem: # 在尝试获取并迭代生成器前获取信号量
                try:
                    # 1. 调用原始函数获取异步生成器对象
                    gen = func(*args, **kwargs)
                    # 2. 迭代原始生成器，并将值 yield 给调用方
                    # 这个 async for 循环会在 gen 完成 (StopAsyncIteration) 或抛出异常时结束
                    async for item in gen:
                        # 如果成功从原始生成器获取到值，就 yield 给外部调用方
                        yield item
                    # 3. 如果 async for 循环正常结束，说明生成器运行完毕，跳出重试循环
                    break # 成功完成，退出重试循环
                except ConnectionError as e:
                    redis_logger.exception(f'Redis连接错误 during generator iteration for {func.__name__}, retrying in 30s... {e}')
                    # 信号量在 'async with' 块结束时自动释放
                    await asyncio.sleep(30)
                    # while True 循环继续，尝试获取信号量并重新开始

                except Exception as e:
                    # 捕获其他异常
                    redis_logger.exception(f'An unexpected error occurred during generator iteration for {func.__name__}, retrying in 30s... {e}')
                    # 信号量在 'async with' 块结束时自动释放
                    await asyncio.sleep(30)
                    # while True 循环继续，尝试获取信号量并重新开始

                # Note: StopAsyncIteration 是正常结束标志，会被 async for 内部处理，
                # 不会到达这里的 except 块

    # 返回这个 wrapper 生成器函数
    return wrapper_generator


def retry(func):
    async def wrapper(*args, **kwargs):
        while 1:
            async with _sem:
                try:
                    return await func(*args, **kwargs)
                except BusyLoadingError as e:
                    await asyncio.sleep(30)
                except ConnectionError as e:
                    redis_logger.exception(f'Redis连接错误，重试中...{e}')
                    await asyncio.sleep(30)
                except Exception as e:
                    redis_logger.exception(e)
                    await asyncio.sleep(30)

    return wrapper


def _redis_client_factory(pool, sync=False):
    if sync:
        return sync_redis.Redis(connection_pool=pool, socket_timeout=10)
    return redis.Redis(connection_pool=pool, socket_timeout=10)


def sync_retry(func):
    def wrapper(*args, **kwargs):
        while 1:
            try:
                return func(*args, **kwargs)
            except Exception:
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
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True&retry_on_timeout=30&socket_timeout=30',
            max_connections=_MAX_SEM_NUM
        )
        self.RedisTimeout = 30

    @sync_retry
    def _get(self, key: Union[Any, List[Any]]):
        """
        传入多个参数则使用pipeline批量获取
        :param key:
        :return:
        """
        with _redis_client_factory(pool=self.pool, sync=True) as r:
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
        with _redis_client_factory(pool=self.pool, sync=True) as r:
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
        with _redis_client_factory(pool=self.pool, sync=True) as r:
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
        with _redis_client_factory(pool=self.pool, sync=True) as r:
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
            url=f'redis://{self.host}:{self.port}/{self.db}?decode_responses=True&health_check_interval=30&retry_on_timeout=30&socket_timeout=30',
            max_connections=_MAX_SEM_NUM
        )
        self.RedisTimeout = 30

    # region 批量操作
    @retry_async_generator
    async def _scan_keys_with_prefix_iter(self, prefix: str, chunk_size: int = 1000) -> AsyncIterator[List[bytes]]:
        """
        使用 SCAN 迭代获取带有指定前缀的 keys，逐批返回 key 列表。
        避免一次性加载所有 key 到内存。
        """
        cursor = 0
        async with _redis_client_factory(pool=self.pool) as r:
            while True:
                # SCAN 命令返回的 cursor 在没有更多匹配 key 时会变为 0
                cursor, keys = await r.scan(cursor=cursor, match=f'{prefix}:*', count=chunk_size)
                if keys:
                    yield keys
                if cursor == 0:
                    break

    @retry
    async def _del_keys_with_prefix(self, prefix: str, batch_size: int = 1000):
        """
        批量删除带有指定前缀的 keys，使用 UNLINK 和 Pipeline。
        通过迭代器获取 key，避免内存问题。
        """
        deleted_count = 0
        # 使用 scan_keys_with_prefix_iter 迭代器逐批获取 key
        async for key_batch in self._scan_keys_with_prefix_iter(prefix, chunk_size=batch_size):
            if not key_batch:
                continue

            # 对每一批 key 执行 Pipeline UNLINK
            async with _redis_client_factory(pool=self.pool) as r:
                async with r.pipeline() as pipe:
                    for key in key_batch:
                        await pipe.unlink(key)  # 使用 UNLINK 代替 DEL
                    # 执行当前批次的删除命令
                    results = await pipe.execute()
                    # 可以选择处理 results，例如统计成功删除的数量
                    # 注意：unlink 成功返回 1，失败（key 不存在）返回 0
                    deleted_count += sum(results)  # 简单的统计

        # 可以选择返回总共删除的数量，或者 None
        return deleted_count  # 返回总共尝试删除成功的 key 数量

    @retry_async_generator
    async def _get_all_val_with_prefix(self, prefix: str, batch_size: int = 1000) -> AsyncIterator[Any]:
        """
        批量获取带有指定前缀的 keys 对应的 values，使用 MGET 和 Pipeline。
        通过迭代器获取 key 并生成 value，避免内存问题。
        """
        # 使用 scan_keys_with_prefix_iter 迭代器逐批获取 key
        async for key_batch in self._scan_keys_with_prefix_iter(prefix, chunk_size=batch_size):
            if not key_batch:
                continue

            # 对每一批 key 执行 Pipeline MGET
            async with _redis_client_factory(pool=self.pool) as r:
                # redis-py MGET 可以接受 list of keys
                values_batch = await r.mget(key_batch)  # MGET 在 Pipeline 中执行效率更高

                # 逐个生成获取到的 value
                for value in values_batch:
                    # 注意：如果 key 不存在，MGET 返回的对应位置是 None
                    # 根据需要决定是否跳过 None 值
                    if value is not None:
                        yield value
                    # else: yield None # 或者保留 None 值

    # endregion

    @retry
    async def exists(self, key: Any) -> int:
        """

        :param key:
        :return: 返回1存在 0不存在
        """
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.exists(key)

    # region 字符串操作
    @retry
    async def _get(self, key):
        """
        传入多个参数则使用pipeline批量获取
        :param key:
        :return:
        """
        async with _redis_client_factory(pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for k in key:
                    await pipe.get(k)
                return await pipe.execute()
            else:
                return await r.get(key)

    @retry
    async def _set(self, key, value):
        async with _redis_client_factory(pool=self.pool) as r:
            if type(key) is list:
                async with r.pipeline() as pipe:
                    for idx in range(len(key)):
                        await pipe.set(key[idx], value[idx])
                    return await pipe.execute()
            else:
                return await r.set(key, value)

    @retry
    async def _setex(self, key, value, _time: Union[int, timedelta]):
        async with _redis_client_factory(pool=self.pool) as r:
            if type(key) is list:
                pipe = r.pipeline()
                for idx in range(len(key)):
                    await pipe.setex(name=key[idx], value=value[idx], time=_time)
                return await pipe.execute()
            else:
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
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.delete(*set_name)

    @retry
    async def _sadd(self, set_name, val):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.sadd(set_name, val)

    @retry
    async def _sisexist(self, set_name, val):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.sismember(set_name, val)

    @retry
    async def _sget_rand(self, set_name):
        async with _redis_client_factory(pool=self.pool) as r:
            return r.srandmember(set_name)

    @retry
    async def _scount(self, set_name):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.scard(set_name)

    @retry
    async def _sget_all(self, set_name):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.smembers(set_name)

    @retry
    async def _srem(self, set_name, *val):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.srem(set_name, *val)

    # endregion

    # region 有序集合ZSet操作

    @retry
    async def _z_exist(self, key, element):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zscore(key, element) is not None

    @retry
    async def _zadd(self, key, mapping: dict):
        if mapping:
            insert_map = {}
            for k, v in mapping.items():
                if type(k) in [bytes, memoryview, str, int] and type(v) in [bytes, memoryview, str, int, float]:
                    insert_map[k] = v
                else:
                    redis_logger.critical(f"zadd name:{key} key:{k} value:{v} error")
            async with _redis_client_factory(pool=self.pool) as r:
                return await r.zadd(key, insert_map, )
        return None

    @retry
    async def _zscore_change(self, key, element, score_change: int):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zincrby(key, score_change, element)

    @retry
    async def _zget_range(self, key, start: int = 0, end: int = -1, num: int = None, offset: int = None):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrange(key, start=start, end=end, num=num, offset=offset)

    @retry
    async def _zget_range_with_score(self, key, num: int = None, offset: int = None):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrevrangebyscore(name=key, min='-inf', max='inf', num=num,
                                            start=offset, withscores=True)

    @retry
    async def _zget_rank(self, key, name):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrevrank(key, name)

    @retry
    async def _zcard(self, key):
        """
        计算集合中元素的数量。
        :param key:
        :return:
        """
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zcard(key)

    @retry
    async def _zcount(self, key, min_val, max_val):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zcount(key, min_val, max_val)

    @retry
    async def _zget_top_score(self, key, rand=False) -> str:
        end = 0 if not rand else 20
        async with _redis_client_factory(pool=self.pool) as r:
            if members := await r.zrevrange(key, 0, 0):
                return random.choice(members)
            else:
                return None

    @retry
    async def _zget_bottom_score(self, key):
        async with _redis_client_factory(pool=self.pool) as r:
            if members := await r.zrange(key, 0, 0):
                return members[0]
            else:
                return None

    @retry
    async def _zget_range_by_score(self, key, min_score: int, max_score: int, start: int = None, num: int = None):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrangebyscore(key, min_score, max_score, start=start, num=num, )

    @retry
    async def _zdel_elements(self, key, *elements_to_remove):
        if not elements_to_remove:
            return
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrem(key, *elements_to_remove)

    @retry
    async def _zdel_range(self, key, start: int, end: int):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zremrangebyrank(key, start, end)

    @retry
    async def _zrand(self, key, count: int = None):
        async with _redis_client_factory(pool=self.pool) as r:
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

    @retry
    async def _zrand_member(self, key, count: int = 1):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.zrandmember(key, count=count)

    # endregion

    @retry
    async def _hmset(self, name, field_values):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.hset(name=name, mapping=field_values)

    @retry
    async def _hmset_bulk_batch(self, hm_name: str, hm_k_v_List: list[Dict[int | str, int | str | float | bytes]]):
        # 使用redis连接池创建redis对象
        async with _redis_client_factory(pool=self.pool) as r:
            # 创建redis管道
            async with r.pipeline() as pipe:
                # 设置每次批量处理的数量
                chunk_size = 1000
                # 遍历hm_list，每次处理chunk_size个元素
                for i in range(0, len(hm_k_v_List), chunk_size):
                    # 获取当前批次的元素
                    chunk_kv = hm_k_v_List[i:i + chunk_size]
                    # 遍历当前批次的元素
                    for idx in range(len(chunk_kv)):
                        # 将当前批次的元素添加到管道中
                        await pipe.hset(hm_name, mapping=chunk_kv[idx])
                    # 执行当前批次的命令
                    await pipe.execute()  # 执行当前批次的命令

    @retry
    async def _hmget_bulk(self, name: str, key_arr: list[str], ):
        async with _redis_client_factory(pool=self.pool) as r:
            async with r.pipeline() as pipe:
                for key in key_arr:
                    await pipe.hget(name, key)
                return await pipe.execute()

    @retry
    async def _hmgetall(self, name, ):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.hgetall(name=name)

    async def _hmget(self, name, key):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.hget(name=name, key=key)

    @retry
    async def _hmdel(self, name):
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.delete(name)

    @retry
    async def _scan(self, cursor: int = 0, match_str: str = ''):
        """
        记得确保match_str 里面带个*，如果要获取多个的话
        :param cursor:
        :param match_str:
        :return:
        """
        async with _redis_client_factory(pool=self.pool) as r:
            return await r.scan(cursor=cursor, match=match_str, count=5000)


if __name__ == "__main__":
    async def _test():
        __ = RedisManagerBase()
        ___ = await __.exists('ip_list')
        print(___)


    asyncio.run(_test())
