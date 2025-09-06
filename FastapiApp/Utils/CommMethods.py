# -*- coding:utf- 8 -*-
import random
import re
import time
from pylangtools.langconv import Converter

import numpy
import requests
from Utils.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
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
        self.requests_with_proxy = request_with_proxy_internal
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
            '老板超级大气喵[永雏塔菲_嘻嘻喵][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_星星眼][永雏塔菲_哈哈哈]',
            '老板超级大气喵[永雏塔菲_好热][永雏塔菲_嘻嘻喵]非常感谢老板喵[永雏塔菲_哈哈哈][永雏塔菲_星星眼]',
            '老板超级大气喵[永雏塔菲_令人兴奋][永雏塔菲_好热]非常感谢老板喵[永雏塔菲_亲嘴][永雏塔菲_嘻嘻喵]',
        ]
        self.non_official_chp = ['好耶',
                                 '许愿',
                                 '万一呢',
                                 '冲冲冲',
                                 '冲鸭',
                                 '好运来',
                                 '拉低中奖率',
                                 ]
        self.shangjiayingguang = [  # '水点评论，点点赞，合作那边那好交代[doge]',
            '还不错，买了[doge]',
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
        self.s = requests.session()

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
        tcontent = Converter(r'zh-hans').convert(tcontent)
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


if __name__ == '__main__':
    __test = methods()
    __res = __test.daily_choujiangxinxipanduan("""恭喜你在开学前刷到这条动态[给心心]!
关注@次元数码说 粉丝破9100或者转发破1000
就有机会随机获得一款头戴式耳机陪你开学![鼓掌]
#唠嗑##闲聊##耳机##头戴式耳##QCY##iKF##漫步者##倍思##开学##开学好礼#""")
    print(__res)
