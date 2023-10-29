import numpy
import Bilibili_methods.all_methods
import copy
import json
import random
import re
import time
import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds

comment_fail = list()



BAPI = Bilibili_methods.all_methods.methods()


class re_comment:
    def __init__(self):
        self.pinglunzhuanbiancishu = 5
        self.replycontent = ['[吃瓜]', 'doge']
        self.sleeptime = numpy.linspace(3, 10, 500)
        self.re_comment_dict = dict()
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

    def get_dtl(self):
        with open('comment_log.csv', 'r', encoding='utf-8') as f:
            index = 1
            for i in f:
                user_name = i.split('\t')[1]
                dynamic_id_str = i.split('\t')[2]
                repcontent = i.split('\t')[4]
                url = i.split('\t')[3]
                self.re_comment_dict.update({index: [user_name, dynamic_id_str, repcontent, url]})
                index += 1

    def re_comment(self):
        self.get_dtl()
        for i in range(1, len(self.re_comment_dict) + 1):
            de = self.re_comment_dict.get(i)
            print(de)
            user_name = de[0]
            dynamic_id_str = de[1]
            repcontent = de[2]
            self.user_name_choose(user_name, dynamic_id_str, repcontent)
            time.sleep(3 * random.choice(self.sleeptime))
        with open('comment_log.csv', 'w', encoding='utf-8') as f:
            for i in comment_fail:
                print(i)
                f.writelines(i)

    def user_name_choose(self, user_name, dynamic_id, content):
        cookie1 = gl.get_value('cookie1')  # 星瞳
        fullcookie1 = gl.get_value('fullcookie1')
        ua1 = gl.get_value('ua1')
        fingerprint1 = gl.get_value('fingerprint1')
        csrf1 = gl.get_value('csrf1')
        uid1 = gl.get_value('uid1')
        username1 = gl.get_value('uname1')
        cookie2 = gl.get_value('cookie2')  # 保加利亚
        fullcookie2 = gl.get_value('fullcookie2')
        ua2 = gl.get_value('ua2')
        fingerprint2 = gl.get_value('fingerprint2')
        csrf2 = gl.get_value('csrf2')
        uid2 = gl.get_value('uid2')
        username2 = gl.get_value('uname2')
        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        fullcookie3 = gl.get_value('fullcookie3')
        ua3 = gl.get_value('ua3')
        fingerprint3 = gl.get_value('fingerprint3')
        csrf3 = gl.get_value('csrf3')
        uid3 = gl.get_value('uid3')
        username3 = gl.get_value('uname3')
        share_cookie3 = gl.get_value('share_cookie3')
        cookie4 = gl.get_value('cookie4')  # 墨色
        fullcookie4 = gl.get_value('fullcookie4')
        ua4 = gl.get_value('ua4')
        fingerprint4 = gl.get_value('fingerprint4')
        csrf4 = gl.get_value('csrf4')
        uid4 = gl.get_value('uid4')
        username4 = gl.get_value('uname4')
        if user_name == username1:
            self._doit(dynamic_id, content, cookie1, ua1, csrf1, username1)
        elif user_name == username2:
            self._doit(dynamic_id, content, cookie2, ua2, csrf2, username2)
        elif user_name == username3:
            self._doit(dynamic_id, content, cookie3, ua3, csrf3, username3)
        elif user_name == username4:
            self._doit(dynamic_id, content, cookie4, ua4, csrf4, username4)

    def get_pinglunreq(self, dynamic_id, rid, pn, _type):
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
            'user-agent': fakeuseragent}
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(
            oid) + '&mode=2&plat=1&_=' + str(time.time())
        pinglundata = {
            'jsonp': 'jsonp',
            'next': pn,
            'type': ctype,
            'oid': oid,
            'mode': 2,
            'plat': 1,
            '_': time.time()
        }
        try:
            pinglunreq = requests.request("GET", url=pinglunurl, data=pinglundata, headers=pinglunheader)
        except Exception as e:
            print(e)
            print(self.timeshift(int(time.time())))
            # time.sleep(eval(input('输入等待时间')))
            time.sleep(3)
            self.get_pinglunreq(dynamic_id, rid, pn, _type)
            return None
        return pinglunreq.text

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def panduanbiaoqingbao(self, emo):
        hasemo = ['12周年', '藏狐', 'doge', '微笑', 'OK', '星星眼', '妙啊', '辣眼睛', '吃瓜', '滑稽', '喜欢', '嘟嘟', '给心心', '笑哭', '脱单doge',
                  '嗑瓜子', '调皮', '歪嘴', '打call', '呲牙', '酸了', '哦呼', '嫌弃', '大哭', '害羞', '疑惑', '喜极而泣', '奸笑', '笑', '偷笑', '点赞',
                  '无语',
                  '惊喜', '大笑', '抠鼻', '呆', '囧', '阴险', '捂脸', '惊讶', '鼓掌', '尴尬', '灵魂出窍', '委屈', '傲娇', '疼', '冷', '生病', '吓',
                  '吐',
                  '撇嘴', '难过', '墨镜', '奋斗', '哈欠', '翻白眼', '再见', '思考', '嘘声', '捂眼', '抓狂', '生气', '口罩', '牛年', '2021', '水稻',
                  '福到了',
                  '鸡腿', '雪花', '视频卫星', '拥抱', '支持', '保佑', '响指', '抱拳', '加油', '胜利', '锦鲤', '爱心', '干杯', '跪了', '跪了', '怪我咯',
                  '黑洞',
                  '老鼠', '来古-沉思', '来古-呆滞', '来古-疑问', '来古-震撼', '来古-注意', '哭泣', '原神_嗯', '原神_哼', '原神_哇', '高兴', '气愤', '耍帅',
                  '亲亲',
                  '羞羞', '狗子', '哈哈', '原神_欸嘿', '原神_喝茶', '原神_生气', '热词系列_河南加油', '热词系列_豫你一起', '热词系列_仙人指路', '热词系列_饮茶先啦',
                  '热词系列_知识增加', '热词系列_再来亿遍', '热词系列_好耶', '热词系列_你币有了', '热词系列_吹爆', '热词系列_妙啊', '热词系列_你细品', '热词系列_咕咕',
                  '热词系列_标准结局', '热词系列_张三', '热词系列_害', '热词系列_问号', '热词系列_奥力给', '热词系列_猛男必看', '热词系列_有内味了', '热词系列_我裂开了',
                  '热词系列_我哭了', '热词系列_高产', '热词系列_不愧是你', '热词系列_真香', '热词系列_我全都要', '热词系列_神仙UP', '热词系列_锤', '热词系列_秀',
                  '热词系列_爷关更',
                  '热词系列_我酸了', '热词系列_大师球', '热词系列_完结撒花', '热词系列_我太南了', '热词系列_镇站之宝', '热词系列_有生之年', '热词系列_知识盲区', '热词系列_“狼火”',
                  '热词系列_你可真星', 'tv_白眼', 'tv_doge', 'tv_坏笑', 'tv_难过', 'tv_生气', 'tv_委屈', 'tv_斜眼笑', 'tv_呆', 'tv_发怒',
                  'tv_惊吓',
                  'tv_笑哭', 'tv_亲亲', 'tv_调皮', 'tv_抠鼻', 'tv_鼓掌', 'tv_大哭', 'tv_疑问', 'tv_微笑', 'tv_思考', 'tv_呕吐', 'tv_晕',
                  'tv_点赞',
                  'tv_害羞', 'tv_睡着', 'tv_色', 'tv_吐血', 'tv_无奈', 'tv_再见', 'tv_流汗', 'tv_偷笑', 'tv_发财', 'tv_可爱', 'tv_馋',
                  'tv_腼腆',
                  'tv_鄙视', 'tv_闭嘴', 'tv_打脸', 'tv_困', 'tv_黑人问号', 'tv_抓狂', 'tv_生病', 'tv_流鼻血', 'tv_尴尬', 'tv_大佬', 'tv_流泪',
                  'tv_冷漠', 'tv_皱眉', 'tv_鬼脸', 'tv_调侃', 'tv_目瞪口呆', '坎公骑冠剑_吃鸡', '坎公骑冠剑_钻石', '坎公骑冠剑_无语', '热词系列_不孤鸟',
                  '热词系列_对象',
                  '保卫萝卜_问号', '保卫萝卜_哇', '保卫萝卜_哭哭', '保卫萝卜_笔芯', '保卫萝卜_白眼',
                  '热词系列_多谢款待', '脸红', '热词系列_破防了', '热词系列_燃起来了'
            , '热词系列_住在B站', '热词系列_B站有房', '热词系列_365', '热词系列_最美的夜', '热词系列_干杯', '热词系列_2022新年', '热词系列_奇幻时空', '热词系列_魔幻时空'
            , '虎年', '冰墩墩', '雪容融', '热词系列_红红火火', '小电视_笑', '小电视_发愁', '小电视_赞', '小电视_差评', '小电视_嘟嘴', '小电视_汗', '小电视_害羞',
                  '小电视_吃惊', '小电视_哭泣', '小电视_太太喜欢', '小电视_好怒啊', '小电视_困惑', '小电视_我好兴奋', '小电视_思索', '小电视_无语'

                  ]
        tihuanbiaoqing = []
        for biaoqing in emo:
            if (biaoqing not in hasemo):
                tihuanbiaoqing.append(biaoqing)
        return tihuanbiaoqing

    def huifuneirong(self, content, dynamic_id, rid, _type):  # 回复内容的判断
        msg = ''
        nomsg = '@盛百凡'
        premsg = ''
        topobj_5 = re.match('.*@上同学.*', content, re.DOTALL)
        topobj_4 = re.match('.*@你的好友.*', content, re.DOTALL)
        topobj_3 = re.match('.*@一位好友.*', content, re.DOTALL)
        topobj_2 = re.match('.*艾特.*', content, re.DOTALL)
        topobj_1 = re.match('.*@你想祝福的人.*', content, re.DOTALL)
        topobj0 = re.match('.*@1位胖友.*', content, re.DOTALL)
        topobj1 = re.match('.*圈1位你的伙伴.*', content, re.DOTALL)
        topobj2 = re.match('.*带tag#.*#.*', content, re.DOTALL)
        topobj3 = re.match('.*带话题#.*#.*', content, re.DOTALL)
        topobj4 = re.match('.*带上tag#.*#.*', content, re.DOTALL)
        topobj5 = re.match('.*带#.*#.*', content, re.DOTALL)
        if topobj_5 != None:
            premsg = '@_大锦鲤_  '
        if topobj_4 != None:
            premsg = '@_大锦鲤_  '
        if topobj_3 != None:
            premsg = '@_大锦鲤_  '
        if topobj_2 != None:
            premsg = '@_大锦鲤_  '
        if topobj_1 != None:
            premsg = '@_大锦鲤_  '
        if topobj0 != None:
            premsg = '@_大锦鲤_  '
        if topobj1 != None:
            premsg = '@_大锦鲤_  '
        if topobj2 != None:
            msg = re.findall(r'带tag#(.*?)#', content, re.DOTALL)
            premsg = '#' + str(msg[0]) + '#'
        if topobj3 != None:
            msg = re.findall(r'带话题#(.*?)#', content, re.DOTALL)
            premsg = '#' + str(msg[0]) + '#'
        if topobj4 != None:
            msg = re.findall(r'带上tag#(.*?)#', content, re.DOTALL)
            premsg = '#' + str(msg[0]) + '#'
        if topobj5 != None:
            msg = re.findall(r'带#(.*?)#', content, re.DOTALL)
            if msg == None or msg == [''] or msg == '' or msg == ' ':
                premsg = ''
            else:
                premsg = '#' + str(msg[0]) + '#'
        pn = 0
        pinglun_req = self.get_pinglunreq(str(dynamic_id), str(rid), pn, str(_type))
        pinglun_dict = json.loads(pinglun_req)
        try:
            pinglun_count = pinglun_dict.get('data').get('cursor').get('prev')
        except:
            print('获取评论失败')
            print(pinglun_req)
            pinglun_count = 0
            while 1:
                try:
                    time.sleep(eval(input('输入等待时间')))
                    break
                except:
                    continue
            return self.huifuneirong(content, dynamic_id, rid, _type)
        if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
            if pinglun_count != 0:
                i = 0
                while True:
                    if i >= 5:
                        break
                    i += 1
                    pnlist = list(range(pinglun_count - 30, pinglun_count - 5))
                    if pnlist == []:
                        print('动态下评论过少，评论获取失败')
                        break
                    pn = random.choice(pnlist)
                    pinglun_req = self.get_pinglunreq(dynamic_id, rid, pn, _type)
                    pinglun_dict = json.loads(pinglun_req)
                    reply_content = []
                    if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
                        pinglun_list = pinglun_dict.get('data').get('replies')
                        for reply in pinglun_list:
                            reply_content.append(reply.get('content').get('message'))
                    else:
                        print('获取评论失败')
                        break
                    if reply_content != []:
                        for i in range(self.pinglunzhuanbiancishu):
                            while 1:
                                msg = ''.join(random.choice(reply_content))
                                sums = 0
                                for wordcount in reply_content:
                                    sums += len(wordcount)
                                if len(msg) <= int(sums / len(reply_content)) + 10:
                                    break
                            biaoqingbao = re.findall('(?<=\[)(.*?)(?=\])', msg, re.DOTALL)
                            changyongemo = ['doge', '脱单doge', '妙啊', '吃瓜', 'tv_doge', '藏狐', '原神_哇', '原神_哼',
                                            '原神_嗯',
                                            '原神_欸嘿', '原神_喝茶']
                            if biaoqingbao != []:
                                tihuanbiaoqing = self.panduanbiaoqingbao(biaoqingbao)
                                if tihuanbiaoqing != []:
                                    for noemo in tihuanbiaoqing:
                                        msg = msg.replace(noemo, random.choice(changyongemo))
                            # msg += '[' + random.choice(changyongemo) + ']'#添加随机表情
                            if nomsg in msg:
                                continue
                            if '@' in msg:
                                msg = re.sub(r'@(.*?) ', '@碧诗 ', msg, re.S)
                            if premsg != '':
                                if premsg in msg:
                                    print('抄的评论：' + msg)
                                    return msg
                                else:
                                    print('抄的评论：' + premsg)
                                    return premsg
                            print('抄的评论：' + msg)
                            return msg
                    if reply_content == []:
                        print('获取评论为空\t尝试重新获取\t动态类型：' + str(_type))
                    time.sleep(random.choice(self.sleeptime))
                    if i >= 5:
                        break
        else:
            print('抄作业失败，启用脚本内置回复')
            mobj_6 = re.match('.*七夕.*', content, re.DOTALL)
            mobj_5 = re.match('.*许愿格式：有趣的愿望+愿望实现城市！.*', content, re.DOTALL)
            mobj_4 = re.match('.*带话题 #.*#.*', content, re.DOTALL)
            mobj_2 = re.match('.*带话题  #.*#.*', content, re.DOTALL)
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
                msg = '中个大奖 上海'
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
        msg = random.choice(self.replycontent)
        return msg

    def _doit(self, dynamic_id, msg, cookie, ua, csrf, username):
        msg = eval(msg).strip()
        url = 'https://t.bilibili.com/{}'.format(dynamic_id)
        print('原回复内容： {}'.format(msg))
        dyresponse = BAPI.get_dynamic_detail(dynamic_id, cookie, ua)
        time.sleep(random.choice(self.sleeptime))
        rid = dyresponse.get('rid')
        _type = dyresponse.get('type')
        relation = dyresponse.get('relation')
        thumbstatus = dyresponse.get('is_liked')
        msg = self.huifuneirong('', dynamic_id, rid, _type)
        print('现回复内容： {}'.format(msg))
        print('链接： {}'.format(url))
        if dyresponse:
            time.sleep(random.choice(self.sleeptime))
            rid = dyresponse.get('rid')
            _type = dyresponse.get('type')
            print('\n')
            time.sleep(1)
            BAPI.comment(str(dynamic_id), msg, str(_type), str(rid), cookie, ua, csrf, username)
        else:
            print('动态获取失败')


if __name__ == '__main__':
    rep = re_comment()
    rep.re_comment()
