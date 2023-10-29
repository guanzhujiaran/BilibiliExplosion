# -*- coding:utf- 8 -*-
import datetime
import json
import os
import random
import re
import sys
import time
import traceback
from atexit import register

from pylangtools.langconv import Converter
import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods

username = ''
if not os.path.exists('./log'):
    os.makedirs('./log')


def login_check(cookie, ua):
    global username
    headers = {
        'User-Agent': ua,
        'cookie': cookie
    }
    url = 'https://api.bilibili.com/x/web-interface/nav'
    res = requests.get(url=url, headers=headers).json()
    if res['data']['isLogin'] == True:
        username = res['data']['uname']
        print('登录成功,当前账号用户名为%s' % username)
        mymethod.username = username
        return 1
    else:
        print('登陆失败,请重新登录')
        sys.exit('登陆失败,请重新登录')


mymethod = Bilibili_methods.all_methods.methods()
mymethod.caihongpi_chance = 1  # 使用彩虹屁的概率，数字越大，彩虹屁频率越高
mymethod.chance_shangjiayingguang = 1  # 随机挑线自定义商家广告回复词的概率
mymethod.chance_copy_comment = 1  # 抄评论的概率
mymethod.non_official_chp_chance = 0.8
mymethod.changyongemo.extend(['永雏塔菲_对呀对呀', '永雏塔菲_令人兴奋', '永雏塔菲_嘻嘻喵'])  # 常用的表情包
mymethod.replycontent = ['[永雏塔菲_对呀对呀][永雏塔菲_对呀对呀]', '[永雏塔菲_对呀对呀]', '好耶[永雏塔菲_令人兴奋]',
                         '来了[永雏塔菲_令人兴奋]', '冲鸭[永雏塔菲_令人兴奋]',
                         '来了来了[永雏塔菲_令人兴奋]', '[永雏塔菲_亲嘴]', '冲[永雏塔菲_星星眼]',
                         '[永雏塔菲_星星眼]', '[永雏塔菲_星星眼][永雏塔菲_星星眼]', '[永雏塔菲_闪亮登场]',
                         '[永雏塔菲_闪亮登场][永雏塔菲_闪亮登场]',
                         '万一呢[永雏塔菲_嘤嘤嘤]']
mymethod.hasemo.extend(
    ['永雏塔菲_累', '永雏塔菲_令人兴奋', '永雏塔菲_亲嘴', '永雏塔菲_摸头', '永雏塔菲_闪亮登场', '永雏塔菲_生日快乐',
     '永雏塔菲_太好吃了', '永雏塔菲_我帅吗', '永雏塔菲_嘻嘻喵',
     '永雏塔菲_星星眼', '永雏塔菲_震惊', '永雏塔菲_晕了', '永雏塔菲_有鬼', '永雏塔菲_嘤嘤嘤', '永雏塔菲_疑惑',
     '永雏塔菲_开派对咯', '永雏塔菲_呼呼喵', '永雏塔菲_好热', '永雏塔菲_哈哈哈',
     '永雏塔菲_尴尬', '永雏塔菲_NO喵!', '永雏塔菲_不理你了', '永雏塔菲_嘲笑', '永雏塔菲_喵喵拳', '永雏塔菲_对呀对呀'])
mymethod.hasemo.extend(
    ['未来有你_5周年', '未来有你_Nooo', '未来有你_SOS', '未来有你_打call', '未来有你_登场', '未来有你_好耶',
     '未来有你_热情', '未来有你_生闷气', '未来有你_酸了',
     '未来有你_头晕晕', '未来有你_未来有你', '未来有你_真的么', '未来有你_走花路', '未来有你_走了', '未来有你_委屈'])
mymethod.non_official_chp = ['[永雏塔菲_令人兴奋]',
                             '[永雏塔菲_嘻嘻喵]',
                             '[永雏塔菲_对呀对呀]',
                             ]

useragent = gl.get_value('ua3')
csrf = gl.get_value('csrf3')  # 填入自己的csrf
cookie = gl.get_value('cookie3')
uid = gl.get_value('uid3')
login_check(cookie, useragent)
sleeptime = numpy.linspace(0.1, 1, 500, endpoint=False)
pinglunsuoxurenshu = 30
yuzancishu = 300  # 遇到点赞次数后停止
# limit_deadline = 3  # 算上今天 允许最久的动态
while True:
    try:
        limit_deadline = input('输入抽奖截止天数  tips：算上今天 允许最久的动态')
        limit_deadline = eval(limit_deadline)
        if type(limit_deadline) == int:
            break
    except:
        pass
