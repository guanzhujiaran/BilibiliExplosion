# -*- coding:utf-8 -*-
import random
import re
import time
import opencc
import numpy
import requests
from Utils.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
up_nickname_dict = {}
kongpinglun = '⁡'
converter = opencc.OpenCC('t2s.json')

class methods:
    def __init__(self):
        self.requests_with_proxy = request_with_proxy_internal
        self.copy_suffix = ['']  # 复制后缀
        self.changyongemo = []  # 常用的表情包
        self._at_member = []
        self.username = ''  # 自己账号的名字，默认为空
        self.caihongpi_chance = 0  # 对官方使用彩虹屁的概率，数字越大，彩虹屁频率越高
        self.repostchance = 0.5  # 转发动态时，转发内容为评论内容的几率
        self.pinglunzhuanbiancishu = 5  # 获取评论时失败重新尝试的次数
        self.chance_shangjiayingguang = 0  # 随机挑线自定义商家广告回复词的概率
        self.chance_copy_comment = 0  # 抄评论的概率
        self.range_copy_comment = 1  # 抄评论的长度在20条评论评均长度的比率，数字越大，抄的评论越长
        self.non_official_chp_chance = 0  # 对非官方使用cph评论的概率
        self.sleeptime = numpy.linspace(1, 3, 500, endpoint=False)
        self.replycontent = []  # 默认回复内容
        self.dianzanshibai = list()
        self.zhuanfashibai = list()
        self.pinglunshibai = list()
        self.guanzhushibai = list()
        self.official_caihongpilist = []
        self.non_official_chp = []
        self.shangjiayingguang = []
        self.xiaoweiba = ['']
        self.xiaoweibawenan = []
        self.None_nickname = list()
        self.hasemo = []  # 拥有的表情包
        self.s = requests.session()

    @property
    def at_member(self):
        return self._at_member or ['陈睿']

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def choujiangxinxipanduan(self, tcontent):  # 动态内容过滤条件
        '''
        相对粗略
        抽奖信息判断      是抽奖返回None 不是抽奖返回1
        :param tcontent:
        :return:
        '''
        tcontent = re.sub(r'@(.{0,12}?) ', '', tcontent)
        tcontent = converter.convert(tcontent)
        tcontent = tcontent.lower()
        tcontent = tcontent.replace(' ', '')
        tcontent = tcontent.replace('传送门', '')
        tcontent = tcontent.replace('车+关', '转+关')
        tcontent = tcontent.replace('lun', '论')
        tcontent = tcontent.replace('车专', '转')
        tcontent = tcontent.replace('扌由', '抽')
        tcontent = tcontent.replace('🧱', '转')
        tcontent = tcontent.replace('🍎', '评')
        tcontent = tcontent.replace('🐷', '关注')
        tcontent = tcontent.replace('卷', '转')
        tcontent = tcontent.replace('苹', '评')
        tcontent = tcontent.replace('平', '评')
        tcontent = tcontent.replace('留言', '评论')
        tcontent = tcontent.replace('选出', '抽')
        tcontent = tcontent.replace('选取', '抽')
        tcontent = tcontent.replace('揪', '抽')
        tcontent = tcontent.replace('抽时间', '')
        tcontent = tcontent.replace('null', '')
        matchobj_101 = re.match(
            '.*挑选.{0,10}送.*|.*评论.{0,20}获得.*|.*粉丝福利.{0,10}送.*|.*参与方式.{0,15}评.*|.*参与方式.{0,15}转.*|.*【抽】.*|.*内含巨大福利',
            tcontent, re.DOTALL)
        matchobj_100 = re.match(
            '.*转.{0,10}关.{0,10}送.*|.*关.{0,10}转.{0,10}送.*|.*送.{0,10}关.{0,10}转.*|.*送.{0,10}转.{0,10}关.*',
            tcontent, re.DOTALL)
        matchobj_99 = re.match(
            '.*抽.{0,10}转|.*抽.{0,10}v|.*抽.{0,5}赞.{0,5}评|.*评.{0,5}抽.{0,5}赞|.*赞.{0,5}评.{0,5}抽', tcontent,
            re.DOTALL)
        matchobj_98 = re.match('.*抽.{0,5}个|.*抽.{0,5}位|.*抽.{0,5}名', tcontent, re.DOTALL)
        matchobj_97 = re.match('.*有奖互动.*', tcontent, re.DOTALL)
        matchobj_96 = re.match(
            '.*转.{0,10}关.{0,10}参.*|.*关.{0,10}转.{0,10}参.*|.*参.{0,10}关.{0,10}转.*|.*转.{0,10}参.{0,10}关.*',
            tcontent, re.DOTALL)
        matchobj_95 = re.match('.*安排.*评论.*', tcontent, re.DOTALL)
        matchobj_94 = re.match('.*抽奖.*', tcontent, re.DOTALL)
        matchobj_93 = re.match('.*抽奖.*参与.*', tcontent, re.DOTALL)
        matchobj_91 = re.match('.*倒霉蛋.*', tcontent, re.DOTALL)
        matchobj_90 = re.match('.*懂的.*|.*懂得都懂|.*dddd|.*懂的都懂|.*寻找失主|.*大拇哥.{0,5}认领', tcontent,
                               re.DOTALL)
        matchobj_89 = re.match('.*留言.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_88 = re.match('.*评论.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_87 = re.match('.*失物招领.*', tcontent, re.DOTALL)
        matchobj_86 = re.match('.*抽个奖.*', tcontent, re.DOTALL)
        matchobj_85 = re.match('.*r.{0,3}o.{0,3}l.{0,3}l.*', tcontent, re.DOTALL)
        matchobj_84 = re.match('.*本.{0,10}动态.{0,10}抽.*', tcontent, re.DOTALL)
        matchobj_83 = re.match('.*关.{0,10}评.{0,10}送.*|.*评.*抽.*', tcontent, re.DOTALL)
        matchobj_82 = re.match('.*赞.{0,10}评.{0,10}转.*', tcontent, re.DOTALL)
        matchobj_81 = re.match('.*注.{0,3}发.*', tcontent, re.DOTALL)
        matchobj_80 = re.match('.*转.{0,10}关.*抽.*', tcontent, re.DOTALL)
        matchobj_79 = re.match('.*关注.*roll.*', tcontent, re.DOTALL)
        matchobj_78 = re.match('.*roll.*关注.*', tcontent, re.DOTALL)
        matchobj_77 = re.match('.*找.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_76 = re.match('.*关注.*评论.{0,10}转发.*', tcontent, re.DOTALL)
        matchobj_75 = re.match('.*抽.{0,10}体验.*', tcontent, re.DOTALL)
        matchobj_74 = re.match('.*抽.{0,10}奖励.*', tcontent, re.DOTALL)
        matchobj_73 = re.match('.*抓.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_72 = re.match('.*动态抽奖.*', tcontent, re.DOTALL)
        matchobj_71 = re.match('.*转.*关.*抽.{0,15}送.*', tcontent, re.DOTALL)
        matchobj_70 = re.match('.*关注.{0,9}有惊喜.*', tcontent, re.DOTALL)
        matchobj_69 = re.match('.*抽.{0,9}喝奶.*', tcontent, re.DOTALL)
        matchobj_68 = re.match('.*抽.{0,9}得到.*', tcontent, re.DOTALL)
        matchobj_67 = re.match('.*抽.{0,9}获得.*', tcontent, re.DOTALL)
        matchobj_65 = re.match('.*抽奖.{0,10}送.*',tcontent, re.DOTALL)
        matchobj_64 = re.match(r'.*评论.{0,10}补贴.*\d+.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*抽.{0,10}带走.*', tcontent, re.DOTALL)
        matchobj_59 = re.match(r'.*补贴.{0,10}\d+元.*', tcontent, re.DOTALL)
        matchobj_58 = re.match('.*转{0,10}抽.*送.*', tcontent, re.DOTALL)
        matchobj_57 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_56 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_55 = re.match('.*关注.{0,10}评论', tcontent, re.DOTALL)
        matchobj_54 = re.match('.*评论.{0,5}白.{0,10}嫖.*', tcontent, re.DOTALL)
        matchobj_53 = re.match('.*车专.*关.*', tcontent, re.DOTALL)
        matchobj_52 = re.match('.*评论.*抽.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_51 = re.match('.*评论.*抽.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_50 = re.match('.*转.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_49 = re.match('.*抽1位50元红包.*', tcontent, re.DOTALL)
        matchobj_48 = re.match('.*抽.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_47 = re.match('.*抽.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_46 = re.match('.*抽奖.*抽.*小伙伴.*评论.*转发.*', tcontent, re.DOTALL)
        matchobj_45 = re.match('.*关注.*一键三连.*分享.*送.*', tcontent, re.DOTALL)
        matchobj_44 = re.match('.*抽.{0,10}小可爱.*每人.*', tcontent, re.DOTALL)
        matchobj_43 = re.match('.*#抽奖#.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_42 = re.match('.*关注.*平论.*抽.*打.*', tcontent, re.DOTALL)
        matchobj_41 = re.match('.*转发.*评论.*关注.*抽.*获得.*', tcontent, re.DOTALL)
        matchobj_40 = re.match('.*关注.*转发.*点赞.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_39 = re.match('.*转发评论点赞本条动态.*送.*', tcontent, re.DOTALL)
        matchobj_38 = re.match('.*挑选.*评论.*送出.*', tcontent, re.DOTALL)
        matchobj_37 = re.match('.*弹幕抽.*送.*', tcontent, re.DOTALL)
        matchobj_36 = re.match('.*随机.*位小伙伴.*现金红包.*', tcontent, re.DOTALL)
        matchobj_34 = re.match('.*评论.*随机.*抽.*', tcontent, re.DOTALL)
        matchobj_33 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_32 = re.match('.*参与方式.*转发.*关注.*评论.*', tcontent, re.DOTALL)
        matchobj_31 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_30 = re.match('.*评论.*随机.*抽.*补贴.*', tcontent, re.DOTALL)
        matchobj_29 = re.match('.*评论区.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_28 = re.match('.*转发.*评论.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_27 = re.match('.*互动抽奖.*', tcontent, re.DOTALL)
        matchobj_26 = re.match('.*#供电局福利社#.*', tcontent, re.DOTALL)
        matchobj_25 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_24 = re.match('.*转发.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_23 = re.match('.*关注.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_22 = re.match('.*评论.*转发.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_21 = re.match('.*有奖转发.*', tcontent, re.DOTALL)
        matchobj_20 = re.match('.*评论就有机会抽.*', tcontent, re.DOTALL)
        matchobj_19 = re.match('.*转发.*关注.{0,10}选.*', tcontent, re.DOTALL)
        matchobj_18 = re.match(r'.*关注\+评论，随机选.*', tcontent, re.DOTALL)
        matchobj_17 = re.match('.*互动抽奖.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_16 = re.match('.*关注.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_15 = re.match('.*转.*评.*赞.*送', tcontent, re.DOTALL)
        matchobj_14 = re.match('.*评论区.*抽.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_13 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_12 = re.match('.*评论转发点赞.*抽取.*送.*', tcontent, re.DOTALL)
        matchobj_11 = re.match(r'.*关注\+评论.*随机选.*送.*', tcontent, re.DOTALL)
        matchobj_10 = re.match('.*抽.{0,10}送', tcontent, re.DOTALL)
        matchobj_9 = re.match('.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_8 = re.match('.*评论.*关注.*抽', tcontent, re.DOTALL)
        matchobj_7 = re.match('.*评论.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_6 = re.match('.*评论区.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_4 = re.match('.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_3 = re.match('.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_2 = re.match('.*评论区.{0,15}抽.*', tcontent, re.DOTALL)
        matchobj_1 = re.match('.*转发.*关注.*', tcontent, re.DOTALL)
        matchobj = re.match('.*转发.*送.*', tcontent, re.DOTALL)
        matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent, re.DOTALL)
        matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent, re.DOTALL)
        matchobj2 = re.match('.*转.{0,7}评.*', tcontent, re.DOTALL)
        matchobj3 = re.match('.*本条.*送.*', tcontent, re.DOTALL)
        matchobj5 = re.match('.*抽.{0,10}送.*', tcontent, re.DOTALL)
        matchobj10 = re.match('.*钓鱼.*', tcontent, re.DOTALL)
        matchobj23 = re.match('.*关注.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj26 = re.match('.*生日直播.*上舰.*', tcontent, re.DOTALL)
        matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent, re.DOTALL)
        matchobj34 = re.match('.*转发抽奖结果.*', tcontent, re.DOTALL)
        matchobj37 = re.match('.*奖品转送举报人.*', tcontent, re.DOTALL)
        matchobj39 = re.match('.*200元优惠券.*', tcontent, re.DOTALL)
        matchobj43 = re.match('.*不抽奖.*', tcontent, re.DOTALL)
        # matchobj44 = re.match('.*求点赞关注转发.*', tcontent, re.DOTALL)
        matchobj45 = re.match('.*置顶动态抽个元.*', tcontent, re.DOTALL)
        if (
                matchobj_101 == None and matchobj_100 == None and matchobj_99 == None and matchobj_98 == None and matchobj_97 == None and matchobj_96 == None and matchobj_95 == None and matchobj_94 == None and matchobj_93 == None and matchobj_91 == None and matchobj_90 == None and matchobj_89 == None and matchobj_88 == None and matchobj_87 == None and matchobj_86 == None and matchobj_85 == None and matchobj_84 == None and matchobj_83 == None and matchobj_82 == None and matchobj_81 == None and matchobj_80 == None and matchobj_79 == None and matchobj_78 == None and matchobj_77 == None and matchobj_76 == None and matchobj_75 == None and matchobj_74 == None and matchobj_73 == None and matchobj_72 == None and matchobj_71 == None and matchobj_70 == None and matchobj_69 == None and matchobj_68 == None and matchobj_67 == None and matchobj_65 == None and matchobj_64 == None and matchobj_63 == None and matchobj_62 == None and matchobj_61 == None and matchobj_60 == None and matchobj_59 == None and matchobj_58 == None and matchobj_57 == None and matchobj_56 == None and matchobj_55 == None and matchobj_54 == None and matchobj_53 == None and matchobj_52 == None and matchobj_51 == None and matchobj_50 == None and matchobj_49 == None and matchobj_48 == None and matchobj_47 == None and matchobj_46 == None and matchobj_45 == None and matchobj_44 == None and matchobj_43 == None and matchobj_42 == None and matchobj_41 == None and matchobj_40 == None and matchobj_39 == None and matchobj_38 == None and matchobj_37 == None and matchobj_36 == None
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
                and matchobj5 == None or matchobj10 != None or matchobj26 != None or matchobj33 != None
                or matchobj34 != None or matchobj37 != None
                or matchobj39 != None
                or matchobj43 != None or matchobj45 != None):
            return 1
        return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1

    def daily_choujiangxinxipanduan(self, tcontent):  # 动态内容过滤条件
        '''
        每日抽奖的信息判断 更加详细，需要人工判断
        抽奖信息判断      是抽奖返回None 不是抽奖返回1
        :param tcontent:
        :return:
        '''
        tcontent = re.sub('@(.{0,12}) ', '', tcontent)
        tcontent = converter.convert(tcontent)
        tcontent = tcontent.lower()
        tcontent = tcontent.replace(' ', '')
        tcontent = tcontent.replace('传送门', '')
        tcontent = tcontent.replace('车+关', '转+关')
        tcontent = tcontent.replace('lun', '论')
        tcontent = tcontent.replace('车专', '转')
        tcontent = tcontent.replace('扌由', '抽')
        tcontent = tcontent.replace('🧱', '转')
        tcontent = tcontent.replace('🍎', '评')
        tcontent = tcontent.replace('🐷', '关注')
        tcontent = tcontent.replace('卷', '转')
        tcontent = tcontent.replace('苹', '评')
        tcontent = tcontent.replace('平', '评')
        tcontent = tcontent.replace('留言', '评论')
        tcontent = tcontent.replace('选出', '抽')
        tcontent = tcontent.replace('选取', '抽')
        tcontent = tcontent.replace('揪', '抽')
        tcontent = tcontent.replace('抽时间', '')
        tcontent = tcontent.replace('null', '')
        matchobj_117 = re.match(
            '.*挑选.{0,10}送.*|.*评论.{0,20}获得.*|.*粉丝福利.{0,10}送.*|.*参与方式.{0,15}评.*|.*参与方式.{0,15}转.*|.*【抽】.*|.*内含巨大福利',
            tcontent, re.DOTALL)
        matchobj_116 = re.match(
            '.*转.{0,10}关.{0,10}送.*|.*关.{0,10}转.{0,10}送.*|.*送.{0,10}关.{0,10}转.*|.*送.{0,10}转.{0,10}关.*',
            tcontent, re.DOTALL)
        matchobj_115 = re.match(
            '.*抽.{0,10}转|.*抽.{0,10}v|.*抽.{0,5}赞.{0,5}评|.*评.{0,5}抽.{0,5}赞|.*赞.{0,5}评.{0,5}抽', tcontent,
            re.DOTALL)
        matchobj_114 = re.match('.*抽.{0,5}个|.*抽.{0,5}位|.*抽.{0,5}名', tcontent, re.DOTALL)
        matchobj_113 = re.match('.*抽.{0,5}套|.*关注.{0,20}抽|.*转发.{0,20}抽|.*转发抽', tcontent, re.DOTALL)
        matchobj_112 = re.match('.*CJ|.*爆装备|.*人人有机用', tcontent, re.DOTALL)
        matchobj_111 = re.match('.*关.{0,10}评.{0,10}给', tcontent, re.DOTALL)
        matchobj_110 = re.match('.*评论.*分享.*请', tcontent, re.DOTALL)
        matchobj_109 = re.match('.*参加.*抽|.*参与.*抽|.*抽.*参加|.*抽.*参与', tcontent, re.DOTALL)
        matchobj_108 = re.match('.*评论.{0,10}整', tcontent, re.DOTALL)
        matchobj_107 = re.match('.*参加.*送|.*参与.*送|.*送.*参加|.*送.*参与', tcontent, re.DOTALL)
        matchobj_106 = re.match('.*参与.*评.*关|.*参与.*关.*评', tcontent, re.DOTALL)
        matchobj_105 = re.match('.*抽.*评.*关', tcontent, re.DOTALL)
        matchobj_104 = re.match('.*转发参与|.*有机会.{0,15}获得', tcontent, re.DOTALL)
        matchobj_103 = re.match('.*给.{0,10}抽|.*抽.{0,15}寄出', tcontent, re.DOTALL)
        matchobj_102 = re.match(
            '.*转.{0,10}关.{0,10}参.*|.*关.{0,10}转.{0,10}参.*|.*参.{0,10}关.{0,10}转.*|.*转.{0,10}参.{0,10}关.*',
            tcontent, re.DOTALL)
        matchobj_101 = re.match('.*安排.*评论.*|.*评论.*安排.*|给.{0,10}礼物', tcontent, re.DOTALL)
        matchobj_100 = re.match('.*参与.*礼品|.*礼品.*参与|.*礼品.*', tcontent, re.DOTALL)
        matchobj_98 = re.match('.*评.{0,10}抽', tcontent, re.DOTALL)
        matchobj_97 = re.match('.*参与.{0,10}关.{0,10}赞.*', tcontent, re.DOTALL)
        matchobj_96 = re.match('.*评.{0,10}赢.*', tcontent, re.DOTALL)
        matchobj_95 = re.match('.*老.{0,10}安排.*', tcontent, re.DOTALL)
        matchobj_94 = re.match('.*抽奖.*', tcontent, re.DOTALL)
        matchobj_93 = re.match('.*抽奖.*参与.*', tcontent, re.DOTALL)
        matchobj_91 = re.match('.*倒霉蛋.*', tcontent, re.DOTALL)
        matchobj_90 = re.match('.*懂的.*|.*懂得都懂|.*dddd|.*懂的都懂|.*寻找失主|.*大拇哥.{0,5}认领', tcontent,
                               re.DOTALL)
        matchobj_89 = re.match('.*留言.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_88 = re.match('.*评论.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_87 = re.match('.*失物招领.*|.*失物认领.*', tcontent, re.DOTALL)
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
        matchobj_74 = re.match('.*抽.{0,10}奖励.*', tcontent, re.DOTALL)
        matchobj_73 = re.match('.*抓.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_72 = re.match('.*动态抽奖.*', tcontent, re.DOTALL)
        matchobj_71 = re.match('.*转.*关.*抽.{0,15}送.*', tcontent, re.DOTALL)
        matchobj_70 = re.match('.*关注.{0,9}有惊喜.*', tcontent, re.DOTALL)
        matchobj_69 = re.match('.*抽.{0,9}喝奶.*', tcontent, re.DOTALL)
        matchobj_68 = re.match('.*抽.{0,9}得到.*', tcontent, re.DOTALL)
        matchobj_67 = re.match('.*抽.{0,9}获得.*', tcontent, re.DOTALL)
        matchobj_65 = re.match('.*抽奖.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_64 = re.match(r'.*评论.{0,10}补贴.*\d+.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*抽.{0,10}带走.*', tcontent, re.DOTALL)
        matchobj_59 = re.match(r'.*补贴.{0,10}\d+元.*', tcontent, re.DOTALL)
        matchobj_58 = re.match('.*转{0,10}抽.*送.*', tcontent, re.DOTALL)
        matchobj_57 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_56 = re.match('.*评论.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_55 = re.match('.*关注.{0,10}评论', tcontent, re.DOTALL)
        matchobj_54 = re.match('.*评论.{0,5}白.{0,10}嫖.*', tcontent, re.DOTALL)
        matchobj_53 = re.match('.*车专.*关.*', tcontent, re.DOTALL)
        matchobj_52 = re.match('.*评论.*抽.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_51 = re.match('.*评论.*抽.{0,9}红包.*', tcontent, re.DOTALL)
        matchobj_50 = re.match('.*转.{0,9}抽.*', tcontent, re.DOTALL)
        matchobj_49 = re.match('.*抽1位50元红包.*', tcontent, re.DOTALL)
        matchobj_48 = re.match('.*抽.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_47 = re.match('.*抽.{0,10}补贴.*元.*', tcontent, re.DOTALL)
        matchobj_46 = re.match('.*抽奖.*抽.*小伙伴.*评论.*转发.*', tcontent, re.DOTALL)
        matchobj_45 = re.match('.*关注.*一键三连.*分享.*送.*', tcontent, re.DOTALL)
        matchobj_44 = re.match('.*抽.{0,10}小可爱.*每人.*', tcontent, re.DOTALL)
        matchobj_43 = re.match('.*#抽奖#.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_42 = re.match('.*关注.*平论.*抽.*打.*', tcontent, re.DOTALL)
        matchobj_41 = re.match('.*转发.*评论.*关注.*抽.*获得.*', tcontent, re.DOTALL)
        matchobj_40 = re.match('.*关注.*转发.*点赞.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_39 = re.match('.*转发评论点赞本条动态.*送.*', tcontent, re.DOTALL)
        matchobj_38 = re.match('.*挑选.*评论.*送出.*', tcontent, re.DOTALL)
        matchobj_37 = re.match('.*弹幕抽.*送.*', tcontent, re.DOTALL)
        matchobj_36 = re.match('.*随机.*位小伙伴.*现金红包.*', tcontent, re.DOTALL)
        matchobj_34 = re.match('.*评论.*随机.*抽.*', tcontent, re.DOTALL)
        matchobj_33 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_32 = re.match('.*参与方式.*转发.*关注.*评论.*', tcontent, re.DOTALL)
        matchobj_31 = re.match('.*评论.*随机.*抓.*', tcontent, re.DOTALL)
        matchobj_30 = re.match('.*评论.*随机.*抽.*补贴.*', tcontent, re.DOTALL)
        matchobj_29 = re.match('.*评论区.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_28 = re.match('.*转发.*评论.*抽.*送.*', tcontent, re.DOTALL)
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
        matchobj_14 = re.match('.*评论区.*抽.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_13 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_12 = re.match('.*评论转发点赞.*抽取.*送.*', tcontent, re.DOTALL)
        matchobj_11 = re.match('.*关注+评论.*随机选.*送.*', tcontent, re.DOTALL)
        matchobj_10 = re.match('.*抽.{0,10}送', tcontent, re.DOTALL)
        matchobj_9 = re.match('.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_8 = re.match('.*评论.*关注.*抽', tcontent, re.DOTALL)
        matchobj_7 = re.match('.*评论.*关注.*抽.*', tcontent, re.DOTALL)
        matchobj_6 = re.match('.*评论区.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_4 = re.match('.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_3 = re.match('.*抽.*送.*', tcontent, re.DOTALL)
        matchobj_2 = re.match('.*评论区.{0,15}抽.*', tcontent, re.DOTALL)
        matchobj_1 = re.match('.*转发.*关注.*', tcontent, re.DOTALL)
        matchobj = re.match('.*转发.*送.*', tcontent, re.DOTALL)
        matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent, re.DOTALL)
        matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent, re.DOTALL)
        matchobj2 = re.match('.*转.{0,7}评.*', tcontent, re.DOTALL)
        matchobj3 = re.match('.*本条.*送.*', tcontent, re.DOTALL)
        matchobj5 = re.match('.*抽.{0,10}送.*', tcontent, re.DOTALL)
        matchobj23 = re.match('.*关注.*转发.*抽.*送.*', tcontent, re.DOTALL)
        matchobj26 = re.match('.*生日直播.*上舰.*', tcontent, re.DOTALL)
        matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent, re.DOTALL)
        matchobj34 = re.match('.*转发抽奖结果.*', tcontent, re.DOTALL)
        matchobj37 = re.match('.*奖品转送举报人.*', tcontent, re.DOTALL)
        # matchobj44 = re.match('.*求点赞关注转发.*', tcontent, re.DOTALL)
        if (
                matchobj_117 == None and matchobj_116 == None and matchobj_115 == None and matchobj_114 == None and matchobj_113 == None and matchobj_112 == None and matchobj_111 == None and matchobj_110 == None and matchobj_109 == None and matchobj_108 == None and
                matchobj_107 == None and matchobj_106 == None and matchobj_105 == None and matchobj_104 == None and matchobj_103 == None and matchobj_102 == None and matchobj_101 == None and
                matchobj_100 == None and matchobj_98 == None and matchobj_97 == None and matchobj_96 == None and matchobj_95 == None and matchobj_94 == None and matchobj_93 == None
                and matchobj_91 == None and matchobj_90 == None and matchobj_89 == None and matchobj_88 == None and matchobj_87 == None and matchobj_86 == None and matchobj_85 == None
                and matchobj_84 == None and matchobj_83 == None and matchobj_82 == None and matchobj_81 == None and matchobj_80 == None and matchobj_79 == None and matchobj_78 == None and matchobj_77 == None
                and matchobj_76 == None and matchobj_75 == None and matchobj_74 == None and matchobj_73 == None and matchobj_72 == None and matchobj_71 == None and matchobj_70 == None and matchobj_69 == None
                and matchobj_68 == None and matchobj_67 == None and matchobj_65 == None and matchobj_64 == None
                and matchobj_63 == None and matchobj_62 == None and matchobj_61 == None and matchobj_60 == None and matchobj_59 == None and matchobj_58 == None and matchobj_57 == None and matchobj_56 == None
                and matchobj_55 == None and matchobj_54 == None and matchobj_53 == None and matchobj_52 == None and matchobj_51 == None and matchobj_50 == None and
                matchobj_49 == None and matchobj_48 == None and matchobj_47 == None and matchobj_46 == None and matchobj_45 == None and matchobj_44 == None and matchobj_43 == None and
                matchobj_42 == None and matchobj_41 == None and matchobj_40 == None and matchobj_39 == None and matchobj_38 == None and matchobj_37 == None and matchobj_36 == None
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
                and matchobj5 == None or matchobj26 != None or matchobj33 != None
                or matchobj34 != None or matchobj37 != None):
            return 1
        return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1

    def zhuanfapanduan(self, dongtaineirong):
        '''
        转发判断 需要转发返回1 不需要转发返回None
        :param dongtaineirong:
        :return:
        '''
        dongtaineirong = dongtaineirong.replace('车', '转')
        dongtaineirong = dongtaineirong.replace('🧱', '转')
        dongtaineirong = dongtaineirong.replace('🍎', '评')
        dongtaineirong = dongtaineirong.replace('卷', '转')
        dongtaineirong = dongtaineirong.replace('zhuan', '转')
        dongtaineirong = dongtaineirong.replace('砖', '转')
        dongtaineirong = dongtaineirong.replace(' ', '')
        zhuanfapanduan_4 = re.match('.*不准转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan_3 = re.match('.*不用转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan_2 = re.match('.*无需转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan_1 = re.match('.*别转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan1 = re.match('.*转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan3 = re.match('.*转.{0,20}评.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan4 = re.match('.*转.{0,20}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan5 = re.match('.*转.{0,20}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan6 = re.match('.*转.{0,20}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan10 = re.match('.*卷.{0,20}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan11 = re.match('.*专.{0,20}评.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan12 = re.match('.*专.{0,20}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan13 = re.match('.*专.{0,20}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan14 = re.match('.*专.{0,20}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan15 = re.match(r'.*转评|.*转加关|.*转\+关', str(dongtaineirong), re.DOTALL)
        if (zhuanfapanduan1 == None and zhuanfapanduan3 == None and zhuanfapanduan4 == None
                and zhuanfapanduan5 == None and zhuanfapanduan6 == None and zhuanfapanduan10 == None and zhuanfapanduan11 == None and zhuanfapanduan12 == None
                and zhuanfapanduan13 == None and zhuanfapanduan14 == None and zhuanfapanduan15 == None
                or zhuanfapanduan_1 != None or zhuanfapanduan_2 != None or zhuanfapanduan_3 != None or zhuanfapanduan_4 != None
        ):
            return None
        else:
            return 1

    def get_all_sixin(self, uid, cookie, ua):
        url = 'https://api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs?talker_id={}&session_type=1&size=10&begin_seqno=0&build=0&mobi_app=web'.format(
            uid)
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = self.s.get(url=url, headers=headers)
        return req.json()
    def pre_msg_processing(self, content):
        """
        判断预处理的内容，确保内容含有里面的东西
        :param content:
        :return:
        """
        premsg = ''  # 判断是否需要@或者带话题
        content = content.replace('＠', '@')
        content = re.sub('@([^ ]{0,10}) ', '', content, re.DOTALL)
        content = content.replace('转发话题', '带话题')
        content = content.replace('＃', '#')
        non_topic_content = re.sub('(?<=#)(.{0,10})(?=#)', '', content, re.DOTALL)
        topobj_6 = re.match('.*@.{0,3}位.*|.*@.{0,3}名.*', non_topic_content, re.DOTALL)
        topobj_5 = re.match('.*@.{0,3}1位.*|.*@.{0,3}1名.*', non_topic_content, re.DOTALL)
        topobj_4 = re.match('.*@.{0,3}一位.*|.*@.{0,3}一名.*', non_topic_content, re.DOTALL)
        topobj_3 = re.match('.*@.{0,3}一位好友.*|.*@.{0,3}你的|.*@.{0,3}一名好友.*', non_topic_content, re.DOTALL)
        topobj_2 = re.match('.*艾特.{0,3}位好友.*|.*艾特.{0,3}名好友.*', non_topic_content, re.DOTALL)
        topobj_1 = re.match('.*@你想祝福的人.*', non_topic_content, re.DOTALL)
        topobj0 = re.match('.*@{0,3}位胖友.*|.*@{0,3}名胖友.*', non_topic_content, re.DOTALL)
        topobj1 = re.match('.*圈.{0,3}位你的伙伴.*|.*圈.{0,3}名你的伙伴.*', non_topic_content, re.DOTALL)
        topobj2 = re.match('.*带tag#.{0,20}#.*', non_topic_content, re.DOTALL)
        topobj3 = re.match('.*带话题.{0,15}#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj4 = re.match('.*带上tag#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj5 = re.match('.*带#.{0,20}#.{0,10}话题((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj6 = re.match('.*艾特好友.*', non_topic_content, re.DOTALL)
        topobj7 = re.match('.*@一名好友.*|.*@一位好友.*', non_topic_content, re.DOTALL)
        topobj8 = re.match('.*@你的.{0,3}个小伙伴.*', non_topic_content, re.DOTALL)
        topobj9 = re.match('.*@两位好友.*', non_topic_content, re.DOTALL)
        topobj10 = re.match('.*带#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj11 = re.match('.*@.{0,5}的一个好友.*', non_topic_content, re.DOTALL)
        topobj12 = re.match('.*带[^来】看懂]{0,5}#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj13 = re.match('.*加话题#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        topobj14 = re.match('.*带标签#.{0,20}#((?!投稿).)*$', non_topic_content, re.DOTALL)
        if topobj_6 is not None or topobj6 is not None or topobj_5 is not None or topobj_4 is not None or topobj_3 is not None or topobj_2 is not None or topobj_1 is not None or topobj0 is not None or topobj1 is not None \
                or topobj7 is not None or topobj8 is not None or topobj11 is not None:
            premsg = f'@{random.choice(self.at_member)} '
        elif topobj9 is not None:
            premsg = f'@{random.choice(self.at_member)} @{random.choice(self.at_member)} '
        elif topobj2 is not None:
            msg = re.findall(r'.*带tag#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj3 is not None:
            msg = re.findall(r'.*带话题.*?#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj4 is not None:
            msg = re.findall(r'.*带上tag#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj5 is not None:
            msg = re.findall(r'.*带#(.{0,20})#.{0,10}话题.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj10 is not None:
            msg = re.findall(r'.*带#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj12 is not None:
            msg = re.findall(r'.*带.{0,10}#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj13 is not None:
            msg = re.findall(r'.*加话题#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        elif topobj14 is not None:
            msg = re.findall(r'.*带标签#(.{0,20})#.*', content, re.DOTALL)
            for i in msg:
                premsg += '#' + str(i) + '#'
        if '#' in premsg:
            tpremsg = ''
            for _ in range(len(premsg.split('#'))):
                if premsg.split('#')[_] != '' and premsg.split('#')[_] != ' ' and premsg.split('#')[_] != '  ' and \
                        premsg.split('#')[_] != '和':
                    if len(tpremsg) < 18:
                        tpremsg += '#' + premsg.split('#')[_] + '#'
            premsg = tpremsg

        if '#' in premsg:
            tpremsg = ''
            for i in premsg.split('#'):
                if i != '' and i != ' ' and i != '和':
                    tpremsg += '#' + i + '#'
            premsg = tpremsg
        return premsg

