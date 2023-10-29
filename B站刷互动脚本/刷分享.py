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

bapi = my_methonds.methods()


class share_add:
    def __init__(self):
        self.sleeptime = numpy.linspace(20, 50, 500, endpoint=False)

    def _doit(self, uid, cookie, ua, csrf, username, midlist):
        v_list = self.get_user_video_aid(midlist)
        i = 1
        v_len=len(v_list)
        if v_len>=900:
            v_len=900
        for a in range(v_len):
            aid = random.choice(v_list)
            print('当前进度【{}/{}】'.format(i, v_len))
            if i % 200 == 0:
                st = random.choice(numpy.linspace(3600, 7200, 500))
                print('休息{}小时'.format(st / 3600))
                time.sleep(st)
            i += 1
            reqtext = bapi.x_share_add(aid, cookie, ua, csrf)
            req = json.loads(reqtext)
            if req.get('code') != 0 and req.get('code') != 71000:
                print(aid)
                exit('分享出错')
            time.sleep(random.choice(self.sleeptime))
            v_list.remove(aid)

    def get_user_video_aid(self, midlist):
        '''
        返回list格式的所有aid
        :return:
        '''
        v_list = list()
        for mid in midlist:
            req = bapi.x_space_arc_search(mid, 1)
            v_count = req.get('data').get('page').get('count')
            vlist = req.get('data').get('list').get('vlist')
            for i in vlist:
                aid = i.get('aid')
                v_list.append(aid)
            allpn = int(v_count / 30) + 1
            time.sleep(1)
            for i in range(2, allpn + 1):
                req = bapi.x_space_arc_search(mid, i)
                vlist = req.get('data').get('list').get('vlist')
                for i in vlist:
                    aid = i.get('aid')
                    v_list.append(aid)
                time.sleep(1)
        print('所有视频列表：')
        for i in v_list:
            print('https://www.bilibili.com/av{}'.format(i))
        print('视频个数：{}'.format(len(v_list)))
        return v_list

    def account_choose(self, accountname, midlist):
        """
        输入选择账号序列和要刷视频的人的uid的list
        :param accountname:
        :param midlist:
        """
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
        share_cookie3 = gl.get_value('share_cookie3')
        cookie4 = gl.get_value('cookie4')  # 墨色
        fullcookie4 = gl.get_value('fullcookie4')
        ua4 = gl.get_value('ua4')
        fingerprint4 = gl.get_value('fingerprint4')
        csrf4 = gl.get_value('csrf4')
        uid4 = gl.get_value('uid4')
        username4 = gl.get_value('uname4')
        if accountname == 1:
            print(uid1)
            self._doit(uid1, cookie1, ua1, csrf1, username1, midlist)
        elif accountname == 2:
            print(uid2)
            self._doit(uid2, cookie2, ua2, csrf2, username2, midlist)
        elif accountname == 3:
            print(uid3)
            self._doit(uid3, share_cookie3, ua3, csrf3, username3, midlist)
        elif accountname == 4:
            print(uid4)
            self._doit(uid4, cookie4, ua4, csrf4, username4, midlist)


if __name__ == '__main__':
    s = share_add()  # 533316954, 643873396, 690820064, 668794409,1429723107,39101587
    s.account_choose(3, [
                         533316954,#SOUNDPEATS
                         1429723107,#索尼中国
                         39101587,#虾米大模王
                         2306780,#哔哩哔哩线下活动
                         1098417804,#坎特伯雷公主求鸡腿
    ])
