# -*- coding: utf-8 -*-
# 由redis和mysql实现数据的统一
import asyncio
import random
import time
from dataclasses import dataclass
from functools import reduce
from json import JSONDecodeError
from ssl import SSLError

import curl_cffi
from exceptiongroup import ExceptionGroup
from httpx import ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout, ReadError, InvalidURL, \
    WriteError, NetworkError, TooManyRedirects, HTTPError
from python_socks._errors import ProxyConnectionError, ProxyTimeoutError, ProxyError as SocksProxyError
from socksio import ProtocolError

from CONFIG import CONFIG
from fastapi接口.log.base_log import request_with_proxy_logger, Voucher352_logger
from fastapi接口.models.AntiRisk.Bili.WebCookie import BiliWebCookie, CookieWrapper
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.grpc_module.Models.CustomRequestErrorModel import Request412Error, Request352Error, \
    RequestProxyResponseError, RequestKnownError, RequestUnknownError
from fastapi接口.service.grpc_module.Models.RabbitmqModel import VoucherInfo
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.mdoel.RequestConf import RequestConf
from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from utl.代理.数据库操作.ProxyCommOp import get_available_proxy
from utl.代理.数据库操作.ProxyEvent import handle_proxy_412, handle_proxy_352, handle_proxy_request_fail, \
    handle_proxy_succ
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper


