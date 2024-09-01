# -*- coding: utf-8 -*-
# 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
import os
import string
from dataclasses import dataclass
import asyncio
import base64
import copy
import datetime
import random
import time
import traceback
from typing import Union
import grpc
from grpc import aio
import json
from bilibili.app.dynamic.v2.dynamic_pb2 import Config, AdParam
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from grpc获取动态.Utils.MQServer.VoucherMQServer import VoucherRabbitMQ
from grpc获取动态.grpc.bapi.biliapi import get_latest_version_builds
from grpc获取动态.grpc.bapi.models import LatestVersionBuild
from grpc获取动态.grpc.makeMetaData import make_metadata, is_useable_Dalvik, gen_trace_id
from grpc获取动态.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, APIExClimbWuzhi
from utl.代理.request_with_proxy import request_with_proxy
from CONFIG import CONFIG
from grpc获取动态.Utils.GrpcProxyUtils import GrpcProxyTools
from utl.代理.SealedRequests import MYASYNCHTTPX
from loguru import logger
from urllib.parse import urlparse


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


@dataclass
class MetaDataWrapper:
    md: tuple
    expire_ts: int
    version_name: str
    times_352: int = 0

    @property
    def able(self) -> bool:
        if self.times_352 >= 10:
            return False
        else:
            return True


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
        self.metadata_list = []  # 设备ip列表
        self.queue_num = 0
        self.my_proxy_addr = CONFIG.my_ipv6_addr
        self.grpc_api_any_log = logger.bind(user=__name__ + "AnyElse")
        self.grpc_api_any_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_grpc_api_log.log"),
                                  level="ERROR",
                                  encoding="utf-8",
                                  enqueue=True,
                                  rotation="500MB",
                                  compression="zip",
                                  retention="15 days",
                                  filter=lambda record: record["extra"].get('user') == __name__ + "AnyElse",
                                  )
        self.s = MYASYNCHTTPX()
        self.GrpcProxyTools = GrpcProxyTools()  # 实例化
        # 版本号根据 ```https://app.bilibili.com/x/v2/version?mobi_app=android```这个api获取
        self.version_name_build_list: [LatestVersionBuild] = [LatestVersionBuild(**x) for x in [
            {
                "build": 8000200,
                "version": "8.0.0"
            },
            {
                "build": 7810200,
                "version": "7.81.0"
            },
            {
                "build": 7800300,
                "version": "7.80.0"
            },
            {
                "build": 7790400,
                "version": "7.79.0"
            },
            {
                "build": 7780300,
                "version": "7.78.0"
            },
            {
                "build": 7770300,
                "version": "7.77.0"
            },
            {
                "build": 7760700,
                "version": "7.76.0"
            },
            {
                "build": 7750300,
                "version": "7.75.0"
            },
            {
                "build": 7740200,
                "version": "7.74.0"
            },
            {
                "build": 7730300,
                "version": "7.73.0"
            },
            {
                "build": 7720200,
                "version": "7.72.0"
            },
            {
                "build": 7710300,
                "version": "7.71.0"
            }
        ]]
        try:
            self.version_name_build_list: [LatestVersionBuild] = get_latest_version_builds()[:10]  # 获取最新的build
        except Exception as e:
            self.grpc_api_any_log.exception(e)
        self.ua = ("Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 os/android "
                   "model/22081212C mobi_app/android build/7630200 channel/bili innerVer/7630200 osVer/13 network/2")
        self.channel_list = ['bili', 'master', 'yyb', '360', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google']  # 渠道包列表
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
        self.timeout = 10
        self.cookies = None
        self.cookies_ts = 0
        self.metadata_lock = asyncio.Lock()
        self._352MQServer = VoucherRabbitMQ.Instance()

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
                self.grpc_api_any_log.warning(
                    f'上次获取cookie时间：{datetime.datetime.fromtimestamp(self.cookies_ts)} 时间过短！')
                if self.cookies:
                    return self.cookies
                await asyncio.sleep(10)
            self.cookies_ts = int(time.time())
            self.grpc_api_any_log.warning(f"COOKIE:{self.cookies}失效！正在尝试获取新的认证过的cookie！")
            cookies = await self.__get_available_cookies(useProxy)
        self.cookies = cookies
        return cookies

    async def __get_available_cookies(self, useProxy=False) -> str:
        try:
            return await ExClimbWuzhi.verifyExClimbWuzhi(
                my_cfg=APIExClimbWuzhi(
                    ua=self.ua
                ),
                use_proxy=useProxy
            )
        except:
            traceback.print_exc()
            await asyncio.sleep(2 * 3600)
            return await self.__get_available_cookies()

    async def __set_available_channel(self, proxy, channel):
        self.proxy = proxy
        self.channel = channel

    async def __get_random_channel(self):
        while 1:
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
                logger.critical('无可用代理状态！')
                await asyncio.sleep(3)

    async def metadata_productor(self, proxy) -> MetaDataWrapper:
        """
        metadata生产者
        :param proxy:
        :return:
        """
        await self.metadata_lock.acquire()
        if self.queue_num < 20:
            self.queue_num += 1
            metadata: Union[MetaDataWrapper, None] = None
        else:
            while 1:
                if len(self.metadata_list) > 0:
                    metadata = random.choice(self.metadata_list)
                    if metadata.expire_ts < time.time() or metadata.able == False:
                        self.queue_num -= 1
                        self.metadata_list.remove(metadata)
                        continue
                    break
                if len(self.metadata_list) == 0 and self.queue_num == 0:
                    self.queue_num += 1
                    metadata = None
                    break
                await asyncio.sleep(1)
        self.metadata_lock.release()
        if not metadata:
            while 1:
                brand = random.choice(self.brand_list)
                Dalvik = random.choice(self.Dalvik_list)
                while not is_useable_Dalvik(Dalvik):
                    Dalvik = random.choice(self.Dalvik_list)
                version_name_build: LatestVersionBuild = random.choice(self.version_name_build_list)
                version_name = version_name_build.version
                build = version_name_build.build
                channel = random.choice(self.channel_list)
                logger.debug(
                    f'当前metadata池数量：{len(self.metadata_list)}，总共{self.queue_num}个meta信息，前往获取新的metadata')
                md = await make_metadata("",
                                         brand=brand,
                                         Dalvik=Dalvik,
                                         version_name=version_name,
                                         build=build,
                                         channel=channel,
                                         proxy=proxy
                                         )
                if not dict(md).get('x-bili-ticket'):
                    logger.error(f'bili-ticket获取失败！{md}')
                    await asyncio.sleep(30)
                    continue
                else:
                    break
            metadata = MetaDataWrapper(
                md=md,
                expire_ts=int(time.time() + 0.5 * 3600),
                version_name=version_name
            )  # TODO 时间长一点应该没问题吧
            self.metadata_list.append(metadata)
        logger.debug(f'当前metadata池数量：{len(self.metadata_list)}')

        return metadata

    async def handle_grpc_request(self, url: str, grpc_req_message, grpc_resp_msg, cookie_flag: bool,
                                  func_name: str = ""):
        """
        处理grpc请求
        :param url:
        :param grpc_req_message: dynamic_pb2.DynDetailReq(**data_dict)
        :param grpc_resp_msg: dynamic_pb2.DynDetailReply()
        :param cookie_flag:
        :return:
        """
        proxy = {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}}
        channel = None
        ipv6_proxy_weights = 5
        real_proxy_weights = 5
        while 1:
            proxy_flag = random.choices([True, False], weights=[real_proxy_weights, ipv6_proxy_weights], k=1)[0]

            ip_status = None
            cookies = None
            if proxy_flag:
                proxy, channel = await self.__get_random_channel()
                if cookie_flag:
                    cookies = await self.__set_available_cookies(self.cookies)
                if not await self.GrpcProxyTools.check_ip_status(proxy['proxy']['http']):
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=10)
                ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
            else:
                proxy = {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}}
                if cookie_flag:
                    self.cookies = await ExClimbWuzhi.verifyExClimbWuzhi(use_proxy=False, my_cfg=APIExClimbWuzhi(
                        ua=self.ua
                    ))
                    cookies = self.cookies
            msg = grpc_req_message
            proto = msg.SerializeToString()
            data = b"\0" + len(proto).to_bytes(4, "big") + proto
            headers = {
                "Content-Type": "application/grpc",
                'Connection': 'close',
                # "user-agent": ua,
                # 'user-agent': random.choice(CONFIG.UA_LIST),
            }
            if cookie_flag and cookies:
                headers.update({
                    "cookie": cookies
                })
            md = await self.metadata_productor({'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}})

            try:
                ret_dict = dict(md.md)
                ret_dict['x-bili-trace-id'] = gen_trace_id()
                headers.update(ret_dict)
                headers_copy = copy.deepcopy(headers)
                for k, v in list(headers_copy.items()):
                    if k.endswith('-bin'):
                        if isinstance(v, bytes):
                            headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
                if not headers.get('x-bili-ticket'):
                    raise ValueError('headers中没有有效的x-bili-ticket！')
                resp = await self.s.request(method="post",
                                            url=url,
                                            data=data,
                                            headers=headers, timeout=self.timeout, proxies={
                        'http': proxy['proxy']['http'],
                        'https': proxy['proxy']['https']} if proxy_flag else proxy.get('proxy'), verify=False)
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if '-352' in str(resp.headers.get('bili-status-code')) or \
                        '-352' in str(resp.headers.get('grpc-Message')) or \
                        '-412' in str(resp.headers.get('bili-status-code')) or \
                        '-412' in str(resp.headers.get('grpc-Message')):  # -352的话尝试把这个metadata丢弃
                    self.grpc_api_any_log.warning(
                        f'{func_name}\t{url} -352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    parsed_url = urlparse(url)
                    self._352MQServer.push_voucher_info(
                        voucher=resp.headers.get('x-bili-gaia-vvoucher'),
                        ua=headers.get('user-agent'),
                        ck=headers.get('buvid'),
                        origin=f"https://{parsed_url.netloc}",
                        referer=url,
                        ticket=headers.get('x-bili-ticket'),
                        version=md.version_name
                    )
                    raise MY_Error(
                        f'{func_name}\t-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}\n{grpc_req_message}')
                gresp = grpc_resp_msg
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy_flag:
                    if proxy != self.proxy:
                        await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    await self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                if ip_status:
                    origin_available = ip_status.available
                    ip_status.available = True
                    if origin_available != ip_status.available:
                        await self.GrpcProxyTools.set_ip_status(ip_status)
                self.grpc_api_any_log.info(
                    f'{func_name}\t{url} 获取grpc动态请求成功代理：{proxy.get("proxy")} {grpc_req_message}\n{headers}'
                    f'\n当前可用代理数量：{self.GrpcProxyTools.avalibleNum}/{self.GrpcProxyTools.allNum}')  # 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
                if md.times_352 > 0:
                    md.times_352 = 0
                return resp_dict
            except Exception as err:
                if str(err) == 'Error parsing message':
                    self.grpc_api_any_log.error(f'{func_name}\t解析grpc消息失败！\n{resp.text}\n{resp.content.hex()}')
                    return {}
                origin_available = False
                if ip_status:
                    origin_available = ip_status.available
                    ip_status.available = False
                score_change = -10
                self.grpc_api_any_log.warning(
                    f"{func_name}\t{url} grpc_get_dynamic_detail_by_type_and_rid\n BiliGRPC error: {err}\n"
                    f"{proxy['proxy'] if proxy_flag else proxy.get('proxy')}\n{err}\n{type(err)}")
                if proxy_flag:
                    if proxy == self.proxy:
                        await self.__set_available_channel(None, None)
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=score_change)
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 1
                if '352' in str(err) or '412' in str(err):
                    score_change = 10
                    ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                    self.grpc_api_any_log.warning(
                        f"{ip_status.ip} ip获取次数到达{ip_status.counter}次，出现-352现象，舍弃当前metadata！")
                    if cookie_flag:
                        if ip_status and ip_status.counter > 10:
                            pass
                        else:
                            if cookies == self.cookies:
                                self.cookies = None
                                await self.__set_available_cookies(None, useProxy=True)
                    md.times_352 += 1  # -352报错就增加一次352次数，满了之后舍弃
                    if proxy['proxy']['http'] != self.my_proxy_addr:
                        if not ip_status:
                            ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                        ip_status.max_counter_ts = int(time.time())
                        ip_status.code = -352
                        ip_status.available = False
                        if origin_available != ip_status.available:
                            await self.GrpcProxyTools.set_ip_status(ip_status)
                    else:

                        await asyncio.sleep(2)  # 本地ipv6状态-352的情况下，等待一段时间，破解验证码之后再执行

    # region 第三方grpc库发起的请求
    async def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        """
        通过grpc客户端请求的，不太好一起统一处理
        通过动态id的列表批量获取动态详情，但是需要有所有的动态id，不能用，很难受
        :param dyn_ids:
        :return:
        """
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
                md = await make_metadata(ack, proxy=proxy)

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
                self.grpc_api_any_log.warning(f"\nBiliGRPC error: {stat} - {proxy['proxy']}")
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
                    self.grpc_api_any_log.warning(
                        f"{dyn_ids} grpc_api_get_DynDetails\n BiliGRPC error: {stat} - {det}\n{dyn_details_req}\n{type(e)}")  # 重大错误！
                await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                          score_change=score_change)

    # endregion

    # region grpc请求接口
    async def grpc_get_dynamic_detail_by_type_and_rid(self, rid: Union[int, str], dynamic_type: int = 2,
                                                      proxy_flag=False, cookie_flag=False) -> dict:
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
        data_dict = {
            'uid': random.randint(1, 9223372036854775807),
            'dyn_type': dynamic_type,
            'rid': rid,
            "ad_param": AdParam(
                ad_extra=''
                # ''.join(random.choices(string.ascii_uppercase + string.digits,
                #                                 k=random.choice([x for x in range(1300, 1350)])))
            ),
            'player_args': PlayerArgs(qn=32, fnval=272, voice_balance=1),
            'share_id': 'dt.dt-detail.0.0.pv',
            'share_mode': 3,
            'local_time': 8,
            'config': Config()
        }
        msg = dynamic_pb2.DynDetailReq(**data_dict)
        gresp = dynamic_pb2.DynDetailReply()
        return await self.handle_grpc_request(url, msg, gresp, cookie_flag)

    async def grpc_get_space_dyn_by_uid(self, uid: Union[str, int], history_offset: str = '', page: int = 1,
                                        proxy_flag: bool = False) -> dict:
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
        url = "http://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace"
        data_dict = {
            'host_uid': int(uid),
            'history_offset': history_offset,
            'local_time': 8,
            'page': page,
            'from': 'space'
        }
        msg = dynamic_pb2.DynSpaceReq(**data_dict)
        gresp = dynamic_pb2.DynSpaceRsp()
        return await self.handle_grpc_request(url, msg, gresp, False, 'grpc_get_space_dyn_by_uid')

    # endregion


class MY_Error(ValueError):
    pass


async def _test():
    t = BiliGrpc()
    resp = await t.grpc_get_dynamic_detail_by_type_and_rid(313189161, 2, False)  # 没有ticket的情况下一个ip大概50次就会出现-352
    print(resp)


if __name__ == '__main__':
    asyncio.run(_test())
