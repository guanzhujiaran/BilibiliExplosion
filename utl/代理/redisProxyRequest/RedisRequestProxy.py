# -*- coding: utf-8 -*-
# 由redis和mysql实现数据的统一
import asyncio
import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import reduce
from json import JSONDecodeError
from typing import Union
from exceptiongroup import ExceptionGroup
from loguru import logger
from python_socks._errors import ProxyConnectionError, ProxyTimeoutError, ProxyError as SocksProxyError
from socksio import ProtocolError
from CONFIG import CONFIG
from utl.redisTool.RedisManager import RedisManagerBase
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from httpx import ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout, ReadError, InvalidURL, \
    WriteError, NetworkError, TooManyRedirects
from ssl import SSLError

import fastapi接口.log.base_log as base_log
import fastapi接口.service.MQ.base.MQServer.VoucherMQServer as VoucherMQServer
import fastapi接口.utils.Common as Common
import fastapi接口.utils.ProxyEvent as ProxyEvent
import fastapi接口.utils.SqlalchemyTool as SqlalchemyTool
import fastapi接口.service.grpc_module.Models.CustomRequestErrorModel as CustomRequestErrorModel
import fastapi接口.service.grpc_module.grpc.prevent_risk_control_tool.activateExClimbWuzhi as activateExClimbWuzhi

ExClimbWuzhi, APIExClimbWuzhi = activateExClimbWuzhi.ExClimbWuzhi, activateExClimbWuzhi.APIExClimbWuzhi
Request412Error, Request352Error, RequestProxyResponseError = CustomRequestErrorModel.Request412Error, \
    CustomRequestErrorModel.Request352Error, CustomRequestErrorModel.RequestProxyResponseError
sqlalchemy_model_2_dict = SqlalchemyTool.sqlalchemy_model_2_dict
request_with_proxy_logger = base_log.request_with_proxy_logger
VoucherRabbitMQ = VoucherMQServer.VoucherRabbitMQ
GLOBAL_SCHEDULER, _sem_wrapper = Common.GLOBAL_SCHEDULER, Common._sem_wrapper


@dataclass
class CookieWrapper:
    ck: str
    ua: str
    expire_ts: int
    times_352: bool = 0

    @property
    def able(self) -> bool:
        if self.times_352 > 10:
            return False
        return True


@dataclass
class CheckProxyTime:
    last_checked_ts: int = 0
    checked_ts_sep: int = 2 * 3600

    def to_dict(self) -> dict:
        return {
            'last_checked_ts': self.last_checked_ts,
            'checked_ts_sep': self.checked_ts_sep
        }


class ProxyRedisManager(RedisManagerBase):
    class RedisMap(str, Enum):
        check_proxy_time = 'check_proxy_time'

    def __init__(self):
        super().__init__()

    async def get_check_proxy_time(self) -> CheckProxyTime:
        resp = await self._get(self.RedisMap.check_proxy_time.value)
        if not resp:
            default_value = CheckProxyTime()
            await self._set(self.RedisMap.check_proxy_time.value, json.dumps(default_value.to_dict()))
            return default_value
        else:
            return CheckProxyTime(**json.loads(resp))

    async def set_check_proxy_time(self, check_proxy_time: CheckProxyTime):
        return await self._set(self.RedisMap.check_proxy_time.value, json.dumps(check_proxy_time.to_dict()))


