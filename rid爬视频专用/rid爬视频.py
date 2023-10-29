# -*- coding: utf-8 -*-
import json
import random
import re
import time
import traceback

from pylangtools.langconv import Converter
import requests
import os
import Bilibili_methods.all_methods
import atexit

BAPI = Bilibili_methods.all_methods.methods()
ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'


class rid_get_dynamic:
    def __init__(self):
        atexit.register(self.quit)
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
        self.list_op = list()
        self.list_official = list()
        self.list_official_lottery = list()
        self.list_f = list()
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

    def choujiangxinxipanduan(self, tcontent):  # 动态内容过滤条件
        matchobj_96 = re.match('.*开奖.*', tcontent, re.DOTALL)
        matchobj_95 = re.match('.*抽.*', tcontent, re.DOTALL)
        matchobj_94 = re.match('.*留言.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_93 = re.match('.*评论.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_92 = re.match('.*失物招领.*', tcontent, re.DOTALL)
        matchobj_91 = re.match('.*抽个奖.*', tcontent, re.DOTALL)
        matchobj_90 = re.match('.*roll.*', tcontent, re.DOTALL)
        matchobj_89 = re.match('.*本.{0,10}动态.{0,10}抽.*', tcontent, re.DOTALL)
        matchobj_88 = re.match('.*关.{0,10}评.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_87 = re.match('.*赞.{0,10}评.{0,10}转.*', tcontent, re.DOTALL)
        matchobj_86 = re.match('.*注.{0,3}发.*', tcontent, re.DOTALL)
        matchobj_85 = re.match('.*转.{0,10}关.*抽.*', tcontent, re.DOTALL)
        matchobj_84 = re.match('.*送.*关.{0,10}转.*', tcontent, re.DOTALL)
        matchobj_83 = re.match('.*转.{0,10}关.{0,10}福利.*', tcontent, re.DOTALL)
        matchobj_82 = re.match('.*抽.{0,10}奖.*', tcontent, re.DOTALL)
        matchobj_81 = re.match('.*关注.*roll.*', tcontent, re.DOTALL)
        matchobj_80 = re.match('.*roll.*关注.*', tcontent, re.DOTALL)
        matchobj_79 = re.match('.*转.*关.{0,10}赠.*', tcontent, re.DOTALL)
        matchobj_78 = re.match('.*关注.*评论.{0,10}转发.*', tcontent, re.DOTALL)
        matchobj_77 = re.match('.*抽.{0,10}体验.*', tcontent, re.DOTALL)
        matchobj_76 = re.match('.*揪.{0,10}奖励.*', tcontent, re.DOTALL)
        matchobj_75 = re.match('.*roll.*', tcontent, re.DOTALL)
        matchobj_74 = re.match('.*转发.{0,10}参与.*', tcontent, re.DOTALL)
        matchobj_73 = re.match('.*抓.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_72 = re.match('.*动态抽奖.*', tcontent, re.DOTALL)
        matchobj_71 = re.match('.*转.*关.*抽.{0,15}送.*', tcontent, re.DOTALL)
        matchobj_70 = re.match('.*关注.{0,9}惊喜.*', tcontent, re.DOTALL)
        matchobj_69 = re.match('.*揪.{0,9}喝奶.*', tcontent, re.DOTALL)
        matchobj_68 = re.match('.*抽.{0,9}得到.*', tcontent, re.DOTALL)
        matchobj_67 = re.match('.*抽.{0,9}获得.*', tcontent, re.DOTALL)
        matchobj_66 = re.match('.*看.{0,9}图.*', tcontent, re.DOTALL)
        matchobj_65 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_64 = re.match('.*抽奖.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*补贴.*\\d+.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*卷.{0,9}抽.*送.*', tcontent, re.DOTALL)
        matchobj_59 = re.match('.*车.{0.10}关.*', tcontent, re.DOTALL)
        matchobj_58 = re.match('.*评论.{0,9}揪.*', tcontent, re.DOTALL)
        matchobj_57 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_56 = re.match('.*关注.{0,10}评论.{20}揪', tcontent, re.DOTALL)
        matchobj_55 = re.match('.*车专.*关.*', tcontent, re.DOTALL)
        matchobj_54 = re.match('.*评论.{0,20}白嫖.*', tcontent, re.DOTALL)
        matchobj_53 = re.match('.*评论.{0,10}.*抽.*', tcontent, re.DOTALL)
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
        matchobj_5 = re.match('.*转.*评.*送.*鲨鲨酱抱枕.*', tcontent, re.DOTALL)
        matchobj_4 = re.match('.*转发.*揪.*', tcontent, re.DOTALL)
        matchobj_3 = re.match('.*揪.*送.*', tcontent, re.DOTALL)
        matchobj_2 = re.match('.*评论区.{0,15}抽.*', tcontent, re.DOTALL)
        matchobj_1 = re.match('.*卷发.*关注.*', tcontent, re.DOTALL)
        matchobj = re.match('.*转发.*送.*', tcontent, re.DOTALL)
        matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent, re.DOTALL)
        matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent, re.DOTALL)
        matchobj2 = re.match('.*转.{0,10}评.*', tcontent, re.DOTALL)
        matchobj3 = re.match('.*本条.*送.*', tcontent, re.DOTALL)
        matchobj5 = re.match('.*抽.{0,15}送.*', tcontent, re.DOTALL)
        matchobj10 = re.match('.*钓鱼.*', tcontent, re.DOTALL)
        matchobj23 = re.match('.*关注.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj28 = re.match('.*开奖.*恭喜.*获得.*', tcontent, re.DOTALL)
        matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent, re.DOTALL)
        matchobj40 = re.match('.*恭喜.*中奖.*', tcontent, re.DOTALL)
        matchobj43 = re.match('.*不抽奖.*', tcontent, re.DOTALL)
        matchobj45 = re.match('.*置顶动态抽个元.*', tcontent, re.DOTALL)
        matchobj46 = re.match('.*开奖.*祝贺.*获得.*', tcontent, re.DOTALL)
        if (
                matchobj_96 == None and matchobj_95 == None and matchobj_94 == None and matchobj_93 == None and matchobj_92 == None and matchobj_91 == None and matchobj_90 == None and matchobj_89 == None and matchobj_88 == None and matchobj_87 == None and matchobj_86 == None and matchobj_85 == None and matchobj_84 == None and matchobj_83 == None and matchobj_82 == None and matchobj_81 == None and matchobj_80 == None and matchobj_79 == None and matchobj_78 == None and matchobj_77 == None and matchobj_76 == None and matchobj_75 == None and matchobj_74 == None and matchobj_73 == None and matchobj_72 == None and matchobj_71 == None and matchobj_70 == None and matchobj_69 == None and matchobj_68 == None and matchobj_67 == None and matchobj_66 == None and matchobj_65 == None and matchobj_64 == None and matchobj_63 == None and matchobj_62 == None and matchobj_61 == None and matchobj_60 == None and matchobj_59 == None and matchobj_58 == None and matchobj_57 == None and matchobj_56 == None and matchobj_55 == None and matchobj_54 == None and matchobj_53 == None and matchobj_52 == None and matchobj_51 == None and matchobj_50 == None and matchobj_49 == None and matchobj_48 == None and matchobj_47 == None and matchobj_46 == None and matchobj_45 == None and matchobj_44 == None and matchobj_43 == None and matchobj_42 == None and matchobj_41 == None and matchobj_40 == None and matchobj_39 == None and matchobj_38 == None and matchobj_37 == None and matchobj_36 == None
                and matchobj_34 == None and matchobj_33 == None and matchobj_32 == None and matchobj_31 == None
                and matchobj_30 == None and matchobj_29 == None and matchobj_28 == None and matchobj_27 == None
                and matchobj_26 == None and matchobj_25 == None and matchobj_24 == None and matchobj_23 == None
                and matchobj_22 == None and matchobj_21 == None and matchobj_20 == None and matchobj_19 == None
                and matchobj_18 == None and matchobj_17 == None and matchobj_16 == None and matchobj_15 == None
                and matchobj_14 == None and matchobj_13 == None and matchobj_12 == None and matchobj_11 == None
                and matchobj_10 == None and matchobj_9 == None and matchobj_8 == None and matchobj_7 == None
                and matchobj_6 == None and matchobj_5 == None and matchobj_4 == None and matchobj_3 == None
                and matchobj_2 == None and matchobj_1 == None and matchobj == None and matchobj0 == None
                and matchobj23 == None and matchobj1 == None and matchobj2 == None and matchobj3 == None
                and matchobj5 == None or matchobj10 != None
                or matchobj28 != None or matchobj33 != None or matchobj40 != None
                or matchobj43 != None or matchobj45 != None or matchobj46 != None):
            return 1
        return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1

    def resolve_dynamic(self, req1_dict):
        try:
            dycode = req1_dict.get('code')
        except Exception as e:
            dycode = 404
            print(req1_dict)
            print('code获取失败')
        print('\n\t\t\t\t第' + str(self.times) + '次获取动态')
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
        elif dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
        elif dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
            self.list_deleted_maybe.append(
                f'{req1_dict}\thttps://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={self.rid}&type=\n')
            self.code_check(dycode)
            return
        elif dycode != 0:
            self.code_check(dycode)
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
                    if not self.choujiangxinxipanduan(dynamic_content):
                        self.list_official_lottery.append(
                            str(uid) + '\t' + uname + '\t' + str(fans) + '\t' + str(level) + '\t' + repr(
                                str(dynamic_content)) + '\t' + str(comment) + '\t' + str(repost) + '\t' + str(
                                jumpurl) + '\t' + str(
                                realtime) + '\t' + str(uid) + '\n')

            append_data_str = f'{uname}\t{str(jumpurl)}\t{self.rid}\t{repr(str(dynamic_content))}\t{str(realtime)}\t{str(comment)}\t{str(repost)}\t{str(official)}\t{str(uid)}\t{picture_list[0]}\t{picture_list[1]}\t{picture_list[2]}\t{picture_list[3]}\t{picture_list[4]}\t{picture_list[5]}\t{picture_list[6]}\t{picture_list[7]}\t{picture_list[8]}\n'  # 写入文件的格式

            if not self.choujiangxinxipanduan(dynamic_content):
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
        print('检查响应码：', dycode)
        print('当前btime：', self.btime)
        if self.btime >= 500:
            self.rid -= 5000
            self.quit()
        try:
            if dycode == 404:
                self.btime += 1
                return 0
        except Exception as e:
            print(dycode)
            print('未知类型代码')
            print(e)
        if dycode == 500205:
            self.btime += 1
            return 0
        else:
            self.btime = 0
        if dycode == -412:
            print('412报错')
            print(BAPI.timeshift(time.time()))
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(60 * 60)
            return -412
        elif dycode != 'None' and dycode != 500207 and \
                dycode != 500205 and dycode != 404 and dycode != -412 and self.dynamic_timestamp != 'None':
            if int(time.time()) - self.dynamic_timestamp < 60 * 60:
                print('已获取到最近60分钟为止的动态')
                print('rid记录回滚10000条')
                self.rid -= 10000
                self.quit()

    def quit(self):
        """
            退出时必定执行
        """
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
        #os.system('python ../rid爬动态测试/rid爬动态.py')
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
            print('获取评论失败')
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

    def get_topcomment(self, dynamicid, rid, pn, _type, mid):
        iner_replies = ''
        pinglunreq = self.get_pinglunreq(dynamicid, rid, pn, _type, 3)
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
            if self.times % 1000 != 0:
                self.resolve_dynamic(BAPI.rid_dynamic_video(self.rid))
                self.rid += 1
            else:
                self.resolve_dynamic(BAPI.rid_dynamic_video(self.rid))
                self.rid += 1
                time.sleep(1)
                if len(self.list_op) > 10000:
                    self.write_in_file()
                    print('\n\n\t\t\t\t写入文件\n')
                time.sleep(4)

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
            self.getfail = open('获取失败rid动态.csv', 'a+', encoding='utf-8')
        except:
            self.getfail = open('获取失败rid动态.csv', 'w', encoding='utf-8')
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
            self.deleted_maybe = open('可能被删的.csv', 'a+', encoding='utf-8')
        except:
            self.deleted_maybe = open('可能被删的.csv', 'w', encoding='utf-8')
        try:
            self.type_wrong = open('可能动态类型出错的.csv', 'a+', encoding='utf-8')
        except:
            self.type_wrong = open('可能动态类型出错的.csv', 'w', encoding='utf-8')
        try:
            ridstartfile = open('ridstart.txt', 'r')
            self.rid = int(ridstartfile.readline())
            ridstartfile.close()
            print('获取rid开始文件成功\nrid开始值：{}'.format(self.rid))
        except:
            print('获取rid开始文件失败')
            self.rid = 189485985


if __name__ == "__main__":
    rid_run = rid_get_dynamic()
    rid_run.init()
    rid_run.get_dynamic()
