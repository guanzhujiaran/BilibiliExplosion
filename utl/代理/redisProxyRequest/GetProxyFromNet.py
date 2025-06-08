"""
从网上获取代理
"""
import asyncio
import inspect
import json
import re
import time
from datetime import datetime
import bs4
from CONFIG import CONFIG
from fastapi接口.log.base_log import sql_log
from fastapi接口.utils.Common import sem_wrapper, sem_gen, retry_wrapper
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from utl.代理.数据库操作.comm import format_proxy

_github_proxy = {
    'http': CONFIG.V2ray_proxy,
    'https': CONFIG.V2ray_proxy
}


class GetProxyMethods:
    get_proxy_page = 10
    log = sql_log
    get_proxy_timestamp = 0
    timeout = 10
    get_proxy_sep_time = 2 * 3600  # 获取代理的间隔
    check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
    GetProxy_Flag = False
    _sem = sem_gen()

    # region a从代理网站获取代理

    # region a从免费代理网站获取代理，每个网站的表格不一样，需要测试！网站按照表格的样式填充代理信息

    def __init__(self):
        self._lock = asyncio.Lock()

    async def get_proxy_from_cn_proxy_tools(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://cn.proxy-tools.com/proxy?page={page}'
            headers.update({'Referer': url})
            req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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

    async def get_proxy_from_kuaidaili_dps(self) -> tuple[list, bool]:
        headers = {
            'cookie': "channelid=0; sid=1744472570698409; _ga=GA1.1.1164732364.1744473880; _gcl_au=1.1.1549492445.1744473880; _ss_s_uid=b40a1d7896a217a1d7db1800aad1c025; _ga_DC1XM0P4JL=GS1.1.1746241898.3.1.1746241905.53.0.0",
            'Sec-Fetch-Site': 'same-origin',
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):

            url = f'https://www.kuaidaili.com/free/dps/{page}'
            headers.update({'Referer': url})
            req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            if req:
                html = bs4.BeautifulSoup(req.text, 'html.parser')
                script = html.select('script[type="text/javascript"]')
                json_str = ''
                for x in filter(lambda y: y.text and 'valid_minute' in x.text, script):
                    json_str = ''.join(re.findall('const fpsList =(.*);', x.text))
                proxies = json.loads(json_str)

                for i in proxies:
                    if i:
                        append_dict = format_proxy(f"{i.get('ip')}:{i.get('port')}", protocol='http')
                        if not append_dict:
                            self.log.exception(f'代理格式错误！{i}')
                            continue
                        # if append_dict not in have_proxy:
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'代理获取失败！\n{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False

            await asyncio.sleep(6)
        return proxy_queue, get_proxy_success

    async def get_proxy_from_kuaidaili_fps(self) -> tuple[list, bool]:
        headers = {
            'cookie': "channelid=0; sid=1744472570698409; _ga=GA1.1.1164732364.1744473880; _gcl_au=1.1.1549492445.1744473880; _ss_s_uid=b40a1d7896a217a1d7db1800aad1c025; _ga_DC1XM0P4JL=GS1.1.1746241898.3.1.1746241905.53.0.0",
            'Sec-Fetch-Site': 'same-origin',
            'user-agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.kuaidaili.com/free/fps/{page}'
            headers.update({'Referer': url})
            req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            if req:
                html = bs4.BeautifulSoup(req.text, 'html.parser')
                script = html.select('script[type="text/javascript"]')
                json_str = ''
                for x in filter(lambda y: y.text and 'last_check_time' in x.text, script):
                    json_str = ''.join(re.findall('const fpsList =(.*);', x.text))
                proxies = json.loads(json_str)
                for i in proxies:
                    if i:
                        append_dict = format_proxy(f"{i.get('ip')}:{i.get('port')}", protocol='http')
                        if not append_dict:
                            self.log.exception(f'代理格式错误！{i}')
                            continue
                        # if append_dict not in have_proxy:
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 10:
                    self.log.info(f'代理获取失败！\n{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False
            await asyncio.sleep(6)
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zdayip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.zdaye.com/free/{page}/'
            req = await my_async_httpx.get(url=url, headers=headers, verify=False,
                                           proxies=(await SQLHelper.select_score_top_proxy()).proxy)
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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                           proxies=(await SQLHelper.select_score_top_proxy()).proxy
                                           )

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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
        def fr(YH):
            oo = [0x91, 0x66, 0xbc, 0xe1, 0x53, 0x94, 0xc5, 0x00, 0x40, 0x93, 0x52, 0x97, 0xd4, 0x12, 0xdc, 0x12, 0x4b,
                  0x9c, 0x7d, 0x2a, 0x65, 0xc3, 0x37, 0x8a, 0xf5, 0x5b, 0x78, 0xd1, 0x58, 0x8b, 0xd0, 0x14, 0x45, 0x8e,
                  0xf5, 0xfe, 0x28, 0x67, 0xac, 0xfd, 0xde, 0xa9, 0x23, 0x0e, 0x5d, 0x8e, 0xd3, 0x1b, 0x42, 0x14, 0xec,
                  0xd7, 0xaa, 0x9d, 0xc6, 0x0c, 0x06, 0x55, 0x30, 0x61, 0xaa, 0xef, 0x37, 0x9d, 0x68, 0x55, 0x26, 0x1f,
                  0xed, 0xae, 0x78, 0xa7, 0xa0, 0x73, 0xba, 0x7b, 0x4e, 0xab, 0x9c, 0xc3, 0xb6, 0x77, 0x52, 0x83, 0x61,
                  0x50, 0x3b, 0xfb, 0x25, 0x6a, 0x59, 0xdc, 0xad, 0xfc, 0xd5, 0xa8, 0xf7, 0xd0, 0xd5, 0xc0, 0x8f, 0x76,
                  0x37, 0x20, 0xec, 0x0e, 0x00, 0xcf, 0xba, 0x9f, 0x7a, 0x47, 0x7c, 0x4d, 0x38, 0x0d, 0xd7, 0x09, 0x64,
                  0x0b, 0x76, 0xaf, 0x17, 0x48, 0xad, 0x8e, 0x7c, 0x89, 0xda, 0x0e, 0xd0, 0x9b, 0x80, 0x7a, 0x45, 0x06,
                  0x0f, 0x7a, 0xc1, 0x82, 0x0f, 0xf5, 0xc6, 0x91, 0x7a, 0x55, 0x2c, 0x25, 0x18, 0xe8, 0xdf, 0xb0, 0x9b,
                  0x46, 0x17, 0x04, 0x05, 0x38, 0x0d, 0xd7, 0x0b, 0x49, 0x86, 0xc7, 0x11, 0x4a, 0x89, 0x6a, 0x4c, 0x0b,
                  0xe5, 0xde, 0x18, 0x63, 0x22, 0x62, 0xa7, 0xe6, 0xdb, 0x86, 0xf1, 0x3b, 0xf5, 0x49, 0x84, 0x65, 0x22,
                  0x17, 0xc1, 0x4a, 0x6f, 0xc0, 0xe5, 0x57, 0xbe, 0xef, 0x95, 0x42, 0x37, 0x84, 0xdd, 0x1d, 0x50, 0x30,
                  0x6d, 0xda, 0x99, 0xcc, 0x0a, 0x4f, 0x0d, 0x7e, 0xbf, 0xf0, 0x30, 0x83, 0x42, 0x81, 0xc4, 0x02, 0x47,
                  0x90, 0xe3, 0x3d, 0xe7, 0x25, 0x64, 0x45, 0x12, 0x4d, 0xc0, 0xcd, 0x21, 0x8c, 0xf1, 0xc8, 0x85, 0x42,
                  0x4a, 0xb7, 0x05, 0x72, 0x31, 0x0c, 0xe4, 0xc7, 0x01, 0x6c, 0x2b, 0x70, 0xaf, 0x6c, 0x04, 0x5d, 0x9c,
                  0xcf, 0x01, 0x7c, 0x99, 0x01, 0xe9, 0xa8, 0xe3, 0x57, 0x98, 0xdb, 0x38, 0x04, 0x3b]

            # 第一轮处理
            qo = 267
            while qo >= 2:
                oo[qo] = (-oo[qo]) & 0xff
                oo[qo] = (((oo[qo] >> 5) | ((oo[qo] << 3) & 0xff)) - 12) & 0xff
                qo -= 1

            # 第二轮处理
            qo = 266
            while qo >= 3:
                oo[qo] = (oo[qo] - oo[qo - 1]) & 0xff
                qo -= 1

            # 第三轮处理
            for qo in range(1, len(oo)):
                oo[qo] = ((((oo[qo] + 110) & 0xff) + 181) & 0xff) << 4 & 0xff | \
                         ((((oo[qo] + 110) & 0xff) + 181) & 0xff) >> 4

            # 构建输出字符串
            po = ""
            for qo in range(1, len(oo) - 1):
                if qo % 7 != 0:
                    po += chr(oo[qo] ^ YH)

            return po

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
            'cookie': re.search(r'https_ydclearance=[^;]+', fr(252)).group(0)
        }
        get_proxy_success = True
        proxy_queue = []
        for page in range(1, self.get_proxy_page + 1):
            url = f'https://www.89ip.cn/index_{page}.html'
            req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)

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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
                            continue
                        proxy_queue.append(append_dict)
                if len(proxy_queue) < 5:
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
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)

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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
            url = f'https://www.qiyunip.com/freeProxy/{page}.html'
            req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)

            if req:

                html = bs4.BeautifulSoup(req.text, 'html.parser')
                td = html.select('tbody>tr>th')
                proxies = []
                for i in range(len(td) // 7):
                    proxies.append(f'{td[i * 7 + 3].text}://{td[i * 7].text}:{td[i * 7 + 1].text}')
                for i in proxies:
                    if i:
                        append_dict = format_proxy(i)
                        if not append_dict:
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "content-type": "",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }
        get_proxy_success = True
        proxy_queue = []
        url = f'https://ip.ihuan.me/'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
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
                        self.log.exception(f'代理格式错误！{i}\n{td}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)

        if req:

            for i in req.json().get('data'):
                if ip := i.get('ip'):
                    append_dict = format_proxy(ip)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)

        if req:

            proxies = []

            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
            req = await my_async_httpx.get(url=url, verify=False, headers=headers, timeout=self.timeout)

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
                            self.log.exception(f'代理格式错误！{i}\n{td}')
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
    async def get_proxy_from_proxy_scdn_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxy.scdn.io/text.php'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxy_list_download_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://www.proxy-list.download/api/v1/get?type=http'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxy_list_download_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://www.proxy-list.download/api/v1/get?type=socks5'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_sunny9577_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/socks5_proxies.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_sunny9577_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/http_proxies.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Vadim287_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Vadim287/free-proxy/refs/heads/main/proxies/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Vadim287_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Vadim287/free-proxy/refs/heads/main/proxies/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_VMHeaven_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_VMHeaven_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/https.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_VMHeaven_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_RioMMO_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/RioMMO/ProxyFree/refs/heads/main/HTTP.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_RioMMO_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/RioMMO/ProxyFree/refs/heads/main/SOCKS5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_databay_labs_lists_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_databay_labs_lists_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Tsprnay_Proxy_lists_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Tsprnay_Proxy_lists_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/https.txt'
        req = await my_async_httpx.get(
            url=url,
            headers=headers,
            verify=False,
            timeout=self.timeout,
            proxies=_github_proxy
        )
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_Tsprnay_Proxy_lists_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_M_logique_Proxies_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/M-logique/Proxies/refs/heads/main/proxies/regular/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_M_logique_Proxies_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/M-logique/Proxies/refs/heads/main/proxies/regular/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_ALIILAPRO_Proxy_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/ALIILAPRO/Proxy/refs/heads/main/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_theriturajps_proxy_list_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/theriturajps/proxy-list/refs/heads/main/proxies.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_SevenworksDev_proxy_list_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/SevenworksDev/proxy-list/refs/heads/main/proxies/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_gh_proxifly_free_proxy_list(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_fyvri_fresh_proxy_list_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_fyvri_fresh_proxy_list_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/https.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_fyvri_fresh_proxy_list_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_BreakingTechFr_Proxy_Free_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/refs/heads/main/proxies/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_BreakingTechFr_Proxy_Free_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/refs/heads/main/proxies/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zloi_user_hideip_me_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zloi_user_hideip_me_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/https.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zloi_user_hideip_me_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_zloi_user_hideip_me_connect(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/zloi-user/hideip.me/refs/heads/master/connect.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_trio666_proxy_checker(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/trio666/proxy-checker/refs/heads/main/all.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_https2(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/https2.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_socks5_2(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/socks5_2.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_http2(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/http2.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := ':'.join(i.strip().split(':')[0:2]):
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_socks5(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_https(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/https.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_MohammadHosseinkargar_proxy_http(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/MohammadHosseinkargar/proxylist/refs/heads/main/http.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_nhan0o22_proxy(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/nhan0o22/proxy/refs/heads/master/proxy.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_parserpp_ip_ports(self) -> tuple[list, bool]:
        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://cdn.jsdelivr.net/gh/parserpp/ip_ports/proxyinfo.json'
        req = await my_async_httpx.get(
            url=url,
            headers=headers,
            verify=False,
            timeout=self.timeout,
            proxies=_github_proxy
        )
        if req:
            proxies = []
            for i in req.text.split('}'):
                if i.strip():
                    i_dict = json.loads(i + '}')
                    port = i_dict.get('port')
                    host = i_dict.get('host')
                    protocol = i_dict.get('type')
                    append_dict = format_proxy(f'{protocol}://{host}:{port}', protocol=protocol)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)

        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False
        return proxy_queue, get_proxy_success

    async def get_proxy_from_r00tee_Proxy_List_socks5(self) -> tuple[list, bool]:

        headers = {
            'user-agent': CONFIG.rand_ua
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(i, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_.split(' ')[0], protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_.split(' ')[0], protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []
            for i in req.json().get('proxies'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(
            url=url,
            headers=headers,
            verify=False,
            timeout=self.timeout,
            proxies=_github_proxy
        )
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        if req:
            proxies = []
            for i in req.text.split('\n'):
                if _ := i.strip():
                    append_dict = format_proxy(_, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{_}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
                        continue
                    proxy_queue.append(append_dict)
            if len(proxy_queue) < 10:
                self.log.info(f'{req.text}, {url}')
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
        else:
            self.log.info(f'{req.text}, {url}')

            get_proxy_success = False

        return proxy_queue, get_proxy_success

    async def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_socks5(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }

        get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt'
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i, protocol='socks5')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i, protocol='http')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i, protocol='https')
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:
            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                addr = ''.join(re.findall('\d+.\d+.\d+.\d+', i.strip()))
                if addr:
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
        if req:

            proxies = []

            for i in req.text.split('\n'):
                if i.strip():
                    append_dict = format_proxy(i)
                    if not append_dict:
                        self.log.exception(f'代理格式错误！{i}')
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
    async def get_proxy_from_kgtools(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = 'https://www.kgtools.cn/api/proxy/ops/list/'
        for pn in range(1, self.get_proxy_page + 1):
            params = {
                'label': 1,
                'name': '全国代理ip',
                'page': pn
            }
            req = await my_async_httpx.get(url=url, headers=headers, params=params, verify=False,
                                           timeout=self.timeout)
            if req:
                req_dict = req.json()
                http_p = req_dict.get('data', {}).get('data')
                if not http_p:
                    break
                for da in http_p:
                    ip = da.get('proxy_ip')
                    port = da.get('port')
                    protocol_type = da.get('type')
                    if protocol_type == 'HTTP':
                        protocol = 'http'
                    elif protocol_type == 'HTTPS':
                        protocol = 'https'
                    elif protocol_type == "SOCKS5":
                        protocol = 'socks5'
                    else:
                        protocol = 'http'
                    proxy_queue.append(format_proxy(f'{ip}:{port}', protocol=protocol))
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False
                break
        return proxy_queue, get_proxy_success

    async def get_proxy_from_lumiproxy(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = 'https://api.lumiproxy.com/web_v1/free-proxy/list?page_size=6000&page=1&language=zh-hans'

        while 1:
            req = await my_async_httpx.get(url=url, headers=headers, verify=False,
                                           timeout=self.timeout)
            if req:
                req_dict = req.json()
                http_p = req_dict.get('data').get('list')
                for da in http_p:
                    ip = da.get('ip')
                    port = da.get('port')
                    protocol_type = da.get('protocol')
                    if protocol_type == 1:
                        protocol = 'http'
                    elif protocol_type == 2:
                        protocol = 'https'
                    elif protocol_type == 4:
                        protocol = 'socks4'
                    elif protocol_type == 8:
                        protocol = 'socks5'
                    else:
                        protocol = 'http'
                    proxy_queue.append(format_proxy(f'{ip}:{port}', protocol=protocol))
                if len(proxy_queue) < 10:
                    self.log.info(f'{req.text}, {url}')
                self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
                break
            else:
                self.log.info(f'{req.text}, {url}')
                get_proxy_success = False
                break
        return proxy_queue, get_proxy_success

    async def get_proxy_from_proxylist_geonode_com(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': CONFIG.rand_ua,
        }
        get_proxy_success = True
        req = ''
        proxy_queue = []
        url = f'https://proxylist.geonode.com/api/proxy-list'
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
            req = await my_async_httpx.get(url=url, params=params, headers=headers, verify=False,
                                           timeout=self.timeout)
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
        for pn in range(0, self.get_proxy_page):
            offset = 30 * pn
            data = {
                "anonlvls": [],
                "offset": offset,
                "protocols": ["https", "http", "socks5"]
            }
            req = await my_async_httpx.post(url=url, data=json.dumps(data), headers=headers, verify=False,
                                            timeout=self.timeout)
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout)
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
        req = await my_async_httpx.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                       proxies=_github_proxy)
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

    # endregion

    # endregion
    # region 获取代理主函数
    async def __get_proxy(self):
        if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
            return
        async with self._lock:
            if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
                self.log.info(
                    f'获取代理时间过短！返回！（冷却剩余：{self.get_proxy_sep_time - (int(time.time() - self.get_proxy_timestamp))}）')
                return
            else:
                self.get_proxy_timestamp = time.time()
                self.GetProxy_Flag = True
        start_ts = int(time.time())
        self.log.critical(
            f'开始获取代理\t上次获取代理时间：{datetime.fromtimestamp(self.get_proxy_timestamp)}\t{datetime.now()}')
        proxy_queue = []
        funcs = inspect.getmembers(get_proxy_methods, predicate=inspect.iscoroutinefunction)
        tasks = set()
        for name, fn in funcs:
            if name.startswith('get_proxy_from'):
                task = asyncio.create_task(fn())
                tasks.add(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) is True:
                self.log.opt(exception=True).error(f'获取代理出错！{result}')
                continue
            _, get_proxy_success = result
            proxy_queue.extend(_)
        _s = set()
        _t = []
        for i in proxy_queue:
            if list(i.values())[0] in _s:
                continue
            else:
                _t.append(i)
                _s.add(list(i.values())[0])
        del proxy_queue
        proxy_queue = _t

        self.log.info(f'最终共有{len(proxy_queue)}个代理需要检查')
        for i in range(len(proxy_queue)):
            task = asyncio.create_task(self._check_ip_by_bili_zone(proxy_queue.pop()))
            tasks.add(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        self.log.info(f'代理已经检查完毕，并添加至数据库！')
        await SQLHelper.remove_list_dict_data_by_proxy()
        self.log.info(f'移除重复代理')
        self.log.critical(
            f'获取代理完成\t耗时：{int(time.time()) - start_ts}秒')
        get_proxy_success = True
        await SQLHelper.check_redis_data()
        return

    async def get_proxy(self):
        task = asyncio.create_task(self.__get_proxy())
        task.add_done_callback(lambda _: self.set_GetProxy_Flag(False))
        await task

    def set_GetProxy_Flag(self, boolean: bool = False):
        self.GetProxy_Flag = boolean

    # endregion
    @retry_wrapper
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
            proxy_dict.update({'add_ts': int(time.time())})
            proxy_tab = ProxyTab(
                **proxy_dict
            )
            await SQLHelper.add_to_proxy_tab_database(proxy_tab)


get_proxy_methods = GetProxyMethods()

if __name__ == "__main__":
    asyncio.run(get_proxy_methods.get_proxy())
