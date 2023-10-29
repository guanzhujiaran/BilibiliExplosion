# -*- coding: utf-8 -*-
import atexit
import copy
import os
import traceback

from functools import reduce

import threading

import random

import time

import queue

import bs4
from loguru import logger
import requests
from requests import session
from selenium import webdriver
from CONFIG import CONFIG


class request_with_proxy:
    def Get_Bili_Cookie(self) -> str:
        url = 'https://t.bilibili.com/'
        opt = webdriver.ChromeOptions()
        # opt.binary_location = "C:/Python39/chromedriver.exe"
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
        self.log = logger.bind(user=__name__)
        self.get_proxy_sep_time = 2 * 3600
        self.get_proxy_timestamp = 0
        self.get_proxy_lock = threading.Lock()
        self.get_proxy_page = 7  # 获取代理网站的页数
        self.write_proxy_lock = threading.Lock()
        self.fresh_proxy_lock = threading.Lock()
        self.__dir_path = CONFIG.root_dir + 'utl/代理/'
        self.check_proxy_flag = False  # 是否检查ip可用，因为没有稳定的代理了，所以默认不去检查代理是否有效
        self.fresh_cookie_lock = threading.Lock()
        self._352_time = 0
        self.lock = threading.Lock()
        self.set_proxy_lock = threading.Lock()
        self.timeout = 10
        self.mode = 'single'  # single || rand
        self.proxy_apikey = ''
        self.proxy_list = []  # 代理列表
        if os.path.exists(self.__dir_path + '代理api_key.txt'):
            with open(self.__dir_path + '代理api_key.txt', 'r', encoding='utf-8') as f:
                self.proxy_apikey = f.read().strip()
        self.recorded_proxy = []
        if os.path.exists(self.__dir_path + 'recorded_proxy.txt'):
            with open(self.__dir_path + 'recorded_proxy.txt', 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    i_strip = i.strip()
                    if i_strip:
                        try:
                            self.recorded_proxy.append(eval(i_strip))
                        except:
                            print(i_strip)
            self.proxy_list = copy.deepcopy(self.recorded_proxy)
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
        atexit.register(self.write_proxy_list_into_file)

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def request_with_proxy(self, *args, **kwargs) -> dict:
        '''
        通过代理请求json格式的resp
        :param args:
        :param kwargs:
        :return:
        '''
        while True:
            if kwargs.get('headers').get('user-agent'):
                if kwargs.get('headers').get('user-agent') in self.ban_ua_list:
                    if self.User_Agent_List:
                        kwargs.get('headers').update({
                            'user-agent': random.choice(self.User_Agent_List)
                        })
            with self.fresh_cookie_lock:
                if self.fake_cookie:
                    kwargs.get('headers').update({'cookie': self.fake_cookie})

            p_dict = self._set_new_proxy()
            p = p_dict.get('proxy')
            status = 0
            if not p:
                time.sleep(10)
                return self.request_with_proxy(*args, **kwargs)

            try:
                req = self.s.request(*args, **kwargs, proxies=p, timeout=self.timeout)
                if 'code' not in req.text:  # 如果返回的不是json那么就打印出来看看是什么
                    print(req.text)
                req_dict = req.json()
                if req_dict.get('code') == -412 or req_dict.get('code') == -352:
                    print(
                        f'{req_dict.get("code")}报错,换个ip\t{p}\t{self._timeshift(time.time())}\t{req_dict}\n{args}\t{kwargs}')
                    if req_dict.get('code') == -412:
                        status = -412
                        self._check_ip_by_bili_zone(p, status=status, score=p_dict)  # 如何代理ip检测没问题就追加回去
                    else:
                        with self.fresh_cookie_lock:
                            self._352_time += 1
                            if self._352_time >= 10:
                                self.fake_cookie = self.Get_Bili_Cookie()
                                self._352_time = 0
                    p_dict['score'] += 10
                    self._update_proxy_list(p_dict)
                    return self.request_with_proxy(*args, **kwargs)
            except Exception as e:
                # if p not in self.ban_proxy_pool:
                #     self.ban_proxy_pool.append(p)
                # try:
                #     self._remove_proxy_list(p_dict['proxy'])
                # except:
                #     pass
                p_dict['score'] -= 10
                p_dict['status'] = -412
                self._update_proxy_list(p_dict)
                self._set_new_proxy()
                print(
                    f'使用代理访问失败，代理扣分。{e}\t{args, kwargs.get("url")}\n获取请求时使用的代理信息：{p_dict}\t{self._timeshift(time.time())}\t剩余{len(self.proxy_list)}个代理，当前禁用代理{len(self.ban_proxy_pool)}个：')
                if len(self.ban_proxy_pool) > 30:
                    self.ban_proxy_pool.clear()
                # return self.request_with_proxy(*args, **kwargs)
                continue
            p_dict['score'] += 10
            p_dict['status'] = status
            self._update_proxy_list(p_dict)
            return req_dict

    def set_GetProxy_Flag(self, boolean: bool):
        self.GetProxy_Flag = boolean

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
            print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
            have_proxy = [x['proxy'] for x in self.proxy_list]

            for i in proxies:
                if i:
                    append_dict = {
                        'http': 'http' + '://' + i,
                        'https': 'http' + '://' + i
                    }
                    if append_dict not in have_proxy:
                        proxy_queue.append(append_dict)
            print(f'总共有{len(proxy_queue)}个代理需要检查')
            if len(proxy_queue) < 100:
                print(req, url)
        else:
            Get_proxy_success = False
        if len(proxy_queue) < 100:
            print(req, url)
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
                req = self.s.get(url=url, verify=False, headers=headers)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                print(url)
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

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
                req = self.request_with_proxy(method='get', url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                print(url)
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

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
                req = self.s.get(url=url, verify=False, headers=headers)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                print(url)
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)
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
                req = self.s.get(url=url, verify=False, headers=headers)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
                traceback.print_exc()
                print(url)
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)
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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)
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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)
                print(req.text)
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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

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
                req = self.s.get(url=url, headers=headers, verify=False)
            except:
                # print(f'获取代理 {url} 报错\t{self._timeshift(time.time())}')
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
                    print(req, url)
                print(f'总共有{len(proxy_queue)}个代理需要检查')
            else:
                print(req, url)

                Get_proxy_success = False
            time.sleep(3)
        return proxy_queue, Get_proxy_success

    def get_proxy(self):
        time.sleep(1)
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
            _, Get_proxy_success = self.get_proxy_from_zdayip()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_kuaidaili()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_66daili()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_89daili()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_taiyangdaili()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_kxdaili_1()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_kxdaili_2()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_ip3366_1()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_ip3366_2()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_qiyun()
            proxy_queue.extend(_)
            _, Get_proxy_success = self.get_proxy_from_ihuan()
            proxy_queue.extend(_)
            print(f'最终共有{len(proxy_queue)}个代理需要检查')

            threads = []
            for i in range(len(proxy_queue)):
                thread = threading.Thread(target=self._check_ip_by_bili_zone, args=(proxy_queue.pop(),))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()

            self.proxy_list = self._remove_list_dict_duplicate(self.proxy_list)  # 去重并保持顺序不变
            self.recorded_proxy = copy.deepcopy(self.proxy_list)
            self.write_proxy_list_into_file()
            print(f'总共还有{len(self.proxy_list)}个有效代理')
            Get_proxy_success = True
            t = threading.Timer(30, self.set_GetProxy_Flag, (False,))  # 获取结束之后等待30秒，之后设为False，允许开始下一轮获取代理
            t.start()

        if Get_proxy_success:
            return
        else:
            return self.get_proxy()

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
        if self.check_proxy_flag:
            try:
                _url = 'http://api.bilibili.com/x/web-interface/zone'
                _req = self.s.get(url=_url, proxies=proxy, timeout=self.timeout)
                if _req.json().get('code') == 0:
                    # print(f'代理检测成功，添加回代理列表：{_req.json()}')
                    self._add_proxy_list(self._proxy_warrper(proxy, status, score))
                    return True
                else:
                    # print(f'代理失效：{_req.text}')
                    return False
            except Exception as e:
                # print(f'代理检测失败：{proxy}')
                return False
        else:
            self._update_proxy_list(self._proxy_warrper(proxy, status, score))
            return True

    def _proxy_warrper(self, proxy, status=0, score=50):
        return {"proxy": proxy, "status": status, "update_ts": int(time.time()), 'score': score}

    def _set_new_proxy(self, old_p_dict=None):
        with self.set_proxy_lock:
            while not self.proxy_list:
                self.get_proxy()  # 如果代理列表用完了就去获取新的代理
                time.sleep(10)

            while 1:
                if self.mode == 'single':
                    p_dict = self.proxy_list[-1]
                else:
                    p_dict = random.choice(self.proxy_list)
                if old_p_dict != p_dict and old_p_dict is not None:
                    # 如果不相等，那么self.using_p是最新的
                    return old_p_dict
                self.using_p_dict = p_dict
                ret_p_dict = p_dict
                _412_counter = 0
                latest_update_ts = 0
                for _ in self.proxy_list:
                    if _['status'] == -412:
                        _412_counter += 1
                    if _['update_ts'] > latest_update_ts:
                        latest_update_ts = _['update_ts']
                if _412_counter > len(self.proxy_list) - 10:
                    self.log.warning(
                        f'-412风控代理过多，等待3分钟\t{_412_counter, len(self.proxy_list)}\t{time.strftime("%Y-%m-%d %H:%M:", time.localtime(time.time()))}')
                    time.sleep(0.05 * 3600)
                    self._refresh_412_proxy()
                    self.get_proxy()  # 如果可用代理数量太少就去获取新的代理
                if int(time.time() - latest_update_ts) > 2 * 24 * 3600 and latest_update_ts != 0:
                    self.get_proxy()  # 最后一次获取的时间如果是两天前，就再去获取一次代理
                if p_dict['score'] <= 0:
                    if time.time() - p_dict['update_ts'] > 12 * 3600:
                        p_dict['score'] = 50
                        self._update_proxy_list(p_dict)
                        break
                    else:
                        try:
                            self._remove_proxy_list(p_dict)  # 移除后添加回队首
                            self._update_proxy_list(p_dict)
                            continue
                        except:
                            pass
                if p_dict['status'] == -412:
                    if time.time() - p_dict['update_ts'] > 2 * 3600:
                        self.using_p_dict = p_dict
                        p_dict['status'] = 0
                        p_dict['update_ts'] = int(time.time())
                        self._update_proxy_list(p_dict)
                        break
                    else:
                        try:
                            self._remove_proxy_list(p_dict)  # 移除后添加回队首
                            self._update_proxy_list(p_dict)
                            continue
                        except:
                            pass
                else:
                    self.using_p_dict = p_dict
                    ret_p_dict = p_dict
                    break
            return ret_p_dict

    def _refresh_412_proxy(self):
        '''
        刷新两个小时前的412代理状态
        :return:
        '''
        with self.fresh_proxy_lock:
            self.proxy_list = sorted(self.proxy_list, key=lambda x: x['update_ts'])  # 按更新时间从小到大排序
            new_list = list()
            for p_dict in self.proxy_list:
                # if p_dict['score'] <= 0:
                #     continue
                if time.time() - p_dict['update_ts'] >= 2 * 3600:
                    new_list.append(self._proxy_warrper(p_dict['proxy'], status=0, score=p_dict['score']))
                else:
                    new_list.append(p_dict)
            new_list = sorted(new_list, key=lambda x: x['update_ts'])  # 按更新时间从小到大排序
            self.proxy_list = new_list

    def _remove_proxy_list(self, proxy_dict):
        '''
        移除所选的proxy
        :param proxy:
        :return:
        '''
        with self.lock:
            new_li = list()
            for p_dict in self.proxy_list:
                if p_dict['proxy'] != proxy_dict['proxy']:
                    new_li.append(p_dict)
            self.proxy_list = new_li

    def _update_proxy_list(self, proxy_dict: dict):
        '''
        修改所选的proxy，如果不存在则新增在第一个
        :param proxy_dict:
        :return:
        '''
        with self.lock:
            have_flag = False
            for p_dict in self.proxy_list:
                if p_dict['proxy'] == proxy_dict['proxy']:
                    self.proxy_list[self.proxy_list.index(p_dict)] = proxy_dict
                    have_flag = True
        if not have_flag:
            self._add_proxy_list(proxy_dict)

    def _add_proxy_list(self, proxy_dict: dict):
        '''
        增加新的proxy
        :param proxy_dict:
        :return:
        '''
        with self.lock:
            have_flag = False
            for _ in self.proxy_list:
                if _['proxy'] == proxy_dict['proxy']:
                    have_flag = True
                    break
            if not have_flag:
                self.proxy_list.insert(0, proxy_dict)

    def write_proxy_list_into_file(self):
        if self.proxy_list:
            with self.write_proxy_lock:
                with open(self.__dir_path + 'recorded_proxy.txt', 'w', encoding='utf-8') as f:
                    for p in self.recorded_proxy:
                        f.writelines(f'{p}\n')
