import asyncio
import datetime
import random
import time
from typing import List, Union

from fastapi接口.log.base_log import redis_logger, BiliGrpcUtils_logger
from fastapi接口.utils.Common import GLOBAL_SCHEDULER
from fastapi接口.service.grpc_module.Utils.GrpcProxyModel import GrpcProxyStatus
from utl.redisTool.RedisManager import RedisManagerBase
from enum import Enum

MIN_USABLE_PROXY_NUM = 50  # 确保MAX_USABLE_PROXY_NUM >> MIN_USABLE_PROXY_NUM
MAX_USABLE_PROXY_NUM = 300


class GrpcProxyRedis(RedisManagerBase):
    """
    这里面的都是放的可用的，不管它是352还是412，只要能访问，得到数据就存在这里，不停等待352或412的冷却时间
    """
    class RedisMap(str, Enum):
        accessible_ip_zset = 'accessible_ip_zset'  # 只保存ip地址的集合 20分的是可用的，减分是正在被使用的次数，负分是不能用的或者次数用完了的
        score_refresh_ts = 'score_refresh_ts'

    def __init__(self):
        super().__init__(db=3)
        self.score_refresh_ts: int = 0
        self.INIT_SCORE = 20
        self.SCORE_REFRESH_TIME = 10 * 60  # 10分钟刷新一次
        self.sched = GLOBAL_SCHEDULER
        self.sched.add_job(self.background_task, 'interval', seconds=10 * 60, next_run_time=datetime.datetime.now(),
                           misfire_grace_time=600)  # 10分钟刷新一次，确保352和412的代理过掉冷却期

    async def get_score_refresh_ts(self) -> int:
        if _ := await self._get(self.RedisMap.score_refresh_ts.value):
            self.score_refresh_ts = int(_)
        if self.score_refresh_ts is None:
            return 0
        return self.score_refresh_ts

    async def set_score_refresh_ts(self, ts: int):
        self.score_refresh_ts = ts
        await self._set(self.RedisMap.score_refresh_ts.value, ts)

    async def background_task(self):
        start_ts = int(time.time())
        redis_logger.critical('开始后台定时任务')
        await asyncio.gather(*[self.reset_ip_score()
                               ])
        redis_logger.critical(f'定时任务执行完毕，耗时：{int(time.time()) - start_ts}秒')

    async def reset_ip_score(self, force: bool = False):

        async def bulk_handle_ips(ip):
            ip_status = await self.get_ip_status(ip)
            if not ip_status.available:
                await self.del_ip(ip_status.ip)
            if ip_status.is_usable_before_use(False):
                await self.init_ip_status(ip_status)  # 重置为20

        if not self.score_refresh_ts:
            await self.get_score_refresh_ts()
        if self.score_refresh_ts and self.score_refresh_ts > (int(time.time()) - self.SCORE_REFRESH_TIME) and not force:
            return
        redis_logger.critical('开始重置ip分数！')
        all_used_ip = await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=-99999,
                                                      max_score=99999)
        await asyncio.gather(*[bulk_handle_ips(__) for __ in all_used_ip])
        await self.set_score_refresh_ts(int(time.time()))

    async def init_ip_status(self, ip_status: GrpcProxyStatus):
        await self._zadd(self.RedisMap.accessible_ip_zset.value,
                         {ip_status.ip: self.INIT_SCORE})  # 每个都设置成20分，用完就检查分数
        await self._hmset(ip_status.ip, ip_status.to_redis_data())

    async def redis_set_ip_status(self,ip_status:GrpcProxyStatus):
        await self._hmset(ip_status.ip, ip_status.to_redis_data())

    async def del_ip(self, ip: str):
        await self._zdel_elements(self.RedisMap.accessible_ip_zset.value, ip)
        await self._hmdel(ip)

    async def change_ip_score(self, ip: str, change_score: int = -1):
        return await self._zscore_change(self.RedisMap.accessible_ip_zset.value, ip, change_score)

    async def get_ip_status(self, ip: str) -> GrpcProxyStatus:
        """
        如果在set里面的代理在hashmap里面没找到，就直接用默认值了
        :param ip:
        :return:
        """
        ip_status_dict = await self._hmgetall(ip)
        if ip_status_dict:
            ip_status = GrpcProxyStatus(ip=ip, counter=1)
            ip_status.parse_form_redis_data(ip_status_dict)
            return ip_status
        else:
            # redis_logger.debug(f'未找到ip:{ip}')
            return GrpcProxyStatus(
                ip=ip,
                counter=1,
                available=False
            )

    async def get_all_ip_status(self) -> List[GrpcProxyStatus]:
        ips = await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=-99999, max_score=99999)
        return await asyncio.gather(*[self.get_ip_status(ip) for ip in ips])

    async def get_accessible_ips(self, start: int = 0, num: int = 5) -> List[str]:
        return await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=0, max_score=99999,
                                               start=start, num=num)

    async def get_rand_accessible_ips(self, num: int = 5) -> List[str]:
        return await self._zrand_member(self.RedisMap.accessible_ip_zset.value, count=num)

    async def get_accessible_ip_zset_len(self):
        return await self._zcard(self.RedisMap.accessible_ip_zset.value)

    async def get_accessible_ip_count(self):
        return await self._zcount(self.RedisMap.accessible_ip_zset.value, 1, 21)


