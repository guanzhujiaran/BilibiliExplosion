# -*- coding:utf- 8 -*-
import os

import json
import random
import re
import sys
import threading
import time
import urllib.parse
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
import numpy
import requests
import logging
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods
from CONFIG import CONFIG

logging.basicConfig(filename='抢魔晶.log', level=logging.DEBUG)

BAPI = Bilibili_methods.all_methods.methods()

cookie_file_name_list = os.listdir(CONFIG.root_dir+'b站cookie/cookie_path')
for i in range(1, len(cookie_file_name_list) + 1):
    exec(f"cookie{i} = gl.get_value('cookie{i}')")
    exec(f"fullcookie{i} = gl.get_value('fullcookie{i}')")
    exec(f"ua{i} = gl.get_value('ua{i}')")
    exec(f"fingerprint{i} = gl.get_value('fingerprint{i}')")
    exec(f"csrf{i} = gl.get_value('csrf{i}')")
    exec(f"watch_cookie{i} = gl.get_value('watch_cookie{i}')")
    exec(f"device_id{i} = gl.get_value('device_id{i}')")
    exec(f"buvid3_{i} = gl.get_value('buvid3_{i}')")


# cookie1 = gl.get_value('cookie1')  # 星瞳
# fullcookie1 = gl.get_value('fullcookie1')
# ua1 = gl.get_value('ua1')
# fingerprint1 = gl.get_value('fingerprint1')
# csrf1 = gl.get_value('csrf1')
# uid1 = gl.get_value('uid1')
# device_id1 = gl.get_value('device_id1')
# buvid3_1 = gl.get_value('buvid3_1')
# cookie2 = gl.get_value('cookie2')  # 保加利亚
# fullcookie2 = gl.get_value('fullcookie2')
# ua2 = gl.get_value('ua2')
# fingerprint2 = gl.get_value('fingerprint2')
# csrf2 = gl.get_value('csrf2')
# uid2 = gl.get_value('uid2')
# device_id2 = gl.get_value('device_id2')
# buvid3_2 = gl.get_value('buvid3_2')
#
# cookie3 = gl.get_value('cookie3')  # 斯卡蒂
# fullcookie3 = gl.get_value('fullcookie3')
# ua3 = gl.get_value('ua3')
# fingerprint3 = gl.get_value('fingerprint3')
# csrf3 = gl.get_value('csrf3')
# uid3 = gl.get_value('uid3')
# device_id3 = gl.get_value('device_id3')
# buvid3_3 = gl.get_value('buvid3_3')
#
# cookie4 = gl.get_value('cookie4')  # 墨色
# fullcookie4 = gl.get_value('fullcookie4')
# ua4 = gl.get_value('ua4')
# fingerprint4 = gl.get_value('fingerprint4')
# csrf4 = gl.get_value('csrf4')
# uid4 = gl.get_value('uid4')
# device_id4 = gl.get_value('device_id4')
# buvid3_4 = gl.get_value('buvid3_4')


def coupon_receive_monitor(uid, buvid, elementid, source_authority_id, cookie, ua):
    url = 'https://mall.bilibili.com/mall-dayu/h5/monitor'
    data = {"event": "lens.track",
            "time": int(time.time() * 1000),
            "mid": uid,
            "platform": 3,
            "buvid": buvid,
            "appV": "0",
            "ua": ua.replace('/', '%2F').replace(' ', '%20'),
            "isbili": 0,
            "url": "https://mall.bilibili.com/act/aicms/Rf5qQsiHYa.html",
            "referer": "https://mall.bilibili.com/act/aicms/Rf5qQsiHYa.html",
            "bid": "[_lensAppId]",
            "lensV": "0.2.6",
            "ext": {"category": "mall.cms.mojing-couponsv2.0.click",
                    "msg": json.dumps({"pageid": 5180,
                                       "elementid": elementid,
                                       "source_authority_id": source_authority_id,
                                       "msource": "mall_8384_banner"}),
                    "stage": "UNSET"}}
    data = json.dumps(data)
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        "Content-Type": "application/json",
        'cookie': cookie,
        'origin': 'https://mall.bilibili.com',
        'referer': 'https://mall.bilibili.com/act/aicms/YJtBDKVtfO.html?from=cms_919dbdh&msource=mall_8384_banner',
        'sec-ch-ua': '\".Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"103\", \"Chromium\";v=\"103\"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '\"Windows\"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ua,
    }
    req = requests.post(url=url, data=data, headers=headers)
    logging.info(f'monitor:{req.text}')


