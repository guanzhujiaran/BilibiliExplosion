# -*- coding: utf-8 -*-
import traceback

import execjs
import json
import random
import re
import sys

sys.path.append('C:/pythontest/')
# sys.path.append('/home/aistudio/') #将该目录添加到该文件夹下，把当前目录当成根目录使用
import datetime
import os

import js2py
import requests
import time

import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods

# import Bilibili_methods.paddlenlp

root_dir = 'C:/pythontest/'


class renew:
    def __init__(self):
        self._获取过动态的b站用户 = dict()  # 格式：{uid:[1,2,3,4,5,6,7,8,9,10]} 最后一次获取的动态
        self._最后一次获取过动态的b站用户 = dict()
        try:
            with open('获取过动态的b站用户.json') as f:
                self._获取过动态的b站用户 = json.load(f)
            print('上次获取的动态：')
            import pprint
            pprint.pprint(self._获取过动态的b站用户, indent=4)
        except Exception as e:
            print(e)
            traceback.print_exc()
            pass

        self.uidlist = [
            # 100680137,#你的工具人老公
            # 323360539,#猪油仔123
            20958956,  # T_T欧萌
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
            332793152,  # ⭐欧王本王
            87838475,  # *万事屋无痕
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
            20343656,
            1234463316,
            16101659,
            1056602325,
            1183157743,
            20094695,
            31341142,
            666801651,
            132973916,
            474695754,
            6369160,
            106821863,
            2064686761,
            1869690859,
            1824937075,
            409592750,
            2094045599,
            49478699,
            344389028,
            353393860,
            6781805,
            4586734,
            90123009,
            71583520,
            490029339,
            3461569637779515,
            5191526
        ]  # 需要爬取的uidlist
        self.uidlist = list(set(self.uidlist))  # 去个重
        self.nonLotteryWords = ['分享视频', '分享动态']
        self.cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        self.fullcookie3 = gl.get_value('fullcookie3')
        self.ua3 = gl.get_value('ua3')
        self.fingerprint3 = gl.get_value('fingerprint3')
        self.csrf3 = gl.get_value('csrf3')
        self.uid3 = gl.get_value('uid3')
        self.username3 = gl.get_value('uname3')
        self.SpareTime = 86400 * 5  # 多少时间以前的就不获取别人的动态了
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
        self.manual_reply_judge = execjs.compile("""
        manual_reply_judge= function (dynamic_content) {
                //判断是否需要人工回复 返回true需要人工判断  返回null不需要人工判断
                //64和67用作判断是否能使用关键词回复
                let none_lottery_word1= /.*测试.{0,5}gua/gmi.test(dynamic_content)
                if (none_lottery_word1){
                                return true
                }
                dynamic_content = dynamic_content.replaceAll(/＠/gmi, '@')
                dynamic_content = dynamic_content.replaceAll(/@.{0,8} /gmi, '')
                dynamic_content = dynamic_content.replaceAll(/好友/gmi, '朋友')
                dynamic_content = dynamic_content.replaceAll(/伙伴/gmi, '朋友')
                dynamic_content = dynamic_content.replaceAll(/安利/gmi, '分享')
                dynamic_content = dynamic_content.replaceAll(/【关注】/gmi, '')
                dynamic_content = dynamic_content.replaceAll(/\?/gmi, '？')
                let manual_re1 = /.*评论.{0,20}告诉|.*有关的评论|.*告诉.{0,20}留言/gmi.test(dynamic_content)
                let manual_re2 = /.*评论.{0,20}理由|.*参与投稿.{0,30}有机会获得/gmi.test(dynamic_content)
                let manual_re3 = /.*评论.{0,10}对|.*造.{0,3}句子/gmi.test(dynamic_content)
                let manual_re4 = /.*猜赢|.*猜对|.*答对|.*猜到.{0,5}答案/gmi.test(dynamic_content)
                let manual_re5 = /.*说.{0,10}说|.*谈.{0,10}谈|.*夸.{0,10}夸|评论.{0,10}写.{0,10}写|.*写下.{0,5}假如.{0,5}是|.*讨论.{0,10}怎么.{0,10}？/gmi.test(dynamic_content)
                let manual_re7 = /.*最先猜中|.*带文案|.*许.{0,5}愿望/gmi.test(dynamic_content)
                let manual_re8 = /.*新衣回/gmi.test(dynamic_content)
                let manual_re9 = /.*留言.{0,10}建议|.*评论.{0,10}答|.*一句话证明|.*留言.{0,10}得分|.*有趣.{0,3}留言|.*有趣.{0,3}评论|.*留言.{0,3}晒出|.*评论.{0,3}晒出/gmi.test(dynamic_content)
                let manual_re11 = /.*评论.{0,10}祝福|.*评论.{0,10}意见|.*意见.{0,10}评论|.*留下.{0,10}意见|.*意见.{0,10}留下/gmi.test(dynamic_content)
                let manual_re12 = /.*评论.{0,10}讨论|.*话题.{0,10}讨论|.*参与.{0,5}讨论/gmi.test(dynamic_content)
                let manual_re14 = /.*评论.{0,10}说出/gmi.test(dynamic_content)
                let manual_re15 = /.*评论.{0,20}分享|.*评论.{0,20}互动((?!抽奖|,|，).)*$|.*评论.{0,20}提问|.*想问.{0,20}评论|.*想说.{0,20}评论|.*想问.{0,20}留言|.*想说.{0,20}留言/gmi.test(dynamic_content)
                let manual_re16 = /.*评论.{0,10}聊.{0,10}聊/gmi.test(dynamic_content)
                let manual_re17 = /.*评.{0,10}接力/gmi.test(dynamic_content)
                let manual_re18 = /.*聊.{0,10}聊/gmi.test(dynamic_content)
                let manual_re19 = /.*评论.{0,10}扣|.*评论.{0,5}说.{0,3}下/gmi.test(dynamic_content)
                let manual_re20 = /.*转发.{0,10}分享/gmi.test(dynamic_content)
                let manual_re21 = /.*评论.{0,10}告诉/gmi.test(dynamic_content)
                let manual_re22 = /.*评论.{0,10}唠.{0,10}唠/gmi.test(dynamic_content)
                let manual_re23 = /.*今日.{0,5}话题|.*参与.{0,5}话题|.*参与.{0,5}答题/gmi.test(dynamic_content)
                let manual_re24 = /.*说.*答案|.*评论.{0,15}答案/gmi.test(dynamic_content)
                let manual_re25 = /.*说出/gmi.test(dynamic_content)
                let manual_re26 = /.*为.{0,10}加油/gmi.test(dynamic_content)
                let manual_re27 = /.*评论.{0,10}话|.*你中意的|.*评.{0,10}你.{0,5}的|.*写上.{0,10}你.{0,5}的|.*写下.{0,10}你.{0,5}的/gmi.test(dynamic_content)
                let manual_re28 = /.*评论.{0,15}最想做7的事|.*评.{0,15}最喜欢|.*评.{0,15}最.{0,7}的事|.*最想定制的画面/gmi.test(dynamic_content)
                let manual_re29 = /.*分享.{0,20}经历|.*经历.{0,20}分享/gmi.test(dynamic_content)
                let manual_re30 = /.*分享.{0,20}心情/gmi.test(dynamic_content)
                let manual_re31 = /.*评论.{0,10}句/gmi.test(dynamic_content)
                let manual_re32 = /.*转关评下方视频/gmi.test(dynamic_content)
                let manual_re33 = /.*分享.{0,10}美好/gmi.test(dynamic_content)
                let manual_re34 = /.*视频.{0,10}弹幕/gmi.test(dynamic_content)
                let manual_re35 = /.*生日快乐/gmi.test(dynamic_content)
                let manual_re36 = /.*一句话形容/gmi.test(dynamic_content)
                let manual_re38 = /.*分享.{0,10}喜爱/gmi.test(dynamic_content)
                let manual_re39 = /.*分享((?!,|，).){0,10}最|.*评论((?!,|，).){0,10}最/gmi.test(dynamic_content)
                let manual_re40 = /.*带话题.{0,15}晒|.*带话题.{0,15}讨论/gmi.test(dynamic_content)
                let manual_re41 = /.*分享.{0,15}事/gmi.test(dynamic_content)
                let manual_re42 = /.*送出.{0,15}祝福/gmi.test(dynamic_content)
                let manual_re43 = /.*评论.{0,30}原因/gmi.test(dynamic_content)
                let manual_re47 = /.*答案.{0,10}参与/gmi.test(dynamic_content)
                let manual_re48 = /.*唠.{0,5}唠/gmi.test(dynamic_content)
                let manual_re49 = /.*分享一下/gmi.test(dynamic_content)
                let manual_re50 = /.*评论.{0,30}故事/gmi.test(dynamic_content)
                let manual_re51 = /.*告诉.{0,30}什么|.*告诉.{0,30}最/gmi.test(dynamic_content)
                let manual_re53 = /.*发布.{0,20}图.{0,5}动态/gmi.test(dynamic_content)
                let manual_re54 = /.*视频.{0,20}评论/gmi.test(dynamic_content)
                let manual_re55 = /.*复zhi|.*长按/gmi.test(dynamic_content)
                let manual_re56 = /.*多少.{0,10}合适/gmi.test(dynamic_content)
                let manual_re57 = /.*喜欢.{0,5}哪/gmi.test(dynamic_content)
                let manual_re58 = /.*多少.{0,15}？|.*多少.{0,15}\?|.*有没有.{0,15}？|.*有没有.{0,15}\?|.*是什么.{0,15}？|.*是什么.{0,15}\?/gmi.test(dynamic_content)
                let manual_re59 = /.*哪.{0,15}？|.*哪.{0,15}？|.*那些.{0,15}？|.*那些.{0,15}？/gmi.test(dynamic_content)
                let manual_re61 = /.*看.{0,10}猜/gmi.test(dynamic_content)
                let manual_re63 = /.*评论.{0,10}猜|.*评论.{0,15}预测/gmi.test(dynamic_content)
                let manual_re65 = /.*老规矩你们懂的/gmi.test(dynamic_content)
                let manual_re67 = /.*[评|带]((?!抽奖|,|，).){0,7}“|.*[评|带]((?!抽奖|,|，).){0,7}【|.*[评|带]((?!抽奖|,|，).){0,7}:|.*[评|带]((?!抽奖|,|，).){0,7}：|.*[评|带]((?!抽奖|,|，).){0,7}「|.*带关键词.{0,7}"|.*留言((?!抽奖|,|，).){0,7}“|.*对出.{0,10}下联.{0,5}横批|.*回答.{0,8}问题|.*留下.{0,10}祝福语|.*留下.{0,10}愿望|.*找到.{0,10}不同的.{0,10}留言|.*答案放在评论区|.*几.{0,5}呢？|.*有奖问答|.*想到.{0,19}关于.{0,20}告诉|.*麻烦大伙评论这个|留下.{0,7}的/gmi.test(dynamic_content)
                let manual_re76 = /.*留下((?!抽奖|,|，).){0,5}“|.*留下((?!抽奖|,|，).){0,5}【|.*留下((?!抽奖|,|，).){0,5}:|.*留下((?!抽奖|,|，).){0,5}：|.*留下((?!抽奖|,|，).){0,5}「/gmi.test(dynamic_content)
                let manual_re77 = /.*留言((?!抽奖|,|，).).{0,7}“|.*留言((?!抽奖|,|，).){0,7}【|.*留言((?!抽奖|,|，).){0,7}:|.*留言((?!抽奖|,|，).){0,7}：|.*留言((?!抽奖|,|，).){0,7}「/gmi.test(dynamic_content)
                let manual_re64 =  /和.{0,5}分享.{0,5}的|.*分享.{0,10}你的|.*正确回答|.*回答正确|.*评论.{0,10}计划|.*定.{0,10}目标.{0,5}？|.*定.{0,10}目标.{0,5}?|.*评论.{0,7}看的电影|.*如果.{0,20}觉得.{0,10}？|.*如果.{0,20}觉得.{0,10}\?|评论.{0,7}希望.{0,5}|.*竞猜[\s\S]{0,15}答|.*把喜欢的.{0,10}评论|.*评论.{0,5}解.{0,5}密|.*这款.{0,10}怎么.{0,3}？|.*最喜欢.{0,5}的.*为什么？|.*留下.{0,15}的.{0,5}疑问|.*写下.{0,10}的.{0,5}问题/gmi.test(dynamic_content)
                let manual_re6 = /.*@TA|.*@.{0,15}朋友|.*艾特|.*@.{0,3}你的|.*标记.{0,10}朋友|.*@{0,15}赞助商|.*发表你的新年愿望\+个人的昵称|.*抽奖规则请仔细看图片|.*带上用户名|.*此视频|.*视频评论区|.*活动详情请戳图片|.*@个人用户名|评论.{0,5}附带.{0,10}相关内容/gmi.test(dynamic_content)
                let manual_re62 = /.*评论.{0,10}#.*什么|.*转评.{0,3}#.*(?<=，)/gmi.test(dynamic_content)
                let manual_re68 = /.*将.{0,10}内容.{0,10}评|.*打几分？/gmi.test(dynamic_content)
                let manual_re70 = /.*会不会.{0,20}？|.*会不会.{0,20}\?|如何.{0,20}？|如何.{0,20}\?/gmi.test(dynamic_content)
                let manual_re71 = /.*猜.{0,10}猜|.*猜.{0,10}比分|.*猜中.{0,10}获得|.*猜中.{0,10}送出/gmi.test(dynamic_content)
                let manual_re72 = /.*生日|.*新年祝福/gmi.test(dynamic_content)
                let manual_re73 = /.*知道.{0,15}什么.{0,15}？|.*知道.{0,15}什么.{0,15}\?|.*用什么|.*评.{0,10}收.{0,5}什么.{0.7}\?|.*评.{0,10}收.{0,5}什么.{0,7}？/gmi.test(dynamic_content)
                let manual_re74 = /.*领.{0,10}红包.{0,5}大小|.*领.{0,10}多少.{0,10}红包|.*红包金额/gmi.test(dynamic_content)
                let manual_re75 = /.*本周话题|.*互动话题|.*互动留言|.*互动时间|.*征集.{0,10}名字|.*投票.{0,5}选.{0,10}最.{0,5}的|.*一人说一个谐音梗|帮.{0,5}想想.{0,5}怎么/gmi.test(dynamic_content)

                return manual_re1 || manual_re2 || manual_re3 || manual_re4 || manual_re5 || manual_re6 || manual_re7 || manual_re8 || manual_re9 ||
                    manual_re11 || manual_re12 || manual_re14 || manual_re15 || manual_re16 || manual_re17 || manual_re18 || manual_re19 || manual_re20 || manual_re21 || manual_re22 || manual_re23 || manual_re24 || manual_re25 ||
                    manual_re26 || manual_re27 || manual_re28 || manual_re29 || manual_re30 ||
                    manual_re31 || manual_re32 || manual_re33 || manual_re34 || manual_re35 ||
                    manual_re36 || manual_re38 || manual_re39 || manual_re40 ||
                    manual_re41 || manual_re42 || manual_re43 ||
                    manual_re47 || manual_re48 || manual_re49 || manual_re50 || manual_re51 ||
                    manual_re53 || manual_re54 || manual_re58 || manual_re59 || manual_re55 || manual_re56 ||
                    manual_re57 || manual_re61 || manual_re62 || manual_re63 || manual_re64 ||
                    manual_re65 || manual_re67 || manual_re68 || manual_re70 || manual_re71 || manual_re72 || manual_re73 ||
                    manual_re74 || manual_re75 || manual_re77 || manual_re77
            }

            """)

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

        def get_attention(cookie, ua):
            url = 'https://api.vc.bilibili.com/feed/v1/feed/get_attention_list'
            headers = {
                'cookie': cookie,
                'user-agent': ua
            }
            req = requests.get(url=url, headers=headers)
            return req.json().get('data').get('list')

        self.all_followed_uid = get_attention(self.cookie3, self.ua3)
        print(f'共{len(self.all_followed_uid)}个关注')
        # self.nlp = Bilibili_methods.paddlenlp.my_paddlenlp()
        os.system(f'cd "{root_dir}github/bili_upload" && git fetch --all && git reset --hard && git pull')

        self.last_order = []  # 上次查询过的记录
        self.recorded_dynamic_id = []
        self.BAPI = Bilibili_methods.all_methods.methods()
        self.lottery_dynamic_ids = []
        self.lottery_dynamic_detail_list = []
        self.useless_info = []

    def file_resolve(self, file_content):
        def is_valid_date(_str):
            '''判断是否是一个有效的日期字符串'''
            try:
                time.strptime(_str, "%Y-%m-%d")
                return True
            except:
                try:
                    time.strptime(_str, "%m-%d-%Y")
                    return True
                except:
                    return False

        now_date = datetime.datetime.now()
        file_split = file_content.split(',')
        file_split.reverse()
        for i in file_split:
            if is_valid_date(i):
                try:
                    lottery_update_date = datetime.datetime.strptime(i, '%Y-%m-%d')
                except:
                    lottery_update_date = datetime.datetime.strptime(i, "%m-%d-%Y")
                if (now_date - lottery_update_date).days >= 4:  # 多少天前的跳过
                    print(lottery_update_date)
                    break
            if i not in self.recorded_dynamic_id and i != '' and i != ' ' and str.isdigit(i):
                self.recorded_dynamic_id.append(i.strip())

    def log_writer(self, filename, content_list: list, write_method):
        try:
            with open(f'log/{filename}', write_method, encoding='utf-8') as f:
                for _ in content_list:
                    f.writelines(f'{_}\n')
        except:
            with open(f'log/{filename}', 'w', encoding='utf-8') as f:
                for _ in content_list:
                    f.writelines(f'{_}\n')

    def judge_lottery(self, dynamic_id):
        try:
            dynamic_detail = self.BAPI.get_dynamic_detail(dynamic_id)
        except:
            time.sleep(60)
            traceback.print_exc()
            return self.judge_lottery(dynamic_id)
        suffix = ''
        if dynamic_detail:
            dynamic_content = dynamic_detail['dynamic_content']
            author_name = dynamic_detail['author_name']
            pub_time = dynamic_detail['pub_time']
            comment_count = dynamic_detail['comment_count']
            forward_count = dynamic_detail['forward_count']
            official_verify_type = dynamic_detail['official_verify_type']
            author_uid = dynamic_detail['author_uid']
            rid = dynamic_detail['rid']
            _type = dynamic_detail['type']
            if dynamic_content != '':
                # deadline = self.nlp.information_extraction(dynamic_content, ['开奖日期'])['开奖日期']
                deadline = None
            else:
                print(f'https://t.bilibili.com/{dynamic_id}')
                print('动态内容为空')
                deadline = None
            premsg = self.BAPI.pre_msg_processing(dynamic_content)
            if comment_count > 50 or str(dynamic_detail.get('type')) == '8':
                dynamic_content += self.BAPI.get_topcomment(str(dynamic_id), str(rid), str(0), _type, author_uid)
            if author_uid in self.all_followed_uid:
                suffix = 'followed_uid'
            ret_url = f'https://t.bilibili.com/{dynamic_id}'
            if self.BAPI.zhuanfapanduan(dynamic_content):
                ret_url += '?tab=2'
            Manual_judge = ''
            if self.manual_reply_judge.call("manual_reply_judge", dynamic_content):
                Manual_judge = '人工判断'
            format_list = [ret_url, author_name, str(official_verify_type), str(pub_time), repr(dynamic_content),
                           str(comment_count), str(forward_count), suffix, premsg, Manual_judge, str(deadline)]
            format_str = '\t'.join(format_list)
            if re.match(r'.*//@.*', str(dynamic_content), re.DOTALL) != None:
                dynamic_content = re.findall(r'(.*?)//@', dynamic_content, re.DOTALL)[0]
            if self.BAPI.daily_choujiangxinxipanduan(dynamic_content):
                self.useless_info.append(format_str)
                return

            self.lottery_dynamic_ids.append(ret_url)

            self.lottery_dynamic_detail_list.append(format_str)

    def get_reqtext(self, hostuid, offset):
        '''
        获取动态空间的response
        :param hostuid:要访问的uid
        :param offset:
        :return:reqtext
        '''
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
        if req.json().get('code') == -412:
            print("get_reqtext\t" + req.text + "\t休息10分钟" + f"\t{time.asctime()}")
            time.sleep(600)
            return self.get_reqtext(hostuid, offset)
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
            return 404
        cards_json = req_dict.get('data').get('cards')
        dynamic_id_list = []
        if cards_json:
            for card_dict in cards_json:
                dynamic_id = card_dict.get('desc').get('pre_dy_id_str')  # 判断中转动态id是否重复；非最原始动态id 类型为string
                try:
                    dynamic_repost_content = json.loads(card_dict.get('card')).get('item').get('content')
                except:
                    dynamic_repost_content = None
                print(
                    f"当前动态： https://t.bilibili.com/{card_dict.get('desc').get('dynamic_id')}\t{time.asctime()}\n转发评论内容：{dynamic_repost_content}")
                if (dynamic_repost_content in self.nonLotteryWords):
                    print('转发评论内容为非抽奖词，跳过')
                    continue
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
                dynamic_time = card_dict.get('desc').get('timestamp')  # 判断是否超时，超时直接退出
                if time.time() - dynamic_time >= self.SpareTime:
                    print('遇到超时动态')
                    return 0
                for _ in self.card_detail(card_dict):
                    if _:
                        print(f'添加进记录：{_}')
                        dynamic_id_list.append(_)  # 间接和原始的动态id全部记录
        else:
            print(space_reqtext)
            print('cards_json为None')
        self.recorded_dynamic_id.extend(dynamic_id_list)

        if not dynamic_id_list:
            time.sleep(2)
        return 0

    def card_detail(self, cards_json):
        """
        返回间接动态和原始动态的动态id
        :param cards_json:
        :return:
        """
        card_json = json.loads(cards_json.get('card'))
        # print(card_json)  # 测试点
        try:
            pre_dy_id = str(card_json.get('item').get('pre_dy_id'))
        except:
            pre_dy_id = None
        try:
            orig_dy_id = str(card_json.get('item').get('orig_dy_id'))
        except:
            orig_dy_id = None
        if pre_dy_id == orig_dy_id:
            pre_dy_id = None
        return [orig_dy_id, pre_dy_id]

    def get_offset(slef, space_reqtext):
        req_dict = json.loads(space_reqtext)
        return req_dict.get('data').get('next_offset')

    def get_space_dynmaic_time(self, space_reqtext):  # 返回list
        req_dict = json.loads(space_reqtext)
        cards_json = req_dict.get('data').get('cards')
        dynamic_time_list = []
        if cards_json:
            for card_dict in cards_json:
                dynamic_time = card_dict.get('desc').get('timestamp')
                dynamic_time_list.append(dynamic_time)
        return dynamic_time_list

    def get_space_dynamic_id_list(self, space_reqtext: str) -> list[str]:
        ret_list = []
        try:
            space_req_dict = json.loads(space_reqtext)
            for dynamic_card in space_req_dict.get('data').get('cards'):
                ret_list.append(str(dynamic_card.get('desc').get('dynamic_id_str')))
            return ret_list
        except:
            print(space_reqtext)
            traceback.print_exc()
            return ret_list

    def get_user_space_dynamic_id(self):
        '''
        根据时间和获取过的动态来判断是否结束爬取别人的空间主页
        :return:
        '''
        sleeptime = 5
        n = 0
        for uid in self.uidlist:
            print(
                f'当前UID：https://space.bilibili.com/{uid}/dynamic\t进度：【{self.uidlist.index(uid) + 1}/{len(self.uidlist)}】')
            first_get_dynamic_falg = True
            offset = 0
            while 1:
                dyreqtext = self.get_reqtext(uid, offset)
                try:
                    if json.loads(dyreqtext).get('data').get('has_more') != 1:
                        print(f'当前用户 https://space.bilibili.com/{uid}/dynamic 无更多动态')
                        break
                except:
                    traceback.print_exc()
                    print(f'Error: has_more获取失败\n{dyreqtext}')
                repost_dynamic_id_list = self.get_space_dynamic_id_list(dyreqtext)  # 脚本们转发生成的动态id
                if first_get_dynamic_falg:
                    self._最后一次获取过动态的b站用户.update({uid: repost_dynamic_id_list})
                    first_get_dynamic_falg = False
                time.sleep(sleeptime)
                n += 1
                if self.get_space_detail(dyreqtext) != 0:
                    offset = 0
                    continue
                offset = self.get_offset(dyreqtext)
                timelist = self.get_space_dynmaic_time(dyreqtext)
                time.sleep(5)
                if not timelist:
                    continue
                if time.time() - timelist[-1] >= self.SpareTime:
                    if uid == self.uidlist[-1]:
                        print('最后一个uid获取结束')
                        break
                    else:
                        print('超时动态，进入下一个uid')
                        time.sleep(60)
                        break
                if self._获取过动态的b站用户.get(str(uid)):
                    print(self._获取过动态的b站用户.get(str(uid)))
                    print(repost_dynamic_id_list)
                    if set(self._获取过动态的b站用户.get(str(uid))) & set(repost_dynamic_id_list):
                        print('遇到获取过动态的b站用户，进入下一个uid')
                        time.sleep(60)
                        break
                if n % 50 == 0:
                    print('获取了50次，休息个10s')
                    time.sleep(10)

    def main(self):
        with open('get_dyid.txt', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                for _i in i.split(','):
                    self.last_order.append(_i.strip())
        self.last_order = list(set(self.last_order))
        if len(self.last_order) > 10000000:
            self.last_order = self.last_order[-10000000:]  # 总共容纳10000000条记录，占不了多少空间的
            # self.last_order.sort()  # 排序之前裁剪掉，去掉那些没动静的号的动态id

        path = root_dir + "github/bili_upload"
        datanames = os.listdir(path)
        path_dir_name = []
        for i in datanames:
            if str.isdigit(i):
                path_dir_name.append(i)

        effective_files_content_list = []

        for i in path_dir_name:
            with open(root_dir + 'github/bili_upload/' + i + '/dyid.txt', 'r', encoding='utf-8') as f:
                effective_files_content_list.append(''.join(f.readlines()))
        print(f'共获取{len(path_dir_name)}个文件')
        for i in effective_files_content_list:
            self.file_resolve(i)  # 记录动态id

        self.get_user_space_dynamic_id()  # 获取uidlist的空间动态
        write_in_list = list(set(self.recorded_dynamic_id))
        write_in_list.sort()
        for i in self.last_order:
            if i in write_in_list:
                write_in_list.remove(i)
        print(f'共获取到{len(write_in_list)}个动态id')

        for i in write_in_list:
            if i in self.last_order:
                continue
            else:
                self.last_order.append(i)
            print(f'当前进度：【{write_in_list.index(i) + 1}/{len(write_in_list)}】\thttps://t.bilibili.com/{i}')
            self.judge_lottery(i)
            time.sleep(7)
        self.log_writer('过滤抽奖信息.csv', self.lottery_dynamic_detail_list, 'w')
        self.log_writer('无用信息(需要检查).csv', self.useless_info, 'w')
        self.log_writer('all_log/所有抽奖信息记录.csv', self.lottery_dynamic_detail_list, 'a+')
        self.log_writer('all_log/所有无用信息.csv', self.useless_info, 'a+')

        # self.last_order.sort()//不排序直接放进去
        with open('get_dyid.txt', 'w', encoding='utf-8') as f:
            f.writelines(','.join(self.last_order))

        with open('获取过动态的b站用户.json', 'w') as f:
            json.dump(self._最后一次获取过动态的b站用户, f, indent=4)
        print('任务完成')


if __name__ == '__main__':
    # time.sleep(60 * 60 * 3)
    a = renew()
    a.main()
