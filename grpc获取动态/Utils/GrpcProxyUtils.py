import ast
import asyncio
import pickle
import random
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Union, List

from utl.redisTool.RedisManager import RedisManagerBase

_max_use_count_before_352 = 20
_352_cd = 15 * 60
_412_cd = 24 * 3600


@dataclass
class GrpcProxyStatus:
    ip: str  # ip地址 如”127.0.0.1:114514“
    counter: int  # 使用次数
    max_counter_ts: int = 0  # 达到最大的时间戳
    code: int = 0  # 返回响应的代码。0或者-352
    available: bool = False  # 是否可以直接使用，也就是说是请求成功过的代理，同时也没有-352风控
    latest_352_ts: int = 0
    latest_used_ts: int = 0

    @property
    def is_usable(self):
        """
        是否可以使用，使用次数没到
        :return:
        """
        if not self.available:
            return False
        if self.code != 0:
            if self.code == -352:
                if self.latest_352_ts + _352_cd > time.time():
                    return True
                else:
                    return False
            if self.code == -412:
                if self.latest_used_ts + _412_cd > time.time():
                    return True
                else:
                    return False
            return False
        if self.counter >= _max_use_count_before_352:
            return False
        return True

    def to_redis_data(self):
        return {
            "ip": self.ip,
            "counter": self.counter,
            "max_counter_ts": self.max_counter_ts,
            "code": self.code,
            "available": str(self.available),
            "latest_352_ts": self.latest_352_ts,
            "latest_used_ts": self.latest_used_ts
        }

    def parse_form_redis_data(self, data: dict):
        self.ip = data["ip"]
        self.counter = ast.literal_eval(data["counter"])
        self.max_counter_ts = ast.literal_eval(data["max_counter_ts"])
        self.code = ast.literal_eval(data["code"])
        self.available = ast.literal_eval(data["available"])
        self.latest_352_ts = ast.literal_eval(data["latest_352_ts"])
        self.latest_used_ts = ast.literal_eval(data["latest_used_ts"])

    def to_dict(self):
        return {
            "ip": self.ip,
            "counter": self.counter,
            "max_counter_ts": self.max_counter_ts,
            "code": self.code,
            "available": self.available,
            "latest_352_ts": self.latest_352_ts,
            "latest_used_ts": self.latest_used_ts
        }


class myRedisManager(RedisManagerBase):
    class RedisMap(str, Enum):
        accessible_ip_zset = 'accessible_ip_zset'  # 只保存ip地址的集合
        score_refresh_ts = 'score_refresh_ts'

    def __init__(self):
        super().__init__(db=3)
        self.lock_ip = asyncio.Lock()
        self.score_refresh_ts: int = 0
        self.INIT_SCORE = 20
        self.SCORE_REFRESH_TIME = 15 * 60
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.background_task())

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
        while True:
            try:
                await self.reset_ip_score()
                await asyncio.sleep(60)
            except Exception as e:
                traceback.print_exc()
                await asyncio.sleep(60)

    async def reset_ip_score(self):
        if self.score_refresh_ts == 0:
            self.score_refresh_ts = await self.get_score_refresh_ts()
        if self.score_refresh_ts != 0 and self.score_refresh_ts + self.SCORE_REFRESH_TIME < time.time():
            return
        all_used_ip = await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=0,
                                                      max_score=19)  # 所有的用过的ip
        for ip in all_used_ip:
            ip_status = await self.get_ip_status(ip)
            if not ip_status.available:
                await self.del_ip(ip_status.ip)
            if GrpcProxyTools.is_usable(ip_status, False):
                await self.change_ip_score(ip, self.INIT_SCORE)
        await self.set_score_refresh_ts(int(time.time()))

    async def set_ip_status(self, ip_status: GrpcProxyStatus):
        async with self.lock_ip:
            await self._zadd(self.RedisMap.accessible_ip_zset.value,
                             {ip_status.ip: self.INIT_SCORE})  # 每个都设置成20分，用完就检查分数
            await self._hmset(ip_status.ip, ip_status.to_redis_data())

    async def del_ip(self, ip: str):
        async with self.lock_ip:
            if self._z_exist(self.RedisMap.accessible_ip_zset.value, ip):
                await self._zdel_elements(self.RedisMap.accessible_ip_zset.value, ip)
                await self._hmdel(ip)

    async def change_ip_score(self, ip: str, score: int = -1):
        async with self.lock_ip:
            return await self._zscore_change(self.RedisMap.accessible_ip_zset.value, ip, score)

    async def get_ip_status(self, ip: str) -> GrpcProxyStatus:
        """
        如果在set里面的代理在hashmap里面没找到，就直接用默认值了
        :param ip:
        :return:
        """
        async with self.lock_ip:
            ip_status_dict = await self._hmgetall(ip)
            if ip_status_dict:
                ip_status = GrpcProxyStatus(ip=ip, counter=1)
                ip_status.parse_form_redis_data(ip_status_dict)
                return ip_status
            else:
                print(f'未找到ip:{ip}')
                return GrpcProxyStatus(
                    ip=ip,
                    counter=1,
                )

    async def get_all_ip_status(self) -> List[GrpcProxyStatus]:
        ret_list = []
        ips = await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=1, max_score=20)
        for ip in ips:
            ret_list.append(await self.get_ip_status(ip))
        return ret_list

    async def get_accessible_ips(self, start: int = 0, num: int = 5) -> List[dict]:
        async with self.lock_ip:
            return await self._zget_range_by_score(self.RedisMap.accessible_ip_zset.value, min_score=1, max_score=20,
                                                   start=start, num=num)


