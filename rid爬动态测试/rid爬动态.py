# -*- coding: utf-8 -*-
import json
import random
import re
import sys

sys.path.append('C:/pythontest/')
import time
import traceback
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
from pylangtools.langconv import Converter
import requests
import os
import Bilibili_methods.all_methods
import atexit

BAPI = Bilibili_methods.all_methods.methods()
ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'


class rid_get_dynamic:
    def __init__(self):

        self.EndTimeSeconds = 3 * 3600  # 提前多久退出爬动态
        self.highlight_word_list = ['jd卡', '京东卡', '红包', '主机', '显卡', '电脑', '天猫卡', '猫超卡', '现金',
                                    '见盘', '耳机', '鼠标', '手办', '景品', 'ps5', '内存', '风扇', '散热', '水冷',
                                    '主板', '电源', '机箱', 'fgo'
            , '折现', '樱瞳', '盈通', '🧧', '键盘']  # 需要重点查看的关键词列表
        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        ua3 = gl.get_value('ua3')

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
                exit('登陆失败,请重新登录')

        login_check(cookie3, ua3)
        atexit.register(self.quit)

        def get_attention(cookie, ua):
            url = 'https://api.vc.bilibili.com/feed/v1/feed/get_attention_list'
            headers = {
                'cookie': cookie,
                'user-agent': ua
            }
            req = requests.get(url=url, headers=headers)
            return req.json().get('data').get('list')

        self.followed_list = get_attention(cookie3, ua)  # 关注的列表
        print(f'共{len(self.followed_list)}个关注')
        self.list_type_wrong = list()
        self.list_deleted_maybe = list()
        self.rid = int()
        self.guanhao = dict()
        self.times = 1
        self.btime = 0
        self.n = int()
        self.dynamic_timestamp = int()
        self.type_wrong = None
        self.lottery = None
        self.op = None
        self.official = None
        self.official_lottery = None
        self.official_account = None
        self.deleted_maybe = None
        self.f = None
        self.getfail = None
        self.unknown = None
        # 文件

        self.list_lottery = list()
        self.list_op = list()  # 总计
        self.list_official = list()
        self.list_official_lottery = list()
        self.list_f = list()  # 每日
        self.list_getfail = list()
        self.list_unknown = list()

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
        if self.list_deleted_maybe:
            my_write(self.deleted_maybe, self.list_deleted_maybe)
        if self.list_f:
            my_write(self.f, self.list_f)
        if self.list_getfail:
            my_write(self.getfail, self.list_getfail)
        if self.list_unknown:
            my_write(self.unknown, self.list_unknown)
        if self.list_type_wrong:
            my_write(self.type_wrong, self.list_type_wrong)

    def contentshow(self, _type, card, dynamicint):
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
        try:
            dycode = req1_dict.get('code')
        except Exception as e:
            dycode = 404
            print(req1_dict)
            print('code获取失败')
        self.code_check(req1_dict)
        print('\n\t\t\t\t第' + str(self.times) + '次获取动态\t' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        print('\t\t\t\trid:{}'.format(self.rid))
        print('\n')
        self.times += 1
        dymsg = req1_dict.get('msg')
        dymessage = req1_dict.get('message')
        dydata = req1_dict.get('data')
        try:
            dynamicid = req1_dict.get('data').get('card').get('desc').get('dynamic_id')
        except Exception as e:  # {'code': 0, 'msg': '', 'message': '', 'data': {'_gt_': 0}}#type可能出错了
            if req1_dict.get('code') == 0 and req1_dict.get('msg') == '' and req1_dict.get('message') == '':
                self.list_type_wrong.append(
                    f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            dynamicid = 'None'
            print(e)
            print(req1_dict)
            print('遇到动态类型可能出错的动态\n')
            print(BAPI.timeshift(time.time()))
            # traceback.print_exc()
        print('https://t.bilibili.com/' + str(dynamicid) + '?tab=2')
        if dycode == 404:
            print(dycode, dymsg, dymessage)
            codelist = [dycode, dynamicid, dydata, req1_dict]
            self.list_getfail.append(str(codelist) + '\t' + str(req1_dict) + '\n')
            self.code_check(dycode)
            return
        if dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
        if dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
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
                if _type == 2:
                    self.dynamic_timestamp = timestamp
                realtime = BAPI.timeshift(timestamp)
                card = json.loads(dydata.get('card').get('card'))
                print('用户昵称：' + uname)
                print(BAPI.timeshift(timestamp))
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
                print(BAPI.timeshift(time.time()))
                # traceback.print_exc()
            dynamic_content = Converter('zh-hans').convert(self.contentshow(_type, card, dynamicint))
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
                    if not BAPI.choujiangxinxipanduan(dynamic_content):
                        self.list_official_lottery.append(
                            str(uid) + '\t' + uname + '\t' + str(fans) + '\t' + str(level) + '\t' + repr(
                                str(dynamic_content)) + '\t' + str(comment) + '\t' + str(repost) + '\t' + str(
                                jumpurl) + '\t' + str(
                                realtime) + '\t' + str(uid) + '\n')

            followed_falg = ''
            highlight_word = []
            for word in self.highlight_word_list:
                if word.lower() in dynamic_content.lower():
                    highlight_word.append(word)
            highlight_word = '；'.join(highlight_word)
            if uid in self.followed_list:
                followed_falg = 'followed_uid'

            append_data_str = f'{uname}\t{str(jumpurl)}\t{self.rid}\t{repr(str(dynamic_content))}\t{str(realtime)}\t{str(comment)}\t{str(repost)}\t{str(official)}\t{str(uid)}\t{followed_falg}\t{highlight_word}\t{picture_list[0]}\t{picture_list[1]}\t{picture_list[2]}\t{picture_list[3]}\t{picture_list[4]}\t{picture_list[5]}\t{picture_list[6]}\t{picture_list[7]}\t{picture_list[8]}\n'  # 写入文件的格式

            if not BAPI.choujiangxinxipanduan(dynamic_content):
                self.list_lottery.append(append_data_str)
                self.list_f.append(append_data_str)
            if uname != 'None':
                self.list_op.append(append_data_str)
            self.code_check(dycode)
            return
        if dycode == -412:
            self.code_check(dycode)
            print(req1_dict)
            self.list_getfail.append(str(BAPI.timeshift(time.time())) + '\t' + str(req1_dict) + '\n')
            return
        if dycode != 0:
            self.list_unknown.append('{}：{}\n'.format(BAPI.timeshift(time.time()), req1_dict))
        return

    def resolve_album(self,req1_dict):
        try:
            dycode = req1_dict.get('code')
        except Exception as e:
            dycode = 404
            print(req1_dict)
            print('code获取失败')
        self.code_check(req1_dict)
        print('\n\t\t\t\t第' + str(self.times) + '次获取动态\t' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        print('\t\t\t\trid:{}'.format(self.rid))
        print('\n')
        self.times += 1
        dymsg = req1_dict.get('msg')
        dymessage = req1_dict.get('message')
        dydata = req1_dict.get('data')
        try:
            dynamicid = req1_dict.get('data').get('card').get('desc').get('dynamic_id')
        except Exception as e:  # {'code': 0, 'msg': '', 'message': '', 'data': {'_gt_': 0}}#type可能出错了
            if req1_dict.get('code') == 0 and req1_dict.get('msg') == '' and req1_dict.get('message') == '':
                self.list_type_wrong.append(
                    f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            dynamicid = 'None'
            print(e)
            print(req1_dict)
            print('遇到动态类型可能出错的动态\n')
            print(BAPI.timeshift(time.time()))
            # traceback.print_exc()
        print('https://t.bilibili.com/' + str(dynamicid) + '?tab=2')
        if dycode == 404:
            print(dycode, dymsg, dymessage)
            codelist = [dycode, dynamicid, dydata, req1_dict]
            self.list_getfail.append(str(codelist) + '\t' + str(req1_dict) + '\n')
            self.code_check(dycode)
            return
        if dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
        if dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
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
                if _type == 2:
                    self.dynamic_timestamp = timestamp
                realtime = BAPI.timeshift(timestamp)
                card = json.loads(dydata.get('card').get('card'))
                print('用户昵称：' + uname)
                print(BAPI.timeshift(timestamp))
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
                print(BAPI.timeshift(time.time()))
                # traceback.print_exc()
            dynamic_content = Converter('zh-hans').convert(self.contentshow(_type, card, dynamicint))
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
                    if not BAPI.choujiangxinxipanduan(dynamic_content):
                        self.list_official_lottery.append(
                            str(uid) + '\t' + uname + '\t' + str(fans) + '\t' + str(level) + '\t' + repr(
                                str(dynamic_content)) + '\t' + str(comment) + '\t' + str(repost) + '\t' + str(
                                jumpurl) + '\t' + str(
                                realtime) + '\t' + str(uid) + '\n')

            followed_falg = ''
            highlight_word = []
            for word in self.highlight_word_list:
                if word.lower() in dynamic_content.lower():
                    highlight_word.append(word)
            highlight_word = '；'.join(highlight_word)
            if uid in self.followed_list:
                followed_falg = 'followed_uid'

            append_data_str = f'{uname}\t{str(jumpurl)}\t{self.rid}\t{repr(str(dynamic_content))}\t{str(realtime)}\t{str(comment)}\t{str(repost)}\t{str(official)}\t{str(uid)}\t{followed_falg}\t{highlight_word}\t{picture_list[0]}\t{picture_list[1]}\t{picture_list[2]}\t{picture_list[3]}\t{picture_list[4]}\t{picture_list[5]}\t{picture_list[6]}\t{picture_list[7]}\t{picture_list[8]}\n'  # 写入文件的格式

            if not BAPI.choujiangxinxipanduan(dynamic_content):
                self.list_lottery.append(append_data_str)
                self.list_f.append(append_data_str)
            if uname != 'None':
                self.list_op.append(append_data_str)
            self.code_check(dycode)
            return
        if dycode == -412:
            self.code_check(dycode)
            print(req1_dict)
            self.list_getfail.append(str(BAPI.timeshift(time.time())) + '\t' + str(req1_dict) + '\n')
            return
        if dycode != 0:
            self.list_unknown.append('{}：{}\n'.format(BAPI.timeshift(time.time()), req1_dict))
        return
    def code_check(self, dycode):
        if self.btime > 500:
            self.quit()
        try:
            if dycode == 404:
                self.btime += 1
                return 0
        except Exception as e:
            print(dycode)
            print('未知类型代码')
            print(e)
        try:
            if dycode == 500205:
                self.btime += 1
                return 0
            else:
                self.btime = 0
        except Exception as e:
            print(dycode)
            print('未知类型代码')
            print(e)
        if dycode == -412:
            print('-412报错,休息20分钟')
            print(BAPI.timeshift(time.time()))
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(20 * 60)
            return -412
        elif dycode != 'None' and dycode != 500207 and \
                dycode != 500205 and dycode != 404 and dycode != -412 and self.dynamic_timestamp != 'None':
            if int(time.time()) - self.dynamic_timestamp < self.EndTimeSeconds:
                print(f'已获取到最近{self.EndTimeSeconds // 60}分钟为止的动态')
                print('rid记录回滚10000条')
                self.rid -= 10000
                self.quit()

    def quit(self):
        """
            退出时必定执行
        """
        if self.rid:
            ridstartfile = open('ridstart.txt', 'w')
            ridstartfile.write(str(self.rid - 5000))
            ridstartfile.close()
        print('共' + str(self.times - 1) + '次获取动态')
        print('其中' + str(self.n) + '个有效动态')
        self.write_in_file()
        self.lottery.close()
        self.op.close()
        self.official.close()
        self.official_lottery.close()
        self.official_account.close()
        self.f.close()
        self.getfail.close()
        self.unknown.close()
        # os.system('shutdown /s /t 3600')
        # os.system('shutdown /s /t 60')
        exit(10)

    def get_pinglunreq(self, dynamic_id, rid, pn, _type, *mode):
        if mode:
            mode = mode[0]
        else:
            mode = 2
        ctype = 17
        if str(_type) == '8':
            ctype = 1
        elif str(_type) == '4' or str(_type) == '1':
            ctype = 17
        elif str(_type) == '2':
            ctype = 11
        elif str(_type) == '64':
            ctype = 12
        if len(rid) == len(dynamic_id):
            oid = dynamic_id
        else:
            oid = rid
        fakeuseragent = random.choice(BAPI.User_Agent_List)
        pinglunheader = {
            'user-agent': fakeuseragent}
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=' + str(mode) + '&plat=1&_=' + str(time.time())
        pinglundata = {
            'jsonp': 'jsonp',
            'next': pn,
            'type': ctype,
            'oid': oid,
            'mode': mode,
            'plat': 1,
            '_': time.time()
        }
        try:
            pinglunreq = requests.request("GET", url=pinglunurl, data=pinglundata, headers=pinglunheader)
        except Exception as e:
            print(e)
            print('获取评论失败,休息10分钟')
            print(BAPI.timeshift(int(time.time())))
            while 1:
                try:
                    time.sleep(10 * 60)
                    # time.sleep(eval(input('输入等待时间')))
                    break
                except:
                    continue
            pinglunreq = self.get_pinglunreq(dynamic_id, rid, pn, _type)
            return pinglunreq
        return pinglunreq.text

    def get_topcomment(self, dynamicid, rid, pn, type, mid):
        iner_replies = ''
        pinglunreq = self.get_pinglunreq(dynamicid, rid, pn, type, 3)
        try:
            pinglun_dict = json.loads(pinglunreq)
            pingluncode = pinglun_dict.get('code')
            if pingluncode != 0:
                print('获取置顶评论失败')
                message = pinglun_dict.get('message')
                print(message)
                if message != 'UP主已关闭评论区' and message != '啥都木有' and message != '评论区已关闭':
                    while 1:
                        try:
                            time.sleep(eval(input('输入等待时间')))
                            break
                        except:
                            continue
                    return 'null'
                else:
                    print(message)
                    return 'null'
            reps = pinglun_dict.get('data').get('replies')
            if reps != None:
                for i in reps:
                    pinglun_mid = i.get('mid')
                    if pinglun_mid == mid:
                        iner_replies += i.get('content').get('message')
            data = pinglun_dict.get('data')
            topreplies = data.get('top_replies')
            if topreplies != None:
                topmsg = topreplies[0].get('content').get('message') + iner_replies
                print('置顶评论：' + topmsg)
            else:
                print('无置顶评论')
                topmsg = 'null' + iner_replies
        except Exception as e:
            print(e)
            print('获取置顶评论失败')
            pinglun_dict = json.loads(pinglunreq)
            data = pinglun_dict.get('data')
            print(pinglun_dict)
            print(data)
            topmsg = 'null'
            print(BAPI.timeshift(int(time.time())))
            if data == '评论区已关闭':
                topmsg = data
            else:
                while 1:
                    try:
                        time.sleep(eval(input('输入等待时间')))
                        break
                    except:
                        continue
        return topmsg

    def get_dynamic(self):
        while 1:
            if self.times % 100 != 0:
                self.resolve_dynamic(BAPI.rid_dynamic(self.rid))
                self.rid += 1
                time.sleep(2)
            else:
                self.resolve_dynamic(BAPI.rid_dynamic(self.rid))
                self.rid += 1
                time.sleep(1)
                if len(self.list_op) > 10000:
                    self.write_in_file()
                    print('\n\n\t\t\t\t写入文件\n')
                print('每100个休眠20秒')
                time.sleep(19)

    def init(self):
        try:
            self.unknown = open('log/未知类型.csv', 'a+', encoding='utf-8')
        except:
            self.unknown = open('log/未知类型.csv', 'w', encoding='utf-8')
        try:
            self.lottery = open('rid疑似抽奖动态.csv', 'a+', encoding='utf-8')
        except:
            self.lottery = open('rid疑似抽奖动态.csv', 'w', encoding='utf-8')
        try:
            self.op = open('rid总计.csv', 'a+', encoding='utf-8')
        except:
            self.op = open('rid总计.csv', 'w', encoding='utf-8')
        try:
            self.getfail = open('log/获取失败rid动态.csv', 'a+', encoding='utf-8')
        except:
            self.getfail = open('log/获取失败rid动态.csv', 'w', encoding='utf-8')
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
        try:
            self.deleted_maybe = open('log/可能被删的.csv', 'a+', encoding='utf-8')
        except:
            self.deleted_maybe = open('log/可能被删的.csv', 'w', encoding='utf-8')
        try:
            self.type_wrong = open('log/可能动态类型出错的.csv', 'a+', encoding='utf-8')
        except:
            self.type_wrong = open('log/可能动态类型出错的.csv', 'w', encoding='utf-8')
        try:
            ridstartfile = open('ridstart.txt', 'r')
            self.rid = int(ridstartfile.readline())
            ridstartfile.close()
            print('获取rid开始文件成功\nrid开始值：{}'.format(self.rid))
            if self.rid <= 0:
                print('获取rid开始文件失败')
                sys.exit('获取rid开始文件失败')
        except:
            print('获取rid开始文件失败')
            sys.exit('获取rid开始文件失败')


if __name__ == "__main__":
    rid_run = rid_get_dynamic()
    rid_run.init()
    rid_run.get_dynamic()
