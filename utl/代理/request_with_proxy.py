# -*- coding: utf-8 -*-
# 最终将请求api的方法全部放到这里面，里面就是一个class
# 相当于一个客户端，所以设置为永不超时，无限次重试
import asyncio
import time
import traceback
import json
import httpx
import requests
import aiohttp
from asgiref.sync import async_to_sync
from httpx import Limits
from loguru import logger
from utl.代理.SealedRequests import MYASYNCHTTPX


class request_with_proxy:
    def __init__(self):
        self.post_localhost_timeout = None
        self.client = httpx.AsyncClient(timeout=self.post_localhost_timeout,
                                        limits=Limits(max_connections=None, max_keepalive_connections=None,
                                                      keepalive_expiry=None))
        self.post_localhost_timeout = None
        self.base_url = 'http://localhost:23333'
        self.base_url1 = 'http://localhost:23333'
        self.log=logger.bind(user=__name__)
    async def async_request_with_proxy(self, *args, **kwargs):
        """
        异步处理请求
        :param args:
        :param kwargs:
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
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.base_url + '/async_request_with_proxy', data=data,
                                            timeout=self.post_localhost_timeout) as response:
                        return await response.json()
            except:
                traceback.print_exc()
                time.sleep(10)

    def sync_request_with_proxy(self, *args, **kwargs) -> dict or list[dict]:
        while 1:
            try:
                result = async_to_sync(self.request_with_proxy)(*args, **kwargs)
                return result
            except Exception as e:
                traceback.print_exc()
                time.sleep(10)

    async def request_with_proxy(self, *args, **kwargs) -> dict or list[dict]:
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
                resp = await self.client.request(url=self.base_url1 + '/request_with_proxy', method='post', data=data,timeout=self.post_localhost_timeout)
                resp.raise_for_status()
                return resp.json()
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    def get_one_rand_proxy(self):
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
                resp = requests.request(url=self.base_url + '/get_one_rand_proxy', method='get')
                return resp.json()
            except:
                traceback.print_exc()
                time.sleep(10)

    async def get_one_rand_grpc_proxy(self):
        while True:
            try:
                resp = await self.client.request(url=self.base_url + '/grpc/get_one_rand_grpc_proxy', method='get',timeout=self.post_localhost_timeout)
                resp.raise_for_status()
                try:
                    resp.json()
                except:
                    self.log.error(f"获取json格式数据失败！{resp.text}")
                if resp.json():
                    return resp.json()
                else:
                    await asyncio.sleep(10)
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

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
                resp = await self.client.request(url=self.base_url + '/grpc/upsert_grpc_proxy_status',
                                                 method='post',
                                                 data=data,timeout=self.post_localhost_timeout)
                try:
                    resp.json()
                except:
                    self.log.error(f'获取json格式数据失败！{resp.text}')
                return resp.json()
            except:
                traceback.print_exc()
                await asyncio.sleep(10)

    def upsert_lot_detail(self, *args, **kwargs):
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
                resp = requests.request(url=self.base_url + '/lot/upsert_lot_detail',
                                        method='post',
                                        data=data,timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()
                time.sleep(10)


if __name__ == '__main__':
    test = request_with_proxy()
    test.upsert_grpc_proxy_status(proxy_id=31178, status=114514, score_change=10)
