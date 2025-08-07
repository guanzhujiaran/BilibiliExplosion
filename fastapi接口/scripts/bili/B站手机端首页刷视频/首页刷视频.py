import atexit
import copy
import csv
import json
import random
import re
import time
import traceback
from hashlib import md5
from typing import Union
from urllib.parse import urlencode

import requests
from loguru import logger
from pylangtools.langconv import Converter

import Bilibili_methods.all_methods


class Crypto:
    APPKEY = '1d8b6e7d45233436'
    APPSECRET = '560c52ccd288fed045859ed18bffd973'

    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        '''generates md5 hex dump of `str` or `bytes`'''
        if type(data) == str:
            return md5(data.encode()).hexdigest()
        return md5(data).hexdigest()

    @staticmethod
    def sign(data: Union[str, dict]) -> str:
        '''salted sign funtion for `dict`(converts to qs then parse) & `str`'''
        if isinstance(data, dict):
            _str = urlencode(data)
        elif type(data) != str:
            raise TypeError
        return Crypto.md5(_str + Crypto.APPSECRET)


class SingableDict(dict):
    @property
    def sorted(self):
        '''returns an alphabetically sorted version of `self`'''
        return dict(sorted(self.items()))

    @property
    def signed(self):
        '''returns our sorted self with calculated `sign` as a new key-value pair at the end'''
        _sorted = self.sorted
        return {**_sorted, 'sign': Crypto.sign(_sorted)}


