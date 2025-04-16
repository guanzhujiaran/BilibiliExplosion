"""
从网上获取代理
"""
import asyncio
import json
import re
import time
from datetime import datetime
from functools import partial
from typing import Union

import bs4
from CONFIG import CONFIG
from fastapi接口.log.base_log import sql_log
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from utl.代理.数据库操作.comm import format_proxy


class GetProxyMethods:
    get_proxy_page = 10
    log = sql_log
    get_proxy_timestamp = 0
    timeout = 30
    get_proxy_sep_time = 0.5 * 3600  # 获取代理的间隔
    check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
    GetProxy_Flag = False
    _sem = asyncio.Semaphore(100)

    # region a从代理网站获取代理

    # region a从免费代理网站获取代理，每个网站的表格不一样，需要测试！网站按照表格的样式填充代理信息
    async def get_proxy_from_cn_proxy_tools(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://cn.proxy-tools.com/proxy?page={page}'
            headers.update({'Referer': url})
            try:
                req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:
                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 9):
                    proxies.append(f'{td[i * 9 + 2].text.strip().lower()}://{td[i * 9].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
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
                get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_kuaidaili(self) -> tuple[list, bool]:
        headers = {
            'cookie': "Hm_lvt_7ed65b1cc4b810e9fd37959c9bb51b31=1680258680; Hm_lvt_e0cc8b6627fae1b9867ddfe65b85c079=1682493581; channelid=0; sid=1688887169922522; _gcl_au=1.1.1132663223.1688887171; __51vcke__K3h4gFH3WOf3aJqX=6c6a659f-9ac6-5a8c-abb0-bd2e2aaf2dd6; __51vuft__K3h4gFH3WOf3aJqX=1688887171061; _gid=GA1.2.1163372563.1688887171; __51uvsct__K3h4gFH3WOf3aJqX=2; _ga_DC1XM0P4JL=GS1.1.1688887171.1.1.1688889750.0.0.0; __vtins__K3h4gFH3WOf3aJqX=%7B%22sid%22%3A%20%22c86f1b8f-1e78-5ad1-86e8-f487d239c80b%22%2C%20%22vd%22%3A%202%2C%20%22stt%22%3A%20432874%2C%20%22dr%22%3A%20432874%2C%20%22expires%22%3A%201688891551028%2C%20%22ct%22%3A%201688889751028%7D; _ga=GA1.2.1430092584.1680258680; _gat=1; _ga_FWN27KSZJB=GS1.2.1688889318.2.1.1688889751.0.0.0",
            'Sec-Fetch-Site': 'same-origin',
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://www.kuaidaili.com/free/intr/{page}/'
            headers.update({'Referer': url})
            try:
                req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:
                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 8):
                    proxies.append(f'{td[i * 8].text}:{td[i * 8 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
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
                get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zdayip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.zdaye.com/free/{page}/'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False,
                                               proxies=(await SQLHelper.select_score_top_proxy()).proxy)
            except Exception:
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req.status_code == 200:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 9):
                    proxies.append(f'{td[i * 9].text}:{td[i * 9 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_66daili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'http://www.66ip.cn/{page}.html'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                               proxies=(await SQLHelper.select_score_top_proxy()).proxy
                                               )
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')[6:]
                proxies = []
                for i in range(len(td) // 5):
                    proxies.append(f'{td[i * 5].text}:{td[i * 5 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_89daili(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.89ip.cn/index_{page}.html'
            try:
                req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 5):
                    proxies.append(f'{td[i * 5].text.strip()}:{td[i * 5 + 1].text.strip()}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_taiyangdaili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://www.tyhttp.com/free/page{page}/'
            try:
                req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('.td')[8:]
                proxies = []
                for i in range(len(td) // 8):
                    proxies.append(f'{td[i * 8].text.strip()}:{td[i * 8 + 1].text.strip()}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_kxdaili_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.kxdaili.com/dailiip/1/{page}.html'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_kxdaili_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.kxdaili.com/dailiip/2/{page}.html'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_ip3366_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.ip3366.net/free/?stype=1&page={page}'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i, protocol='http')
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_ip3366_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'http://www.ip3366.net/free/?stype=2&page={page}'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i, protocol='https')
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_qiyun(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://proxy.ip3366.net/free/?action=china&page={page}'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7].text}:{td[i * 7 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_ihuan(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        page_list = ['b97827cc', '4ce63706', '5crfe930', 'f3k1d581', 'ce1d45977']
        for page in page_list:
            url = f'https://ip.ihuan.me/?page={page}'
            try:
                req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 10):
                    proxies.append(f'{td[i * 10].text}:{td[i * 10 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_docip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        gmt_format = '%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)'
        gmt = datetime.now().strftime(gmt_format)

        url = f'https://www.docip.net/data/free.json?t={gmt}'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            for i in req.json().get('data'):
                if ip := i.get('ip'):
                    append_dict = format_proxy(ip)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_openproxylist(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        url = f'https://openproxylist.xyz/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxyhub(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://proxyhub.me/'
            headers.update({"cookie": f"page={page};"})
            try:
                req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                self.log.info(url)
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tr>td')
                proxies = []
                for i in range(len(td) // 6):
                    proxies.append(f'{td[i * 6].text}:{td[i * 6 + 1].text}')

                # have_proxy = [x['proxy'] for x in self.proxy_list]

                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.critical(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')

                get_proxy_success = False

        return proxy_queue, get_proxy_success

    # endregion

    # region Github获取的text格式的代理，每行格式为ip:port
    async def get_proxy_from_parserpp_ip_ports(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/parserpp/ip_ports/main/proxyinfo.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_api_openproxylist_xyz_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://api.openproxylist.xyz/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i, protocol='https')
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_SevenworksDev_proxy_list_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/SevenworksDev/proxy-list/refs/heads/main/proxies/https.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_SevenworksDev_proxy_list_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/SevenworksDev/proxy-list/refs/heads/main/proxies/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_monosans_proxy_list(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_r00tee_Proxy_List(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_themiralay_Proxy_List_World(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/themiralay/Proxy-List-World/refs/heads/master/data.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_lalifeier_proxy_scraper_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/lalifeier/proxy-scraper/main/proxies/https.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_lalifeier_proxy_scraper_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/lalifeier/proxy-scraper/main/proxies/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_claude89757_free_https_proxies(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/claude89757/free_https_proxies/refs/heads/main/free_https_proxies.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text:
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Simatwa_free_proxies_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Simatwa/free-proxies/master/files/http.json'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.json().get('proxies'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zloi_user_hideipme(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/main/connect.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_elliottophellia_proxylist_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.rei.my.id/proxy/pHTTP'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_elliottophellia_proxylist_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.rei.my.id/proxy/pSOCKS5'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i, protocol='socks5')
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')
            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_officialputuid_KangProxy_KangProxy_https(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_officialputuid_KangProxy_KangProxy_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MuRongPIG_Proxy_Master(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxy_casals_ar_main_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/casals-ar/proxy.casals.ar/main/http'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_https(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_TheSpeedX_PROXY_List_master_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_yemixzy_proxy_list_main_proxies_http(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:
            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                addr = ''.join(re.findall('\d+.\d+.\d+.\d+', i.strip()))
                if addr:
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_sarperavci_freeCheckedHttpProxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/sarperavci/freeCheckedHttpProxies/main/freshHttpProxies.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_prxchk_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_andigwandi_free_proxy(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_elliottophellia_yakumo(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_im_razvan_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxy4parsing_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_mmpx12_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.critical(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    # endregion

    # region json格式代理（每个函数的json响应可能都不一样，要换里面解析json的方式）
    async def get_proxy_from_proxylist_geonode_com(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxylist.geonode.com/api/proxy-list?limit=500&page=2&sort_by=lastChecked&sort_type=desc'
        page = 1
        total_count = 0
        limit = 500
        while 1:
            params = {
                "limit": limit,
                "page": page,
                "sort_by": "lastChecked",
                "sort_type": "desc"
            }
            try:
                req = await my_async_httpx.get(url=url, params=params, headers=headers, verify=False,
                                               timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:
                req_dict = req.json()
                http_p = req_dict.get('data')
                total_count = req_dict.get('total')
                for da in http_p:
                    ip = da.get('ip')
                    port = da.get('port')
                    protocols = da.get('protocols')
                    for protocol in protocols:
                        if ip and port and protocol:
                            proxy_queue.append(format_proxy(f'{protocol}://{ip}:{port}', protocol=protocol))
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False
                break
            page += 1
            if page * limit >= total_count:
                break
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxydb_net(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxydb.net/list'
        offset = 0
        total_count = 0
        while 1:
            data = {
                "anonlvls": [],
                "offset": offset,
                "protocols": ["https", "http", "socks5"]
            }
            try:
                req = await my_async_httpx.post(url=url, data=data, headers=headers, verify=False, timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
            if req:
                req_dict = req.json()
                http_p = req_dict.get('proxies')
                total_count = req_dict.get('total_count')
                for da in http_p:
                    ip = da.get('ip')
                    port = da.get('port')
                    protocol = da.get('type')
                    if ip and port and protocol:
                        proxy_queue.append(format_proxy(f'{protocol}://{ip}:{port}'))
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False
                break
            offset += 30
            if offset >= total_count:
                break
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxy_953959_xyz(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxy.953959.xyz/all/'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
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

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxyshare(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://www.proxyshare.com/detection/proxyList?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
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

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_t0mer_free_proxies(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/t0mer/free-proxies/main/proxies.json'
        try:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except Exception:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

            await asyncio.sleep(10)
            # self.GetProxy_Flag = False
            get_proxy_success = False
            return proxy_queue, get_proxy_success
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

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_omegaproxy(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
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
                req = await my_async_httpx.get(url=url, headers=headers, params=params, verify=False,
                                               timeout=self.timeout)
            except Exception:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')

                await asyncio.sleep(10)
                # self.GetProxy_Flag = False
                get_proxy_success = False
                return proxy_queue, get_proxy_success
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

                get_proxy_success = False
        return proxy_queue, get_proxy_success

    # endregion

    # endregion
    # region 获取代理主函数
    async def __get_proxy(self):
        if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
            self.log.info(
                f'获取代理时间过短！返回！（冷却剩余：{self.get_proxy_sep_time - (int(time.time() - self.get_proxy_timestamp))}）')
            return
        else:
            self.GetProxy_Flag = True
        self.log.info(
            f'开始获取代理\t上次获取代理时间：{datetime.fromtimestamp(self.get_proxy_timestamp)}\t{datetime.now()}')
        self.get_proxy_timestamp = time.time()
        proxy_queue = []
        task_list = []
        try:
            task = asyncio.create_task(self.get_proxy_from_cn_proxy_tools())
            task_list.append(task)
        except Exception as e:
            self.log.critical(e)
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
        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxydb_net())
            task_list.append(task)
        except Exception as e:
            self.log.critical(e)

        try:
            task = asyncio.create_task(
                self.get_proxy_from_proxylist_geonode_com())
            task_list.append(task)
        except Exception as e:
            self.log.critical(e)

        results: Union[tuple[list[str], bool] or Exception] = await asyncio.gather(*task_list, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception) is True:
                self.log.exception(f'获取代理出错！{result}')
                continue
            _, get_proxy_success = result
            proxy_queue.extend(_)
        self.log.info(f'最终共有{len(proxy_queue)}个代理需要检查')

        all_tasks = []
        for i in range(len(proxy_queue)):
            all_tasks.append(self._check_ip_by_bili_zone(proxy_queue.pop()))
        await asyncio.gather(*all_tasks)
        self.log.info(f'代理已经检查完毕，并添加至数据库！')
        await SQLHelper.remove_list_dict_data_by_proxy()
        self.log.info(f'移除重复代理')
        get_proxy_success = True
        await SQLHelper.check_redis_data(True)
        return

    async def get_proxy(self):
        try:
            task = asyncio.create_task(self.__get_proxy())
            task.add_done_callback(self.set_GetProxy_Flag)
            await task
        except Exception as e:
            self.log.exception(e)

    def set_GetProxy_Flag(self, boolean: bool=False):
        self.GetProxy_Flag = boolean

    # endregion

    async def _check_ip_by_bili_zone(self, proxy: dict, status=0, score=50) -> bool:
        '''
        使用zone检测代理ip，没问题就追加回队首，返回True为可用代理
        :param status:
        :param proxy:
        :return:
        '''
        async with self._sem:
            if self.check_proxy_flag:
                try:
                    _url = 'http://api.bilibili.com/x/web-interface/zone'
                    _req = await my_async_httpx.get(url=_url, proxies=proxy, timeout=self.timeout)
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

    async def _add_to_proxy_list(self, proxy_dict: dict):
        '''
        增加新的proxy
        :param proxy_dict:
        :return:
        '''
        have_flag = await SQLHelper.is_exist_proxy_by_proxy(proxy_dict['proxy'])
        if not have_flag:
            self.log.debug(f'添加代理至数据库：{proxy_dict}')
            proxy_dict.update({'add_ts': int(time.time())})
            proxy_tab = ProxyTab(
                **proxy_dict
            )
            await SQLHelper.add_to_proxy_tab_database(proxy_tab)


get_proxy_methods = GetProxyMethods()
if __name__ == "__main__":
    asyncio.run(get_proxy_methods.get_proxy_from_cn_proxy_tools())
