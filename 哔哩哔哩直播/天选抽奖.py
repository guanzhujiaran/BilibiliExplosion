# -*- coding: utf-8 -*-
import atexit
import csv
import datetime
import json
import os
import random
import re
import sys
import threading
import time
# noinspection PyUnresolvedReferences
import traceback
import copy
import threading as thd
from pprint import pprint

import requests
from six import unichr

sys.path.append('C:/pythontest/')
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import numpy
import Bilibili_methods.all_methods

mymethod = Bilibili_methods.all_methods.methods()
import bili_live.bili_live_api as api

myapi = api.bili_live_api()


class Auto_lottery:
    def __init__(self):
        self.accountname = str
        self.uid = str
        self.cookie = str
        self.ua = str
        self.csrf = str
        self.living_room_id = list()
        self.shortsleeptime = numpy.linspace(1, 3, 500, endpoint=True)
        self.Anchor_ignore_keyword = ["大蒜", "点播", "表情", "小游戏", "cos", "看号", "加速器", "优惠", "舰", "抵扣",
                                      "返券", "冬日热饮", "一起玩",
                                      "星际战甲", "上车", "搭配", "上船", "保温", "写真", "自画像", "自拍", "照",
                                      "总督", "提督", "一毛", "禁言",
                                      "代金", "通行证", "第五人格", "抵用", "精美壁纸", "资格"]
        self.money_min = 30
        self.canjiajiange = 10
        self.chaxunjiange = 600  # 查询关注直播间的间隔
        self.redpocket_queue = list()
        self.anchor_queue = list()
        self.following_list = list()
        self.canjiaguode = list()

    def get_living_room_id(self):
        try:
            url = 'https://api.live.bilibili.com/xlive/web-ucenter/v1/xfetter/GetWebList?page=1&page_size=10&_={}'.format(
                int(time.time()))
            headers = {
                'cookie': self.cookie,
                'user-agent': self.ua
            }
            req = requests.get(url=url, headers=headers)
            for a in req.json().get('data').get('list'):
                self.living_room_id.append(a.get('room_id'))
            count = req.json().get('data').get('count')
            time.sleep(5)
            for p in range(2, int(count / 10) + 2):
                url = 'https://api.live.bilibili.com/xlive/web-ucenter/v1/xfetter/GetWebList?page={0}&page_size=10&_={1}'.format(
                    p, int(time.time()))
                req = requests.get(url=url, headers=headers)
                count = req.json().get('data').get('count')
                for a in req.json().get('data').get('list'):
                    self.living_room_id.append(a.get('room_id'))
                time.sleep(5)
            print('当前共{}个直播间直播中'.format(count))
            self.living_room_id = list(set(self.living_room_id))
            return thd.Timer(self.chaxunjiange, self.get_living_room_id).start()
        except Exception as e:
            print('更新正在直播的房间失败')
            print(e)

    def account_info_init(self, accountname, accountno):
        try:
            open('./log/使用脚本者.csv', 'a+', encoding='utf-8')
        except:
            open('./log/使用脚本者.csv', 'w', encoding='utf-8')
        try:
            open('./log/未知的返回值.csv', 'a+', encoding='utf-8')
        except:
            open('./log/未知的返回值.csv', 'w', encoding='utf-8')
        try:
            open('./log/所有未知类型.csv', 'a+', encoding='utf-8')
        except:
            open('./log/所有未知类型.csv', 'w', encoding='utf-8')
        ############################文件初始化
        self.accountname = accountname
        self.uid = gl.get_value('uid{}'.format(accountno))
        self.cookie = gl.get_value('tianxuan_cookie{}'.format(accountno)).encode('utf-8')
        self.ua = gl.get_value('ua{}'.format(accountno))
        self.csrf = gl.get_value('csrf{}'.format(accountno))

        ###############关注列表初始化
        def login_check(cookie, ua):
            headers = {
                'User-Agent': ua,
                'cookie': cookie
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

        login_check(self.cookie, self.ua)
        # try:
        #     followingf = open('./账号：{}/关注者列表.txt'.format(accountname), 'r+', encoding='utf-8')
        #     last_get_following_time = followingf.readlines()
        #     if time.time() - int(last_get_following_time) > 7 * 24 * 60 * 60:
        #         followingf.close()
        #         followingf = open('./账号：{}/关注者列表.txt'.format(accountname), 'w', encoding='utf-8')
        #         uids = myapi.get_all_following(self.cookie, self.ua)
        #         followingf.writelines('{}\n'.format(time.time()))
        #         for i in uids:
        #             followingf.writelines('{}\n'.format(i))
        #             self.following_list.append(i)
        #         followingf.close()
        #     else:
        #         for i in followingf.readlines():
        #             self.following_list.append(int(i.strip()))
        #         followingf.close()
        # except:
        #     followingf = open('./账号：{}/关注者列表.txt'.format(accountname), 'w', encoding='utf-8')
        #     uids = myapi.get_all_following(self.cookie, self.ua)
        #     followingf.writelines('{}\n'.format(time.time()))
        #     for i in uids:
        #         followingf.writelines('{}\n'.format(i))
        #         self.following_list.append(i)
        #     followingf.close()
        #####################################
        self.fanmedal = dict()
        #####################################获取粉丝牌信息
        try:
            with open('./账号：{}/粉丝勋章.txt'.format(accountname), 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    self.fanmedal.update({i.strip().split('\t')[0]: i.strip().split('\t')[1]})
        except Exception as e:
            print(e)
        ######################################
        print(self.uid)
        print(self.following_list)
        print(self.fanmedal)
        t = thd.Thread(target=self.get_living_room_id, args=())
        t.start()
        # t.join()
        print(self.living_room_id)
        print('账号资料初始化完毕')
        thd.Thread(target=self.start_loop_and_darw, args=()).start()

    def get_data_from_server(self, contrusted_lottery_data):
        print(self.accountname, self.uid)
        if not isinstance(contrusted_lottery_data, dict) or contrusted_lottery_data == {}:
            print('未获取到架构好的抽奖信息')
            exit(114514)
        else:
            print('成功获取到服务器数据')
            l_dict = copy.deepcopy(contrusted_lottery_data)
            try:
                for i in l_dict.get('anchor'):
                    self.lottery_filter(i)
                for i in l_dict.get('popularity_red_pocket'):
                    self.lottery_filter(i)
            except:
                print('l_dict出错')
                print(l_dict)
            # print(
            #    '\033[0;36;40m✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n\033[0m')
            l_dict.clear()

    def lottery_filter(self, l_data):  # 过滤并加入队列
        try:
            if l_data.get('type') == 'anchor':
                uid = l_data.get('uid')
                room_id = l_data.get('room_id')
                award_name = l_data.get('award_name')
                gift_price = l_data.get('gift_price')
                gift_num = l_data.get('gift_num')
                require_text = l_data.get('require_text')
                danmu = l_data.get('danmu')
                require_value = l_data.get('require_value')
                tianxuanid = l_data.get('id')
                # print('{}\t\t【天选时刻】\n直播间：https://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                #     mymethod.timeshift(time.time()), room_id,
                #     award_name,
                #     require_text,
                #     danmu,
                #     gift_price * gift_num))
                if tianxuanid in self.canjiaguode:
                    print('【天选时刻】已参与\n')
                    return 0
                for i in self.Anchor_ignore_keyword:
                    if i in award_name:
                        print('【天选时刻】含有屏蔽词，不参与\n')
                        return 0
                if re.match('.*红包.*|.*元.*|.*rmb.*', award_name):
                    print(
                        '{}\t\t【天选时刻】\n直播间：https://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                            mymethod.timeshift(time.time()), room_id,
                            award_name,
                            require_text,
                            danmu,
                            gift_price * gift_num))
                    try:
                        money = re.findall('\d+', award_name)[0]
                        if int(money) < self.money_min:
                            print('【天选时刻】{0}元红包金额小于{1}元，不参加\n'.format(money, self.money_min))
                            return 0
                    except:
                        print('【天选时刻】红包金额获取失败，不参与\n')
                        return 0
                if l_data.get('room_id') in self.living_room_id:
                    if l_data.get('require_type') == 0:
                        if gift_price * gift_num == 0:
                            print(
                                '{}\t\t【天选时刻】\n直播间：https://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                                    mymethod.timeshift(time.time()), room_id,
                                    award_name,
                                    require_text,
                                    danmu,
                                    gift_price * gift_num))
                            print('【天选时刻】成功加入队列\n')
                            self.anchor_queue.append(l_data)
                            return 0
                        else:
                            print('【天选时刻】付费的不参加\n')
                            return 0
                    elif l_data.get('require_type') == 1:
                        if gift_price * gift_num == 0:
                            print(
                                '{}\t\t【天选时刻】\n直播间：https://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                                    mymethod.timeshift(time.time()), room_id,
                                    award_name,
                                    require_text,
                                    danmu,
                                    gift_price * gift_num))
                            print('【天选时刻】成功加入队列\n')
                            self.anchor_queue.append(l_data)
                            return 0
                        else:
                            print('【天选时刻】付费的不参加\n')
                            return 0
                    elif l_data.get('require_type') == 2:
                        if str(room_id) in self.fanmedal.keys():
                            if require_value <= int(self.fanmedal.get(str(room_id))):
                                if gift_price * gift_num == 0:
                                    self.anchor_queue.append(l_data)
                                    # myapi.join_anchor(tianxuanid, gift_id, gift_num, room_id, cookie, ua, csrf)
                                    return 0
                                else:
                                    print('【天选时刻】付费的不参加\n')
                                    return 0
                            else:
                                print('【天选时刻】粉丝勋章等级不足，不参与 http://live.bilibili.com/{}\n'.format(room_id))
                                return 0
                        else:
                            print('【天选时刻】未拥有粉丝勋章，不参与 http://live.bilibili.com/{}\n'.format(room_id))
                            return 0
                    elif l_data.get('require_type') == 3:
                        print('【天线时刻】大航海玩家，不参加\n')
                        return 0
                    elif l_data.get('require_type') == 5:
                        if gift_price * gift_num == 0:
                            print(
                                '{}\t\t【天选时刻】\n直播间：http://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                                    mymethod.timeshift(time.time()), room_id,
                                    award_name,
                                    require_text,
                                    danmu,
                                    gift_price * gift_num))
                            print('【天选时刻】成功加入队列\n')
                            self.anchor_queue.append(l_data)
                            return 0
                else:
                    print('【天线时刻】未关注或未预约，不参加')
                    print(
                        '{}\t\t【天选时刻】\n直播间：http://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}\n\n\n'.format(
                            mymethod.timeshift(time.time()), room_id,
                            award_name,
                            require_text,
                            danmu,
                            gift_price * gift_num))
                    return 0
                print('识别失败')
                print(l_data)
                return 0
                #################################################天选时刻过滤

            elif l_data.get('type') == 'popularity_red_pocket':
                # anchor_uid = l_data.get('anchor_uid')
                # total_price = l_data.get('total_price') / 1000
                # room_id = l_data.get('room_id')
                # hongbaoid = l_data.get('id')
                # print('{}\n\t\t\t\t【电池红包】\n\t\t\t\t房间号： https://live.bilibili.com/{} \n\t\t\t\t金额：{}元'.format(
                #     mymethod.timeshift(time.time()),
                #     room_id, total_price))
                # if hongbaoid in self.canjiaguode:
                #     print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t已参加，不再加入队列\n'.format(
                #         mymethod.timeshift(time.time()), room_id))
                #     return 0
                # if total_price >= 100:
                #     print(
                #         '\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t超大红包成功加入队列\n'.format(
                #             room_id))
                #     self.redpocket_queue.append(l_data)
                # elif anchor_uid in self.following_list:
                #     if total_price >= self.money_min:
                #         print('\t\t\t\t【电池红包】\n\t\t\t\t房间号： https://live.bilibili.com/{} \n\t\t\t\t关注者大红包成功加入队列\n'.format(
                #             mymethod.timeshift(time.time()), room_id))
                #     else:
                #         print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t关注者的小红包，不加入队列\n'.format(
                #             mymethod.timeshift(time.time()), room_id))
                # else:
                #     print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t未关注者小红包不加入队列\n'.format(room_id))
                # return 0
                print('电池红包不参加')
            else:
                print('识别失败')
                print(l_data)
                return 0
        except:
            print(l_data)
            exit(1919810)

    def start_loop_and_darw(self):
        while 1:
            if self.anchor_queue != []:
                print('抽奖队列：')
                print(self.anchor_queue)
                for i in self.anchor_queue:
                    try:
                        with open('./账号：{}/log/参与天选记录.txt'.format(self.accountname), 'a+',
                                  encoding='utf-8') as f:
                            f.writelines('{0}：{1}\n'.format(mymethod.timeshift(time.time()), i))
                    except:
                        f = open('./账号：{}/log/参与天选记录.txt'.format(self.accountname), 'w', encoding='utf-8')
                        f.writelines('{0}：{1}\n'.format(mymethod.timeshift(time.time()), i))
                    tianxuanid = i.get('id')
                    self.canjiaguode.append(tianxuanid)
                    gift_id = i.get('gift_id')
                    gift_num = i.get('gift_num')
                    room_id = i.get('room_id')
                    if i.get('time') - 60 > 0:
                        thd.Timer(random.choice(numpy.linspace(0, i.get('time') - 50, 500)), myapi.join_anchor, args=(
                            tianxuanid, gift_id, gift_num, room_id, self.cookie, self.ua, self.csrf, self.uid)).start()
                    else:
                        thd.Timer(1, myapi.join_anchor, args=(
                            tianxuanid, gift_id, gift_num, room_id, self.cookie, self.ua, self.csrf, self.uid)).start()
                self.anchor_queue.clear()
            if self.redpocket_queue != []:
                for i in self.redpocket_queue:
                    endtime = i.get('end_time')
                    id = i.get('id')
                    self.canjiaguode.append(id)
                    roomid = i.get('room_id')
                    ruid = i.get('anchor_uid')
                    thd.Timer(endtime - int(time.time()) - 30, myapi.popularity_red_pocket_join,
                              (self.uid, id, roomid, ruid, self.cookie, self.ua, self.csrf)).start()
                self.redpocket_queue.clear()
            time.sleep(1)


