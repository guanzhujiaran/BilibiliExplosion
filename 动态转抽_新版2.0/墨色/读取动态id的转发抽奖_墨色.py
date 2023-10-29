# -*- coding:utf- 8 -*-
import copy
import json
import os
import random
import re
import sys
import threading
import time
import traceback
from atexit import register

import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods

myapi = Bilibili_methods.all_methods.methods()
myapi.caihongpi_chance = 0.7 # 使用彩虹屁的概率，数字越大，彩虹屁频率越高
myapi.repostchance = 0.3  # 转发动态时，转发内容为评论内容的几率
myapi.pinglunzhuanbiancishu = 5  # 获取评论时失败重新尝试的次数
myapi.chance_shangjiayingguang = 0  # 随机挑线自定义商家广告回复词的概率
myapi.chance_copy_comment = 1  # 抄评论的概率
myapi.non_official_chp_chance = 0.7
myapi.range_copy_comment = 1.5  # 抄评论的长度在20条评论评均长度的比率，数字越大，抄的评论越长
myapi.official_caihongpilist = [
    '冲',
    '来了来了',
    '冲鸭',
    '我我我',
    '中中中中中中',
    '必中',
    '许个愿能中吧',
    '中',
    '试一试',
    '万一',
    '[呲牙]',
    '[OK][OK]',
    '中在参与',
    '重在参与',
    '拉低中奖率',
    '[星星眼][星星眼]',
    '冲吖~',
    '[保卫萝卜_哇]',
    '[保卫萝卜_哇][保卫萝卜_哇]',
    '美滋滋',
    '分母星人',
    '分母来了',
    '来力',
    '从不缺席',
    '拉低中奖率[脱单doge]',
    '参与',
    '好耶[doge]',
    '玄学中奖不会输',
    '来试试手气[妙啊]',
    '来试试手气[doge]',
    '许愿',
    '来了来了许愿'
]
myapi.non_official_chp = [
    '冲',
    '来了来了',
    '冲鸭',
    '秋梨膏',
    '我我我',
    '中中中中中中',
    '必中',
    '许个愿能中吧',
    '中',
    '试一试',
    '万一',
    '[呲牙]',
    '[OK][OK]',
    '中在参与',
    '重在参与',
    '拉低中奖率',
    '[星星眼][星星眼]',
    '冲吖~',
    '[保卫萝卜_哇]',
    '[保卫萝卜_哇][保卫萝卜_哇]',
    '美滋滋',
    '分母星人',
    '分母来了',
    '来力',
    '从不缺席',
    '拉低中奖率[脱单doge]',
    '参与',
    '好耶[doge]',
    '玄学中奖不会输',
    '来试试手气[妙啊]',
    '来试试手气[doge]',
    '许愿',
    '来了来了许愿'
]
csrf = gl.get_value('csrf4')  # 填入自己的csrf
cookie = gl.get_value('cookie4')
useragent = gl.get_value('ua4')
uid = 1178256718


