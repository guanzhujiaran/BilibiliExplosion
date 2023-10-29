# -*- coding:utf- 8 -*-
import json
import random
import re
import sys
import threading
import time
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
from pprint import pprint

import numpy
import requests

import b站cookie.b站cookie_
import b站cookie.globalvar as gl

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
sleeptime = numpy.linspace(5, 7, 500, endpoint=False)


class fast_lottery:
    def fetchLotteryUserInfo(self, activityId, cookie, ua):
        url = f'https://mall.bilibili.com/activity/lottery/fetchLotteryUserInfo?_={int(time.time() * 1000)}&activityId={activityId}'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        return req.json().get('data').get('score')

    def draw_lottery(self, cookie, ua, activityid):
        while 1:
            url = 'https://mall.bilibili.com/activity/lottery/drawLottery'
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua}
            data = {"activityId": activityid
                , "bizInfo": {}}
            data = json.dumps(data)
            req = requests.post(url=url, headers=headers, data=data)
            time.sleep(2)
            try:
                req_dict = json.loads(req.text)
                prizelist = req_dict.get('data').get('prizeInfoDTOList')
                recordid = prizelist[0].get('recordId')
                prizename = prizelist[0].get('prizeName')
                print('奖品名称：{}'.format(prizename))
                # url = 'https://mall.bilibili.com/mall-dayu/mall-marketing-core/lottery_prize/draw_subsidy'
                # data = {"recordId": recordid}
                # data = json.dumps(data)
                # req = requests.post(url=url, data=data, headers=headers)
                # print(req.text)
                if req.json().get('code') != 0:
                    break
            except Exception as e:
                print('抽奖失败')
                print(req.text)
                break


if __name__ == '__main__':
    time_now = time.strftime("%H:%M:%S", time.localtime())
    print(time_now)
    t_list=[]
    while 1:
        time_now = time.strftime("%H:%M:%S", time.localtime())
        if time_now == '00:00:00':
            s = fast_lottery()
            for e in range(2, 5):
                eval('t_list.append(threading.Thread(target=s.draw_lottery,args=(cookie{n},ua{n},2022092032061002)))'.format(
                    n=e))

            for __t in t_list:
                __t.start()
            for __t in t_list:
                __t.join()
            break