class handle_data_from_server:
    def __init__(self):
        self.fake_ua = [
            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
            "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
            "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
            "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
            "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
            "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
            "UCWEB7.0.2.37/28/999",
            "NOKIA5700/ UCWEB7.0.2.37/28/999",
            "Openwave/ UCWEB7.0.2.37/28/999",
            "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999",
            # iPhone 6：
            "Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25",

        ]
        self.jiangeshijian = 20  # 从服务器获取数据的间隔时间
        self.script_users = list()
        self.unknown = list()
        self.luckyone = list()
        self.highlight_keyword = ['京东卡', 'q', 'Q', '手机', '硬盘', '处理器', '床垫', '3D鼠标垫']  # 高亮提醒词
        self.alive_items = []  # 未过期的抽奖
        self.judge_lottery_past()  # 判断列表里是否过期
        self.show_bar()
        self.null_id_list = []
        self.getinfo_done_list = []
        self.lottery_data = []
        self.recorded_id = []
        self.anchor_list = list()  # 记录所有天选
        self.redpocket_list = list()  # 记录所有红包
        self.anchor_luck_guy_list = []  # 记录中奖用户
        try:
            open('./log/中奖用户详情记录.csv', 'a+', encoding='utf-8')
        except:
            open('./log/中奖用户详情记录.csv', 'w', encoding='utf-8')
        try:
            open('./log/所有天选记录.csv', 'a+', encoding='utf-8')
        except:
            open('./log/所有天选记录.csv', 'w', encoding='utf-8')
        try:
            open('./log/所有红包记录.csv', 'a+', encoding='utf-8')
        except:
            open('./log/所有红包记录.csv', 'w', encoding='utf-8')
        try:
            open('./log/所有天选中奖记录.csv', 'a+', encoding='utf-8')
        except:
            open('./log/所有天选中奖记录.csv', 'w', encoding='utf-8')
        thd.Thread(target=self.record_anchor_redpocket, args=()).start()
        thd.Timer(30, self.pushplus,args=()).start()  # pushplus推送

    def record_anchor_redpocket(self):
        time.sleep(60)
        while 1:
            if not self.anchor_list:
                pass
            else:
                with open('./log/所有天选记录.csv', 'a+', encoding='utf-8') as record1:
                    for i in self.anchor_list:
                        record1.writelines('{}\n'.format(i))
                self.anchor_list.clear()
            if not self.redpocket_list:
                pass
            else:
                with open('./log/所有红包记录.csv', 'a+', encoding='utf-8') as record2:
                    for q in self.anchor_list:
                        record2.writelines('{}\n'.format(q))
                self.redpocket_list.clear()
            if not self.anchor_luck_guy_list:
                pass
            else:
                dr = csv.DictReader(open('./log/所有天选中奖记录.csv', 'r', encoding='utf-8'), delimiter=',')
                with open('./log/所有天选中奖记录.csv', 'a+', encoding='utf-8', newline='') as record3:
                    writer = csv.DictWriter(record3, delimiter=',', fieldnames=dr.fieldnames)
                    if self.anchor_luck_guy_list:
                        for a_r in self.anchor_luck_guy_list:
                            if a_r:
                                writer.writerow(a_r)
                self.anchor_luck_guy_list.clear()
            time.sleep(5 * 60)

    def get_online_gold_rank(self, ruid, roomId):
        '''
        {
        "userRank":1,
        "uid":474368284,
        "name":"Ll六梨",
        "face":"https://i1.hdslb.com/bfs/face/48c8d7f6d2480f3171a8dddd749af00a6dac1a49.jpg",
        "score":1380,
        "medalInfo":{
            "guardLevel":3,
            "medalColorStart":1725515,
            "medalColorEnd":5414290,
            "medalColorBorder":6809855,
            "medalName":"千鸟毛",
            "level":24,
            "targetId":32367854,
            "isLight":1
        },
        "guard_level":3
        }
        :return:
        '''
        # print('获取Online Gold Rank')
        user_list = []

        page = 1
        while 1:
            url = 'https://api.live.bilibili.com/xlive/general-interface/v1/rank/getOnlineGoldRank'
            params = {
                'ruid': ruid,
                'roomId': roomId,
                'page': page,
                'pageSize': 50
            }
            headers = {
                'user-agent': random.choice(self.fake_ua)
            }
            req = requests.get(url=url, params=params, headers=headers)
            onlineNum = req.json().get('data').get('onlineNum')
            OnlineRankItem = req.json().get('data').get('OnlineRankItem')
            user_list.extend(OnlineRankItem)
            if len(user_list) >= onlineNum:
                break
            else:
                page += 1
            if OnlineRankItem == []:
                break
        return user_list

    def show_bar(self):
        if self.alive_items:
            self.alive_items.sort(key=lambda x: x.get('end_time'), reverse=False)
            for i in self.alive_items:
                print(i.get('pt_msg') + '\t剩余时间：{}'.format(i.get("end_time") - int(time.time())))
            print('============================', mymethod.timeshift(int(time.time())))
        threading.Timer(15, self.show_bar).start()

    def pushplus(self):
        if self.alive_items:
            self.alive_items.sort(key=lambda x: x.get('end_time'), reverse=False)
            #             highlight_prize=[
            #     "手办",
            #     "ps",
            #     "旗舰手机",
            #     "铁三角",
            #     "海盗船",
            #     "情书",
            #     "告白花束",
            #     "花式夸夸",
            #     "撒花",
            #     "星愿水晶球",
            #     "守护之翼"
            # ]
            # push_num=0
            print('pushplus Start')
            msg_return = """<!DOCTYPE html><html><head><meta charset="utf-8"><style  type="text/css">a {background-color:GhostWhite;color: #FF34B3;border-radius: 4px;border: solid;padding: 5px;cursor: pointer;box-shadow: 1px 1px 2px #00000075;}</style></head><body>"""
            for i in self.alive_items:
                # if i not in highlight_prize:
                #     continue
                # else:
                #     push_num+=1
                __url = ''.join(re.findall('(https://live.bilibili.com/\d+)', i.get('pt_msg')))
                html_text = i.get('prizename') + '\t剩余时间：{}秒'.format(i.get("end_time") - int(time.time()))
                # html_former = f'<a href="{__url}">{html_text[7:].replace("　", " ")}</a><br>'
                html_former = f'<a href="{__url}">{html_text.replace("　", " ")}</a><br>'
                msg_return += html_former
            msg_return += '</body></html>'
            # if push_num:
            res = requests.post('http://www.pushplus.plus/send',
                                data=json.dumps({
                                    'title': '天选和红包',
                                    'content': msg_return,
                                    'token': '044b3325295b47228409452e0e7aeef7',
                                    'template': 'html'
                                }),
                                headers={
                                    'content-type': 'application/json'
                                }
                                )
            if res.json().get('code') == 900:
                print(f'pushplus:{res.text}')
                today = datetime.date.today()
                tomorrow = today + datetime.timedelta(days=1)
                tomorrow_start_time = int(time.mktime(time.strptime(str(tomorrow), '%Y-%m-%d')))
                threading.Timer(tomorrow_start_time - int(time.time()), self.pushplus).start()
                return
            print(f'pushplus:{res.text}')
        threading.Timer(7.5 * 60, self.pushplus).start()

    def record_lottery_winner(self, ruid, room_id, award_name, award_users: list):
        def get_user_info(_mid):
            '''

            :param _mid:
            :return:{
    "mid": "3461572708010189",
    "name": "bili_3461572708010189",
    "approve": false,
    "sex": "保密",
    "rank": "5000",
    "face": "https://i2.hdslb.com/bfs/face/93620dfe162a453b2cb147fa6a15bb8d4e78b5e9.jpg",
    "face_nft": 0,
    "face_nft_type": 0,
    "DisplayRank": "0",
    "regtime": 0,
    "spacesta": 0,
    "birthday": "",
    "place": "",
    "description": "",
    "article": 0,
    "attentions": [],
    "fans": 0,
    "friend": 12,
    "attention": 12,
    "sign": "",
    "level_info": {
        "current_level": 0,
        "current_min": 0,
        "current_exp": 0,
        "next_exp": 0
    },
    "pendant": {
        "pid": 0,
        "name": "",
        "image": "",
        "expire": 0,
        "image_enhance": "",
        "image_enhance_frame": ""
    },
    "nameplate": {
        "nid": 0,
        "name": "",
        "image": "",
        "image_small": "",
        "level": "",
        "condition": ""
    },
    "Official": {
        "role": 0,
        "title": "",
        "desc": "",
        "type": -1
    },
    "official_verify": {
        "type": -1,
        "desc": ""
    },
    "vip": {
        "type": 0,
        "status": 0,
        "due_date": 0,
        "vip_pay_type": 0,
        "theme_type": 0,
        "label": {
            "path": "",
            "text": "",
            "label_theme": "",
            "text_color": "",
            "bg_style": 0,
            "bg_color": "",
            "border_color": "",
            "use_img_label": true,
            "img_label_uri_hans": "",
            "img_label_uri_hant": "",
            "img_label_uri_hans_static": "https://i0.hdslb.com/bfs/vip/d7b702ef65a976b20ed854cbd04cb9e27341bb79.png",
            "img_label_uri_hant_static": "https://i0.hdslb.com/bfs/activity-plat/static/20220614/e369244d0b14644f5e1a06431e22a4d5/KJunwh19T5.png"
        },
        "avatar_subscript": 0,
        "nickname_color": "",
        "role": 0,
        "avatar_subscript_url": "",
        "tv_vip_status": 0,
        "tv_vip_pay_type": 0,
        "vipType": 0,
        "vipStatus": 0
    },
    "is_senior_member": 0
}
            '''
            url = 'http://api.bilibili.com/x/web-interface/card'
            params = {
                'mid': _mid
            }
            headers = {
                'user-agent': random.choice(self.fake_ua)
            }
            req = requests.get(url=url, headers=headers, params=params)
            try:
                return req.json().get('data').get('card')
            except:
                traceback.print_exc()
                print(req.json())

        def get_jointime(_mid):
            url = 'http://flyx.fun:1369/sync/getinfo/{}'.format(_mid)
            headers = {
                'user-agent': random.choice(self.fake_ua)
            }
            req = requests.get(url=url, headers=headers)
            jointime = re.findall('B站注册时间：(.*)<br>', req.text)
            return ''.join(jointime)

        gold_rank_list = self.get_online_gold_rank(ruid, room_id)
        winner_info_list = []
        for award_user in award_users:
            uid = int(''.join(re.findall('https://space.bilibili.com/(.*)', award_user.get('space_page'))))
            uname = award_user.get('user_name')
            userRank = None
            for gold_rank in gold_rank_list:
                gold_rank_uid = gold_rank.get('uid')
                if gold_rank_uid == uid:
                    jointime = get_jointime(uid)
                    userRank = gold_rank.get('userRank')
                    score = gold_rank.get('score')
                    liveroom_guard_level = gold_rank.get('guard_level')
                    medalInfo = gold_rank.get('medalInfo')
                    if medalInfo:
                        medalName = medalInfo.get('medalName')
                        level = medalInfo.get('level')
                        isLight = medalInfo.get('isLight')
                        guard_level = medalInfo.get('guard_level')
                        targetId = f"https://space.bilibili.com/{medalInfo.get('targetId')}/dynamic "
                    else:
                        medalName = None
                        level = None
                        isLight = None
                        guard_level = None
                        targetId = None
                    try:
                        user_info_card = get_user_info(uid)
                        user_level = user_info_card.get('level_info').get('current_level')
                        official_verify = user_info_card.get('official_verify').get('type')
                        friend = user_info_card.get('friend')  # 关注数
                        fans = user_info_card.get('fans')
                        vip = user_info_card.get('vip')
                        vipType = vip.get('vipType')
                        if vipType == 0:
                            vipType = '无大会员'
                        elif vipType == 1:
                            vipType = '月度大会员'
                        elif vipType == 2:
                            vipType = '年度及以上大会员'
                        vipStatus = vip.get('vipStatus')
                        if vipStatus == 0:
                            vipStatus = '否'
                        else:
                            vipStatus = '是'

                    except:
                        traceback.print_exc()
                        user_level = None
                        friend = None
                        fans = None
                        vipStatus = None
                        vipType = None
                        official_verify = None
                    winner_info_list.append(
                        {
                            '中奖时间': mymethod.timeshift(int(time.time())),
                            'uid': uid,
                            '昵称': uname,
                            '用户等级': user_level,
                            '奖品': award_name,
                            '开奖时排名': '{}/{}'.format(userRank, len(gold_rank_list)),
                            '助力值': score,
                            '注册时间': jointime,
                            '直播UL等级': award_user.get('level'),
                            '直播间大航海等级': liveroom_guard_level,
                            '关注数': friend,
                            '粉丝数': fans,
                            '当前是否是大会员': vipStatus,
                            '大会员类型': vipType,
                            '粉丝牌名称': medalName,
                            '粉丝牌等级': level,
                            '是否点亮粉丝灯牌': isLight,
                            '粉丝牌大航海等级': guard_level,
                            '粉丝牌up主uid': targetId,
                            '账号认证类型': official_verify,
                            '抽奖直播间': 'https://live.bilibili.com/{} '.format(room_id),
                            '中奖者主页': 'https://space.bilibili.com/{}/dynamic '.format(uid)
                        }
                    )

            if userRank is None:
                print(gold_rank_list)
                jointime = get_jointime(uid)
                try:
                    user_info_card = get_user_info(uid)
                    user_level = user_info_card.get('level_info').get('current_level')
                    official_verify = user_info_card.get('official_verify').get('type')
                    friend = user_info_card.get('friend')  # 关注数
                    fans = user_info_card.get('fans')
                    vip = user_info_card.get('vip')
                    vipType = vip.get('vipType')
                    if vipType == 0:
                        vipType = '无大会员'
                    elif vipType == 1:
                        vipType = '月度大会员'
                    elif vipType == 2:
                        vipType = '年度及以上大会员'
                    vipStatus = vip.get('vipStatus')
                    if vipStatus == 0:
                        vipStatus = '否'
                    else:
                        vipStatus = '是'

                except:
                    traceback.print_exc()
                    user_level = None
                    friend = None
                    fans = None
                    vipStatus = None
                    vipType = None
                    official_verify = None
                winner_info_list.append(
                    {
                        '中奖时间': mymethod.timeshift(int(time.time())),
                        'uid': uid,
                        '昵称': uname,
                        '用户等级': user_level,
                        '奖品': award_name,
                        '开奖时排名': '{}/{}'.format(userRank, len(gold_rank_list)),
                        '助力值': '未知',
                        '注册时间': jointime,
                        '直播UL等级': award_user.get('level'),
                        '直播间大航海等级': '未知',
                        '关注数': friend,
                        '粉丝数': fans,
                        '当前是否是大会员': vipStatus,
                        '大会员类型': vipType,
                        '粉丝牌名称': '未知',
                        '粉丝牌等级': '未知',
                        '是否点亮粉丝灯牌': '未知',
                        '粉丝牌大航海等级': '未知',
                        '粉丝牌up主uid': '未知',
                        '账号认证类型': official_verify,
                        '抽奖直播间': 'https://live.bilibili.com/{} '.format(room_id),
                        '中奖者主页': 'https://space.bilibili.com/{}/dynamic '.format(uid)
                    }
                )

        if winner_info_list:
            # print('记录中奖用户详情')
            ## pprint(winner_info_list)
            with open('./log/中奖用户详情记录.csv', 'a+', encoding='utf-8', newline='') as record:
                writer = csv.DictWriter(record, delimiter=',', fieldnames=winner_info_list[0].keys())
                for a_r in winner_info_list:
                    writer.writerow(a_r)

    def judge_lottery_past(self):
        try:
            if self.alive_items:
                temp_list = self.alive_items
                for i in temp_list:
                    if int(time.time()) > i.get('end_time') + 5:
                        self.alive_items.remove(i)
                        print('清除过期抽奖')
                        if i.get('type') == 'anchor':
                            anchor_result = myapi.anchor_check(i.get('room_id'))
                            anchor_result_data = anchor_result.get('data')
                            award_users = []
                            if anchor_result_data:
                                if anchor_result_data.get('award_users'):
                                    for user in anchor_result_data['award_users']:
                                        award_users.append(
                                            {'space_page': 'https://space.bilibili.com/{}'.format(user['uid']),
                                             'user_name': user['uname'], 'level': user['level'],
                                             'bag_id': user['bag_id'], 'gift_id': user['gift_id'], 'num': user['num']})
                            else:
                                print('anchor_result', anchor_result)
                                print(i.get('room_id'))
                                continue
                            self.anchor_luck_guy_list.append(
                                {
                                    'id': anchor_result_data['id'],
                                    'room_id': anchor_result_data['room_id'],
                                    'status': anchor_result_data['status'],
                                    'award_name': anchor_result_data['award_name'],
                                    'award_num': anchor_result_data['award_num'],
                                    'award_image': anchor_result_data['award_image'],
                                    'danmu': anchor_result_data['danmu'],
                                    'time': anchor_result_data['time'],
                                    'current_time': mymethod.timeshift(anchor_result_data['current_time']),
                                    'join_type': anchor_result_data['join_type'],
                                    'require_type': anchor_result_data['require_type'],
                                    'require_value': anchor_result_data['require_value'],
                                    'require_text': anchor_result_data['require_text'],
                                    'gift_id': anchor_result_data['gift_id'],
                                    'gift_name': anchor_result_data['gift_name'],
                                    'gift_num': anchor_result_data['gift_num'],
                                    'gift_price': anchor_result_data['gift_price'],
                                    'cur_gift_num': anchor_result_data['cur_gift_num'],
                                    'goaway_time': anchor_result_data['goaway_time'],
                                    'award_users': award_users,
                                    'show_panel': anchor_result_data['show_panel'],
                                    'lot_status': anchor_result_data['lot_status'],
                                    'send_gift_ensure': anchor_result_data['send_gift_ensure'],
                                    'goods_id': anchor_result_data['goods_id'],
                                    'award_type': anchor_result_data['award_type'],
                                    'award_price_text': anchor_result_data['award_price_text'],
                                    'ruid': anchor_result_data['ruid'],
                                }
                            )
                            threading.Thread(target=self.record_lottery_winner, args=(
                                anchor_result_data['ruid'], anchor_result_data['room_id'],
                                anchor_result_data['award_name'],
                                award_users)).start()
            threading.Timer(1, self.judge_lottery_past).start()
        except:
            threading.Timer(1, self.judge_lottery_past).start()
            errorTime = time.time()
            while 1:
                print(errorTime)
                traceback.print_exc()
                time.sleep(5)

    def strQ2B(self, ustring):
        """全角转半角"""
        rstring = ""
        for uchar in ustring:
            inside_code = ord(uchar)
            # print(inside_code)
            if inside_code == 12288:  # 全角空格直接转换
                inside_code = 32
            elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
                inside_code -= 65248

            rstring += unichr(inside_code)
        return rstring

    def strB2Q(self, ustring):
        """半角转全角"""
        rstring = ""
        for uchar in ustring:
            inside_code = ord(uchar)
            if inside_code == 32:  # 半角空格直接转化
                inside_code = 12288
            elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
                inside_code += 65248

            rstring += unichr(inside_code)
        return rstring

    def data_printer(self, single_data):
        id = single_data['id']
        if len(self.recorded_id) > 1000:
            self.recorded_id = self.recorded_id[700:]
        if id != 999999999999 and id in self.recorded_id:
            return
        self.recorded_id.append(id)
        room_id = single_data['room_id']
        try:
            data = json.loads(single_data['data'])
        except:
            print('data_printer', single_data['data'])
            return
        single_data.update({'data': data})
        ip = single_data['ip']
        if type(data) == list:
            for i in data:
                print(i)
            return

        _type = data.get("type")
        if data.get('room_id') is None and data.get('sender_uid') is None:
            return
        if _type == 'popularity_red_pocket':
            print('popularity_red_pocket_data', single_data)
            try:
                dm = data['danmu']
            except:
                dm = 'None'
                print('data_printer', 'dm', single_data)
            end_time = data['end_time']
            # anchor_uid = data['anchor_uid']
            # sender_uid = data['sender_uid']
            total_price = data['total_price']
            pattern = '\033[1;31m【道具红包】 https://live.bilibili.com/{0:<15}价值：{1:{4}<45}结束时间：{2:{4}<20}上传者ip：{3:<15}'
            pt_msg = pattern.format(room_id, self.strB2Q(str(total_price / 1000) + ' 弹幕：{}'.format(dm)),
                                    mymethod.timeshift(end_time), ip,
                                    chr(12288))
            if single_data not in self.redpocket_list:
                self.alive_items.append(
                    {'pt_msg': pt_msg, 'end_time': end_time, 'type': 'popularity_red_pocket', 'room_id': room_id,
                     'prizename': f'{int(total_price / 1000)}元红包'})
                self.redpocket_list.append(single_data)
        elif _type == 'anchor':
            print('anchor_data', single_data)
            try:
                dm = data['danmu']
            except:
                dm = 'None'
                print('data_printer', 'dm', single_data)
            end_time = data['current_time'] + data['time']
            gift_price = data['gift_price'] * data['gift_num']
            require_text = data['require_text']
            award_name = data['award_name']
            try:
                award_num = data['award_num']
            except:
                award_num = data
            pattern = '\033[1;35m【天选抽奖】 https://live.bilibili.com/{0:<15}奖品：{1:{4}<45}结束时间：{2:{4}<20}上传者ip：{3:<15}'
            pt_msg = pattern.format(room_id,
                                    self.strB2Q(
                                        '{} *{} 需求：{} 需要投喂：{}元 弹幕：{}'.format(award_name, award_num,
                                                                                      require_text,
                                                                                      gift_price / 1000, dm)),
                                    mymethod.timeshift(end_time), ip, chr(12288))
            if single_data not in self.anchor_list:
                self.alive_items.append({'pt_msg': pt_msg, 'end_time': end_time, 'type': 'anchor', 'room_id': room_id,
                                         'prizename': f'{award_name} {require_text} {int(gift_price / 1000)}'})
                self.anchor_list.append(single_data)

    def contrust_lottery_data(self):
        self.lottery_data = myapi.get_data_from_server()
        # print(self.lottery_data)
        for j in range(len(self.lottery_data)):
            res = self.getLotteryInfoWeb(self.lottery_data[j])
            self.lottery_data[j] = res
        for q in self.lottery_data:
            # print(q)
            self.data_printer(q)
        l_dict = {'anchor': list(), 'popularity_red_pocket': list()}
        if self.lottery_data:
            for i in self.lottery_data:
                # print(i)
                if i.get('data') != '在线打卡' and '天选时刻' not in i.get('data') and '道具大红包' not in i.get(
                        'data') and '动态抽奖' not in i.get('data') and i.get('data') not in ["辣条", "小心心", "亿圆",
                                                                                              "B坷垃",
                                                                                              "i了i了", "情书",
                                                                                              "打call", "牛哇",
                                                                                              "干杯", "这个好诶",
                                                                                              "星愿水晶球", "告白花束",
                                                                                              "花式夸夸", "撒花",
                                                                                              "守护之翼", "牛哇牛哇",
                                                                                              "小花花"]:
                    if not isinstance(i.get('data'), list) and not isinstance(i.get('data'), str):
                        try:
                            if i.get('data').get('type') == 'anchor':
                                if i.get('data').get('current_time') is None:
                                    return
                                if i.get('data').get('current_time') + i.get('data').get(
                                        'time') - int(
                                    time.time()) > 0:  # 筛选出未开奖的天选
                                    l_dict['anchor'].append(i.get('data'))
                            elif i.get('data').get('type') == 'popularity_red_pocket':
                                if i.get('data').get('current_time') is None:
                                    return
                                if i.get('data').get('end_time') > int(time.time()):  # 筛选出为开奖的电池红包
                                    red_pocket_dict = copy.deepcopy(i.get('data'))
                                    dtldict = {'id': i.get('id'), 'room_id': i.get('room_id')}
                                    red_pocket_dict.update(dtldict)
                                    l_dict['popularity_red_pocket'].append(red_pocket_dict)
                            else:
                                if i.get('id') == 999999999999:
                                    try:
                                        with open('./log/未知的返回值.csv', 'a+', encoding='utf-8') as f:
                                            f.writelines('{}\n'.format(i))
                                    except:
                                        with open('./log/未知的返回值.csv', 'w', encoding='utf-8') as f:
                                            f.writelines('{}\n'.format(i))
                        except Exception as e:
                            self.unknown.append(i)
                            traceback.print_exc()
                            # print(type(i))
                    else:
                        print('无用信息', i.get('data'))
                else:
                    if not isinstance(i.get('data'), dict):
                        if i.get('data') != '在线打卡':
                            if not isinstance(i.get('data'), dict):
                                self.luckyone.append(i)
                        else:
                            self.script_users.append(i)
        self.lottery_data.clear()
        return l_dict

    def getLotteryInfoWeb(self, data_json):
        id = data_json.get('id')
        if len(self.getinfo_done_list) > 1000:
            self.getinfo_done_list = self.getinfo_done_list[700:]
        if id in self.getinfo_done_list:
            return data_json
        roomid = data_json.get('room_id')
        if id == 999999999999:
            self.null_id_list.append(id)
            # print('无改动', data_json)
            return data_json
        if 'type' not in data_json.get('data'):
            # print('无改动', data_json)
            return data_json
        if 'popularity_red_pocket' in data_json.get('data') or 'anchor' in data_json.get('data'):
            if id > 0 and id in self.null_id_list:
                # print('无改动', data_json)
                return data_json
            _data = myapi.getLotteryInfoWeb(roomid)
            # print('getLotteryInfoWeb',_data)
            self.getinfo_done_list.append(id)
            time.sleep(1)
            if _data.get('code') == 0:
                anchor_data = _data.get('data').get('anchor')
                red_pocket_data = _data.get('data').get('red_pocket')
                popularity_red_pocket_data = _data.get('data').get('popularity_red_pocket')
                if popularity_red_pocket_data:
                    popularity_red_pocket_data = popularity_red_pocket_data[0]
                storm_data = _data.get('data').get('storm')
                if anchor_data is None and popularity_red_pocket_data is None and storm_data is None and id > 0 and id in self.null_id_list:
                    self.null_id_list.append(id)
                if len(self.null_id_list) > 100:
                    self.null_id_list = self.null_id_list[50:]
                if (anchor_data != None):
                    anchor_data.update({'type': 'anchor'})
                    anchor_data.update({'anchor_uid': anchor_data.get('ruid')})
                    data_json.update({'data': json.dumps(anchor_data)})
                    # print('返回字典：',data_json)
                    return data_json
                if (popularity_red_pocket_data != None):
                    popularity_red_pocket_data.update({'type': 'popularity_red_pocket'})
                    popularity_red_pocket_data.update({'id': popularity_red_pocket_data.get('lot_id')})
                    data_json.update({'data': json.dumps(popularity_red_pocket_data)})
                    # print('返回字典：',data_json)
                    return data_json
        # print('无改动', data_json)
        return data_json

    def record_script_users(self):
        while 1:
            if self.script_users != []:
                data_list = list(map(eval, set(list(map(str, self.script_users)))))
                for i in data_list:
                    yongjiaobendeuid = i.get('room_id')
                    space_url = 'http://space.bilibili.com/{}'.format(i.get('room_id'))
                    dakashijian = mymethod.timeshift(int(i.get('id')) / 1000)
                    ip = i.get('ip')
                    try:
                        with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{0}\t{1}\t{2}\t{3}\n'.format(dakashijian, yongjiaobendeuid, space_url, ip))
                    except:
                        f = open('./log/使用脚本者.csv', 'w', encoding='utf-8')
                        f.writelines('脚本使用时间\t脚本者uid\t脚本者空间\tip\n')
                        f.close()
                        with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{0}\t{1}\t{2}\t{3}\n'.format(dakashijian, yongjiaobendeuid, space_url, ip))
                self.script_users.clear()
            if self.unknown:
                data_list = list(map(eval, set(list(map(str, self.unknown)))))
                for i in data_list:
                    try:
                        with open('./log/所有未知类型.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{}\n'.format(i))
                    except:
                        f = open('./log/所有未知类型.csv', 'w', encoding='utf-8')
                        f.close()
                        with open('./log/所有未知类型.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{}\n'.format(i))
                self.unknown.clear()
            if self.luckyone:
                data_list = list(map(eval, set(list(map(str, self.luckyone)))))
                for i in data_list:
                    mid = i.get('room_id')
                    u = 'https://space.bilibili.com/{}'.format(mid)
                    ip = i.get('ip')
                    prize = i.get('data')
                    try:
                        with open('./log/中奖用户.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{}\t{}\t{}\t{}\n'.format(u, ip, prize, i))
                    except:
                        f = open('./log/中奖用户.csv', 'w', encoding='utf-8')
                        f.close()
                        with open('./log/中奖用户.csv', 'a+', encoding='utf-8') as f:
                            f.writelines(
                                '{}\t{}\t{}\t{}\n'.format(u, ip, prize, i))
                self.luckyone.clear()
            time.sleep(3 * 60)

    def quit(self):
        print('quit_write_in')
        if self.script_users != []:
            data_list = list(map(eval, set(list(map(str, self.script_users)))))
            for i in data_list:
                yongjiaobendeuid = i.get('room_id')
                space_url = 'http://space.bilibili.com/{}'.format(i.get('room_id'))
                dakashijian = mymethod.timeshift(int(i.get('id')) / 1000)
                ip = i.get('ip')
                try:
                    with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(
                            '{0}\t{1}\t{2}\t{3}\n'.format(dakashijian, yongjiaobendeuid, space_url, ip))
                except:
                    f = open('./log/使用脚本者.csv', 'w', encoding='utf-8')
                    f.writelines('脚本使用时间\t脚本者uid\t脚本者空间\tip\n')
                    f.close()
                    with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(
                            '{0}\t{1}\t{2}\t{3}\n'.format(dakashijian, yongjiaobendeuid, space_url, ip))
            self.script_users.clear()
        if self.unknown:
            data_list = list(map(eval, set(list(map(str, self.unknown)))))
            for i in data_list:
                try:
                    with open('./log/所有未知类型.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(
                            '{}\n'.format(i))
                except:
                    f = open('./log/所有未知类型.csv', 'w', encoding='utf-8')
                    f.close()
                    with open('./log/所有未知类型.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(
                            '{}\n'.format(i))
            self.unknown.clear()
        if self.luckyone:
            data_list = list(map(eval, set(list(map(str, self.luckyone)))))
            for i in data_list:
                try:
                    with open('./log/中奖用户.csv', 'a+', encoding='utf-8') as f:
                        u = 'https://space.bilibili.com/{}'.format(i.get('room_id'))
                        if i.get('id') == 999999999999:
                            f.writelines(
                                '{}'.format(i))
                        else:
                            f.writelines(
                                '{}\t{}\t{}\t{}'.format(mymethod.timeshift(int(i.get('id') / 1000)), u, i, i.get('ip')))
                except:
                    u = 'https://space.bilibili.com/{}'.format(i.get('room_id'))
                    f = open('./log/中奖用户.csv', 'w', encoding='utf-8')
                    f.close()
                    with open('./log/中奖用户.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(
                            '{}\t{}\t{}\t{}'.format(mymethod.timeshift(int(i.get('id') / 1000)), u, i, i.get('ip')))
            self.luckyone.clear()
        if not self.anchor_list:
            pass
        else:
            with open('./log/所有天选记录.csv', 'a+', encoding='utf-8') as record1:
                for i in self.anchor_list:
                    record1.writelines('{}\n'.format(i))
            self.anchor_list.clear()
        if not self.redpocket_list:
            pass
        else:
            with open('./log/所有红包记录.csv', 'a+', encoding='utf-8') as record2:
                for q in self.anchor_list:
                    record2.writelines('{}\n'.format(q))
            self.redpocket_list.clear()
        if not self.anchor_luck_guy_list:
            pass
        else:
            dr = csv.DictReader(open('./log/所有天选中奖记录.csv', 'r', encoding='utf-8'), delimiter=',')
            with open('./log/所有天选中奖记录.csv', 'a+', encoding='utf-8', newline='') as record3:
                writer = csv.DictWriter(record3, delimiter=',', fieldnames=dr.fieldnames)
                for a_r in self.anchor_luck_guy_list:
                    writer.writerow(a_r)
            self.anchor_luck_guy_list.clear()


