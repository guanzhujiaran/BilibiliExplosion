# -*- coding: utf-8 -*-
# 最终将请求api的方法全部放到这里面，里面就是一个class
# 相当于一个客户端，所以设置为永不超时，无限次重试

import asyncio
import json
import traceback
from typing import Union

import httpx
from loguru import logger

from utl.代理.ProxyTool.ProxyObj import TypePDict
from utl.代理.SealedRequests import MYASYNCHTTPX
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy as redis_request_with_proxy


class request_with_proxy:
    """
    提供调用接口的功能
    """

    def __init__(self):
        self.post_localhost_timeout = None
        self.post_localhost_timeout = None
        self.base_url = 'http://localhost:23333'
        self.base_url1 = 'http://localhost:23333'
        self.log = logger.bind(user=__name__ + "request_with_proxy")
        # self.log.add(sys.stderr, level="INFO", filter=lambda record: record["extra"].get('user') == __name__ + "request_with_proxy")
        self.redis_request_with_proxy = redis_request_with_proxy()
        self.session = MYASYNCHTTPX()

    #
    # async def request_with_proxy(self, *args, **kwargs) -> dict or list[dict]:
    #     if args:
    #         kwargs.update(*args)
    #     data = json.dumps(kwargs)
    #     ret_time = 0
    #     while True:
    #         ret_time += 1
    #         if ret_time > 3:
    #             # assert ret_time > 3, "超出重试次数"
    #             # exit()  #
    #             pass
    #         try:
    #             async with httpx.AsyncClient() as client:
    #                 resp = await client.request(url=self.base_url1 + '/request_with_proxy', method='post', data=data,
    #                                             timeout=self.post_localhost_timeout)
    #             resp.raise_for_status()
    #             return resp.json()
    #         except:
    #             traceback.print_exc()
    #             await asyncio.sleep(10)
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
                traceback.print_exc()
                await asyncio.sleep(10)

    async def get_one_rand_proxy(self):
        """

        :return:
        {
            "proxy_id": 103494,
            "proxy": {
                "http": "http://120.76.137.67:3128",
                "https": "http://120.76.137.67:3128"
                },
            "status": 0,
            "update_ts": 1693397281,
            "score": -50,
            "add_ts": 1692975739,
            "success_times": 192,
            "zhihu_status": 0
        }
        """
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(url=self.base_url + '/get_one_rand_proxy', method='get')
                return resp.json()
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    # async def get_one_rand_grpc_proxy(self):
    #     while True:
    #         try:
    #             async with httpx.AsyncClient() as client:
    #                 resp = await client.request(url=self.base_url + '/grpc/get_one_rand_grpc_proxy', method='get',
    #                                             timeout=self.post_localhost_timeout)
    #             resp.raise_for_status()
    #             try:
    #                 resp.json()
    #             except:
    #                 self.log.error(f"获取json格式数据失败！{resp.text}")
    #             if resp.json():
    #                 return resp.json()
    #             else:
    #                 await asyncio.sleep(10)
    #         except:
    #             traceback.print_exc()
    #             await asyncio.sleep(10)

    async def get_one_rand_grpc_proxy(self) -> Union[TypePDict, None]:
        while True:
            try:
                resp = await self.redis_request_with_proxy.get_one_rand_grpc_proxy()
                return resp
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    # async def upsert_grpc_proxy_status(self, *args, **kwargs):
    #     """
    #
    #     :param args:
    #     :param kwargs: proxy_id: int, status: int, score_change: int = 0
    #     :return:
    #     """
    #     if args:
    #         kwargs.update(*args)
    #     data = json.dumps(kwargs)
    #     ret_time = 0
    #     while True:
    #         ret_time += 1
    #         if ret_time > 3:
    #             # assert ret_time > 3, "超出重试次数"
    #             # exit()  #
    #             pass
    #         try:
    #             async with httpx.AsyncClient() as client:
    #                 resp = await client.request(url=self.base_url + '/grpc/upsert_grpc_proxy_status',
    #                                             method='post',
    #                                             data=data, timeout=self.post_localhost_timeout)
    #             try:
    #                 resp.json()
    #             except:
    #                 self.log.error(f'获取json格式数据失败！{resp.text}')
    #             return resp.json()
    #         except:
    #             traceback.print_exc()
    #             await asyncio.sleep(10)
    #
    async def upsert_grpc_proxy_status(self, *args, **kwargs):
        """

        :param args:
        :param kwargs: proxy_id: int, status: int, score_change: int = 0
        :return:
        """
        if args:
            kwargs.update(*args)
        data = json.dumps(kwargs)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = await self.redis_request_with_proxy.upsert_grpc_proxy_status(*args, **kwargs)
                return resp
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    # async def get_grpc_proxy_by_ip(self, ip: str):
    #     ret_time = 0
    #     while True:
    #         ret_time += 1
    #         if ret_time > 3:
    #             # assert ret_time > 3, "超出重试次数"
    #             # exit()  #
    #             pass
    #         try:
    #             async with httpx.AsyncClient() as client:
    #                 resp = await client.request(url=self.base_url + '/grpc/get_grpc_proxy_by_ip',
    #                                             method='get',
    #                                             params={
    #                                                 'ip': ip,
    #                                             }, timeout=self.post_localhost_timeout)
    #             try:
    #                 resp.json()
    #             except:
    #                 self.log.error(f'获取json格式数据失败！{resp.text}')
    #             return resp.json()
    #         except:
    #             traceback.print_exc()
    #             await asyncio.sleep(10)

    async def get_grpc_proxy_by_ip(self, ip: str):
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = await self.redis_request_with_proxy.get_grpc_proxy_by_ip(ip)
                return resp
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    async def upsert_lot_detail(self, *args, **kwargs):
        if args:
            kwargs.update(*args)
        data = json.dumps(kwargs)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(url=self.base_url + '/lot/upsert_lot_detail',
                                                method='post',
                                                data=data, timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()
                await asyncio.sleep(10)


if __name__ == '__main__':
    test = request_with_proxy()
    test.upsert_grpc_proxy_status(proxy_id=31178, status=114514, score_change=10)
