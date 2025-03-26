import asyncio
import datetime
import random
import time
from typing import List, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi接口.log.base_log import redis_logger, BiliGrpcUtils_logger
from grpc获取动态.Utils.GrpcProxyModel import GrpcProxyStatus
from utl.redisTool.RedisManager import RedisManagerBase
from enum import Enum

MIN_USABLE_PROXY_NUM = 100  # 确保MAX_USABLE_PROXY_NUM >> MIN_USABLE_PROXY_NUM
MAX_USABLE_PROXY_NUM = 200


class GrpcProxyRedis(RedisManagerBase):
    class RedisMap(str, Enum):
        accessible_ip_zset = 'accessible_ip_zset'  # 只保存ip地址的集合 20分的是可用的，减分是正在被使用的次数，负分是不能用的或者次数用完了的
        score_refresh_ts = 'score_refresh_ts'

    def __init__(self):
        super().__init__(db=3)
        self.lock_ip = asyncio.Lock()
        self.score_refresh_ts: int = 0
        self.INIT_SCORE = 20
        self.SCORE_REFRESH_TIME = 10 * 60  # 10分钟刷新一次
        self.sched = AsyncIOScheduler()
        self.sched.add_job(self.background_task, 'interval', seconds=10 * 60, next_run_time=datetime.datetime.now(),
                           misfire_grace_time=600)  # 10分钟刷新一次，确保352和412的代理过掉冷却期
        self.sched.start()

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

    async def del_ip(self, ip: str):
        await self._zdel_elements(self.RedisMap.accessible_ip_zset.value, ip)
        await self._hmdel(ip)

    async def change_ip_score(self, ip: str, score: int = -1):
        return await self._zscore_change(self.RedisMap.accessible_ip_zset.value, ip, score)

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

    async def get_accessible_ips(self, start: int = 0, num: int = 5) -> List[dict]:
        return await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=0, max_score=99999,
                                               start=start, num=num)

    async def get_accessible_ip_count(self):
        return await self._zcount(self.RedisMap.accessible_ip_zset.value, 1, 21)


class GrpcProxyTools:
    """
    redis里面只存能用的代理！！！
    用一个zset有序集合存储，设置一个分数，每次取用分数最大的，取完就扣分，
    """
    ip_list: list[GrpcProxyStatus] = []  # 所有的ip列表
    __ip_str_list: list[str] = []
    _redis_data_sync_flag = False  # 只需要同步一次，剩下都是同步的

    def __init__(self):
        self.use_good_proxy_flag = False
        self.lock_change_ip_data = asyncio.Lock()
        self._available_num = 0
        self._available_num_need_refresh = False
        self.__set_proxy_lock = asyncio.Lock()

    @property
    def available_num(self):
        if self._available_num and not self._available_num_need_refresh:
            return self._available_num
        else:
            self._available_num = len([x for x in self.ip_list if x.is_usable_before_use(False)])
            self._available_num_need_refresh = False
        return self._available_num

    @available_num.setter
    def available_num(self, value):
        self._available_num = value

    @property
    def allNum(self):
        return len(self.ip_list)

    @staticmethod
    def _check_ip_352(ip: str, ip_list: list[GrpcProxyStatus]) -> bool:
        '''
        true 可用，false无法用
        :param ip:
        :param ip_list:
        :return:
        '''
        filter_ip_list: list[GrpcProxyStatus] = list(
            filter(lambda x: x.ip == ip, ip_list)
        )
        if len(filter_ip_list) == 0:
            ip_list.append(GrpcProxyStatus(ip=ip, counter=1, max_counter_ts=0, code=0))
            return True
        ip_stat = filter_ip_list[0]
        return ip_stat.is_usable_before_use(True)

    def check_ip_status(self, ip: str) -> bool:
        return GrpcProxyTools._check_ip_352(ip, self.ip_list)

    async def set_ip_status(
            self,
            ip_status: GrpcProxyStatus,
    ):
        """
        设置代理状态的同时同步一下代理列表
        :param ip_status:
        :return:
        """
        async with self.__set_proxy_lock:
            if not self._redis_data_sync_flag:
                self.ip_list = await grpc_proxy_redis.get_all_ip_status()
                self.__ip_str_list = [x.ip for x in self.ip_list]
                self._redis_data_sync_flag = True
            if not ip_status.available:
                await grpc_proxy_redis.del_ip(ip_status.ip)
                if ip_status.ip in self.__ip_str_list:
                    self.available_num -= 1
            else:
                await grpc_proxy_redis.init_ip_status(ip_status)
                self._available_num_need_refresh = True

    async def get_ip_status_by_ip(self, ip: str) -> GrpcProxyStatus:
        resp = list(filter(lambda x: x.ip == ip, self.ip_list))
        if resp:
            return resp[0]
        else:
            if ip_status := await grpc_proxy_redis.get_ip_status(ip):
                return ip_status
            else:
                return GrpcProxyStatus(
                    ip=ip,
                    counter=0,
                    max_counter_ts=0,
                )

    async def get_rand_available_ip_status(self) -> Union[GrpcProxyStatus, None]:
        if not self._redis_data_sync_flag:
            self.ip_list = await grpc_proxy_redis.get_all_ip_status()
            self._redis_data_sync_flag = True
        if len(self.ip_list) >= 2000:
            BiliGrpcUtils_logger.debug(f'代理列表达到2000，清理无效代理（x.available is False）')
            self.ip_list = [x for x in self.ip_list if x.is_usable_before_use(False)]
        avalibleNum = self.available_num
        # BiliGrpcUtils_logger.debug(f'GrpcProxyTools中代理数量：{avalibleNum}/{len(self.ip_list)}')
        if avalibleNum > MAX_USABLE_PROXY_NUM and self.use_good_proxy_flag:
            while 1:
                _ = await grpc_proxy_redis.get_accessible_ips(start=0, num=100)
                if len(_) == 100:
                    picked_ip = random.choice(_)
                    ip_status = await grpc_proxy_redis.get_ip_status(picked_ip)
                    if ip_status.is_usable_before_use(False):
                        ip_status.is_usable_before_use(True)
                        await grpc_proxy_redis.change_ip_score(picked_ip, -1)  # 每用一次就扣分，扣到负分就不会瞬间把20次全部用完，等自动刷新之后再用
                        return ip_status
                    else:
                        if not ip_status.available:
                            await grpc_proxy_redis.del_ip(ip_status.ip)
                else:
                    return None
        else:
            if avalibleNum > MAX_USABLE_PROXY_NUM:
                self.use_good_proxy_flag = True
            if avalibleNum < MIN_USABLE_PROXY_NUM:
                self.use_good_proxy_flag = False
            return None

    @staticmethod
    async def get_accessible_ip_count():
        return await grpc_proxy_redis.get_accessible_ip_count()


grpc_proxy_tools = GrpcProxyTools()
grpc_proxy_redis = GrpcProxyRedis()

if __name__ == '__main__':
    print(asyncio.run(grpc_proxy_redis.reset_ip_score()))
