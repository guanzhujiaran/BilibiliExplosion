# -*- coding:utf- 8 -*-
import copy
import json
import os
import random
import re
import sys
import time
import traceback
from atexit import register

import requests
import numpy
# noinspection PyUnresolvedReferences
import Bilibili_methods.module_prevent_filter
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds


class start:
    def __init__(self):
        self.get_dynamic_detail_fail = []
        self.comment_list = []
        self.comment_floor_list = []
        if not os.path.exists('./log'):
            os.makedirs('./log')
        self.wuxuzhuanfa = []
        self.dianguozandedongtai = list()
        self.weiguanzhu = list()
        self.yunxingshijian = 1 * 3600
        self.lottery_dict = dict()
        self.username = ''
        self.random_share_video = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]  # 每转发超过指定数字的时候随机分享一个视频
        self.run_time_step1 = 0.5 * 3600
        self.run_time_step2 = 0.75 * 3600
        self.run_time_step3 = 1 * 3600
        self.run_time_step4 = 1.5 * 3600
        self.pf_api = Bilibili_methods.module_prevent_filter.module_pf()

    def login_check(self, cookie, ua):
        headers = {
            'User-Agent': ua,
            'cookie': cookie
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        res = requests.get(url=url, headers=headers).json()
        if res['data']['isLogin'] == True:
            name = res['data']['uname']
            self.username = name
            print('登录成功,当前账号用户名为%s' % name)
            return 1
        else:
            print('登陆失败,请重新登录')
            sys.exit('登陆失败,请重新登录')

    def account_choose(self, accountname):
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
        if accountname == 1:
            print(uid1)
            self.doit(uid1, cookie1, ua1, csrf1)
        elif accountname == 2:
            print(uid2)
            self.doit(uid2, cookie2, ua2, csrf2)
        elif accountname == 3:
            print(uid3)
            self.doit(uid3, cookie3, ua3, csrf3)
        elif accountname == 4:
            print(uid4)
            self.doit(uid4, cookie4, ua4, csrf4)

    def read_file(self):
        index = 0
        with open('../抽奖转发评论信息（根据文件转评）.csv', 'r', encoding='utf-8') as myf:
            for line in myf.readlines():
                try:
                    index += 1
                    myline = line.strip()
                    dtl = myline.split('\t')
                    dynamic_id = dtl[0]
                    if 'http' in dynamic_id:
                        dynamic_id = dynamic_id.split('/')[-1]
                    uname = dtl[1]
                    dongtaineirong = dtl[2]
                    msg = dtl[3]
                    self.lottery_dict.update(
                        {index: {'dynamic_id': dynamic_id, 'uname': uname, '动态内容': dongtaineirong, 'msg': msg}})
                except:
                    continue

    def doit(self, uid, cookie, ua, csrf):
        self.login_check(cookie, ua)
        username = self.username
        print(username)
        self.read_file()
        for i, j in self.lottery_dict.items():
            print(i, j)
        print('\n\n共有{}条动态'.format(len(self.lottery_dict)))
        input('按任意键继续...')
        print(uid)
        print(new_my_methods.timeshift(timestamp=time.time()))
        # 四阶段运行时间
        if len(self.lottery_dict) <= 50:
            self.yunxingshijian = self.run_time_step1
        elif 100 >= len(self.lottery_dict) > 50:
            self.yunxingshijian = self.run_time_step2
        elif 150 > len(self.lottery_dict) > 100:
            self.yunxingshijian = self.run_time_step3
        else:
            self.yunxingshijian = self.run_time_step4
        print(f'运行时间约为{self.yunxingshijian / 3600}小时')
        longsleeptime = numpy.linspace(0.1 * self.yunxingshijian / (len(self.lottery_dict)),
                                       1.9 * self.yunxingshijian / (len(self.lottery_dict)))
        my_lottery_dict = copy.deepcopy(self.lottery_dict)
        repost_counter = 0  # 转发计数
        for ind in my_lottery_dict.keys():
            if repost_counter > random.choice(self.random_share_video):
                share_sep = self.pf_api.module_share_popvideo(cookie, ua, csrf)
                if share_sep > 300:
                    time.sleep(300)
                else:
                    time.sleep(share_sep)
                repost_counter = 0
            print('\t\t\t\t\t\t\t\t\t当前进度{a}/{b}'.format(a=ind, b=len(self.lottery_dict)))
            try:
                msg = eval(my_lottery_dict[ind]['msg'])
                dynamic_id = my_lottery_dict[ind]['dynamic_id']
                with open('./log/抽奖动态id记录.csv', 'a+', encoding='utf-8') as f:
                    f.writelines(f'{dynamic_id},')
                url = 'https://t.bilibili.com/{}'.format(my_lottery_dict[ind]['dynamic_id'])
                dyresponse = new_my_methods.get_dynamic_detail(my_lottery_dict[ind]['dynamic_id'], cookie, ua)
                if dyresponse:
                    time.sleep(random.choice(new_my_methods.sleeptime))
                    rid = dyresponse.get('rid')
                    type = dyresponse.get('type')
                    relation = dyresponse.get('relation')
                    thumbstatus = dyresponse.get('is_liked')
                    dycontent = dyresponse.get('dynamic_content')
                    card_stype = dyresponse.get('card_stype')
                    if relation != 1:
                        print('未关注\n')
                        self.weiguanzhu.append(url)
                    else:
                        print('已经关注了\n')
                    if thumbstatus == 1:
                        print('遇到点过赞的动态\thttps://t.bilibili.com/{dyid}'.format(dyid=dynamic_id))
                        time.sleep(random.choice(new_my_methods.sleeptime))
                        self.dianguozandedongtai.append(url)
                        stime = random.choice(longsleeptime)
                        print(new_my_methods.timeshift(time.time()))
                        print('休眠{}秒'.format(stime))
                        time.sleep(stime)
                        continue
                    print(url, my_lottery_dict[ind]['uname'], my_lottery_dict[ind]['动态内容'], type, rid, msg)
                    print('\n')
                    if new_my_methods.zhuanfapanduan(my_lottery_dict[ind]['动态内容']):
                        # if str(type) == '2' or str(type) == '4' or str(type) == '8' or str(type) == '64':
                        #     if new_my_methods.repostchance < random.random():
                        #         new_my_methods.repost(dynamic_id, '转发动态', cookie, ua, uid, csrf)
                        #     else:
                        #         new_my_methods.repost(dynamic_id, msg, cookie, ua, uid, csrf)
                        # else:
                        #     if new_my_methods.repostchance < random.random():
                        #         try:
                        #             new_my_methods.js_repost_non_content_dyn(dyresponse, dynamic_id, uid, cookie, ua, csrf)
                        #         except:
                        #             print('js版转发动态失败')
                        #             new_my_methods.repost(dynamic_id, '转发动态', cookie, ua, uid, csrf)
                        #     else:
                        #         new_my_methods.repost(dynamic_id, msg, cookie, ua, uid, csrf)
                        if new_my_methods.repostchance < random.random() and '#' not in msg:
                            try:
                                new_my_methods.js_repost_non_content_dyn(dyresponse, dynamic_id, uid, cookie, ua, csrf,card_stype)
                            except:
                                print('js版转发动态失败')
                                new_my_methods.repost(dynamic_id, msg, cookie, ua, uid, csrf)
                        else:
                            new_my_methods.repost(dynamic_id, msg, cookie, ua, uid, csrf)
                        repost_counter += 1
                    else:
                        self.wuxuzhuanfa.append(url + '\t' + my_lottery_dict[ind]['动态内容'] + '\n')
                    time.sleep(1)

                    # l = new_my_methods.comment_with_thumb(str(dynamic_id), msg, str(type), str(rid), cookie, ua, csrf,
                    #                                       username)
                    l = new_my_methods.comment(str(dynamic_id), msg, str(type), str(rid), cookie, ua, csrf,
                                               username)
                    self.comment_list.append(
                        'https://t.bilibili.com/' + str(dynamic_id) + '\t' + repr(str(msg)) + '\t' +
                        str(dycontent))
                    if l:
                        self.comment_floor_list.append(
                            f'{l}\t{new_my_methods.timeshift(int(time.time()))}\t{repr(msg)}')
                    else:
                        print('评论楼层记录失败')
                    time.sleep(random.choice(new_my_methods.sleeptime))
                    new_my_methods.thumb(dynamic_id, cookie, ua, uid, csrf,card_stype)
                    time.sleep(random.choice(new_my_methods.sleeptime))
                else:
                    print(f'获取失败：{i}')
                    self.get_dynamic_detail_fail.append(str(my_lottery_dict[ind]))
            except:
                traceback.print_exc()
                print('获取动态失败')
                self.get_dynamic_detail_fail.append(str(my_lottery_dict[ind]))
            stime = random.choice(longsleeptime)
            print(new_my_methods.timeshift(time.time()))
            print('休眠{}秒'.format(stime))
            time.sleep(stime)
        try:
            p = open(f'./log/完成记录.csv', 'a+', encoding='utf-8')
        except:
            p = open(f'./log/完成记录.csv', 'w', encoding='utf-8')
        p.writelines(f'{new_my_methods.timeshift(time.time())}\t已完成\n')
        p.close()
        # os.system('python ../../专栏抽奖/转发热门视频_斯卡蒂.py')

    def write_print_log(self):
        def log_write(path, input_list, write_method):
            with open(path, write_method, encoding='utf-8') as _a:
                for __i in input_list:
                    _a.writelines(__i + '\n')

        log_write('log/点赞失败.csv', new_my_methods.dianzanshibai, 'w')
        log_write('log/评论失败.csv', new_my_methods.pinglunshibai, 'w')
        log_write('log/转发失败.csv', new_my_methods.zhuanfashibai, 'w')
        log_write('log/未关注.csv', self.weiguanzhu, 'w')
        log_write('log/无需转发动态id.csv', self.wuxuzhuanfa, 'w')
        log_write('log/评论相关.csv', self.comment_list, 'w')
        log_write('log/关注失败.csv', new_my_methods.guanzhushibai, 'w')
        try:
            log_write('log/评论地址楼层记录.csv', self.comment_floor_list, 'a+')
        except:
            traceback.print_exc()
            log_write('log/评论地址楼层记录.csv', self.comment_floor_list, 'w')
        try:
            log_write('log/获取动态失败.csv', self.get_dynamic_detail_fail, 'a+')
        except:
            traceback.print_exc()
            log_write('log/获取动态失败.csv', self.get_dynamic_detail_fail, 'w')
        print('点赞失败：')
        for i in new_my_methods.dianzanshibai:
            print(i)
        print('评论失败：')
        for i in new_my_methods.pinglunshibai:
            print(i)
        print('转发失败：')
        for i in new_my_methods.zhuanfashibai:
            print(i)
        print('未关注：')
        for i in self.weiguanzhu:
            print(i)
        print('关注失败：')
        for i in new_my_methods.guanzhushibai:
            print(i)


if __name__ == '__main__':
    mycls = start()
    register(mycls.write_print_log)
    mycls.yunxingshijian = 3 * 3600
    # 设置运行时间
    new_my_methods = my_methonds.methods()
    new_my_methods.repostchance = 0.5
    # 转发动态时，转发内容为评论内容的几率
    new_my_methods.sleeptime = numpy.linspace(2, 4, 500, endpoint=False)
    mycls.account_choose(3)
    # 1：星瞳
    # 2：保加利亚
    # 3：斯卡蒂
    # 4：墨色
