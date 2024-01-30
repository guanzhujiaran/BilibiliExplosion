# 最终将请求grpc_api的方法全部放到这里面，里面就是一个class
# 相当于一个客户端
import asyncio
import traceback
import json
import httpx
from httpx import Limits
from loguru import logger


class BiliGrpc:
    def __init__(self):
        self.post_localhost_timeout = None
        self.base_url = 'http://127.0.0.1:23333'
        self.client = httpx.AsyncClient(timeout=self.post_localhost_timeout)
        self.log = logger.bind(name="BiliGrpcClient")

    async def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        """
        通过动态ids列表获取动态
        :param dyn_ids: [int]
        :return:
        """
        data = json.dumps(dyn_ids)
        ret_time = 0
        while True:
            ret_time += 1
            if ret_time > 3:
                # assert ret_time > 3, "超出重试次数"
                # exit()  #
                pass
            try:
                # resp = requests.request(url=self.base_url + '/grpc/grpc_api_get_DynDetails/',
                #                         method='post',
                #                         data=data,
                #                         timeout=self.post_localhost_timeout)
                resp = await self.client.request(url=self.base_url + '/grpc/grpc_api_get_DynDetails',
                                                 method='post',
                                                 data=data, timeout=self.post_localhost_timeout)
                resp.raise_for_status()
                return resp.json()
            except:
                self.log.error(traceback.format_exc())

    async def grpc_get_dynamic_detail_by_type_and_rid(self, rid: int, dynamic_type: int = 2) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param dynamic_type:
        :param rid:
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
                resp = await self.client.request(url=self.base_url + '/grpc/grpc_get_dynamic_detail_by_type_and_rid',
                                                 method='post',
                                                 data=data, timeout=self.post_localhost_timeout)
                resp.raise_for_status()
                return resp.json()
            except:
                self.log.error(traceback.format_exc(1))

    async def grpc_get_space_dyn_by_uid(self, uid: int, history_offset: str = '', page: int = 1) -> dict:
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
                resp = await self.client.request(url=self.base_url + '/grpc/grpc_get_space_dyn_by_uid',
                                                 method='post',
                                                 data=data, timeout=self.post_localhost_timeout)
                resp.raise_for_status()
                return resp.json()
            except:
                self.log.error(traceback.format_exc())

    # endregion


if __name__ == '__main__':
    bg = BiliGrpc()
    loop = asyncio.get_event_loop()
    task = loop.create_task(bg.grpc_get_dynamic_detail_by_type_and_rid(305354951))
    loop.run_until_complete(task)
    print(task.result())