class RequestWithProxy:

    def __init__(self):
        self.use_p_dict_flag = False
        self.channel = 'bili'
        self.log = request_with_proxy_logger
        self.timeout = 30
        self.available_proxy_timeout = 30
        self.task_set = set()

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    async def get_one_rand_proxy(self) -> ProxyTab:
        return await SQLHelper.select_proxy('rand', channel=self.channel)

    async def request_with_proxy(self,
                                 request_conf: RequestConf = RequestConf(),
                                 cookie_data: CookieWrapper | None = None,
                                 **kwargs) -> dict | list[dict] | curl_cffi.requests.models.Request:
        """
        :param request_conf:
        :param cookie_data:
        :param kwargs:
        :mode single|rand 设置代理是否选择最高的单一代理还是随机
        :hybrid 是否将本地ipv6代理加入随机选择中
        :return:
        """
        is_use_available_proxy: bool = request_conf.is_use_available_proxy
        is_use_custom_proxy: bool = request_conf.is_use_custom_proxy
        is_return_raw_response: bool = request_conf.is_return_raw_response
        use_my_ipv6_proxy_pool_weights = 10  # 使用自己的ipv6代理池的权重
        use_real_proxy_weights = 1000  # 使用抓取的代理的权重
        status = 0
        origin = kwargs.get('headers', {}).get('origin', 'https://www.bilibili.com')
        referer = kwargs.get('headers', {}).get('referer', 'https://www.bilibili.com/')
        used_available_proxy = False
        my_ipv6_proxy = ProxyTab(
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
        proxy = None if not is_use_custom_proxy else my_ipv6_proxy
        while not proxy:  # 获取代理这里可以while 1 循环
            proxy_flag: bool = random.choices([True, False], weights=[
                use_my_ipv6_proxy_pool_weights if use_my_ipv6_proxy_pool_weights >= 0 else 0,
                use_real_proxy_weights if use_real_proxy_weights >= 0 else 0
            ], k=1)[0]
            if not proxy_flag or status != 0:
                use_my_ipv6_proxy_pool_weights += 1
                proxy, used_available_proxy = await get_available_proxy(is_use_available_proxy)
                if not proxy:
                    self.log.warning('获取代理失败！')
                    await get_proxy_methods.main()
                    continue
            else:
                use_real_proxy_weights += 20
                proxy = my_ipv6_proxy
        req_dict = False
        req_text = ''
        try:
            req = await my_async_httpx.request(**kwargs,
                                               timeout=self.timeout if not used_available_proxy else self.available_proxy_timeout,
                                               proxies=proxy.proxy)
            req_text = req.text
            if 'code' not in req_text and 'bili' in str(req.url):  # 如果返回的不是json那么就打印出来看看是什么
                # self.log.info(req_text.replace('\n', ''))
                ...
            if '<div class="txt-item err-text">由于触发哔哩哔哩安全风控策略，该次访问请求被拒绝。</div>' in req_text:
                raise Request412Error(req_text, -412)
            if not is_return_raw_response:
                req_dict = req.json()
                if type(req_dict) is list:
                    if proxy:
                        # self.log.critical(
                        #     f'获取请求成功代理：{proxy.proxy}\n{kwargs.get("url")}')
                        await handle_proxy_succ(
                            proxy_tab=proxy,
                        )
                    return req_dict
                if type(req_dict) is not dict:
                    self.log.critical(f'请求获取的req_dict类型出错！{req_dict}')
                if ((req_dict.get('code') is None or type(req_dict.get('code')) is not int or req_dict == {'code': 5,
                                                                                                           'message': 'Not Found'}) or req_dict.get(
                    'msg') == 'system error' and 'bili' in req.url.host):
                    raise RequestProxyResponseError(f'代理返回真实响应错误！\n{req.text}\n{kwargs}\n', -500)

                if req_dict.get('code') == -412 or req_dict.get('code') == -352 or req_dict.get('code') == 65539:
                    if cookie_data:
                        cookie_data.times_352 += 1
                    status = -412
                    err_msg = f'{req_dict.get("code")}报错,换个ip\t{proxy}\t{self._timeshift(time.time())}\t{req_dict}\n{kwargs}\n{req.headers}'
                    if req_dict.get('code') == 65539:
                        pass
                    if req_dict.get('code') == -412:
                        raise Request412Error(err_msg, -412)
                    elif req_dict.get('code') == -352:
                        voucher = req.headers.get('x-bili-gaia-vvoucher')
                        ua = req.request.headers.get('user-agent')
                        task = asyncio.create_task(BiliLotDataPublisher.pub_bili_voucher(body=VoucherInfo(
                            voucher=voucher,
                            ua=ua,
                            generate_ts=int(time.time()),
                            ck=cookie_data.ck.to_str() if cookie_data else "",
                            origin=origin,
                            referer=referer,
                            ticket='',
                            version="",
                            session_id=""
                        ))
                        )
                        self.task_set.add(task)
                        task.add_done_callback(self.task_set.discard)
                        raise Request352Error(err_msg, -352)
                    raise Request412Error(err_msg, req_dict.get('code'))
        except (Request412Error, Request352Error) as _err:
            if proxy:
                match (_err.code):
                    case -412:
                        await handle_proxy_412(
                            proxy_tab=proxy,
                        )
                    case -352:
                        Voucher352_logger.critical(f"代理{proxy.proxy} 报错-352 被封禁\n{kwargs}")
                        await handle_proxy_352(
                            proxy_tab=proxy,
                        )
                    case _:
                        await handle_proxy_request_fail(
                            proxy_tab=proxy,
                        )
            raise _err
        except (
                TooManyRedirects, SSLError, JSONDecodeError, ProxyError, RemoteProtocolError, ConnectError,
                ConnectTimeout, HTTPError,
                ReadTimeout, ReadError, WriteError, InvalidURL, NetworkError, RequestProxyResponseError,
                ExceptionGroup, ProxyConnectionError, ProxyTimeoutError, SocksProxyError,
                ValueError, ProtocolError, curl_cffi.requests.exceptions.ConnectionError,
                curl_cffi.requests.exceptions.ProxyError, curl_cffi.requests.exceptions.SSLError,
                curl_cffi.requests.exceptions.Timeout, curl_cffi.requests.exceptions.HTTPError,
                TimeoutError
        ) as _err:
            self.log.debug(f'请求时发生网络错误：{type(_err)}\n{_err}')
            if proxy:
                await handle_proxy_request_fail(
                    proxy_tab=proxy,
                )
            raise RequestProxyResponseError(_err)
        except AttributeError as _err:
            self.log.exception(f'请求时出错，一般错误：{_err}')
            if proxy:
                await handle_proxy_request_fail(
                    proxy_tab=proxy,
                )
            raise RequestUnknownError(_err)
        except Exception as _err:
            self.log.exception(
                f'未知请求错误！请求：\n{kwargs}'
                f'\n结束，报错了！'
                f'\n{type(_err)}'
                f'\t{sqlalchemy_model_2_dict(proxy)}'
                f'\n{_err}\n{req_text}')
            if proxy:
                await handle_proxy_request_fail(
                    proxy_tab=proxy,
                )
            raise RequestUnknownError(_err)
        if req_dict is False and is_return_raw_response is False:
            raise ValueError('请求返回的req_dict是False')
        if proxy:
            # self.log.critical(
            #     f'获取请求成功代理：{proxy.proxy}\n{kwargs.get("url")}')
            await handle_proxy_succ(
                proxy_tab=proxy,
            )
        if is_return_raw_response:
            return req
        return req_dict

    def _remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    async def _remove_proxy_list(self, proxy_dict):
        '''
        移除代理
        :param proxy_dict:
        :return:
        '''
        await SQLHelper.remove_proxy(proxy_dict['proxy'])

    async def update_to_proxy_dict(self, proxy_dict: ProxyTab,
                                   change_score_num=10):
        '''
        修改所选的proxy，如果不存在则新增在第一个
        最多只记录   score: -50 ~ 100分    success_times: -10 ~ 100
        :param proxy_dict:
        :return:
        '''
        if proxy_dict.proxy.get('http') == CONFIG.my_ipv6_addr:
            return
        proxy_dict.update_ts = int(time.time())
        if proxy_dict.score > 10000:
            proxy_dict.score = 10000
        if proxy_dict.score < -10000:
            proxy_dict.score = -10000
        if proxy_dict.success_times > 100:
            proxy_dict.success_times = 100
        if proxy_dict.success_times < -10:
            proxy_dict.success_times = -10
        await SQLHelper.update_to_proxy_list(proxy_dict, change_score_num)

    async def get_proxy_by_ip(self, ip: str) -> ProxyTab | None:
        '''

        :param ip:传个ip地址进去查找
        :return:
        '''
        while 1:
            ret_proxy = await SQLHelper.get_proxy_by_ip(ip)
            if ret_proxy:
                return ret_proxy
            else:
                return None


request_with_proxy_internal = RequestWithProxy()
