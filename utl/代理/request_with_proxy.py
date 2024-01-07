# -*- coding: utf-8 -*-
# 最终将请求api的方法全部放到这里面，里面就是一个class
import traceback
import json
import requests
import aiohttp


class request_with_proxy:
    def __init__(self):
        self.post_localhost_timeout = None
        self.base_url = 'http://localhost:23333'

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

    def request_with_proxy(self, *args, **kwargs) -> dict or list[dict]:
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
                resp = requests.request(url=self.base_url + '/request_with_proxy', method='post', data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()

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
                resp = requests.request(url=self.base_url + '/get_one_rand_proxy/', method='get')
                return resp.json()
            except:
                traceback.print_exc()

    def get_one_rand_grpc_proxy(self):
        while True:
            try:
                resp = requests.request(url=self.base_url + '/grpc/get_one_rand_grpc_proxy/', method='get')
                return resp.json()
            except:
                traceback.print_exc()

    def upsert_grpc_proxy_status(self, *args, **kwargs):
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
                resp = requests.request(url=self.base_url + '/grpc/upsert_grpc_proxy_status/',
                                        method='post',
                                        data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()

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
                resp = requests.request(url=self.base_url + '/lot/upsert_lot_detail/',
                                        method='post',
                                        data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()



if __name__ == '__main__':
    test = request_with_proxy()
    test.upsert_grpc_proxy_status(proxy_id=31178, status=114514, score_change=10)