class RequestWithProxy:

    def __init__(self):
        self.redis = ProxyRedisManager()
        self.use_p_dict_flag = False
        self.channel = 'bili'
        self.log = request_with_proxy_logger
        self.check_proxy_time: CheckProxyTime = CheckProxyTime()
        self.__dir_path = CONFIG.root_dir + 'utl/代理/'
        self.timeout = 10
        self.mode = 'rand'  # single || rand # 默认是rand，改成single之后从分数最高的代理开始用，这样获取响应特别快
        self.mode_fixed = True  # 是否固定mode (已丢弃的功能)
        self.proxy_apikey = ''
        if os.path.exists(self.__dir_path + '代理api_key.txt'):
            with open(self.__dir_path + '代理api_key.txt', 'r', encoding='utf-8') as f:
                self.proxy_apikey = f.read().strip()

        #  self.s = session()
        self.fake_cookie_list: list[CookieWrapper] = []
        self.cookie_queue_num = 0
        self._352MQServer = VoucherRabbitMQ.Instance()
        self.schd = GLOBAL_SCHEDULER
        self.schd.add_job(self.background_service, 'interval', seconds=2 * 3600, next_run_time=datetime.now(),
                          misfire_grace_time=600)

    async def background_service(self):
        start_ts = int(time.time())
        request_with_proxy_logger.critical('开始后台定时任务')
        await asyncio.gather(
            *[
                get_proxy_methods.get_proxy()
            ]
        )
        request_with_proxy_logger.critical(f'定时任务执行完毕，耗时：{int(time.time()) - start_ts}秒')

    async def Get_Bili_Cookie(self, ua: str) -> CookieWrapper:
        """
        获取b站cookie
        :param ua:
        :return:
        """
        cookie_data = None
        if self.cookie_queue_num <= 20:
            self.cookie_queue_num += 1
            cookie_data: Union[CookieWrapper, None] = None
        else:
            ret_times = 0
            while ret_times < 3:
                ret_times += 1
                if len(self.fake_cookie_list) > 0:
                    cookie_data = random.choice(self.fake_cookie_list)
                    if cookie_data.expire_ts < time.time() or cookie_data.able == False:
                        self.cookie_queue_num -= 1
                        self.fake_cookie_list.remove(cookie_data)
                        continue
                    break
                if len(self.fake_cookie_list) == 0 and self.cookie_queue_num == 0:
                    self.cookie_queue_num += 1
                    cookie_data = None
                    break
        if not cookie_data:
            logger.debug(
                f'当前cookie池数量：{len(self.fake_cookie_list)}，总共{self.cookie_queue_num}个cookie信息，前往获取新的cookie')
            ck = await ExClimbWuzhi.verifyExClimbWuzhi(my_cfg=APIExClimbWuzhi(ua=ua), use_proxy=False)
            cookie_data = CookieWrapper(ck=ck, ua=ua, expire_ts=int(time.time() + 24 * 3600))  # cookie时间长一点应该没问题吧
            self.fake_cookie_list.append(cookie_data)
        # logger.debug(f'当前cookie池数量：{len(self.fake_cookie_list)}')
        return cookie_data

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    async def get_one_rand_proxy(self) -> ProxyTab:
        return await SQLHelper.select_proxy('rand', channel=self.channel)

    @_sem_wrapper
    async def request_with_proxy(self, *args, **kwargs) -> dict | list[dict]:
        """
        :param args:
        :param kwargs:
        :mode single|rand 设置代理是否选择最高的单一代理还是随机
        :hybrid 是否将本地ipv6代理加入随机选择中
        :return:
        """
        kwargs.update(*args)
        args = ()
        real_proxy_weights = 1
        ipv6_proxy_weights = 1000
        if 'mode' in kwargs.keys():
            kwargs.pop('mode')
        if 'hybrid' in kwargs.keys():
            kwargs.pop('hybrid')
        status = 0
        ua = kwargs.get('headers', {}).get('user-agent', '') or kwargs.get('headers', {}).get('User-Agent',
                                                                                              '') or CONFIG.rand_ua
        origin = kwargs.get('headers', {}).get('origin', 'https://www.bilibili.com')
        referer = kwargs.get('headers', {}).get('referer', 'https://www.bilibili.com/')
        kwargs.get('headers').update({'user-agent': ua})
        use_cookie_flag = False
        while 1:
            cookie_data = await self.Get_Bili_Cookie(ua)
            proxy_flag: bool = random.choices([True, False], weights=[
                real_proxy_weights if real_proxy_weights >= 0 else 0,
                ipv6_proxy_weights * 2 if ipv6_proxy_weights >= 0 else 0
            ], k=1)[0]
            if kwargs.get('headers', {}).get('cookie', '') or kwargs.get('headers', {}).get(
                    'Cookie', '') and 'x/frontend/finger/spi' not in kwargs.get(
                'url') and 'x/internal/gaia-gateway/ExClimbWuzhi' not in kwargs.get('url'):
                kwargs.get('headers').update({'cookie': cookie_data.ck, 'user-agent': cookie_data.ua})
                use_cookie_flag = True
            if not proxy_flag or status != 0:
                real_proxy_weights += 1
                proxy: ProxyTab = await SQLHelper.get_available_proxy()
                if not proxy:
                    self.log.warning('获取代理失败！')
                    await get_proxy_methods.get_proxy()
                    continue
            else:
                ipv6_proxy_weights += 20
                proxy: ProxyTab = ProxyTab(
                    **{
                        'proxy_id': -1,
                        'proxy': {'http': CONFIG.my_ipv6_addr, 'https': CONFIG.my_ipv6_addr},
                        'status': 0,
                        'update_ts': 0,
                        'score': 0,
                        'add_ts': 0,
                        'success_times': 0,
                        'zhihu_status': 0
                    }
                )
            req_dict = False
            req_text = ''
            self.log.debug(f"全都准备好了，开始获取请求：\nURL={kwargs.get('url')}\n Proxy={proxy.proxy}")
            try:
                req = await asyncio.wait_for(
                    my_async_httpx.request(*args, **kwargs, timeout=self.timeout, proxies=proxy.proxy), self.timeout)
                req_text = req.text
                self.log.debug(f"url:{kwargs.get('url')} 获取到请求结果！\n{proxy.proxy}\n{req.text[0:200]}\n")
                if 'code' not in req_text and 'bili' in req.url.host:  # 如果返回的不是json那么就打印出来看看是什么
                    self.log.info(req_text.replace('\n', ''))
                if '<div class="txt-item err-text">由于触发哔哩哔哩安全风控策略，该次访问请求被拒绝。</div>' in req_text:
                    raise Request412Error(req_text, -412)
                req_dict = req.json()
                if type(req_dict) is list:
                    if proxy:
                        await ProxyEvent.handle_proxy_succ(
                            proxy_tab=proxy,
                        )
                    return req_dict
                if type(req_dict) is not dict:
                    self.log.warning(f'请求获取的req_dict类型出错！{req_dict}')
                if ((req_dict.get('code') is None or type(req_dict.get('code')) is not int or req_dict == {'code': 5,
                                                                                                           'message': 'Not Found'}) or req_dict.get(
                    'msg') == 'system error' and 'bili' in req.url.host):
                    raise RequestProxyResponseError(f'代理返回真实响应错误！\n{req.text}\n{args}\n{kwargs}\n', -500)

                if req_dict.get('code') == -412 or req_dict.get('code') == -352 or req_dict.get('code') == 65539:
                    if use_cookie_flag:
                        cookie_data.times_352 += 1
                    status = -412
                    err_msg = f'{req_dict.get("code")}报错,换个ip\t{proxy}\t{self._timeshift(time.time())}\t{req_dict}\n{args}\t{kwargs}\n{req.headers}'
                    if req_dict.get('code') == 65539:
                        pass
                    if req_dict.get('code') == -412:
                        raise Request412Error(err_msg, -412)
                    elif req_dict.get('code') == -352:
                        voucher = req.headers.get('x-bili-gaia-vvoucher')
                        ua = req.request.headers.get('user-agent')
                        self._352MQServer.push_voucher_info(voucher=voucher,
                                                            ua=ua,
                                                            ck=cookie_data.ck if use_cookie_flag else "",
                                                            origin=origin,
                                                            referer=referer,
                                                            ticket='',
                                                            version=""
                                                            )
                        raise Request352Error(err_msg, -352)
                    raise Request412Error(err_msg, req_dict.get('code'))
            except (Request412Error, Request352Error) as _err:
                self.log.debug(
                    f'{_err}\n请求：\n{kwargs}\n结束，报错了！\n{type(_err)}\t{sqlalchemy_model_2_dict(proxy)}\n{req_text}')
                if proxy:
                    match (_err.code):
                        case -412:
                            await ProxyEvent.handle_proxy_412(
                                proxy_tab=proxy,
                            )
                        case -352:
                            await ProxyEvent.handle_proxy_352(
                                proxy_tab=proxy,
                            )
                        case _:
                            await ProxyEvent.handle_proxy_request_fail(
                                proxy_tab=proxy,
                            )
            except (
                    TooManyRedirects, SSLError, JSONDecodeError, ProxyError, RemoteProtocolError, ConnectError,
                    ConnectTimeout,
                    ReadTimeout, ReadError, WriteError, InvalidURL, NetworkError, RequestProxyResponseError,
                    ExceptionGroup, ProxyConnectionError, ProxyTimeoutError, SocksProxyError,
                    ValueError, ProtocolError, asyncio.exceptions.TimeoutError
            ) as _err:
                self.log.debug(
                    f'{_err}\n请求：\n{kwargs}\n结束，报错了！\n{type(_err)}\t{sqlalchemy_model_2_dict(proxy)}\n{req_text}')
                if proxy:
                    await ProxyEvent.handle_proxy_request_fail(
                        proxy_tab=proxy,
                    )
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 20
                continue
            except  AttributeError as _err:
                self.log.error(f'请求时出错，一般错误：{_err}')
                continue
            except Exception as _err:
                self.log.exception(
                    f'未知请求错误！请求：\n{kwargs}'
                    f'\n结束，报错了！'
                    f'\n{type(_err)}'
                    f'\t{sqlalchemy_model_2_dict(proxy)}'
                    f'\n{_err}\n{req_text}')
                if proxy:
                    await ProxyEvent.handle_proxy_request_fail(
                        proxy_tab=proxy,
                    )
                continue

            if req_dict is False:
                continue
            if proxy:
                await ProxyEvent.handle_proxy_succ(
                    proxy_tab=proxy,
                )
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
