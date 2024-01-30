import asyncio
import random
import threading
import time
from dataclasses import dataclass
from typing import Union


@dataclass
class GrpcProxyStatus:
    ip: str  # ip地址 如”127.0.0.1:114514“
    counter: int  # 使用次数
    max_counter_ts: int  # 达到最大的时间戳
    MetaData: tuple = ()  # ip对应的MetaData
    code: int = 0  # 返回响应的代码。0或者-352
    available: bool = False  # 是否可以直接使用，也就是说是请求成功过的代理，同时也没有-352风控


class GrpcProxyTools:
    ip_list: list[GrpcProxyStatus] = []  # 所有的ip列表
    use_avaliable_proxy_flag: bool = False  # 是否可以使用可用代理列表中的代理

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
        if int(time.time()) - ip_stat.max_counter_ts >= 3600:  # 如果一小时以上就重置为0
            ip_stat.counter = 1
            ip_stat.code = 0
            ip_stat.max_counter_ts = int(time.time())
            return True
        if ip_stat.code == -352:
            return False
        if ip_stat.counter >= 200:
            ip_stat.code = -352
            ip_stat.max_counter_ts = int(time.time())
            return False
        ip_stat.counter += 1
        return True

    @staticmethod
    def _set_ip_status(ipstatus: GrpcProxyStatus, ip_list: list[GrpcProxyStatus]):
        '''
        设置ip的状态
        :param ipstatus:
        :param ip_list:
        :return:
        '''
        filter_ip_list: list[GrpcProxyStatus] = list(
            filter(lambda x: x.ip == ipstatus.ip, ip_list)
        )
        if len(filter_ip_list) == 0:
            ip_list.append(ipstatus)
            return
        else:
            filter_ip = filter_ip_list[0]
            filter_ip.counter = ipstatus.counter
            filter_ip.max_counter_ts = ipstatus.max_counter_ts
            filter_ip.code = ipstatus.code

    async def check_ip_status(self, ip: str) -> bool:
        return GrpcProxyTools._check_ip_352(ip, self.ip_list)

    async def set_ip_status(self, ipstatus: GrpcProxyStatus):
        return GrpcProxyTools._set_ip_status(ipstatus, self.ip_list)

    async def get_ip_status_by_ip(self, ip: str) -> Union[GrpcProxyStatus, None]:
        resp = list(filter(lambda x: x.ip == ip, self.ip_list))
        if resp:
            return resp[0]
        else:
            return None

    async def get_rand_avaliable_ip_status(self) -> Union[GrpcProxyStatus, None]:
        avaliable_ip_status_list = [x for x in self.ip_list if x.available]
        if len(avaliable_ip_status_list) > 10:
            self.use_avaliable_proxy_flag = True
        if len(avaliable_ip_status_list) < 3:
            self.use_avaliable_proxy_flag = False
        if self.use_avaliable_proxy_flag:
            if avaliable_ip_status_list:
                return random.choice(avaliable_ip_status_list)
            else:
                return None