if __name__ == '__main__':
    # myapi.daka()
    # account1 = Auto_lottery()
    # account2 = Auto_lottery()
    # account3 = Auto_lottery()
    # account4 = Auto_lottery()
    # account1.account_info_init('星瞳', 1)
    # account2.account_info_init('保加利亚', 2)
    # account3.account_info_init('斯卡蒂', 3)
    # account4.account_info_init('墨色', 4)

    data_from_server = handle_data_from_server()
    atexit.register(data_from_server.quit)
    thd.Thread(target=data_from_server.record_script_users, args=()).start()
    while 1:
        print('从服务器获取数据')
        try:
            contrusted_lottery_data = data_from_server.contrust_lottery_data()
            # for i in range(2, 5):
            #     str1 = 'thd.Thread(target=account{}.get_data_from_server, args=(contrusted_lottery_data,))'.format(i)
            #     t1 = eval(str1)
            #     t1.start()
            #     t1.join()
            # for i in range(2, 5):
            #     print('account{}'.format(i))
            #     str2 = 'account{}.anchor_queue'.format(i)
            #     print(eval(str2))
            print(mymethod.timeshift(time.time()))
            print('\n\n\n')
            time.sleep(data_from_server.jiangeshijian)
        except:
            traceback.print_exc()
            exit()
