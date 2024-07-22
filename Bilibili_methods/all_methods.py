# -*- coding:utf- 8 -*-
import asyncio
import hashlib
import httpx
import json
import math
import random
import re
import sys
import time
import traceback
import urllib
from urllib import parse
from CONFIG import CONFIG
from pylangtools.langconv import Converter

import Bilibili_methods.log_reporter as log_reporter
import js2py

import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import numpy
import requests
from asgiref.sync import async_to_sync
from utl.代理 import request_with_proxy

up_nickname_dict = {
    '真果粒官方': '果粒总',
    '邻家小妹装机馆': '小欣阿姨',
    '苏宁易购': '小狮子',
    'Jesse_White': 'J哥',
    '红魔游戏手机': '红魔姬',
    'Haylou嘿喽': '嘿喽',
    'IGN中国': 'IGN',
    '苏泊尔SUPOR': '苏酱',
    '美菱电器': '菱菱子',
    'MuMu模拟器-Mu酱': 'Mu酱',
    '宁波银行信用卡': '卡宝',
    '文石BOOX': '小布',
    'GATERON-佳达隆': '佳达隆',
    'Chiline': '千濑',
    '天猫国际': '阿际',
    '宁美NINGMEI': '宁美',
    '宁晓美': '晓美',
    '麦当劳': '麦麦',
    '中国平安': '平总',
    '平安银行': '安总',
    '中国联通客服官方': '小U',
    '招商银行App': '小招喵',
    '华硕天选官方UP': '天选姬',
    '雅迪电动车官方': '迪迪子',
    '食族人食品': '食人族',
    'QCY蓝牙耳机官方号': 'Q宝',
    'UGREEN绿联': '绿联',
    '叙世视频': '叙事君',
    '平安小财娘': '小财娘',
    '威马汽车': '威酱',
    '当贝投影': '贝酱',
    'andaseaT安德斯特电竞椅': '小安',
    '智云稳定器': '云妹',
    '奉科麦克风': '奉科',
    '小明投影': '明仔',
    '只投螺碗小碗妹': '碗妹',
    '黑鲨游戏手机': '鲨鲨酱',
    'Thunderobot雷神笔记本': '小雷',
    '哔哩哔哩番剧': '官方',
    '哔哩哔哩纪录片': '官方',
    '中国移动动感地带': '小动宝',
    '二柄APP': '二柄',
    '同程旅行': '程仔',
    '酸酸乳官方': '酸酸',
    '唐麦官方账号': '麦子哥',
    '燕子DIY装机': '燕子',
    '中国电信青年一派': '派派',
    '大华存储宠': '华妹',
    '次元书馆': '馆长',
    'COLG玩家社区': '香蕉皮',
    '美的生活小家电': '美美子',
    '唯品会': '三口娘',
    'UPUPOO动态桌面': '啊噗',
    '索泰ZOTAC': '阿索',
    '美的系洗衣机': '净净子',
    '广汽丰田': '小田田',
    'Apexgaming艾湃电竞': '小艾',
    '平安人寿': '豹总',
    'QQ星': 'Q酱',
    '小白一键重装系统': '小白',
    '味知香食品官方': '小香',
    '健力宝微泡水': '泡泡子',
    '虎课网': '虎妞妞',
    'ALIENWARE外星人': '外星人',
    'KBEAR魁宝耳机': '魁宝',
    'CRD克徕帝官方号': '徕徕',
    '麦富迪': '糊迪',
    '惠而浦家电': '惠小浦',
    'TT语音': '16',
    '起点读书-点娘': '点娘',
    '纯甄官方': '小甄',
    '旺旺旺仔俱乐部': '旺仔',
    '美商海盗船CORSAIR': '船船',
    '阿志-三国志战略版': '阿志',
    'v猫诺v': '猫诺',
    '大鹏质检员': '大鹏',
    '水月雨Moondrop': '阿水',
    'SONGX耳机': '小X',
    '刘庸干净又卫生': '庸子',
    '沃隆坚果': '小隆人',
    '掌阅iReader官方账号': '小阅阅',
    '奥迪双钻AULDEY': '钻钻',
    '友坑': '坑哥',
    'Wacom和冠': '小Wa',
    'KIOXIA铠侠中国': '铠侠',
    'iKF蓝牙耳机': 'i总',
    '杭州联通': '杭子',
    '大华存储': '华妹',
    '台电科技TECLAST': '小台',
    'Ulanzi优篮子': '篮篮子',
    '都市时报官方': '小都',
    '巴士管家': '小巴',
    '斗鱼直播': '鲨鱼娘',
    '来伊份': '伊仔',
    '子彦娱乐': '子彦君',
    'LETSHUOER铄耳': '铄耳君',
    'BANPRESTO': '眼睛厂',
    '明基专业摄影显示器': '明基',
    'MAXSUN铭瑄': '帮主',
    '枫笛Saramonic': '小笛',
    '高漫手绘板': '高漫',
    '哔哩哔哩广告娘': '广告娘',
    '酒拾烤肉': '小酒',
    '橙光官方': '橙娘',
    '屈臣氏中国': '小屈',
    'T3出行': 'T酱',
    '芙清密钥官方账号': '小密钥',
    '螺霸王': '螺霸霸',
    '遐内衣官方账号': '小遐',
    'bilibiliGoods': '谷子娘',
    '施德楼STAEDTLER': '楼楼',
    '十六萃': '萃萃',
    '谷粒多鼓励': '小谷',
    '老乡鸡': 'BB鸡',
    '美的料理爆料局': '小料',
    'KOORUI科睿官方UP': '科睿',
    '九州风神DeepCool': '九州风神',
    '周黑鸭': '鸭鸭',
    '斯塔克3000': '小塔',
    '应用宝': '宝妹',
    '哈弗HAVAL': '小哈',
    '小米有品': '有品',
    '派乐汉堡': '乐乐子',
    '前程无忧官方': 'uu',
    '中国电信营业厅官方': 'A星',
    '华宇万维': '维维',
    '聚划算': '章鱼娘',
    '金典SATINE': '典典子',
    '罗马仕官方号': '罗宝',
    '虹领金官方账号': '小金',
    '格兰仕官方账号': '小格',
    'Mlily梦百合床垫': '仙子',
    'Defense决色小彩壳': '星星',
    '骁骑电竞椅': '小骑',
    '小希小桃Channel': '小希小桃',
    'Thermalright官方账号': '利民',
    '漫绘新风': '漫绘',
    '王者荣耀': '老亚瑟',
    'COGI高姿': '小高高',
    'AIMER爱慕内衣': '小慕',
    '五菱汽车': '小五',
    '奇影动漫官方账号': '奇影动漫',
    'cdf三亚国际免税城': '三亚国际免税城',
    '-评头论足-': '评头论足',
    '联想拯救者官方': '联想拯救者',
    '硬核的半佛仙人': '半fo',
    'SOUNDPEATS': 'S君',
    '爱整活的41崽w': '栗子',
    '安慕希': '安丽',
    'iFashion千送衣': '小千',
    '武哥分享': '武哥',
    '移速科技': '移宝',
    '哔哩哔哩线下活动': '线下娘',
    'Xbox盒子君': '和盒子君',
    'APEX-TOYS': 'APEX',
    'iQOO手机': 'iQOO',
    '优地机器人': '小优',
    '创信工程咨询': '创创',
    '正宗转转APP': '转转',
    '梦想的阿肯老师': '阿肯老师',
    'FreeCheck免费查重': '小论文',
    '冰糖IO': '冰糖',
    '小龙坎火锅': '巨龙',
    '猴子音悦官方账号': '猴老师',
    '联想未来探秘局': '阿young',
    '不愧是良品铺子': '良老板',
    '芝洛洛官方': '小芝音',
    '曦彤Asuna': '曦彤',
    '囧鸽官方账号': '囧鸽',
    '妖舞_YOWU': '妖舞小姐姐',
    '淘菜菜真的菜': '菜菜',
    '北京移动官方': '小移酱',
    '皇家加勒比游轮': '比比',
    'CFORCE品牌': 'CFORCE',
    'GAN电脑实验室': '老GAN',
    '欧莱雅男士官方': '小雅',
    '福昕教育': '小福狸',
    '佑美': '佑美君',
    '精萃自然': '小然',
    '娃哈哈': '娃娃子',
    '元气森林': '林子',
    'ACTOYS官方账号': 'ACTOYS',
    'COMICA科唛': '小唛',
    '澳乐乳': '乐乐',
    '浦科特Plextor': '浦科特',
    '陆金所官方账号': '所长',
    '松下panasonic': '松松子',
    '灵动创想官方': '阿动',
    '禾川兴科技': '摸鱼川',
    '海信官方': '哈利',
    '夸克_Quark': '夸叽',
    '尼康趣发现': '尼康',
    '微星GAMING': '小红龙',
    '天美意制鞋厂': '美酱',
    '水的合唱': '水叔',
    'Padmate派美特': '派派',
    '明月镜片认识下': '明月镜片',
    '应届生求职网': '职前菌',
    '-雷电模拟器-': '雷电模拟器',
    'HFP': 'Home妹',
    'wellymerck威利默克': '威宝',
    '陈不乐REACTION': '不乐',
    '杰士邦jissbon': 'JJ',
    '懂你的TCL': 'T哥',
    '萌羽moeyu': '萌羽',
    '太二酸菜鱼': '小二哥',
    '多多视频不正经官方': '多多',
    '幸运石官方': '老石',
    '在下钟薛高': '高高',
    'TTC正牌科电': 'TTC',
    '喜欢就买JustBuy': '段总',
    '3DM游戏网官方': '三大妈',
    '得力集团': '力力',
    '哈啰出行': '小哈',
    'RAPOO雷柏': '雷柏',
    '猫耳FM': 'M娘',
    '金山文档': '金小獴',
    'Bio-E': '小E',
    '芙清FulQun': '小芙',
    '九号公司': '九号',
    'AutoFull傲风电竞椅': '椅子精',
    'ROG玩家国度官方UP': '小R',
    '漫库Mancool': '库仔',
    '优酸乳': '小优',
    '五谷道场官方账号': '阿谷',
    '绿源电动车官': '小绿',
    '思谋科技': '思小谋',
    '雷蛇玩家殿堂': '雷蛇',
    '蘑菇街官方': '蘑菇酱',
    '腾讯卫士官方帐号': '鹅探长',
    '太太乐鲜味厨房': '太太乐',
    'inphic英菲克': '小英',
    '影驰科技': '影驰',
    '异能者官方': '小异',
    '小鹏汽车的小P': '小P',
    'URBANREVIVO': 'Una',
    '晨光文创研究社': '社长',
    '潮玩客': '健哥',
    '352净水器': '阿净',
    'ZMI紫米': '小紫',
    'Redmi红米手机': '红米',
    '招商银行信用卡': '小招喵',
    '华擎科技_ASRock': '皮皮擎',
    '达墨Topmore': '达墨',
    '和平精英': '鸡仔',
    '慕课网官方账号': '老慕',
    '氧气语音': '小鲸鱼',
    'HUION绘王': '小绘',
    '珠峰凯越机车': '小凯',
    '网易游戏奇遇': '蚌蚌',
    '装机小潘西': '馨馨',
    '又画教育': '又酱',
    '沃尔玛Official': '二妈',
    '英特尔游戏': '七七',
    'AMD中国': 'AMD',
    '鹅厂程序员': '猿猿',
    '尊客蓝牙耳机': '尊客',
    'MSI微星显卡官方账号': '龙妹',
    'Midea推理社': '推理社',
    '脱毛狗刘老板': '刘老板',
    '逆战': '安琪儿',
    '里世界的相宜本草铺': '阿相',
    '中国电信重庆公司': '小信',
    '麻辣王子MLWZ': '麻辣王子',
    '火绒安全实验室': '绒绒',
    '杉果Sonkwo': '杉果娘',
    '澳柯玛官方账号': '小澳',
    '战双帕弥什': '双宝',
    '360粉丝团': '团团',
    '陕西中公教育': '阿中',
    '网易MuMu-Mu酱': 'Mu酱',
    '尖叫SCREAM': "尖叫",
    '卓玛泉': '卓玛',
    '哔哩哔哩大会员': '大学长',
    'HEYTEA喜茶': '喜茶',
    '水星家纺电商': '小水星',
    '三五二净化姬': '阿净',
    '汽车之家原创': '家家',
    'LEVEL8地平线8号': '小八',
    '闪魔SmartDevil': '魔魔',
    'Insta360': '小影',
    '羚邦动漫': '邦邦',
    '宏发股份': '发发',
    '电巢': '阿巢',
    'KLOOK客路': 'KK',
    '大白卫浴': '大白',
    '吉比特游戏': '小G',
    'ZEROZONE泽洛': '阿Z',
    '自然堂': '堂主',
    '梅见青梅酒': '小梅子',
    '比亚迪汽车': '小迪',
    'GAOKINMOTO高金动力': '阿金',
    '舜华临武鸭': '鸭鸭',
    '雪佛兰官方账号': '小雪',
    '摩登仕蓝牙耳机': '小摩',
    '阿特弈耳蓝牙耳机': '阿特',
    '网易UU加速器官方': 'UU妹',
    '北海牧场官方账号': '小北',
    '脉动驻小破站办事处': '小脉',
    '苏宁易购手机电脑': '苏苏',
    'SoleusAir舒乐氏': '小舒',
    '罗针盘': '兰兰',
    '北京联通官方账号': '北北',
    '招商银行官方账号': '小招招',
    '三星盖乐世手机': '小星',
    '哈趣投影': '小哈',
    '美的智慧家': '小美',
    '群核科技招聘小助理': '小助理',
    '臭宝螺蛳粉': '臭宝',
    '育碧中国Ubisoft': '阿育',
    '比苛电池': '小苛',
    '大家的音乐姬': '音乐姬',
    '哔哩哔哩会员购': '会员购',
    '榄菊官方': '榄菊',
    '梵音瑜伽官方账号': '梵音瑜伽',
    '吉利招聘': '66熊',
    '生死狙击2官方': '酱酱',
    '智行火车票官方账号': '票姐',
    'Anker中国': '安Sir',
    '墨将BIGBIG-WON官方账号': '小墨',
    '飞利浦家电官方': '飞利浦家电',
    '福特中国': '福特',
    '元气桌面官方号': '元气喵',
    '五环观察室': '小观',
    'aigo国民好物': '小a',
    'machenike机械师': '机械师',
    'BOYA声学': '小雅',
    'Anker安克_': '安克',
    '鲁大师官方': '小鲁',
    '联想YOGA和小新官方': 'YOGA和小新',
    '腾讯招聘': '聘子',
    '艾肯电子科技': '艾肯',
    '美的': 'M博',
    '一加手机': '加哥',
    'realme真我手机': 'realme',
    '味可滋': 'vv',
    '合天网安实验室': '小合',
    '一只宝妹': '宝妹',
    '大金空调中国': '大金',
    'Sapphire蓝宝科技': '蓝宝石',
    '一只啊噗喵': '啊噗',
    '奈雪的茶': '奈雪',
    'NVIDIA英伟达官方账号': '英伟达',
    'Varmilo阿米洛': '阿米洛',
    '黑峡谷': '小谷',
    '轻肴CHEAYO': '肴肴',
    '酷比魔方官方账号': '酷比魔方',
    '万代南梦宫中国': '小南',
    '骨伽COUGAR中国': '骨伽',
    '银欣SilverStone官方': '银欣',
    'Razer雷蛇': '雷蛇',
    '禾君硕行': '小禾',
    '哔哩哔哩漫画': '漫画姬',
    '创信教育': '小创',
    '亿码聚合': '亿码',
    '斯泰得乐StadlerForm': '得乐子',
    '太平洋汽车APP': '小汽车',
    'MasterGo产品设计工具': 'MasterGo',
    '五芳斋1921': '阿斋',
    'Dataland迪兰显卡': '迪兰',
    'Segotep鑫谷': '小鑫',
    '绿源电动车官方': '小绿',
    'AORUS技嘉电竞': '雕妹',
    '78动漫网': '78动漫',
    '凯华电子': '凯华',
    'AI度晓晓': '晓晓',
    'BDuck就是小黄鸭': '小黄鸭',
    '别克': '小克',
    'Pico-VR官方': 'Pico妹',
    'PHILIPS显示器': 'PHILIPS小编',
    '猎聘app': '小猎',
    '人类快乐': '多多',
    '美术宝艺考': '美宝',
    'Nanoleaf官方': 'Nanoleaf',
    '中国金币': '小金',
    'AGON爱攻电竞官方': '爱攻',
    '美团买菜': '小菜',
    'Darmoshark官方账号': 'Darmoshark',
    '索尼中国': '阿索',
    'AJAZZ黑爵外设': '小黑',
    '爱玛电动车官方账号': '爱玛',
    '宝丽来Polaroid': '小宝',
    'TCL': 'T哥',

}

# 噫！好！我中了！
kongpinglun = '⁡'


