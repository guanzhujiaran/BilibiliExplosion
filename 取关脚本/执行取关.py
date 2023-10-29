import sys

import json
import random
import re
import time
# noinspection PyUnresolvedReferences
import traceback
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import numpy
import requests


class relation_change:
    def __init__(self):
        self.quguanshibai = []
        self.sleeptime = numpy.linspace(2, 3, 500, endpoint=False)

    def relation_change(self, cookie, ua, csrf):
        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin']:
                name = res['data']['uname']
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie,ua)
        f = open('取关对象.csv', 'r', encoding='utf-8')
        for mids in f:
            if mids in ['\n', '\r\n'] or mids.strip() == '':
                # doing something
                continue
            mid = mids.split('\t')[0]
            if 'http' in mid:
                mid = mid.split('/')[-1]
            url = 'https://api.bilibili.com/x/relation/modify'
            headers = {
                'cookie': cookie,
                'user-agent': ua
            }
            data = {
                'fid': mid,
                'act': 2,
                're_src': 11,
                # 'spmid': 1145141919810,
                'extend_content': {"entity": "user", "entity_id": mid},
                'jsonp': 'jsonp',
                'csrf': csrf
            }
            req = requests.request('POST', url=url, headers=headers, data=data)
            try:
                req_dict = json.loads(req.text)
            except Exception as e:
                print(e)
                print(traceback.print_exc())
                print(req.text)
                continue
            code = req_dict.get('code')
            if code == 0:
                print('取关成功：{a}'.format(a=mids))
            else:
                self.quguanshibai.append(mid)
                print(req_dict)
                time.sleep(eval(input('输入等待时间')))
            time.sleep(random.choice(self.sleeptime))

    def start(self, accountname):
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

        cookie5 = gl.get_value('cookie5')  # 墨色
        fullcookie5 = gl.get_value('fullcookie5')
        ua5 = gl.get_value('ua5')
        fingerprint5 = gl.get_value('fingerprint5')
        csrf5 = gl.get_value('csrf5')
        uid5 = gl.get_value('uid5')
        if accountname == 1:
            print(uid1)
            self.relation_change(cookie1, ua1, csrf1)

        elif accountname == 2:
            print(uid2)
            self.relation_change(cookie2, ua2, csrf2)

        elif accountname == 3:
            print(uid3)
            self.relation_change(cookie3, ua3, csrf3)

        elif accountname == 4:
            print(uid4)
            self.relation_change(cookie4, ua4, csrf4)


        elif accountname == 5:
            print(uid5)
            self.relation_change(cookie5, ua5, csrf5)


        print('取关失败：{a}'.format(a=self.quguanshibai))

if __name__ == '__main__':
    myexc = relation_change()
    myexc.start(5)
    # myexc.start(2)
    # myexc.start(3)
    # 1：星瞳
    # 2：保加利亚
    # 3：斯卡蒂
    # 4：墨色

