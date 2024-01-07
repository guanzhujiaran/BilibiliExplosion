# 最终将请求grpc_api的方法全部放到这里面，里面就是一个class
import traceback
import json
import httpx
import requests
from loguru import logger


class BiliGrpc:
    def __init__(self):
        self.post_localhost_timeout = None
        self.base_url = 'http://127.0.0.1:23333'

    def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        """
        通过动态ids列表获取动态
        :param args: dyn_ids: [int]
        :param kwargs:
        :return:
        """
        da = {
            'dyn_ids': dyn_ids
        }
        data = json.dumps(da)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = requests.request(url=self.base_url + '/grpc/grpc_api_get_DynDetails/',
                                        method='post',
                                        data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()

    def grpc_get_dynamic_detail_by_type_and_rid(self, rid: int, dynamic_type: int = 2) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param args: rid: int, dynamic_type: int = 2
        :param kwargs:
        :return:
        """
        da = {
            'rid': rid,
            'dynamic_type': dynamic_type
        }
        data = json.dumps(da)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = requests.request(url=self.base_url + '/grpc/grpc_get_dynamic_detail_by_type_and_rid/',
                                        method='post',
                                        data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()

    def grpc_get_space_dyn_by_uid(self, uid: int, history_offset: str = '', page: int = 1) -> dict:
        """
        获取up空间
        :param uid:
        :param page:
        :param history_offset:
        :param args: uid:int, history_offset: str = '', page: int = 1
        :param kwargs:
        :return:
        """

        da = {
            'uid': uid,
            'history_offset': history_offset,
            'page': page
        }
        data = json.dumps(da)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                resp = requests.request(url=self.base_url + '/grpc/grpc_get_space_dyn_by_uid/',
                                        method='post',
                                        data=data,
                                        timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()

    # region 异步处理api
    async def Async_grpc_get_space_dyn_by_uid(self, uid: int, history_offset: str = '', page: int = 1) -> dict:
        """
        获取up空间
        :param history_offset:
        :param uid:
        :param page:
        :param args: uid:int, history_offset: str = '', page: int = 1
        :param kwargs:
        :return:
        """

        da = {
            'uid': uid,
            'history_offset': history_offset,
            'page': page
        }
        data = json.dumps(da)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url=self.base_url + '/grpc/Async_grpc_get_space_dyn_by_uid/',
                                             data=data,
                                             timeout=self.post_localhost_timeout)
                return resp.json()
            except:
                traceback.print_exc()
    # endregion
