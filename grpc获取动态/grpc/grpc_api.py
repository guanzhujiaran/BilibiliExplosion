# -*- coding: utf-8 -*-
import asyncio
import base64
import copy
import datetime
import random
import sys
import time
import traceback
from typing import Union
import grpc
from grpc import aio
import json
import httpx
from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from grpc获取动态.grpc.makeMetaData import make_metadata, is_useable_Dalvik
from grpc获取动态.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, APIExClimbWuzhi
from utl.代理.request_with_proxy import request_with_proxy
from CONFIG import CONFIG
from grpc获取动态.Utils.GrpcProxyUtils import GrpcProxyStatus, GrpcProxyTools
from utl.代理.SealedRequests import MYASYNCHTTPX
from loguru import logger


# grpc_err_log.add(
#     CONFIG.root_dir + 'grpc获取动态/src/' + "log/grpc_err.log",
#     encoding="utf-8",
#     enqueue=True,
#     rotation="500MB",
#     compression="zip",
#     retention="15 days",
#     filter=lambda record: record["extra"].get('user') == "grpc_err"
# )

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
        self.grpc_api_log = logger.bind(user=__name__,
                                        filter=lambda record: record["extra"].get('user') == __name__)
        self.s = MYASYNCHTTPX()
        self.GrpcProxyTools = GrpcProxyTools()  # 实例化
        self.version_name_build_list = [
            {  # 版本号的build对应的列表
                'build': 7630200,
                'version_name': '7.63.0'
            }
        ]
        self.ua = "Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 os/android model/22081212C mobi_app/android build/7630200 channel/bili innerVer/7630200 osVer/13 network/2"
        self.channel_list = ['bili', 'master', 'yyb', '360', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google']  # 渠道包列表
        self.Dalvik_brand_list = [
            {'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1)",  # T
             'brand': "Xiaomi"},
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 12; NOH-AN01 Build/HUAWEINOH-AN01)",  # T
                'brand': "Huawei"},
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 14; 2210132C Build/UKQ1.230705.002)",  # T
                'brand': "Xiaomi"},
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; Android 7.1.1; OPPO R11st Build/NMF26X; wv)",  # T
                'brand': "Oppo"
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 9; motorola g8play Build/PMD29.70-81)",  # T
                'brand': "Motorola"
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 12; SM-M127G Build/SP1A.210812.016)",  # T
                'brand': "Samsung"
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 13; moto g 5G (2022) Build/T1SAS33.73-40-7-7)",  # T
                'brand': "Motorola"
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 14; SM-A236U Build/UP1A.231005.007)",  # T
                'brand': 'Samsung'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 14; SM-G998W Build/UP1A.231005.007)",  # T
                'brand': 'Samsung'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 8.1.0; XP8800 Build/8A.0.0-07-8.1.0-12.27.00)",  # T
                'brand': 'Sonim'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 13; V2247 Build/TP1A.220624.014_SC)",  # T
                'brand': 'Vivo'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 14; SM-F711U1 Build/UP1A.231005.007)",  # T
                'brand': 'Samsung'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 6.0; M90+ Build/LMY47I)",  # T
                'brand': 'Newman'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 12; SM-G977P Build/SP1A.210812.016)",  # T
                'brand': 'Samsung'
            },
            {
                'Dalvik': "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6a Build/TQ3A.230605.010.A1)",  # T
                'brand': 'Google'
            }

        ]
        with open(CONFIG.root_dir + 'grpc获取动态/Utils/user-agents_dalvik_application_2-1.json', 'r',
                  encoding='utf-8') as f:
            self.Dalvik_list = json.loads(f.read())
            self.Dalvik_list = list(filter(lambda x: 'Dalvik/2.1.0' in x
                                                     and '[ip:' not in x
                                                     and 'AppleWebKit' not in x
                                           , self.Dalvik_list))
        self.brand_list = ['Xiaomi', 'Huawei', 'Samsung', 'Vivo', 'Oppo', 'Oneplus', 'Meizu', 'Nubia', 'Sony', 'Zte',
                           'Honor', 'Lenovo', 'Lg', 'Blu', 'Asus', 'Panasonic', 'Htc', 'Nokia', 'Motorola', 'Realme',
                           'Alcatel', 'BlackBerry']
        self.__req = request_with_proxy()
        self.channel = None
        self.proxy = None
        self.timeout = 30  # 30秒好像太长了时间
        self.cookies = None
        self.cookies_ts = 0

    async def _prepare_ck_proxy(self):
        proxy = self.proxy
        channel = self.channel
        cookies = await self.__set_available_cookies(self.cookies)
        if not channel:
            proxy, channel = await self.__get_random_channel()

        return proxy, channel, cookies

    async def __set_available_cookies(self, cookies, useProxy=False):
        if not cookies:
            while int(time.time()) - self.cookies_ts < 3 * 60:
                self.grpc_api_log.warning(
                    f'上次获取cookie时间：{datetime.datetime.fromtimestamp(self.cookies_ts)} 时间过短！')
                if self.cookies:
                    return self.cookies
                await asyncio.sleep(10)
            self.cookies_ts = int(time.time())
            self.grpc_api_log.warning(f"COOKIE:{self.cookies}失效！正在尝试获取新的认证过的cookie！")
            cookies = await self.__get_available_cookies(useProxy)
        self.cookies = cookies
        return cookies

    async def __get_available_cookies(self, useProxy=False) -> str:
        try:
            return await ExClimbWuzhi.verifyExClimbWuzhi(
                MYCFG=APIExClimbWuzhi(
                    ua=self.ua
                ),
                useProxy=useProxy
            )
        except:
            traceback.print_exc()
            await asyncio.sleep(2 * 3600)
            return await self.__get_available_cookies()

    async def __set_available_channel(self, proxy, channel):
        self.proxy = proxy
        self.channel = channel

    async def __get_random_channel(self):
        while 1:  # TODO:在这里添加判断是否使用可用的代理
            avaliable_ip_status = await self.GrpcProxyTools.get_rand_avaliable_ip_status()
            proxy = {}
            if avaliable_ip_status:
                proxy = await self.__req.get_grpc_proxy_by_ip(avaliable_ip_status.ip)
            if not proxy:
                proxy = await self.__req.get_one_rand_grpc_proxy()
            if proxy:
                options = [
                    ("grpc.http_proxy", proxy['proxy']['http']),
                ]
                channel = aio.secure_channel('grpc.biliapi.net:443', grpc.ssl_channel_credentials(),
                                             options=options,
                                             compression=grpc.Compression.NoCompression
                                             )  # Connect to the gRPC server
                return proxy, channel
            else:
                print('无可用代理状态，休眠3分钟！')
                await asyncio.sleep(3 * 60)
                options = []

    async def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        if type(dyn_ids) is not list:
            raise TypeError(f'dyn_ids must be a list!{dyn_ids}')
        if len(dyn_ids) == 0:
            return {}
        dyn_ids = [int(x) for x in dyn_ids]
        # proxy_server_address = sqlhelper.select_rand_proxy()['proxy']['https']
        # intercept_channel = grpc.intercept_channel(
        #     channel,
        #     # RequestInterceptor()
        # )

        while 1:
            proxy, channel, cookies = await self._prepare_ck_proxy()
            dyn_details_req = dynamic_pb2.DynDetailsReq(
                dynamic_ids=json.dumps({'dyn_ids': dyn_ids}),
            )
            try:
                dynamic_client = dynamic_pb2_grpc.DynamicStub(channel)
                # print(dyn_details_req.SerializeToString())
                # ack = gen_random_access_key()
                ack = ''
                md = make_metadata(ack)

                dyn_all_resp = await dynamic_client.DynDetails(dyn_details_req,
                                                               metadata=md,
                                                               timeout=self.timeout)
                ret_dict = MessageToDict(dyn_all_resp)
                if proxy != self.proxy:
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    await self.__set_available_channel(proxy, channel)
                return ret_dict
            except grpc.RpcError as e:
                stat, det = grpc_error(e)
                self.grpc_api_log.warning(f"\nBiliGRPC error: {stat} - {proxy['proxy']}")
                if proxy == self.proxy:
                    await self.__set_available_channel(None, None)
                score_change = -10
                if 'HTTP proxy returned response code 400' in det or 'OPENSSL_internal' in det:  # 400状态码表示代理可能是http1.1协议，不支持grpc的http2.0
                    score_change = -10
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
                    self.grpc_api_log.warning(
                        f"{dyn_ids} grpc_api_get_DynDetails\n BiliGRPC error: {stat} - {det}\n{dyn_details_req}\n{type(e)}")  # 重大错误！
                await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                          score_change=score_change)

    async def grpc_get_dynamic_detail_by_type_and_rid(self, rid: Union[int, str], dynamic_type: int = 2,
                                                      proxy_flag=True, cookie_flag=False) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param cookie_flag: 是否使用cookie
        :param proxy_flag:
        :param dynamic_type:动态类型
        :param rid:动态rid
        :return:
        """
        if type(rid) is str and str.isdigit(rid):
            rid = int(rid)
        if type(rid) is not int:
            raise TypeError(f'rid must be number! rid:{rid}')
        url = "http://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynDetail"
        # ua=CONFIG.UA_LIST[0]
        # ua = self.ua
        proxy = {'proxy': {'http': '', 'https': ''}}
        while 1:
            ip_status=None
            if proxy_flag:
                proxy, channel = await self.__get_random_channel()
                if cookie_flag:
                    cookies = await self.__set_available_cookies(self.cookies)
                if not await self.GrpcProxyTools.check_ip_status(proxy['proxy']['http']):
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=10)
            else:
                if cookie_flag:
                    self.cookies = await ExClimbWuzhi.verifyExClimbWuzhi(useProxy=False, MYCFG=APIExClimbWuzhi(
                        ua=self.ua
                    ))
                    cookies = self.cookies
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
                "Content-Type": "application/grpc",
                # 'Connection': 'close',
                # "User-Agent": ua,
                # 'User-Agent': random.choice(CONFIG.UA_LIST),
            }
            if cookie_flag:
                headers.update({
                    "Cookie": cookies
                })
            if proxy_flag:
                ip_status = await  self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                if ip_status.MetaData:
                    md = ip_status.MetaData
                else:
                    # Dalvik_brand = random.choice(self.Dalvik_brand_list)
                    brand = random.choice(self.brand_list)
                    Dalvik = random.choice(self.Dalvik_list)
                    while not is_useable_Dalvik(Dalvik):
                        Dalvik = random.choice(self.Dalvik_list)
                    version_name_build = random.choice(self.version_name_build_list)
                    version_name = version_name_build['version_name']
                    build = version_name_build['build']
                    channel = random.choice(self.channel_list)
                    md = make_metadata("",
                                       brand=brand,
                                       Dalvik=Dalvik,
                                       version_name=version_name,
                                       build=build,
                                       channel=channel)
                    ip_status.MetaData = md
            else:
                Dalvik_brand = random.choice(self.Dalvik_brand_list)
                brand = Dalvik_brand['brand']
                Dalvik = Dalvik_brand['Dalvik']
                version_name_build = random.choice(self.version_name_build_list)
                version_name = version_name_build['version_name']
                build = version_name_build['build']
                channel = random.choice(self.channel_list)
                md = make_metadata("",
                                   brand=brand,
                                   Dalvik=Dalvik,
                                   version_name=version_name,
                                   build=build,
                                   channel=channel)
            headers.update(dict(md))
            headers_copy = copy.deepcopy(headers)
            for k, v in list(headers_copy.items()):
                if k.endswith('-bin'):
                    if type(v) == bytes:
                        headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
            try:
                resp = await  self.s.request(method="post",
                                             url=url,
                                             data=data,
                                             headers=headers, timeout=self.timeout, proxies={
                        'http': proxy['proxy']['http'],
                        'https': proxy['proxy']['https']} if proxy_flag else None, verify=False)
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if '-352' in str(resp.headers.get('bili-status-code')) or \
                        '-352' in str(resp.headers.get('grpc-Message')) or \
                        '-412' in str(resp.headers.get('bili-status-code')) or \
                        '-412' in str(resp.headers.get('grpc-Message')):
                    self.grpc_api_log.warning(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    raise MY_Error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}')
                gresp = dynamic_pb2.DynDetailReply()
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy_flag:
                    if proxy != self.proxy:
                        await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    await self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                if ip_status:
                    ip_status.available=True
                self.grpc_api_log.info(
                    f'{rid} 获取grpc动态请求成功代理：{proxy["proxy"] if proxy_flag else None} {rid} grpc_get_dynamic_detail_by_type_and_rid\n{headers}'
                    f'\n当前可用代理数量：{len([x for x in self.GrpcProxyTools.ip_list if x.available])}')
                return resp_dict
            except Exception as err:
                if ip_status:
                    ip_status.available = False
                score_change = -10
                self.grpc_api_log.warning(
                    f"{rid} grpc_get_dynamic_detail_by_type_and_rid\n BiliGRPC error: {err} - {proxy['proxy'] if proxy_flag else None}\n{type(err)}")
                if '-352' in str(err) or '-412' in str(err):
                    score_change = 10
                    ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                    self.grpc_api_log.warning(f"{ip_status.ip} ip获取次数到达{ip_status.counter}次，出现-352现象！")
                    if cookie_flag:
                        if ip_status and ip_status.counter > 10:
                            pass
                        else:
                            if cookies == self.cookies:
                                self.cookies = None
                                await self.__set_available_cookies(None, useProxy=True)
                    if proxy['proxy']['http']:
                        if not ip_status:
                            ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                        ip_status.max_counter_ts=int(time.time())
                        ip_status.code=-352
                        ip_status.available=False
                if proxy_flag:
                    if proxy == self.proxy:
                        await self.__set_available_channel(None, None)
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=score_change)
                else:
                    await asyncio.sleep(114514)

    async def grpc_get_space_dyn_by_uid(self, uid: Union[str, int], history_offset: str = '', page: int = 1) -> dict:
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
            proxy, channel = await self.__get_random_channel()
            if not await self.GrpcProxyTools.check_ip_status(proxy['proxy']['http']):
                await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                          score_change=10)
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
                "Content-Type": "application/grpc",
                # 'Connection': 'close',
                # "User-Agent": ua,
                # 'User-Agent': random.choice(CONFIG.UA_LIST),
            }
            ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
            if ip_status.MetaData:
                md = ip_status.MetaData
            else:
                # Dalvik_brand = random.choice(self.Dalvik_brand_list)
                brand = random.choice(self.brand_list)
                Dalvik = random.choice(self.Dalvik_list)
                while not is_useable_Dalvik(Dalvik):
                    Dalvik = random.choice(self.Dalvik_list)
                version_name_build = random.choice(self.version_name_build_list)
                version_name = version_name_build['version_name']
                build = version_name_build['build']
                channel = random.choice(self.channel_list)
                md = make_metadata("",
                                   brand=brand,
                                   Dalvik=Dalvik,
                                   version_name=version_name,
                                   build=build,
                                   channel=channel)
                ip_status.MetaData = md
            headers.update(dict(md))
            headers_copy = copy.deepcopy(headers)
            for k, v in list(headers_copy.items()):
                if k.endswith('-bin'):
                    if type(v) == bytes:
                        headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
            try:
                # resp = requests.request(method="post",
                #                         url="https://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace",
                #                         data=data,
                #                         headers=headers, timeout=self.timeout, proxies={
                #         'http': proxy['proxy']['http'],
                #         'https': proxy['proxy']['https']
                #     })
                resp = await self.s.request(
                    method="post",
                    url="http://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace",
                    data=data,
                    headers=headers, timeout=self.timeout, proxies=proxy['proxy'], verify=False
                )
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if '-352' in str(resp.headers.get('bili-status-code')) or \
                        '-352' in str(resp.headers.get('grpc-Message')) or \
                        '-412' in str(resp.headers.get('bili-status-code')) or \
                        '-412' in str(resp.headers.get('grpc-Message')):
                    self.grpc_api_log.warning(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    raise MY_Error(f'-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}')
                gresp = dynamic_pb2.DynSpaceRsp()
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy != self.proxy:
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                await self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                ip_status.available = True
                self.grpc_api_log.info(
                    f'{uid} {history_offset} 获取grpc动态请求成功代理：{proxy["proxy"]} grpc_get_space_dyn_by_uid\n{headers}'
                    f'\n当前可用代理数量：{len([x for x in self.GrpcProxyTools.ip_list if x.available])}')
                return resp_dict
            except Exception as err:
                ip_status.available = False
                score_change = -10
                self.grpc_api_log.warning(
                    f"{uid} {history_offset} grpc_get_space_dyn_by_uid\n BiliGRPC error: {err} - {proxy['proxy']}\n{type(err)}")
                if '-352' in str(err) or '-412' in str(err):
                    score_change = 10
                    if proxy['proxy']['http']:
                        self.grpc_api_log.warning(f"{ip_status.ip} ip获取次数到达{ip_status.counter}次，出现-352现象！")
                        if not ip_status:
                            ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                        ip_status.max_counter_ts=int(time.time())
                        ip_status.code=-352
                        ip_status.available=False
                if proxy == self.proxy:
                    await self.__set_available_channel(None, None)
                await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                          score_change=score_change)



class MY_Error(ValueError):
    pass


async def test():
    t = BiliGrpc()
    resp = await t.grpc_get_dynamic_detail_by_type_and_rid(303765580, proxy_flag=False)
    print(resp)


if __name__ == '__main__':
    asyncio.run(test())
