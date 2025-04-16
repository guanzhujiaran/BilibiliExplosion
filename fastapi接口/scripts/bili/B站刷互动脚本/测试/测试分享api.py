# -*- coding:utf- 8 -*-
import copy
import json
import random
import re
import time
import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds
import websocket

cookie1 = gl.get_value('cookie1')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1')
ua1 = gl.get_value('ua1')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
username1 = gl.get_value('uname1')
cookie2 = gl.get_value('cookie2')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
username2 = gl.get_value('uname2')
cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
username3 = gl.get_value('uname3')
cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
username4 = gl.get_value('uname4')
url = 'wss://broadcastlv.chat.bilibili.com:2245/sub'
wss=websocket.WebSocket(url)
data = {
    "uid": 0,
    "roomid": 5440,
    "protover": 1,
    "platform": "web",
    "clientver": "1.4.0"
}
wss.send(bytes(str(data)))
print(wss.recv())

# req=requests.post(url=url,data=data,headers=headers)
# print(req.content.decode('utf-8'))
