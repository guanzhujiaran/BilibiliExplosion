# -*- coding:utf- 8 -*-
import json
import random
import re
import threading
import time
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
import numpy
import requests

import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods

BAPI = Bilibili_methods.all_methods.methods()
cookie1 = gl.get_value('cookie1')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1')
ua1 = gl.get_value('ua1')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
device_id1 = gl.get_value('device_id1')
cookie2 = gl.get_value('cookie2')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
device_id2 = gl.get_value('device_id2')
cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
device_id3 = gl.get_value('device_id3')
cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
device_id4 = gl.get_value('device_id4')
import random
import re
import time


class zhuanpanlottery:
    def get_task_list(self, _eventId, cookie, ua):
        url = 'https://mall.bilibili.com/mall-dayu/ticket-activity/activity/v2/taskset/get?id={}&_={}'.format(_eventId,
                                                                                                              int(time.time()))
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': cookie,
            'referer': 'https://mall.bilibili.com/act/aicms/CI5nEXX997.html?from=mall_home_tab&msource=mall_6954_banner&outsideMall=no',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        print(req.json())
        return req.json()

    def dispatch(self, _taskId,cookie,ua):
        url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
        data = {'taskId': _taskId}
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'Content-type':'application/json',
            'cookie': cookie,
            'referer': 'https://mall.bilibili.com/act/aicms/CI5nEXX997.html?from=mall_home_tab&msource=mall_6954_banner&outsideMall=no',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua
        }
        req=requests.post(url=url,headers=headers,data=data)
        print(req.text)
        return req.json()

    #def do(self):


if __name__ == '__main__':
    a = zhuanpanlottery()
    eventId = 'kxg01zpr9o'
    #a.get_task_list(eventId,cookie3,ua3)
    a.dispatch(1864,cookie3,ua3)