def coupon_receive_log_reporter(cookie, ua, elementid, source_authority_id):
    __time = int(time.time() * 1000)
    url = f"https://data.bilibili.com/log/web?000041{__time}{__time}|mall.cms.mojing-couponsv2.0.click|" + json.dumps(
        {"pageid": 5180,
         "elementid": elementid,
         "source_authority_id": source_authority_id,
         "msource": "mall_8384_banner",
         "from": "cms_919dbdh"}
    ).replace('"', '%22').replace(' ', '') + '|'
    headers = {
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': cookie,
        'referer': 'https://mall.bilibili.com/',
        'sec-ch-ua': '\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '\"Windows\"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-site',
        'user-agent': ua
    }
    req = requests.get(url=url, headers=headers)
    logging.info(f'repoter:{req.text}')


class ThRobber:
    def __init__(self):
        self.btimes = 0
        self.breakFlag = False

    def receive_coupon(self, _sourceAuthorityId, _cookie, _ua, _uid, _buvid3, _device_id, elementid, sourceActivityId,
                       sourceId):
        nowtime = requests.get('https://api.bilibili.com/x/click-interface/click/now').json().get('data').get('now')
        url = "https://mall.bilibili.com/mall-c/coupon/receivecoupon"
        # params = {
        #     'buvid': _buvid3,
        #     'platform': 'h5',
        #     'uid': _uid,
        #     'channel': 1
        # }
        data = {
            'deviceId': _device_id,
            'deviceInfo': {'build': 0, 'info': "web", 'platform': "h5",
                           'ua': _ua},
            'fromPage': 3,
            'needDeviceCheck': False,
            'sourceActivityId': sourceActivityId,  # 同时也要改变ActivityId
            'sourceAuthorityId': _sourceAuthorityId,
            'sourceBizId': int(time.time() * 1000),
            'sourceId': sourceId,  # 每个不同的sourceid 和sourceActivityId 对应不同活动的coupon
        }
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            "Content-Type": "application/json",
            'cookie': _cookie,
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/act/aicms/3iMV07H0At.html?from=cms_dbdh&msource=brand_spread_main_activity',
            'sec-ch-ua': '\".Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"103\", \"Chromium\";v=\"103\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': _ua,
            'x-risk-header': 'platform/h5 uid/{} channel/1 deviceId/{}'.format(
                _uid, _buvid3),
        }
        if self.breakFlag:
            return
        req = requests.post(url=url, data=json.dumps(data), headers=headers)
        logging.info(f'{_uid}:{req.text}')
        print(f'{_uid}:{req.text} {_sourceAuthorityId, sourceActivityId, sourceId} {nowtime}')
        res = req.json()
        # logging.info('尝试领取')
        if res.get('code') == 83094004:
            logging.info(f'{_uid}：领取成功 {nowtime}')
            print(f'{_uid}：领取成功 {nowtime}')
            threading.Thread(target=coupon_receive_log_reporter,
                             args=(_cookie, _ua, elementid, _sourceAuthorityId)).start()
            threading.Thread(target=coupon_receive_monitor,
                             args=(
                                 _uid, _buvid3, elementid, _sourceAuthorityId, _cookie,
                                 _ua)).start()  # 领取成功后进行log上报
            self.breakFlag = True
        if res.get('code') == 831103147:
            logging.info(f'{_uid} {res.get("message")} {nowtime}')  # 忘记是啥了，可能是已经领取
            print(f'{_uid} {res.get("message")} {nowtime}')
            self.breakFlag = True
        elif res.get('code') == 831103148:
            logging.info(f'{_uid}：领完了，没领到 {nowtime}')
            print(f'{_uid}：领完了，没领到 {nowtime}')
            self.breakFlag = True
        elif res.get('code') == 831103145:  # 魔晶未到领取开始时间
            logging.info(f'{_uid}, {res}, {nowtime}')
            print(f'{_uid}, {res}, {nowtime}')
            return
        elif res.get('code') == 83110034:
            # 操作太频繁
            logging.info(f'{_uid}, {res}, {nowtime}')
            print(f'{_uid}, {res}, {nowtime}')
            return
        else:
            logging.info(f'{_uid}：未知代码 {res} {nowtime}')
            print(f'{_uid}：未知代码 {res} {nowtime}')
            self.btimes += 1
        return res

    def robber_coupon(self, start_time, _sourceAuthorityId, _cookie, _ua, _uid, _buvid3, _device_id, elementid,
                      sourceActivityId, sourceId):
        while 1:
            nowtime = time.time()
            t = threading.Thread(target=self.receive_coupon,
                                 args=(_sourceAuthorityId, _cookie, _ua, _uid, _buvid3, _device_id, elementid,
                                       sourceActivityId, sourceId))
            if self.btimes > 5:
                logging.info(f'{_uid}超过重试最大次数，退出 {time.time()}')
                print(f'{_uid}超过重试最大次数，退出 {time.time()}')
                break
            if int(nowtime-0.5) >= start_time:
                try:
                    t.start()
                except:
                    time.sleep(0.5)
                    continue
                time.sleep(0.01)
                if self.breakFlag:
                    break
            if int(nowtime) >= start_time + 5:
                logging.info(f'{_uid}：超时太多退出')
                print(f'{_uid}：超时太多退出')
                break
            time.sleep(1e-10)


