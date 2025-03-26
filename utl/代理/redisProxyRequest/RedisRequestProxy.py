# -*- coding: utf-8 -*-
# 由redis和mysql实现数据的统一
import asyncio
import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import reduce
from json import JSONDecodeError
from typing import Union
import bs4
from exceptiongroup import ExceptionGroup
from loguru import logger
from CONFIG import CONFIG
from fastapi接口.log.base_log import request_with_proxy_logger
from fastapi接口.service.MQ.base.MQServer.VoucherMQServer import VoucherRabbitMQ
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from grpc获取动态.Models.CustomRequestErrorModel import Request412Error, Request352Error, RequestProxyResponseError
from grpc获取动态.Utils.GrpcRedis import grpc_proxy_tools
from grpc获取动态.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, APIExClimbWuzhi
from utl.redisTool.RedisManager import RedisManagerBase
from utl.代理.SealedRequests import MYASYNCHTTPX
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from httpx import ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout, ReadError, InvalidURL, \
    WriteError, NetworkError, TooManyRedirects
from ssl import SSLError

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
        self.mysql_proxy_op = SQLHelper
        self.max_get_proxy_sep = 0.5 * 3600 * 24  # 最大间隔x天获取一次网络上的代理
        self.log = request_with_proxy_logger
        self.get_proxy_sep_time = 0.5 * 3600  # 获取代理的间隔
        self.get_proxy_timestamp = 0
        self.check_proxy_time: CheckProxyTime = CheckProxyTime()
        self.get_proxy_page = 7  # 获取代理网站的页数
        self.__dir_path = CONFIG.root_dir + 'utl/代理/'
        self.check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
        self.timeout = 10
        self.mode = 'rand'  # single || rand # 默认是rand，改成single之后从分数最高的代理开始用，这样获取响应特别快
        self.mode_fixed = True  # 是否固定mode (已丢弃的功能)
        self.proxy_apikey = ''
        if os.path.exists(self.__dir_path + '代理api_key.txt'):
            with open(self.__dir_path + '代理api_key.txt', 'r', encoding='utf-8') as f:
                self.proxy_apikey = f.read().strip()
        self.GetProxy_Flag = False
        #  self.s = session()
        self.s = MYASYNCHTTPX()
        self.fake_cookie_list: list[CookieWrapper] = []
        self.cookie_lock = asyncio.Lock()
        self.cookie_queue_num = 0
        self._352MQServer = VoucherRabbitMQ.Instance()

    def format_proxy(self, proxy_str) -> dict | None:
        """
        将传入的代理字符串标准化为 {'protocol1': 'address1', 'protocol2': 'address2'} 的形式。

        :param proxy_str: 代理字符串，可能是IP地址或带有协议前缀的完整URL
        :return: 标准化的代理字典或None（如果输入不符合预期格式）
        """
        ip_pattern = re.compile(r'^(?:(http|https|socks[45])://)?([0-9]{1,3}\.){3}[0-9]{1,3}(:[0-9]{2,5})?$')

        match = ip_pattern.match(proxy_str)
        if not match:
            return None

        protocol_in_input = match.group(1)  # 输入中的协议部分，可能为None
        ip_address = match.group(2)
        port = match.group(3) or ':80'  # 如果没有提供端口，默认使用80

        # 构建基础的代理地址
        base_protocol = protocol_in_input or 'http'
        normalized_address = f"{base_protocol}://{ip_address}{port}"

        # 创建代理字典
        proxy_dict = {}

        # 添加原始协议到字典
        proxy_dict[base_protocol] = normalized_address

        # 如果不是http或https协议，还需要添加默认的http和https代理配置
        if base_protocol not in ['http', 'https']:
            proxy_dict['http'] = f"http://{ip_address}{port}"
            proxy_dict['https'] = f"https://{ip_address}{port}"
        else:
            # 确保http和https都有，并且值与输入保持一致
            proxy_dict['http'] = proxy_str if base_protocol == 'http' else proxy_str.replace("https://", "http://")
            proxy_dict['https'] = proxy_str if base_protocol == 'https' else proxy_str.replace("http://", "https://")

        return proxy_dict

    async def Get_Bili_Cookie(self, ua: str) -> CookieWrapper:
        """
        获取b站cookie
        :param ua:
        :return:
        """
        async with self.cookie_lock:
            if self.cookie_queue_num <= 20:
                self.cookie_queue_num += 1
                cookie_data: Union[CookieWrapper, None] = None
            else:
                while 1:
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
                    await asyncio.sleep(1)
        if not cookie_data:
            while 1:
                logger.debug(
                    f'当前cookie池数量：{len(self.fake_cookie_list)}，总共{self.cookie_queue_num}个cookie信息，前往获取新的cookie')
                ck = await ExClimbWuzhi.verifyExClimbWuzhi(my_cfg=APIExClimbWuzhi(ua=ua), use_proxy=False)
                break
            cookie_data = CookieWrapper(ck=ck, ua=ua, expire_ts=int(time.time() + 24 * 3600))  # cookie时间长一点应该没问题吧
            self.fake_cookie_list.append(cookie_data)
        # logger.debug(f'当前cookie池数量：{len(self.fake_cookie_list)}')
        return cookie_data

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    async def get_one_rand_proxy(self) -> ProxyTab:
        return await self.mysql_proxy_op.select_proxy('rand', channel=self.channel)

    def _generate_httpx_proxy_from_requests_proxy(self, request_proxy: dict) -> dict:
        return {
            'http://': request_proxy['http'],
            'https://': request_proxy['https'],
        }

    async def request_with_proxy(self, *args, **kwargs) -> dict| list[dict]:
        """

        :param args:
        :param kwargs:
        :mode single|rand 设置代理是否选择最高的单一代理还是随机
        :hybrid 是否将本地ipv6代理加入随机选择中
        :return:
        """
        kwargs.update(*args)
        args = ()
        mode = self.mode
        proxy_flag: bool = False
        hybrid_flag = False
        real_proxy_weights = 1
        ipv6_proxy_weights = 1000
        if 'mode' in kwargs.keys():
            mode = kwargs.pop('mode')
        if 'hybrid' in kwargs.keys():
            kwargs.pop('hybrid')
        status = 0
        ua = kwargs.get('headers', {}).get('user-agent', '') or kwargs.get('headers', {}).get('User-Agent',
                                                                                              '') or CONFIG.rand_ua
        origin = kwargs.get('headers', {}).get('origin', 'https://www.bilibili.com')
        referer = kwargs.get('headers', {}).get('referer', 'https://www.bilibili.com/')
        kwargs.get('headers').update({'user-agent': ua})
        use_cookie_flag = False
        while True:
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
            if self.GetProxy_Flag:
                self.log.info('获取代理中')
                await asyncio.sleep(30)
                loop = asyncio.get_event_loop()
                loop.call_later(30, self.set_GetProxy_Flag, False)
                continue
            ip_status = None
            if not proxy_flag or status != 0:
                real_proxy_weights += 1
                proxy: ProxyTab = await self._set_new_proxy()
                ip_status = await grpc_proxy_tools.get_ip_status_by_ip(proxy.proxy['http'])
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
            if not proxy:
                self.log.critical('无代理，单独刷新全局-412代理')
                await self._refresh_412_proxy()
                continue
            req_dict = False
            req_text = ''
            try:
                # self.log.debug(f'正在通过代理发起一般http请求中！\t使用代理：{sqlalchemy_model_2_dict(proxy)}\n{args}\n{kwargs}\n')
                req = await self.s.request(*args, **kwargs, timeout=self.timeout, proxies=proxy.proxy)
                req_text = req.text
                self.log.debug(f'url:{kwargs.get("url")}) 获取到请求结果！\n{proxy.proxy}\n{req_text[0:200]}\n')
                if 'code' not in req_text and 'bili' in req.url.host:  # 如果返回的不是json那么就打印出来看看是什么
                    self.log.info(req_text.replace('\n', ''))
                req_dict = req.json()
                if type(req_dict) is list:
                    if proxy and proxy.proxy['http'] != CONFIG.my_ipv6_addr:
                        proxy.score += 100
                        proxy.status = status
                        await self.update_to_proxy_dict(proxy, 50)
                        if ip_status:
                            ip_status.available = True
                            ip_status.code = 0
                            ip_status.latest_used_ts = int(time.time())
                            await grpc_proxy_tools.set_ip_status(ip_status)
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
                        await self.Get_Bili_Cookie(kwargs.get('headers').get('user-agent'))
                        raise Request352Error(err_msg, -352)
                    raise Request412Error(err_msg, req_dict.get('code'))
            except (Request412Error, Request352Error) as _err:
                self.log.debug(
                    f'{_err}\n请求：\n{kwargs}\n结束，报错了！\n{type(_err)}\t{sqlalchemy_model_2_dict(proxy)}\n{req_text}')
                if proxy and proxy.proxy['http'] != CONFIG.my_ipv6_addr:
                    proxy.score += 10
                    proxy.status = status
                    await self.update_to_proxy_dict(proxy, 50)
                    if ip_status:
                        ip_status.available = True
                        ip_status.code = 0
                        ip_status.latest_used_ts = int(time.time())
                        await grpc_proxy_tools.set_ip_status(ip_status)
                continue
            except (TooManyRedirects,SSLError,JSONDecodeError, ProxyError, RemoteProtocolError, ConnectError, ConnectTimeout, ReadTimeout,ReadError, WriteError,InvalidURL, NetworkError, RequestProxyResponseError, ExceptionGroup)as _err:
                self.log.debug(
                    f'{_err}\n请求：\n{kwargs}\n结束，报错了！\n{type(_err)}\t{sqlalchemy_model_2_dict(proxy)}\n{req_text}')
                score_change = -10
                if proxy and proxy.proxy['http'] != CONFIG.my_ipv6_addr:
                    proxy.status = -412
                    await self.update_to_proxy_dict(proxy, score_change)
                    if not ip_status:
                        ip_status = await grpc_proxy_tools.get_ip_status_by_ip(proxy.proxy['http'])
                    ip_status.max_counter_ts = int(time.time())
                    ip_status.code = -412
                    ip_status.available = False
                    await grpc_proxy_tools.set_ip_status(ip_status)
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 20
                continue
            except (ValueError, AttributeError) as _err:
                self.log.error(f'请求时出错，一般错误：{_err}')
                continue
            except Exception as _err:
                self.log.exception(
                    f'未知请求错误！请求：\n{kwargs}'
                    f'\n结束，报错了！'
                    f'\n{type(_err)}'
                    f'\t{sqlalchemy_model_2_dict(proxy)}'
                    f'\n{_err}\n{req_text}')
                if proxy and proxy.proxy['http'] != CONFIG.my_ipv6_addr:
                    proxy.status = -412
                    await self.update_to_proxy_dict(proxy, -10)
                    if not ip_status:
                        ip_status = await grpc_proxy_tools.get_ip_status_by_ip(proxy.proxy['http'])
                    ip_status.max_counter_ts = int(time.time())
                    ip_status.code = -412
                    ip_status.available = False
                continue



            if req_dict is False:
                continue
            if proxy and proxy.proxy['http'] != CONFIG.my_ipv6_addr:
                proxy.score += 100
                proxy.status = 0
                await self.update_to_proxy_dict(proxy, 50)
                if ip_status:
                    ip_status.available = True
                    ip_status.code = 0
                    ip_status.latest_used_ts = int(time.time())
                    await grpc_proxy_tools.set_ip_status(ip_status)
            return req_dict

    def set_GetProxy_Flag(self, boolean: bool):
        self.GetProxy_Flag = boolean

    # region a从代理网站获取代理

    # region a从免费代理网站获取代理，每个网站的表格不一样，需要测试！网站按照表格的样式填充代理信息

    async def get_proxy_from_kuaidaili(self) -> tuple[list, bool]:
        headers = {
            'cookie': "Hm_lvt_7ed65b1cc4b810e9fd37959c9bb51b31=1680258680; Hm_lvt_e0cc8b6627fae1b9867ddfe65b85c079=1682493581; channelid=0; sid=1688887169922522; _gcl_au=1.1.1132663223.1688887171; __51vcke__K3h4gFH3WOf3aJqX=6c6a659f-9ac6-5a8c-abb0-bd2e2aaf2dd6; __51vuft__K3h4gFH3WOf3aJqX=1688887171061; _gid=GA1.2.1163372563.1688887171; __51uvsct__K3h4gFH3WOf3aJqX=2; _ga_DC1XM0P4JL=GS1.1.1688887171.1.1.1688889750.0.0.0; __vtins__K3h4gFH3WOf3aJqX=%7B%22sid%22%3A%20%22c86f1b8f-1e78-5ad1-86e8-f487d239c80b%22%2C%20%22vd%22%3A%202%2C%20%22stt%22%3A%20432874%2C%20%22dr%22%3A%20432874%2C%20%22expires%22%3A%201688891551028%2C%20%22ct%22%3A%201688889751028%7D; _ga=GA1.2.1430092584.1680258680; _gat=1; _ga_FWN27KSZJB=GS1.2.1688889318.2.1.1688889751.0.0.0",
            'Sec-Fetch-Site': 'same-origin',
            'user-agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://www.kuaidaili.com/free/intr/{page}/'
            headers.update({'Referer': url})

            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 8):
                    proxies.append(f'{td[i * 8].text}:{td[i * 8 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        # if append_dict not in have_proxy:
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_zdayip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.zdaye.com/free/{page}/'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False,
                                       proxies=(await self.mysql_proxy_op.select_score_top_proxy()).proxy)
            except Exception as e:
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req.status_code == 200:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 9):
                    proxies.append(f'{td[i * 9].text}:{td[i * 9 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_66daili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'http://www.66ip.cn/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=(await self.mysql_proxy_op.select_score_top_proxy()).proxy
                                       )
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')[6:]
                proxies = []
                for i in range(len(td) // 5):
                    proxies.append(f'{td[i * 5].text}:{td[i * 5 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_89daili(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.89ip.cn/index_{page}.html'
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 5):
                    proxies.append(f'{td[i * 5].text.strip()}:{td[i * 5 + 1].text.strip()}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_taiyangdaili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://www.tyhttp.com/free/page{page}/'
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('.td')[8:]
                proxies = []
                for i in range(len(td) // 8):
                    proxies.append(f'{td[i * 8].text.strip()}:{td[i * 8 + 1].text.strip()}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_kxdaili_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.kxdaili.com/dailiip/1/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_kxdaili_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.kxdaili.com/dailiip/2/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_ip3366_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.ip3366.net/free/?stype=1&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_ip3366_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.ip3366.net/free/?stype=2&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_qiyun(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://proxy.ip3366.net/free/?action=china&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_ihuan(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        page_list = ['b97827cc', '4ce63706', '5crfe930', 'f3k1d581', 'ce1d45977']
        for page in page_list:
            url = f'https://ip.ihuan.me/?page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 10):
                    proxies.append(f'{td[i * 10].text}:{td[i * 10 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_docip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        gmt_format = '%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)'
        gmt = datetime.now().strftime(gmt_format)

        url = f'https://www.docip.net/data/free.json?t={gmt}'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.json().get('data'):
                if i.get('ip'):
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_openproxylist(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        gmt_format = '%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)'
        gmt = datetime.now().strftime(gmt_format)

        url = f'https://openproxylist.xyz/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_proxyhub(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://proxyhub.me/'
            headers.update({"cookie": f"page={page};"})
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 6):
                    proxies.append(f'{td[i * 6].text}:{td[i * 6 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = self.format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    # endregion

    # region Github获取的text格式的代理，每行格式为ip:port
    async def get_proxy_from_parserpp_ip_ports(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/parserpp/ip_ports/main/proxyinfo.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_api_openproxylist_xyz_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://api.openproxylist.xyz/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_SevenworksDev_proxy_list_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/SevenworksDev/proxy-list/refs/heads/main/proxies/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_SevenworksDev_proxy_list_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/SevenworksDev/proxy-list/refs/heads/main/proxies/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_monosans_proxy_list(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_r00tee_Proxy_List(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_themiralay_Proxy_List_World(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/themiralay/Proxy-List-World/refs/heads/master/data.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_lalifeier_proxy_scraper_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/lalifeier/proxy-scraper/main/proxies/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_lalifeier_proxy_scraper_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/lalifeier/proxy-scraper/main/proxies/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_claude89757_free_https_proxies(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/claude89757/free_https_proxies/refs/heads/main/free_https_proxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_Simatwa_free_proxies_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Simatwa/free-proxies/master/files/http.json'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.json().get('proxies'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_zloi_user_hideipme(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/main/connect.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_elliottophellia_proxylist_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.rei.my.id/proxy/pHTTP'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_elliottophellia_proxylist_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.rei.my.id/proxy/pSOCKS5'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')
            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_officialputuid_KangProxy_KangProxy_https(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_officialputuid_KangProxy_KangProxy_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_MuRongPIG_Proxy_Master(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_proxy_casals_ar_main_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/casals-ar/proxy.casals.ar/main/http'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_https(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_TheSpeedX_PROXY_List_master_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_yemixzy_proxy_list_main_proxies_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                addr = ''.join(re.findall('\d+.\d+.\d+.\d+', i.strip()))
                if addr:
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_sarperavci_freeCheckedHttpProxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/sarperavci/freeCheckedHttpProxies/main/freshHttpProxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_prxchk_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_andigwandi_free_proxy(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_elliottophellia_yakumo(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_im_razvan_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_proxy4parsing_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_mmpx12_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = self.format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    # endregion

    # region json格式代理（每个函数的json响应可能都不一样，要换里面解析json的方式）
    async def get_proxy_from_proxy_953959_xyz(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxy.953959.xyz/all/'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            req_dict = req.json()
            http_p = req_dict
            for da in http_p:
                if proxy := da.get('proxy'):
                    proxy_queue.append({
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    })
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_proxyshare(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://www.proxyshare.com/detection/proxyList?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            req_dict = req.json()
            http_p = req_dict.get('data')
            for da in http_p:
                if ip := da.get('ip'):
                    if port := da.get('port'):
                        proxy_queue.append({
                            'http': f'http://{ip}:{port}',
                            'https': f'http://{ip}:{port}'
                        })
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_t0mer_free_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/t0mer/free-proxies/main/proxies.json'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            req_dict = json.loads(req.text.replace('None', 'null').replace('False', 'false').replace('True', 'true'))
            http_p = req_dict.get('http')
            for i in list(http_p.keys()):
                proxy_queue.append({
                    'http': f'http://{i}',
                    'https': f'http://{i}'
                })
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    async def get_proxy_from_omegaproxy(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://www.omegaproxy.com/detection/proxyList'
        for page in range(1, self.get_proxy_page + 1):
            params = {
                'limit': 20,
                'page': page,
                'sort_by': 'lastChecked',
                'sort_type': 'desc',
                'protocols': 'http',
            }
            try:
                req = await self.s.get(url=url, headers=headers, params=params, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
                return proxy_queue, Get_proxy_success
            if req:

                req_dict = json.loads(req.text)
                http_p = req_dict.get('data')
                for i in http_p:
                    ip_port = f'http://{i.get("ip")}:{i.get("port")}'
                    proxy_queue.append({
                        'http': ip_port,
                        'https': ip_port
                    })
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    # endregion

    # region 获取代理主函数
    async def __get_proxy(self):
        Get_proxy_success = False
        if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
            self.log.info(
                f'获取代理时间过短！返回！（冷却剩余：{self.get_proxy_sep_time - (int(time.time() - self.get_proxy_timestamp))}）')
            return
        else:
            self.GetProxy_Flag = True
        self.log.info(
            f'开始获取代理\t上次获取代理时间：{datetime.fromtimestamp(self.get_proxy_timestamp)}\t{self._timeshift(time.time())}')
        self.get_proxy_timestamp = time.time()
        proxy_queue = []
        task_list = []
        try:
            task = asyncio.create_task(self.get_proxy_from_kuaidaili())
            task_list.append(task)
        except Exception as e:
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_66daili())
            task_list.append(task)
        except Exception as e:
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_89daili())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_taiyangdaili())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_kxdaili_1())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_kxdaili_2())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ip3366_1())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ip3366_2())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_qiyun())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ihuan())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_docip())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_openproxylist())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_zdayip())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_proxy_casals_ar_main_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_yemixzy_proxy_list_main_proxies_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_TheSpeedX_PROXY_List_master_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxyhub())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_sarperavci_freeCheckedHttpProxies())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_prxchk_proxy_list())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_andigwandi_free_proxy())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_elliottophellia_yakumo())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_im_razvan_proxy_list())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxy4parsing_proxy_list())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_mmpx12_proxy_list())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_t0mer_free_proxies())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_MuRongPIG_Proxy_Master())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_officialputuid_KangProxy_KangProxy_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_officialputuid_KangProxy_KangProxy_https())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_omegaproxy())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_elliottophellia_proxylist_socks5())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_elliottophellia_proxylist_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_zloi_user_hideipme())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_Simatwa_free_proxies_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_claude89757_free_https_proxies())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_lalifeier_proxy_scraper_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_lalifeier_proxy_scraper_https())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_themiralay_Proxy_List_World())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_r00tee_Proxy_List())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_monosans_proxy_list())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_SevenworksDev_proxy_list_https())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_SevenworksDev_proxy_list_http())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_api_openproxylist_xyz_https())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxyshare())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxy_953959_xyz())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)

        try:
            task = asyncio.create_task(
                self.get_proxy_from_parserpp_ip_ports())
            task_list.append(task)
        except Exception as e:

            self.log.critical(e)
        results: Union[tuple[list[str], bool] or Exception] = await asyncio.gather(*task_list,
                                                                                   return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) is True:
                self.log.critical(f'获取代理出错！{result}')
                continue
            _, Get_proxy_success = result
            proxy_queue.extend(_)
        self.log.info(f'最终共有{len(proxy_queue)}个代理需要检查')

        sem = asyncio.Semaphore(10)
        all_tasks = []
        for i in range(len(proxy_queue)):
            all_tasks.append(self._check_ip_by_bili_zone(proxy_queue.pop(), sem=sem))
        await asyncio.gather(*all_tasks)
        self.log.info(f'代理已经检查完毕，并添加至数据库！')
        await self.mysql_proxy_op.remove_list_dict_data_by_proxy()
        self.log.info(f'移除重复代理')
        Get_proxy_success = True
        return

    async def get_proxy(self):
        try:
            await self.__get_proxy()
            await self.mysql_proxy_op.check_redis_data(True)
        except Exception as e:
            self.log.exception(e)
        finally:
            loop = asyncio.get_event_loop()
            loop.call_later(30, self.set_GetProxy_Flag, False)

    # endregion

    # endregion

    def _remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    async def _check_ip_by_bili_zone(self, proxy: dict, status=0, score=50, sem=None) -> bool:
        '''
        使用zone检测代理ip，没问题就追加回队首，返回True为可用代理
        :param status:
        :param proxy:
        :return:
        '''
        async with sem:
            if self.check_proxy_flag:
                try:
                    _url = 'http://api.bilibili.com/x/web-interface/zone'
                    _req = await self.s.get(url=_url, proxies=proxy, timeout=self.timeout)
                    if _req.json().get('code') == 0:
                        # self.log.info(f'代理检测成功，添加回代理列表：{_req.json()}')
                        await self._add_to_proxy_list(self._proxy_warrper(proxy, status, score))
                        return True
                    else:
                        # self.log.info(f'代理失效：{_req.text}')
                        return False
                except Exception as e:
                    # self.log.info(f'代理检测失败：{proxy}')
                    return False
            else:
                await self._add_to_proxy_list(self._proxy_warrper(proxy, status, score))
                return True

    def _proxy_warrper(self, proxy, status=0, score=50):
        return {"proxy": proxy, "status": status, "update_ts": int(time.time()), 'score': score}

    async def _set_new_proxy(self) -> ProxyTab:
        while 1:
            available_ip_status = await grpc_proxy_tools.get_rand_available_ip_status()
            proxy: ProxyTab | None = None
            if available_ip_status:
                proxy = await self.get_proxy_by_ip(available_ip_status.ip)
            if not proxy:
                proxy = await self.get_one_rand_proxy()
            if proxy:
                return proxy
            else:
                self.log.debug('无可用代理状态！')
                await asyncio.sleep(30)

    async def _refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        await self.mysql_proxy_op.refresh_412_proxy()

    async def _remove_proxy_list(self, proxy_dict):
        '''
        移除代理
        :param proxy_dict:
        :return:
        '''
        await self.mysql_proxy_op.remove_proxy(proxy_dict['proxy'])

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
        if proxy_dict.score > 100000:
            proxy_dict.score = 100000
        if proxy_dict.score < -100000:
            proxy_dict.score = -100000
        if proxy_dict.success_times > 100:
            proxy_dict.success_times = 100
        if proxy_dict.success_times < -10:
            proxy_dict.success_times = -10
        await self.mysql_proxy_op.update_to_proxy_list(proxy_dict, change_score_num)

    async def _add_to_proxy_list(self, proxy_dict: dict):
        '''
        增加新的proxy
        :param proxy_dict:
        :return:
        '''
        have_flag = await self.mysql_proxy_op.is_exist_proxy_by_proxy(proxy_dict['proxy'])
        if not have_flag:
            proxy_dict.update({'add_ts': int(time.time())})
            self.log.info(f'新增代理：{proxy_dict}')
            proxy_tab = ProxyTab(
                **proxy_dict
            )
            await self.mysql_proxy_op.add_to_proxy_tab_database(proxy_tab)

    async def get_proxy_by_ip(self, ip: str) -> ProxyTab | None:
        '''

        :param ip:传个ip地址进去查找
        :return:
        '''
        while 1:
            ret_proxy = await self.mysql_proxy_op.get_proxy_by_ip(ip)
            if ret_proxy:
                return ret_proxy
            else:
                return None


request_with_proxy_internal = RequestWithProxy()

if __name__ == '__main__':
    __a = asyncio.run(request_with_proxy_internal.get_one_rand_proxy())
    print(type(__a.proxy))
