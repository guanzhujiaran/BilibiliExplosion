# -*- coding:utf- 8 -*-
import json
import random
import re
import time
import requests
import numpy
from lxml import etree
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl


class mycls:
    def __init__(self):
        self.cvdict = {}
        self.sleeptime = numpy.linspace(2, 4, 500, endpoint=True)
        self.yunxingshijian = 0.25 * 3600
        self.urlcount = 0
        self.changefail = []
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

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def get_cv_info(self, uid, csrf, cookie, ua, msglist):
        f = open('专栏抽奖.csv', 'w', encoding='utf-8')
        url = 'https://api.bilibili.com/x/space/article?mid=73773270&pn=1&ps=12&sort=publish_time&jsonp=jsonp'
        headers = {
            'user-agent': 'Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)'
        }
        req = requests.get(url=url, headers=headers)
        time.sleep(1)
        articles = req.json().get('data').get('articles')
        mydict = {}
        index = 1
        for article in articles:
            title = article.get('title')
            cvid = article.get('id')
            mydict.update({index: {'title': title, 'id': cvid}})
            index += 1
        for key in mydict.keys():
            print(key, mydict[key])
        while 1:
            try:
                returnnum = int(input('输入选取专栏数量：'))
                if isinstance(returnnum, int):
                    break
            except:
                returnnum = 1
                continue
        for i in range(1, returnnum + 1):
            self.cvdict.update({i: mydict[i]})
        print('选取专栏抽奖内容：')
        for key in self.cvdict.keys():
            prizedict = self.create_prizedict(mydict.get(key).get('id'))
            for j, k in prizedict.items():
                print(j, k)
            for prizename in prizedict.keys():
                print(prizename)
                f.writelines(prizename)
                for shorturl in prizedict.get(prizename):
                    print('短url：\t{surl}'.format(surl=shorturl))
                    if not 'http' in shorturl:
                        print('shorturl分割出错')
                        print(shorturl)
                        time.sleep(3)
                        continue
                    f.writelines('\t' + shorturl)
                f.writelines('\n')
            f.close()
            print('抽奖文件已写好，请检查')
            input('按任意键继续...')
            prizedict_new = {}
            myindex = 1
            with open('进行专栏抽奖.csv', 'r', encoding='utf-8') as q:
                for line in q:
                    pname = line.strip().split('\t')[0]
                    pu = []
                    for u in line.strip().split('\t')[1:]:
                        pu.append(u)
                        self.urlcount += 1
                    prizedict_new.update({myindex: {pname: pu}})
                    myindex += 1
            print('此专栏共有{c}条抽奖'.format(c=self.urlcount))
            for p_index in prizedict_new:
                for prizename in prizedict_new.get(p_index).keys():
                    print(prizename)
                    print(prizedict_new.get(p_index).get(prizename))
                    for shorturl in prizedict_new.get(p_index).get(prizename):
                        print('短url：\t{surl}'.format(surl=shorturl))
                        if not 'http' in shorturl:
                            print('shorturl分割出错')
                            print(shorturl)
                            time.sleep(3)
                            continue
                        dyid = self.revertShortLink(shorturl)
                        if dyid:
                            time.sleep(random.choice(numpy.linspace(3, 5, 500, endpoint=True)))
                            self.start_lottery(dyid, uid, csrf, cookie, ua, msglist)
                        else:
                            self.changefail.append([prizename, shorturl])

    def start_lottery(self, dynamicid, uid, csrf, cookie, useragent, msglist):
        longsleeptime = numpy.linspace(0.75 * self.yunxingshijian / self.urlcount,
                                       1.25 * self.yunxingshijian / self.urlcount, 500, endpoint=True)
        dyresponse = self.get_dynamic_detail(dynamicid, cookie, useragent)
        time.sleep(1)
        url = 'https://t.bilibili.com/{dyid}'.format(dyid=dynamicid)
        if dyresponse:
            time.sleep(random.choice(self.sleeptime))
            rid = dyresponse.get('rid')
            type = dyresponse.get('type')
            relation = dyresponse.get('relation')
            thumbstatus = dyresponse.get('is_liked')
            if relation != 1:
                print('未关注\n')
                weiguanzhu.append(url)
            else:
                print('已经关注了\n')
            if thumbstatus == 1:
                print('遇到点过赞的动态\thttps://t.bilibili.com/{dyid}'.format(dyid=dynamicid))
                time.sleep(random.choice(self.sleeptime))
                dianguozandedongtai.append(url)
                # return 0
            if msglist == ():
                pinglunmsg = self.huifuneirong('dycontent', dynamicid, rid, type)
            else:
                pinglunmsg = random.choice(msglist[0])
            print(url, type, rid, pinglunmsg)
            print('\n')
            if not isinstance(pinglunmsg, str):
                print('回复内容出错，请检查')
                exit(-1)
            print('评论内容：{m}'.format(m=pinglunmsg))
            if str(type) == '2' or str(type) == '4' or str(type) == '8':
                self.repost(dynamicid, '转发动态', cookie, useragent, uid, csrf)
            else:
                self.repost(dynamicid, pinglunmsg, cookie, useragent, uid, csrf)
            time.sleep(1)
            self.comment(str(dynamicid), pinglunmsg, str(type), str(rid), cookie, useragent, csrf)
            time.sleep(random.choice(self.sleeptime))
            self.thumb(dynamicid, cookie, useragent, uid, csrf)
            time.sleep(random.choice(self.sleeptime))
        else:
            print('动态获取错误：')
            print(url)
        stime=random.choice(longsleeptime)
        print(self.timeshift(time.time()))
        print('休息时间：{}秒'.format(stime))
        time.sleep(stime)

    def comment(self, dy, msg, _type, rid, cookie, useragent, csrf):  # 发送评论
        if len(rid) == len(dy):
            oid = dy
        else:
            oid = rid
        commentheader = {
            'authority': 'api.bilibili.com',
            'method': 'POST',
            'path': '/x/v2/reply/add',
            'scheme': 'https',
            'accept': 'application / json, text / javascript, * / *; q = 0.01',
            'cookie': cookie,
            'user-agent': useragent
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
        reqcomment = requests.request('POST', url=commenturl, data=commentdata, headers=commentheader)
        comment_dict = json.loads(reqcomment.text)
        try:
            commentresult = comment_dict.get('data').get('success_toast')
        except:
            commentresult = None
            url = 'https://t.bilibili.com/' + str(dy)
            pinglunshibai.append(url)
            print(reqcomment.text)
        time.sleep(random.choice(self.sleeptime))

        ###########################
        # try:
        #     commentrpid = comment_dict.get('data').get('rpid')
        # except:
        #     commentrpid = None
        # if commentrpid == None:
        #     print('评论点赞失败\t\t\t原因：rpid获取失败')
        # else:
        #     print('获取rpid=' + str(commentrpid))
        #     pinglundianzanurl = 'https://api.bilibili.com/x/v2/reply/action'
        #     pinglundianzanheaders = {
        #         'authority': 'api.bilibili.com',
        #         'method': 'POST',
        #         'cookie': cookie,
        #         'user-agent': useragent
        #     }
        #     pinglundianzandata = {'oid': oid,
        #                           'type': ctype,
        #                           'rpid': commentrpid,
        #                           'action': '1',
        #                           'ordering': 'time',
        #                           'jsonp': 'jsonp',
        #                           'csrf': csrf
        #                           }
        #     pinglundianzanreq = requests.request('POST', url=pinglundianzanurl, data=pinglundianzandata,
        #                                          headers=pinglundianzanheaders)
        #     pinglundianzan_dict = json.loads(pinglundianzanreq.text)
        #     dianzancode = pinglundianzan_dict.get('code')
        #     if dianzancode == 0:
        #         print('评论点赞成功')
        #     else:
        #         print('评论点赞失败\t\t\t原因：')
        #         print(pinglundianzan_dict)
        ################################################
        if commentresult != "发送成功":
            cuowuid = 'https://t.bilibili.com/' + str(dy)
            pinglunshibai.append(cuowuid)
            print('评论失败\n' + str(commentresult) + '： https://t.bilibili.com/' + str(dy))
            print('oid：' + str(oid))
            print('rid：' + str(rid))
            print('dynamic_id：' + str(dy))
            message = comment_dict.get('message')
            print(message)
            print(self.timeshift(int(time.time())))
            time.sleep(eval(input('输入等待时间')))

        print('评论动态结果：' + str(commentresult) + '；评论类型：' + str(ctype))

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
                  "user-agent": useragent
                  }
        reposturl = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/reply'
        try:
            reqrepost = requests.request('POST', reposturl, headers=header, data=repostdata)
        except Exception as e:
            print(e)
            print(self.timeshift(int(time.time())))
            time.sleep(eval(input('输入等待时间')))
            self.repost(dy, '', cookie, useragent, uid, csrf)
            return 0
        try:
            repostresult = json.loads(reqrepost.text)
        except:
            repostresult = {'data': {'errmsg': '转发失败'}}
        print('转发动态结果：' + str(repostresult.get('data').get('errmsg')))
        if repostresult.get('data').get('errmsg') == None:
            lianjie = 'https://t.bilibili.com/' + str(dy)
            zhuanfashibai.append(lianjie)

    def thumb(self, dynamic_ID, cookie, useragent, uid, csrf):  # 为动态点赞标记
        thumbheader = {
            'authority': 'api.vc.bilibili.com',
            'method': 'POST',
            'path': '/ dynamic_like / v1 / dynamic_like / thumb',
            'scheme': 'https',
            'cookie': cookie,
            'user-agent': useragent
        }
        thumbdata = {
            'uid': uid,
            'dynamic_id': dynamic_ID,
            'up': '1',
            'csrf_token': csrf,
            'csrf': csrf
        }
        thumburl = 'https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb'
        try:
            reqthumb = requests.request('POST', url=thumburl, data=thumbdata, headers=thumbheader)
        except Exception as e:
            print(e)
            while 1:
                try:
                    time.sleep(int(input('输入等待时间')))
                    break
                except:
                    continue
            reqthumb = self.thumb(dynamic_ID, cookie, useragent, uid, csrf)
        if (reqthumb.text) == '{"code":0,"msg":"","message":"","data":{"_gt_":0}}':
            print('点赞成功')
        else:
            print('点赞失败')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_ID)
            dianzanshibai.append((lianjie))

    def huifuneirong(self, content, dynamic_id, rid, type):  # 回复内容的判断
        msg = ''
        nomsg = '@盛百凡'
        premsg = ''
        topobj_3 = re.match('.*@一位好友.*', content, re.DOTALL)
        topobj_2 = re.match('.*艾特1位好友.*', content, re.DOTALL)
        topobj_1 = re.match('.*@你想祝福的人.*', content, re.DOTALL)
        topobj0 = re.match('.*@1位胖友.*', content, re.DOTALL)
        topobj1 = re.match('.*圈1位你的伙伴.*', content, re.DOTALL)
        topobj2 = re.match('.*带tag#.*#.*', content, re.DOTALL)
        topobj3 = re.match('.*带话题#.*#.*', content, re.DOTALL)
        topobj4 = re.match('.*带上tag#.*#.*', content, re.DOTALL)
        topobj5 = re.match('.*带#.*#.*', content, re.DOTALL)
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
        pinglun_req = self.get_pinglunreq(str(dynamic_id), str(rid), pn, str(type))
        pinglun_dict = json.loads(pinglun_req)
        try:
            pinglun_count = pinglun_dict.get('data').get('cursor').get('prev')
        except:
            print('获取评论失败')
            print(pinglun_req)
            pinglun_count = 0
            print(self.timeshift(int(time.time())))
            time.sleep(eval(input('输入等待时间')))
        if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
            if pinglun_count != 0:
                i = 0
                while True:
                    i += 1
                    pnlist = list(range(10, pinglun_count - 20))
                    if pnlist == []:
                        print('动态下评论过少，评论获取失败')
                        break
                    pn = random.choice(pnlist)
                    pinglun_req = self.get_pinglunreq(str(dynamic_id), str(rid), pn, str(type))
                    pinglun_dict = json.loads(pinglun_req)
                    reply_content = []
                    if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
                        pinglun_list = pinglun_dict.get('data').get('replies')
                        for reply in pinglun_list:
                            reply_content.append(reply.get('content').get('message'))
                    else:
                        print('获取评论失败')
                    if reply_content != []:
                        for i in range(pinglunzhuanbiancishu):
                            while 1:
                                msg = ''.join(random.choice(reply_content))
                                sums = 0
                                for wordcount in reply_content:
                                    sums += len(wordcount)
                                if len(msg) <= int(sums / len(reply_content)) + 10:
                                    break
                            biaoqingbao = re.findall('(?<=\[)(.*?)(?=\])', msg, re.DOTALL)
                            changyongemo = ['doge', '脱单doge', '妙啊', '吃瓜', '嗑瓜子', 'tv_doge', '狗子', '原神_哇', '原神_哼',
                                            '原神_嗯',
                                            '原神_欸嘿', '原神_喝茶']
                            if biaoqingbao != []:
                                tihuanbiaoqing = self.panduanbiaoqingbao(biaoqingbao)
                                if tihuanbiaoqing != []:
                                    for noemo in tihuanbiaoqing:
                                        msg = msg.replace(noemo, random.choice(changyongemo))
                            msg += '[' + random.choice(changyongemo) + ']'  # 添加随机表情
                            if nomsg in msg:
                                continue
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
                        print('获取评论为空\t动态类型：' + str(type))
                    time.sleep(random.choice(self.sleeptime))
                    if i >= 3:
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
        msg = random.choice(replycontent)
        return msg

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
        fakeuseragent = random.choice(User_Agent_List)
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
            time.sleep(eval(input('输入等待时间')))
            self.get_pinglunreq(str(dynamic_id), str(rid), pn, str(_type))
            return 0
        return pinglunreq.text

    def get_dynamic_detail(self, dynamic_id, cookie, useragent):
        url = 'http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id=' + str(dynamic_id)
        headers = {
            "cookie": cookie,
            "user-agent": useragent
        }
        data = {"dynamic_id": str(dynamic_id)}
        dynamic_req = requests.request('GET', url=url, headers=headers, data=data)
        try:
            dynamic_dict = json.loads(dynamic_req.text)
            dynamic_data = dynamic_dict.get('data')
            dynamic_type = dynamic_data.get('card').get('desc').get('type')
            dynamic_rid = dynamic_data.get('card').get('desc').get('rid')
            relation = dynamic_data.get('card').get('display').get('relation').get('is_follow')
            is_liked = dynamic_data.get('card').get('desc').get('is_liked')
        except Exception as e:
            print(e)
            time.sleep(eval(input('输入等待时间')))
            return None
        structure = {'type': dynamic_type,
                     'rid': dynamic_rid,
                     'relation': relation,
                     'is_liked': is_liked
                     }
        return structure

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
                  '热词系列_多谢款待', '热词系列_EDG', '热词系列_我们是冠军', '脸红', '热词系列_破防了', '热词系列_燃起来了',
                  '虎年', '冰墩墩', '雪容融', '热词系列_红红火火', '小电视_笑', '小电视_发愁', '小电视_赞', '小电视_差评', '小电视_嘟嘴', '小电视_汗', '小电视_害羞',
                  '小电视_吃惊', '小电视_哭泣', '小电视_太太喜欢', '小电视_好怒啊', '小电视_困惑', '小电视_我好兴奋', '小电视_思索', '小电视_无语', '2233娘_大笑',
                  '2233娘_吃惊', '2233娘_大哭', '2233娘_耶', '2233娘_卖萌', '2233娘_疑问', '2233娘_汗', '2233娘_困惑', '2233娘_怒',
                  '2233娘_委屈', '2233娘_郁闷', '2233娘_第一', '2233娘_喝水', '2233娘_吐魂', '2233娘_无言'
                  ]
        tihuanbiaoqing = []
        for biaoqing in emo:
            if (biaoqing not in hasemo):
                tihuanbiaoqing.append(biaoqing)
        return tihuanbiaoqing

    def create_prizedict(self, id):
        url = 'http://api.bilibili.com/x/article/view?id={id}'.format(id=id)
        req = requests.get(url=url)
        time.sleep(3)
        content = req.json().get('data').get('content')
        html = etree.HTML(content)
        prizecontent = html.xpath('//text()')
        cutflag1 = 0
        cutflag2 = -1
        if prizecontent.index('非官方抽奖') < prizecontent.index('官方抽奖'):
            for i in prizecontent:
                if '非官方抽奖' == i:
                    cutflag1 = prizecontent.index(i) + 1
                if '官方抽奖' == i:
                    cutflag2 = prizecontent.index(i) - 1
                    break
            prizecontent = prizecontent[cutflag1:cutflag2]
        else:
            for i in prizecontent:
                if '非官方抽奖' == i:
                    cutflag1 = prizecontent.index(i) + 1
                if '预约抽奖' == i:
                    cutflag2 = prizecontent.index(i) - 1
                    break
            prizecontent = prizecontent[cutflag1:cutflag2]
        prizedict = {}
        i = 0
        prizename = 'none'
        while 1:
            if i < len(prizecontent):
                if not 'https' in prizecontent[i]:
                    prizename = prizecontent[i]
                    i += 1
                    continue
                else:
                    prizebuff1 = i
                    while 1:
                        if not 'https' in prizecontent[i]:
                            i -= 1
                            break
                        else:
                            i += 1
                    if i - prizebuff1 == 0:
                        prizedict.update({prizename: [prizecontent[i]]})
                        i += 1
                    else:
                        prizelist = prizecontent[prizebuff1:i + 1]
                        prizedict.update({prizename: prizelist})
                        i += 1
            else:
                break
        return prizedict

    def revertShortLink(self, short_url):
        req = requests.head(short_url)
        dyurl = req.headers.get('location')
        try:
            if 'BV' in dyurl:
                return None
            dynamicid = dyurl.split('/')[4].split('?')[0]
            return dynamicid
        except Exception as e:
            print(e)
            print('url转换失败')
            print(short_url)
            print(dyurl)
            self.changefail.append(short_url)
            while 1:
                try:
                    time.sleep(int(input('输入等待时间')))
                    break
                except:
                    continue
            return self.revertShortLink(short_url)

    # def url_change(self, short_url):
    #     url = 'https://api.mfpad.com/api/tool/redirects'
    #     data = {
    #         'url': short_url
    #     }
    #     headers = {
    #         'path': '/api/tool/redirects',
    #         'user-agent': random.choice(self.User_Agent_List)
    #     }
    #     while 1:
    #         try:
    #             req = requests.post(url=url, data=data, headers=headers)
    #             break
    #         except Exception as e:
    #             print(e)
    #             time.sleep(int(input('输入等待时间')))
    #     try:
    #         dyurl = req.json().get('data')[0].get('redirect')
    #         dynamicid = dyurl.split('/')[4].split('?')[0]
    #         return dynamicid
    #     except Exception as e:
    #         print(e)
    #         print('url转换失败')
    #         print(req.json())
    #         self.changefail.append(short_url)
    #         while 1:
    #             try:
    #                 time.sleep(int(input('输入等待时间')))
    #                 break
    #             except:
    #                 continue
    #         return self.url_change(short_url)

    def account_choose(self, accountname, *msglist):
        cookie1 = gl.get_value('cookie1')  # 星瞳
        fullcookie1 = gl.get_value('fullcookie1')
        ua1 = gl.get_value('ua1')
        fingerprint1 = gl.get_value('fingerprint1')
        csrf1 = gl.get_value('csrf1')
        uid1 = gl.get_value('uid1')
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
        if accountname == 1:
            print(uid1)
            self.get_cv_info(uid=uid1, csrf=csrf1, cookie=cookie1, ua=ua1, msglist=msglist)
        elif accountname == 2:
            print(uid2)
            self.get_cv_info(uid=uid2, csrf=csrf2, cookie=cookie2, ua=ua2, msglist=msglist)
        elif accountname == 3:
            print(uid3)
            self.get_cv_info(uid=uid3, csrf=csrf3, cookie=cookie3, ua=ua3, msglist=msglist)
        elif accountname == 4:
            print(uid4)
            self.get_cv_info(uid=uid4, csrf=csrf4, cookie=cookie4, ua=ua4, msglist=msglist)


