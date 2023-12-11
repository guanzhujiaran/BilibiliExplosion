# -*- coding: utf-8 -*-
import base64
import random
import threading

import time

import traceback
from typing import Union

import grpc
import json
import logging
import httpx
import loguru

from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from grpc获取动态.grpc.makeMetaData import make_metadata
from utl.代理.request_with_proxy import request_with_proxy
from CONFIG import CONFIG

grpc_err_log = loguru.logger.bind(user='grpc_err')
grpc_err_log.add(
    CONFIG.root_dir + 'grpc获取动态/src/' + "log/grpc_err.log",
    encoding="utf-8",
    enqueue=True,
    rotation="500MB",
    compression="zip",
    retention="15 days",
    filter=lambda record: record["extra"].get('user') == "grpc_err")


# Handle gRPC errors
def grpc_error(err):
    status = grpc.StatusCode.UNKNOWN
    details = str(err)
    if isinstance(err, grpc.RpcError):
        status = err.code()
        if err.details():
            details = err.details()
    return status, details


class RequestInterceptor(grpc.UnaryUnaryClientInterceptor):
    '''
    grpc请求拦截器
    '''

    def intercept_unary_unary(self, continuation, client_call_details, request):
        print("Method:", client_call_details.method)
        print("Request:", request)
        print("MetaData:", client_call_details.metadata)

        # 调用原始的 continuation，继续处理请求
        response = continuation(client_call_details, request)

        return response


