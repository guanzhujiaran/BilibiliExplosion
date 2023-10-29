# -*- coding:utf- 8 -*-
import random
import threading
import time
from pprint import pprint

import numpy
import requests
import json
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import bili_live.bili_live_api

BAPI = bili_live.bili_live_api.bili_live_api()
cookie1 = gl.get_value('cookie1')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1')
ua1 = gl.get_value('ua1')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
cookie2 = gl.get_value('cookie2')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')


cookie5 = gl.get_value('cookie5')
fullcookie5 = gl.get_value('fullcookie5')
ua5 = gl.get_value('ua5')
fingerprint5 = gl.get_value('fingerprint5')
csrf5 = gl.get_value('csrf5')
uid5 = gl.get_value('uid5')

cookie6 = gl.get_value('cookie6')
fullcookie6 = gl.get_value('fullcookie6')
ua6 = gl.get_value('ua6')
fingerprint6 = gl.get_value('fingerprint6')
csrf6 = gl.get_value('csrf6')
uid6 = gl.get_value('uid6')

class DM:
    def __init__(self):
        self.s = requests.session()

    def send_msg(self, msg4, rid, cookie, csrf, ua):
        url = 'https://api.live.bilibili.com/msg/send'
        data = {
            'bubble': '0',
            'msg': msg4,
            'color': '16777215',
            'mode': '1 ',
            'rnd': int(time.time()),
            'fontsize': '25',
            'roomid': rid,
            'csrf': csrf,
            'csrf_token': csrf
        }
        headers = {
            "cookie": cookie,
            "user-agent": ua,
            'origin': 'https://live.bilibili.com',
            'referer': 'https://live.bilibili.com/{}?broadcast_type=0&is_room_feed=1&spm_id_from=333.999.0.0'.format(
                rid),

        }
        try:
            response = self.s.request("POST", url, headers=headers, data=data, timeout=1)
            response_dict = json.loads(response.text)
            print(response_dict)
        except Exception as e:
            print(e)
            return
        if response.json().get('message') != '' and response.json().get('message') != '您发送弹幕的频率过快':
            if response.json().get('message') == 'f':
                pprint(data)
            print('发送失败重发\t只重发一次')
            t = threading.Thread(target=self.send_msg, args=(msg4, rid, cookie, csrf, ua))
            t.start()
        if response.json().get('code') == -1:
            exit(response.json().get('message'))


def mycls():
    msg = 'ROG7 超神进化'
    sleeptime = numpy.linspace(0.2, 1, 500)  # 等待时间
    rid = 25349102
    #iqoo
    # rid =22119935 #英特尔游戏
    # rid = 1528395  # 雷神
    # rid = 5055636#会员购
    # rid = 25523906#一加
    # rid=23975776#小米w
    # rid = 25981995  # 康师傅
    # rid =22699050#优酸乳
    # rid =1017 #逍遥散人
    # rid=  3990262 #荣耀
    # #房间号
    msglist = [msg]
    kongge = ' '
    msg_1 = kongge + msg
    msg_2 = kongge + msg_1
    msg_3 = kongge + msg_2
    msg_4 = kongge + msg_3
    msg_5 = kongge + msg_4
    msg1 = msg + kongge
    msg2 = msg1 + kongge
    msg3 = msg2 + kongge
    msg4 = msg3 + kongge
    msg5 = msg4 + kongge


    msglist.append(msg1)
    msglist.append(msg2)
    msglist.append(msg3)
    msglist.append(msg4)
    msglist.append(msg5)
    # msglist.append(msg6)
    # msglist.append(msg7)
    # msglist.append(msg8)
    # msglist.append(msg9)

    msglist.append(msg_1)
    msglist.append(msg_2)
    msglist.append(msg_3)
    msglist.append(msg_4)
    msglist.append(msg_5)
    cls = DM()
    print(msglist)
    # BAPI.roomEntryAction(cookie2,ua2,csrf2,rid)
    # BAPI.roomEntryAction(cookie3, ua3, csrf3, rid)
    # BAPI.roomEntryAction(cookie4, ua4, csrf4, rid)
    while True:
        # 1：星瞳
        # 2：保加利亚
        # 3：斯卡蒂
        # 4：墨色
        for a in msglist:
            # cls.send_msg(a,rid,cookie1,csrf1,ua1)#星瞳
            # time.sleep(sleeptime)
            print('斯卡蒂')
            threading.Thread(target=cls.send_msg, args=(a, rid, cookie3, csrf3, ua3)).start()  # 斯卡蒂
            time.sleep(random.choice(sleeptime))

            # print('墨色')
            # threading.Thread(target=cls.send_msg,args=(a, rid, cookie4, csrf4, ua4)).start()  # 墨色
            # time.sleep(random.choice(sleeptime))

            print('保加利亚')
            threading.Thread(target=cls.send_msg, args=(a, rid, cookie2, csrf2, ua2)).start()  # 保加利亚
            time.sleep(random.choice(sleeptime))
            print('\n')

            print('5')
            threading.Thread(target=cls.send_msg, args=(a, rid, cookie5, csrf5, ua5)).start()  # 保加利亚
            time.sleep(random.choice(sleeptime))
            print('\n')

            print('6')
            threading.Thread(target=cls.send_msg, args=(a, rid, cookie6, csrf6, ua6)).start()  # 保加利亚
            time.sleep(random.choice(sleeptime))
            print('\n')

if __name__ == '__main__':
    mycls()