if __name__ == '__main__':
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
    pinglunzhuanbiancishu = 5
    replycontent = ['[原神_欸嘿]', '[原神_喝茶]', '好耶', '来了', '冲鸭', '来了来了', '贴贴', '冲',
                    '[原神_哼]', '[原神_嗯][原神_哇][原神_哼]', '[原神_哇][原神_哼]', '[原神_哇]',
                    '万一呢']  # 默认评论内容
    pinglunshibai = []
    dianzanshibai = []
    zhuanfashibai = []
    weiguanzhu = []
    dianguozandedongtai = []
    a = mycls()
    a.yunxingshijian = 3600 / 4
    print(a.timeshift(time.time()))
    pinglunneirong1 = ['[虎年]']
    pinglunneirong2 = ['[豹富]', '[2022]', '[虎年]', '[酸了]', '╮(￣▽￣)╭']
    pinglunneirong4 = ['[豹富]']
    pinglunneirong3 = ['[热词系列_好耶]','[冰墩墩]', '[热词系列_红红火火]']
    a.account_choose(3, pinglunneirong3)
    # 1：星瞳
    # 2：保加利亚
    # 3：斯卡蒂
    # 4：墨色
    print('评论失败：')
    print(pinglunshibai)
    print('点赞失败')
    print(dianzanshibai)
    print('转发失败：')
    print(zhuanfashibai)
    print('点过赞的动态：' + str(dianguozandedongtai))
    print('未关注：')
    print(weiguanzhu)
    print('url转换失败：')
    for i in a.changefail:
        print(i)
    print(a.timeshift(time.time()))
