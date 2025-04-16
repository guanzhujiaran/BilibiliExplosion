# -*- coding: utf-8 -*-
# 最终将请求api的方法全部放到这里面，里面就是一个class
# 相当于一个客户端，所以设置为永不超时，无限次重试

import asyncio
import traceback
import utl.代理.redisProxyRequest.RedisRequestProxy as RedisRequestProxy
from typing import Union
from fastapi接口.log.base_log import request_with_proxy_logger
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab


class request_with_proxy:
    """
    提供调用接口的功能
    """

    def __init__(self):
        self.post_localhost_timeout = None
        self.post_localhost_timeout = None
        self.log = request_with_proxy_logger
        self.redis_request_with_proxy = RedisRequestProxy.request_with_proxy_internal

    async def request_with_proxy(self, *args, **kwargs) -> Union[dict, list[dict]]:
        """
        :param args:
        :param kwargs:
        mode : single|rand 设置代理是否选择最高的单一代理还是随机
        hybrid : 随便给个值 是否将本地ipv6代理加入随机选择中
        :return:
        """
        while 1:
            try:
                resp = await self.redis_request_with_proxy.request_with_proxy(*args, **kwargs)
                return resp
            except Exception as e:
                request_with_proxy_logger.exception(e)
                await asyncio.sleep(10)

    async def get_one_rand_proxy(self) -> ProxyTab | None:
        while True:
            try:
                resp = await self.redis_request_with_proxy.get_one_rand_proxy()
                return resp
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    async def update_to_proxy_list(self, proxy_dict: ProxyTab, change_score_num=10):
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = await self.redis_request_with_proxy.update_to_proxy_dict(proxy_dict, change_score_num)
                return resp
            except Exception as e:
                traceback.print_exc()
                await asyncio.sleep(10)

    # async def upsert_grpc_proxy_status(self, proxy_id: int, status: int, score_change: int = 0):
    #     """
    #
    #     :param args:
    #     :param kwargs: proxy_id: int, status: int, score_change: int = 0
    #     :return:
    #     """
    #     ret_time = 0
    #     while True:
    #         ret_time += 1
    #         if ret_time > 3:
    #             # assert ret_time > 3, "超出重试次数"
    #             # exit()  #
    #             pass
    #         try:
    #             resp = await self.redis_request_with_proxy.upsert_grpc_proxy_status(proxy_id, status, score_change)
    #             return resp
    #         except:
    #             traceback.print_exc()
    #             await asyncio.sleep(10)

    async def get_proxy_by_ip(self, ip: str)->ProxyTab | None:
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = await self.redis_request_with_proxy.get_proxy_by_ip(ip)
                return resp
            except:
                traceback.print_exc()
                await asyncio.sleep(10)


if __name__ == '__main__':
    test = request_with_proxy()
    # test.upsert_grpc_proxy_status(proxy_id=31178, status=114514, score_change=10)
