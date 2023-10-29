# -*- coding:utf- 8 -*-
import os
import random
import json
import re
import sys
import time
import traceback

import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import requests
import Bilibili_methods.all_methods

BAPI = Bilibili_methods.all_methods.methods()


def timeshift(timestamp):
    local_time = time.localtime(timestamp)
    realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
    return realtime


class get_space_history:
    def __init__(self):
        if not os.path.exists('./OutputFile'):
            os.makedirs('./OutputFile')
        self.alldynamicid = []
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
        self.all_followed_uid = []
        self.f = None
        self.cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        self.fullcookie3 = gl.get_value('fullcookie3')
        self.ua3 = gl.get_value('ua3')
        self.fingerprint3 = gl.get_value('fingerprint3')
        self.csrf3 = gl.get_value('csrf3')
        self.uid3 = gl.get_value('uid3')
        self.username3 = gl.get_value('uname3')
        self.recorded_dynamic_id = []
        self._get_recorded_dynamic_id()
        try:
            self.record_log_file = open('log/抽奖号的记录.csv', 'a+', encoding='utf-8')
        except:
            self.record_log_file = open('log/抽奖号的记录.csv', 'w', encoding='utf-8')
        def login_check(cookie, ua):
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

        login_check(self.cookie3, self.ua3)
        def get_attention(cookie,ua):
            url='https://api.vc.bilibili.com/feed/v1/feed/get_attention_list'
            headers={
                'cookie':cookie,
                'user-agent':ua
            }
            req=requests.get(url=url,headers=headers)
            return req.json().get('data').get('list')
        self.all_followed_uid = get_attention(self.cookie3,self.ua3)
        print(f'共{len(self.all_followed_uid)}个关注')

    def _get_recorded_dynamic_id(self):
        with open('OutputFile/抽奖号的动态.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                if re.findall('https://t.bilibili.com/(.\d+)', i, re.S):
                    self.recorded_dynamic_id.append(re.findall('https://t.bilibili.com/(.\d+)', i, re.S)[0].strip())

    def get_reqtext(self, hostuid, offset):
        ua = random.choice(self.User_Agent_List)
        headers = {'user-agent': ua}
        uid = 0
        dongtaidata = {
            'visitor_uid': uid,
            'host_uid': hostuid,
            'offset_dynamic_id': offset,
            'need_top': '0',
            'platform': 'web'
        }
        url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=' + str(
            uid) + '&host_uid=' + str(hostuid) + '&offset_dynamic_id=' + str(offset) + '&need_top=0'
        req = requests.request('GET', url=url, headers=headers, data=dongtaidata)
        return req.text

    def get_space_detail(self, space_reqtext):  # 直接处理
        req_dict = json.loads(space_reqtext)
        if req_dict.get('code') == -412:
            print(req_dict)
            print(req_dict.get('message'))
            time.sleep(10 * 60)
        if not req_dict:
            print('ERROR')
            print(space_reqtext)
        cards_json = req_dict.get('data').get('cards')
        dynamic_id_list = []
        for card_dict in cards_json:
            dynamic_id = card_dict.get('desc').get('pre_dy_id_str')  # 判断中转动态id是否重复；非最原始动态id
            print(f"当前动态： https://t.bilibili.com/{card_dict.get('desc').get('dynamic_id')}")
            if dynamic_id in self.recorded_dynamic_id:
                print('遇到log文件记录过的动态id')
                continue
            if dynamic_id == "0":
                print('遇到已删除动态')
                continue
            if dynamic_id in dynamic_id_list:
                print('遇到重复动态id')
                print('https://t.bilibili.com/{}'.format(dynamic_id))
                continue
            if dynamic_id in self.alldynamicid:
                print('遇到重复动态id')
                print('https://t.bilibili.com/{}'.format(dynamic_id))
                continue
            dynamic_id_list.append(dynamic_id)
            self.card_detail(card_dict)
        self.alldynamicid.extend(dynamic_id_list)
        if not dynamic_id_list:
            time.sleep(2)
        return 0

    def card_detail(self, cards_json):
        card_json = json.loads(cards_json.get('card'))
        pre_isliked = None
        pre_relation = None
        pre_author_name = None
        pre_content = None
        pre_commentcount = None
        pre_replycount = None
        pre_official_verify_type = None
        pre_pub_time = None
        # print(card_json)  # 测试点
        uname = cards_json.get('desc').get('user_profile').get('info').get('uname')
        try:
            if card_json.get('item').get('tips') == "源动态已被作者删除":
                print(card_json.get('item').get('tips'))
                return 0
            if card_json.get('origin_user').get('card') is not None:
                origin_official_verify = card_json.get('origin_user').get('card').get('official_verify').get('type')
                origin_uname = card_json.get('origin_user').get('info').get('uname')
            else:
                origin_uname = None
                origin_official_verify = None
            pre_dy_id = card_json.get('item').get('pre_dy_id')
            orig_dy_id = card_json.get('item').get('orig_dy_id')
            if pre_dy_id == orig_dy_id:
                pre_dy_id = None
            user_content = card_json.get('item').get('content')
            orig_type = card_json.get('item').get('orig_type')
            origin = json.loads(card_json.get('origin'))
            reply = origin.get('reply')
            origin_timestamp = cards_json.get('desc').get('origin').get('timestamp')
            pre_dy_detail = None
            if pre_dy_id:
                pre_dy_detail = BAPI.get_dynamic_detail(pre_dy_id,log_report_falg=False)
                time.sleep(3)
                pre_isliked = pre_dy_detail.get('is_liked')
                pre_isliked = None
                pre_author_uid = pre_dy_detail.get('author_uid')
                pre_relation = pre_dy_detail.get('relation')
                if pre_author_uid in self.all_followed_uid:
                    pre_relation = 1
                else:
                    pre_relation = 0
                pre_author_name = pre_dy_detail.get('author_name')
                pre_commentcount = pre_dy_detail.get('comment_count')
                pre_replycount = pre_dy_detail.get('forward_count')
                pre_content = pre_dy_detail.get('dynamic_content')
                pre_official_verify_type = pre_dy_detail.get('official_verify_type')
                pre_pub_time = pre_dy_detail.get('pub_time')
            ori_dy_detail = BAPI.get_dynamic_detail(orig_dy_id,log_report_falg=False)
            time.sleep(3)
            ori_isliked = ori_dy_detail.get('is_liked')
            ori_isliked = None
            ori_relation = ori_dy_detail.get('relation')
            pre_author_uid = ori_dy_detail.get('author_uid')
            if pre_author_uid in self.all_followed_uid:
                ori_relation = 1
            else:
                ori_relation = 0
            ori_reply = ori_dy_detail.get('forward_count')
        except Exception as e:
            traceback.print_exc()
            print(cards_json)
            return 0
        dynamic_commentcount = None
        if orig_type == 1:
            dynamic_content = origin.get('item').get('content')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('转发动态或转发视频：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 2:
            dynamic_content = origin.get('item').get('description')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带图原创动态：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 4:
            dynamic_content = origin.get('item').get('content')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('不带图的原创动态：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 8:
            dynamic_content1 = origin.get('desc')
            dynamic_content2 = origin.get('dynamic')
            dynamic_content = dynamic_content1 + dynamic_content2
            dynamic_commentcount = origin.get('stat').get('reply')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('原创视频：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 64:
            dynamic_content = origin.get('title')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('专栏动态：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 4308:
            dynamic_content = '直播间标题，无视'
            print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print(origin.get('live_play_info').get('title'))
            print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('直播动态：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        elif orig_type == 2048:
            dynamic_content = origin.get('vest').get('content')
            print(dynamic_content)
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带简报的动态：https://t.bilibili.com/' + str(orig_dy_id) + '?tab=2')
        else:
            dynamic_content = 'Error'
        if reply is not None:
            commentcount = reply
        elif dynamic_commentcount:
            commentcount = dynamic_commentcount
        elif origin.get('item'):
            commentcount = origin.get('item').get('reply')
        else:
            commentcount = None
        if pre_dy_id == None:
            pre_dy_id_url = None
        else:
            pre_dy_id_url = f'https://t.bilibili.com/{pre_dy_id}'

        def str_modify(input_str):
            if input_str == None:
                return 'None'
            if input_str == True:
                return 'True'
            if input_str == False:
                return 'False'
            return input_str.replace(',', '，').replace('"', '\'')

        self.f.writelines(
            f'https://t.bilibili.com/{orig_dy_id} ,\
{ori_isliked},\
{origin_uname},\
{ori_relation},\
{origin_official_verify},\
{(repr(str_modify(dynamic_content)))},\
{timeshift(origin_timestamp)},\
{commentcount},\
{ori_reply},\
{uname},\
{repr(str_modify(user_content))},\
{pre_dy_id_url},\
{pre_isliked},\
{pre_author_name},\
{pre_relation},\
{pre_official_verify_type},\
{repr(str_modify(pre_content))},\
{pre_pub_time},\
{pre_commentcount},\
{pre_replycount},\
{orig_type}\n')
        self.record_log_file.writelines(
            f'https://t.bilibili.com/{orig_dy_id} ,\
{ori_isliked},\
{origin_uname},\
{ori_relation},\
{origin_official_verify},\
{(repr(str_modify(dynamic_content)))},\
{timeshift(origin_timestamp)},\
{commentcount},\
{ori_reply},\
{uname},\
{repr(str_modify(user_content))},\
{pre_dy_id_url},\
{pre_isliked},\
{pre_author_name},\
{pre_relation},\
{pre_official_verify_type},\
{repr(str_modify(pre_content))},\
{pre_pub_time},\
{pre_commentcount},\
{pre_replycount},\
{orig_type}\n')
        print(
            f'https://t.bilibili.com/{orig_dy_id} ,\
{ori_isliked},\
{pre_dy_id_url} ,\
{pre_isliked},\
{origin_uname},\
{ori_relation},\
{origin_official_verify},\
{(repr(str_modify(dynamic_content)))},\
{timeshift(origin_timestamp)},\
{commentcount},\
{ori_reply},\
{uname},\
{repr(str_modify(user_content))},\
{pre_dy_id_url} ,\
{pre_isliked},\
{pre_author_name},\
{pre_relation},\
{pre_official_verify_type},\
{repr(str_modify(pre_content))},\
{pre_pub_time},\
{pre_commentcount},\
{pre_replycount}\n')
        # (
        #    '原动态,原动态是否点赞,原动态用户昵称,是否关注原动态up,原动态up认证类型,原内容,原发布时间,原评论数,原转发数,原转发者,转发内容,
        #    间接动态,间接动态是否点赞,间接动态用户昵称,是否关注间接动态up,间接动态up认证类型,间接动态内容,间接发布时间,间接评论数,间接转发数\n')

    def get_space_dynmaic_time(self, space_reqtext):  # 返回list
        req_dict = json.loads(space_reqtext)
        cards_json = req_dict.get('data').get('cards')
        dynamic_time_list = []
        for card_dict in cards_json:
            dynamic_time = card_dict.get('desc').get('timestamp')
            dynamic_time_list.append(dynamic_time)
        return dynamic_time_list

    def get_offset(slef, space_reqtext):
        req_dict = json.loads(space_reqtext)
        return req_dict.get('data').get('next_offset')

    def main(self):
        sleeptime = 0
        uidlist = [
            # 100680137,#你的工具人老公
            # 323360539,#猪油仔123
            20958956,#T_T欧萌
            # 970408,  # up主的颜粉
            # 24150189,#不适这样的
            # 275215223,#黑板小弟
            # 4380948,#玉瑢
            # 96948162,#究极貔貅
            # 365404611,#梦灵VtL
            # 672080,#喋血的爱丽丝
            # 587970586,#扬升平安夜
            # 239894183,#お帰り_Doctor
            # 47350939,#焰燃丶
            # 456414076,#为斯卡蒂献出心脏T_T
            # 442624804,#粉墨小兔兔
            # 295117380,#乘风破浪锦鲤小皇后
            # 672080,#喋血的爱丽丝
            # 1397970246,#六七爱十三k
            # 323198113,#⭐吃蓝莓的喵酱
            # 332793152,#⭐欧王本王
            # 87838475,  # *万事屋无痕
            1122996945,  # 多f邦
            646686238,  # 小欧太难了a
            372793166,  # 二二的辰
            386051299,  # 云散水消
            332793152,  # 仲夏凝秋
            342819796,  # 它知我意
            1992540748,  # Lady_oy
            1045135038,  # 神之忏悔王神
            381282283,  # 小尤怜
            279262754,  # 星空听虫鸣
            237736901,
        ]
        jiangeshijian = 86400 * 2  # 多少时间以前的就不获取了
        n = 0
        self.f = open('./OutputFile/抽奖号的动态.csv', 'w', encoding='utf-8', newline="")
        self.f.writelines(timeshift(time.time()) + '\n\n')
        self.f.writelines('\n')
        self.f.writelines('原动态,原动态是否点赞,原动态用户昵称,是否关注原动态up,原动态up认证类型,原内容,原发布时间,原评论数,原转发数,原转发者,转发内容,间接动态,间接动态是否点赞,间接动态用户昵称,是否关注间接动态up,间接动态up认证类型,间接动态内容,间接发布时间,间接评论数,间接转发数,原动态类型\n')
        for uid in uidlist:
            offset = 0
            while 1:
                dyreqtext = self.get_reqtext(uid, offset)
                n += 1
                time.sleep(sleeptime)
                if self.get_space_detail(dyreqtext) != 0:
                    offset = 0
                    continue
                offset = self.get_offset(dyreqtext)
                timelist = self.get_space_dynmaic_time(dyreqtext)
                time.sleep(5)
                if time.time() - timelist[-1] >= jiangeshijian:
                    if uid == uidlist[-1]:
                        print('最后一个uid获取结束')
                        break
                    else:
                        print('超时动态，进入下一个uid')
                        time.sleep(60)
                        break
                if n % 50 == 0:
                    print('获取了50次，休息个10s')
                    time.sleep(10)
        self.f.close()
        self.record_log_file.close()


if __name__ == '__main__':
    getspace = get_space_history()
    getspace.main()
