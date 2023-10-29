# -*- coding:utf- 8 -*-
import random
import threading
import time
from hashlib import md5
from pprint import pprint
from typing import Union
from urllib.parse import urlencode

import requests
import json
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import bili_live.bili_live_api
import Bilibili_methods.all_methods

liveapi = bili_live.bili_live_api.bili_live_api()
myapi = Bilibili_methods.all_methods.methods()


class Crypto:
    APPKEY = '1d8b6e7d45233436'
    APPSECRET = '560c52ccd288fed045859ed18bffd973'

    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        '''generates md5 hex dump of `str` or `bytes`'''
        if type(data) == str:
            return md5(data.encode()).hexdigest()
        return md5(data).hexdigest()

    @staticmethod
    def sign(data: Union[str, dict]) -> str:
        '''salted sign funtion for `dict`(converts to qs then parse) & `str`'''
        if isinstance(data, dict):
            _str = urlencode(data)
        elif type(data) != str:
            raise TypeError
        return Crypto.md5(_str + Crypto.APPSECRET)


class SingableDict(dict):
    @property
    def sorted(self):
        '''returns an alphabetically sorted version of `self`'''
        return dict(sorted(self.items()))

    @property
    def signed(self):
        '''returns our sorted self with calculated `sign` as a new key-value pair at the end'''
        _sorted = self.sorted
        return {**_sorted, 'sign': Crypto.sign(_sorted)}


class DM:
    def __init__(self):
        self.s = requests.session()

    def send_msg(self, msg: str, room_id, access_key):
        """
        发送弹幕
        """
        url = "https://api-live-bo.biliapi.net/xlive/app-room/v1/dM/sendmsg"
        params = {
            "access_key": access_key,
            "actionKey": "appkey",
            "appkey": Crypto.APPKEY,
            "ts": int(time.time()),
        }
        data = {
            "cid": room_id,
            "msg": msg,
            "rnd": int(time.time()),
            "color": "16777215",
            "fontsize": "25",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 BiliDroid/7.9.0 (bbcallen@gmail.com) os/android model/Mi 10 Pro mobi_app/android build/7090310 channel/xiaomi innerVer/7090310 osVer/12 network/2",
            'env': 'prod',
            'app-key': 'android64',
            'content-type': 'application/x-www-form-urlencoded',
            'accept-encoding': 'gzip',

        }
        req = self.s.post(
            url,
            params=SingableDict(params).signed,
            data=data,
            headers=headers
        )
        print(req.json())
        print(req.headers)
        if req.json().get('message') != '' and req.json().get('message') != '您发送弹幕的频率过快':
            if req.json().get('message') == 'f':
                print(req.json())
                print('弹幕内容被屏蔽')
                t = threading.Thread(target=self.send_msg, args=(msg.strip(), room_id, access_key))
                t.start()
                return
            print(req.json())
            print('发送失败重发')
            t = threading.Thread(target=self.send_msg, args=(msg, room_id, access_key))
            t.start()


#
# def mycls():
#     msg = 、、'我爱小安'
#     sleeptime = 2 # 等待时间
#     rid = 25054665
#     msglist = [msg]
#     kongge = ' '
#     msg_1 = kongge + msg
#     msg_2 = kongge + msg_1
#     msg_3 = kongge + msg_2
#     msg_4 = kongge + msg_3
#     msg_5 = kongge + msg_4
#     msg1 = msg + kongge
#     msg2 = msg1 + kongge
#     msg3 = msg2 + kongge
#     msg4 = msg3 + kongge
#     msg5 = msg4 + kongge
#     # msglist.append(msg)
#     # msglist.append(msg_1)
#     # msglist.append(msg1)
#     # msglist.append(msg2)
#     # msglist.append(msg_2)
#     # msglist.append(msg3)
#     # msglist.append(msg_3)
#     # msglist.append(msg4)
#     # msglist.append(msg_4)
#     # msglist.append(msg5)
#     # msglist.append(msg_5)
#     cls = DM()
#     print(msglist)
#     # BAPI.roomEntryAction(cookie2,ua2,csrf2,rid)
#     # BAPI.roomEntryAction(cookie3, ua3, csrf3, rid)
#     # BAPI.roomEntryAction(cookie4, ua4, csrf4, rid)
#     while True:
#         # 1：星瞳
#         # 2：保加利亚
#         # 3：斯卡蒂
#         # 4：墨色
#         for a in msglist:
#             # cls.send_msg(a,rid,cookie1,csrf1,ua1)#星瞳
#             # time.sleep(sleeptime)
#             cls.send_msg(a, rid, cookie3, csrf3, ua3)  # 斯卡蒂
#             time.sleep(sleeptime)
#             cls.send_msg(a, rid, cookie4, csrf4, ua4)  # 墨色
#             time.sleep(sleeptime)
#             cls.send_msg(str(a), rid, cookie2, csrf2, ua2)  # 保加利亚
#             time.sleep(sleeptime)
#             print('\n')

def mycls(msg: str, sparetime, room_id: int, cheatmode: bool):
    rid = room_id
    msglist = []
    kongge = ' '
    msglist.append(msg)
    sleeptime = sparetime / 3  # 等待时间
    if cheatmode:
        for i in range(1, 11):
            msglist.append(msg + i * kongge)
        for i in range(1, 11):
            msglist.append(i * kongge + msg)
        sleeptime = 1
    cls1 = DM()
    cls2 = DM()
    cls3 = DM()
    print(msglist)
    # BAPI.roomEntryAction(cookie2,ua2,csrf2,rid)
    # BAPI.roomEntryAction(cookie3, ua3, csrf3, rid)
    # BAPI.roomEntryAction(cookie4, ua4, csrf4, rid)

    while True:
        # 1：星瞳
        # 2：保加利亚
        # 3：斯卡蒂
        # 4：墨色
        while 1:
            # cls.send_msg(a,rid,cookie1,csrf1,ua1)#星瞳
            # time.sleep(sleeptime)

            print('斯卡蒂')
            t = threading.Thread(target=cls1.send_msg, args=(random.choice(msglist), rid, a3))
            t.start()  # 斯卡蒂
            time.sleep(sleeptime)

            # print('墨色')
            # cls.send_msg(random.choice(msglist), rid, a4)  # 墨色
            # time.sleep(sleeptime)

            print('保加利亚')
            t = threading.Thread(target=cls2.send_msg, args=(random.choice(msglist), rid, a2))
            t.start()  # 保加利亚
            time.sleep(sleeptime)

            # print('小黑子')
            # t = threading.Thread(target=cls3.send_msg, args=(random.choice(msglist), rid, a5))
            # # t.start()  # 小黑子
            # time.sleep(sleeptime)
            # print('=====================\n')


if __name__ == '__main__':
    a2 = 'd06984f515b9e0d16109ebe2548da491'
    uid2 = '9295261'

    a3 = '1026bc16ef51e9d05f91f3bde391f531'
    uid3 = '1905702375'

    a4 = 'd4d2a01c17ea40e89d3682cecf36dc91'
    uid4 = '1178256718'

    a5 = '691afcd2f97127f4aa21e6adfb786cb2'

    mycls(msg='极致游戏体验',
          sparetime=6,
          # sparetime=0,
          room_id=22119935,
          # 22699050  优酸乳
          # 22237535  华为
          # 4944659   技嘉
          # 24585586  度晓晓
          # 26153015  iQOO官方直播
          # 22119935  英特尔游戏
          # 21430693  知电晓春哥
          cheatmode=False

          )
