import asyncio
import random
import sys
import time
import requests
import base64
from selenium.webdriver.common.by import By
from selenium.webdriver.edge import webdriver, options
from selenium.webdriver.edge.service import Service
from CONFIG import CONFIG
from fastapi接口.log.base_log import ipv6_monitor_logger


class ipv6Obj:
    def __init__(self):
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        self.edge = None

    def init_browser(self):
        if self.edge is None or self.edge.service.process is None:
            opts = options.Options()
            prefs = {
                "profile.default_content_setting_values.notifications": 2  # 2 表示关闭通知
            }
            opts.add_argument("--headless")
            # 添加无痕模式参数
            opts.add_argument('--incognito')
            opts.add_experimental_option("prefs", prefs)
            if sys.platform.startswith('linux'):
                edge_path = CONFIG.selenium_config.linux_edge_path
            else:
                edge_path = CONFIG.selenium_config.edge_path
            self.edge = webdriver.WebDriver(service=Service(edge_path), options=opts)
            self.edge.implicitly_wait(30)

    def _get_register_result(self) -> dict:
        '''
        返回一个sessionid
        :return:
        {
            "sessionid":	"y2niWz78",
            "session_valid":	1,
            "progress_stop":	1,
            "progress_value":	100,
            "is_error":	0,
            "error_type":	-1,
            "stage":	6,
            "services":	"",
            "data_type":	-1,
            "area":	"Shanghai",
            "result":	"1",
            "regmode":	"0"
    }
        '''
        url = 'http://192.168.1.1/cgi-bin/ajax'
        params = {
            'ajaxmethod': 'get_register_result',
            '_': round(random.random(), 16),
            'token': self.ua
        }
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Dnt': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://192.168.1.1',
            'Referer': 'http://192.168.1.1/html/login_CM.html',
            'User-Agent': self.ua,
        }
        req = requests.get(url, headers=headers, params=params)
        return req.json()

    def _get_login_user(self):
        url = 'http://192.168.1.1/cgi-bin/ajax'
        params = {
            'ajaxmethod': 'get_login_user',
            '_': round(random.random(), 16),
            'token': self.ua
        }
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Dnt': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://192.168.1.1',
            'Referer': 'http://192.168.1.1/html/login_CM.html',
            'User-Agent': self.ua,
        }
        req = requests.get(url, params=params, headers=headers)
        return req.json()

    def _ccmc_login(self, username, password, sessionid):
        url = 'http://192.168.1.1/cgi-bin/ajax'
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://192.168.1.1',
            'Referer': 'http://192.168.1.1/html/login_CM.html',
            'User-Agent': self.ua,
        }
        data = {'username': username,
                'password': base64.b64encode(password.encode('utf8')).decode('utf8'),
                'page': 1,
                'sessionid': sessionid,
                'ajaxmethod': 'do_login',
                '_': round(random.random(), 16)
                }
        req = requests.post(url, headers=headers, data=data)
        return req.json()

    def _get_allwan_info(self):
        url = 'http://192.168.1.1/cgi-bin/ajax'
        params = {
            'ajaxmethod': 'get_allwan_info',
            '_': round(random.random(), 16),
            'token': self.ua
        }
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Dnt': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://192.168.1.1',
            'Referer': 'http://192.168.1.1/html/login_CM.html',
            'User-Agent': self.ua,
        }
        req = requests.get(url, params=params, headers=headers)

        return req.json()

    def get_allwan_info(self) -> dict:
        allwan_info = dict()
        while not allwan_info.get('session_valid'):
            allwan_info = self._get_allwan_info()
            # print(f'allwan_info:{allwan_info}')
            if not allwan_info.get('session_valid'):
                register_result = self._get_register_result()
                # print(f'register_result:{register_result}')
                sid = register_result.get('sessionid')
                login_user = self._get_login_user()
                # print(f'login_user:{login_user}')
                ccmc_login = self._ccmc_login('CMCCAdmin', 'CMCCAdminMr1Ua#Ir', sid)
                time.sleep(30)
            else:
                return allwan_info

    async def async_get_allwan_info(self) -> dict:
        allwan_info = dict()
        while not allwan_info.get('session_valid'):
            allwan_info = await asyncio.to_thread(self._get_allwan_info)
            # print(f'allwan_info:{allwan_info}')
            if not allwan_info.get('session_valid'):
                register_result = await asyncio.to_thread(self._get_register_result)
                # print(f'register_result:{register_result}')
                sid = register_result.get('sessionid')
                login_user = await asyncio.to_thread(self._get_login_user)
                # print(f'login_user:{login_user}')
                ccmc_login = await asyncio.to_thread(self._ccmc_login, 'CMCCAdmin', 'CMCCAdminMr1Ua#Ir', sid)
                await asyncio.sleep(30)
            else:
                return allwan_info

    def get_ipv6_prefix(self) -> str:
        '''
        获取光猫的ipv6前缀：2409:8a1e:2a60:3a0::/60
        :return:
        '''
        while 1:
            try:
                allwan_info = self.get_allwan_info()
                return next(filter(lambda x: x.get('IPv6Prefix') != 'NULL', allwan_info.get('wan'))).get('IPv6Prefix')
            except Exception as e:
                ipv6_monitor_logger.exception(e)
                time.sleep(30)

    async def async_get_ipv6_prefix(self) -> str:
        """

        :return: # 2409:8a1e:2a62:69a0::/60
        """
        while 1:
            try:
                allwan_info = await self.async_get_allwan_info()
                return next(filter(lambda x: x.get('IPv6Prefix') != 'NULL', allwan_info.get('wan'))).get('IPv6Prefix')
            except Exception as e:
                ipv6_monitor_logger.exception(e)
                await asyncio.sleep(30)

    async def async_get_ipv6_prefix_selenium(self):
        """

        :return: # 2409:8a1e:2a62:69a0::/60
        """
        while 1:
            try:
                ipv6_prefix = await asyncio.to_thread(self.get_ipv6_prefix_from_selenium)
                return ipv6_prefix
            except Exception as e:
                ipv6_monitor_logger.exception(f'selenium获取ipv6失败！{e}')
                if self.edge:
                    self.edge.get('about:blank')

    def get_ipv6_prefix_from_selenium(self):
        def login():
            driver.get('http://192.168.1.1/')
            driver.find_element(By.CLASS_NAME, 'username').send_keys('user')
            driver.find_element(By.CLASS_NAME, 'password').send_keys('tAP9d#e3')
            driver.find_element(By.CLASS_NAME, 'login').click()

        def get_ipv6_prefix():
            driver.switch_to.frame('mainFrame')
            if not is_logined:
                driver.find_element(By.ID, 'smWanStatu').click()
                driver.implicitly_wait(2)
                driver.find_element(By.ID, 'ssmIPv6WANSta').click()
                driver.implicitly_wait(2)
            Tbl_WANstauts1 = driver.find_element(By.ID, 'Tbl_WANstauts1')
            Tbl_WANstauts1_text = Tbl_WANstauts1.text
            driver.switch_to.default_content()
            return Tbl_WANstauts1_text.split('\n')[9].replace("前缀 ", "")

        self.init_browser()
        self.edge.refresh()
        driver = self.edge
        is_logined = False
        if driver.current_url != 'http://192.168.1.1/' and driver.current_url != 'http://192.168.1.1/start.ghtml':
            login()
        else:
            is_logined = True
        ipv6_prefix = get_ipv6_prefix()
        return ipv6_prefix


if __name__ == '__main__':
    myapp = ipv6Obj()
    while 1:
        print(asyncio.run(myapp.async_get_ipv6_prefix_selenium()))
        time.sleep(10)