class GrpcProxyTools:
    """
    redis里面只存能用的代理！！！
    用一个zset有序集合存储，设置一个分数，每次取用分数最大的，取完就扣分，
    """
    ip_list: list[GrpcProxyStatus] = []  # 所有的ip列表
    r = myRedisManager()
    lock_change_ip_data = asyncio.Lock()
    _redis_data_sync_flag = False  # 只需要同步一次，剩下都是同步的

    def __init__(self):
        self.use_good_proxy_flag = False

    @property
    def avalibleNum(self):
        return len([x for x in self.ip_list if x.available and x.is_usable])

    @property
    def allNum(self):
        return len(self.ip_list)

    @staticmethod
    def is_usable(ip_status: GrpcProxyStatus, add_counter_flag: bool = False) -> bool:
        if ip_status.max_counter_ts and int(time.time()) - ip_status.max_counter_ts >= 3600:  # 如果一小时以上就重置为0
            ip_status.counter = 1
            ip_status.code = 0
            ip_status.max_counter_ts = int(time.time())
            ip_status.latest_used_ts = 0
            ip_status.latest_352_ts = 0
            return True
        if add_counter_flag:
            ip_status.latest_used_ts = int(time.time())
            ip_status.counter += 1
        return ip_status.is_usable

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
        return GrpcProxyTools.is_usable(ip_stat, True)

    async def check_ip_status(self, ip: str) -> bool:
        return GrpcProxyTools._check_ip_352(ip, self.ip_list)

    async def set_ip_status(self, ipstatus: GrpcProxyStatus):
        """
        设置代理状态的同时同步一下代理列表
        :param ipstatus:
        :return:
        """
        async with self.lock_change_ip_data:
            if self._redis_data_sync_flag == False:
                self.ip_list = await self.r.get_all_ip_status()
                self._redis_data_sync_flag = True
            if not ipstatus.available:
                await self.r.del_ip(ipstatus.ip)
            else:
                await self.r.set_ip_status(ipstatus)

    async def get_ip_status_by_ip(self, ip: str) -> GrpcProxyStatus:
        resp = list(filter(lambda x: x.ip == ip, self.ip_list))
        if resp:
            return resp[0]
        else:
            if ip_status := await self.r.get_ip_status(ip):
                return ip_status
            else:
                return GrpcProxyStatus(
                    ip=ip,
                    counter=0,
                    max_counter_ts=0,
                )

    async def get_rand_avaliable_ip_status(self) -> Union[GrpcProxyStatus, None]:
        async with self.lock_change_ip_data:
            if not self._redis_data_sync_flag:
                self.ip_list = await self.r.get_all_ip_status()
                self._redis_data_sync_flag = True
            if len(self.ip_list) >= 2000:
                self.ip_list = [x for x in self.ip_list if x.available]
            avalibleNum = self.avalibleNum
            if avalibleNum > 100 and self.use_good_proxy_flag:
                while 1:
                    _ = await self.r.get_accessible_ips(start=0, num=5)
                    if len(_) == 5:
                        picked_ip = random.choice(_)
                        await self.r.change_ip_score(picked_ip, -1)
                        ip_status = await self.r.get_ip_status(picked_ip)
                        if GrpcProxyTools.is_usable(ip_status, False):
                            return ip_status
                        else:
                            await self.r.change_ip_score(picked_ip, -20)
                    else:
                        return None
            else:
                if avalibleNum > 300:
                    self.use_good_proxy_flag = True
                if avalibleNum < 100:
                    self.use_good_proxy_flag = False
                return None

    async def get_all_ip(self):
        return await self.r.get_all_ip_status()


if __name__ == '__main__':
    a = GrpcProxyTools()
    result = asyncio.run(a.get_all_ip())
    print(len(result))