class GrpcProxyTools:
    """
    redis里面只存能用的代理！！！
    用一个zset有序集合存储，设置一个分数，每次取用分数最大的，取完就扣分，
    """
    ip_list: List[GrpcProxyStatus] = []  # 所有的ip列表
    __ip_str_set: set[str] = set()  # 可用的ip_str的set，用于获取可用个数
    _redis_data_sync_flag = False  # 只需要同步一次，剩下都是同步的
    _ip_list_clear_ts: int = 0

    def __init__(self):
        self.use_good_proxy_flag = False
        self._available_num = 0

    @property
    def available_num(self):
        return len(self.__ip_str_set)

    @property
    def allNum(self):
        return len(self.ip_list)

    async def set_ip_status(
            self,
            ip_status: GrpcProxyStatus,
    ):
        """
        设置代理状态的同时同步一下代理列表
        :param ip_status:
        :return:
        """
        if not self._redis_data_sync_flag:
            self._redis_data_sync_flag = True
            self.ip_list = await grpc_proxy_redis.get_all_ip_status()
            self.__ip_str_set = set([x.ip for x in self.ip_list if x.is_usable_before_use(False)])
        if not ip_status.available:
            await grpc_proxy_redis.del_ip(ip_status.ip)
            self.__ip_str_set.discard(ip_status.ip)
            return
        else:
            ip_status = await self.get_ip_status_by_ip(ip_status.ip)
            now = int(time.time())
            ip_status.latest_used_ts = now
            ip_status.counter += 1
            match ip_status.code:
                case -352:
                    ip_status.latest_352_ts = now
                case -412:
                    ip_status.max_counter_ts = now
            # await grpc_proxy_redis.init_ip_status(ip_status)  # 可用的就刷新 这里不刷新，等待后台任务每10分钟自动刷新
            await grpc_proxy_redis.redis_set_ip_status(ip_status)
            self.__ip_str_set.add(ip_status.ip)

    async def get_ip_status_by_ip(self, ip: str) -> GrpcProxyStatus:
        resp = list(filter(lambda x: x.ip == ip, self.ip_list))
        if resp:
            redis_logger.debug(f'从ip_list里面找到ip:{ip}')
            return resp[0]
        else:
            if ip_status := await grpc_proxy_redis.get_ip_status(ip):
                redis_logger.debug(f'从redis里面找到ip:{ip}')
                return ip_status
            else:
                redis_logger.debug(f'未找到ip:{ip}')
                return GrpcProxyStatus(
                    ip=ip,
                    counter=0,
                    max_counter_ts=0,
                )

    async def get_rand_available_ip_status(self) -> Union[GrpcProxyStatus, None]:
        if not self._redis_data_sync_flag:
            self._redis_data_sync_flag = True
            self.ip_list = await grpc_proxy_redis.get_all_ip_status()
        if len(self.ip_list) >= 2000 and self._ip_list_clear_ts < time.time() - 60 * 60 * 24:
            BiliGrpcUtils_logger.debug(f'代理列表达到2000，清理无效代理（x.available is False）')
            self.ip_list = [x for x in self.ip_list if x.is_usable_before_use(False)]
            self._ip_list_clear_ts = int(time.time())
        avalible_num = self.available_num
        if avalible_num > MIN_USABLE_PROXY_NUM and self.use_good_proxy_flag:

            _ = await grpc_proxy_redis.get_accessible_ips(start=0, num=30)
            if len(_) == 30:
                picked_ip = random.choice(_)
                ip_status = await grpc_proxy_redis.get_ip_status(picked_ip)
                if not ip_status.available:
                    await grpc_proxy_redis.del_ip(ip_status.ip)
                    redis_logger.debug(f'这个代理不太行，删了！{ip_status}')
                    return None
                if ip_status.is_usable_before_use(False):
                    await grpc_proxy_redis.change_ip_score(picked_ip, -1)  # 每随机到一次就扣分，让这个最前面的列表不停地变化，不需要管这个代理是不是能用
                    ip_status.is_usable_before_use(True)
                    return ip_status
            else:
                redis_logger.debug(f'没有好用的代理')
                return None
            redis_logger.debug(f'没有好用的代理')
            return None
        else:
            if avalible_num > MAX_USABLE_PROXY_NUM:
                self.use_good_proxy_flag = True
            if avalible_num < MIN_USABLE_PROXY_NUM:
                self.use_good_proxy_flag = False
            redis_logger.debug(f'没有好用的代理')
            return None

    @staticmethod
    async def get_accessible_ip_count():
        return await grpc_proxy_redis.get_accessible_ip_count()


grpc_proxy_tools = GrpcProxyTools()
grpc_proxy_redis = GrpcProxyRedis()

if __name__ == '__main__':
    print(asyncio.run(grpc_proxy_redis.get_accessible_ips(0, 30)))