def thread_receive_coupon(_cookie_list, _ua_list, _buvid3_list, _device_id_list):
    def login_check(_cookie, _ua):
        headers = {
            'User-Agent': _ua,
            'cookie': _cookie,
            'Connection': 'close'
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        res = requests.get(url=url, headers=headers).json()
        if res['data']['isLogin'] == True:
            name = res['data']['uname']
            uid = res['data']['mid']
            print(f'登录成功,当前账号用户名为{name}\tuid：{uid}')
            return {'name': name, 'uid': uid}
        else:
            print('登陆失败,请重新登录')
            exit('登陆失败,请重新登录')

    _uid_list = []
    for _i in range(len(_cookie_list)):
        cookie = _cookie_list[_i]
        ua = _ua_list[_i]
        buvid3 = _buvid3_list[_i]
        _uid_list.append(login_check(cookie, ua)['uid'])
    # 使用前修改sourceId的值
    sourceAuthorityIdlist = [
        'd17f00fd9563e524834e'  # 1.28
    ]  # 每天更新 https://mall.bilibili.com/act/aicms/Rf5qQsiHYa.html
    element_id_list = [
        'MYkCpdVFNx9U',  # 1.28
    ]
    start_time_list = [
        1674835200  # 1.28
    ]
    sourceActivityId = 6319  # 每次都要改变
    sourceId = "s_5ad18f9ababe2f460f91"  # 每次都要改变
    start_time = start_time_list[0]

    thread_list = []
    for _class_number in range(len(_cookie_list)):
        exec(f'rob{_class_number}=ThRobber()')

    _t_dict = {}
    for _i in range(len(_cookie_list)):
        exec(
            f'_t = threading.Thread(target=rob{_i}.robber_coupon, args=(start_time, sourceAuthorityIdlist[0], _cookie_list[_i], _ua_list[_i], _uid_list[_i], _buvid3_list[_i],_device_id_list[_i], element_id_list[0],sourceActivityId,sourceId))',
            {'threading': threading, f'rob{_i}': eval(f'rob{_i}'), 'start_time': start_time,
             'sourceAuthorityIdlist': sourceAuthorityIdlist, '_cookie_list': _cookie_list, '_ua_list': _ua_list,
             '_uid_list': _uid_list, '_buvid3_list': _buvid3_list, '_device_id_list': _device_id_list,
             'element_id_list': element_id_list, '_i': _i, "sourceActivityId": sourceActivityId, "sourceId": sourceId},
            _t_dict)
        thread_list.append(_t_dict['_t'])

    for _thread in thread_list:
        _thread.start()  # 先开始后加入防止没有一起运行

    for _thread in thread_list:
        _thread.join()


if __name__ == '__main__':
    c_list = [cookie2, cookie3, cookie5]
    u_list = [ua2, ua3, ua5]
    b_list = [buvid3_2, buvid3_3, buvid3_5]
    device_id_list = ['ba48683e093188101591e0d940282ccd',
                      '782bc33cb065325b0aa26ae94516b1d2',
                      '311acb22c5fe99f40cc4d93128b31413'
                      ]  # deviceid限制了每个设备只能领一张，多领就会出现"大家挤作一团(Ｔ▽Ｔ)快来重新提交"的提示
    thread_receive_coupon(c_list, u_list, b_list, device_id_list)
    # t1 = threading.Thread(target=thread_receive_coupon, args=(cookie2, ua2, uid2, buvid3_2))
    # t2 = threading.Thread(target=thread_receive_coupon, args=(cookie3, ua3, uid3, buvid3_3))
    # t3 = threading.Thread(target=thread_receive_coupon, args=(cookie4, ua4, uid4, buvid3_4))
    # t1.start()
    # t2.start()
    # t3.start()
    # t1.join()
    # t2.join()
    # t3.join()
