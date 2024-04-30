# -*- coding: utf-8 -*-
# 相当于服务器端的业务代码
import asyncio
import json
import os
import random
import re
import sys
import time
import traceback
from datetime import datetime
from functools import reduce
from typing import Union
import bs4
from loguru import logger
from CONFIG import CONFIG
from grpc获取动态.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, APIExClimbWuzhi
# from utl.代理.数据库操作 import sqlite3_proxy_op as sqlite3_proxy_op
# from utl.代理.数据库操作 import async_proxy_op_alchemy_ver as sqlite3_proxy_op
from utl.代理.数据库操作 import async_proxy_op_alchemy_mysql_ver as sqlite3_proxy_op
from utl.代理.SealedRequests import MYASYNCHTTPX
from utl.代理.ProxyTool.ProxyObj import MyProxyData, MyProxyDataTools, TypePDict


class request_with_proxy:
    async def Get_Bili_Cookie(self, ua: str) -> str:
        if int(time.time()) - self.cookies_ts <= 2 * 3600:
            if self.fake_cookie:
                return self.fake_cookie
        self.cookies_ts = int(time.time())
        self.fake_cookie = await ExClimbWuzhi.verifyExClimbWuzhi(MYCFG=APIExClimbWuzhi(ua=ua), useProxy=False)
        return self.fake_cookie

    def __init__(self):
        self.cookie_lock = asyncio.Lock()
        self.use_p_dict_flag = False
        self.channel = 'bili'
        self.sqlite3_proxy_op = sqlite3_proxy_op.SQLHelper()
        self.max_get_proxy_sep = 0.5 * 3600 * 24  # 最大间隔x天获取一次网络上的代理
        self.log = logger
        # self.log.remove()
        # self.log.add(sys.stdout, level='ERROR')
        self.get_proxy_sep_time = 0.5 * 3600  # 获取代理的间隔
        self.get_proxy_timestamp = 0
        self.check_proxy_time = {
            'last_checked_ts': 0,  # 最后一次检查和刷新代理的时间
            'checked_ts_sep': 2 * 3600
        }
        self.get_proxy_page = 7  # 获取代理网站的页数
        self.__dir_path = CONFIG.root_dir + 'utl/代理/'
        self.check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
        self.fresh_cookie_lock = asyncio.Lock()
        self.cookies_ts = 0
        self._352_time = 0
        self.using_p_dict_list: list[MyProxyData] = []  # 正在使用的代理列表，可以使用的，无法使用则删除

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
        self.fake_cookie = ''

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    async def get_one_rand_proxy(self):
        return await self.sqlite3_proxy_op.select_one_proxy('rand', channel=self.channel)

    def generate_httpx_proxy_from_requests_proxy(self, request_proxy: dict) -> dict:
        return {
            'http://': request_proxy['http'],
            'https://': request_proxy['https'],
        }

    async def request_with_proxy(self, *args, **kwargs) -> dict:
        kwargs.update(*args)
        args = ()
        mode = self.mode
        if 'mode' in kwargs.keys():
            mode = kwargs.pop('mode')
        while True:
            # if kwargs.get('headers').get('user-agent'):
            #     if kwargs.get('headers').get('user-agent') in self.ban_ua_list:
            #         if self.User_Agent_List:
            #             kwargs.get('headers').update({
            #                 'user-agent': random.choice(self.User_Agent_List)
            #             })
            if kwargs.get('headers', {}).get('cookie', '') or kwargs.get('headers', {}).get(
                    'Cookie', '') and 'x/frontend/finger/spi' not in kwargs.get(
                'url') and 'x/internal/gaia-gateway/ExClimbWuzhi' not in kwargs.get('url'):
                if self.fake_cookie:
                    kwargs.get('headers').update({'cookie': self.fake_cookie})
                else:
                    async with self.cookie_lock:
                        if not self.fake_cookie:
                            await self.Get_Bili_Cookie(kwargs.get('headers').get('user-agent'))
                            kwargs.get('headers').update({'cookie': self.fake_cookie})
            if self.GetProxy_Flag:
                self.log.info('获取代理中')
                await asyncio.sleep(30)
                loop = asyncio.get_event_loop()
                loop.call_later(30, self.set_GetProxy_Flag, False)
                continue
            p_dict: Union[TypePDict, {}] = {}
            if len(self.using_p_dict_list) > 10:
                self.use_p_dict_flag = True
            if len(self.using_p_dict_list) < 3:
                self.use_p_dict_flag = False
            if self.use_p_dict_flag and self.using_p_dict_list:
                task_list = []

                def remove_unavailable_ProxyData(ProxyData: MyProxyData):
                    if ProxyData.is_available():
                        return True
                    else:
                        task_list.append(self._update_to_proxy_dict(ProxyData.__dict__(), 0))
                        return False

                self.using_p_dict_list = list(filter(remove_unavailable_ProxyData, self.using_p_dict_list))
                if task_list:
                    await asyncio.gather(*task_list)
                temp: MyProxyData = random.choice(self.using_p_dict_list)
                if temp.is_available(True):
                    p_dict = temp.__dict__()
                    p_dict['status'] = -412 if p_dict['status'] != 0 else p_dict['status']
            if not p_dict:
                p_dict = await self._set_new_proxy(mode)
                if p_dict.get('proxy') in [x.proxy for x in self.using_p_dict_list]:
                    temp: MyProxyData = MyProxyDataTools.get_MyProxyData_by_proxy_dict(p_dict.get('proxy'),
                                                                                       self.using_p_dict_list)
                    temp.is_available(True)
            p = p_dict.get('proxy', {})
            status = 0
            if not p:
                self.log.debug('刷新全局-412代理')
                await self._refresh_412_proxy()
                continue
            req_dict = False
            req_text = ''
            try:
                # self.log.info(f'正在发起请求中！\t{p}\n{args}\n{kwargs}\n')
                req = await self.s.request(*args, **kwargs, timeout=self.timeout, proxies=p)
                req_text = req.text
                self.log.debug(f'url:{kwargs.get("url")}) 获取到请求结果！\t{p}\n{req.text[0:200]}\n')
                if 'code' not in req.text and 'bili' in req.url.host:  # 如果返回的不是json那么就打印出来看看是什么
                    self.log.info(req.text.replace('\n', ''))
                try:
                    req_dict = req.json()
                except:
                    req_text = req.text.replace("\n", "")
                    self.log.warning(f'解析为dict时失败，响应内容为：\n{req_text}\n{args}\n{kwargs}\n')
                if type(req_dict) is list:
                    p_dict['score'] += 10   
                    p_dict['status'] = status
                    self.log.debug(f'更新数据库中的代理status:{status}')
                    await self._update_to_proxy_dict(p_dict, 50)
                    return req_dict
                if type(req_dict) is not dict:
                    self.log.warning(f'请求获取的req_dict类型出错！{req_dict}')
                if (req_dict.get('code') is None or type(req_dict.get('code')) is not int or req_dict=={'code': 5, 'message': 'Not Found'}) and 'bili' in req.url.host:
                    self.log.warning(f'获取bili真实响应失败！\n{req.text}\n{args}\n{kwargs}\n')
                    p_dict['score'] -= 10
                    p_dict['status'] = -412
                    await self._update_to_proxy_dict(p_dict, -10)
                    continue
                if req_dict.get('code') == -412 or req_dict.get('code') == -352 or req_dict.get('code') == 65539:
                    status = -412
                    # 代理被风控
                    temp = MyProxyDataTools.get_MyProxyData_by_proxy_dict(p_dict.get('proxy'),
                                                                          self.using_p_dict_list)
                    if temp:
                        temp.status = -352
                        temp.max_counter_ts = int(time.time())
                    self.log.critical(
                        f'{req_dict.get("code")}报错,换个ip\t{p_dict}\t{self._timeshift(time.time())}\t{req_dict}\n{args}\t{kwargs}')
                    if req_dict.get('code') == 65539:
                        pass
                    if req_dict.get('code') == -412:
                        # self._check_ip_by_bili_zone(p, status=status, score=p_dict['score'])  # 如何代理ip检测没问题就追加回去
                        pass
                    elif req_dict.get('code') == -352:
                        self._352_time += 1
                        if self._352_time >= 20:
                            await self.Get_Bili_Cookie(kwargs.get('headers').get('user-agent'))
                            self._352_time = 0
                    p_dict['score'] += 10
                    p_dict['status'] = status
                    self.log.debug(f'更新数据库中的代理status:{status}')
                    await self._update_to_proxy_dict(p_dict, 50)
                    continue
                if req_dict.get('code') == 0 or req_dict.get('code') == 4101131 or req_dict.get('code') == -9999:
                    # self.log.info(
                    #     f'{mode}获取成功(url:{kwargs.get("url")})目前正在使用代理{p_dict}\n目前正在使用代理数量:{len(self.using_p_dict_list)}\n{p_dict}\n{kwargs}')
                    p_dict['score'] += 100
                    p_dict['status'] = 0
                    self.log.debug(f'更新数据库中的代理status:{status}')

            except Exception as e:
                # if p not in self.ban_proxy_pool:
                #     self.ban_proxy_pool.append(p)
                # try:
                #     self._remove_proxy_list(p_dict['proxy'])
                # except:
                #     pass
                self.log.warning(f'请求结束，报错了！\t{p}\n{traceback.format_exc()}\n{req_text}')
                status = -412
                temp = MyProxyDataTools.get_MyProxyData_by_proxy_dict(p_dict.get('proxy'), self.using_p_dict_list)
                if temp:
                    temp.status = -352
                    temp.max_counter_ts = int(time.time())
                p_dict['score'] -= 10
                p_dict['status'] = status
                # self.log.warning(f'更新数据库中的代理status:{status}')
                await self._update_to_proxy_dict(p_dict, change_score_num=-10)
                self.log.warning(
                    f'{mode}使用代理访问失败，代理扣分。\n{e}\t{type(e)}\n{kwargs}\n获取请求时使用的代理信息：{p_dict}\t{self._timeshift(time.time())}\t剩余{await self.sqlite3_proxy_op.get_available_proxy_nums()}/{await self.sqlite3_proxy_op.get_all_proxy_nums()}个代理')
                continue
            p_dict['score'] += 50
            p_dict['status'] = status
            # 最后能返回dict肯定是获取去成功了，这个时候再设置使用的代理
            temp = MyProxyDataTools.get_MyProxyData_by_proxy_dict(p_dict.get('proxy'), self.using_p_dict_list)
            if not temp:
                self.using_p_dict_list.append(MyProxyData(**p_dict))
            await self._update_to_proxy_dict(p_dict, 50)
            if req_dict is False:
                continue
            return req_dict

    def set_GetProxy_Flag(self, boolean: bool):
        self.GetProxy_Flag = boolean

    # region 从代理网站获取代理
    # region 从免费代理网站获取代理，每个网站的表格不一样，需要测试！
    async def get_proxy_from_kuaidaili(self) -> tuple[list, bool]:
        headers = {
            'cookie': "Hm_lvt_7ed65b1cc4b810e9fd37959c9bb51b31=1680258680; Hm_lvt_e0cc8b6627fae1b9867ddfe65b85c079=1682493581; channelid=0; sid=1688887169922522; _gcl_au=1.1.1132663223.1688887171; __51vcke__K3h4gFH3WOf3aJqX=6c6a659f-9ac6-5a8c-abb0-bd2e2aaf2dd6; __51vuft__K3h4gFH3WOf3aJqX=1688887171061; _gid=GA1.2.1163372563.1688887171; __51uvsct__K3h4gFH3WOf3aJqX=2; _ga_DC1XM0P4JL=GS1.1.1688887171.1.1.1688889750.0.0.0; __vtins__K3h4gFH3WOf3aJqX=%7B%22sid%22%3A%20%22c86f1b8f-1e78-5ad1-86e8-f487d239c80b%22%2C%20%22vd%22%3A%202%2C%20%22stt%22%3A%20432874%2C%20%22dr%22%3A%20432874%2C%20%22expires%22%3A%201688891551028%2C%20%22ct%22%3A%201688889751028%7D; _ga=GA1.2.1430092584.1680258680; _gat=1; _ga_FWN27KSZJB=GS1.2.1688889318.2.1.1688889751.0.0.0",
            'Sec-Fetch-Site': 'same-origin',
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'https://www.kuaidaili.com/free/intr/{page}/'
            headers.update({'Referer': url})

            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                self.log.info(url)
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'https://www.zdaye.com/free/{page}/'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False,
                                       proxies=(await self.sqlite3_proxy_op.select_score_top_proxy()).get('proxy'))
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                self.log.critical(traceback.format_exc())
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'http://www.66ip.cn/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=(await self.sqlite3_proxy_op.select_score_top_proxy()).get('proxy')
                                       )
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
        for page in range(1, self.get_proxy_page):
            url = f'https://www.89ip.cn/index_{page}.html'
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'https://www.tyhttp.com/free/page{page}/'
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                Get_proxy_success = False

        return proxy_queue, Get_proxy_success

    async def get_proxy_from_kxdaili_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.kxdaili.com/dailiip/1/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.kxdaili.com/dailiip/2/{page}.html'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.ip3366.net/free/?stype=1&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.ip3366.net/free/?stype=2&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'https://proxy.ip3366.net/free/?action=china&page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        page_list = ['b97827cc', '4ce63706', '5crfe930', 'f3k1d581', 'ce1d45977']
        for page in page_list:
            url = f'https://ip.ihuan.me/?page={page}'
            try:
                req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        gmt_format = '%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)'
        gmt = datetime.now().strftime(gmt_format)

        url = f'https://www.docip.net/data/free.json?t={gmt}'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.json().get('data'):
                if i.get('ip'):
                    append_dict = {
                        'http': 'http' + '://' + i.get('ip'),
                        'https': 'http' + '://' + i.get('ip')
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        gmt_format = '%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)'
        gmt = datetime.now().strftime(gmt_format)

        url = f'https://openproxylist.xyz/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'https://proxyhub.me/'
            headers.update({"cookie": f"page={page};"})
            try:
                req = await self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
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
                        append_dict = {
                            'http': 'http' + '://' + i,
                            'https': 'http' + '://' + i
                        }
                        # if append_dict not in have_proxy:
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

    async def get_proxy_from_officialputuid_KangProxy_KangProxy_https(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/casals-ar/proxy.casals.ar/main/http'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:
            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                addr = ''.join(re.findall('\d+.\d+.\d+.\d+', i.strip()))
                if addr:
                    append_dict = {
                        'http': 'http' + '://' + addr,
                        'https': 'http' + '://' + addr
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/sarperavci/freeCheckedHttpProxies/main/freshHttpProxies.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
            return proxy_queue, Get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = {
                        'http': 'http' + '://' + i.strip(),
                        'https': 'http' + '://' + i.strip()
                    }
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            Get_proxy_success = False
        return proxy_queue, Get_proxy_success

    # endregion

    # region github json格式代理（每个函数的json响应可能都不一样，要换里面解析json的方式）
    async def get_proxy_from_t0mer_free_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/t0mer/free-proxies/main/proxies.json'
        try:
            req = await self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
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

    # endregion

    # region 获取代理主函数
    async def __get_proxy(self):
        Get_proxy_success = False
        if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
            self.log.debug(
                f'获取代理时间过短！返回！（冷却剩余：{self.get_proxy_sep_time - (int(time.time() - self.get_proxy_timestamp))}）')
            return
        else:
            self.GetProxy_Flag = True
            self.get_proxy_timestamp = time.time()
        self.log.info(f'开始获取代理\t{self._timeshift(time.time())}')
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
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_taiyangdaili())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_kxdaili_1())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_kxdaili_2())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ip3366_1())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ip3366_2())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_qiyun())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_ihuan())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_docip())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_openproxylist())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_zdayip())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_proxy_casals_ar_main_http())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_yemixzy_proxy_list_main_proxies_http())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(self.get_proxy_from_TheSpeedX_PROXY_List_master_http())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxyhub())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_sarperavci_freeCheckedHttpProxies())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_prxchk_proxy_list())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_andigwandi_free_proxy())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_elliottophellia_yakumo())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_im_razvan_proxy_list())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxy4parsing_proxy_list())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_mmpx12_proxy_list())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_t0mer_free_proxies())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_MuRongPIG_Proxy_Master())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_officialputuid_KangProxy_KangProxy_http())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
        try:
            task = asyncio.create_task(
                self.get_proxy_from_officialputuid_KangProxy_KangProxy_https())
            task_list.append(task)
        except Exception as e:
            traceback.print_exc()
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
        for _ in range(len(proxy_queue)):
            await self._check_ip_by_bili_zone(proxy_queue.pop())
        await self.sqlite3_proxy_op.remove_list_dict_data_by_proxy()
        Get_proxy_success = True
        return

    async def get_proxy(self):
        try:
            await self.__get_proxy()
        except Exception as e:
            traceback.print_exc()
            self.log.critical(e)
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

    async def _check_ip_by_bili_zone(self, proxy: dict, status=0, score=50) -> bool:
        '''
        使用zone检测代理ip，没问题就追加回队首，返回True为可用代理
        :param status:
        :param proxy:
        :return:
        '''
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

    async def _set_new_proxy(self, mode=None):
        if not mode:
            mode = self.mode
        ret_p_dict={}
        while 1:
            try:
                p_dict = await self.sqlite3_proxy_op.select_one_proxy(mode, channel=self.channel)
                if p_dict == {}:
                    self.log.critical('获取代理为空')
                    await self.get_proxy()
                    self.log.debug('刷新全局-412代理')
                    await self._refresh_412_proxy()
                    continue
                ret_p_dict = p_dict
                if int(time.time()) - self.check_proxy_time['last_checked_ts'] >= self.check_proxy_time[
                    'checked_ts_sep']:
                    _412_counter = await self.sqlite3_proxy_op.get_412_proxy_num()
                    latest_add_ts = await self.sqlite3_proxy_op.get_latest_add_ts()  # 最后一次更新的时间
                    proxy_num = await self.sqlite3_proxy_op.get_all_proxy_nums()
                    if _412_counter > proxy_num - 10:
                        self.log.warning(
                            f'-412风控代理过多\t{_412_counter, proxy_num}\t{time.strftime("%Y-%m-%d %H:%M:", time.localtime(time.time()))}')
                        self.log.debug('刷新全局-412代理')
                        await self._refresh_412_proxy()
                        await self.get_proxy()  # 如果可用代理数量太少就去获取新的代理
                    if latest_add_ts:
                        if int(time.time() - latest_add_ts) > self.max_get_proxy_sep and latest_add_ts != 0:
                            await self.get_proxy()  # 最后一次获取的时间如果是x天前，就再去获取一次代理
                            self.log.debug('刷新全局-412代理')
                            await self._refresh_412_proxy()
                    else:
                        await self.get_proxy()  # 最后一次获取的时间如果是x天前，就再去获取一次代理
                        self.log.debug('刷新全局-412代理')
                        await self._refresh_412_proxy()
                    self.check_proxy_time['last_checked_ts'] = int(time.time())
                break
            except Exception as e:
                self.log.critical(e)
                continue
        return ret_p_dict

    async def _refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        await self.sqlite3_proxy_op.refresh_412_proxy()

    async def _remove_proxy_list(self, proxy_dict):
        '''
        移除代理
        :param proxy_dict:
        :return:
        '''
        await self.sqlite3_proxy_op.remove_proxy(proxy_dict['proxy'])

    async def _update_to_proxy_dict(self, proxy_dict: dict,
                                    change_score_num=10):
        '''
        修改所选的proxy，如果不存在则新增在第一个
        最多只记录   score: -50 ~ 100分    success_times: -10 ~ 100
        :param proxy_dict:
        :return:
        '''
        proxy_dict['update_ts'] = int(time.time())
        if proxy_dict['score'] > 100000:
            proxy_dict['score'] = 100000
        if proxy_dict['score'] < -100000:
            proxy_dict['score'] = -100000
        if proxy_dict['success_times'] > 100:
            proxy_dict['success_times'] = 100
        if proxy_dict['success_times'] < -10:
            proxy_dict['success_times'] = -10
        await self.sqlite3_proxy_op.update_to_proxy_list(proxy_dict, change_score_num)

    async def _add_to_proxy_list(self, proxy_dict: dict):
        '''
        增加新的proxy
        :param proxy_dict:
        :return:
        '''
        have_flag = await self.sqlite3_proxy_op.is_exist_proxy_by_proxy(proxy_dict['proxy'])
        if not have_flag:
            proxy_dict.update({'add_ts': int(time.time())})
            self.log.info(f'新增代理：{proxy_dict}')
            await self.sqlite3_proxy_op.add_to_proxy_list(proxy_dict)

    async def get_one_rand_grpc_proxy(self) -> Union[TypePDict, None]:
        while 1:
            ret_proxy = await self.sqlite3_proxy_op.get_one_rand_grpc_proxy()
            if not ret_proxy:
                # self.log.critical(f'没有可用的Grpc代理，尝试获取新代理！')
                await self.get_proxy()
                return None
            return ret_proxy

    async def get_grpc_proxy_by_ip(self, ip: str) -> Union[TypePDict, None]:
        '''

        :param ip:传个ip地址进去查找
        :return:
        '''
        while 1:
            ret_proxy = await self.sqlite3_proxy_op.get_grpc_proxy_by_ip(ip)
            if ret_proxy:
                return ret_proxy
            else:
                return None

    async def upsert_grpc_proxy_status(self, *args, **kwargs) -> None:
        if args:
            kwargs.update(*args)
        if int(time.time()) - self.check_proxy_time['last_checked_ts'] >= self.check_proxy_time[
            'checked_ts_sep']:
            grpc_412_num = await self.sqlite3_proxy_op.get_412_proxy_num()
            latest_add_ts = await self.sqlite3_proxy_op.get_latest_add_ts()  # 最后一次更新的时间
            proxy_num = await self.sqlite3_proxy_op.grpc_get_all_proxy_nums()
            if grpc_412_num > proxy_num * 0.8:
                self.log.warning(
                    f'-412风控代理过多\t{grpc_412_num, proxy_num}\t{time.strftime("%Y-%m-%d %H:%M:", time.localtime(time.time()))}')
                await self._grpc_refresh_412_proxy()
                await self.get_proxy()  # 如果可用代理数量太少就去获取新的代理
            if latest_add_ts:
                if int(time.time() - latest_add_ts) > self.max_get_proxy_sep and latest_add_ts != 0:
                    await self.get_proxy()  # 最后一次获取的时间如果是x天前，就再去获取一次代理
                    await self._grpc_refresh_412_proxy()
            else:
                await self.get_proxy()  # 最后一次获取的时间如果是x天前，就再去获取一次代理
                await self._grpc_refresh_412_proxy()
            self.check_proxy_time['last_checked_ts'] = int(time.time())
        # else:
        #     self.check_proxy_time['last_checked_ts'] = int(time.time())

        await self.sqlite3_proxy_op.upsert_grpc_proxy_status(**kwargs)

    async def _grpc_refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        await self.sqlite3_proxy_op.grpc_refresh_412_proxy()
