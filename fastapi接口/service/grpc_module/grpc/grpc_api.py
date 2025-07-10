# -*- coding: utf-8 -*-
# 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
import asyncio
import base64
import datetime
import gzip
import json
import os
import random
import time
import uuid
from ssl import SSLError
from typing import Union
from urllib.parse import urlparse

import curl_cffi
import grpc
from exceptiongroup import ExceptionGroup
from google.protobuf.json_format import MessageToDict  # 这是第三方包，不用管
from google.protobuf.message import DecodeError, EncodeError
from httpx import ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout, ReadError, InvalidURL, \
    Response, WriteError, NetworkError
from python_socks._errors import ProxyConnectionError, ProxyTimeoutError, ProxyError as SocksProxyError
from socksio import ProtocolError

from CONFIG import CONFIG
from fastapi接口.log.base_log import BiliGrpcApi_logger
from fastapi接口.service.grpc_module.Models.CustomRequestErrorModel import Request352Error
from fastapi接口.service.grpc_module.Models.GrpcApiBaseModel import MetaDataWrapper
from fastapi接口.service.grpc_module.Utils.metadata.makeMetaData import make_metadata, is_useable_Dalvik, gen_trace_id
from fastapi接口.service.grpc_module.Utils.极验.极验点击验证码 import  geetest_v3_breaker
from fastapi接口.service.grpc_module.grpc.bapi.biliapi import get_latest_version_builds, resource_abtest_abserver
from fastapi接口.service.grpc_module.grpc.bapi.models import LatestVersionBuild
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.app.dynamic.v2.dynamic_pb2 import Config, DynDetailReq, \
    DynDetailReply, DynDetailsReq, DynSpaceReq, DynSpaceRsp
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.app.dynamic.v2.dynamic_pb2_grpc import DynamicStub
from fastapi接口.service.grpc_module.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, \
    APIExClimbWuzhi
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.数据库操作.ProxyCommOp import get_available_proxy
from utl.代理.数据库操作.ProxyEvent import handle_proxy_succ, handle_proxy_request_fail, handle_proxy_352, \
    handle_proxy_unknown_err
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from utl.代理.数据库操作.comm import get_scheme_ip_port_form_proxy_dict

current_file_path = os.path.abspath(os.path.dirname(__file__))


def grpc_error(err):
    status = grpc.StatusCode.UNKNOWN
    details = str(err)
    if isinstance(err, grpc.RpcError):
        status = err.code()
        if err.details():
            details = err.details()
    return status, details