end = 0  # 遇到点赞个数初始值
n = 0  # 动态个数初始值
caihongpi_chance = 1
pinglunzhuanbiancishu = 5
yuanshipingpinglun = []
zhuanpingdongtaicishu = 0
xiaoliwu = []
pinglunshibai = []
zhuanfashibai = []
choujiangdongtai = []
dianzanshibai = []
wuxuzhuanfa = []
User_Agent_List = [
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
yisichou = open('疑似抽奖（每日必查）.csv', 'w', encoding='utf-8')
kaijiang = open('开奖动态（每日必查）.csv', 'w', encoding='utf-8')
f = open('非官方抽奖动态.csv', 'w', encoding='utf-8')
p = open('评论失败的动态.csv', 'w', encoding='utf-8')
q = open('原视频下方评论.csv', 'w', encoding='utf-8')
# temp = open('log/抽奖转发评论信息（根据文件转评）（备份）.csv', 'w', encoding='utf-8')
# temp.close()
commentf = open('评论相关.csv', 'w', encoding='utf-8')
xiaowanyi = open('小礼物.csv', 'w', encoding='utf-8')
myfile = open('../抽奖转发评论信息（根据文件转评）.csv', 'w', encoding='utf-8')
myfile.close()
rengongfile = open('../人工审核抽奖转发评论信息（根据文件转评）.csv', 'w', encoding='utf-8')
rengongfile.close()
f.writelines('发布者uid\t动态链接\t动态内容\trid\ttype\t评论人数\n')
wuxuzhuanfaid = open('无需转发动态id（每日必查）.csv', 'w+', encoding='utf-8')


def quchong(inputfile, outputfile):
    with open(inputfile, 'r', encoding='utf8') as oringinfile, open(outputfile, 'w+', encoding='utf8') as resultfile:
        data = [item.strip() for item in oringinfile.readlines()]
        new_data = list(set(data))
        resultfile.writelines([item + '\n' for item in new_data if item])


def panduanbiaoqingbao(emo):
    hasemo = ['12周年', '藏狐', 'doge', '微笑', 'OK', '星星眼', '妙啊', '辣眼睛', '吃瓜', '滑稽', '喜欢', '嘟嘟',
              '给心心', '笑哭', '脱单doge',
              '嗑瓜子', '调皮', '歪嘴', '打call', '呲牙', '酸了', '哦呼', '嫌弃', '大哭', '害羞', '疑惑', '喜极而泣',
              '奸笑', '笑', '偷笑', '点赞',
              '无语',
              '惊喜', '大笑', '抠鼻', '呆', '囧', '阴险', '捂脸', '惊讶', '鼓掌', '尴尬', '灵魂出窍', '委屈', '傲娇',
              '疼', '冷', '生病', '吓',
              '吐',
              '撇嘴', '难过', '墨镜', '奋斗', '哈欠', '翻白眼', '再见', '思考', '嘘声', '捂眼', '抓狂', '生气', '口罩',
              '牛年', '2021', '水稻',
              '福到了',
              '鸡腿', '雪花', '视频卫星', '拥抱', '支持', '保佑', '响指', '抱拳', '加油', '胜利', '锦鲤', '爱心',
              '干杯', '跪了', '跪了', '怪我咯',
              '黑洞',
              '老鼠', '来古-沉思', '来古-呆滞', '来古-疑问', '来古-震撼', '来古-注意', '哭泣', '原神_嗯', '原神_哼',
              '原神_哇', '高兴', '气愤', '耍帅',
              '亲亲',
              '羞羞', '狗子', '哈哈', '原神_欸嘿', '原神_喝茶', '原神_生气', '热词系列_河南加油', '热词系列_豫你一起',
              '热词系列_仙人指路', '热词系列_饮茶先啦',
              '热词系列_知识增加', '热词系列_再来亿遍', '热词系列_好耶', '热词系列_你币有了', '热词系列_吹爆',
              '热词系列_妙啊', '热词系列_你细品', '热词系列_咕咕',
              '热词系列_标准结局', '热词系列_张三', '热词系列_害', '热词系列_问号', '热词系列_奥力给',
              '热词系列_猛男必看', '热词系列_有内味了', '热词系列_我裂开了',
              '热词系列_我哭了', '热词系列_高产', '热词系列_不愧是你', '热词系列_真香', '热词系列_我全都要',
              '热词系列_神仙UP', '热词系列_锤', '热词系列_秀',
              '热词系列_爷关更',
              '热词系列_我酸了', '热词系列_大师球', '热词系列_完结撒花', '热词系列_我太南了', '热词系列_镇站之宝',
              '热词系列_有生之年', '热词系列_知识盲区', '热词系列_“狼火”',
              '热词系列_你可真星', 'tv_白眼', 'tv_doge', 'tv_坏笑', 'tv_难过', 'tv_生气', 'tv_委屈', 'tv_斜眼笑',
              'tv_呆', 'tv_发怒',
              'tv_惊吓',
              'tv_笑哭', 'tv_亲亲', 'tv_调皮', 'tv_抠鼻', 'tv_鼓掌', 'tv_大哭', 'tv_疑问', 'tv_微笑', 'tv_思考',
              'tv_呕吐', 'tv_晕',
              'tv_点赞',
              'tv_害羞', 'tv_睡着', 'tv_色', 'tv_吐血', 'tv_无奈', 'tv_再见', 'tv_流汗', 'tv_偷笑', 'tv_发财',
              'tv_可爱', 'tv_馋',
              'tv_腼腆',
              'tv_鄙视', 'tv_闭嘴', 'tv_打脸', 'tv_困', 'tv_黑人问号', 'tv_抓狂', 'tv_生病', 'tv_流鼻血', 'tv_尴尬',
              'tv_大佬', 'tv_流泪',
              'tv_冷漠', 'tv_皱眉', 'tv_鬼脸', 'tv_调侃', 'tv_目瞪口呆', '坎公骑冠剑_吃鸡', '坎公骑冠剑_钻石',
              '坎公骑冠剑_无语', '热词系列_不孤鸟',
              '热词系列_对象',
              '保卫萝卜_问号', '保卫萝卜_哇', '保卫萝卜_哭哭', '保卫萝卜_笔芯', '保卫萝卜_白眼',
              '热词系列_多谢款待', '热词系列_EDG', '热词系列_我们是冠军', '脸红', '热词系列_破防了', '热词系列_燃起来了'
        , '热词系列_住在B站', '热词系列_B站有房', '热词系列_365', '热词系列_最美的夜', '热词系列_干杯',
              '热词系列_2022新年', '热词系列_奇幻时空', '热词系列_魔幻时空',
              '虎年', '冰墩墩', '雪容融',
              '热词系列_红红火火', '小电视_笑', '小电视_发愁', '小电视_赞', '小电视_差评', '小电视_嘟嘴', '小电视_汗',
              '小电视_害羞', '小电视_吃惊', '小电视_哭泣',
              '小电视_太太喜欢', '小电视_好怒啊', '小电视_困惑', '小电视_我好兴奋', '小电视_思索', '小电视_无语',
              '2233娘_大笑', '2233娘_吃惊', '2233娘_大哭',
              '2233娘_耶', '2233娘_卖萌', '2233娘_疑问', '2233娘_汗', '2233娘_困惑', '2233娘_怒', '2233娘_委屈',
              '2233娘_郁闷', '2233娘_第一',
              '2233娘_喝水', '2233娘_吐魂', '2233娘_无言'
              ]
    tihuanbiaoqing = []
    for biaoqing in emo:
        if (biaoqing not in hasemo):
            tihuanbiaoqing.append(biaoqing)
    return tihuanbiaoqing


def dynamic_new():
    typelist = 268435455
    url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid=' + str(uid) + '&type_list=' + str(
        typelist) + '&from=weball&platform=web'
    header = {
        'cookie': cookie,
        'user-agent': useragent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://t.bilibili.com/?spm_id_from=333.934.0.0',
        'Origin': 'https://www.bilibili.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'TE': 'trailers'
    }
    data = {
        'uid': uid,
        'type_list': typelist,
        'from': 'weball',
        'platform': 'web',
    }
    dynamic_newreq = requests.get(url=url, headers=header, data=data)
    return dynamic_newreq.text


