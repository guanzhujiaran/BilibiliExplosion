# -*- coding:utf- 8 -*-
import json
import os
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
import Bilibili_methods.all_methods
import b站cookie.b站cookie_
import b站cookie.globalvar as gl

BAPI = Bilibili_methods.all_methods.methods()
cookie1 = gl.get_value('cookie1').encode('utf-8')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1').encode('utf-8')
ua1 = gl.get_value('ua1').encode('utf-8')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
username1 = gl.get_value('uname1')
watch_cookie1 = gl.get_value('watch_cookie1').encode('utf-8')

cookie2 = gl.get_value('cookie2').encode('utf-8')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2').encode('utf-8')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
username2 = gl.get_value('uname2')
watch_cookie2 = gl.get_value('watch_cookie2').encode('utf-8')

cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3').encode('utf-8')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3').encode('utf-8')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
username3 = gl.get_value('uname3')
watch_cookie3 = gl.get_value('watch_cookie3').encode('utf-8')

cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4').encode('utf-8')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4').encode('utf-8')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
username4 = gl.get_value('uname4')
watch_cookie4 = gl.get_value('watch_cookie4').encode('utf-8')


class reserve_lottery:
    def __init__(self):
        if not os.path.exists('./预约抽奖log'):
            os.makedirs('./预约抽奖log')
        self.cookie = ''
        self.ua = ''
        self.uid=''
        self.username = ''
    def login_check(self):
        headers = {
            'User-Agent': self.ua,
            'cookie': self.cookie
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        res = requests.get(url=url, headers=headers).json()
        if res['data']['isLogin'] == True:
            name = res['data']['uname']
            self.username = name
            self.uid = res['data']['mid']
            print(f'登录成功,当前账号用户名为{self.username}\tUID:{self.uid}')
            if not os.path.exists(f'./预约抽奖log'):
                os.makedirs(f'./预约抽奖log')
            return 1
        else:
            print('登陆失败,请重新登录')
            sys.exit('登陆失败,请重新登录')

    def get_reserve_total(self, business_id):
        url = 'https://api.bilibili.com/x/activity/up/reserve/relation/info?ids={}'.format(business_id)
        # {'code': 0, 'message': '0', 'ttl': 1, 'data': {'list': {'713185': {'sid': 713185, 'name': '直播预约：预约先看评测 618
        # 直播', 'total': 14327, 'stime': 1654945555, 'etime': 1655469300, 'isFollow': 0, 'state': 100, 'oid': '',
        # 'type': 2, 'upmid': 483311105, 'reserveRecordCtime': 0, 'livePlanStartTime': 1655467200, 'upActVisible': 0,
        # 'lotteryType': 1, 'prizeInfo': {'text': '预约有奖：保友金豪 EX*1份', 'jumpUrl':
        # 'https://www.bilibili.com/h5/lottery/result?business_id=713185&business_type=10&lottery_id=96545'},
        # 'dynamicId': '670475400331132952', 'reserveTotalShowLimit': 50, 'desc': '', 'start_show_time': 0,
        # 'hide': None, 'ext': '{"subType":0,"productIdPrice":""}'}}}}
        req = requests.get(url)
        try:
            return req.json().get('data').get('list').get(str(business_id)).get('total')
        except:
            print(req.json())
            print(url)
            print('获取预约人数失败')
            return None

    def reserve_attach_card_button(self, business_id, reserve_total, csrf, cookie, ua):
        url = 'https://api.vc.bilibili.com/dynamic_mix/v1/dynamic_mix/reserve_attach_card_button'
        data = {
            'csrf': csrf,
            'cur_btn_status': 1,
            'reserve_id': business_id,
            'reserve_total': reserve_total,
        }
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': cookie,
            'origin': 'https://www.bilibili.com',
            'referer': 'https://www.bilibili.com/',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua
        }
        req = requests.post(url=url, data=data, headers=headers)
        print(req.text)
        return req.json()

    def start_reserve(self, url_list, csrf, cookie, ua):
        self.cookie = cookie
        self.ua = ua
        self.login_check()
        try:
            q = open(f'./预约抽奖log/{self.uid}参加过的官方抽奖.csv','r',encoding='utf-8')
        except:
            q = open(f'./预约抽奖log/{self.uid}参加过的官方抽奖.csv', 'w', encoding='utf-8')
            q.close()
            q=None
        already_list = []
        if q:
            for i in q.readlines():
                already_list.append(i.strip())
            q.close()
        print(f'参加过的抽奖：\n{already_list}')
        for i in url_list:
            if i not in already_list:
                business_id = re.findall('business_id=(\d+)', i)[0]
                lottery_id = re.findall('lottery_id=(\d+)', i)[0]
                reserve_total = self.get_reserve_total(business_id)
                if reserve_total:
                    print('共{}人预约'.format(reserve_total))
                    with open(f'./预约抽奖log/{self.uid}参加过的官方抽奖.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(f'{i}\n')
                    if self.reserve_attach_card_button(business_id, reserve_total, csrf, cookie, ua).get('code') == 0:
                        print('预约抽奖参加成功')
                    else:
                        print('预约参加失败')
                        print(i)
                        try:
                            with open(f'./预约抽奖log/{self.uid}参加失败的官方抽奖.csv','a+',encoding='utf-8')as p:
                                p.writelines(f'{i}\n')
                        except:
                            with open(f'./预约抽奖log/{self.uid}参加失败的官方抽奖.csv','w',encoding='utf-8')as p:
                                p.writelines(f'{i}\n')
                    time.sleep(30)


if __name__ == '__main__':
    u_l = [

'https://www.bilibili.com/h5/lottery/result?business_id=949250&business_type=10&lottery_id=110420',
'https://www.bilibili.com/h5/lottery/result?business_id=954323&business_type=10&lottery_id=109883',
'https://www.bilibili.com/h5/lottery/result?business_id=922071&business_type=10&lottery_id=107633',
'https://www.bilibili.com/h5/lottery/result?business_id=951960&business_type=10&lottery_id=109650',
'https://www.bilibili.com/h5/lottery/result?business_id=944044&business_type=10&lottery_id=109043',
'https://www.bilibili.com/h5/lottery/result?business_id=967334&business_type=10&lottery_id=110543',
'https://www.bilibili.com/h5/lottery/result?business_id=968416&business_type=10&lottery_id=110629',
'https://www.bilibili.com/h5/lottery/result?business_id=951305&business_type=10&lottery_id=109584',

]

    a = reserve_lottery()
    a.start_reserve(u_l, csrf2, cookie2, ua2)
    a.start_reserve(u_l, csrf3, cookie3, ua3)
    a.start_reserve(u_l, csrf4, cookie4, ua4)