class zhuanfadongtai:
    def __init__(self):
        self.get_dynamic_detail_fail = []
        if not os.path.exists('./log'):
            os.makedirs('./log')

        def login_check(_cookie, ua):
            headers = {
                'User-Agent': ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                username = name
                print('登录成功,当前账号用户名为%s' % username)
                myapi.username = username
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie, useragent)
        self.comment_floor_list = []
        self.comment_list = []
        self.wuxuzhuanfa = []
        self.weiguanzhu = []
        # self.yunxingshijian = 2.5 * 3600#暂时采用分段式运行时间
        self.sleeptime = numpy.linspace(1, 3, 500, endpoint=False)
        self.pinglunzhuanbiancishu = 5
        self.dianguozandedongtai = []
        self.run_time_step1 = 0.5 * 3600
        self.run_time_step2 = 0.75 * 3600
        self.run_time_step3 = 1 * 3600
        self.run_time_step4 = 1.5 * 3600
        self.User_Agent_List = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
            'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
            'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
            'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
            'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999'
        ]
        self.lottery_info_random_percent = 0.1  # 抽奖信息随机的百分比

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def write_print_log(self):
        def log_write(path, input_list, write_method):
            with open(path, write_method, encoding='utf-8') as _a:
                for __i in input_list:
                    _a.writelines(__i + '\n')

        log_write('log/点赞失败.csv', myapi.dianzanshibai, 'w')
        log_write('log/评论失败.csv', myapi.pinglunshibai, 'w')
        log_write('log/转发失败.csv', myapi.zhuanfashibai, 'w')
        log_write('log/未关注.csv', self.weiguanzhu, 'w')
        log_write('log/无需转发动态id.csv', self.wuxuzhuanfa, 'w')
        log_write('log/评论相关.csv', self.comment_list, 'w')
        log_write('log/关注失败.csv', myapi.guanzhushibai, 'w')
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
        for i in myapi.dianzanshibai:
            print(i)
        print('评论失败：')
        for i in myapi.pinglunshibai:
            print(i)
        print('转发失败：')
        for i in myapi.zhuanfashibai:
            print(i)
        print('未关注：')
        for i in self.weiguanzhu:
            print(i)
        print('关注失败：')
        for i in myapi.guanzhushibai:
            print(i)

    def kaishizhuanfa(self):
        mydict = {}
        index = 0
        zhuanfapingluncishu = 0
        with open('../抽奖转发评论信息（根据文件转评）.csv', 'r', encoding='utf-8') as f:
            for i in f:
                if i.strip():
                    if re.findall('\d', i):
                        mydict.update({index: i})
                        index += 1
        if len(mydict) <= 50:
            self.yunxingshijian = self.run_time_step1
        elif 100 >= len(mydict) > 50:
            self.yunxingshijian = self.run_time_step2
        elif 150 > len(mydict) > 100:
            self.yunxingshijian = self.run_time_step3
        else:
            self.yunxingshijian = self.run_time_step4
        longsleeptime = numpy.linspace(0.1 * self.yunxingshijian / (index + 1),
                                       1.9 * self.yunxingshijian / (index + 1), endpoint=True)
        # longsleeptime = [5 * 60, 4 * 60, 6 * 60]
        repost_counter = 0  # 转发计数
        keys = random.sample(sorted(mydict), int(self.lottery_info_random_percent * (index + 1)))
        for i in keys:
            temp = {i: mydict.get(i)}
            mydict.pop(i)
            mydict.update(temp)
        mydict0 = copy.deepcopy(mydict)
        for key in mydict0.keys():
            print('\t\t\t\t当前进度：{0}/{1}'.format(key, len(mydict0)))
            i = mydict0.get(key)
            mydict.pop(key)
            detail = i.rstrip().split('\t')
            try:
                dycontent = detail[2]
            except:
                dycontent = 'None'
            try:
                print(i)
                dynamicid = detail[0]
                if 'http' in dynamicid:
                    dynamicid = dynamicid.split('/')[-1]
                url = 'https://t.bilibili.com/{}'.format(dynamicid)
                dyresponse = myapi.get_dynamic_detail(dynamicid, cookie, useragent)
                time.sleep(random.choice(self.sleeptime))
                rid = dyresponse.get('rid')
                _type = dyresponse.get('type')
                relation = dyresponse.get('relation')
                thumbstatus = dyresponse.get('is_liked')
                author_uid = dyresponse.get('author_uid')
                author_name = dyresponse.get('author_name')
                official_verify_type = dyresponse.get('official_verify_type')
                card_stype= dyresponse.get('card_stype')
                if thumbstatus == 1:
                    print('遇到点过赞的动态')
                    time.sleep(random.choice(self.sleeptime))
                    self.dianguozandedongtai.append(url)
                    print('**********************************************')
                    stime = random.choice(longsleeptime)
                    print(self.timeshift(time.time()))
                    print('休眠{}秒'.format(stime))
                    time.sleep(stime)
                    continue
                else:
                    print('未点赞')
                if relation != 1:
                    print('未关注')
                    self.weiguanzhu.append(url)
                    myapi.relation_modify(1, author_uid, cookie, useragent, csrf)
                else:
                    print('已经关注了')
                if str(_type) == '1':
                    origin_name = dyresponse.get('orig_name')
                    msg = myapi.huifuneirong(official_verify_type, str(dycontent), dynamicid, rid, _type, author_name,
                                             origin_name)
                else:
                    msg = myapi.huifuneirong(official_verify_type, str(dycontent), dynamicid, rid, _type, author_name)
                if msg != '':
                    if not '\u200b互动抽奖' in dycontent:
                        l = myapi.comment(str(dynamicid), msg, str(_type), str(rid), cookie, useragent, csrf,
                                          myapi.username)
                        self.comment_list.append(
                            'https://t.bilibili.com/' + str(dynamicid) + '\t' + repr(str(msg)) + '\t' +
                            str(dycontent))
                        if l:
                            self.comment_floor_list.append(f'{l}\t{myapi.timeshift(int(time.time()))}\t{repr(msg)}')
                        else:
                            print('评论楼层记录失败')
                        time.sleep(1)
                    if myapi.zhuanfapanduan(dycontent):
                        if myapi.repostchance < random.random() and '#' not in msg:
                            try:
                                myapi.js_repost_non_content_dyn(dyresponse, dynamicid, uid, cookie, useragent, csrf,card_stype)
                            except:
                                print('js版转发动态失败')
                                myapi.repost(dynamicid, msg, cookie, useragent, uid, csrf)
                        else:
                            myapi.repost(dynamicid, msg, cookie, useragent, uid, csrf)
                        repost_counter += 1
                    else:
                        print('无需转发：https://t.bilibili.com/' + str(dynamicid))
                        self.wuxuzhuanfa.append(url + '\t' + dycontent + '\n')
                    time.sleep(random.choice(self.sleeptime))
                    myapi.thumb(dynamicid, cookie, useragent, uid, csrf,card_stype)
                    time.sleep(random.choice(self.sleeptime))
                    zhuanfapingluncishu += 1
                else:
                    print('评论失败\n原因：获取评论失败')
                    choujianglianjie = 'https://t.bilibili.com/' + str(dynamicid)
                    myapi.pinglunshibai.append(f'{choujianglianjie}\t获取评论失败')
                stime = random.choice(longsleeptime)
                print(self.timeshift(time.time()))
                print('休眠{}秒'.format(stime))
                time.sleep(stime)
            except Exception as e:
                print(e)
                print(f'获取失败：{i}')
                traceback.print_exc()
                self.get_dynamic_detail_fail.append(i)
                # time.sleep(eval(input('输入等待时间')))
                continue
            print('=================================')
        print('无需转发：')
        for i in self.wuxuzhuanfa:
            print(i)
        print('点赞失败：' + str(myapi.dianzanshibai))
        print('评论失败：' + str(myapi.pinglunshibai))
        print('转发失败：' + str(myapi.zhuanfashibai))
        print('点过赞的动态：\n' + str(self.dianguozandedongtai))
        print('未关注：')
        print(self.weiguanzhu)
        print('关注失败：')
        print(myapi.guanzhushibai)
        print('mydict剩余：')
        print(mydict)
        try:
            p = open(f'./log/完成记录.csv', 'a+', encoding='utf-8')
        except:
            p = open(f'./log/完成记录.csv', 'w', encoding='utf-8')
        p.writelines(f'{myapi.timeshift(time.time())}\t已完成\n')
        p.close()
        # os.system('python ../../专栏抽奖/转发热门视频_墨色.py')
        # os.system('shutdown /s /t 900')

if __name__ == '__main__':
    a = zhuanfadongtai()
    register(a.write_print_log)
    print(a.timeshift(time.time()))
    # a.kaishizhuanfa()
    t = threading.Timer(3600 * 0, a.kaishizhuanfa).start()
    print(a.timeshift(time.time()))
    # os.system('python ../../专栏抽奖/转发热门视频_墨色.py')