def dynamic_history(next_offset):
    typelist = 268435455
    url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid=' + str(
        uid) + '&offset_dynamic_id=' + str(next_offset) + '&type=' + str(typelist) + '&from=weball&platform=web'
    header = {
        'cookie': cookie,
        'user-agent': useragent,
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'origin': 'https://t.bilibili.com',
        'referer': 'https://t.bilibili.com/?spm_id_from=333.1007.0.0',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': "Windows",
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    data = {
        'uid': uid,
        'offset_dynamic_id': next_offset,
        'type_list': typelist,
        'from': 'weball',
        'platform': 'web',
    }
    try:
        dynamic_historyreq = requests.get(url=url, headers=header, data=data)
    except Exception as e:
        print(e)
        time.sleep(int(input('输入等待时间')))
        traceback.print_exc()
        return dynamic_history(next_offset)
    if dynamic_historyreq.text == '{"code":-412,"message":"请求被拦截","ttl":1,"data":null}' or dynamic_historyreq.json().get(
            'code') != 0:
        print(timeshift(int(time.time())))
        while 1:
            try:
                print(dynamic_historyreq.text)
                time.sleep(eval(input('输入等待时间')))
                break
            except:
                continue
        dynamic_history(next_offset)
    return dynamic_historyreq.text


def timeshift(timestamp):
    local_time = time.localtime(timestamp)
    realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
    return realtime


def get_singledynamic_cards_jsonlist(dynamic_cards_list):
    global n
    detaillist = [[] for _ in range(len(dynamic_cards_list))]
    # uid 用户名 动态id 网址 rid 内容 时间 评论数 转发数 是否点赞 动态类型
    detaillisti = 0
    for singledynamic in dynamic_cards_list:
        origin_uname = None
        try:
            n += 1
            print('第' + str(n) + '次获取动态')
            dynamic_card_json = json.loads(singledynamic.get('card'))
            dynamic_id = str(eval(singledynamic.get('desc').get('dynamic_id_str')))
            dynamic_url = 'https://t.bilibili.com/' + dynamic_id + '?tab=2'
            dynamic_rid = str(singledynamic.get('desc').get('rid'))
            dynamic_repostcount = singledynamic.get('desc').get('repost')
            dynamic_commentcount = singledynamic.get('desc').get('comment')
            dynamic_is_liked = singledynamic.get('desc').get('is_liked')
            dynamic_type = str(singledynamic.get('desc').get('type'))
            dynamic_timestamp = singledynamic.get('desc').get('timestamp')
            dynamic_uname = singledynamic.get('desc').get('user_profile').get('info').get('uname')
            dynamic_uid = singledynamic.get('desc').get('user_profile').get('info').get('uid')
            if dynamic_uname == username:
                continue
        except:
            print('singledynamic', singledynamic)
            print(singledynamic)
            traceback.print_exc()
            continue
        try:
            if str(dynamic_type) == '64':
                dynamic_commentcount = json.loads(singledynamic.get('card')).get('stats').get('reply')
        except:
            print('专栏评论数获取失败')
        print(dynamic_uname)
        print('动态url：' + dynamic_url)
        print('发布时间：' + timeshift(dynamic_timestamp))
        if dynamic_type == '1':
            dynamic_content = dynamic_card_json.get('item').get('content')
            try:
                origin_uname = dynamic_card_json.get('origin_user').get('info').get('uname')
            except Exception as e:
                print('singledynamic', singledynamic)
                traceback.print_exc()
                print(e)

            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('转发动态或转发视频：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '2':
            dynamic_content = dynamic_card_json.get('item').get('description')
            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带图原创动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '4':
            dynamic_content = dynamic_card_json.get('item').get('content')
            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('不带图的原创动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '8':
            dynamic_content0 = dynamic_card_json.get('title')
            dynamic_content1 = dynamic_card_json.get('desc')
            dynamic_content2 = dynamic_card_json.get('dynamic')
            if len(dynamic_rid) == len(dynamic_id):
                oid = dynamic_id
            else:
                oid = dynamic_rid
            time.sleep(random.choice(sleeptime))
            dynamic_content3 = mymethod.get_topcomment(str(dynamic_id), str(oid), str(0), str(dynamic_type),
                                                       dynamic_uid)
            time.sleep(random.choice(sleeptime))
            if dynamic_content3 != 'null':
                dynamic_content = dynamic_content0 + dynamic_content1 + dynamic_content2 + dynamic_content3
            else:
                dynamic_content = dynamic_content0 + dynamic_content1 + dynamic_content2
            dynamic_commentcount = dynamic_card_json.get('stat').get('reply')
            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('原创视频：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '64':
            dynamic_content1 = dynamic_card_json.get('summary')
            if len(dynamic_rid) == len(dynamic_id):
                oid = dynamic_id
            else:
                oid = dynamic_rid
            dynamic_content2 = mymethod.get_topcomment(str(dynamic_id), str(oid), str(0), str(dynamic_type),
                                                       dynamic_uid)
            dynamic_content = dynamic_content1 + dynamic_content2
            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('专栏动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '4308':
            dynamic_content = '直播间标题，无视'
            # print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print(dynamic_card_json.get('live_play_info').get('title'))
            # print('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('直播动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        elif dynamic_type == '2048':
            dynamic_content = dynamic_card_json.get('vest').get('content')
            print(dynamic_content)
            # print(
            #     '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
            print('带简报的动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
        else:
            dynamic_content = 'Error'
        try:
            official_type = singledynamic.get('desc').get('user_profile').get('card').get(
                'official_verify').get(
                'type')
        except:
            print('获取official_type失败')
            official_type = 404
        try:
            if len(dynamic_rid) == len(dynamic_id):
                oid = dynamic_id
            else:
                oid = dynamic_rid
            if dynamic_commentcount >= 50 and dynamic_type != '8' and dynamic_type != '64':
                dyc = mymethod.get_topcomment(str(dynamic_id), str(oid), str(0), str(dynamic_type), dynamic_uid)
                dynamic_content += dyc
        except:
            pass
        detaildict = {
            'dynamic_uid': dynamic_uid,
            'dynamic_uname': dynamic_uname,
            'dynamic_id': dynamic_id,
            'dynamic_url': dynamic_url,
            'dynamic_rid': dynamic_rid,
            'dynamic_content': Converter('zh-hans').convert(dynamic_content),  # 进行繁体转简体
            'dynamic_timestamp': timeshift(dynamic_timestamp),
            'dynamic_commentcount': dynamic_commentcount,
            'dynamic_repostcount': dynamic_repostcount,
            'dynamic_is_liked': dynamic_is_liked,
            'dynamic_type': dynamic_type,
            'official_type': official_type,
            'origin_uname': origin_uname,
        }
        xinxichuli(detaildict)
        detaillist[detaillisti] = detaildict
        detaillisti += 1
        print("\033[1;31;47m\n\033[0m")
        if n % 500 == 0:
            print('到达500条休息30秒\n\n\n\n\n')
            time.sleep(30)
    return detaillist


def get_list_detail_dynamic(dynamic_req):
    dynamic_dict = json.loads(dynamic_req)
    try:
        dynamic_cards_list = dynamic_dict.get('data').get('cards')
        print('\t\t此页共有' + str(len(dynamic_cards_list)) + '条动态\n')
        detaillist = get_singledynamic_cards_jsonlist(dynamic_cards_list)
        return detaillist
    except Exception as e:
        print(e)
        print(dynamic_dict)
        traceback.print_exc()
        exit(114514)


def kaijiangpanduan(tcontent):
    matchobj8 = re.match('.*点击互动抽奖查看.*', tcontent, re.DOTALL)
    matchobj7 = re.match('.*恭喜.*获得.*', tcontent, re.DOTALL)
    matchobj6 = re.match('.*开奖啦！.*', tcontent, re.DOTALL)
    matchobj5 = re.match('.*来开奖！.*', tcontent, re.DOTALL)
    matchobj4 = re.match('.*恭喜.*中奖.*', tcontent, re.DOTALL)
    matchobj3 = re.match('.*福利公示.*', tcontent, re.DOTALL)
    matchobj2 = re.match('.*开奖.*祝贺.*获得.*', tcontent, re.DOTALL)
    matchobj1 = re.match('.*开奖.*恭喜.*获得.*', tcontent, re.DOTALL)
    matchobj_1 = re.match('.*转.*评.*', tcontent, re.DOTALL)
    if (matchobj1 != None or matchobj2 != None or matchobj3 != None or matchobj4 != None or matchobj5 != None or
            matchobj6 != None or matchobj7 != None or matchobj8 != None and matchobj_1 == None):
        return 1
    else:
        return None


def yisichoujiangpanduan(tcontent):
    obj14 = re.match('.*获得.*', tcontent, re.DOTALL)
    obj13 = re.match('.*看.{0,10}图.*|.*见.{0,10}图.*', tcontent, re.DOTALL)
    obj12 = re.match('.*开奖.*', tcontent, re.DOTALL)
    obj11 = re.match('.*啾.*', tcontent, re.DOTALL)
    obj10 = re.match('.*卷.*', tcontent, re.DOTALL)
    obj9 = re.match('.*安排.*', tcontent, re.DOTALL)
    obj8 = re.match('.*补贴.*', tcontent, re.DOTALL)
    obj7 = re.match('.*车专.*', tcontent, re.DOTALL)
    obj6 = re.match('.*嫖.*', tcontent, re.DOTALL)
    obj5 = re.match('.*抽.*', tcontent, re.DOTALL)
    obj4 = re.match('.*送.*', tcontent, re.DOTALL)
    obj3 = re.match('.*请.*', tcontent, re.DOTALL)
    obj2 = re.match('.*揪.*', tcontent, re.DOTALL)
    obj1 = re.match('.*转.*', tcontent, re.DOTALL)
    if (
            obj1 != None or obj2 != None or obj3 != None or obj4 != None or obj5 != None or obj6 != None or obj7 != None or obj8 != None
            or obj9 != None or obj10 != None or obj11 != None or obj12 != None or obj13 != None or obj14 != None

    ):
        return 1
    else:
        return None


def xinxichuli(single_dynamic_list):
    # detaildict = {
    #     'dynamic_uid': dynamic_uid,
    #     'dynamic_uname': dynamic_uname,
    #     'dynamic_id': dynamic_id,
    #     'dynamic_url': dynamic_url,
    #     'dynamic_rid': dynamic_rid,
    #     'dynamic_content': dynamic_content,
    #     'dynamic_timestamp': timeshift(dynamic_timestamp),
    #     'dynamic_commentcount': dynamic_commentcount,
    #     'dynamic_repostcount': dynamic_repostcount,
    #     'dynamic_is_liked': dynamic_is_liked,
    #     'dynamic_type': dynamic_type,
    #     'official_type': official_type,
    #     'origin_uname': origin_uname,
    # }
    global end, zhuanpingdongtaicishu, wuxuzhuanfa
    suffix = '?tab=2'  # 默认转评
    uname = single_dynamic_list.get('dynamic_uname')
    dongtaineirong = single_dynamic_list.get('dynamic_content')
    dynamic_id = single_dynamic_list.get('dynamic_id')
    thumbstatus = single_dynamic_list.get('dynamic_is_liked')
    pinglunrenshu = single_dynamic_list.get('dynamic_commentcount')
    dynamic_repostcount = single_dynamic_list.get('dynamic_repostcount')
    dynamic_timestamp = single_dynamic_list.get('dynamic_timestamp')
    fuid = single_dynamic_list.get('dynamic_uid')
    rid = single_dynamic_list.get('dynamic_rid')
    type = single_dynamic_list.get('dynamic_type')
    official_type = single_dynamic_list.get('official_type')
    if re.match(r'.*//@.*', str(dongtaineirong), re.DOTALL) != None:
        dongtaineirong = re.findall(r'(.*?)//@', dongtaineirong, re.DOTALL)[0]
    if yisichoujiangpanduan(str(dongtaineirong)):
        yisichou.writelines(
            uname + '\t' + repr(str(dongtaineirong)) + '\thttps://t.bilibili.com/' + dynamic_id + '\t' + str(
                pinglunrenshu) + '\t' + str(dynamic_repostcount) + '\t' + str(dynamic_timestamp))
        if mymethod.daily_choujiangxinxipanduan(str(dongtaineirong)) != None:
            if kaijiangpanduan(str(dongtaineirong)):
                kaijiang.writelines(
                    uname + '\t' + repr(str(dongtaineirong)) + '\thttps://t.bilibili.com/' + dynamic_id + '\n')
                time.sleep(random.choice(sleeptime))
                print('开奖动态')
                yisichou.writelines('\t' + '开奖动态\n')
                return 1
            print('不含抽奖信息，跳过\n')
            yisichou.writelines('\t' + '不含抽奖信息\n')
            time.sleep(random.choice(sleeptime))
            return 1
    if mymethod.daily_choujiangxinxipanduan(str(dongtaineirong)) != None:
        if kaijiangpanduan(str(dongtaineirong)):
            kaijiang.writelines(
                uname + '\t' + repr(str(dongtaineirong)) + '\thttps://t.bilibili.com/' + dynamic_id + '\n')
            time.sleep(random.choice(sleeptime))
            print('开奖动态')
            # yisichou.writelines('\t' + '开奖动态\n')
            return 1
        print('不含抽奖信息，跳过\n')
        # yisichou.writelines('\t' + '不含抽奖信息\n')
        time.sleep(random.choice(sleeptime))
        return 1
    if kaijiangpanduan(str(dongtaineirong)):
        kaijiang.writelines(
            uname + '\t' + repr(str(dongtaineirong)) + '\thttps://t.bilibili.com/' + dynamic_id + '\n')
        time.sleep(random.choice(sleeptime))
        print('开奖动态')
        yisichou.writelines('\t' + '开奖动态\n')
        return 1
    if thumbstatus == 1:
        end += 1
        print('第' + str(end) + '遇到点过赞的动态' + dynamic_id + '\n')
        print(
            '\033[4;31;40m点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n点过赞啦\n\033[0m')
        if end == 1:
            with open('../人工审核抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as mf:
                mf.writelines('第一次遇到点过赞的动态：**********************************\n')
            with open('../抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as mf:
                mf.writelines('第一次遇到点过赞的动态：**********************************\n')
            yuanshipingpinglun.append(['第一次遇到点过赞的动态：**********************************'])
        time.sleep(random.choice(sleeptime))
        yisichou.writelines('\t' + '遇到点过赞的动态\n')
        yisichou.writelines('\n*********************************************\n')
        return 1
    try:
        try:
            int(pinglunrenshu) <= pinglunsuoxurenshu
        except:
            print(single_dynamic_list)
            pinglunrenshu = 999999
        if int(pinglunrenshu) <= pinglunsuoxurenshu:
            time.sleep(random.choice(sleeptime))
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id) + '?tab=2'
            print('原视频抽奖：' + str(lianjie) + '\n')
            if str(type) == '1':
                origin_name = single_dynamic_list.get('origin_uname')
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname,
                                            origin_name)
            else:
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname)
            print('回复转发内容：' + str(msg))
            q.writelines(
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=dynamic_id, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
            if mymethod.zhuanfapanduan(dongtaineirong):
                houzhui = '?tab=2'
            else:
                houzhui = ''
            detaillist = [
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=str(dynamic_id) + houzhui, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount)]
            yuanshipingpinglun.append(detaillist)
            yisichou.writelines('\t' + '评论人数过少，原视频抽奖\n')
            return 1
    except Exception as e:
        print(pinglunrenshu)
        print(single_dynamic_list)
        print(e)
        print(
            '\033[4;31;40mWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\n\033[0m')
        traceback.print_exc()
        yisichou.writelines('\t' + '评论人数过少，原视频抽奖\n')
        return 1
    if int(pinglunrenshu) > pinglunsuoxurenshu:
        matchobj000 = re.match('.*直播抽奖.*', str(dongtaineirong), re.DOTALL)
        matchobj001 = re.match('.*转发评论视频.*', str(dongtaineirong), re.DOTALL)
        matchobj002 = re.match('.*视频评论.*抽.*', str(dongtaineirong), re.DOTALL)
        matchobj003 = re.match('.*在原视频下.*', str(dongtaineirong), re.DOTALL)
        matchobj004 = re.match('.*转发.*评论.*弹幕.*视频.*', str(dongtaineirong), re.DOTALL)
        obj1 = re.match('.*原视频.*', str(dongtaineirong), re.DOTALL)
        obj2 = re.match('.*在.*视频下.*转.*评.*', str(dongtaineirong), re.DOTALL)
        obj3 = re.match('.*转发https://.*', str(dongtaineirong), re.DOTALL)
        obj4 = re.match('.*原视频.*评.*抽', str(dongtaineirong), re.DOTALL)
        obj5 = re.match('.*在视频.*抽.*', str(dongtaineirong), re.DOTALL)
        obj6 = re.match('.*点开视频.*评论区.*弹幕.*', str(dongtaineirong), re.DOTALL)
        obj7 = re.match('.*关注+转发+评论以下视频.*', str(dongtaineirong), re.DOTALL)
        obj8 = re.match('.*在视频弹幕区和评论区.*', str(dongtaineirong), re.DOTALL)
        obj9 = re.match('.*原动态.*', str(dongtaineirong), re.DOTALL)
        obj10 = re.match('.*关注.*转发.*评论视频', str(dongtaineirong), re.DOTALL)
        obj11 = re.match('.*来下方动态.*参加抽奖.*', str(dongtaineirong), re.DOTALL)
        obj12 = re.match('.*参与.*话题互动.*并@.*', str(dongtaineirong), re.DOTALL)
        obj13 = re.match('.*评论、弹幕、转发.*从中选出.*', str(dongtaineirong), re.DOTALL)
        obj15 = re.match('.*三连里面抽.*', str(dongtaineirong), re.DOTALL)
        obj16 = re.match('.*转发.*评论.*下方视频.*', str(dongtaineirong), re.DOTALL)
        obj17 = re.match('.*评论.*弹幕.*', str(dongtaineirong), re.DOTALL)
        obj19 = re.match('.*在评论下面.*', str(dongtaineirong), re.DOTALL)
        obj20 = re.match('.*转关评本专栏文章.*', str(dongtaineirong), re.DOTALL)
        obj21 = re.match('.*弹幕.*揪.*送.*', str(dongtaineirong), re.DOTALL)
        obj22 = re.match('.*点赞并评论视频.*', str(dongtaineirong), re.DOTALL)
        obj23 = re.match('.*弹幕抽.*', str(dongtaineirong), re.DOTALL)
        obj24 = re.match('.*视频.*一键三连.*抽.*', str(dongtaineirong), re.DOTALL)
        obj25 = re.match('.*关注.*转发.*评论.*本视频.*', str(dongtaineirong), re.DOTALL)
        obj26 = re.match('.*下方视频.*抽.*送.*', str(dongtaineirong), re.DOTALL)
        obj27 = re.match('.*视频.*一键三连.*', str(dongtaineirong), re.DOTALL)
        obj28 = re.match('.*置顶动态.*抽奖.*', str(dongtaineirong), re.DOTALL)
        obj29 = re.match('.*三连.*转发.*', str(dongtaineirong), re.DOTALL)
        obj30 = re.match('.*点击下方动态链接.*抽奖.*', str(dongtaineirong), re.DOTALL)
        obj31 = re.match('.*视频.*的评论底下.*揪.*', str(dongtaineirong), re.DOTALL)
        obj32 = re.match('.*视频.*一键三联.*', str(dongtaineirong), re.DOTALL)
        obj33 = re.match('.*弹幕.*评论.*选', str(dongtaineirong), re.DOTALL)
        obj34 = re.match('.*文章内.*评论区.*', str(dongtaineirong), re.DOTALL)
        obj35 = re.match('.*抽奖传送门.*', str(dongtaineirong), re.DOTALL)
        obj36 = re.match('.*置顶动态.*', str(dongtaineirong), re.DOTALL)
        obj37 = re.match('.*原抽奖动态.*', str(dongtaineirong), re.DOTALL)
        if (
                obj10 != None or obj9 != None or obj8 != None or obj7 != None or obj6 != None or obj5 != None or obj1 != None or
                obj2 != None or obj3 != None or obj4 != None or matchobj001 != None or matchobj002 != None or matchobj003 != None
                or matchobj004 != None or obj11 != None or obj12 != None or obj13 != None or obj15 != None or obj16 != None
                or obj17 != None or obj19 != None or obj20 != None or obj21 != None or obj22 != None or obj23 != None
                or obj24 != None or obj25 != None or obj26 != None or obj27 != None or obj28 != None or obj29 != None
                or obj30 != None or obj31 != None or obj32 != None or obj33 != None or obj34 != None or obj35 != None
                or obj36 != None or obj37 != None
        ):
            if str(type) == '1':
                origin_name = single_dynamic_list.get('origin_uname')
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname,
                                            origin_name)
            else:
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname)
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id) + '?tab=2'
            if mymethod.zhuanfapanduan(dongtaineirong):
                houzhui = '?tab=2'
            else:
                houzhui = ''
            detaillist = [
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=str(dynamic_id) + houzhui, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount)]
            yuanshipingpinglun.append(detaillist)
            print('原动态抽奖：' + str(lianjie) + '\n')
            q.writelines(
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=dynamic_id, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg='好耶', pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))

            time.sleep(random.choice(sleeptime))
            yisichou.writelines('\t' + '原动态抽奖\n')
            return 1
        if (matchobj000 != None):
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id) + '?tab=2'
            if str(type) == '1':
                origin_name = single_dynamic_list.get('origin_uname')
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname,
                                            origin_name)
            else:
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname)
            if mymethod.zhuanfapanduan(dongtaineirong):
                houzhui = '?tab=2'
            else:
                houzhui = ''
            detaillist = [
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=str(dynamic_id) + houzhui, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount)]
            yuanshipingpinglun.append(detaillist)
            print('直播间抽奖：' + str(lianjie) + '\n')
            q.writelines(
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=dynamic_id, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg='好耶', pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
            time.sleep(random.choice(sleeptime))
            yisichou.writelines('\t' + '直播间抽奖\n')
            return 1
        xiaoliwuobj = re.match('.*香囊.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj1 = re.match('.*vlog套装.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj3 = re.match('.*狼人杀限量版联名卡牌.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj4 = re.match('.*美的口袋挂脖风扇.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj5 = re.match('.*绿源周边礼品.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj6 = re.match('.*帆布袋.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj7 = re.match('.*点娘十二生肖大礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj8 = re.match('.*一个人的古典.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj9 = re.match('.*周边礼盒.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj10 = re.match('.*航线召唤礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj11 = re.match('.*名校周边大礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj12 = re.match('.*吉祥文化书签一套.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj13 = re.match('.*小招喵抱枕.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj14 = re.match('.*RD定制腰枕.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj15 = re.match('.*可爱果味猫爪杯.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj16 = re.match('.*鹅博士公仔.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj17 = re.match('.*招募令礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj18 = re.match('.*雁翎甲礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj21 = re.match('.*补光灯.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj22 = re.match('.*珍贵影像.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj23 = re.match('.*签名照.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj24 = re.match('.*门票.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj26 = re.match('.*玩偶.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj27 = re.match('.*手持小风扇.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj28 = re.match('.*SKG品牌抱枕.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj29 = re.match('.*古茗千里江山图周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj30 = re.match('.*讯飞鼠标垫.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj31 = re.match('.*狼人杀卡牌.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj33 = re.match('.*狼人杀限量版限量礼盒.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj34 = re.match('.*茗茗.*奶茶.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj35 = re.match('.*炎天鼠标垫.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj36 = re.match('.*素乐桌面风扇.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj37 = re.match('.*鹅博士手提袋.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj38 = re.match('.*马克杯.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj39 = re.match('.*蔬菜精灵玩偶抱枕.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj40 = re.match('.*人人视频周边礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj41 = re.match('.*TT周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj42 = re.match('.*微泡抱枕.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj43 = re.match('.*七工匠精美周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj44 = re.match('.*品牌周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj45 = re.match('.*小风扇.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj46 = re.match('.*美的熊小美加油鸭杯.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj47 = re.match('.*小红龙玩偶.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj48 = re.match('.*阴阳师叠叠乐.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj49 = re.match('.*帽子.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj50 = re.match('.*累计视频播放时长排行、视频互动指标排行、动态互动指标排行.*', str(dongtaineirong),
                                 re.DOTALL)
        xiaoliwuobj51 = re.match('.*捞一下明天开.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj52 = re.match('.*新衣福袋.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj53 = re.match('.*小米静态积木飞鱼座穿梭器.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj54 = re.match('.*茗千里江山图周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj55 = re.match('.*公仔.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj56 = re.match('.*KiWi EV限定徽章.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj57 = re.match('.*南光周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj58 = re.match('.*超好用.*手机支架.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj60 = re.match('.*「芬达」周边礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj61 = re.match('.*帆软周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj62 = re.match('.*百闻牌挂画.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj63 = re.match('.*长腿风筝.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj64 = re.match('.*DMZJ限量法披.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj65 = re.match('.*命题小作文.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj66 = re.match('.*车模.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj67 = re.match('.*小蓝×脉动联名周边三件套.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj68 = re.match('.*特斯拉神秘手稿.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj69 = re.match('.*吉祥文化书签.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj71 = re.match('.*古龙香水.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj72 = re.match('.*求职打气包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj73 = re.match('.*春秋航空机模.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj74 = re.match('.*九霄环佩.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj75 = re.match('.*转发赠书.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj76 = re.match('.*牛蒙蒙运动周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj77 = re.match('.*香皂.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj78 = re.match('.*拯救者电竞手机x狼人杀联名卡牌.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj79 = re.match('.*数码宝贝食玩.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj80 = re.match('.*都市时报周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj81 = re.match('.*飞机模型.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj82 = re.match('.*浩瀚周边礼包.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj83 = re.match('.*七工匠周边.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj84 = re.match('.*派乐礼盒.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj85 = re.match('.*权益体验卡/九阳修缘盒.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj86 = re.match('.*权益体验卡or九阳修缘丹.*', str(dongtaineirong), re.DOTALL)
        xiaoliwuobj87 = re.match('.*权益体验卡.*', str(dongtaineirong), re.DOTALL)
        if (xiaoliwuobj != None or xiaoliwuobj1 != None or xiaoliwuobj3 != None
                or xiaoliwuobj4 != None or xiaoliwuobj5 != None or xiaoliwuobj6 != None or xiaoliwuobj7 != None or xiaoliwuobj8 != None
                or xiaoliwuobj9 != None or xiaoliwuobj10 != None or xiaoliwuobj11 != None or xiaoliwuobj12 != None or xiaoliwuobj13 != None
                or xiaoliwuobj14 != None or xiaoliwuobj15 != None or xiaoliwuobj16 != None or xiaoliwuobj17 != None or xiaoliwuobj18 != None
                or xiaoliwuobj21 != None or xiaoliwuobj22 != None or xiaoliwuobj23 != None or xiaoliwuobj24 != None
                or xiaoliwuobj26 != None or xiaoliwuobj27 != None or xiaoliwuobj28 != None or xiaoliwuobj29 != None
                or xiaoliwuobj30 != None or xiaoliwuobj31 != None or xiaoliwuobj33 != None or xiaoliwuobj34 != None or xiaoliwuobj85 != None
                or xiaoliwuobj35 != None or xiaoliwuobj36 != None or xiaoliwuobj37 != None or xiaoliwuobj38 != None or xiaoliwuobj39 != None
                or xiaoliwuobj40 != None or xiaoliwuobj41 != None or xiaoliwuobj42 != None or xiaoliwuobj43 != None or xiaoliwuobj44 != None
                or xiaoliwuobj45 != None or xiaoliwuobj46 != None or xiaoliwuobj47 != None or xiaoliwuobj48 != None or xiaoliwuobj49 != None
                or xiaoliwuobj50 != None or xiaoliwuobj51 != None or xiaoliwuobj52 != None or xiaoliwuobj53 != None or xiaoliwuobj54 != None
                or xiaoliwuobj55 != None or xiaoliwuobj56 != None or xiaoliwuobj57 != None or xiaoliwuobj58 != None
                or xiaoliwuobj60 != None or xiaoliwuobj61 != None or xiaoliwuobj62 != None or xiaoliwuobj63 != None or xiaoliwuobj64 != None
                or xiaoliwuobj65 != None or xiaoliwuobj66 != None or xiaoliwuobj67 != None or xiaoliwuobj68 != None or xiaoliwuobj69 != None
                or xiaoliwuobj71 != None or xiaoliwuobj72 != None or xiaoliwuobj73 != None or xiaoliwuobj74 != None
                or xiaoliwuobj75 != None or xiaoliwuobj76 != None or xiaoliwuobj77 != None or xiaoliwuobj78 != None or xiaoliwuobj79 != None
                or xiaoliwuobj80 != None or xiaoliwuobj81 != None or xiaoliwuobj82 != None or xiaoliwuobj83 != None or xiaoliwuobj84 != None
                or xiaoliwuobj86 != None or xiaoliwuobj86 != None or xiaoliwuobj87 != None

        ):
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id) + '?tab=2'
            if str(type) == '1':
                origin_name = single_dynamic_list.get('origin_uname')
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname,
                                            origin_name)
            else:
                msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname)
            print('回复转发内容：' + str(msg))
            if mymethod.zhuanfapanduan(dongtaineirong):
                houzhui = '?tab=2'
            else:
                houzhui = ''
            detaillist = [
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=str(dynamic_id) + houzhui, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount)]
            yuanshipingpinglun.append(detaillist)
            xiaoliwu.append(detaillist)
            print('小礼物：' + str(lianjie) + '\n')
            xiaowanyi.writelines(
                '{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                    dynamic_id=dynamic_id, uname=uname,
                    dongtaineirong=repr(
                        dongtaineirong.replace('\t',
                                               '').replace(
                            '"', '').strip()),
                    msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
            time.sleep(random.choice(sleeptime))
            yisichou.writelines('\t' + '小礼物没参与\n')
            return 1
        dongtaineirong = dongtaineirong.replace('🧱', '转')
        dongtaineirong = dongtaineirong.replace('🍎', '评')
        zhuanfapanduan_3 = re.match('.*不用转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan_2 = re.match('.*无需转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan_1 = re.match('.*别转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan1 = re.match('.*转发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan2 = re.match('.*卷发.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan3 = re.match('.*转.{0,10}评.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan4 = re.match('.*转.{0,10}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan5 = re.match('.*转.{0,10}揪.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan6 = re.match('.*转.{0,10}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan7 = re.match('.*卷.{0,10}评.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan8 = re.match('.*卷.{0,10}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan9 = re.match('.*卷.{0,10}揪.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan10 = re.match('.*卷.{0,10}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan11 = re.match('.*专.{0,10}评.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan12 = re.match('.*专.{0,10}抽.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan13 = re.match('.*专.{0,10}揪.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan14 = re.match('.*专.{0,10}送.*', str(dongtaineirong), re.DOTALL)
        zhuanfapanduan15 = re.match('.*转评.*', str(dongtaineirong), re.DOTALL)
        if (zhuanfapanduan1 == None and zhuanfapanduan2 == None and zhuanfapanduan3 == None and zhuanfapanduan4 == None
                and zhuanfapanduan5 == None and zhuanfapanduan6 == None and zhuanfapanduan7 == None and zhuanfapanduan8 == None
                and zhuanfapanduan9 == None and zhuanfapanduan10 == None and zhuanfapanduan11 == None and zhuanfapanduan12 == None
                and zhuanfapanduan13 == None and zhuanfapanduan14 == None and zhuanfapanduan15 == None
                or zhuanfapanduan_1 != None or zhuanfapanduan_2 != None or zhuanfapanduan_3 != None
        ):
            suffix = ''
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            detaillist = [uname, lianjie, str(dongtaineirong), type, rid]
            wuxuzhuanfa.append(detaillist)
            wuxuzhuanfaid.write(
                detaillist[1] + '\t' + repr(detaillist[2]) + '\t' + detaillist[3] + '\t' + detaillist[4] + '\n')
        print('https://space.bilibili.com/' + str(fuid) + '\t' + 'https://t.bilibili.com/' + str(dynamic_id) + '\n')
        f.writelines('https://space.bilibili.com/' + str(fuid) + '\t' + 'https://t.bilibili.com/' + str(
            dynamic_id) + '\t' + repr(str(dongtaineirong)) + '\t' + str(rid) + '\t' + str(type) + '\t' + str(
            pinglunrenshu) + '\n')
        time.sleep(random.choice(sleeptime))
        if str(type) == '1':
            origin_name = single_dynamic_list.get('origin_uname')
            msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname, origin_name)
        else:
            msg = mymethod.huifuneirong(official_type, str(dongtaineirong), dynamic_id, rid, type, uname)
        print('回复转发内容：' + str(msg))
        if msg != '':
            if not '\u200b互动抽奖' in dongtaineirong:
                # comment(dynamic_id, msg, type, rid)
                commentf.writelines(
                    'https://t.bilibili.com/' + str(dynamic_id) + '\t' + repr(str(msg)) + '\t' + repr(
                        str(dongtaineirong)) + '\n')

            rengonghuifu_panduan = re.match('.*评论.*告诉|'
                                            '.*评论.*理由|'
                                            '.*评论.{0,10}对|'
                                            '.*三连|'
                                            '.*说.{0,10}说|'
                                            '.*@.{0,10}好友|'
                                            '.*万粉福利|'
                                            '.*新衣回|'
                                            '.*评论.{0,10}留言|'
                                            '.*恭喜|'
                                            '.*评论.{0,10}祝福|'
                                            '.*评论.{0,10}讨论|'
                                            '.*@.{0,10}朋友|'
                                            '.*评论.{0,10}说出|'
                                            '.*评论.{0,10}分享|'
                                            '.*评论.{0,10}聊.{0,10}聊|'
                                            '.*评论区评论.{0,10}#|'
                                            '.*聊.{0,10}聊|'
                                            '.*评论.{0,10}扣|'
                                            '.*转发.{0,10}分享|'
                                            '.*评论.{0,10}告诉|'
                                            '.*评论.{0,10}唠.{0,10}唠|'
                                            '.*今日话题|'
                                            '.*说.*答案|'
                                            '.*说出|'
                                            '.*为.{0,10}加油|'
                                            '.*评论.{0,10}话|'
                                            '.*评论.{0,10}最想做的事|'
                                            '.*分享.{0,20}经历|'
                                            '.*分享.{0,20}心情|'
                                            '.*评论.{0,10}句|'
                                            '.*转关评下方视频|'
                                            '.*分享.{0,10}美好|'
                                            '.*视频.{0,10}弹幕|'
                                            '.*生日快乐|'
                                            '.*正确回答|'
                                            '.*谈.{0,10}谈|'
                                            '.*分享.{0,10}喜爱|'
                                            '.*分享.{0,10}最'
                                            , dongtaineirong, re.S)
            print(rengonghuifu_panduan)
            if rengonghuifu_panduan:
                try:
                    with open('../人工审核抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=dynamic_id, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
                except:
                    with open('../人工审核抽奖转发评论信息（根据文件转评）.csv', 'w', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=dynamic_id, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))

                try:
                    with open('./log/人工审核抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=dynamic_id, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
                except:
                    with open('./log/人工审核抽奖转发评论信息（根据文件转评）.csv', 'w', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=dynamic_id, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))


            else:
                # if '#' in msg:
                #     suffix = '?tab=3'
                try:
                    with open('../抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=str(dynamic_id) + suffix, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
                except:
                    with open('../抽奖转发评论信息（根据文件转评）.csv', 'w', encoding='utf-8') as mf:
                        mf.writelines(
                            'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                                dynamic_id=str(dynamic_id) + suffix, uname=uname,
                                dongtaineirong=repr(
                                    dongtaineirong.replace('\t',
                                                           '').replace(
                                        '"', '').strip()),
                                msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
            with open('log/抽奖转发评论信息（根据文件转评）（备份）.csv', 'a+', encoding='utf-8') as mf:
                mf.writelines(
                    'https://t.bilibili.com/{dynamic_id}\t{uname}\t{dongtaineirong}\t{msg}\t{pinglunrenshu}\t{dynamic_repostcount}\n'.format(
                        dynamic_id=dynamic_id, uname=uname,
                        dongtaineirong=repr(
                            dongtaineirong.replace('\t',
                                                   '').replace(
                                '"', '').strip()),
                        msg=repr(msg), pinglunrenshu=pinglunrenshu, dynamic_repostcount=dynamic_repostcount))
            time.sleep(random.choice(sleeptime))
            zhuanfapanduan1 = re.match('.*转发.*', str(dongtaineirong), re.DOTALL)
            zhuanfapanduan2 = re.match('.*卷发.*', str(dongtaineirong), re.DOTALL)
            zhuanfapanduan3 = re.match('.*转.*', str(dongtaineirong), re.DOTALL)
            zhuanfapanduan4 = re.match('.*互动抽奖.*', str(dongtaineirong), re.DOTALL)
            zhuanfapanduan5 = '车专' in dongtaineirong
            zhuanfapanduan6 = re.match('.*卷.*', str(dongtaineirong), re.DOTALL)
            if (zhuanfapanduan1 != None or zhuanfapanduan2 != None or zhuanfapanduan3 != None
                    or zhuanfapanduan4 != None or zhuanfapanduan5 != None or zhuanfapanduan6 != None):
                # repost(dynamic_id, msg)
                yisichou.writelines('\t' + '已转发评论\n')
            else:
                yisichou.writelines('\t' + '已评论\n')
                print('无需转发：https://t.bilibili.com/' + str(dynamic_id))
            time.sleep(random.choice(sleeptime))
            # thumb(dynamic_id)
            choujianglianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            choujiangdongtai.append(choujianglianjie)
            zhuanpingdongtaicishu += 1
            print('\n')
            time.sleep(random.choice(sleeptime))
        else:
            print('评论失败\n原因：获取评论失败')
            choujianglianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            pinglunshibai.append(choujianglianjie)
            yisichou.writelines('\t' + '转发失败\n')


def quit():
    global f
    f.close()
    print('共有' + str(choujiangdongtai.__len__()) + '条非官方抽奖动态')
    print(choujiangdongtai)
    print('\n\n\n')
    print('原视频抽奖：')
    print(yuanshipingpinglun)
    with open('../抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as myl:
        myl.writelines('原视频抽奖：\n')
        for i in yuanshipingpinglun:
            print('https://t.bilibili.com/' + i[0])
            myl.writelines('https://t.bilibili.com/{}'.format(i[0]))
    print('\n\n\n')
    print('总转发评论数：' + str(zhuanpingdongtaicishu))
    for i in pinglunshibai:
        print('https://t.bilibili.com/' + i[0])
        p.writelines('\n')
    print('\n\n\n')
    print('小东西：')
    with open('../抽奖转发评论信息（根据文件转评）.csv', 'a+', encoding='utf-8') as myl:
        myl.writelines('小东西：\n')
        for i in xiaoliwu:
            if i in yuanshipingpinglun:
                print('在原视频评论中出现过')
                continue
            print('https://t.bilibili.com/' + i[0])
            myl.writelines(i)
    print('\n\n\n')
    print('无需转发：')
    for i in wuxuzhuanfa:
        print(i)
    print('点赞失败：' + str(dianzanshibai))
    print('评论失败：' + str(pinglunshibai))
    print('转发失败：' + str(zhuanfashibai))
    xiaowanyi.close()
    p.close()
    q.close()
    commentf.close()
    wuxuzhuanfaid.close()
    kaijiang.close()
    yisichou.close()
    yisichoujiangbeifen = open('./log/疑似抽奖（累计.csv', 'a+', encoding='utf-8')
    with open('疑似抽奖（每日必查）.csv', 'r', encoding='utf-8') as f:
        for i in f:
            yisichoujiangbeifen.writelines('{}'.format(i))
    yisichoujiangbeifen.close()
    for i in mymethod.None_nickname:
        print(i)


def main():
    global f
    print(timeshift(time.time()))
    dynamic_new_req = dynamic_new()
    dynamic_detail_list = get_list_detail_dynamic(dynamic_new_req)
    dynamic_dict = json.loads(dynamic_new_req)
    offset = str(dynamic_dict.get('data').get('history_offset'))
    print('offset=' + offset)
    now_date = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          '%Y-%m-%d %H:%M:%S')
    while True:
        if end >= yuzancishu:
            print('到达指定遇赞次数，结束')
            break
        dynamic_history_req = dynamic_history(offset)
        dynamic_detail_list = get_list_detail_dynamic(dynamic_history_req)
        dynamic_dict = json.loads(dynamic_history_req)
        offset = str(dynamic_dict.get('data').get('next_offset'))
        print('offset=' + offset)
        try:
            new_dynamic_timestamp = dynamic_detail_list[1].get('dynamic_timestamp')
        except:
            print('error\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\terror\t')
            print(dynamic_detail_list[1])
            new_dynamic_timestamp = str(datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          '%Y-%m-%d %H:%M:%S'))

        print('相差天数：', (now_date - datetime.datetime.strptime(new_dynamic_timestamp, '%Y-%m-%d %H:%M:%S')).days + 1)
        if (now_date - datetime.datetime.strptime(new_dynamic_timestamp,
                                                  '%Y-%m-%d %H:%M:%S')).days >= limit_deadline and yuzancishu > 0:  # 到了指定日期同时遇到了点过赞的动态
            print(f'超过指定{limit_deadline}天数，结束')
            break

        elif (now_date - datetime.datetime.strptime(new_dynamic_timestamp,
                                                    '%Y-%m-%d %H:%M:%S')).days >= 2 * limit_deadline:
            print(f'超过两倍的指定{limit_deadline}天数，强制结束')
            break


if __name__ == '__main__':
    register(quit)
    main()