class BiliGrpc:
    def __init__(self):
        self.debug_mode = False
        self.metadata_pool_size = 30  # 元数据（headers）池大小
        self.metadata_list = []  # 元数据（headers）池大小列表
        self.queue_num = 0
        self.my_proxy_addr = CONFIG.my_ipv6_addr
        self.grpc_api_any_log = BiliGrpcApi_logger
        # 版本号根据 ```https://app.bilibili.com/x/v2/version?mobi_app=android```这个api获取
        self.version_name_build_list: list[LatestVersionBuild] = [LatestVersionBuild(**x) for x in [
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
            self.version_name_build_list: list[LatestVersionBuild] = get_latest_version_builds()[:70]  # 获取最新的build
        except Exception as e:
            self.grpc_api_any_log.exception(e)
        self.ua = ("Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 os/android "
                   "model/22081212C mobi_app/android build/7630200 channel/bili innerVer/7630200 osVer/13 network/2")
        self.channel_list = ['master', '360', 'bili', 'xiaomi', 'google']  # 渠道包列表
        with open(os.path.join(
                current_file_path,
                '../Utils/user-agents_dalvik_application_2-1.json'
        ), 'r',
                encoding='utf-8') as f:
            self.Dalvik_list = json.loads(f.read())
            self.Dalvik_list = list(filter(lambda x: 'Dalvik/2.1.0' in x
                                                     and '[ip:' not in x
                                                     and 'AppleWebKit' not in x
                                           , self.Dalvik_list))
        self.brand_list = ['Xiaomi', 'Huawei', 'Samsung', 'Vivo', 'Oppo', 'Oneplus', 'Meizu', 'Nubia', 'Sony', 'Zte',
                           'Honor', 'Lenovo', 'Lg', 'Blu', 'Asus', 'Panasonic', 'Htc', 'Nokia', 'Motorola', 'Realme',
                           'Alcatel', 'BlackBerry']
        self.channel = None
        self.proxy: ProxyTab | None = None

        self.timeout = 30
        self.cookies = None
        self.cookies_ts = 0
        self.latest_352_ts = 0

    @property
    def proxy_id(self):
        return self.proxy.proxy_id if self.proxy else 0

    # region 准备工作
    async def _prepare_ck_proxy(self):
        proxy = self.proxy
        channel = self.channel
        cookies = await self.__set_available_cookies(self.cookies)
        if not channel:
            proxy, channel = await self._get_random_channel(is_need_channel=True)

        return proxy, channel, cookies

    async def __set_available_cookies(self, cookies, useProxy=False):
        if not cookies:
            while int(time.time()) - self.cookies_ts < 3 * 60:
                self.grpc_api_any_log.debug(
                    f'上次获取cookie时间：{datetime.datetime.fromtimestamp(self.cookies_ts)} 时间过短！')
                if self.cookies:
                    return self.cookies
                await asyncio.sleep(10)
            self.cookies_ts = int(time.time())
            self.grpc_api_any_log.debug(f"COOKIE:{self.cookies}失效！正在尝试获取新的认证过的cookie！")
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
        except Exception as e:
            self.grpc_api_any_log.exception(e)
            return await self.__get_available_cookies()

    async def _get_random_channel(self, is_need_channel: bool = False, is_use_available_proxy: bool = False) -> tuple[
        ProxyTab, grpc.aio.Channel | None]:
        proxy_tab, _ = await get_available_proxy(is_use_available_proxy)
        channel = None
        if is_need_channel:
            channel = grpc.aio.secure_channel('grpc.biliapi.net:443', grpc.ssl_channel_credentials(),
                                              options=[],
                                              compression=grpc.Compression.NoCompression
                                              )  # Connect to the gRPC server
        return proxy_tab, channel

    # endregion

    async def metadata_productor(self, proxy) -> MetaDataWrapper:
        """
        metadata生产者
        :param proxy:
        :return:
        """
        if self.queue_num < self.metadata_pool_size:
            self.queue_num += 1
            metadata: Union[MetaDataWrapper, None] = None
        else:
            while 1:
                if len(self.metadata_list) > 0:
                    metadata = random.choice(self.metadata_list)
                    if metadata.is_need_delete:
                        self.queue_num -= 1
                        self.metadata_list.remove(metadata)
                        continue
                    # if not metadata.able(num_add=False):
                    #     await asyncio.sleep(10)
                    #     continue
                    break
                if len(self.metadata_list) == 0 and self.queue_num == 0:
                    self.queue_num += 1
                    metadata = None
                    break
                await asyncio.sleep(1)
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
                # self.grpc_api_any_log.debug(
                #     f'当前metadata池数量：{len(self.metadata_list)}，总共{self.queue_num}个meta信息，前往获取新的metadata')
                md, ticket_resp, metadat_basic_info = await make_metadata(
                    "",
                    brand=brand,
                    Dalvik=Dalvik,
                    version_name=version_name,
                    build=build,
                    channel=channel,
                    proxy=proxy
                )
                session_id = uuid.uuid4().hex[0:8]
                md_dict = dict(md)
                ck = f'Buvid={md_dict.get("buvid")}'
                cfg = APIExClimbWuzhi()
                if not md_dict.get('x-bili-ticket'):
                    self.grpc_api_any_log.error(f'bili-ticket获取失败！{md}')
                    await asyncio.sleep(30)
                    continue
                else:
                    cfg = APIExClimbWuzhi(
                        ua=md_dict.get('user-agent'),
                        Buvid=md_dict.get('buvid'),
                        bili_ticket=ticket_resp.ticket,
                        bili_ticket_expires=ticket_resp.created_at + ticket_resp.ttl,
                    )
                    try:
                        ck = await ExClimbWuzhi.verifyExClimbWuzhi(
                            url="https://www.bilibili.com/",
                            my_cfg=cfg,
                            _from="h5"
                        )
                        await resource_abtest_abserver(
                            buvid=metadat_basic_info.buvid,
                            fp_local=metadat_basic_info.fp_local,
                            fp_remote=metadat_basic_info.fp_remote,
                            session_id=session_id,
                            guestid=metadat_basic_info.guestid,
                            app_version_name=metadat_basic_info.app_version_name,
                            model=metadat_basic_info.model,
                            app_build=metadat_basic_info.app_build,
                            channel=metadat_basic_info.channel,
                            osver=metadat_basic_info.osver,
                            ticket=metadat_basic_info.ticket,
                            brand=metadat_basic_info.brand,
                        )
                    except Exception as e:
                        # self.grpc_api_any_log.exception(f'激活cookie失败！')
                        ...
                    finally:
                        ...
                    break
            metadata = MetaDataWrapper(
                md=md,
                expire_ts=ticket_resp.created_at + ticket_resp.ttl,
                version_name=version_name,
                cookie=ck,
                session_id=session_id,
                guestid=metadat_basic_info.guestid,
                exclimb_wuzhi_cfg=cfg
            )
            self.metadata_list.append(metadata)
        # self.grpc_api_any_log.debug(f'当前metadata池数量：{len(self.metadata_list)}')
        return metadata

    async def handle_grpc_request(self, url: str, grpc_req_message, grpc_resp_msg, cookie_flag: bool,
                                  func_name: str = "", force_proxy: bool = False,
                                  force_non_proxy: bool = False):  # 连续请求20次出现-352
        """
        处理grpc请求
        :param force_non_proxy:  强制不使用代理，也就是直连
        :param force_proxy: 强制使用真实代理
        :param func_name:
        :param url:
        :param grpc_req_message: dynamic_pb2.DynDetailReq(**data_dict)
        :param grpc_resp_msg: dynamic_pb2.DynDetailReply()
        :param cookie_flag:
        :return:
        """
        md: MetaDataWrapper | None = None
        validate_token: str = ''
        channel = None
        ipv6_proxy_weights = 1
        real_proxy_weights = 1000
        while 1:
            # self.grpc_api_any_log.debug(f'距离上次352时间：{int(time.time()) - self.latest_352_ts}秒')
            if int(time.time()) - self.latest_352_ts > 30 * 60:
                proxy_flag = random.choices([True, False], weights=[
                    real_proxy_weights if real_proxy_weights >= 0 else 0,
                    ipv6_proxy_weights * 2 if ipv6_proxy_weights >= 0 else 0
                ], k=1)[0]  # 是否使用真实代理 True用真实代理 False用ipv6代理
            else:
                proxy_flag = False
                # random.choices([True, False], weights=[
                #     real_proxy_weights if real_proxy_weights >= 0 else 0,
                #     ipv6_proxy_weights if ipv6_proxy_weights >= 0 else 0
                # ], k=1)[0]
            if validate_token and int(time.time()) - self.latest_352_ts > 30 * 60:
                proxy_flag = False
            if force_proxy:
                proxy_flag = True
            if self.debug_mode:
                proxy_flag = False
            if int(time.time()) - self.latest_352_ts <= 30 * 60:
                proxy_flag = True
            cookies = None
            if proxy_flag:
                proxy, channel = await self._get_random_channel()
                if cookie_flag:
                    cookies = await self.__set_available_cookies(self.cookies)
            else:
                proxy: ProxyTab = ProxyTab(
                    **{
                        'proxy_id': 1,
                        'proxy': CONFIG.custom_proxy,
                        'status': 0,
                        'update_ts': 0,
                        'score': 10000,
                        'add_ts': 0,
                        'success_times': 10000,
                        'zhihu_status': 0,
                        'computed_proxy_str': CONFIG.my_ipv6_addr
                    }
                )

                if cookie_flag:
                    self.cookies = await ExClimbWuzhi.verifyExClimbWuzhi(use_proxy=True, my_cfg=APIExClimbWuzhi(
                        ua=self.ua
                    ))
                    cookies = self.cookies

            if force_non_proxy or not proxy:
                proxy_flag = False
            msg = grpc_req_message
            proto_bytes = msg.SerializeToString()
            headers = {
                "content-type": "application/grpc",
                # 'Connection': 'close',
                # "user-agent": ua,
                # 'user-agent': random.choice(CONFIG.UA_LIST),
            }
            if cookie_flag and cookies:
                headers.update({
                    "cookie": cookies
                })
            if (not md or not md.able(num_add=False)) and not validate_token:
                md: MetaDataWrapper = await self.metadata_productor(
                    {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}})
            md_dict = dict(md.md)
            headers.update(md_dict)
            if not headers.get('x-bili-ticket'):
                raise ValueError('headers中没有有效的x-bili-ticket！')
            new_headers = []
            for k, v in md.md:
                if isinstance(v, bytes):
                    new_headers.append((k, base64.b64encode(v).decode('utf-8').strip('=')))
                    continue
                if k == 'x-bili-trace-id':
                    new_headers.append((k, gen_trace_id()))
                    continue
                if k == 'x-bili-gaia-vtoken':
                    # if validate_token:
                    #     self.grpc_api_any_log.debug(f'x-bili-gaia-vtoken被覆盖！{validate_token}')
                    new_headers.append((k, validate_token if validate_token else ''))
                    continue
                if isinstance(v, str):
                    new_headers.append((k, v))
                else:
                    new_headers.append((k, ''))
                    self.grpc_api_any_log.critical(f'headers中出现了非法类型！{k}:{v}')
            headers.update(dict(new_headers))
            # for i in md.cookie.split(';'):
            #     new_headers += (('cookie', i.strip(),),)
            resp = Response(status_code=114514)
            try:
                if 'gzip' in headers.get('grpc-encoding'):
                    compressed_proto_bytes = gzip.compress(proto_bytes, compresslevel=6)
                    data = b"\01" + len(compressed_proto_bytes).to_bytes(4, "big") + compressed_proto_bytes
                else:
                    data = b"\01" + len(proto_bytes).to_bytes(4, "big") + proto_bytes

                resp = await my_async_httpx.request(method="post",
                                                    url=url,
                                                    data=data,
                                                    headers=tuple(new_headers),
                                                    # headers=dict(new_headers),
                                                    timeout=self.timeout,
                                                    proxies=proxy.proxy if not force_proxy else {
                                                        'http': self.my_proxy_addr, 'https': self.my_proxy_addr},
                                                    )
                resp.raise_for_status()
                md.able(num_add=True)
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if '-352' in str(resp.headers.get('bili-status-code')) or \
                        '-352' in str(resp.headers.get('grpc-Message')) or \
                        '-412' in str(resp.headers.get('bili-status-code')) or \
                        '-412' in str(resp.headers.get('grpc-Message')):  # -352的话尝试把这个metadata丢弃
                    self.grpc_api_any_log.critical(
                        f'\n-352报错！\n'
                        f'url:{url}\n'
                        f'body:{grpc_req_message}'
                        f'headers:{new_headers}\n'
                        f'token:{validate_token}\n'
                        f'{sqlalchemy_model_2_dict(proxy)}')
                    if not validate_token:
                        # self.grpc_api_any_log.debug(f'未携带validate_token报错-352')
                        parsed_url = urlparse(url)
                        validate_token = await geetest_v3_breaker.a_validate_form_voucher_ua(
                            v_voucher=resp.headers.get('x-bili-gaia-vvoucher'),
                            ua=headers.get('user-agent'),
                            ck=headers.get('buvid'),
                            ori=f"https://{parsed_url.netloc}",
                            ref=url,
                            ticket=headers.get('x-bili-ticket'),
                            version=md.version_name,
                            session_id=md.session_id,
                        )
                        await ExClimbWuzhi.verifyExClimbWuzhi(
                            url="https://www.bilibili.com/",
                            my_cfg=md.exclimb_wuzhi_cfg,
                            _from="h5"
                        )
                        if validate_token:
                            self.grpc_api_any_log.debug(f'获取到-352验证token:{validate_token}')
                            continue
                        else:
                            raise Request352Error(
                                f'{func_name}\t{url} metadata已经发起了{md.used_times}次有效请求，遇到-352，未获取到-352验证token',
                                -352
                            )
                    else:
                        raise Request352Error(
                            f'{func_name}\t{url} metadata已经发起了{md.used_times}次有效请求，携带validate_token{validate_token}请求依旧 -352报错-{proxy}\n{str(resp.headers)}\n{str(new_headers)}\n{str(data)}',
                            -352
                        )

                gresp = grpc_resp_msg
                if 'gzip' in headers.get('grpc-encoding'):
                    gresp.ParseFromString(gzip.decompress(resp.content[5:]))
                else:
                    gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy:
                    await handle_proxy_succ(proxy_tab=proxy, )
                # self.grpc_api_any_log.critical(
                #     f'{func_name}\t{url} \n获取grpc动态请求成功代理：{proxy.proxy} \n{grpc_req_message}\n{new_headers}')  # 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
                md.times_352 = 0
                return resp_dict
            except (
                    ConnectionError, ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout,
                    ReadError, WriteError,
                    InvalidURL, NetworkError, ValueError, OverflowError, ExceptionGroup, ProxyConnectionError,
                    ProxyTimeoutError, SocksProxyError, ProtocolError, SSLError,
                    curl_cffi.requests.exceptions.ConnectionError,
                    curl_cffi.requests.exceptions.ProxyError, curl_cffi.requests.exceptions.SSLError,
                    curl_cffi.requests.exceptions.Timeout, curl_cffi.requests.exceptions.HTTPError

            ) as httpx_err:
                if proxy_flag:
                    await handle_proxy_request_fail(proxy_tab=proxy, )
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 20
            except Request352Error as _352_err:
                md.times_352 += 1  # -352报错就增加一次352次数，满了之后舍弃
                ipv6_proxy_weights -= 10
                if proxy:
                    if get_scheme_ip_port_form_proxy_dict(proxy.proxy) == self.my_proxy_addr:
                        self.latest_352_ts = int(time.time())
                        self.grpc_api_any_log.debug(f'设置本地代理最后-352时间为：{self.latest_352_ts}')
                    await handle_proxy_352(
                        proxy_tab=proxy,
                    )
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 20
            except Exception as err:
                if type(err) == DecodeError or type(err) == EncodeError:
                    self.grpc_api_any_log.error(
                        f'{func_name}\t解析grpc消息失败！\n{url}\n{grpc_req_message}\n{resp.text}\n{resp.content.hex()}')
                    if proxy:
                        await handle_proxy_succ(proxy_tab=proxy, )
                    return {}

                self.grpc_api_any_log.exception(
                    f"{func_name}\n{grpc_req_message}\n{proxy.proxy}\n{url} grpc_get_dynamic_detail_by_type_and_rid\nBiliGRPC error: {err}\n"
                    f"{new_headers}\n"
                    f"{proxy.proxy}")
                if proxy:
                    await handle_proxy_unknown_err(proxy_tab=proxy, )
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 20
                validate_token = ""

    # region 第三方grpc库发起的请求
    async def grpc_api_get_DynDetails(self, dyn_ids: list[int]) -> dict:
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
            dyn_details_req = DynDetailsReq(
                dynamic_ids=json.dumps({'dyn_ids': dyn_ids}),
            )
            try:
                dynamic_client = DynamicStub(channel)
                # print(dyn_details_req.SerializeToString())
                # ack = gen_random_access_key()
                ack = ''
                md, ticket, metadat_basic_info = await make_metadata(ack)

                dyn_all_resp = await dynamic_client.DynDetails(dyn_details_req,
                                                               metadata=md,
                                                               timeout=self.timeout)
                ret_dict = MessageToDict(dyn_all_resp)
                if proxy.proxy_id != self.proxy_id:
                    proxy.status = 0
                    await SQLHelper.update_to_proxy_list(proxy, 10)
                return ret_dict
            except grpc.RpcError as e:
                stat, det = grpc_error(e)
                self.grpc_api_any_log.critical(f"\nBiliGRPC error: {stat} - {proxy['proxy']}")
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
                proxy.status = -412
                await SQLHelper.update_to_proxy_list(proxy, score_change)

    # endregion

    # region grpc请求接口
    async def grpc_get_dynamic_detail_by_type_and_rid(self, rid: Union[int, str], dynamic_type: int = 2,
                                                      proxy_flag=False, cookie_flag=False,
                                                      force_proxy: bool = False) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param force_proxy:
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
        url = "https://grpc.biliapi.net/bilibili.app.dynamic.v2.Dynamic/DynDetail"
        data_dict = {
            # 'uid': random.randint(1, 3537105317792299),
            'dyn_type': dynamic_type,
            'rid': rid,
            # "ad_param": AdParam(
            #     ad_extra=''.join(random.choices(string.ascii_uppercase + string.digits,
            #                                     k=random.choice([x for x in range(1300, 1350)])))
            # ),
            'player_args': PlayerArgs(qn=32, fnval=272, voice_balance=1, voice_any=1),
            'share_id': 'dt.dt-detail.0.0.pv',
            'share_mode': 3,
            'local_time': 8,
            'config': Config()
        }
        msg = DynDetailReq(**data_dict)
        gresp = DynDetailReply()
        return await self.handle_grpc_request(url, msg, gresp, cookie_flag, force_proxy=force_proxy)

    async def grpc_get_dynamic_detail_by_dynamic_id(self, dynamic_id: int | str,
                                                    proxy_flag=False, cookie_flag=False,
                                                    force_proxy: bool = False) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param force_proxy:
        :param cookie_flag: 是否使用cookie
        :param proxy_flag:
        :param dynamic_type:动态类型
        :param rid:动态rid
        :return:
        """
        if type(dynamic_id) is int:
            dynamic_id = str(dynamic_id)
        if type(dynamic_id) is not str or not str.isdigit(dynamic_id):
            raise TypeError(f'dynamic_id must be string type number! dynamic_id:{dynamic_id}')
        url = "https://grpc.biliapi.net/bilibili.app.dynamic.v2.Dynamic/DynDetail"
        data_dict = {
            # 'uid': random.randint(1, 3537105317792299),
            'dynamic_id': dynamic_id,
            # "ad_param": AdParam(
            #     # ad_extra='E86F4CFF1F8FA890A75155EEAA51E6AE4FA9DBE62FCE708186D0CE5EF37B86948620D8BA1D991685B1288E2EDE09C6D52F8C2D33D59872EAE1EB776D11F71523CE1AF2112D8A950B98F6A1A48F848BC65E3D1B2687A17E44CDDEF6F0174F5E6548175C99B236CB32EBBE9DD7819D2DA0E272638B4DD5D4B27AD4119C056FA5362A495A2A482E35BBDD264A1829624B4446583ACCDDC6F867B3B7D0A53A7E6863D8425D19899FF591BAF3205F2A2051DDF7D60C649D9DE5221DFC48D8F592FB31DB4A72ABD8960A8DA289EAFE1C5E61334854717F0627A8DD6A897240F3847F517ED311FDCC904D4A2B4183944BEB5C9E4080BD059A3B56D25219D4115F8861E8745D65144C4A7D906CE3A4C1BAD79D9F2E80D86CA43052937843D6A841FCE72295389B8428B90743BA06685D3880D342A51B8CCEF21C5D7BF64BB1917A245E8CBB20F79B40A08D4380CCD603179D6AD77F9ED906CE0007A3F1AEF1CD6703B739A245A81820550CE06FCA780D3F0A9C098FFAB6BEF2AC1C8D3448ACB27079E623C50AE141DEE943F26DCA8E8EDF32299A7BF8935E496CD3708ACA16114149C85C99E8A7B9B1EB5188620F531EB13A89254E0AC941706CC14F31C776DFB7D329F6DA649A425E058B4187D5EA0117C2107D518D10ADE56CA721DCFA53CD8688D4ADC151C338A2C74CA8DE46CB736D0743F7706C7D273CFB847FA3CE51BE6D976EF4739A6C3488199E15A4463DD7522DF5A43E8207BE32906748A59EF28AB065961B4D69AD1E000D2601C58EA27126A5A7A7D3E3DBCA9E743F75657FB53FED2391244D3A7331C8D08CA712D9E73BFBB45F41FA0DA2A4087C6148C0D78731EE9BBE877227EFC2633FC5D113ED7EF3300335151B5E65C5D493A9A6BDFEB8D317BDBE4DA1A2B433B3CDE87FFE40B3B2C1DCB316'
            #     # ad_extra=''.joi n(random.choices(string.ascii_uppercase + string.digits,
            #     #                                 k=random.choice([x for x in range(1300, 1350)])))
            # ),
            'player_args': PlayerArgs(qn=32, fnval=272, voice_balance=1, voice_any=1),
            'share_id': 'dt.dt-detail.0.0.pv',
            'share_mode': 3,
            'local_time': 8,
            'config': Config()
        }
        msg = DynDetailReq(**data_dict)
        gresp = DynDetailReply()
        return await self.handle_grpc_request(url, msg, gresp, cookie_flag, force_proxy=force_proxy)

    async def grpc_get_space_dyn_by_uid(self, uid: Union[str, int], history_offset: str = '', page: int = 1,
                                        proxy_flag: bool = False, force_non_proxy: bool = False) -> dict:
        """
         获取up空间
        :param force_non_proxy:
        :param proxy_flag:
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
        url = "https://grpc.biliapi.net/bilibili.app.dynamic.v2.Dynamic/DynSpace"
        data_dict = {
            'host_uid': int(uid),
            'history_offset': history_offset,
            'local_time': 8,
            'page': page,
            'from': 'space'
        }
        msg = DynSpaceReq(**data_dict)
        gresp = DynSpaceRsp()
        return await self.handle_grpc_request(url, msg, gresp, False, 'grpc_get_space_dyn_by_uid',
                                              force_non_proxy=force_non_proxy)

    # endregion


class MY_Error(ValueError):
    pass


bili_grpc = BiliGrpc()

if __name__ == '__main__':
    async def _test():
        bili_grpc.my_proxy_addr = 'http://127.0.0.1:8080'  # mitm代理默认地址
        result1 = await bili_grpc.grpc_get_dynamic_detail_by_type_and_rid(dynamic_type=2, rid=343543865,
                                                                          force_proxy=True)
        print(result1)


    asyncio.run(_test())
