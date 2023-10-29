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
import Bilibili_methods.module_prevent_filter as Bi


class my_share:
    def __init__(self):
        self.m = Bi.module_pf()
        self.m.copy_comment_chance = 0.7  # 抄评论概率
        self.m.ero_pic_up_list = [1242384245, 37743601, 129060, 1930483018, 44714970]  # 色图up
        self.m.random_crate_dynamic_content = ['中', '我', '你', '。', '，']  # 自己创建动态的随机内容
        self.m.yunxingshijian = 0.5 * 3600  # 默认运行时间为半小时
        self.m.ero_pic_num = random.choice(range(6, 12))  # 色图的存量


        self.share_num = range(8, 12)  # 分享次数
        self.chance_list = [0, 1, 0, 0]  # 色图概率 热门视频概率  创建动态概率  换头像挂件概率
        self.pf_type = [1, 2, 3, 4]  # 防过滤种类

    def _main(self, uid, cookie, ua, csrf):
        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                username = name
                print('登录成功,当前账号用户名为%s' % username)
                self.m.BAPI.username = username
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie, ua)
        crate_dynamic_content = random.choice(self.m.random_crate_dynamic_content)
        X = [0] * random.choice(self.share_num)
        ero_time = 0
        pop_time = 0
        crate_time = 0
        change_time = 0
        MAX = 0
        for i in self.chance_list:
            MAX += i
        s1 = self.chance_list[0] / MAX
        s2 = s1 + self.chance_list[1] / MAX
        s3 = s2 + self.chance_list[2] / MAX
        s4 = s3 + self.chance_list[3] / MAX
        print(f'共分享{len(X)}次')
        for i in range(len(X)):
            rd = random.random()
            if rd < s1:
                X[i] = 1
            elif s1 <= rd < s2:
                X[i] = 2
            elif s2 <= rd < s3:
                X[i] = 3
            else:
                X[i] = 4
        X.sort()
        print(X)
        for i in X:
            if i == 1:
                ero_time += 1
            elif i == 2:
                pop_time += 1
            elif i == 3:
                crate_time += 1
            elif i == 4:
                change_time += 1
        random.shuffle(self.pf_type)
        print(f'分享图片次数：{ero_time}')
        print(f'分享视频次数：{pop_time}')
        print(f'创建动态次数：{crate_time}')
        print(f'更换头像次数：{change_time}')
        longsleeptime = numpy.linspace(0.5 * self.m.yunxingshijian / (pop_time + 1),
                                       1.5 * self.m.yunxingshijian / (pop_time + 1), endpoint=True)
        for i in self.pf_type:
            if i == 1:
                for ii in range(ero_time):
                    print('分享图片')
                    self.m.module_share_ero_pic(uid, cookie, ua, csrf)
                    time.sleep(random.choice([10,15,20,25]))
            elif i == 2:
                for ii in range(pop_time):
                    print('分享视频')
                    self.m.module_share_popvideo(cookie, ua, csrf)
                    time.sleep(random.choice(longsleeptime))
            elif i == 3:
                for ii in range(crate_time):
                    print('创建动态')
                    self.m.module_random_crate_dynamic(crate_dynamic_content, cookie, ua, csrf, uid)
                    time.sleep(random.choice([1, 2, 3, 4, 5, 6, 7, 8]))
                    continue
            elif i == 4:
                for ii in range(change_time):
                    print('更换头像')
                    self.m.module_change_pendant(cookie, ua, csrf)
                time.sleep(random.choice(longsleeptime))

    def start(self, account_No):
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
        if account_No == 1:
            print(uid1)
            self._main(uid1, cookie1, ua1, csrf1)

        elif account_No == 2:
            print(uid2)
            self._main(uid2, cookie2, ua2, csrf2)


        elif account_No == 3:
            print(uid3)
            self._main(uid3, cookie3, ua3, csrf3)


        elif account_No == 4:
            print(uid4)
            self._main(uid4, cookie4, ua4, csrf4)


if __name__ == '__main__':
    my = my_share()
    my.start(2)
