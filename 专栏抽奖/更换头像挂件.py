# -*- coding:utf- 8 -*-

import json
import sys

import numpy
import requests
import random
import re
import time
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as mymethod

myapi = mymethod.methods()


class dynamic_equip_share:
    def __init__(self):
        self.item_id_list = list()
        self.replaceTimes = 1
        self.sleeptime = numpy.linspace(0.5, 5, 500, endpoint=False)

    def main(self, cookie, ua, csrf):
        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')
        login_check(cookie,ua)
        self.item_id_list = myapi.get_pendant_item_id_list(cookie, ua, csrf)
        print('大会员头像挂件{}个'.format(len(self.item_id_list)))
        print(self.item_id_list)
        templist = list()
        for i in range(random.choice([2, 3, 4])):
            templist.append(random.choice(self.item_id_list))
        print('更换{}次'.format(self.replaceTimes))
        for i in range(self.replaceTimes):
            print(myapi.dynamic_equip_share(random.choice(templist), cookie, ua, csrf))
            time.sleep(random.choice(self.sleeptime))


if __name__ == '__main__':
    cookie3 = gl.get_value('cookie3')
    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')
    share = dynamic_equip_share()
    share.replaceTimes = random.choice(range(5, 7))
    share.main(cookie3, ua3, csrf3)