class methods:
    def __init__(self):
        self.requests_with_proxy = request_with_proxy.request_with_proxy()
        self.copy_suffix = ['']  # 复制后缀
        self.changyongemo = ['doge', '脱单doge', '妙啊', '吃瓜', 'tv_doge', '藏狐', '原神_哇', '原神_哼', '原神_嗯',
                             '原神_欸嘿', '原神_喝茶']  # 常用的表情包
        self.at_member = ['_大锦鲤_', '陈睿', '哔哩哔哩大会员', '哔哩哔哩会员购']
        self.username = ''  # 自己账号的名字，默认为空
        self.caihongpi_chance = 0  # 对官方使用彩虹屁的概率，数字越大，彩虹屁频率越高
        self.repostchance = 0.5  # 转发动态时，转发内容为评论内容的几率
        self.pinglunzhuanbiancishu = 5  # 获取评论时失败重新尝试的次数
        self.chance_shangjiayingguang = 0  # 随机挑线自定义商家广告回复词的概率
        self.chance_copy_comment = 0  # 抄评论的概率
        self.range_copy_comment = 1  # 抄评论的长度在20条评论评均长度的比率，数字越大，抄的评论越长
        self.non_official_chp_chance = 0  # 对非官方使用cph评论的概率
        self.sleeptime = numpy.linspace(1, 3, 500, endpoint=False)
        self.replycontent = ['[原神_欸嘿]', '[原神_喝茶]', '好耶', '来了', '冲鸭', '来了来了', '冲',
                             '[原神_哼]', '[原神_嗯][原神_哇][原神_哼]', '[原神_哇][原神_哼]', '[原神_哇]',
                             '万一呢', '[歪嘴][歪嘴]', '[doge]', '[脱单doge][脱单doge]', '[脱单doge]', '牛', '[脸红]',
                             '[鼓掌]']  # 默认回复内容
        self.dianzanshibai = list()
        self.zhuanfashibai = list()
        self.pinglunshibai = list()
        self.guanzhushibai = list()
        self.official_caihongpilist = [  # 官方回复内容
            # '老板超级大气喵[永雏塔菲_嘻嘻喵][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_星星眼][永雏塔菲_哈哈哈]@{1} 的评论喵',
            # '老板超级大气喵[永雏塔菲_好热][永雏塔菲_嘻嘻喵]非常感谢老板喵[永雏塔菲_哈哈哈][永雏塔菲_星星眼]@{1} 的评论喵',
            # '老板超级大气喵[永雏塔菲_令人兴奋][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_亲嘴][永雏塔菲_嘻嘻喵]@{1} 的评论喵',
            '老板超级大气喵[永雏塔菲_嘻嘻喵][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_星星眼][永雏塔菲_哈哈哈]',
            '老板超级大气喵[永雏塔菲_好热][永雏塔菲_嘻嘻喵]非常感谢老板喵[永雏塔菲_哈哈哈][永雏塔菲_星星眼]',
            '老板超级大气喵[永雏塔菲_令人兴奋][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_亲嘴][永雏塔菲_嘻嘻喵]',
            # '老板超级大气喵[未来有你_打call][永雏塔菲_好热]非常感谢老板喵[未来有你_走花路][永雏塔菲_哈哈哈]',
            # '老板超级大气喵[未来有你_好耶][永雏塔菲_嘻嘻喵]非常感谢老板喵[未来有你_热情][永雏塔菲_星星眼]',
            # '老板超级大气喵[永雏塔菲_令人兴奋][未来有你_打call]非常感谢老板喵[永雏塔菲_亲嘴][未来有你_好耶]',
            # # '@{1} 祝{0}粉丝越来越多！',
            # # '@{1} 祝{0}粉丝越来越多，人气越来越旺[热词系列_好耶]',
            # '\n{0}的宠粉福利好耶[未来有你_登场]\n被戳中了……心巴！n(*≧▽≦*)n[未来有你_未来有你]\n',
            # '\n爱了爱了[未来有你_登场]\n{0}，你！是！我的神！！！[未来有你_未来有你]\n',
            # '\n{0}真宠粉[未来有你_登场]\n祝所有人都有超级美好的一天！！ヾ(≧∇≦*)ゝ[未来有你_未来有你]\n',
            # '\n哇，是{0}的宠粉抽奖[未来有你_登场]\n你是~我！的！神！[未来有你_未来有你]\n',
            # '\n{0}的宠粉抽奖[未来有你_登场]\n你是~我！的！神！[未来有你_未来有你]\n',
            # # '\n{0}超宠粉的er[未来有你_登场]\n{1}祝{0}三阳开泰，四季安康[未来有你_走花路]\n最重要的是粉丝越来越多[未来有你_未来有你]\n',
            # '\n感谢{0}的宠粉抽奖[未来有你_打call]\n听我说👂👂👂谢谢你🙏🙏🙏因为有你👉👉👉温暖了四季🌈🌈🌈\n',
            # '\n{0}超宠粉的er[未来有你_打call]\n你是~我！的！神！[未来有你_未来有你]\n',
            # '\n关注{0}，好运来！来！来！水逆霉运退！退！退！[未来有你_打call]\n',
            # # '感谢{0}的宠粉福利[热词系列_可以][热词系列_可以]\n愿粉丝越来越多[热词系列_秀][热词系列_秀]\n祝@{1} 好运来[热词系列_保护][热词系列_保护]',
            # # '好耶，希望能被宠粉的{0}抽到呀[脱单doge]\n',
            # # '来了来了，来支持{0}了[打call]\n',
            # # '来了来了，希望能被宠粉的{0}抽到[脱单doge]',
            # # '来了来了，希望能被宠粉的{0}抽到呀[脱单doge]\n',
            # '\n来了来了，{0}真宠粉，希望能被抽到呀[未来有你_酸了][未来有你_酸了]\n',
            # '\n{0}超宠粉，惊喜不断，好运常伴[未来有你_未来有你][未来有你_未来有你]\n',
            # '\n来了来了，{0}超宠粉的er，希望能被抽到呀[未来有你_酸了][未来有你_酸了]\n',
            # '\n{0}宠粉福利多，点点关注不迷路[未来有你_打call][未来有你_打call]\n祝大家每天有个好心情o(≧v≦)o[未来有你_好耶]\n',
            # '\n心动不如行动，关注{0}，福利一直有[未来有你_未来有你]\n',
            # '\n关注{0}，欧气不断[未来有你_未来有你]\n',
            #
            # # '支持{0}，祝你们的粉丝越来越多[打call]产品越卖越火[保卫萝卜_笔芯]',
            # # '我对您的爱滔滔不绝[热词系列_爱了爱了]\n我会多多支持您的[热词系列_仙人指路]\n好耶，感谢{0}[热词系列_妙啊]\n@{1} 在这里真诚的祝福您![热词系列_多谢款待]\n祝您万事无忧!万事顺心![热词系列_可以]\n希望您的粉丝越来越多![热词系列_再来亿遍]',
            # # '@{1} 在此祝福[热词系列_仙人指路]\n愿{0}的粉丝越来越多[热词系列_好耶]\n在b站越来越好[热词系列_秀]',
            # # '来了来了，谢谢{0}的宠粉福利[脱单doge]\n',
            # # '{0}太宠粉了，遇见{0}，是我最大的幸运！[未来有你_未来有你][未来有你_未来有你][未来有你_未来有你]\n',
        ]  # 为了你😨😨😨我变成狼人模样🐺🐺🐺\n为了你😱😱😱染上疯狂🤡🤡🤡\n为了你😰😰😰穿上厚厚的伪装👹👹👹\n为了你🤗🤗🤗换了心肠💀💀💀\n
        self.non_official_chp = ['好耶',
                                 '许愿',
                                 '万一呢',
                                 '冲冲冲',
                                 '冲鸭',
                                 '好运来',
                                 '拉低中奖率',
                                 ]
        self.shangjiayingguang = [  # '水点评论，点点赞，合作那边那好交代[doge]',
            # '很满意的一次购物。',
            # '买了三台了，质量非常好，与卖家描述一致，孩子们都特别喜欢吃，版型很好，面料舒适，尺码标准，不沾杯持妆久，很满意的一次购物。',
            # '橘色系更加显白，洗完也很柔顺头发也不油了，屏幕清晰运行流畅，很满意的一次购物。',
            # '敏感肌用起来毫无压力，握感舒适不伤牙龈，每次炒菜都会放几滴，很满意的一次购物。',
            # 'UP多发这种广告，很实用谢谢',
            '还不错，买了[doge]',
            # '已经买了几个了，用起来跟真人差不多，推荐大家也去买来用[doge][doge][doge]',
            # '买过认为值 好评，买了三台了，质量非常好，与卖家描述一致',
            # '孩子们都特别喜欢吃，版型很好，面料舒适，尺码标准。很满意的一次购物。',
            # '不沾杯持妆久，很满意的一次购物。',
            # '屏幕清晰运行流畅，每次炒菜都会放几滴，很满意的一次购物。',
            # '货很好 物美价廉 快递也迅速。很满意的一次购物。',
            # '已折叠对您购物参考帮助不大的评价',
            # '买了三台了，质量非常好，括约肌也能用！',
            # '橘色系更加显白，屏幕清晰运行流畅。很满意的一次购物。',
            # '握感舒适不伤牙龈，每次炒菜都会放几滴，用起来和真人差不多，很舒服。很满意的一次购物。',
            # '该用户未做出评价，系统已默认好评！',
            # '已收到货。质量很好，与描述一致，完全超出期望，包装仔细严实，总的来说这次是很满意的一次购物',
            # '孩子很喜欢，不伤牙龈，一口气上五楼，很满意的一次购物。',
            '好好好',
            '未下单期待收货[doge]',
            '很好吃[doge]',
        ]  # 商家硬广回复词
        self.xiaoweiba = ['']  # '\n------------------\n以上是我想说的，以下是为了加字数过审\n']
        self.xiaoweibawenan = ['',
                               # '抽奖3不原则: \n1.从来不缺席\n2.从来不中奖\n3.从来不放弃[doge]\n',
                               # '一个赞\n一世情\n一个转发\n这个世界就会少一个伤心人~\n'
                               # '抽奖福利挺好的\n但是有点缺陷\n给up提三点建议\n...\n展开\n',
                               # '一旦接受了自己的软弱🎶那我就是 无敌的🎵\n发生什么事了🔉发生什么事了🔉发生什么事了🔉发生什么事了🔉发生什么事了🔉\n🎶假↓面↑骑↑士↓～～～🎵\n🎶贞→贞→贞→贞↗德↘↗🎶\n',
                               # '一旦吃了黄金脆皮鸡🎶那我就是 无敌的🎵\n疯狂星期四了🔉疯狂星期四了🔉疯狂星期四了🔉疯狂星期四了🔉疯狂星期四了🔉\n🎶假↓面↑骑↑士↓～～～🎵\n🎶疯→狂→星→期↗四↘↗🎶\n',
                               # '本人抽奖\n①从不缺席\n②从不中奖\n③从不放弃',
                               # '第一：绝对不会上头\n第二：绝对不会错过任何抽奖\n第三：绝对非到喜闻乐见\n非酋队长前来觐见_(:3」∠)_',
                               # '日常虽然抽不到我[虎年]\n但是我还要参加[2022]\n期待着这次能转一次运[锦鲤]'
                               ]
        self.None_nickname = list()
        self.hasemo = ['藏狐', 'doge', '微笑', 'OK', '星星眼', '妙啊', '辣眼睛', '吃瓜', '滑稽', '喜欢', '嘟嘟',
                       '给心心', '笑哭',
                       '脱单doge',
                       '嗑瓜子', '调皮', '歪嘴', '打call', '呲牙', '酸了', '哦呼', '嫌弃', '大哭', '害羞', '疑惑',
                       '喜极而泣', '奸笑', '笑', '偷笑',
                       '点赞',
                       '无语',
                       '惊喜', '大笑', '抠鼻', '呆', '囧', '阴险', '捂脸', '惊讶', '鼓掌', '尴尬', '灵魂出窍', '委屈',
                       '傲娇', '疼', '冷', '生病',
                       '吓',
                       '吐',
                       '撇嘴', '难过', '墨镜', '奋斗', '哈欠', '翻白眼', '再见', '思考', '嘘声', '捂眼', '抓狂', '生气',
                       '口罩', '牛年', '2021',
                       '水稻',
                       '福到了',
                       '鸡腿', '雪花', '视频卫星', '拥抱', '支持', '保佑', '响指', '抱拳', '加油', '胜利', '锦鲤',
                       '爱心', '干杯', '跪了', '跪了',
                       '怪我咯',
                       '黑洞',
                       '老鼠', '来古-沉思', '来古-呆滞', '来古-疑问', '来古-震撼', '来古-注意', '哭泣', '原神_嗯',
                       '原神_哼', '原神_哇', '高兴', '气愤',
                       '耍帅',
                       '亲亲',
                       '羞羞', '狗子', '哈哈', '原神_欸嘿', '原神_喝茶', '原神_生气', '热词系列_河南加油',
                       '热词系列_豫你一起', '热词系列_仙人指路', '热词系列_饮茶先啦',
                       '热词系列_知识增加', '热词系列_再来亿遍', '热词系列_好耶', '热词系列_你币有了', '热词系列_吹爆',
                       '热词系列_妙啊', '热词系列_你细品', '热词系列_咕咕',
                       '热词系列_标准结局', '热词系列_张三', '热词系列_害', '热词系列_问号', '热词系列_奥力给',
                       '热词系列_猛男必看', '热词系列_有内味了', '热词系列_我裂开了',
                       '热词系列_我哭了', '热词系列_高产', '热词系列_不愧是你', '热词系列_真香', '热词系列_我全都要',
                       '热词系列_神仙UP', '热词系列_锤', '热词系列_秀',
                       '热词系列_爷关更',
                       '热词系列_我酸了', '热词系列_大师球', '热词系列_完结撒花', '热词系列_我太南了',
                       '热词系列_镇站之宝', '热词系列_有生之年', '热词系列_知识盲区',
                       '热词系列_“狼火”',
                       '热词系列_你可真星', 'tv_白眼', 'tv_doge', 'tv_坏笑', 'tv_难过', 'tv_生气', 'tv_委屈',
                       'tv_斜眼笑', 'tv_呆', 'tv_发怒',
                       'tv_惊吓',
                       'tv_笑哭', 'tv_亲亲', 'tv_调皮', 'tv_抠鼻', 'tv_鼓掌', 'tv_大哭', 'tv_疑问', 'tv_微笑',
                       'tv_思考', 'tv_呕吐', 'tv_晕',
                       'tv_点赞',
                       'tv_害羞', 'tv_睡着', 'tv_色', 'tv_吐血', 'tv_无奈', 'tv_再见', 'tv_流汗', 'tv_偷笑', 'tv_发财',
                       'tv_可爱', 'tv_馋',
                       'tv_腼腆',
                       'tv_鄙视', 'tv_闭嘴', 'tv_打脸', 'tv_困', 'tv_黑人问号', 'tv_抓狂', 'tv_生病', 'tv_流鼻血',
                       'tv_尴尬', 'tv_大佬',
                       'tv_流泪',
                       'tv_冷漠', 'tv_皱眉', 'tv_鬼脸', 'tv_调侃', 'tv_目瞪口呆', '坎公骑冠剑_吃鸡', '坎公骑冠剑_钻石',
                       '坎公骑冠剑_无语', '热词系列_不孤鸟',
                       '热词系列_对象',
                       '保卫萝卜_问号', '保卫萝卜_哇', '保卫萝卜_哭哭', '保卫萝卜_笔芯', '保卫萝卜_白眼',
                       '热词系列_多谢款待', '热词系列_EDG', '热词系列_我们是冠军', '脸红', '热词系列_破防了',
                       '热词系列_燃起来了'
            , '热词系列_住在B站', '热词系列_B站有房', '热词系列_365', '热词系列_最美的夜', '热词系列_干杯',
                       '热词系列_2022新年', '热词系列_奇幻时空', '热词系列_魔幻时空',
                       '虎年',
                       '热词系列_红红火火', '小电视_笑', '小电视_发愁', '小电视_赞', '小电视_差评', '小电视_嘟嘴',
                       '小电视_汗', '小电视_害羞', '小电视_吃惊',
                       '小电视_哭泣',
                       '小电视_太太喜欢', '小电视_好怒啊', '小电视_困惑', '小电视_我好兴奋', '小电视_思索', '小电视_无语'
                       ]  # 拥有的表情包
        self.User_Agent_List = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.61',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36 Edg/86.0.622.43',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.63',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4346.0 Safari/537.36 Edg/89.0.731.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4369.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.68',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.75',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.69 Safari/537.36 Edg/89.0.774.39',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.50',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.54',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.57',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.63',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4414.0 Safari/537.36 Edg/90.0.803.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4421.0 Safari/537.36 Edg/90.0.808.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4421.0 Safari/537.36 Edg/90.0.810.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4422.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36 Edg/90.0.818.62',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.30 Safari/537.36 Edg/90.0.818.14',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.41 Safari/537.36 Edg/90.0.818.22',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.51 Safari/537.36 Edg/90.0.818.27',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.46',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.49',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4433.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4435.0 Safari/537.36 Edg/91.0.825.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4460.0 Safari/537.36 Edg/91.0.849.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4471.0 Safari/537.36 Edg/91.0.864.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.19 Safari/537.36 Edg/91.0.864.11',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4476.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4482.0 Safari/537.36 Edg/92.0.874.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4495.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.55',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.30',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 Edg/101.0.1210.39',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.30',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36 Edg/102.0.1245.39',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.50',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53'
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 '
            'Edg/106.0.1370.47',
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        ]
        proxy_pool = [
        ]
        self.proxy_pool = list(map(eval, set(list(map(str, proxy_pool)))))
        self.ban_proxy_pool = list()
        self.s = requests.session()

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def get_pinglunreq(self, dynamic_id, rid, pn, _type, *mode):
        """
        3是热评，2是最新，大概
        :param dynamic_id:
        :param rid:
        :param pn:
        :param _type:
        :param mode:
        :return:
        """
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
        if len(str(rid)) == len(str(dynamic_id)):
            oid = dynamic_id
        else:
            oid = rid
        fakeuseragent = random.choice(self.User_Agent_List)
        pinglunheader = {
            'user-agent': fakeuseragent}
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=' + str(mode) + '&plat=1&_=' + str(int(time.time()))
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
            pinglunreq = self.s.request("GET", url=pinglunurl, data=pinglundata, headers=pinglunheader)
        except:
            traceback.print_exc()
            print('获取评论失败')
            print(self.timeshift(int(time.time())))
            # while 1:
            #     try:
            #         time.sleep(eval(input('输入等待时间')))
            #         break
            #     except:
            #         continue
            time.sleep(3)
            pinglunreq = self.get_pinglunreq(dynamic_id, rid, pn, _type)
            return pinglunreq
        return pinglunreq.text

    def panduanbiaoqingbao(self, emo):
        tihuanbiaoqing = []
        for biaoqing in emo:
            if (biaoqing not in self.hasemo):
                tihuanbiaoqing.append(biaoqing)
        return tihuanbiaoqing

    def thumb(self, dynamic_id, cookie, useragent, uid, csrf, card_stype=''):  # 为动态点赞标记
        thumbheader = {
            'authority': 'api.vc.bilibili.com',
            'method': 'POST',
            'path': '/dynamic_like/v1/dynamic_like/thumb',
            'scheme': 'https',
            'cookie': cookie,
            'user-agent': useragent,
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/{}'.format(dynamic_id),
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        }
        thumbdata = {
            'uid': uid,
            'dynamic_id': dynamic_id,
            'up': 1,
            'csrf_token': csrf,
            'csrf': csrf
        }
        thumburl = 'https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb'
        reqthumb = self.s.request('POST', url=thumburl, data=thumbdata, headers=thumbheader)
        if reqthumb.json().get('code') == 0:
            print('点赞成功')
        else:
            print('点赞失败')
            print(reqthumb.json())
            self.dianzanshibai.append(f'https://t.bilibili.com/{dynamic_id}\t{reqthumb.json()}')
        if card_stype != '' and card_stype is not None:
            res = asyncio.run(
                log_reporter.handleSelfDefReport(eventname='dynamic_thumb', url=f'https://t.bilibili.com/{dynamic_id}',
                                                 cookie=cookie
                                                 ,
                                                 ua=useragent
                                                 , ops={
                        'dynamic_id': dynamic_id, 'card_stype': card_stype
                    }))  # card_stype: DYNAMIC_TYPE_DRAW
            for i in res:
                asyncio.run(self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', cookie,
                                            useragent))

    def repost(self, dy, msg, cookie, useragent, uid, csrf):
        repostdata = {
            'uid': uid,
            'type': '1',
            'rid': dy,
            'content': msg,
            'repost_code': '30000',
            'from': 'create.comment',
            'extension': '{"emoji_type":1}',
            'csrf_token': csrf,
            'csrf': csrf
        }
        header = {"cookie": cookie,
                  "user-agent": useragent,
                  'origin': 'https://t.bilibili.com',
                  'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dy),
                  'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                  'sec-ch-ua-mobile': '?0',
                  'sec-ch-ua-platform': "\"Windows\"",
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'same-site',
                  'content-type': 'application/x-www-form-urlencoded',
                  'accept': 'application/json, text/plain, */*',
                  'accept-encoding': 'gzip, deflate, br',
                  'accept-language': 'zh-CN,zh;q=0.9'
                  }
        reposturl = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/reply'
        try:
            reqrepost = self.s.request('POST', reposturl, headers=header, data=repostdata)
        except Exception as e:
            # traceback.print_exc()
            # print(self.timeshift(int(time.time())))
            # time.sleep(eval(input('输入等待时间')))
            # self.repost(dy, msg, cookie, useragent, uid, csrf)
            traceback.print_exc()
            self.zhuanfashibai.append(f'https://t.bilibili.com/{dy}\tpost请求错误')
            return 0
        try:
            repostresult = json.loads(reqrepost.text)
        except:
            repostresult = {'data': {'errmsg': '转发失败'}}
        if not repostresult.get('data').get('errmsg'):
            print(reqrepost.text)
        print('转发动态结果：' + str(repostresult.get('data').get('errmsg')))
        if repostresult.get('data').get('errmsg') == None:
            self.zhuanfashibai.append(f'https://t.bilibili.com/{dy}\t{reqrepost.json()}')
            print(repostresult)

    def get_dynamic_detail(self, dynamic_id, _cookie='', _useragent='', log_report_falg=True):
        '''

        :param dynamic_id:
        :param _cookie:
        :param _useragent:
        :return:
        structure = {
            'dynamic_id': dynamic_id,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,

            'card_stype': card_stype,
            'top_dynamic': top_dynamic,

            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        '''
        if _cookie == '':
            headers = {
                "user-agent": random.choice(self.User_Agent_List),
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        else:
            headers = {
                "cookie": _cookie,
                "user-agent": _useragent,
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&id=' + str(
            dynamic_id) + '&gaia_source=Athena'

        try:
            dynamic_req = self.s.request('GET', url=url, headers=headers)
        except Exception as e:
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(10)
            print()
            traceback.print_exc()
            return self.get_dynamic_detail(dynamic_id, _cookie, _useragent)
        try:
            if dynamic_req.json().get('code') == 4101131:
                print(dynamic_req.text)
                return None
            dynamic_dict = json.loads(dynamic_req.text)
            dynamic_data = dynamic_dict.get('data')
            comment_type = dynamic_data.get('item').get('basic').get('comment_type')
            dynamic_type = '8'
            if str(comment_type) == '17':
                dynamic_type = '4'
            elif str(comment_type) == '1':
                dynamic_type = '8'
            elif str(comment_type) == '11':
                dynamic_type = '2'
            elif str(comment_type) == '12':
                dynamic_type = '64'
            card_stype = dynamic_data.get('item').get('type')
            dynamic_id = dynamic_data.get('item').get('id_str')
            dynamic_rid = dynamic_data.get('item').get('basic').get('comment_id_str')
            relation = dynamic_data.get('item').get('modules').get('module_author').get('following')
            author_uid = dynamic_data.get('item').get('modules').get('module_author').get('mid')
            author_name = dynamic_data.get('item').get('modules').get('module_author').get('name')
            pub_time = dynamic_data.get('item').get('modules').get('module_author').get('pub_time')
            pub_ts = dynamic_data.get('item').get('modules').get('module_author').get('pub_ts')
            official_verify_type = dynamic_data.get('item').get('modules').get('module_author').get(
                'official_verify').get('type')
            comment_count = dynamic_data.get('item').get('modules').get('module_stat').get('comment').get('count')
            forward_count = dynamic_data.get('item').get('modules').get('module_stat').get('forward').get('count')
            like_count = dynamic_data.get('item').get('modules').get('module_stat').get('like').get('count')
            dynamic_content1 = ''
            if dynamic_data.get('item').get('modules').get('module_dynamic').get('desc'):
                dynamic_content1 = dynamic_data.get('item').get('modules').get('module_dynamic').get('desc').get('text')
            dynamic_content2 = ''
            if dynamic_data.get('item').get('modules').get('module_dynamic').get('major'):
                if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('archive'):
                    dynamic_content2 = dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get(
                        'archive').get('desc') + dynamic_data.get('item').get('modules').get('module_dynamic').get(
                        'major').get(
                        'archive').get('title')
                if dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get('article'):
                    dynamic_content2 = dynamic_data.get('item').get('modules').get('module_dynamic').get('major').get(
                        'article').get('desc') + dynamic_data.get('item').get('modules').get('module_dynamic').get(
                        'major').get(
                        'article').get('title')
            dynamic_content = dynamic_content1 + dynamic_content2
            desc = dynamic_data.get('item').get('modules').get(
                'module_dynamic').get(
                'desc')
            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = dynamic_data.get('item').get('modules').get('module_stat').get('like').get('status')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                print('未关注的response')
                print(f'https://space.bilibili.com/{author_uid}')
        except Exception as e:
            print(f'https://t.bilibili.com/{dynamic_id}')
            print(dynamic_req.text)
            traceback.print_exc()
            if dynamic_req.json().get('code') == -412:
                print('412风控')
                time.sleep(10 * 60)
                return self.get_dynamic_detail(dynamic_id, _cookie, _useragent)
            if dynamic_req.json().get('code') == 4101128:
                print(dynamic_req.json().get('message'))
                time.sleep(10 * 60)
            # time.sleep(eval(input('输入等待时间')))
            return None

        top_dynamic = None
        try:
            module_tag = dynamic_data.get('item').get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    print(module_tag_text)
                    print('未知动态tag')
            else:
                top_dynamic = False
        except:
            top_dynamic = None

        orig_name = None
        orig_mid = None
        orig_official_verify = None
        orig_pub_ts = None
        orig_comment_count = None
        orig_forward_count = None
        orig_dynamic_content = None
        orig_like_count = None
        orig_relation = None
        orig_is_liked = None
        orig_dynamic_id = None
        orig_desc = None
        try:
            if dynamic_data.get('item').get('orig'):
                orig_dynamic_id = dynamic_data.get('item').get('orig').get('id_str')
                orig_mid = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('mid')
                orig_name = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('name')
                orig_pub_ts = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('pub_ts')
                if dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify'):
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify').get('type')
                else:
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'type')
                # orig_comment_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get('count')
                orig_dynamic_content1 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('desc'):
                    orig_dynamic_content1 = dynamic_data.get('item').get('orig').get('modules').get(
                        'module_dynamic').get(
                        'desc').get('text')
                orig_dynamic_content2 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major'):
                    if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major').get(
                            'archive'):
                        orig_dynamic_content2 = dynamic_data.get('item').get('orig').get('modules').get(
                            'module_dynamic').get('major').get('archive').get('desc')
                orig_dynamic_content = orig_dynamic_content1 + orig_dynamic_content2
                orig_desc = dynamic_data.get('item').get('orig').get('modules').get(
                    'module_dynamic').get(
                    'desc')
                orig_relation = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                    'following')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                print('非转发动态，无原动态')
        except:
            print(dynamic_req.text)
            traceback.print_exc()
        structure = {
            'dynamic_id': dynamic_id,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,

            'card_stype': card_stype,
            'top_dynamic': top_dynamic,

            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        if log_report_falg is True:
            if _cookie != '':
                res = asyncio.run(
                    log_reporter.handleSelfDefReport(eventname='dynamic_pv', url=f'https://t.bilibili.com/{dynamic_id}',
                                                     cookie=_cookie
                                                     ,
                                                     ua=_useragent
                                                     , ops={
                            'dynamic_id': dynamic_id, 'type': comment_type, 'card_stype': card_stype, 'oid': dynamic_rid
                        }))
                for i in res:
                    asyncio.run(
                        self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', _cookie,
                                        _useragent))
        return structure

    def dynamic_svr_v1_get_dynamic_detail(self, dynamic_id, _cookie='', _useragent='', log_report_falg=False):
        '''
        目前返回全是0，无法使用
        :param dynamic_id:
        :param _cookie:
        :param _useragent:
        :param log_report_falg:
        :return:
        '''
        if _cookie == '':
            headers = {
                "user-agent": random.choice(self.User_Agent_List),
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        else:
            headers = {
                "cookie": _cookie,
                "user-agent": _useragent,
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id=' + str(dynamic_id)

        try:
            dynamic_req = self.s.request('GET', url=url, headers=headers)
        except Exception as e:
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(10)
            print()
            traceback.print_exc()
            return self.dynamic_svr_v1_get_dynamic_detail(dynamic_id, _cookie, _useragent)
        try:
            if dynamic_req.json().get('code') == 4101131:
                print(dynamic_req.text)
                return None
            dynamic_dict = json.loads(dynamic_req.text)
            dynamic_data = dynamic_dict.get('data')
            dynamic_card = dynamic_data.get('card')
            dynamic_type = dynamic_card.get('desc').get('type')
            comment_type = '1'
            if str(dynamic_type) == '4':
                comment_type = '17'
            elif str(dynamic_type) == '8':
                comment_type = '1'
            elif str(dynamic_type) == '2':
                comment_type = '11'
            elif str(dynamic_type) == '64':
                comment_type = '12'
            card_stype = dynamic_type
            dynamic_id = dynamic_card.get('desc').get('dynamic_id_str')
            dynamic_rid = dynamic_card.get('desc').get('rid_str')
            relation = dynamic_card.get('display').get('relation').get('is_follow')
            author_uid = dynamic_card.get('desc').get('user_profile').get('info').get('uid')
            author_name = dynamic_card.get('desc').get('user_profile').get('info').get('uname')
            pub_time = self.timeshift(dynamic_card.get('desc').get('timestamp'))
            pub_ts = dynamic_card.get('desc').get('timestamp')
            official_verify_type = dynamic_card.get('desc').get('user_profile').get('card').get('official_verify').get(
                'type')
            dynamic_detail_card = json.loads(dynamic_card.get('card'))
            try:
                comment_count = dynamic_detail_card.get('stat').get('reply')
            except:
                if dynamic_card.get('desc').get('comment') is not None:
                    comment_count = dynamic_card.get('desc').get('comment')
                elif dynamic_detail_card.get('stats').get('reply'):
                    comment_count = dynamic_detail_card.get('stats').get('reply')
                else:
                    comment_count = 0
            forward_count = dynamic_card.get('desc').get('repost')
            like_count = dynamic_card.get('desc').get('like')
            dynamic_content1 = []

            if dynamic_detail_card.get('item'):
                if dynamic_detail_card.get('item').get('content'):
                    dynamic_content1.append(dynamic_detail_card.get('item').get('content'))
                if dynamic_detail_card.get('item').get('description'):
                    dynamic_content1.append(dynamic_detail_card.get('item').get('description'))

            dynamic_content2 = []
            if dynamic_detail_card.get('desc'):
                dynamic_content2.append(dynamic_detail_card.get('desc'))
            if dynamic_detail_card.get('dynamic'):
                dynamic_content2.append(dynamic_detail_card.get('dynamic'))
            if dynamic_detail_card.get('title'):
                dynamic_content2.append(dynamic_detail_card.get('title'))
            if dynamic_detail_card.get('summary'):
                dynamic_content2.append(dynamic_detail_card.get('summary'))
            if dynamic_detail_card.get('live_play_info'):
                if dynamic_detail_card.get('live_play_info').get('title'):
                    dynamic_content2.append(dynamic_detail_card.get('live_play_info').get('title'))
            if dynamic_detail_card.get('vest'):
                if dynamic_detail_card.get('vest').get('content'):
                    dynamic_content2.append(dynamic_detail_card.get('vest').get('content'))
            dynamic_content = '\n'.join(dynamic_content1) + '\n'.join(dynamic_content2)
            desc = dynamic_card.get('desc')
            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = dynamic_card.get('desc').get('is_liked')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                print('未关注的response')
                print(f'https://space.bilibili.com/{author_uid}')
        except Exception as e:
            print(f'https://t.bilibili.com/{dynamic_id}')
            print(dynamic_req.text)
            traceback.print_exc()
            if dynamic_req.json().get('code') == -412:
                print('412风控')
                time.sleep(10 * 60)
                return self.get_dynamic_detail(dynamic_id, _cookie, _useragent)
            if dynamic_req.json().get('code') == 4101128:
                print(dynamic_req.json().get('message'))
                time.sleep(10 * 60)
            # time.sleep(eval(input('输入等待时间')))
            return None

        top_dynamic = None
        try:
            module_tag = dynamic_data.get('item').get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    print(module_tag_text)
                    print('未知动态tag')
            else:
                top_dynamic = False
        except:
            top_dynamic = None
        pre_dy_id_str = dynamic_card.get('desc').get('pre_dy_id_str')
        if pre_dy_id_str == '0':
            pre_dy_id_str = None
        orig_name = None
        orig_mid = None
        orig_official_verify = None
        orig_pub_ts = None
        orig_comment_count = None
        orig_forward_count = None
        orig_dynamic_content = None
        orig_like_count = None
        orig_relation = None
        orig_is_liked = None
        orig_dynamic_id = None
        orig_desc = None

        try:
            if dynamic_card.get('desc').get('origin'):
                dynamic_card_origin = dynamic_card.get('desc').get('origin')
                dynamic_detail_card_origin = json.loads(dynamic_detail_card.get('origin'))
                orig_dynamic_id = dynamic_card_origin.get('dynamic_id_str')
                try:
                    orig_mid = dynamic_detail_card_origin.get('user').get('uid')
                except:
                    try:
                        orig_mid = dynamic_detail_card_origin.get('owner').get('mid')
                    except:
                        orig_mid = dynamic_detail_card_origin.get('author').get('mid')
                try:
                    orig_name = dynamic_detail_card_origin.get('user').get('name')
                except:
                    orig_name = dynamic_detail_card_origin.get('owner').get('name')
                try:
                    orig_pub_ts = dynamic_detail_card_origin.get('item').get('upload_time')
                except:
                    orig_pub_ts = dynamic_detail_card_origin.get('pubdate')

                orig_official_verify = dynamic_detail_card.get('origin_user').get('card').get('official_verify').get(
                    'type')
                # orig_comment_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get('count')
                orig_dynamic_content1 = []

                if dynamic_detail_card_origin.get('item'):
                    if dynamic_detail_card_origin.get('item').get('content'):
                        orig_dynamic_content1.append(dynamic_detail_card_origin.get('item').get('content'))
                    if dynamic_detail_card_origin.get('item').get('description'):
                        orig_dynamic_content1.append(dynamic_detail_card_origin.get('item').get('description'))

                orig_dynamic_content2 = []
                if dynamic_detail_card_origin.get('desc'):
                    orig_dynamic_content2.append(dynamic_detail_card_origin.get('desc'))
                if dynamic_detail_card_origin.get('dynamic'):
                    orig_dynamic_content2.append(dynamic_detail_card_origin.get('desc'))
                if dynamic_detail_card_origin.get('title'):
                    orig_dynamic_content2.append(dynamic_detail_card_origin.get('title'))
                if dynamic_detail_card_origin.get('summary'):
                    orig_dynamic_content2.append(dynamic_detail_card_origin.get('summary'))
                if dynamic_detail_card_origin.get('live_play_info'):
                    if dynamic_detail_card_origin.get('live_play_info').get('title'):
                        orig_dynamic_content2.append(dynamic_detail_card_origin.get('live_play_info').get('title'))
                if dynamic_detail_card_origin.get('vest'):
                    if dynamic_detail_card_origin.get('vest').get('content'):
                        orig_dynamic_content2.append(dynamic_detail_card_origin.get('vest').get('content'))
                orig_dynamic_content = '\n'.join(orig_dynamic_content1) + '\n'.join(orig_dynamic_content2)
                orig_desc = dynamic_detail_card_origin
                orig_relation = dynamic_card.get('display').get('origin').get('relation').get('is_follow')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                print('非转发动态，无原动态')
        except:
            print(dynamic_req.text)
            traceback.print_exc()
        structure = {
            'dynamic_id': dynamic_id,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,

            'card_stype': card_stype,
            'top_dynamic': top_dynamic,
            'pre_dy_id_str': pre_dy_id_str,  # 间接动态（也就是这个动态转发的动态，当转发的是原动态时和原动态值相同

            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        if log_report_falg is True:
            if _cookie != '':
                res = asyncio.run(
                    log_reporter.handleSelfDefReport(eventname='dynamic_pv', url=f'https://t.bilibili.com/{dynamic_id}',
                                                     cookie=_cookie
                                                     ,
                                                     ua=_useragent
                                                     , ops={
                            'dynamic_id': dynamic_id, 'type': comment_type, 'card_stype': card_stype, 'oid': dynamic_rid
                        }))
                for i in res:
                    asyncio.run(
                        self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', _cookie,
                                        _useragent))
        return structure

    def polymer_web_dynamic_v1_opus_detail(self, dynamic_id, _cookie='', _useragent='',
                                           log_report_falg=False) -> dict or None:
        '''
        https://api.bilibili.com/x/polymer/web-dynamic/v1/opus/detail?id=
        获取动态详情 目前无法获取视频或者转发的详情，谨慎使用！ ————5.22.2023
        :param dynamic_id:
        :param _cookie:
        :param _useragent:
        :param log_report_falg:
        :return:
        '''
        if _cookie == '':
            headers = {
                "user-agent": random.choice(self.User_Agent_List),
                'origin': 'https://t.bilibili.com',
                'referer': 'https://www.bilibili.com/opus/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        else:
            headers = {
                "cookie": _cookie,
                "user-agent": _useragent,
                'origin': 'https://t.bilibili.com',
                'referer': 'https://www.bilibili.com/opus/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
        url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/opus/detail?id=' + str(dynamic_id)

        try:
            dynamic_req = self.s.request('GET', url=url, headers=headers)
        except Exception as e:
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(10)
            print()
            traceback.print_exc()
            return self.get_dynamic_detail(dynamic_id, _cookie, _useragent)
        try:
            if dynamic_req.json().get('code') == 4101131:
                print(dynamic_req.text)
                return None
            dynamic_dict = json.loads(dynamic_req.text)
            dynamic_data = dynamic_dict.get('data')
            comment_type = dynamic_data.get('item').get('basic').get('comment_type')
            dynamic_type = '8'
            if str(comment_type) == '17':
                dynamic_type = '4'
            elif str(comment_type) == '1':
                dynamic_type = '8'
            elif str(comment_type) == '11':
                dynamic_type = '2'
            elif str(comment_type) == '12':
                dynamic_type = '64'
            dynamic_modules = dynamic_data.get('item').get('modules')
            module_author = dict()
            module_content = dict()
            module_stat = dict()
            for module in dynamic_modules:
                if module.get('module_type') == "MODULE_TYPE_AUTHOR":
                    module_author = module.get('module_author')
                elif module.get('module_type') == "MODULE_TYPE_CONTENT":
                    module_content = module.get('module_content')
                elif module.get('module_type') == "MODULE_TYPE_STAT":
                    module_stat = module.get('module_stat')
            card_stype = dynamic_data.get('item').get('type')
            dynamic_id = dynamic_data.get('item').get('id_str')
            dynamic_rid = dynamic_data.get('item').get('basic').get('comment_id_str')
            relation = module_author.get('following')
            author_uid = module_author.get('mid')
            author_name = module_author.get('name')
            pub_time = module_author.get('pub_time')
            pub_ts = module_author.get('pub_ts')
            official_verify_type = module_author.get(
                'official').get('type')
            comment_count = module_stat.get('comment').get('count')
            forward_count = module_stat.get('forward').get('count')
            like_count = module_stat.get('like').get('count')
            dynamic_content = ''
            for para in module_content.get('paragraphs'):
                if para.get('text'):
                    for nodes in para.get('text').get('nodes'):
                        __type = nodes.get('type')
                        if __type == "TEXT_NODE_TYPE_RICH":
                            dynamic_content += nodes.get('rich').get('text')
                        if __type == 'TEXT_NODE_TYPE_WORD':
                            dynamic_content += nodes.get('word').get('words')
            desc = dynamic_data.get('item')
            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = module_stat.get('like').get('status')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                print('未关注的response')
                print(f'https://space.bilibili.com/{author_uid}')
        except Exception as e:
            print(f'https://t.bilibili.com/{dynamic_id}')
            print(dynamic_req.text)
            traceback.print_exc()
            if dynamic_req.json().get('code') == -412:
                print('412风控')
                time.sleep(10 * 60)
                return self.get_dynamic_detail(dynamic_id, _cookie, _useragent)
            if dynamic_req.json().get('code') == 4101128:
                print(dynamic_req.json().get('message'))
                time.sleep(10 * 60)
            # time.sleep(eval(input('输入等待时间')))
            return None

        top_dynamic = None
        try:
            module_tag = dynamic_data.get('item').get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    print(module_tag_text)
                    print('未知动态tag')
            else:
                top_dynamic = False
        except:
            top_dynamic = None

        orig_name = None
        orig_mid = None
        orig_official_verify = None
        orig_pub_ts = None
        orig_comment_count = None
        orig_forward_count = None
        orig_dynamic_content = None
        orig_like_count = None
        orig_relation = None
        orig_is_liked = None
        orig_dynamic_id = None
        orig_desc = None
        try:
            if dynamic_data.get('item').get('orig'):
                orig_dynamic_id = dynamic_data.get('item').get('orig').get('id_str')
                orig_mid = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('mid')
                orig_name = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('name')
                orig_pub_ts = dynamic_data.get('item').get('orig').get('modules').get('module_author').get('pub_ts')
                if dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify'):
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'official_verify').get('type')
                else:
                    orig_official_verify = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                        'type')
                # orig_comment_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get('count')
                orig_dynamic_content1 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('desc'):
                    orig_dynamic_content1 = dynamic_data.get('item').get('orig').get('modules').get(
                        'module_dynamic').get(
                        'desc').get('text')
                orig_dynamic_content2 = ''
                if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major'):
                    if dynamic_data.get('item').get('orig').get('modules').get('module_dynamic').get('major').get(
                            'archive'):
                        orig_dynamic_content2 = dynamic_data.get('item').get('orig').get('modules').get(
                            'module_dynamic').get('major').get('archive').get('desc')
                orig_dynamic_content = orig_dynamic_content1 + orig_dynamic_content2
                orig_desc = dynamic_data.get('item').get('orig').get('modules').get(
                    'module_dynamic').get(
                    'desc')
                orig_relation = dynamic_data.get('item').get('orig').get('modules').get('module_author').get(
                    'following')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                print('非转发动态，无原动态')
        except:
            print(dynamic_req.text)
            traceback.print_exc()
        structure = {
            'dynamic_id': dynamic_id,
            'desc': desc,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,

            'card_stype': card_stype,
            'top_dynamic': top_dynamic,

            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
            'orig_desc': orig_desc
        }
        if log_report_falg is True:
            if _cookie != '':
                res = asyncio.run(
                    log_reporter.handleSelfDefReport(eventname='dynamic_pv', url=f'https://t.bilibili.com/{dynamic_id}',
                                                     cookie=_cookie
                                                     ,
                                                     ua=_useragent
                                                     , ops={
                            'dynamic_id': dynamic_id, 'type': comment_type, 'card_stype': card_stype, 'oid': dynamic_rid
                        }))
                for i in res:
                    asyncio.run(
                        self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', _cookie,
                                        _useragent))
        return structure

    async def log_report(self, log_data, origin_url, refer_url, cookie, ua):
        url = 'https://data.bilibili.com/log/web'
        params = log_data
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': cookie,
            'origin': origin_url,
            'referer': refer_url,
            'user-agent': ua,
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'same-site'
        }
        req = self.s.post(url=url, params=params, headers=headers)
        print(f'log_report结果：{req.text}')

    def comment(self, dynamic_id, msg, _type, rid, cookie, useragent, csrf, username):  # 发送评论
        print(f'评论内容：{msg}')
        if len(rid) == len(dynamic_id):
            oid = dynamic_id
        else:
            oid = rid
        commentheader = {
            'authority': 'api.bilibili.com',
            'method': 'POST',
            'path': '/x/v2/reply/add',
            'scheme': 'https',
            'accept': 'application/json,text/javascript,*/*;q=0.01',
            'cookie': cookie,
            'user-agent': useragent,
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        ctype = 17
        if str(_type) == '8':
            ctype = 1
        elif str(_type) == '4' or str(_type) == '1':
            ctype = 17
        elif str(_type) == '2':
            ctype = 11
        elif str(_type) == '64':
            ctype = 12
        commentdata = {
            'oid': oid,
            'type': ctype,
            'message': msg,
            'ordering': 'time',
            'jsonp': 'jsonp',
            'plat': '1',
            'csrf': csrf,
        }
        commenturl = 'https://api.bilibili.com/x/v2/reply/add'
        reqcomment = self.s.request('POST', url=commenturl, data=commentdata, headers=commentheader)
        comment_dict = json.loads(reqcomment.text)
        try:
            commentresult = comment_dict.get('data').get('success_toast')
        except:
            commentresult = None
            url = 'https://t.bilibili.com/' + str(dynamic_id)
            self.pinglunshibai.append(f'{url}\t{comment_dict}')
            traceback.print_exc()
            print(reqcomment.text)
        time.sleep(2)
        if int(comment_dict.get('code')) == 12015:
            while 1:
                try:
                    print(self.timeshift(time.time()))
                    print(commentresult)
                    # time.sleep(eval(input('输入等待时间')))
                    time.sleep(10 * 60)
                    print('验证码了，等十分钟')
                    break
                except:
                    continue
        if comment_dict.get('message') == 'UP主已关闭评论区':
            pass
        elif self._check_comment(username, dynamic_id, rid, _type):
            print('评论存在')
        else:
            print(username)
            print('评论被吞')
            print('评论内容：{}'.format(msg))
            try:
                with open(CONFIG.root_dir+'动态转抽_新版2.0/评论log/comment_log.csv', 'a+', encoding='utf-8') as c:
                    c.writelines(
                        '{0}\t{1}\t{2}\thttps://t.bilibili.com/{2}\t{3}\t{4}\n'.format(self.timeshift(time.time()),
                                                                                       username,
                                                                                       dynamic_id, repr(msg),
                                                                                       comment_dict))
            except:
                with open(CONFIG.root_dir+'动态转抽_新版2.0/评论log/comment_log.csv', 'w', encoding='utf-8') as c:
                    c.writelines(
                        '{0}\t{1}\t{2}\thttps://t.bilibili.com/{2}\t{3}\t{4}\n'.format(self.timeshift(time.time()),
                                                                                       username,
                                                                                       dynamic_id, repr(msg),
                                                                                       comment_dict))
        time.sleep(random.choice(self.sleeptime))
        if commentresult != "发送成功":
            cuowuid = 'https://t.bilibili.com/' + str(dynamic_id)
            self.pinglunshibai.append(f'{cuowuid}\t{comment_dict}')
            print('评论失败\n' + str(commentresult) + '： https://t.bilibili.com/' + str(dynamic_id))
            print('oid：' + str(oid))
            print('rid：' + str(rid))
            print('dynamic_id：' + str(dynamic_id))
            message = comment_dict.get('message')
            print(message)
            print(self.timeshift(int(time.time())))
            # while 1:
            #     try:
            #         time.sleep(eval(input('输入等待时间')))
            #         break
            #     except:
            #         continue
            return None
        print('评论动态结果：' + str(commentresult) + '；评论类型：' + str(ctype))
        commentrpid = comment_dict.get('data').get('rpid')

        res = asyncio.run(
            log_reporter.handleSelfDefReport(eventname='dynamic_comment', url=f'https://t.bilibili.com/{dynamic_id}',
                                             cookie=cookie,
                                             ua=useragent,
                                             ops={
                                                 'type': ctype, 'oid': oid
                                             }))  # card_stype: DYNAMIC_TYPE_DRAW
        for i in res:
            asyncio.run(self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', cookie,
                                        useragent))

        return 'https://t.bilibili.com/{}#reply{}'.format(dynamic_id, commentrpid)

    def _comment_like(self, comment_dict, oid, ctype, cookie, useragent, csrf):
        try:
            commentrpid = comment_dict.get('data').get('rpid')
        except:
            commentrpid = None
        if commentrpid == None or str(commentrpid) == '0':
            print('评论点赞失败\t\t\t原因：rpid获取失败')
        else:
            print('获取rpid=' + str(commentrpid))
            pinglundianzanurl = 'https://api.bilibili.com/x/v2/reply/action'
            pinglundianzanheaders = {
                'authority': 'api.bilibili.com',
                'method': 'POST',
                'cookie': cookie,
                'user-agent': useragent,
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/',
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
            pinglundianzandata = {'oid': oid,
                                  'type': ctype,
                                  'rpid': commentrpid,
                                  'action': '1',
                                  'ordering': 'time',
                                  'jsonp': 'jsonp',
                                  'csrf': csrf
                                  }
            pinglundianzanreq = self.s.request('POST', url=pinglundianzanurl, data=pinglundianzandata,
                                               headers=pinglundianzanheaders)
            pinglundianzan_dict = json.loads(pinglundianzanreq.text)
            dianzancode = pinglundianzan_dict.get('code')
            if dianzancode == 0:
                print('评论点赞成功')
            else:
                print('评论点赞失败\t\t\t原因：')
                print(pinglundianzan_dict)

    def comment_with_thumb(self, dy, msg, _type, rid, cookie, useragent, csrf, username):  # 发送评论
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
        if len(rid) == len(dy):
            oid = dy
        else:
            oid = rid
        commentheader = {
            'authority': 'api.bilibili.com',
            'method': 'POST',
            'path': '/x/v2/reply/add',
            'scheme': 'https',
            'accept': 'application/json,text/javascript,*/*;q=0.01',
            'cookie': cookie,
            'user-agent': useragent,
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dy),
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        ctype = 17
        if str(_type) == '8':
            ctype = 1
        elif str(_type) == '4' or str(_type) == '1':
            ctype = 17
        elif str(_type) == '2':
            ctype = 11
        elif str(_type) == '64':
            ctype = 12
        commentdata = {
            'oid': oid,
            'type': ctype,
            'message': msg,
            'ordering': 'time',
            'jsonp': 'jsonp',
            'plat': '1',
            'csrf': csrf,
        }
        commenturl = 'https://api.bilibili.com/x/v2/reply/add'
        reqcomment = self.s.request('POST', url=commenturl, data=commentdata, headers=commentheader)
        comment_dict = json.loads(reqcomment.text)
        url = 'https://t.bilibili.com/' + str(dy)
        try:
            commentresult = comment_dict.get('data').get('success_toast')
        except:
            commentresult = None
            url = 'https://t.bilibili.com/' + str(dy)
            self.pinglunshibai.append(f'{url}\t{comment_dict}')
            print(reqcomment.text)
        time.sleep(2)
        if comment_dict.get('code') != 0:
            self.pinglunshibai.append(f'{url}\t{comment_dict}')
            print(comment_dict)
            print(dy, msg, _type, rid, cookie, useragent, csrf, username)
            print(commentdata)
            print('评论失败')
        if int(comment_dict.get('code')) == 12015:
            while 1:
                try:
                    print(self.timeshift(time.time()))
                    print('验证码了，休息10分钟')
                    time.sleep(600)
                    break
                except:
                    continue
        if self._check_comment(username, dy, rid, _type):
            print('评论存在')
            ###########################
            if csrf == csrf2:
                self._comment_like(comment_dict, oid, ctype, cookie2, ua2, csrf2)
                time.sleep(1)
            elif csrf == csrf3:
                self._comment_like(comment_dict, oid, ctype, cookie3, ua3, csrf3)
                time.sleep(1)
            elif csrf == csrf4:
                self._comment_like(comment_dict, oid, ctype, cookie4, ua4, csrf4)
                time.sleep(1)
            ################################################
        else:
            print(username)
            print('评论被吞')
            try:
                with open(CONFIG.root_dir+'动态转抽_新版2.0/评论log/comment_log.csv', 'a+', encoding='utf-8') as c:
                    c.writelines(
                        '{0}\t{1}\t{2}\thttps://t.bilibili.com/{2}\t{3}\t{4}\n'.format(self.timeshift(time.time()),
                                                                                       username,
                                                                                       dy, repr(msg), comment_dict))
            except:
                with open(CONFIG.root_dir+'动态转抽_新版2.0/评论log/comment_log.csv', 'w', encoding='utf-8') as c:
                    c.writelines(
                        '{0}\t{1}\t{2}\thttps://t.bilibili.com/{2}\t{3}\t{4}\n'.format(self.timeshift(time.time()),
                                                                                       username,
                                                                                       dy, repr(msg), comment_dict))
        time.sleep(random.choice(self.sleeptime))

        if commentresult != "发送成功":
            print('评论失败\n' + str(commentresult) + '： https://t.bilibili.com/' + str(dy))
            print('oid：' + str(oid))
            print('rid：' + str(rid))
            print('dynamic_id：' + str(dy))
            message = comment_dict.get('message')
            print(message)
            print(self.timeshift(int(time.time())))
            # while 1:
            #     try:
            #         time.sleep(eval(input('输入等待时间')))
            #         break
            #     except:
            #         continue
            return None
        print('评论动态结果：' + str(commentresult) + '；评论类型：' + str(ctype))
        commentrpid = comment_dict.get('data').get('rpid')
        return 'https://t.bilibili.com/{}#reply{}'.format(dy, commentrpid)

    def choujiangxinxipanduan(self, tcontent):  # 动态内容过滤条件
        '''
        相对粗略
        抽奖信息判断      是抽奖返回None 不是抽奖返回1
        :param tcontent:
        :return:
        '''
        tcontent = re.sub('@(.{0,12}?) ', '', tcontent)
        tcontent = Converter('zh-hans').convert(tcontent)
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
        matchobj_65 = re.match('.*抽奖.{0,10}送.*', tcontent, re.DOTALL)
        matchobj_64 = re.match('.*评论.{0,10}补贴.*\\d+.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*抽.{0,10}带走.*', tcontent, re.DOTALL)
        matchobj_59 = re.match('.*补贴.{0,10}\d+元.*', tcontent, re.DOTALL)
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
        matchobj_18 = re.match('.*关注\+评论，随机选.*', tcontent, re.DOTALL)
        matchobj_17 = re.match('.*互动抽奖.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_16 = re.match('.*关注.*转发.*抽.*', tcontent, re.DOTALL)
        matchobj_15 = re.match('.*转.*评.*赞.*送', tcontent, re.DOTALL)
        matchobj_14 = re.match('.*评论区.*抽.{0,9}送.*', tcontent, re.DOTALL)
        matchobj_13 = re.match('.*关注.*评论.*抽.*', tcontent, re.DOTALL)
        matchobj_12 = re.match('.*评论转发点赞.*抽取.*送.*', tcontent, re.DOTALL)
        matchobj_11 = re.match('.*关注\+评论.*随机选.*送.*', tcontent, re.DOTALL)
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
        tcontent = Converter('zh-hans').convert(tcontent)
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
        matchobj_64 = re.match('.*评论.{0,10}补贴.*\\d+.*', tcontent, re.DOTALL)
        matchobj_63 = re.match('.*车专扌由.*', tcontent, re.DOTALL)
        matchobj_62 = re.match('.*车关.{0,20}送.*', tcontent, re.DOTALL)
        matchobj_61 = re.match('.*抽.{0,10}补贴.*', tcontent, re.DOTALL)
        matchobj_60 = re.match('.*抽.{0,10}带走.*', tcontent, re.DOTALL)
        matchobj_59 = re.match('.*补贴.{0,10}\d+元.*', tcontent, re.DOTALL)
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
        zhuanfapanduan15 = re.match('.*转评|.*转加关|.*转\+关', str(dongtaineirong), re.DOTALL)
        if (zhuanfapanduan1 == None and zhuanfapanduan3 == None and zhuanfapanduan4 == None
                and zhuanfapanduan5 == None and zhuanfapanduan6 == None and zhuanfapanduan10 == None and zhuanfapanduan11 == None and zhuanfapanduan12 == None
                and zhuanfapanduan13 == None and zhuanfapanduan14 == None and zhuanfapanduan15 == None
                or zhuanfapanduan_1 != None or zhuanfapanduan_2 != None or zhuanfapanduan_3 != None or zhuanfapanduan_4 != None
        ):
            return None
        else:
            return 1

    def caihongpi(self, username, uname, *uname1):  # username:脚本使用者的名字     uname：发起抽奖者的名字
        caihongpi = random.choice(self.official_caihongpilist)
        if uname1 == ():
            if uname in up_nickname_dict.keys():
                if '{1}' in caihongpi:
                    retmsg = caihongpi.format(up_nickname_dict.get(uname), username)
                else:
                    retmsg = caihongpi.format(up_nickname_dict.get(uname))
            else:
                if '{1}' in caihongpi:
                    retmsg = caihongpi.format(uname, username)
                else:
                    retmsg = caihongpi.format(uname)
                self.None_nickname.append(uname)
        else:
            uname1 = uname1[0]
            if uname in up_nickname_dict.keys():
                if uname1 in up_nickname_dict.keys():
                    if '{1}' in caihongpi:
                        retmsg = caihongpi.format(
                            '{0}和{1}'.format(up_nickname_dict.get(uname), up_nickname_dict.get(uname1)), username)
                    else:
                        retmsg = caihongpi.format(
                            '{0}和{1}'.format(up_nickname_dict.get(uname), up_nickname_dict.get(uname1)))
                else:
                    if '{1}' in caihongpi:
                        retmsg = caihongpi.format('{0}和{1}'.format(up_nickname_dict.get(uname), uname1), username)
                    else:
                        retmsg = caihongpi.format('{0}和{1}'.format(up_nickname_dict.get(uname), uname1))
                    self.None_nickname.append(uname1)
            else:
                if uname1 in up_nickname_dict.keys():
                    if '{1}' in caihongpi:
                        retmsg = caihongpi.format(
                            '{0}和{1}'.format(uname, up_nickname_dict.get(uname1)), username)
                    else:
                        retmsg = caihongpi.format(
                            '{0}和{1}'.format(uname, up_nickname_dict.get(uname1)))
                else:
                    if '{1}' in caihongpi:
                        retmsg = caihongpi.format('{0}和{1}'.format(uname, uname1), username)
                    else:
                        retmsg = caihongpi.format('{0}和{1}'.format(uname, uname1))
                    self.None_nickname.append(uname1)
                self.None_nickname.append(uname)
        return retmsg + random.choice(self.xiaoweiba) + random.choice(self.xiaoweibawenan)

    def get_all_sixin(self, uid, cookie, ua):
        url = 'https://api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs?talker_id={}&session_type=1&size=10&begin_seqno=0&build=0&mobi_app=web'.format(
            uid)
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = self.s.get(url=url, headers=headers)
        return req.json()

    def dynamic_equip_share(self, item_id, cookie, ua, csrf):
        url = 'https://api.bilibili.com/x/garb/user/dynamic/equip/share'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        data = {
            'csrf': csrf,
            'part': 'pendant',
            'item_id': item_id
        }
        req = self.s.post(url=url, headers=headers, data=data)
        return req.json()

    def get_pendant_item_id_list(self, cookie, ua, csrf):
        mylist = list()
        url = 'https://api.bilibili.com/x/garb/mall/list?csrf={}&part=pendant&tab_id=22&pn=1&ps=20'.format(csrf)
        data = {
            'csrf': csrf,
            'part': 'pendant',
            'tab_id': 22,
            'pn': 1,
            'ps': 20
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = self.s.get(url=url, data=data, headers=headers)
        if not req.json().get('code'):
            total = req.json().get('data').get('page').get('total')
            plist = req.json().get('data').get('list')
            for i in plist:
                mylist.append(i.get('item_id'))
            time.sleep(1)
            for i in range(2, int(total / 20) + 2):
                url = 'https://api.bilibili.com/x/garb/mall/list?csrf={0}&part=pendant&tab_id=22&pn={1}&ps=20'.format(
                    csrf, i)
                data = {
                    'csrf': csrf,
                    'part': 'pendant',
                    'tab_id': 22,
                    'pn': i,
                    'ps': 20
                }
                req = self.s.get(url=url, data=data, headers=headers)
                if not req.json().get('code'):
                    plist = req.json().get('data').get('list')
                    for i in plist:
                        mylist.append(i.get('item_id'))
                    time.sleep(1)
        return mylist

    def rid_dynamic_video(self, rid, _type=8):
        """
获取type==8的rid动态
        :param rid:
        :param _type:
        :return:
        """
        print(f'当前type类型：{_type}')
        # p=random.choice(proxy_pool.get('http'))
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={rid}&type={_type}'
        data = {'rid': str(rid),
                'type': _type,
                }
        # ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'
        ua = 'Mozilla/5.0 (Windows Phone 8.1; ARM; Trident/7.0; Touch; rv:11.0; IEMobile/11.0; NOKIA; Lumia 530) like Gecko BingPreview/1.0b'
        headers = {
            'authority': 'api.vc.bilibili.com',
            'method': 'GET',
            'scheme': 'https',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/',
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                                                    random.choice(range(0, 255)), random.choice(range(0, 255))),
            'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                                              random.choice(range(0, 255)), random.choice(range(0, 255))),
            'From': 'bingbot(at)microsoft.com',
        }
        try:
            req = self.s.request("GET", url=url, data=data, headers=headers)
            req_dict = req.json()
        except Exception as e:
            print('error\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\n')
            traceback.print_exc()
            err = traceback.format_exc()
            print(err)
            print(self.timeshift(time.time()))
            print('进程被阻塞')
            time.sleep(60)
            return self.rid_dynamic_video(rid)
        # if req_dict.get('code') == 0 and req_dict.get('msg') == '' and req_dict.get('message') == '' and req_dict.get(
        #         'data').get('result') is None and _type == 2:
        #     req_dict = self.rid_dynamic(rid=rid, _type=8)
        return req_dict

    def dynamic_repost_view_repost(self, dynamic_id):
        '''
        获取转发详情
        :return:
        '''
        # TODO 114514
        url = 'https://api.live.bilibili.com/dynamic_repost/v1/dynamic_repost/view_repost'
        query = {
            'dynamic_id': dynamic_id
        }
        headers = {
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044207 Mobile Safari/537.36 MicroMessenger/6.7.3.1340(0x26070332) NetType/4G Language/zh_CN Process/tools",
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9',
        }
        req = requests.get(url=url, headers=headers, params=query)
        return req.json()

    def rid_dynamic(self, rid, _type=2):
        print(f'当前type类型：{_type}')
        # p=random.choice(proxy_pool.get('http'))
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={rid}&type={_type}'
        data = {'rid': str(rid),
                'type': _type,
                }
        # ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'
        # ua = 'Mozilla/5.0 (Windows Phone 8.1; ARM; Trident/7.0; Touch; rv:11.0; IEMobile/11.0; NOKIA; Lumia 530) like Gecko BingPreview/1.0b'
        ua = random.choice(self.User_Agent_List)
        headers = {
            'host': 'api.vc.bilibili.com',
            'authority': 'api.vc.bilibili.com',
            'method': 'GET',
            'path': f'/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?rid={rid}&type={_type}',
            'scheme': 'https',
            'accept': 'text/html,application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'origin': 'https://t.bilibili.com',
            'referer': f'https://t.bilibili.com/?rid={rid}&type={_type}',
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        try:
            req = self.s.request("GET", url=url, headers=headers)
            req_dict = req.json()
        except Exception as e:
            print('error\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\n')
            traceback.print_exc()
            err = traceback.format_exc()
            print(err)
            print(self.timeshift(time.time()))
            print('进程被阻塞')
            time.sleep(60)
            return self.rid_dynamic(rid)
        # if req_dict.get('code') == 0 and req_dict.get('msg') == '' and req_dict.get('message') == '' and req_dict.get(
        #         'data').get('result') is None and _type == 2:
        #     req_dict = self.rid_dynamic(rid=rid, _type=8)
        return req_dict

    def album_dynamic(self, rid, ):
        '''
        https://api.vc.bilibili.com/link_draw/v1/doc/detail?doc_id=
        通过doc_id,也就是后面的rid获取动态
        这个接口现在需要cookie验证了——2023.08.15
        :param rid:
        :return:
        '''
        # p=random.choice(proxy_pool.get('http'))
        url = f'https://api.vc.bilibili.com/link_draw/v1/doc/detail'
        params = {
            'doc_id': str(rid),
        }
        # ua = 'Mozilla/5.0 (compatible; bingbot/2.0 +http://www.bing.com/bingbot.htm)'
        # ua = 'Mozilla/5.0 (Windows Phone 8.1; ARM; Trident/7.0; Touch; rv:11.0; IEMobile/11.0; NOKIA; Lumia 530) like Gecko BingPreview/1.0b'
        ua = random.choice(self.User_Agent_List)
        headers = {
            'host': 'api.vc.bilibili.com',
            'authority': 'api.vc.bilibili.com',
            'method': 'GET',
            'path': f'/link_draw/v1/doc/detail?doc_id={rid}',
            'scheme': 'https',
            'accept': 'text/html,application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'origin': 'https://h.bilibili.com/',
            'referer': f'https://h.bilibili.com/{rid}',
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        try:
            req = self.s.request("GET", url=url, params=params, headers=headers)
            req_dict = req.json()
        except Exception as e:
            print('error\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\nerror\n')
            traceback.print_exc()
            err = traceback.format_exc()
            print(err)
            print(self.timeshift(time.time()))
            print('进程被阻塞')
            time.sleep(60)
            return self.rid_dynamic(rid)
        # if req_dict.get('code') == 0 and req_dict.get('msg') == '' and req_dict.get('message') == '' and req_dict.get(
        #         'data').get('result') is None and _type == 2:
        #     req_dict = self.rid_dynamic(rid=rid, _type=8)
        return req_dict

    def _check_ip(self, p):
        '''
        只检测http代理
        :param p:
        :return:
        '''
        try:
            url = 'http://httpbin.org/ip'
            return self.s.get(url, proxies=p).json()
        except:
            print('ip获取失败')
            return False

    def _check_comment(self, username, dynamic_id, rid, _type):  # 返回true代表评论存在，None代表评论被吞
        time.sleep(5)
        unamelist = list()
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
        fakeuseragent = random.choice(self.User_Agent_List)
        pinglunheader = {
            'user-agent': fakeuseragent,
            'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                                                    random.choice(range(0, 255)), random.choice(range(0, 255))),
            'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
                                              random.choice(range(0, 255)), random.choice(range(0, 255))),
        }
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=0&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=2&plat=1&_=' + str(int(time.time()))
        try:
            pinglunreq = self.s.request("GET", url=pinglunurl, headers=pinglunheader)
        except Exception as e:
            traceback.print_exc()
            print('获取评论失败')
            traceback.print_exc()
            print(self.timeshift(int(time.time())))
            # while 1:
            #     try:
            #         time.sleep(eval(input('输入等待时间')))
            #         break
            #     except:
            #         continue
            time.sleep(3)
            return None
        if pinglunreq.json().get('code') != 0:
            print('获取动态评论失败')
            print(username, dynamic_id, rid, _type, pinglunurl, pinglunreq.json())
            if pinglunreq.json().get('code') == -412:
                print('风控了')
                time.sleep(60 * 3600)
                return self._check_comment(username, dynamic_id, rid, _type)
        replies = pinglunreq.json().get('data').get('replies')
        for rp in replies:
            uname = rp.get('member').get('uname')
            unamelist.append(uname)
        if username in unamelist:
            return True
        else:
            print(username)
            print(unamelist)
            return None

    def x_share_add(self, aid, cookie, ua, csrf):
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        data = {
            'aid': aid,
            'jsonp': "jsonp",
            'csrf': csrf
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = self.s.post(url=url, data=data, headers=headers)
        print(req.text)
        return req.text

    def view_bvid(self, bvid):
        """
        bvid获取视频信息
        :param bvid:
        :return:json
        """
        url = 'https://api.bilibili.com/x/web-interface/view?bvid={}'.format(bvid)
        data = {
            'bvid': bvid
        }
        req = self.s.get(url=url, data=data)
        return req.json()

    def x_space_arc_search(self, mid, pn):
        """
获取用户空间视频json
        """
        url = 'https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=30&tid=0&pn={pn}&keyword=&order=pubdate&jsonp=jsonp'.format(
            mid=mid, pn=pn)
        req = self.s.get(url)
        return req.json()

    def cookie_constructor(self, fullcookie):
        '''
        获取cookie的字典格式
        :param fullcookie:
        :return:
        '''
        c_dict = dict()
        for i in fullcookie.split(';'):
            k = i.split('=')[0].strip()
            v = i.split('=')[1].strip()
            c_dict.update({k: v})
        return c_dict

    def Activity_ClockIn(self, cookie, ua):
        """
        B站漫画签到
        :param cookie:
        :param ua:
        返回json
        """
        url = 'https://manga.bilibili.com/twirp/activity.v1.Activity/ClockIn'
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': cookie,
            'user-agent': ua,
        }
        data = {
            'platform': 'android'
        }
        req = self.s.request(method='POST', url=url, headers=headers, data=data)
        print(req.json())
        return req.json()

    def _appsign(self, params, appkey='1d8b6e7d45233436', appsec='560c52ccd288fed045859ed18bffd973'):
        '为请求参数进行 api 签名'
        params.update({'appkey': appkey})
        params = dict(sorted(params.items()))  # 重排序参数 key
        query = urllib.parse.urlencode(params)  # 序列化参数
        sign = hashlib.md5((query + appsec).encode()).hexdigest()  # 计算 api 签名
        params.update({'sign': sign})
        return params

    def client_query(self, params, *appkey):
        if appkey != ():
            signed_params = self._appsign(params, appkey[0])
        else:
            signed_params = self._appsign(params)
        query = urllib.parse.urlencode(signed_params)
        return query

    def getbuvid3(self, uid, target_url, cookie, ua):
        url = 'https://api.bilibili.com/x/web-frontend/getbuvid'
        data = {
            'mid': uid,
            'fts': '',
            'url': parse.quote_plus(target_url),
            'proid': 3,
            'ptype': 2,
            'module': "game",
            'ajaxtag': "",
            'ajaxid': "",
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = self.s.get(url=url, data=data, headers=headers)
        return req.json().get('data').get('buvid')

    def space_top_set(self, dynamic_id, csrf, uid, cookie, ua):
        url = 'https://api.vc.bilibili.com/dynamic_mix/v1/dynamic_mix/space_top_set'
        data = {
            'dynamic_id': dynamic_id,
            'csrf': csrf
        }
        headers = {
            'origin': 'https://space.bilibili.com',
            'referer': 'https://space.bilibili.com/{}/dynamic?spm_id_from=444.42.0.0'.format(uid),
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
        }
        req = self.s.post(url=url, data=data, headers=headers)
        print(req.text)

    def login_check(self, cookie, ua):
        headers = {
            'User-Agent': ua,
            'cookie': cookie
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        res = self.s.get(url=url, headers=headers).json()
        if res['data']['isLogin'] == True:
            name = res['data']['uname']
            print('登录成功,当前账号用户名为%s' % name)
            return {'name': res['data']['uname'], 'uid': res['data']['mid']}
        else:
            print('登陆失败,请重新登录')
            sys.exit('登陆失败,请重新登录')

    def name_to_uid(self, uname):
        url = f'https://api.vc.bilibili.com/dynamic_mix/v1/dynamic_mix/name_to_uid?names={uname}&teenagers_mode=0'
        req = self.s.get(url=url)
        if req.json().get('data').get('uid_list'):
            return req.json().get('data').get('uid_list')[0].get('uid')
        else:
            return ''

    def raw_text_process(self, raw_text):
        def combine_check(input_str):
            if not '@' in input_str and not '[' in input_str and not ']' in input_str:
                return True
            else:
                return False

        def content_split(_raw_text):
            a = _raw_text.split(' ')
            templist1 = []
            for i in a:
                if '@' in i:
                    templist1.append(i)
                    templist1.append(' ')
                elif '[' in i and ']' in i:
                    templist1.extend(re.findall('(\[.*?])', i))
                    i = re.sub('(\[.*?])', '', i)
                    templist1.append(i)
                else:
                    templist1.append(i)
            start = 0
            end = len(templist1) - 1
            for i in range(len(templist1)):
                if templist1[i] == '':
                    templist1[i] = ' '
            while 1:
                if start >= end: break
                if combine_check(templist1[start]):
                    if combine_check(templist1[start + 1]):
                        templist1[start] = templist1[start] + templist1[start + 1]
                        templist1.pop(start + 1)
                        end -= 1
                        continue
                start += 1
            return templist1

        if raw_text == ' ' or raw_text == '':
            raw_text = '转发动态'
        split_content = content_split(raw_text)
        c = []
        for i in split_content:
            if '[' in i and ']' in i:
                c.append({
                    'biz_id': '',
                    'raw_text': i,
                    'type': 9
                })
            elif '@' in i:
                mid = self.name_to_uid(i[1:])
                if mid:
                    c.append({
                        'biz_id': mid,
                        'raw_text': i,
                        'type': 2
                    })
                else:
                    c.append({
                        'biz_id': '',
                        'raw_text': i,
                        'type': 1
                    })
            else:
                c.append({
                    'biz_id': '',
                    'raw_text': i,
                    'type': 1
                })
        return {'content': {'contents': c}}

    def reply_feed_create_dyn(self, uid, dynamic_id, raw_text, cookie, ua, csrf):
        """
        新版本的转发动态
        :param uid:自己的uid
        :param dynamic_id:
        :param raw_text:
        :param cookie:
        :param ua:
        :param csrf:
        :return: {"dyn_id":687243841675198471,"dyn_id_str":"687243841675198471","dyn_type":1,"dyn_rid":687243841740210243}}
        """

        def submit_check(__dynamic_id, __raw_text, __cookie, __ua, __csrf):
            __url = f'https://api.bilibili.com/x/dynamic/feed/create/submit_check?csrf={__csrf}'
            __data = self.raw_text_process(__raw_text)
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': __cookie,
                'origin': 'https://t.bilibili.com',
                'referer': f'https://t.bilibili.com/{__dynamic_id}',
                'user-agent': __ua
            }
            __req = self.s.post(url=__url, data=json.dumps(__data), headers=headers)
            if __req.json().get('code') == 0:
                return True, __data
            else:
                print(__req.text)
                print('检查出错')
                return False

        def get_upload_id(__uid):
            return f'{__uid}_{int(time.time())}_{math.floor(1e3 * random.random())}'

        res = submit_check(dynamic_id, raw_text, cookie, ua, csrf)
        time.sleep(0.2)
        if res[0]:
            url = f'https://api.bilibili.com/x/dynamic/feed/create/dyn?csrf={csrf}'
            data = {
                'dyn_req': {"content": res[1].get('content'), "scene": 4, "upload_id": get_upload_id(uid),
                            "meta": {"app_meta":
                                         {"from": "create.dynamic.web",
                                          "mobi_app": "web"}}},
                "web_repost_src": {"dyn_id_str": str(dynamic_id)}
            }
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': cookie,
                'origin': 'https://t.bilibili.com',
                'referer': f'https://t.bilibili.com/{dynamic_id}',
                'user-agent': ua
            }
            req = self.s.post(url=url, data=json.dumps(data), headers=headers)
            if req.json().get('code') == 0:
                print('转发成功')
                return req.json().get('data')
            # {'dyn_id': 687256039630831623, 'dyn_id_str': '687256039630831623', 'dyn_type': 1, 'dyn_rid': 687256039451525142}
            else:
                print('转发失败')
                print(req.json())
                self.zhuanfashibai.append(f'https://t.bilibili.com/{dynamic_id}\t{req.json()}')

    def relation_modify(self, act, fid, cookie, ua, csrf):
        """
        :param act: 1是关注，2是取关
        :param fid: 关注对象uid
        :param cookie:
        :param ua:
        :param csrf:
        :return:
        """
        url = f'https://api.bilibili.com/x/relation/modify?act={act}&fid={fid}&spmid=444.42&re_src=0&csrf={csrf}'
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json;charset=UTF-8',
            'cookie': cookie,
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/',
            'user-agent': ua
        }
        req = self.s.post(url=url, headers=headers)
        if req.json().get('code') == 0:
            if act == 1:
                print(f'关注操作成功\t关注了 https://space.bilibili.com/{fid}/dynamic')
                return True
            else:
                print('取关操作成功\t取关了 https://space.bilibili.com/{fid}/dynamic')
                return True
        else:
            print(req.text)
            print('操作失败')
            self.guanzhushibai.append(f'https://space.bilibili.com/{fid}\t{req.json()}')
            return False

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

    def huifuneirong(self, official_type, content, dynamic_id, rid, _type, pre_dynamic_uname,
                     *origin_dynamic_uname):  # 回复内容的判断
        """

        :param official_type: 账号认证类型，1官号；0黄v；-1一般人
        :param content: 动态内容
        :param dynamic_id: 动态id
        :param rid: 动态rid
        :param _type: 动态类型
        :param pre_dynamic_uname:间接转发的动态用户名
        :param origin_dynamic_uname: 原动态的用户名
        :return:
        """

        def huifuneirongpanduan(_reply_content_list, _premsg):
            for _i in range(self.pinglunzhuanbiancishu):
                bt = 0
                while 1:
                    _msg = ''.join(random.choice(_reply_content_list))
                    _sums = 0
                    for _wordcount in _reply_content_list:
                        _sums += len(_wordcount)
                    if len(_msg) <= int(self.range_copy_comment * _sums / len(_reply_content_list)):
                        break
                    elif bt > 10:
                        _msg = ''
                        break
                    else:
                        bt += 1
                _biaoqingbao = re.findall('(?<=\[)(.*?)(?=\])', _msg, re.DOTALL)
                if _biaoqingbao:
                    _tihuanbiaoqing = self.panduanbiaoqingbao(_biaoqingbao)
                    if _tihuanbiaoqing:
                        for _noemo in _tihuanbiaoqing:
                            _msg = _msg.replace(_noemo, random.choice(self.changyongemo))
                # msg += '[' + random.choice(self.changyongemo) + ']'
                if '盛百凡' in _msg:
                    continue
                if '@' in _msg:
                    if '@' in _premsg:
                        _msg = re.sub(r'@(.*?)', f'@{random.choice(self.at_member)} ', _msg, re.S)
                    else:
                        continue
                if '#' in _msg:
                    if '#' not in _premsg:
                        _msg = re.sub(r'(#.*?#)', '', _msg, re.S)
                if _premsg != '':
                    if _premsg in _msg:
                        print('附带premsg抄的评论：' + _msg)
                        return _msg
                    else:
                        print('附带premsg抄的评论：' + _premsg + _msg)
                        return _premsg + _msg
                print('无premsg抄的评论：' + _msg)
                return _msg

        try:
            if origin_dynamic_uname[0] == pre_dynamic_uname:
                origin_dynamic_uname = ()
        except:
            pass
        try:
            if origin_dynamic_uname is None:
                origin_dynamic_uname = ()
        except:
            pass
        msg = ''
        premsg = self.pre_msg_processing(content)

        if '评论你喜欢什么口味' in content:
            return random.choice(['巧克力', '香草', '蔓越莓味', '蓝莓', '芒果', '抹茶', ''])
        if '喜欢什么零食' in content or '你喜欢的零食' in content or '评论你喜欢吃的零食' in content or '评论你最喜欢吃的零食' in content:
            return random.choice(['薯片', '巧克力', '辣条', '麦丽素'])
        if '评论你喜欢的颜色' in content or '评论你喜欢什么颜色' in content or '评论你最喜欢哪个颜色' in content or '评论你最爱的颜色' in content:
            return random.choice(['白色', '黑色', '黄色', '绿色', '蓝色', '红色'])
        if '评论你暗恋的女神' in content or '评论你喜欢的女神' in content or '评论你喜欢的妹子' in content:
            return random.choice(['赵今麦', '杨幂', '高木', '朱茵', '朴信惠', '刘诗诗', '高圆圆', '迪丽热巴'])
        if '评论你最喜欢喝哪个口味' in content:
            return random.choice(
                ['柠檬', '白桃味', '白桃味yyds', '樱花白兰地风味', '草莓味', '水蜜桃', '冰激凌味', '荔枝'])
        if '评论说说' not in content and '评论区说说' not in content and '评论区留下' not in content \
                and '评论你白嫖' not in content and '评论区里交流' not in content and '告诉' not in content \
                and '说出你的答案' not in content and '评论区分享' not in content and '话题参与' not in content and '长按复制' not in content \
                and '评论你喜欢什么口味' not in content:
            pass
        else:
            if '长按复制' in content:
                if random.random() < self.chance_shangjiayingguang:
                    msg = random.choice(self.shangjiayingguang)
                    return premsg + msg

        if official_type == 1:  # 判断如果是官号是否有彩虹屁要说
            if random.random() < self.caihongpi_chance:  # 自定义彩虹屁的概率
                if '评论说说' not in content and '评论区说说' not in content and '评论区留下' not in content \
                        and '评论你白嫖' not in content and '评论区里交流' not in content and '告诉' not in content \
                        and '说出你的答案' not in content and '评论区分享' not in content and '话题参与' not in content and '长按复制' not in content \
                        and '评论你喜欢什么口味' not in content:
                    if origin_dynamic_uname == ():
                        msg = self.caihongpi(self.username, pre_dynamic_uname)
                        # if '京东卡' in content:
                        #     msg = '许愿京东卡[未来有你_打call]' + msg
                        # elif '大会员' in content:
                        #     msg = '许愿大会员[未来有你_打call]' + msg
                        print('使用官方彩虹屁')
                        return premsg + msg
                    else:
                        origin_dynamic_uname = origin_dynamic_uname[0]
                        msg = self.caihongpi(self.username, pre_dynamic_uname, origin_dynamic_uname)
                        # if '京东卡' in content or '京东E卡' in content:
                        #     msg = '许愿京东卡[未来有你_打call]' + msg
                        # elif '大会员' in content:
                        #     msg = '许愿大会员[未来有你_打call]' + msg
                        print('使用官方彩虹屁')
                        return premsg + msg
        else:
            if random.random() < self.non_official_chp_chance:
                msg = random.choice(self.non_official_chp)
                print('使用非官方彩虹屁')
                return premsg + msg

        # 抄评论部分/未获取到评论也将抄评论
        print('msg:', msg)
        if msg == '' or random.random() < self.chance_copy_comment:
            pn = 0
            qianpai_xishu = 0.8
            for i in range(self.pinglunzhuanbiancishu):
                print(f'第{i + 1}次获取评论')
                pinglun_req = self.get_pinglunreq(dynamic_id, rid, pn, _type)
                try:
                    pinglun_dict = json.loads(pinglun_req)
                    pinglun_count = pinglun_dict.get('data').get('cursor').get('all_count')
                except Exception as e:
                    print(e)
                    print(pinglun_req)
                    print('获取评论失败')
                    return '[吃瓜]'
                if pinglun_count != 0:
                    if json.loads(pinglun_req).get('code') == 0:
                        reply_content = []
                        top_reply_list = []
                        pinglun_list = pinglun_dict.get('data').get('replies')
                        top_reply = pinglun_dict.get('data').get('top_replies')
                        if top_reply:
                            for __i in top_reply:
                                top_reply_list.append(__i.get('content').get('message'))
                        for reply in pinglun_list:
                            if reply not in top_reply_list:
                                reply_content.append(reply.get('content').get('message'))
                        print(reply_content)
                        print(premsg)
                        if reply_content != []:
                            ret_msg = huifuneirongpanduan(reply_content, premsg)
                        else:
                            ret_msg = ''
                        if ret_msg != '':
                            ret_msg += random.choice(self.copy_suffix)
                            return ret_msg
                        else:
                            try:
                                pnlist = list(range(int(qianpai_xishu * pinglun_count), int(1 * pinglun_count)))
                            except:
                                print(pinglun_count)
                                pnlist = []
                            if not pnlist:
                                print('动态下评论过少，评论获取失败')
                                break
                            pn = random.choice(pnlist)
                    else:
                        print(f'动态：https://t.bilibili.com/{dynamic_id} 评论为空')

        print('此次抄评论关闭，启用脚本内置回复')
        mobj_6 = re.match('.*七夕.*', content, re.DOTALL)
        mobj_5 = re.match('.*许愿格式：有趣的愿望+愿望实现城市！.*', content, re.DOTALL)
        mobj_4 = re.match('.*带话题 #.*#.*', content, re.DOTALL)
        mobj_2 = re.match('.*带话题.{0,10}#.*#.*', content, re.DOTALL)
        mobj_1 = re.match('.*评论#.*#.*', content, re.DOTALL)
        mobj = re.match('.*在评论区打出#.*#.*', content, re.DOTALL)
        mobj1 = re.match('.*评论区刷#.*#.*', content, re.DOTALL)
        mobj4 = re.match('.*带#.*#.*', content, re.DOTALL)
        mobj5 = re.match('.*为.*加油.*', content, re.DOTALL)
        mobj6 = re.match('.*随机数方式抽取到.*', content, re.DOTALL)
        mobj7 = re.match('.*评论话题#.*#.*', content, re.DOTALL)
        mobj8 = re.match('.*奥迪双钻AULDEY.*', content, re.DOTALL)
        mobj9 = re.match('.*说说.*计划.*', content, re.DOTALL)
        mobj10 = re.match('.*预告.*', content, re.DOTALL)
        mobj11 = re.match('.*长按复制这条信息.*', content, re.DOTALL)
        mobj12 = re.match('.*把.*打在评论区.*', content, re.DOTALL)
        mobj13 = re.match('.*华为.*系列.*', content, re.DOTALL)
        mobj14 = re.match('.*生日祝福.*', content, re.DOTALL)
        if mobj_6 != None:
            msg = '浪漫七夕'
            return msg
        if mobj_5 != None:
            msg = '中个大奖'
            return msg
        if mobj_4 != None:
            msg = re.findall(r'带话题 #(.*?)#', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj_2 != None:
            msg = re.findall(r'带话题  #(.*?)#', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj_1 != None:
            msg = re.findall(r'评论#(.*?)#，', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj != None:
            msg = re.findall(r'在评论区打出#(.*?)#，', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj1 != None:
            msg = re.findall(r'评论区刷#(.*?)#，', content, re.DOTALL)
            msg1 = msg[0]
            return msg1
        if mobj4 != None:
            msg = re.findall(r'带#(.*?)#', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj7 != None:
            msg = re.findall(r'评论话题#(.*?)#', content, re.DOTALL)
            msg1 = '#' + str(msg[0]) + '#'
            return msg1
        if mobj14 != None:
            msg = '生日快乐！'
            return msg
        if mobj5 != None:
            msg = '加油！'
            return msg
        if mobj6 != None:
            msg = '恭喜'
            return msg
        if mobj8 != None:
            msglist = ['奥迪双钻，我的伙伴[doge]', '老板大气']
            return random.choice(msglist)
        if mobj9 != None:
            msg = '宅家'
            return msg
        if mobj10 != None:
            msg = '期待[星星眼]'
            return msg
        if mobj11 != None:
            msglist1 = ['买了买了', '太划算啦', '确实挺便宜', '有点心动']
            msg = random.choice(msglist1)
            return msg
        if mobj12 != None:
            msg = re.findall(r'把(.*)打在评论区', content, re.DOTALL)
            msg1 = str(msg[0])
            return msg1
        if mobj13 != None:
            msg = '华为加油！'
            return msg
        print('使用常用回复')
        msg = random.choice(self.replycontent)
        return msg

    def dynamic_card_resolution(self, dynamic_item):
        """
            新版本动态卡片解析
        :param dynamic_item:
        :return:
        """
        try:
            comment_type = dynamic_item.get('basic').get('comment_type')
            dynamic_type = None
            if str(comment_type) == '17':
                dynamic_type = '4'
            elif str(comment_type) == '1':
                dynamic_type = '8'
            elif str(comment_type) == '11':
                dynamic_type = '2'
            elif str(comment_type) == '12':
                dynamic_type = '64'
            dynamic_id = dynamic_item.get('id_str')
            dynamic_rid = dynamic_item.get('basic').get('comment_id_str')
            relation = dynamic_item.get('modules').get('module_author').get('following')
            author_uid = dynamic_item.get('modules').get('module_author').get('mid')
            author_name = dynamic_item.get('modules').get('module_author').get('name')
            pub_time = dynamic_item.get('modules').get('module_author').get('pub_time')
            pub_ts = dynamic_item.get('modules').get('module_author').get('pub_ts')
            official_verify_type = dynamic_item.get('modules').get('module_author').get(
                'official_verify').get('type')
            comment_count = dynamic_item.get('modules').get('module_stat').get('comment').get('count')
            forward_count = dynamic_item.get('modules').get('module_stat').get('forward').get('count')
            like_count = dynamic_item.get('modules').get('module_stat').get('like').get('count')
            dynamic_content1 = ''
            if dynamic_item.get('modules').get('module_dynamic').get('desc'):
                dynamic_content1 = dynamic_item.get('modules').get('module_dynamic').get('desc').get('text')
            dynamic_content2 = ''
            dynamic_content3 = ''
            if dynamic_item.get('modules').get('module_dynamic').get('major'):
                if dynamic_item.get('modules').get('module_dynamic').get('major').get('archive'):
                    dynamic_content2 = dynamic_item.get('modules').get('module_dynamic').get('major').get(
                        'archive').get('desc')
                if dynamic_item.get('modules').get('module_dynamic').get('major').get('article'):
                    dynamic_content3 = dynamic_item.get('modules').get('module_dynamic').get('major').get(
                        'article').get('desc')
            dynamic_content = dynamic_content1 + dynamic_content2 + dynamic_content3
            if relation:
                relation = 1
            else:
                relation = 0
            is_liked = dynamic_item.get('modules').get('module_stat').get('like').get('status')
            if is_liked:
                is_liked = 1
            else:
                is_liked = 0
            if relation != 1:
                print('未关注的response')
                print(f'https://space.bilibili.com/{author_uid}')
        except Exception as e:
            traceback.print_exc()
            # time.sleep(eval(input('输入等待时间')))
            return None

        top_dynamic = None
        try:
            module_tag = dynamic_item.get('modules').get('module_tag')
            if module_tag:
                module_tag_text = module_tag.get('text')
                if module_tag_text == "置顶":
                    top_dynamic = True
                else:
                    print(module_tag_text)
                    print('未知动态tag')
            else:
                top_dynamic = False
        except:
            top_dynamic = None
        orig_name = None
        orig_mid = None
        orig_official_verify = None
        orig_pub_ts = None
        orig_comment_count = None
        orig_forward_count = None
        orig_dynamic_content = None
        orig_like_count = None
        orig_relation = None
        orig_is_liked = None
        orig_dynamic_id = None
        try:
            if dynamic_item.get('orig'):
                orig_dynamic_id = dynamic_item.get('id_str')
                orig_mid = dynamic_item.get('orig').get('modules').get('module_author').get('mid')
                orig_name = dynamic_item.get('orig').get('modules').get('module_author').get('name')
                orig_pub_ts = dynamic_item.get('orig').get('modules').get('module_author').get('pub_ts')
                orig_official_verify = dynamic_item.get('orig').get('modules').get('module_author').get(
                    'official_verify').get('type')
                # orig_comment_count = dynamic_item.get('orig').get('modules').get('module_stat').get('comment').get(
                #     'count')
                # orig_forward_count = dynamic_item.get('orig').get('modules').get('module_stat').get('forward').get(
                #     'count')
                # orig_like_count = dynamic_item.get('orig').get('modules').get('module_stat').get('like').get('count')
                # 原动态暂时无法获取转评赞数据
                orig_dynamic_content1 = ''
                if dynamic_item.get('orig').get('modules').get('module_dynamic').get('desc'):
                    orig_dynamic_content1 = dynamic_item.get('orig').get('modules').get(
                        'module_dynamic').get(
                        'desc').get('text')
                orig_dynamic_content2 = ''
                if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major'):
                    if dynamic_item.get('orig').get('modules').get('module_dynamic').get('major').get(
                            'archive'):
                        orig_dynamic_content2 = dynamic_item.get('orig').get('modules').get(
                            'module_dynamic').get('major').get('archive').get('desc')
                orig_dynamic_content = orig_dynamic_content1 + orig_dynamic_content2
                orig_relation = dynamic_item.get('orig').get('modules').get('module_author').get(
                    'following')
                if orig_relation:
                    orig_relation = 1
                else:
                    orig_relation = 0
                # orig_is_liked = dynamic_data.get('item').get('orig').get('modules').get('module_stat').get('like').get(
                #     'status')
                # if orig_is_liked:
                #     orig_is_liked = 1
                # else:
                #     orig_is_liked = 0
            else:
                print('非转发动态，无原动态')
        except:
            print(dynamic_item)
            traceback.print_exc()
        structure = {
            'dynamic_id': dynamic_id,
            'type': dynamic_type,
            'rid': dynamic_rid,
            'relation': relation,
            'is_liked': is_liked,
            'author_uid': author_uid,
            'author_name': author_name,
            'comment_count': comment_count,
            'forward_count': forward_count,  # 转发数
            'like_count': like_count,
            'dynamic_content': dynamic_content,
            'pub_time': pub_time,
            'pub_ts': pub_ts,
            'official_verify_type': official_verify_type,

            'top_dynamic': top_dynamic,

            'orig_dynamic_id': orig_dynamic_id,
            'orig_mid': orig_mid,
            'orig_name': orig_name,
            'orig_pub_ts': orig_pub_ts,
            'orig_official_verify': orig_official_verify,
            'orig_comment_count': orig_comment_count,
            'orig_forward_count': orig_forward_count,
            'orig_like_count': orig_like_count,
            'orig_dynamic_content': orig_dynamic_content,
            'orig_relation': orig_relation,
        }
        return structure

    def feed_space_without_cookie(self, host_mid, offset=''):
        """
            新版本隐身模式查看某人空间动态
            暂时无法获取原动态的转评赞数据
        :param offset:
        :param host_mid:
        """
        url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?offset={offset}&host_mid={host_mid}&timezone_offset=-480'
        req = self.s.get(url=url)
        has_more = None
        tempitems = []
        if req.json().get('code') == 0:
            has_more = req.json().get('data').get('has_more')
            offset = req.json().get('data').get('offset')
            for i in req.json().get('data').get('items'):
                tempitems.append(self.dynamic_card_resolution(i))
        if req.json().get('code') == -412:
            print('412风控')
            time.sleep(10 * 60)
            return self.feed_space_without_cookie(host_mid, offset)
        if req.json().get('code') == 4101128:
            print(req.json().get('message'))
            time.sleep(10 * 60)
            # time.sleep(eval(input('输入等待时间')))
            return None
        if not tempitems:
            print(req.json())
        return {'offset': offset, 'data': tempitems, 'has_more': has_more}

    def dynamic_lottery_notice(self, dynamic_id):
        url = f'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?dynamic_id={dynamic_id}'
        req = self.s.get(url=url)
        try:
            if req.json().get('code') == 0:
                return req.json()
            else:
                print(req.text)
                print(url)
                while 1:
                    try:
                        time.sleep(int(input('输入等待时间')))
                    except:
                        continue
                return None
        except:
            print(req.text)
            while 1:
                try:
                    time.sleep(int(input('输入等待时间')))
                except:
                    continue
            return False

    def js_repost_non_content_dyn(self, _dynamic_req, dynamic_id, uid, cookie, ua, csrf, card_stype=''):
        """

        :param _dynamic_req:
        :param dynamic_id:
        :param uid:自己的uid
        :param cookie:
        :param ua:
        :param csrf:
        """
        if card_stype != '' and card_stype is not None:
            res = asyncio.run(
                log_reporter.handleSelfDefReport(eventname='dynamic_forward_click',
                                                 url=f'https://t.bilibili.com/{dynamic_id}',
                                                 cookie=cookie
                                                 ,
                                                 ua=ua
                                                 , ops={
                        "dynamic_id": dynamic_id, "card_stype": card_stype
                    }))
            for i in res:
                asyncio.run(self.log_report(i, 'https://t.bilibili.com', f'https://t.bilibili.com/{dynamic_id}', cookie,
                                            ua))

        js = '''
        function U(t, e) {
                        (null == e || e > t.length) && (e = t.length);
                        for (var n = 0, r = new Array(e); n < e; n++)
                            r[n] = t[n];
                        return r
                    }
        function Te(t) {
                        return function(t) {
                            if (Array.isArray(t))
                                return U(t)
                        }(t) || function(t) {
                            if ("undefined" != typeof Symbol && Symbol.iterator in Object(t))
                                return Array.from(t)
                        }(t) || W(t) || function() {
                            throw new TypeError("Invalid attempt to spread non-iterable instance.In order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
                        }()
                    }
        function h(t, e, n) {
                        return e in t ? Object.defineProperty(t, e, {
                            value: n,
                            enumerable: !0,
                            configurable: !0,
                            writable: !0
                        }) : t[e] = n,
                        t
                    }
        function m(t, e) {
                        var n = Object.keys(t);
                        if (Object.getOwnPropertySymbols) {
                            var r = Object.getOwnPropertySymbols(t);
                            e && (r = r.filter((function(e) {
                                return Object.getOwnPropertyDescriptor(t, e).enumerable
                            }
                            ))),
                            n.push.apply(n, r)
                        }
                        return n
                    }
        function _(t) {
                        for (var e = 1; e < arguments.length; e++) {
                            var n = null != arguments[e] ? arguments[e] : {};
                            e % 2 ? m(Object(n), !0).forEach((function(e) {
                                h(t, e, n[e])
                            }
                            )) : Object.getOwnPropertyDescriptors ? Object.defineProperties(t, Object.getOwnPropertyDescriptors(n)) : m(Object(n)).forEach((function(e) {
                                Object.defineProperty(t, e, Object.getOwnPropertyDescriptor(n, e))
                            }
                            ))
                        }
                        return t
                    }
    
        var vd = function(t, e) {
                         return [Yr("//"), jr({
                             type: "at",
                             data: {
                                 rid: t.uid,
                                 text: "@".concat(t.name)
                            }
                             }), Yr(":")].concat(Te(e.map(Mu)))
                     }
        var Or = function(t, e) {
                        return t && e ? "".concat(t, ":").concat(e) : null
                    }
        var Yr = function(t) {
                         return {
                            type: "text",
                            text: t,
                            data: null
                         }
                     }
        var jr = function(t) {
                         var e = t.type
                           , n = t.data;
                         return {
                             id: t.unique && Or(e, n.rid) || null,
                             type: "highlight",
                             text: n.text,
                             data: _(_({}, n), {}, {
                                 type: e
                             })
                         }
                     }
    
        var Mu = function(t) {
                        switch (t.type) {
                        case "RICH_TEXT_NODE_TYPE_AT":
                            return jr({
                                type: "at",
                                data: {
                                    text: t.text,
                                    rid: t.rid
                                }
                            });
                        case "RICH_TEXT_NODE_TYPE_LOTTERY":
                            return jr({
                                type: "lottery",
                                data: {
                                    text: t.text,
                                    rid: t.rid
                                },
                                unique: !0
                            });
                        case "RICH_TEXT_NODE_TYPE_VOTE":
                            return jr({
                                type: "vote",
                                data: {
                                    text: t.text,
                                    rid: t.rid
                                },
                                unique: !0
                            });
                        case "RICH_TEXT_NODE_TYPE_EMOJI":
                            return Ir(t.text, {
                                type: t.emoji.type,
                                size: t.emoji.size,
                                text: t.emoji.text,
                                id: t.emoji.id,
                                src: t.emoji.icon_url
                            });
                        case "RICH_TEXT_NODE_TYPE_BV":
                            return jr({
                                type: "bv",
                                data: {
                                    text: t.text,
                                    rid: t.rid
                                },
                                unique: !0
                            });
                        case "RICH_TEXT_NODE_TYPE_TOPIC":
                        case "RICH_TEXT_NODE_TYPE_WEB":
                        case "RICH_TEXT_NODE_TYPE_TAOBAO":
                        case "RICH_TEXT_NODE_TYPE_NONE":
                        case "RICH_TEXT_NODE_TYPE_TEXT":
                        default:
                            return Yr(t.text)
                        }
                    }
    
        var wr = null
        var Mr = {}
        var Ir = function(t, e) {
                    return {
                        type: "emoji",
                        text: t,
                        data: t
                    }
                }
    
    
    
    
        var defaultForwardContentNodes= function(dynamic_detail) {
                                var t;
                                if (!dynamic_detail.orig_dynamic_id || dynamic_detail.isPGCAuthor)
                                    return [];
                                var e = null === (t = dynamic_detail.desc) || void 0 === t ? void 0 : t.rich_text_nodes;
                                return e ? vd({
                                    uid: dynamic_detail.author_uid,
                                    name: dynamic_detail.author_name
                                }, e) : []
                            }
    
        var si = function(t, e) {
                        switch (e.type) {
                        case "text":
                            t.push({
                                raw_text: e.text,
                                type: 1,
                                biz_id: ""
                            });
                            break;
                        case "highlight":
                            switch (e.data.type) {
                            case "at":
                                t.push({
                                    raw_text: e.text,
                                    type: 2,
                                    biz_id: String(e.data.rid)
                                });
                                break;
                            case "lottery":
                                t.push({
                                    raw_text: e.text,
                                    type: 3,
                                    biz_id: String(e.data.rid)
                                });
                                break;
                            case "vote":
                                t.push({
                                    raw_text: e.text,
                                    type: 4,
                                    biz_id: String(e.data.rid)
                                });
                                break;
                            case "bv":
                                t.push({
                                    raw_text: e.data.rid,
                                    type: 7,
                                    biz_id: e.data.rid
                                })
                            }
                            break;
                        case "emoji":
                            t.push({
                                raw_text: e.text,
                                type: 9,
                                biz_id: ""
                            })
                        }
                        return t
                    }
                      ci = function(t, e) {
                        switch (e) {
                        case 0:
                            oi(t, "close_comment", 1);
                            break;
                        case 2:
                            oi(t, "up_choose_comment", 1)
                        }
                    }
            var ai = function(t) {
                        var e = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : void 0;
                        return "object" !== C(t) ? t || e : Er(t) ? t.length ? t : e : t || e
                    }
            function C(t) {
                        return (C = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(t) {
                            return typeof t
                        }
                        : function(t) {
                            return t && "function" == typeof Symbol && t.constructor === Symbol && t !== Symbol.prototype ? "symbol" : typeof t
                        }
                        )(t)
                    }
    
            var ui = function(t) {
                        var e, n, r;
                        if (!t.scene && (null !== (e = t.content) && void 0 !== e && null !== (n = e.contents) && void 0 !== n && n.length && (t.scene = 1),
                        null !== (r = t.pics) && void 0 !== r && r.length && (t.scene = 2),
                        t.video && (t.scene = 3),
                        t.repost_src && (t.repost_src.dynId ? t.scene = 4 : t.repost_src.revsId && (t.scene = 5)),
                        t.sketch && (t.scene = 6),
                        !t.scene))
                            throw new Error("dyn create params scene empty")
                    }
    
            function gen_contents(e){
            a={content: {
                       contents: null == e || null === (r = e.nodes) || void 0 === r ? void 0 : r.reduce(si, [])
                                        }}
            return a
            }
    
    
    
    
    
    Sr = function(t) {
        return (null == t ? void 0 : t.length) > 0 ? t[t.length - 1] : null
    }
    
    le = function(t) {
        return JSON.parse(JSON.stringify(t))
    }
    
    de = function(t) {
        var e = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : "JSON";
        switch (e) {
        case "JSON":
        default:
            return le(t)
        }
    }
    
    Rr = function(t) {//主要的刷新nodes的方式
        for (var e = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : t.length, n = [], r = 0, i = 0; i < t.length; i++) {
            var a = t[i]
              , o = Sr(n);
            "text" === (null == o ? void 0 : o.type) && "text" === a.type ? (o.text += a.text,
            i <= e && r++) : n.push(a)
        }
        return [n, r]
    }
    var refresh_nodes = function(t) {
        if (i = t.value,
            null == (a = t.nodes) || !a.length) {
                return []
            }
            return Rr(de(a))[0]
    
                        }
        '''

        def submit(_data, _dynamic_id, _csrf, _cookie, _ua):
            url = f'https://api.bilibili.com/x/dynamic/feed/create/submit_check?csrf={_csrf}'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': _cookie,
                'origin': 'https://t.bilibili.com',
                'referer': f'https://t.bilibili.com/{_dynamic_id}',
                'user-agent': _ua
            }
            req = self.s.post(url=url, data=json.dumps(eval(str(_data))), headers=headers)
            if req.json().get('code') == 0:
                return True
            else:
                print(req.text)
                return False

        def feed_crate_dyn(_data, _dynamic_id, _csrf, _cookie, _ua):
            url = f'https://api.bilibili.com/x/dynamic/feed/create/dyn?csrf={_csrf}'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': _cookie,
                'origin': 'https://t.bilibili.com',
                'referer': f'https://t.bilibili.com/{_dynamic_id}',
                'user-agent': _ua
            }
            req = self.s.post(url=url, headers=headers, data=json.dumps(eval(str(_data))))
            if req.json().get('code') == 0:
                print(f'转发动态结果：{req.json()}')
                return req.json().get('data')
            else:
                print('无内容转发失败')
                print(req.text)
                print(eval(str(_data)))
                print(f'转发动态结果：{req.json()}')
                self.zhuanfashibai.append(f'https://t.bilibili.com/{dynamic_id}\t{req.json()}\tjsfail')

                return False

        def get_upload_id(__uid):
            return f'{__uid}_{int(time.time())}_{math.floor(1e3 * random.random())}'

        content = js2py.EvalJs()
        content.execute(js)
        res = content.defaultForwardContentNodes(_dynamic_req)
        nodes = {'nodes': res}
        nodes = {'nodes': content.refresh_nodes(nodes)}
        contents = content.gen_contents(nodes)  # submit的参数
        submit(contents, dynamic_id, csrf, cookie, ua)
        forward_args = {
            "dyn_req": {
                'content': eval(str(contents)).get('content'),
                "meta": {
                    "app_meta": {
                        'from': "create.dynamic.web",
                        'mobi_app': 'web'
                    },
                },
                "scene": 4,
                "uploadId": get_upload_id(uid)
            },
            "web_repost_src": {
                "dyn_id_str": str(dynamic_id)
            }
        }
        res = feed_crate_dyn(forward_args, dynamic_id, csrf, cookie, ua)
        if res:
            return res
        else:
            return False

    def get_topcomment(self, dynamicid, rid, pn, _type, mid):
        iner_replies = ''
        pinglunreq = self.get_pinglunreq(dynamicid, rid, pn, _type, 3)
        try:
            pinglun_dict = json.loads(pinglunreq)
            pingluncode = pinglun_dict.get('code')
            if pingluncode != 0:
                print('获取置顶评论失败')
                message = pinglun_dict.get('message')
                print(pinglun_dict)

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
            topmsg = ''
            if topreplies != None:
                for tprps in topreplies:
                    topmsg += tprps.get('content').get('message')
                    if tprps.get('replies'):
                        for tprpsrps in tprps.get('replies'):
                            if tprpsrps.get('mid') == mid:
                                iner_replies += tprpsrps.get('content').get('message')
                topmsg += iner_replies
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
            print(self.timeshift(int(time.time())))
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

    def get_pinglunreq_proxy(self, dynamic_id, rid, pn, _type, *mode) -> dict:
        """
        3是热评，2是最新，大概
        :param dynamic_id:
        :param rid:
        :param pn:
        :param _type:
        :param mode:
        :return:
        """
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
        if len(str(rid)) == len(str(dynamic_id)):
            oid = dynamic_id
        else:
            oid = rid
        pinglunheader = {
            'user-agent': 'Mozilla/5.0'}
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=' + str(mode) + '&plat=1&_=' + str(int(time.time()))
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
            pinglunreq = async_to_sync(
                self.requests_with_proxy.request_with_proxy
            )(method="GET", url=pinglunurl, data=pinglundata,headers=pinglunheader)
        except:
            traceback.print_exc()
            print('获取评论失败')
            print(self.timeshift(int(time.time())))
            # while 1:
            #     try:
            #         time.sleep(eval(input('输入等待时间')))
            #         break
            #     except:
            #         continue
            time.sleep(3)
            pinglunreq = self.get_pinglunreq(dynamic_id, rid, pn, _type)
            return pinglunreq
        return pinglunreq

    def get_topcomment_proxy(self, dynamicid, rid, pn, _type, mid) -> str:
        iner_replies = ''
        pinglunreq = self.get_pinglunreq_proxy(dynamicid, rid, pn, _type, 3)
        try:
            pinglun_dict = pinglunreq
            pingluncode = pinglun_dict.get('code')
            if pingluncode != 0:
                print('获取置顶评论失败')
                message = pinglun_dict.get('message')
                print(pinglun_dict)

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
            topmsg = ''
            if topreplies != None:
                for tprps in topreplies:
                    topmsg += tprps.get('content').get('message')
                    if tprps.get('replies'):
                        for tprpsrps in tprps.get('replies'):
                            if tprpsrps.get('mid') == mid:
                                iner_replies += tprpsrps.get('content').get('message')
                topmsg += iner_replies
                print('置顶评论：' + topmsg)
            else:
                print('无置顶评论')
                topmsg = 'null' + iner_replies
        except Exception as e:
            print(e)
            print('获取置顶评论失败')
            pinglun_dict = pinglunreq
            data = pinglun_dict.get('data')
            print(pinglun_dict)
            print(data)
            topmsg = 'null'
            print(self.timeshift(int(time.time())))
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

    def get_private_cookie_t_bilibili(self) -> str:
        '''
        获取未登录状态的cookie
        :return:
        '''
        r1 = httpx.get(
            "https://t.bilibili.com/",
            headers={
                "Host": "space.bilibili.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            },
        )
        payload = {
            "payload": "{\"3064\":1,\"5062\":\"1688485907676\",\"03bf\":\"https%3A%2F%2Ft.bilibili.com%2F\",\"39c8\":\"444.41.fp.risk\",\"34f1\":\"\",\"d402\":\"\",\"654a\":\"\",\"6e7c\":\"995x1321\",\"3c43\":{\"2673\":0,\"5766\":24,\"6527\":0,\"7003\":1,\"807e\":1,\"b8ce\":\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67\",\"641c\":0,\"07a4\":\"zh-CN\",\"1c57\":8,\"0bd0\":12,\"748e\":[2560,1440],\"d61f\":[2560,1392],\"fc9d\":-480,\"6aa9\":\"Asia/Shanghai\",\"75b8\":1,\"3b21\":1,\"8a1c\":1,\"d52f\":\"not available\",\"adca\":\"Win32\",\"80c9\":[[\"PDF Viewer\",\"Portable Document Format\",[[\"application/pdf\",\"pdf\"],[\"text/pdf\",\"pdf\"]]],[\"Chrome PDF Viewer\",\"Portable Document Format\",[[\"application/pdf\",\"pdf\"],[\"text/pdf\",\"pdf\"]]],[\"Chromium PDF Viewer\",\"Portable Document Format\",[[\"application/pdf\",\"pdf\"],[\"text/pdf\",\"pdf\"]]],[\"Microsoft Edge PDF Viewer\",\"Portable Document Format\",[[\"application/pdf\",\"pdf\"],[\"text/pdf\",\"pdf\"]]],[\"WebKit built-in PDF\",\"Portable Document Format\",[[\"application/pdf\",\"pdf\"],[\"text/pdf\",\"pdf\"]]]],\"13ab\":\"NgoAAAAASUVORK5CYII=\",\"bfe9\":\"AFzCgAsMxYTaIooF+B/wGUsPWmkr+6+QAAAABJRU5ErkJggg==\",\"a3c1\":[\"extensions:ANGLE_instanced_arrays;EXT_blend_minmax;EXT_color_buffer_half_float;EXT_disjoint_timer_query;EXT_float_blend;EXT_frag_depth;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;EXT_sRGB;KHR_parallel_shader_compile;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBGL_multi_draw\",\"webgl aliased line width range:[1, 1]\",\"webgl aliased point size range:[1, 1024]\",\"webgl alpha bits:8\",\"webgl antialiasing:yes\",\"webgl blue bits:8\",\"webgl depth bits:24\",\"webgl green bits:8\",\"webgl max anisotropy:16\",\"webgl max combined texture image units:32\",\"webgl max cube map texture size:16384\",\"webgl max fragment uniform vectors:1024\",\"webgl max render buffer size:16384\",\"webgl max texture image units:16\",\"webgl max texture size:16384\",\"webgl max varying vectors:30\",\"webgl max vertex attribs:16\",\"webgl max vertex texture image units:16\",\"webgl max vertex uniform vectors:4095\",\"webgl max viewport dims:[32767, 32767]\",\"webgl red bits:8\",\"webgl renderer:WebKit WebGL\",\"webgl shading language version:WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)\",\"webgl stencil bits:0\",\"webgl vendor:WebKit\",\"webgl version:WebGL 1.0 (OpenGL ES 2.0 Chromium)\",\"webgl unmasked vendor:Google Inc. (NVIDIA)\",\"webgl unmasked renderer:ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)\",\"webgl vertex shader high float precision:23\",\"webgl vertex shader high float precision rangeMin:127\",\"webgl vertex shader high float precision rangeMax:127\",\"webgl vertex shader medium float precision:23\",\"webgl vertex shader medium float precision rangeMin:127\",\"webgl vertex shader medium float precision rangeMax:127\",\"webgl vertex shader low float precision:23\",\"webgl vertex shader low float precision rangeMin:127\",\"webgl vertex shader low float precision rangeMax:127\",\"webgl fragment shader high float precision:23\",\"webgl fragment shader high float precision rangeMin:127\",\"webgl fragment shader high float precision rangeMax:127\",\"webgl fragment shader medium float precision:23\",\"webgl fragment shader medium float precision rangeMin:127\",\"webgl fragment shader medium float precision rangeMax:127\",\"webgl fragment shader low float precision:23\",\"webgl fragment shader low float precision rangeMin:127\",\"webgl fragment shader low float precision rangeMax:127\",\"webgl vertex shader high int precision:0\",\"webgl vertex shader high int precision rangeMin:31\",\"webgl vertex shader high int precision rangeMax:30\",\"webgl vertex shader medium int precision:0\",\"webgl vertex shader medium int precision rangeMin:31\",\"webgl vertex shader medium int precision rangeMax:30\",\"webgl vertex shader low int precision:0\",\"webgl vertex shader low int precision rangeMin:31\",\"webgl vertex shader low int precision rangeMax:30\",\"webgl fragment shader high int precision:0\",\"webgl fragment shader high int precision rangeMin:31\",\"webgl fragment shader high int precision rangeMax:30\",\"webgl fragment shader medium int precision:0\",\"webgl fragment shader medium int precision rangeMin:31\",\"webgl fragment shader medium int precision rangeMax:30\",\"webgl fragment shader low int precision:0\",\"webgl fragment shader low int precision rangeMin:31\",\"webgl fragment shader low int precision rangeMax:30\"],\"6bc5\":\"Google Inc. (NVIDIA)~ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)\",\"ed31\":0,\"72bd\":0,\"097b\":0,\"52cd\":[0,0,0],\"a658\":[\"Arial\",\"Arial Black\",\"Arial Narrow\",\"Book Antiqua\",\"Bookman Old Style\",\"Calibri\",\"Cambria\",\"Cambria Math\",\"Century\",\"Century Gothic\",\"Century Schoolbook\",\"Comic Sans MS\",\"Consolas\",\"Courier\",\"Courier New\",\"Georgia\",\"Helvetica\",\"Impact\",\"Lucida Bright\",\"Lucida Calligraphy\",\"Lucida Console\",\"Lucida Fax\",\"Lucida Handwriting\",\"Lucida Sans\",\"Lucida Sans Typewriter\",\"Lucida Sans Unicode\",\"Microsoft Sans Serif\",\"Monotype Corsiva\",\"MS Gothic\",\"MS PGothic\",\"MS Reference Sans Serif\",\"MS Sans Serif\",\"MS Serif\",\"Palatino Linotype\",\"Segoe Print\",\"Segoe Script\",\"Segoe UI\",\"Segoe UI Light\",\"Segoe UI Semibold\",\"Segoe UI Symbol\",\"Tahoma\",\"Times\",\"Times New Roman\",\"Trebuchet MS\",\"Verdana\",\"Wingdings\",\"Wingdings 2\",\"Wingdings 3\"],\"d02f\":\"124.04347527516074\"},\"54ef\":\"{\\\"in_new_ab\\\":true,\\\"ab_version\\\":{},\\\"ab_split_num\\\":{},\\\"ab_type\\\":1}\",\"8b94\":\"\",\"df35\":\"634B21D10-AA27-911D-848A-2F142F351EED07055infoc\",\"07a4\":\"zh-CN\",\"5f45\":null,\"db46\":0}"}
        url = "https://api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi"
        headers = {
            "authority": "api.bilibili.com",
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "origin": "https://space.bilibili.com",
            "referer": "https://space.bilibili.com/1133258171/dynamic",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67",
        }

        response = httpx.post(url, headers=headers, data=json.dumps(payload), cookies=r1.cookies)
        print(response.json())
        print(response.cookies)
        print(r1.cookies)
        print(response.status_code)
        fake_cookie_str = ''
        for k, v in response.cookies.items():
            fake_cookie_str += f"{k}={v}; "
        return fake_cookie_str

    def rid_2_dynamic_id(self, rid):
        url = 'https://api.vc.bilibili.com/link_draw/v2/doc/dynamic_id'
        params = {
            'doc_id': rid
        }
        headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0",
        }
        req = self.s.get(url, params=params, headers=headers)
        return req.json()

if __name__=='__main__':
    __test =methods()
    __res=__test.daily_choujiangxinxipanduan("""恭喜你在开学前刷到这条动态[给心心]!
关注@次元数码说 粉丝破9100或者转发破1000
就有机会随机获得一款头戴式耳机陪你开学![鼓掌]
#唠嗑##闲聊##耳机##头戴式耳##QCY##iKF##漫步者##倍思##开学##开学好礼#""")
    print(__res)