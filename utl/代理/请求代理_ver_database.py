# -*- coding: utf-8 -*-
import os
import random
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from functools import reduce

import bs4
import requests
from loguru import logger
from requests import session
from selenium import webdriver

from CONFIG import CONFIG
from .数据库操作 import sqlite3_proxy_op as sqlite3_proxy_op


class request_with_proxy:
    def Get_Bili_Cookie(self, ua: str) -> str:
        url = 'https://t.bilibili.com/'
        opt = webdriver.ChromeOptions()
        # opt.binary_location = "C:/Python39/chromedriver.exe"
        if ua:
            opt.add_argument(f'--user-agent={ua}')
        opt.add_argument('--no-sandbox')
        opt.add_argument('--disable-dev-shm-usage')
        opt.add_argument('--headless')
        opt.add_argument('blink-settings=imagesEnabled=false')
        opt.add_argument('--disable-gpu')
        opt.add_argument('--disable-extensions')
        opt.add_argument('--remote-debugging-port=9222')
        browser = webdriver.Chrome(options=opt,
                                   # service=Service("C:/Python39/chromedriver.exe")
                                   )
        browser.get(url)
        time.sleep(3)
        bili_unlogin_cookie_list = browser.get_cookies()
        browser.quit()
        cookie_str = ''
        for cookie in bili_unlogin_cookie_list:
            cookie_str += f'{cookie["name"]}={cookie["value"]}; '
        return cookie_str.strip('; ')

    def __init__(self):
        self.channel = 'bili'
        self.sqlite3_proxy_op = sqlite3_proxy_op.SQLHelper(CONFIG.database.proxy_db,
                                                           'proxy_tab')
        self.max_get_proxy_sep = 2 * 3600 * 24  # 最大间隔两天获取一次网络上的代理
        self.log = logger.bind(user=__name__)
        # self.log.remove()
        self.log.add(sys.stdout, level='ERROR')
        self.get_proxy_sep_time = 2 * 3600  # 获取代理的间隔
        self.get_proxy_timestamp = 0
        self.check_proxy_time = {
            'last_checked_ts': 0, # 最后一次检查和刷新代理的时间
            'checked_ts_sep': 2 * 3600
        }
        self.get_proxy_lock = threading.Lock()
        self.get_proxy_page = 7  # 获取代理网站的页数
        self.write_proxy_lock = threading.Lock()
        self.fresh_proxy_lock = threading.Lock()
        self.__dir_path = CONFIG.root_dir + 'utl/代理/'
        self.check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
        self.fresh_cookie_lock = threading.Lock()
        self._352_time = 0
        self.lock = threading.Lock()
        self.set_proxy_lock = threading.RLock()
        self.timeout = 10
        self.mode = 'single'  # single || rand
        self.mode_fixed = False  # 是否固定mode
        self.proxy_apikey = ''
        if os.path.exists(self.__dir_path + '代理api_key.txt'):
            with open(self.__dir_path + '代理api_key.txt', 'r', encoding='utf-8') as f:
                self.proxy_apikey = f.read().strip()
        self.using_p_dict = dict()  # 正在使用的代理
        self.GetProxy_Flag = False
        self.s = session()
        self.ban_proxy_pool = []  # 无法使用的代理列表
        self.ban_ua_list = []
        self.User_Agent_List = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 SE 2.X MetaSr 1.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
            'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
            'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
            'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
            'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999',
        ]
        self.fake_cookie = ''
        self._refresh_412_proxy()

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def get_one_rand_proxy(self):
        return self.sqlite3_proxy_op.select_one_proxy('rand', channel=self.channel)

    def request_with_proxy(self, *args, **kwargs) -> dict:
        kwargs.update(*args)
        args = ()
        while True:
            # if kwargs.get('headers').get('user-agent'):
            #     if kwargs.get('headers').get('user-agent') in self.ban_ua_list:
            #         if self.User_Agent_List:
            #             kwargs.get('headers').update({
            #                 'user-agent': random.choice(self.User_Agent_List)
            #             })
            with self.fresh_cookie_lock:
                if kwargs.get('headers').get('cookie'):
                    if self.fake_cookie:
                        kwargs.get('headers').update({'cookie': self.fake_cookie})
                    else:
                        self.fake_cookie = self.Get_Bili_Cookie(kwargs.get('headers').get('user-agent'))
                        kwargs.get('headers').update({'cookie': self.fake_cookie})
            if self.GetProxy_Flag:
                self.log.info('获取代理中')
                time.sleep(30)
                t = threading.Timer(30, self.set_GetProxy_Flag, (False,))  # 获取结束之后等待30秒，之后设为False，允许开始下一轮获取代理
                t.start()
                continue
            p_dict = self._set_new_proxy()
            p = p_dict.get('proxy')
            status = 0
            if not p:
                time.sleep(10)
                self._refresh_412_proxy()
                continue
            try:
                req = self.s.request(*args, **kwargs, proxies=p, timeout=self.timeout)
                if 'code' not in req.text and self.channel == 'bili':  # 如果返回的不是json那么就打印出来看看是什么
                    self.log.info(req.text)
                try:
                    req_dict = req.json()
                except:
                    logger.error(f'解析为dict时失败，相应内容为：{req.text}')
                    raise ValueError
                if type(req_dict) is list:
                    p_dict['score'] += 10
                    p_dict['status'] = status
                    self._update_to_proxy_dict(p_dict, score_plus_Flag=True)
                    return req_dict
                if req_dict.get('code') == -412 or req_dict.get('code') == -352 or req_dict.get('code') == 65539:
                    if not self.mode_fixed:
                        self.mode = 'rand'
                    self.log.error(
                        f'{req_dict.get("code")}报错,换个ip\t{p_dict}\t{self._timeshift(time.time())}\t{req_dict}\n{args}\t{kwargs}')
                    if req_dict.get('code') == 65539:
                        pass
                    else:
                        status = -412
                    if req_dict.get('code') == -412:
                        # self._check_ip_by_bili_zone(p, status=status, score=p_dict['score'])  # 如何代理ip检测没问题就追加回去
                        pass
                    elif req_dict.get('code') == -352:
                        with self.fresh_cookie_lock:
                            self._352_time += 1
                            if self._352_time >= 10:
                                self.fake_cookie = self.Get_Bili_Cookie(kwargs.get('headers').get('user-agent'))
                                self._352_time = 0
                    p_dict['score'] += 10
                    p_dict['status'] = status
                    self._update_to_proxy_dict(p_dict, score_plus_Flag=True, change_score_num=10)
                    # return self.request_with_proxy(*args, **kwargs)

                    continue
                if req_dict.get('code') == 0 or req_dict.get('code') == 4101131 or req_dict.get('code') == -9999:
                    if not self.mode_fixed:
                        self.mode = 'single'
                    logger.info(f'获取成功(rid:{kwargs.get("url")})：\n{p_dict}')
                    p_dict['score'] = 100
                    p_dict['status'] = 0
                    self._update_to_proxy_dict(p_dict, score_plus_Flag=True, change_score_num=200)

            except Exception as e:
                # if p not in self.ban_proxy_pool:
                #     self.ban_proxy_pool.append(p)
                # try:
                #     self._remove_proxy_list(p_dict['proxy'])
                # except:
                #     pass
                if not self.mode_fixed:
                    self.mode = 'rand'
                if self.channel != 'zhihu':
                    p_dict['score'] -= 50
                    p_dict['status'] = 0
                    self._update_to_proxy_dict(p_dict, score_minus_Flag=True, change_score_num=50)
                self._set_new_proxy()
                logger.warning(
                    f'{self.mode}使用代理访问失败，代理扣分。{e}\t{kwargs}\n获取请求时使用的代理信息：{p_dict}\t{self._timeshift(time.time())}\t剩余{self.sqlite3_proxy_op.get_available_proxy_nums()}/{self.sqlite3_proxy_op.get_all_proxy_nums()}个代理，当前禁用代理{len(self.ban_proxy_pool)}个：')
                if len(self.ban_proxy_pool) > 30:
                    self.ban_proxy_pool.clear()
                # return self.request_with_proxy(*args, **kwargs)
                continue
            p_dict['score'] += 10
            p_dict['status'] = status
            self._update_to_proxy_dict(p_dict, score_plus_Flag=True)
            return req_dict

    def set_GetProxy_Flag(self, boolean: bool):
        self.GetProxy_Flag = boolean

    # region 从代理网站获取代理
    def get_proxy_from_padaili(self) -> tuple[list, bool]:
        """
        返回一个等待检查的proxy队列,
        队列内容如下：
        {
                        'http': 'http' + '://' + i,
                        'https': 'http' + '://' + i
                    }
        :return:
        """
        Get_proxy_success = True
        url = f'https://www.padaili.com/proxyapi?api={self.proxy_apikey}&num=200&type={random.choice([3])}&order=jiance'
        req = ''
        proxy_queue = []
        try:
            req = self.s.get(url=url)
        except:
            self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                    f.write(self.proxy_apikey)
                self.GetProxy_Flag = False
                Get_proxy_success = False
            proxies = req.text.split('<br/>')
            proxies.reverse()
            # have_proxy = [x['proxy'] for x in self.proxy_list]

            for i in proxies:
                if i:
                    append_dict = {
                        'http': 'http' + '://' + i,
                        'https': 'http' + '://' + i
                    }
                    # if append_dict not in have_proxy:
                    proxy_queue.append(append_dict)
            self.log.info(f'总共有{len(proxy_queue)}个代理需要检查')
            if len(proxy_queue) < 100:
                self.log.info(f'{req.text}, {url}')
        else:
            Get_proxy_success = False
        if len(proxy_queue) < 100:
            self.log.info(f'{req.text}, {url}')
        return proxy_queue, Get_proxy_success

    def get_proxy_from_kuaidaili(self) -> tuple[list, bool]:
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
                req = self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                self.log.info(url)
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_zdayip(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'https://www.zdaye.com/free/{page}/'
            try:
                req = self.s.get(url=url, headers=headers, verify=False,
                                 proxies=self.sqlite3_proxy_op.select_score_top_proxy().get('proxy'))
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req.status_code == 200:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_66daili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'http://www.66ip.cn/{page}.html'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout,
                                 proxies=self.sqlite3_proxy_op.select_score_top_proxy().get('proxy')
                                 )
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                self.log.info(url)
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_89daili(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'https://www.89ip.cn/index_{page}.html'
            try:
                req = self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                self.log.info(url)
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_taiyangdaili(self) -> tuple[list, bool]:
        headers = {
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43",
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):

            url = f'https://www.tyhttp.com/free/page{page}/'
            try:
                req = self.s.get(url=url, verify=False, headers=headers, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                self.log.info(url)
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_kxdaili_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.kxdaili.com/dailiip/1/{page}.html'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_kxdaili_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }
        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.kxdaili.com/dailiip/2/{page}.html'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_ip3366_1(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.ip3366.net/free/?stype=1&page={page}'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_ip3366_2(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'http://www.ip3366.net/free/?stype=2&page={page}'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_qiyun(self) -> tuple[list, bool]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []
        for page in range(1, self.get_proxy_page):
            url = f'https://proxy.ip3366.net/free/?action=china&page={page}'
            try:
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_ihuan(self) -> tuple[list, bool]:
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
                req = self.s.get(url=url, headers=headers, verify=False, timeout=self.timeout)
            except:
                # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                time.sleep(10)
                # self.GetProxy_Flag = False
                Get_proxy_success = False
            if req:
                # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
                # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
                # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
                #     f.write(proxy_apikey)
                # self.GetProxy_Flag = False
                # Get_proxy_success = False
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
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_docip(self) -> tuple[list, bool]:
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
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_openproxylist(self) -> tuple[list, bool]:
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
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_proxy_casals_ar_main_http(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/casals-ar/proxy.casals.ar/main/http'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_https(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_yemixzy_proxy_list_main_proxies_http(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_TheSpeedX_PROXY_List_master_http(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.79',
        }

        Get_proxy_success = True
        req = ''
        proxy_queue = []

        url = f'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt'
        try:
            req = requests.get(url=url, headers=headers, verify=False, timeout=self.timeout)
        except:
            # self.log.info(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
            traceback.print_exc()
            time.sleep(10)
            # self.GetProxy_Flag = False
            Get_proxy_success = False
        if req:
            # if '您的套餐已过期' in req.text or '参数错误' in req.text or '请先验证邮箱，然后再提取代理' in req.text:
            # self.proxy_apikey = input('前往 https://www.padaili.com 获取新的apikey\n请输入新的代理apikey')
            # with open(self.__dir_path + '代理api_key.txt', 'w', encoding='utf-8') as f:
            #     f.write(proxy_apikey)
            # self.GetProxy_Flag = False
            # Get_proxy_success = False
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
        time.sleep(3)
        return proxy_queue, Get_proxy_success

    def __get_proxy(self):
        Get_proxy_success = False
        with self.get_proxy_lock:
            if self.GetProxy_Flag or time.time() - self.get_proxy_timestamp < self.get_proxy_sep_time:
                return
            else:
                self.GetProxy_Flag = True
                self.get_proxy_timestamp = time.time()
            self.log.info(f'开始获取代理\t{self._timeshift(time.time())}')
            proxy_queue = []
            # proxy_queue, Get_proxy_success = self.get_proxy_from_padaili()
            try:
                _, Get_proxy_success = self.get_proxy_from_kuaidaili()
                proxy_queue.extend(_)
            except Exception as e:

                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_66daili()
                proxy_queue.extend(_)
            except Exception as e:
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_89daili()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_taiyangdaili()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_kxdaili_1()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_kxdaili_2()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_ip3366_1()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_ip3366_2()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_qiyun()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_ihuan()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_docip()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_openproxylist()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_zdayip()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_proxy_casals_ar_main_http()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)

            try:
                _, Get_proxy_success = self.get_proxy_from_Zaeem20_FREE_PROXIES_LIST_master_http()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_roosterkid_openproxylist_main_HTTPS_RAW()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_yemixzy_proxy_list_main_proxies_http()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_Free_Proxies_blob_main_proxy_files_http_proxies()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_Free_Proxies_blob_main_proxy_files_https_proxies()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_TheSpeedX_PROXY_List_master_http()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)
            try:
                _, Get_proxy_success = self.get_proxy_from_proxifly_free_proxy_list_main_proxies_protocols_http_data()
                proxy_queue.extend(_)
            except Exception as e:
                traceback.print_exc()
                self.log.error(e)

            self.log.info(f'最终共有{len(proxy_queue)}个代理需要检查')

            threads = []
            for i in range(len(proxy_queue)):
                thread = threading.Thread(target=self._check_ip_by_bili_zone, args=(proxy_queue.pop(),))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()

            self.sqlite3_proxy_op.remove_list_dict_data_by_proxy()
            self.log.info(f'总共还有{self.sqlite3_proxy_op.get_all_proxy_nums()}个有效代理')
            Get_proxy_success = True

        # if Get_proxy_success:
        #     return
        # else:
        #     return self.get_proxy()
        return

    def get_proxy(self):
        try:
            thd = threading.Thread(target=self.__get_proxy)
            thd.start()
            thd.join(180)
        except Exception as e:
            traceback.print_exc()
            self.log.error(e)
        finally:
            t = threading.Timer(30, self.set_GetProxy_Flag, (False,))  # 获取结束之后等待30秒，之后设为False，允许开始下一轮获取代理
            t.start()

    # endregion

    def _remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    def _check_ip_by_bili_zone(self, proxy: dict, status=0, score=50) -> bool:
        '''
        使用zone检测代理ip，没问题就追加回队首，返回True为可用代理
        :param status:
        :param proxy:
        :return:
        '''
        if not self.sqlite3_proxy_op.is_exist_proxy_by_proxy(proxy):
            if self.check_proxy_flag:
                try:
                    _url = 'http://api.bilibili.com/x/web-interface/zone'
                    _req = self.s.get(url=_url, proxies=proxy, timeout=self.timeout)
                    if _req.json().get('code') == 0:
                        # self.log.info(f'代理检测成功，添加回代理列表：{_req.json()}')
                        self._add_to_proxy_list(self._proxy_warrper(proxy, status, score))
                        return True
                    else:
                        # self.log.info(f'代理失效：{_req.text}')
                        return False
                except Exception as e:
                    # self.log.info(f'代理检测失败：{proxy}')
                    return False
            else:
                self._add_to_proxy_list(self._proxy_warrper(proxy, status, score))
                return True
        else:
            return True

    def _proxy_warrper(self, proxy, status=0, score=50):
        return {"proxy": proxy, "status": status, "update_ts": int(time.time()), 'score': score}

    def _set_new_proxy(self):
        with self.set_proxy_lock:
            while not self.sqlite3_proxy_op.get_all_proxy_nums():
                self.get_proxy()  # 如果代理列表用完了就去获取新的代理
                time.sleep(10)
            while 1:
                try:
                    p_dict = self.sqlite3_proxy_op.select_one_proxy(self.mode, channel=self.channel)
                    if p_dict == {}:
                        self.log.error('获取代理为空，休息3分钟')
                        time.sleep(180)
                        self.get_proxy()
                        self._refresh_412_proxy()
                        continue
                    self.using_p_dict = p_dict
                    ret_p_dict = p_dict
                    if int(time.time()) - self.check_proxy_time['last_checked_ts'] >= self.check_proxy_time[
                        'checked_ts_sep']:
                        _412_counter = self.sqlite3_proxy_op.get_412_proxy_num()
                        latest_add_ts = self.sqlite3_proxy_op.get_latest_add_ts()  # 最后一次更新的时间
                        proxy_num = self.sqlite3_proxy_op.get_all_proxy_nums()
                        if _412_counter > proxy_num - 10:
                            self.log.warning(
                                f'-412风控代理过多，等待3分钟\t{_412_counter, proxy_num}\t{time.strftime("%Y-%m-%d %H:%M:", time.localtime(time.time()))}')
                            time.sleep(0.05 * 3600)
                            self._refresh_412_proxy()
                            self.get_proxy()  # 如果可用代理数量太少就去获取新的代理
                        if latest_add_ts:
                            if int(time.time() - latest_add_ts) > self.max_get_proxy_sep and latest_add_ts != 0:
                                self.get_proxy()  # 最后一次获取的时间如果是两天前，就再去获取一次代理
                                self._refresh_412_proxy()
                        else:
                            self.get_proxy()  # 最后一次获取的时间如果是两天前，就再去获取一次代理
                            self._refresh_412_proxy()
                        self.check_proxy_time['last_checked_ts'] = int(time.time())
                    # else:
                    #     self.check_proxy_time['last_checked_ts'] = int(time.time())
                    break
                    # if p_dict['score'] <= 0:
                    #     if time.time() - p_dict['update_ts'] > 12 * 3600:
                    #         p_dict['score'] = 50
                    #         p_dict['update_ts'] = int(time.time())
                    #         self._update_proxy_list(p_dict)
                    #         break
                    #     else:
                    #         try:
                    #             self._update_proxy_list(p_dict)
                    #             continue
                    #         except:
                    #             pass
                    # if p_dict['status'] == -412:
                    #     if time.time() - p_dict['update_ts'] > 2 * 3600:
                    #         self.using_p_dict = p_dict
                    #         p_dict['status'] = 0
                    #         p_dict['update_ts'] = int(time.time())
                    #         self._update_proxy_list(p_dict)
                    #         break
                    #     else:
                    #         try:
                    #             self._update_proxy_list(p_dict)
                    #             continue
                    #         except:
                    #             pass
                    # else:
                    #     self.using_p_dict = p_dict
                    #     ret_p_dict = p_dict
                    #     break
                except Exception as e:
                    logger.error(e)
                    continue
            return ret_p_dict

    def _refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        with self.fresh_proxy_lock:
            self.sqlite3_proxy_op.refresh_412_proxy()

    def _remove_proxy_list(self, proxy_dict):
        '''
        移除代理
        :param proxy_dict:
        :return:
        '''
        with self.lock:
            self.sqlite3_proxy_op.remove_proxy(proxy_dict['proxy'])

    def _update_to_proxy_dict(self, proxy_dict: dict, score_plus_Flag=False, score_minus_Flag=False,
                              change_score_num=10):
        '''
        修改所选的proxy，如果不存在则新增在第一个
        :param proxy_dict:
        :return:
        '''
        with self.lock:
            proxy_dict['update_ts'] = int(time.time())
            if proxy_dict['score'] > 100:
                proxy_dict['score'] = 100
                score_plus_Flag = False
            if proxy_dict['score'] < -50:
                proxy_dict['score'] = -50
                score_minus_Flag = False
            self.sqlite3_proxy_op.update_to_proxy_list(proxy_dict, score_plus_Flag, score_minus_Flag, change_score_num)

    def _add_to_proxy_list(self, proxy_dict: dict):
        '''
        增加新的proxy
        :param proxy_dict:
        :return:
        '''
        with self.lock:
            have_flag = False
            if self.sqlite3_proxy_op.is_exist_proxy_by_proxy(proxy_dict['proxy']):
                have_flag = True
            if not have_flag:
                proxy_dict.update({'add_ts': int(time.time())})
                self.log.info(f'新增代理：{proxy_dict}')
                self.sqlite3_proxy_op.add_to_proxy_list(proxy_dict)

    def get_one_rand_grpc_proxy(self):
        while 1:
            ret_proxy = self.sqlite3_proxy_op.get_one_rand_grpc_proxy()
            if not ret_proxy:
                self.get_proxy()
                continue
            return ret_proxy

    def upsert_grpc_proxy_status(self, *args, **kwargs):
        if args:
            kwargs.update(*args)
        if int(time.time()) - self.check_proxy_time['last_checked_ts'] >= self.check_proxy_time[
            'checked_ts_sep']:
            grpc_412_num = self.sqlite3_proxy_op.get_412_proxy_num()
            latest_add_ts = self.sqlite3_proxy_op.get_latest_add_ts()  # 最后一次更新的时间
            proxy_num = self.sqlite3_proxy_op.grpc_get_all_proxy_nums()
            if grpc_412_num > proxy_num * 0.8:
                self.log.warning(
                    f'-412风控代理过多，等待3分钟\t{grpc_412_num, proxy_num}\t{time.strftime("%Y-%m-%d %H:%M:", time.localtime(time.time()))}')
                time.sleep(0.05 * 3600)
                self._grpc_refresh_412_proxy()
                self.get_proxy()  # 如果可用代理数量太少就去获取新的代理
            if latest_add_ts:
                if int(time.time() - latest_add_ts) > self.max_get_proxy_sep and latest_add_ts != 0:
                    self.get_proxy()  # 最后一次获取的时间如果是两天前，就再去获取一次代理
                    self._grpc_refresh_412_proxy()
            else:
                self.get_proxy()  # 最后一次获取的时间如果是两天前，就再去获取一次代理
                self._grpc_refresh_412_proxy()
            self.check_proxy_time['last_checked_ts'] = int(time.time())
        # else:
        #     self.check_proxy_time['last_checked_ts'] = int(time.time())

        self.sqlite3_proxy_op.upsert_grpc_proxy_status(**kwargs)

    def _grpc_refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        with self.fresh_proxy_lock:
            self.sqlite3_proxy_op.grpc_refresh_412_proxy()