class BiliGrpc:
    def __init__(self):
        self.__req = request_with_proxy()
        self.channel = None
        self.proxy = None
        self.channel_lock = threading.Lock()

    def __set_available_channel(self, proxy, channel):
        with self.channel_lock:
            self.proxy = proxy
            self.channel = channel

    def __get_random_channel(self):
        while 1:
            proxy = self.__req.get_one_rand_grpc_proxy()
            if proxy:
                options = [
                    ("grpc.http_proxy", proxy['proxy']['http']),
                ]
                channel = grpc.secure_channel('grpc.biliapi.net:443', grpc.ssl_channel_credentials(),
                                              options=options,
                                              compression=grpc.Compression.NoCompression
                                              )  # Connect to the gRPC server
                return proxy, channel
            else:
                print('无可用代理状态，休眠3分钟！')
                time.sleep(3 * 60)
                options = []

    def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        if type(dyn_ids) is not list:
            raise TypeError('dyn_ids must be a list!')
        if len(dyn_ids) == 0:
            return {}
        dyn_ids = [int(x) for x in dyn_ids]
        # proxy_server_address = sqlhelper.select_rand_proxy()['proxy']['https']
        # intercept_channel = grpc.intercept_channel(
        #     channel,
        #     # RequestInterceptor()
        # )

        while 1:
            proxy = self.proxy
            channel = self.channel
            if not channel:
                proxy, channel = self.__get_random_channel()
            dyn_details_req = dynamic_pb2.DynDetailsReq(
                dynamic_ids=json.dumps({'dyn_ids': dyn_ids}),
            )
            try:
                dynamic_client = dynamic_pb2_grpc.DynamicStub(channel)
                # print(dyn_details_req.SerializeToString())
                # ack = gen_random_access_key()
                ack = ''
                md = make_metadata(ack)

                dyn_all_resp, call = dynamic_client.DynDetails.with_call(dyn_details_req,
                                                                         metadata=md,
                                                                         timeout=10)
                ret_dict = MessageToDict(dyn_all_resp)
                if proxy != self.proxy:
                    self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    self.__set_available_channel(proxy, channel)
                return ret_dict
            except grpc.RpcError as e:
                stat, det = grpc_error(e)
                logging.warning(f"BiliGRPC error: {stat} - {proxy['proxy']}")
                if proxy == self.proxy:
                    self.__set_available_channel(None, None)
                score_change = -10
                if 'HTTP proxy returned response code 400' in det or 'OPENSSL_internal' in det:  # 400状态码表示代理可能是http1.1协议，不支持grpc的http2.0
                    score_change = -100
                # 已知的不重要的错误
                if det == 'Deadline Exceeded':
                    pass
                elif 'failed to connect to all addresses' in det:
                    pass
                elif 'OPENSSL_internal:TLSV1_ALERT_NO_APPLICATION_PROTOCOL.' in det:
                    pass
                elif 'OPENSSL_internal:WRONG_VERSION_NUMBER.' in det:
                    pass
                else:
                    logging.error(f"BiliGRPC error: {stat} - {det}\n{dyn_details_req}")  # 重大错误！
                self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                    score_change=score_change)

    def grpc_get_dynamic_detail_by_type_and_rid(self, rid: Union[int, str], dynamic_type: int = 2) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param dynamic_type:动态类型
        :param rid:动态rid
        :return:
        """
        if type(rid) is str and str.isdigit(rid):
            rid = int(rid)
        if type(rid) is not int:
            raise TypeError('rid must be number!')
        while 1:
            proxy = self.proxy
            channel = self.channel
            if not channel:
                proxy, channel = self.__get_random_channel()
            data_dict = {
                'share_id': '3',
                'dyn_type': dynamic_type,
                'rid': rid,
                'local_time': 8,
                'share_mode': 3,
                'from': 'opus.detail',
                'player_args': PlayerArgs(qn=32, fnval=random.randint(130, 200)),
                'config': Config()
            }
            msg = dynamic_pb2.DynDetailReq(**data_dict)
            proto = msg.SerializeToString()
            data = b"\0" + len(proto).to_bytes(4, "big") + proto
            headers = {
                # "User-Agent": "Dalvik/2.1.0 (Linux; Android) os/android",
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/grpc",
                # "x-bili-device-bin": ""
            }
            headers.update(dict(make_metadata("")))
            for k, v in list(headers.items()):
                if k == 'user-agent':
                    headers.pop(k)
                if k.endswith('-bin'):
                    if type(v) == bytes:
                        headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
            try:
                with httpx.Client(proxies={
                    'http://': proxy['proxy']['http'],
                    'https://': proxy['proxy']['https']},
                        verify=False
                ) as client:
                    resp = client.post("https://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynDetail", data=data,
                                       headers=headers,
                                       )
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if resp.headers.get('bili-status-code') == '-352' or resp.headers.get('grpc-Message') == '-352':
                    grpc_err_log.error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    raise MY_Error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}')
                gresp = dynamic_pb2.DynDetailReply()
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy != self.proxy:
                    self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                loguru.logger.debug(f'获取grpc请求成功代理：{proxy["proxy"]}')
                self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                return resp_dict
            except Exception as err:
                score_change = -10
                logging.error(f"BiliGRPC error: {err} - {proxy['proxy']}")
                if '-352' in str(err):
                    score_change = 0
                if proxy == self.proxy:
                    self.__set_available_channel(None, None)
                self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                    score_change=score_change)

    def grpc_get_space_dyn_by_uid(self, uid: Union[str, int], history_offset: str = '', page: int = 1) -> dict:
        """
         获取up空间
        :param uid:
        :param history_offset:
        :param page:
        :return:
        """
        if type(uid) is str and str.isdigit(uid):
            uid = int(uid)
        if type(uid) is not int or type(history_offset) is not str:
            raise TypeError(
                f'uid must be a number and history_offset must be str! uid:{uid} history_offset:{history_offset}')
        while 1:
            proxy = self.proxy
            channel = self.channel
            if not channel:
                proxy, channel = self.__get_random_channel()
            data_dict = {
                'host_uid': int(uid),
                'history_offset': history_offset,
                'local_time': 8,
                'page': page,
                'from': 'space'
            }
            msg = dynamic_pb2.DynSpaceReq(**data_dict)
            proto = msg.SerializeToString()
            data = b"\0" + len(proto).to_bytes(4, "big") + proto
            headers = {
                # "User-Agent": "Dalvik/2.1.0 (Linux; Android) os/android",
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/grpc",
                # "x-bili-device-bin": ""
            }
            headers.update(dict(make_metadata("")))
            for k, v in list(headers.items()):
                if k == 'user-agent':
                    headers.pop(k)
                if k.endswith('-bin'):
                    if type(v) == bytes:
                        headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
            try:
                with httpx.Client(proxies={
                    'http://': proxy['proxy']['http'],
                    'https://': proxy['proxy']['https']
                },
                        verify=False, ) as client:
                    resp = client.post("https://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace", data=data,
                                       headers=headers,
                                       )
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if resp.headers.get('bili-status-code') == '-352' or resp.headers.get('grpc-Message') == '-352':
                    grpc_err_log.error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    raise MY_Error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}')
                gresp = dynamic_pb2.DynSpaceRsp()
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy != self.proxy:
                    self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                loguru.logger.debug(f'获取grpc请求成功代理：{proxy["proxy"]}')
                self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                return resp_dict
            except Exception as err:
                score_change = -10
                logging.error(f"BiliGRPC error: {err} - {proxy['proxy']}")
                if '-352' in str(err):
                    score_change = 0
                if proxy == self.proxy:
                    self.__set_available_channel(None, None)
                self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                    score_change=score_change)


class MY_Error(ValueError):
    pass


def test():
    t = BiliGrpc()
    resp = t.grpc_get_space_dyn_by_uid(
        2)
    print(resp)


if __name__ == '__main__':
    test()
