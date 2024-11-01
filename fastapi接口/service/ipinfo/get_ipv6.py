import asyncio
import base64
import random
import time

import requests
from langchain_community.utilities.pebblo import get_ip
from loguru import logger

from fastapi接口.dao.IpInfoRedisObj import ip_info_redis

class ipv6Obj:
    def __init__(self):
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'

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
                logger.exception(e)
                time.sleep(30)


ipv6_obj = ipv6Obj()


async def get_ipv6()->str:
    if ipv6 := await ip_info_redis.get_ip_addr():
        return ipv6
    else:
        ipv6 = await asyncio.get_event_loop().run_in_executor(
            None,
            ipv6_obj.get_ipv6_prefix)
        await set_ipv6(ipv6)
        return ipv6

async def set_ipv6(ip_addr):
    await ip_info_redis.set_ip_addr(ip_addr)

if __name__ == "__main__":
    result = asyncio.run(get_ipv6())
    print(result)