class index:
    def __init__(self):
        self.recorded_aid = []
        atexit.register(self.quit)
        # 文件
        self.lottery = None
        self.op = None
        self.official = None
        self.official_lottery = None
        self.official_account = None
        self.f = None
        self.unknown = None
        # 文件

        self.list_unknown = []
        self.list_op = []
        self.list_f = []
        self.list_lottery = []
        self.list_official_lottery = []
        self.list_official = []
        self.guanhao = {}
        self.BAPI = Bilibili_methods.all_methods.methods()
        self.n = 0
        self.times = 0
        if not self.loginVerify():
            self.log.log("ERROR", "登录失败")
            exit("登录失败")
        self.init()
    headers = {
        "User-Agent": "Mozilla/5.0 BiliDroid/6.73.1 (bbcallen@gmail.com) os/android model/Mi 10 Pro mobi_app/android build/6731100 channel/xiaomi innerVer/6731110 osVer/12 network/2",
    }
    access_key = '83b05d0b1f84a507e61d79c04e623681'

    def loginVerify(self) -> bool:
        """
        登录验证
        """
        loginInfo = self.loginVerift()
        self.mid, self.name = loginInfo['mid'], loginInfo['name']
        self.log = logger.bind(user=self.name)
        if loginInfo['mid'] == 0:
            self.isLogin = False
            return False
        self.log.log("SUCCESS", str(loginInfo['mid']) + " 登录成功")
        self.isLogin = True
        return True

    def loginVerift(self):
        """
        登录验证
        """
        url = "https://app.bilibili.com/x/v2/account/mine"
        params = {
            "access_key": self.access_key,
            "actionKey": "appkey",
            "appkey": Crypto.APPKEY,
            "ts": int(time.time()),
        }
        req = requests.get(url=url, params=SingableDict(params).signed, headers=self.headers)
        if req.json().get('code') == 0:
            print(req.text)
            return req.json().get('data')
        else:
            print(req.url)
            print(req.text)
            return False

    def index_splash(self):
        """
        获取首页刷新的视频
        :return:
        """
        url = 'https://app.bilibili.com/x/v2/feed/index'
        params = {
            "access_key": self.access_key,
            "appkey": Crypto.APPKEY,
            "ts": int(time.time()),
        }
        req = requests.get(url=url, params=SingableDict(params).signed, headers=self.headers)
        if req.json().get('code') == 0:
            return req.json().get('data')
        else:
            print(req.url)
            print(req.text)
            return False

    def data_items_resolve(self, items: list) -> list:
        def dict2csv(dic, filename):
            """
            将字典写入csv文件，要求字典的值长度一致。
            :param dic: the dict to csv
            :param filename: the name of the csv file
            :return: None
            """
            file = open(filename, 'a+', encoding='utf-8', newline='')
            csv_writer = csv.DictWriter(file, fieldnames=list(dic.keys()))
            csv_writer.writerow(dic)
            file.close()

        templist = []
        for i in items:
            dict2csv(i, 'log/b站服务器返回的data记录.csv')
            can_play = i.get('can_play')
            card_goto = i.get('card_goto')
            card_type = i.get('card_goto')
            cover = i.get('cover')
            cover_left_1_content_description = i.get('cover_left_1_content_description')
            cover_left_2_content_description = i.get('cover_left_2_content_description')
            cover_left_icon_1 = i.get('cover_left_icon_1')
            cover_left_icon_2 = i.get('cover_left_icon_2')
            cover_left_text_1 = i.get('cover_left_text_1')
            cover_left_text_2 = i.get('cover_left_text_2')
            cover_right_content_description = i.get('cover_right_content_description')
            cover_right_text = i.get('cover_right_text')
            goto = i.get('goto')
            idx = i.get('idx')
            param = i.get('param')
            player_args = i.get('player_args')
            if player_args:
                aid = player_args.get('aid')
                cid = player_args.get('cid')
                duration = player_args.get('duration')
                _type = player_args.get('type')
            else:
                aid = None
                cid = None
                duration = None
                _type = None
            talk_back = i.get('talk_back')
            title = i.get('title')
            track_id = i.get('track_id')
            tempdict = {
                'can_play': can_play,
                'card_goto': card_goto,
                'card_type': card_type,
                'cover': cover,
                'cover_left_1_content_description': cover_left_1_content_description,
                'cover_left_2_content_description': cover_left_2_content_description,
                'cover_left_icon_1': cover_left_icon_1,
                'cover_left_icon_2': cover_left_icon_2,
                'cover_left_text_1': cover_left_text_1,
                'cover_left_text_2': cover_left_text_2,
                'cover_right_content_description': cover_right_content_description,
                'cover_right_text': cover_right_text,
                'goto': goto,
                'idx': idx,
                'param': param,  # aid
                'aid': aid,
                'cid': cid,
                'duration': duration,
                'type': _type,
                'talk_back': talk_back,
                'title': title,
                'track_id': track_id
            }
            templist.append(copy.copy(tempdict))
            tempdict.clear()
        return templist

    def contentshow(self, _type, card, dynamicint, dynamic_uid):
        if _type == 1:
            dynamic_content = card.get('item').get('content')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('转发动态或转发视频：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        elif _type == 2:
            dynamic_content = card.get('item').get('description')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带图原创动态：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        elif _type == 4:
            dynamic_content = card.get('item').get('content')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('不带图的原创动态：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        elif _type == 8:
            dynamic_content1 = card.get('desc')
            dynamic_content2 = card.get('dynamic')
            dynamic_rid = card.get('aid')
            dynamic_id = dynamicint
            if len(str(dynamic_rid)) == len(str(dynamic_id)):
                oid = dynamic_id
            else:
                oid = dynamic_rid
            time.sleep(random.choice(self.BAPI.sleeptime))
            dynamic_content3 = self.BAPI.get_topcomment(str(dynamic_id), str(oid), str(0), str(_type), dynamic_uid)
            time.sleep(random.choice(self.BAPI.sleeptime))
            if dynamic_content3 != 'null':
                dynamic_content = dynamic_content1 + dynamic_content2 + dynamic_content3
            else:
                dynamic_content = dynamic_content1 + dynamic_content2
            dynamic_commentcount = card.get('stat').get('reply')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('原创视频：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
            # print(dynamic_commentcount)
        elif _type == 64:
            dynamic_content = card.get('title')
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('专栏动态：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        elif _type == 4308:
            dynamic_content = '直播间标题，无视'
            print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print(card.get('live_play_info').get('title'))
            print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('直播动态：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        elif _type == 2048:
            dynamic_content = card.get('vest').get('content')
            print(dynamic_content)
            print(
                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带简报的动态：https://t.bilibili.com/' + str(dynamicint) + '?tab=2')
        else:
            dynamic_content = '获取动态内容出错，可能是已删除动态'
        return dynamic_content

    def resolve_dynamic(self, req1_dict):
        ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'
        try:
            dycode = req1_dict.get('code')
        except Exception as e:
            dycode = 404
            print(req1_dict)
            print('code获取失败')
        print('\n\t\t\t\t第' + str(self.times+1) + '次获取动态')
        print('\n')
        self.times += 1
        dymsg = req1_dict.get('msg')
        dymessage = req1_dict.get('message')
        dydata = req1_dict.get('data')
        dynamicid = req1_dict.get('data').get('card').get('desc').get('dynamic_id')
        print('https://t.bilibili.com/' + str(dynamicid) + '?tab=2')
        if dycode != 0:
            print('返回码出错')
            print(req1_dict)
            exit()
        if dycode == 0:
            self.n += 1
            try:
                description = dydata.get('card').get('desc')
                dynamicint = description.get('dynamic_id')
                uname = description.get('user_profile').get('info').get('uname')
                uid = description.get('user_profile').get('info').get('uid')
                _type = description.get('type')
                rid = description.get('rid')
                repost = description.get('repost')
                if _type == 2:
                    comment = description.get('comment')
                else:
                    comment = json.loads(dydata.get('card').get('card')).get('stat').get('reply')
                timestamp = description.get('timestamp')
                self.dynamic_timestamp = timestamp
                realtime = self.BAPI.timeshift(timestamp)
                card = json.loads(dydata.get('card').get('card'))
                print('用户昵称：' + uname)
                print(self.BAPI.timeshift(timestamp))
            except Exception as e:
                print(req1_dict)
                uname = 'None'
                timestamp = 'None'
                self.dynamic_timestamp = 'None'
                _type = 'None'
                card = 'None'
                dynamicint = 'None'
                uid = 'None'
                rid = 'None'
                repost = 'None'
                comment = 'None'
                realtime = 'None'
                print('获取动态内容出错，可能是已删除或审核中的动态')
                print(self.BAPI.timeshift(time.time()))
                # traceback.print_exc()
            dynamic_content = Converter('zh-hans').convert(self.contentshow(_type, card, dynamicint, uid))
            try:
                picture_list = ['None'] * 9
                if _type == 2:
                    pic_url_list = card.get('item').get('pictures')
                    for i in range(len(pic_url_list)):
                        picture_list[i] = pic_url_list[i].get('img_src')
                else:
                    pic_url = card.get('pic')
                    picture_list[0] = pic_url
            except:
                print(card)
                print('获取动态图片失败')
                picture_list = ['None'] * 9
            # if dynamic_content != '获取动态内容出错，可能是已删除动态' and rid != 'None':
            #     top_comment = self.get_topcomment(str(dynamicint), str(rid), str(0), str(_type), uid)
            #     dynamic_content += top_comment
            jumpurl = 'https://t.bilibili.com/' + str(dynamicint)
            official = -1
            if uname != 'None' and uid != 'None':
                try:
                    official = dydata.get('card').get('desc').get('user_profile').get('card').get(
                        'official_verify').get(
                        'type')
                except:
                    print('official_type获取失败')
                    official = -1
                if official == 1:
                    if not uname in self.guanhao:
                        try:
                            fansurl = 'https://api.bilibili.com/x/web-interface/card?mid={uid}'.format(uid=uid)
                            data = {
                                'mid': uid,
                            }
                            # p = random.choice(proxy_pool)
                            headers = {
                                'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255))),
                                'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255))),
                                'From': 'bingbot(at)microsoft.com',
                                'user-agent': ua
                            }

                            fansreq = requests.request('GET', url=fansurl, data=data, headers=headers)
                            # except:
                            #     while 1:
                            #         proxy_pool.remove(p)
                            #         fansreq = requests.request('GET', url=fansurl, data=data, headers=headers,
                            #                                    proxies=p)
                            #         if fansreq.status_code == 200:
                            #             break
                            fans_dict = json.loads(fansreq.text)
                            fanscode = fans_dict.get('code')
                            if fanscode == -412:
                                print('获取粉丝数失败')
                                fans = -1
                                level = -1
                                self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                            else:
                                fans = fans_dict.get('data').get('follower')
                                level = fans_dict.get('data').get('card').get('level_info').get('current_level')
                                self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                        except:
                            fans = -1
                            level = -1
                            self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                    elif self.guanhao.get(uname).get('fans') == -1:
                        try:
                            fansurl = 'https://api.bilibili.com/x/web-interface/card?mid={uid}'.format(uid=uid)
                            data = {
                                'mid': uid,
                            }
                            # p = random.choice(proxy_pool)
                            headers = {
                                'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255)),
                                                                        random.choice(range(0, 255))),
                                'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255)),
                                                                  random.choice(range(0, 255))),
                                'From': 'bingbot(at)microsoft.com',
                                'user-agent': ua
                            }

                            fansreq = requests.request('GET', url=fansurl, data=data, headers=headers)
                            # except:
                            #     while 1:
                            #         proxy_pool.remove(p)
                            #         fansreq = requests.request('GET', url=fansurl, data=data, headers=headers,
                            #                                    proxies=p)
                            #         if fansreq.status_code == 200:
                            #             break
                            fans_dict = json.loads(fansreq.text)
                            fanscode = fans_dict.get('code')
                            if fanscode == -412:
                                print('获取粉丝数失败')
                                fans = -1
                                level = -1
                                self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                            else:
                                fans = fans_dict.get('data').get('follower')
                                level = fans_dict.get('data').get('card').get('level_info').get('current_level')
                                self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                        except:
                            fans = -1
                            level = -1
                            self.guanhao.update({uname: {'fans': fans, 'level': level, 'uid': uid}})
                    else:
                        fans = self.guanhao.get(uname).get('fans')
                        level = self.guanhao.get(uname).get('level')
                    self.list_official.append(
                        str(uid) + '\t' + uname + '\t' + str(fans) + '\t' + str(level) + '\t' + repr(
                            str(dynamic_content)) + '\t' + str(comment) + '\t' + str(repost) + '\t' + str(
                            jumpurl) + '\t' + str(
                            realtime) + '\t' + str(uid) + '\n')
                    if not self.choujiangxinxipanduan(dynamic_content):
                        self.list_official_lottery.append(
                            str(uid) + '\t' + uname + '\t' + str(fans) + '\t' + str(level) + '\t' + repr(
                                str(dynamic_content)) + '\t' + str(comment) + '\t' + str(repost) + '\t' + str(
                                jumpurl) + '\t' + str(
                                realtime) + '\t' + str(uid) + '\n')

            append_data_str = f'{uname}\t{str(jumpurl)}\t{rid}\t{repr(str(dynamic_content))}\t{str(realtime)}\t{str(comment)}\t{str(repost)}\t{str(official)}\t{str(uid)}\t{picture_list[0]}\t{picture_list[1]}\t{picture_list[2]}\t{picture_list[3]}\t{picture_list[4]}\t{picture_list[5]}\t{picture_list[6]}\t{picture_list[7]}\t{picture_list[8]}\n'  # 写入文件的格式

            if not self.choujiangxinxipanduan(dynamic_content):
                self.list_lottery.append(append_data_str)
                self.list_f.append(append_data_str)
            if uname != 'None':
                self.list_op.append(append_data_str)
            return
        if dycode != 0:
            self.list_unknown.append('{}：{}\n'.format(self.BAPI.timeshift(time.time()), req1_dict))
        return

    def slash(self, times: int, ):
        for i in range(times):
            ret_data = self.index_splash()
            if ret_data:
                items = ret_data.get('items')
                resolved_data_list = self.data_items_resolve(items)
                for video_info in resolved_data_list:
                    aid = video_info.get('param')
                    if aid not in self.recorded_aid:
                        req_dict = self.BAPI.rid_dynamic_video(aid)
                        try:
                            self.resolve_dynamic(req_dict)
                        except:
                            print(req_dict)
                            traceback.print_exc()
                        self.recorded_aid.append(aid)
            else:
                print('刷新失败，退出')
                exit()
            print('刷新了第{}次index主页'.format(times+1))
            time.sleep(5)

    def init(self):
        try:
            self.unknown = open('未知类型.csv', 'a+', encoding='utf-8')
        except:
            self.unknown = open('未知类型.csv', 'w', encoding='utf-8')
        try:
            self.lottery = open('rid疑似抽奖动态.csv', 'a+', encoding='utf-8')
        except:
            self.lottery = open('rid疑似抽奖动态.csv', 'w', encoding='utf-8')
        try:
            self.op = open('rid总计.csv', 'a+', encoding='utf-8')
        except:
            self.op = open('rid总计.csv', 'w', encoding='utf-8')
        try:
            self.official_account = open('官方号的全部抽奖.csv', 'a+', encoding='utf-8')
        except:
            self.official_account = open('官方号的全部抽奖.csv', 'w', encoding='utf-8')
        try:
            self.official = open('官方号.csv', 'a+', encoding='utf-8')
        except:
            self.official = open('官方号.csv', 'w', encoding='utf-8')
        self.f = open('rid每日动态.csv', 'w', encoding='utf-8')
        self.official_lottery = open('官方号的抽奖.csv', 'w', encoding='utf-8')

    def write_in_file(self):
        def my_write(path_io, content_list):
            for __i in content_list:
                path_io.write('{}'.format(__i))
            content_list.clear()

        if self.list_lottery:
            my_write(self.lottery, self.list_lottery)
        if self.list_op:
            my_write(self.op, self.list_op)
        if self.list_official:
            my_write(self.official, self.list_official)
        if self.list_official_lottery:
            my_write(self.official_lottery, self.list_official_lottery)
            my_write(self.official_account, self.list_official_lottery)
        if self.list_f:
            my_write(self.f, self.list_f)
        if self.list_unknown:
            my_write(self.unknown, self.list_unknown)

    def quit(self):
        """
            退出时必定执行
        """
        print('共' + str(self.times - 1) + '次获取动态')
        print('其中' + str(self.n) + '个有效动态')
        self.write_in_file()
        self.lottery.close()
        self.op.close()
        self.official.close()
        self.official_lottery.close()
        self.official_account.close()
        self.f.close()
        self.unknown.close()
        # os.system('shutdown /s /t 3600')
        # os.system('shutdown /s /t 60')
        # os.system('python ../rid爬动态测试/rid爬动态.py')
        exit(10)

    def choujiangxinxipanduan(self,tcontent):  # 动态内容过滤条件
        '''
        抽奖信息判断      是抽奖返回None 不是抽奖返回1
        :param tcontent:
        :return:
        '''
        tcontent = Converter('zh-hans').convert(tcontent)
        tcontent = tcontent.lower()
        tcontent = tcontent.replace('🧱', '转')
        tcontent = tcontent.replace('🍎', '评')
        tcontent = tcontent.replace('🐷', '注')
        matchobj_100 = re.match('.*参与.*礼品|.*礼品.*参与', tcontent, re.DOTALL)
        matchobj_99 = re.match('.*转.{0,20}得', tcontent, re.DOTALL)
        matchobj_98 = re.match('.*评.{0,10}抽', tcontent, re.DOTALL)
        matchobj_97 = re.match('.*参与.{0,10}关.{0,10}赞.*', tcontent, re.DOTALL)
        matchobj_96 = re.match('.*评.{0,10}赢.*', tcontent, re.DOTALL)
        matchobj_95 = re.match('.*老.{0,10}安排.*', tcontent, re.DOTALL)
        matchobj_94 = re.match('.*抽奖.*', tcontent, re.DOTALL)
        matchobj_93 = re.match('.*抽奖.*参与.*', tcontent, re.DOTALL)
        matchobj_92 = re.match('.*快递.*', tcontent, re.DOTALL)
        matchobj_91 = re.match('.*倒霉蛋.*', tcontent, re.DOTALL)
        matchobj_90 = re.match('.*懂的.*', tcontent, re.DOTALL)
        matchobj_89 = re.match('.*留言.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_88 = re.match('.*评论.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_87 = re.match('.*失物招领.*', tcontent, re.DOTALL)
        matchobj_86 = re.match('.*抽个奖.*', tcontent, re.DOTALL)
        matchobj_85 = re.match('.*r.{0,3}o.{0,3}l.{0,3}l.*', tcontent, re.DOTALL)
        matchobj_84 = re.match('.*本.{0,10}动态.{0,10}抽.*', tcontent, re.DOTALL)
        matchobj_83 = re.match('.*关.{0,10}评.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_82 = re.match('.*赞.{0,10}评.{0,10}转.*', tcontent, re.DOTALL)
        matchobj_81 = re.match('.*注.{0,3}发.*', tcontent, re.DOTALL)
        matchobj_80 = re.match('.*转.{0,10}关.*抽.*', tcontent, re.DOTALL)
        matchobj_79 = re.match('.*关注.*roll.*', tcontent, re.DOTALL)
        matchobj_78 = re.match('.*roll.*关注.*', tcontent, re.DOTALL)
        matchobj_77 = re.match('.*找.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_76 = re.match('.*关注.*评论.{0,10}转发.*', tcontent, re.DOTALL)
        matchobj_75 = re.match('.*抽.{0,10}体验.*', tcontent, re.DOTALL)
        matchobj_74 = re.match('.*揪.{0,10}奖励.*', tcontent, re.DOTALL)
        matchobj_73 = re.match('.*抓.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_72 = re.match('.*动态抽奖.*', tcontent, re.DOTALL)
        matchobj_71 = re.match('.*转.*关.*抽.{0,15}送.*', tcontent, re.DOTALL)
        matchobj_70 = re.match('.*关注.{0,9}惊喜.*', tcontent, re.DOTALL)
        matchobj_69 = re.match('.*揪.{0,9}喝奶.*', tcontent, re.DOTALL)
        matchobj_68 = re.match('.*抽.{0,9}得到.*', tcontent, re.DOTALL)
        matchobj_67 = re.match('.*抽.{0,9}获得.*', tcontent, re.DOTALL)
        matchobj_65 = re.match('.*抽奖.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_64 = re.match('.*评论.{0,10}补贴.*\\d+.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*抽.{0,10}带走.*', tcontent, re.DOTALL)
        matchobj_59 = re.match('.*补贴.{0,10}\d+元.*', tcontent, re.DOTALL)
        matchobj_58 = re.match('.*卷{0,10}抽.*送.*', tcontent, re.DOTALL)
        matchobj_57 = re.match('.*评论.{0,9}揪.*', tcontent, re.DOTALL)
        matchobj_56 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_55 = re.match('.*关注.{0,10}评论.{20}揪', tcontent, re.DOTALL)
        matchobj_54 = re.match('.*评论.{0,5}白.{0,10}嫖.*', tcontent, re.DOTALL)
        matchobj_53 = re.match('.*车专.*关.*', tcontent, re.DOTALL)
        matchobj_52 = re.match('.*评论.*揪.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_51 = re.match('.*评论.*抽.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_50 = re.match('.*转.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_49 = re.match('.*抽1位50元红包.*', tcontent, re.DOTALL)
        matchobj_48 = re.match('.*揪.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_47 = re.match('.*抽.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_46 = re.match('.*抽奖.*抽.*小伙伴.*评论.*转发.*', tcontent, re.DOTALL)
        matchobj_45 = re.match('.*关注.*一键三连.*分享.*送.*', tcontent, re.DOTALL)
        matchobj_44 = re.match('.*揪.{0,10}小可爱.*每人.*', tcontent, re.DOTALL)
        matchobj_43 = re.match('.*#抽奖#.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_42 = re.match('.*关注.*平论.*揪.*打.*', tcontent, re.DOTALL)
        matchobj_41 = re.match('.*转发.*评论.*关注.*抽.*获得.*', tcontent, re.DOTALL)
        matchobj_40 = re.match('.*关注.*转发.*点赞.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_39 = re.match('.*转发评论点赞本条动态.*送.*', tcontent, re.DOTALL)
        matchobj_38 = re.match('.*挑选.*评论.*送出.*', tcontent, re.DOTALL)
        matchobj_37 = re.match('.*弹幕抽.*送.*', tcontent, re.DOTALL)
        matchobj_36 = re.match('.*随机.*位小伙伴.*现金红包.*', tcontent, re.DOTALL)
        matchobj_34 = re.match('.*评论.*随机.*抽.*', tcontent, re.DOTALL)
        matchobj_33 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_32 = re.match('.*参与方式.*转发.*关注.*评论.*', tcontent, re.DOTALL)
        matchobj_31 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_30 = re.match('.*评论.*随机.*抽.*补贴.*', tcontent, re.DOTALL)
        matchobj_29 = re.match('.*评论区.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_28 = re.match('.*转发.*评论.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_27 = re.match('.*互动抽奖.*', tcontent, re.DOTALL)
        matchobj_26 = re.match('.*#供电局福利社#.*', tcontent, re.DOTALL)
        matchobj_25 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_24 = re.match('.*转发.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_23 = re.match('.*关注.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_22 = re.match('.*评论.*转发.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_21 = re.match('.*有奖转发.*', tcontent, re.DOTALL)
        matchobj_20 = re.match('.*评论就有机会抽.*', tcontent, re.DOTALL)
        matchobj_19 = re.match('.*转发.*关注.{0,10}选.*', tcontent, re.DOTALL)
        matchobj_18 = re.match('.*关注+评论，随机选.*', tcontent, re.DOTALL)
        matchobj_17 = re.match('.*互动抽奖.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_16 = re.match('.*关注.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_15 = re.match('.*转.*评.*赞.*送', tcontent, re.DOTALL)
        matchobj_14 = re.match('.*评论区.*揪.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_13 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_12 = re.match('.*评论转发点赞.*抽取.*送.*', tcontent, re.DOTALL)
        matchobj_11 = re.match('.*关注+评论.*随机选.*送.*', tcontent, re.DOTALL)
        matchobj_10 = re.match('.*揪.{0,10}送', tcontent, re.DOTALL)
        matchobj_9 = re.match('.*转发.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_8 = re.match('.*评论.*关注.*揪', tcontent, re.DOTALL)
        matchobj_7 = re.match('.*评论.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_6 = re.match('.*评论区.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_4 = re.match('.*转发.*揪.*', tcontent, re.DOTALL)
        matchobj_3 = re.match('.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_2 = re.match('.*评论区.{0,15}抽.*', tcontent, re.DOTALL)
        matchobj_1 = re.match('.*卷发.*关注.*', tcontent, re.DOTALL)
        matchobj = re.match('.*转发.*送.*', tcontent, re.DOTALL)
        matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent, re.DOTALL)
        matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent, re.DOTALL)
        matchobj2 = re.match('.*转.{0,7}评.*', tcontent, re.DOTALL)
        matchobj3 = re.match('.*本条.*送.*', tcontent, re.DOTALL)
        matchobj5 = re.match('.*抽.{0,10}送.*', tcontent, re.DOTALL)
        matchobj10 = re.match('.*钓鱼.*', tcontent, re.DOTALL)
        matchobj23 = re.match('.*关注.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj26 = re.match('.*生日直播.*上舰.*', tcontent, re.DOTALL)
        matchobj29 = re.match(
            '.*最大贝者场游戏规则公告大家以后要来碰碰运气一定要记住按照最后在碗里可见的卷数为准垫底的卷无效喔快来许愿碰碰运气吧.*',
            tcontent, re.DOTALL)
        matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent, re.DOTALL)
        matchobj34 = re.match('.*转发抽奖结果.*', tcontent, re.DOTALL)
        matchobj37 = re.match('.*奖品转送举报人.*', tcontent, re.DOTALL)
        matchobj39 = re.match('.*200元优惠券.*', tcontent, re.DOTALL)
        matchobj43 = re.match('.*不抽奖.*', tcontent, re.DOTALL)
        # matchobj44 = re.match('.*求点赞关注转发.*', tcontent, re.DOTALL)
        matchobj45 = re.match('.*置顶动态抽个元.*', tcontent, re.DOTALL)
        if (
                matchobj_100 == None and matchobj_99 == None and matchobj_98 == None and matchobj_97 == None and matchobj_96 == None and matchobj_95 == None and matchobj_94 == None and matchobj_93 == None and matchobj_92 == None and matchobj_91 == None and matchobj_90 == None and matchobj_89 == None and matchobj_88 == None and matchobj_87 == None and matchobj_86 == None and matchobj_85 == None and matchobj_84 == None and matchobj_83 == None and matchobj_82 == None and matchobj_81 == None and matchobj_80 == None and matchobj_79 == None and matchobj_78 == None and matchobj_77 == None and matchobj_76 == None and matchobj_75 == None and matchobj_74 == None and matchobj_73 == None and matchobj_72 == None and matchobj_71 == None and matchobj_70 == None and matchobj_69 == None and matchobj_68 == None and matchobj_67 == None and matchobj_65 == None and matchobj_64 == None and matchobj_63 == None and matchobj_62 == None and matchobj_61 == None and matchobj_60 == None and matchobj_59 == None and matchobj_58 == None and matchobj_57 == None and matchobj_56 == None and matchobj_55 == None and matchobj_54 == None and matchobj_53 == None and matchobj_52 == None and matchobj_51 == None and matchobj_50 == None and matchobj_49 == None and matchobj_48 == None and matchobj_47 == None and matchobj_46 == None and matchobj_45 == None and matchobj_44 == None and matchobj_43 == None and matchobj_42 == None and matchobj_41 == None and matchobj_40 == None and matchobj_39 == None and matchobj_38 == None and matchobj_37 == None and matchobj_36 == None
                and matchobj_34 == None and matchobj_33 == None and matchobj_32 == None and matchobj_31 == None
                and matchobj_30 == None and matchobj_29 == None and matchobj_28 == None and matchobj_27 == None
                and matchobj_26 == None and matchobj_25 == None and matchobj_24 == None and matchobj_23 == None
                and matchobj_22 == None and matchobj_21 == None and matchobj_20 == None and matchobj_19 == None
                and matchobj_18 == None and matchobj_17 == None and matchobj_16 == None and matchobj_15 == None
                and matchobj_14 == None and matchobj_13 == None and matchobj_12 == None and matchobj_11 == None
                and matchobj_10 == None and matchobj_9 == None and matchobj_8 == None and matchobj_7 == None
                and matchobj_6 == None and matchobj_4 == None and matchobj_3 == None
                and matchobj_2 == None and matchobj_1 == None and matchobj == None and matchobj0 == None
                and matchobj23 == None and matchobj1 == None and matchobj2 == None and matchobj3 == None
                and matchobj5 == None or matchobj10 != None or matchobj26 != None
                or matchobj29 != None or matchobj33 != None
                or matchobj34 != None or matchobj37 != None
                or matchobj39 != None
                or matchobj43 != None or matchobj45 != None):
            return 1
        return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1


if __name__ == '__main__':
    a=index()
    a.slash(300)
