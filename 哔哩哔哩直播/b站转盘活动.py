# coding:utf-8
import json
import os
import random
import re
import threading
import time
import numpy
import requests
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl


def get_actvity_lottery_past():
    retlist = []
    f = open('./转盘日志/已结束的盘子.csv', 'r', encoding='utf-8')
    for i in f.readlines():
        retlist.append(i.split(',')[1].strip())
    f.close()
    return retlist


try:
    past_sid_List = get_actvity_lottery_past()
    print(f'过期盘子sid：{past_sid_List}')
except:
    past_sid_List = []
sleeptime = numpy.linspace(3, 5, 500, endpoint=False)
yijieshuhuodong = {}

sanlianpanlianjie = {
    # '春日种草游园会':'https://www.bilibili.com/blackboard/activity-9lnXdixhzC.html',
    # '荣耀手机Vlog大赛': "https://www.bilibili.com/blackboard/activity-9hZucZl0A3.html",
    # '全民健康局，你UP你也行':'https://www.bilibili.com/blackboard/activity-Z7bBvZpmrC.html',
    # '人均操控大师': 'https://www.bilibili.com/blackboard/activity-zINjefmUi7.html',  # 5
    # '2022要红奥': 'https://www.bilibili.com/blackboard/activity-msEfZLowdZ.html',  # 5
    # '华帝时光之味': "https://www.bilibili.com/blackboard/activity-nNUAbmyXhl.html",
    # '新年优宇宙干杯选乳汽': 'https://www.bilibili.com/blackboard/activity-QMKrt0ruBM.html',  # 5
    # # '轻装上阵2022':'https://www.bilibili.com/blackboard/activity-fQB5cPnoZX.html',
    # '打工人职场生态图鉴': "https://www.bilibili.com/blackboard/activity-ScCKyHcb6K.html",
    # # '科鲁泽，人生的痛快连成串':"https://www.bilibili.com/blackboard/activity-nvBL6YX616.html",
    # # '头文字S':"https://www.bilibili.com/blackboard/activity-AfWjifffmW.html",
    # # '一罐高能把把带劲':"https://www.bilibili.com/blackboard/activity-1DapBs1tZ0.html",#5
    # # '快到我胃里来':'https://www.bilibili.com/blackboard/activity-iOhxlUK20P.html',
    # # '再啵嘴，就打折':"https://www.bilibili.com/blackboard/activity-S3E3hexwoU.html",
    # # '原来可以这样整活':'https://www.bilibili.com/blackboard/activity-0iWeTtTgMl.html',#5
    # # '我的奶茶很能打':'https://www.bilibili.com/blackboard/activity-8t11VMHNAN.html',
    # '益成长趣生活': "https://www.bilibili.com/blackboard/activity-pPyBEzc3p2.html",  # 5
    # # '全民潮玩新国风':"https://www.bilibili.com/blackboard/activity-dnEcsd9Gbz.html",
    # # '穿出去，才是对汉服更好的守护':'https://www.bilibili.com/blackboard/activity-9TM8IAanI0.html',
    # # '随心所欲的FEEL':"https://www.bilibili.com/blackboard/activity-Ir0YSm6eYL.html",
    # # '2060未来玩家':"https://www.bilibili.com/blackboard/activity-zsf2uh9HKX.html",#5
    # # '许昕教你用夸克漂亮回击问题':'https://www.bilibili.com/blackboard/activity-mfvDDiMU89.html',#5
    # # '我的COUPLE世界':"https://www.bilibili.com/blackboard/activity-vBq77HX64S.html",
    # # '集结！智造家':'https://www.bilibili.com/blackboard/activity-5RNq54ICib.html',
    # # '不主动就被冻':'https://www.bilibili.com/blackboard/activity-tAKZGS0wE3.html',
    # # '萌宠的问号脸': 'https://www.bilibili.com/blackboard/activity-u0ihStjXug.html',
    # # '健康星人club':'https://www.bilibili.com/blackboard/activity-aooaMgmN9F.html',
    # # '2021广州车展':'https://www.bilibili.com/blackboard/activity-x5E8CM4kOK.html'

}
jifenpanlianjie = {
    # '快乐小Pro站 有内味乐':'https://www.bilibili.com/blackboard/activity-HnR0mbMXOA.html',
    # '活力行为大赏':'https://www.bilibili.com/blackboard/activity-K8n6PP20zC.html',
    # '原来家电还可以这样': 'https://www.bilibili.com/blackboard/activity-WUTcgxEPSS.html',
    # '即刻奔赴一面之约':"https://www.bilibili.com/blackboard/activity-Whv6aRjJHm.html"
}

qiandaolianjie = {
    '幻塔': 'https://www.bilibili.com/blackboard/activity-3q9ofO7uXn.html'
}
meiripanlianjie = {

    'KPL':'https://www.bilibili.com/blackboard/activity-WsALgeVJcc.html',
    '青春':'https://www.bilibili.com/blackboard/activity-ickPWgXsv5.html',
    '扩音':'https://www.bilibili.com/blackboard/activity-kuoyinjihua2-PC.html',
    '美孚':'https://www.bilibili.com/blackboard/activity-dKrLNJxcJH.html',
    '毕业':'https://www.bilibili.com/blackboard/activity-rTbrIqOEtt.html',
    '科幻':'https://www.bilibili.com/blackboard/activity-sci-fi-2022.html',
    '必剪1':'https://www.bilibili.com/blackboard/activity-oCKb1F8nD2.html',
    '聚会':'https://www.bilibili.com/blackboard/topic/activity-IzmyVTtpI2.html',
    '歌手':'https://www.bilibili.com/blackboard/campus-singer.html',
    '黄绿':'https://www.bilibili.com/blackboard/activity-yellowVSgreen8th.html',
    'RTX':'https://www.bilibili.com/blackboard/activity-OP3Tl9IaZX.html',
    '彩虹': 'https://www.bilibili.com/blackboard/activity-DizrLJpOma.html',
    '特优': 'https://www.bilibili.com/blackboard/topic/activity-KYdzoX8Hyt.html',
    '新星': 'https://www.bilibili.com/blackboard/supernova3.html',
    'oppo': 'https://www.bilibili.com/blackboard/activity-82jcdvfkO2.html',
    'pico': 'https://www.bilibili.com/blackboard/activity-ZuG3mKyf1x.html',
    '算法': 'https://www.bilibili.com/blackboard/topic/activity-KdSV8C8MIC.html',
    '租房': 'https://www.bilibili.com/blackboard/activity-MiUvgGJdDa.html',
    '挂摊': 'https://www.bilibili.com/blackboard/activity-I6J1u6hcgG.html',
    '音浪': 'https://www.bilibili.com/blackboard/activity-summer-pc.html',
    '港风': 'https://www.bilibili.com/blackboard/activity-oXcOyOBhv5.html',
    '乱斗': 'https://www.bilibili.com/blackboard/activity-mPCGIXOrmI.html',
    '九号': 'https://www.bilibili.com/blackboard/activity-xwt0mXrwUd.html',
    '野生': 'https://www.bilibili.com/blackboard/activity-5nIjt7Rq3q.html',
    '荣耀': 'https://www.bilibili.com/blackboard/activity-rongyaoPC.html',
    'b看': 'https://www.bilibili.com/blackboard/BMustSee07.html',
    '手游': 'https://www.bilibili.com/blackboard/activity-EVOSJHYlKe.html',
    'lpl': 'https://www.bilibili.com/blackboard/activity-Xl5J9ObBQM.html',
    'pgp': 'https://www.bilibili.com/blackboard/activity-6OE2G5hfKB.html',
    '果然': 'https://www.bilibili.com/blackboard/activity-KfPEIhF4dq.html',
    '脱单': 'https://www.bilibili.com/blackboard/activity-hJuJy1xP3a.html',
    '天依': 'https://www.bilibili.com/blackboard/luotianyi10.html',
    '盛夏': 'https://www.bilibili.com/blackboard/2022Vsinger02.html',
    '暂停': 'https://www.bilibili.com/blackboard/activity-mZJZiWPsJ3.html',
    # '粤来粤好':'https://www.bilibili.com/blackboard/activity-JNNZBjq8cF.html',
    # '改造':'https://www.bilibili.com/blackboard/activity-mznqXt8537.html',
    # '密事':'https://www.bilibili.com/blackboard/topic/activity-7o31ouyNaO.html',
    # '九号':'https://www.bilibili.com/blackboard/activity-xwt0mXrwUd.html',
    # '好看':'https://www.bilibili.com/blackboard/activity-V3Vp3XaNfz.html',
    # '脱单':'https://www.bilibili.com/blackboard/activity-hJuJy1xP3a.html',
    # 'D5':'https://www.bilibili.com/blackboard/activity-YkzFLriekf.html',
    # '盛夏':'https://www.bilibili.com/blackboard/2022Vsinger02-m.html',
    # '天依':'https://www.bilibili.com/blackboard/luotianyi10th.html',
    # 'MSI':'https://www.bilibili.com/blackboard/activity-k9XKdOvtuO.html',
    # '和平':'https://www.bilibili.com/blackboard/activity-AWS13XWaeu.html',
    # '三星1':'https://www.bilibili.com/blackboard/activity-OgXKsjfYSX.html',
    # '三星2':'https://www.bilibili.com/blackboard/activity-6JUJBCUhzg.html',
    # '漫画':'https://www.bilibili.com/blackboard/423manga_fes-m.html',
    # 'KPL':'https://www.bilibili.com/blackboard/activity-usEUW4aiTI.html',
    # '脉动':'https://www.bilibili.com/blackboard/activity-XlZexFgxBm.html',

    # #'唱歌':'https://www.bilibili.com/blackboard/activity-singwithmePC.html',
    # '三星':'https://www.bilibili.com/blackboard/activity-6JUJBCUhzg.html',
    # '舞蹈':'https://www.bilibili.com/blackboard/BDF2022.html',
    # 'BDF':'https://www.bilibili.com/blackboard/activity-XlZexFgxBm.html',
    # #'影片':'https://www.bilibili.com/blackboard/topic/activity-uPdPgxmkJN.html',
    # '说唱':'https://www.bilibili.com/blackboard/rapforyouth-pc.html',
    # '改造':'https://www.bilibili.com/blackboard/activity-q3ElZbvNJI.html',
    # #'RTX':'https://www.bilibili.com/blackboard/activity-go6YaYufgx.html',
    # #'oppo':'https://www.bilibili.com/blackboard/activity-OPPOEncoX2.html',
    # 'kpl':'https://www.bilibili.com/blackboard/activity-7PcjuVx0Mk.html',
    # #'气象':'https://www.bilibili.com/blackboard/activity-cSlOCOInJA.html',
    # '天依':'https://www.bilibili.com/blackboard/luotianyi10.html',
    # #'娱你':'https://www.bilibili.com/blackboard/activity-ruWwtb8Eq8.html',
    # # '追番':'https://www.bilibili.com/blackboard/activity-o5wADj36Y0.html',
    # # '匠人':'https://www.bilibili.com/blackboard/activity-DB0qaHzh5B.html',
    # # 'LPL':'https://www.bilibili.com/blackboard/activity-RiD9cZ0xqr.html',
    # # '萌宠':'https://www.bilibili.com/blackboard/mcbnh.html',
    # # '时空':'https://www.bilibili.com/blackboard/activity-2lsqjo2RBP.html',
    # # '公益':'https://www.bilibili.com/blackboard/activity-S8lOikXwZi.html',
    # # '吉利':'https://www.bilibili.com/blackboard/activity-GIJc4KJHsP.html',
    # # '明星': 'https://www.bilibili.com/blackboard/activity-foKiAkNBDb.html',
    # # '颜值': 'https://www.bilibili.com/blackboard/activity-ig22yGMowI.html',
    # # '太和': 'https://www.bilibili.com/blackboard/taihemusic-PC.html',
    # # '知夜': 'https://www.bilibili.com/blackboard/activity-or1Ig7ifRa.html',
    # # '百大': "https://www.bilibili.com/blackboard/BPU2021/activity-LopbXDX7Xn.html",
    # # '新春': 'https://www.bilibili.com/blackboard/activity-1jGR6WdRD3.html',
    # # # '参半':'https://www.bilibili.com/blackboard/activity-hGcqFysu1V.html',
    # # '盒乐': 'https://www.bilibili.com/blackboard/activity-UVCTVdUNug.html',
    # # '音乐': 'https://www.bilibili.com/blackboard/activity-yinyue2021-PC.html',
    # # 'vivo s12': 'https://www.bilibili.com/blackboard/activity-0DROx92R9j.html',
    # # '特修班': 'https://www.bilibili.com/blackboard/activity-1ID7Ctv8l0.html',
    # # '腾讯游戏': "https://www.bilibili.com/blackboard/activity-blyFzGPafM.html",
    # # '粤来粤好': 'https://www.bilibili.com/blackboard/activity-iwt8D2hxva.html',
    # # #'住在b站': 'https://www.bilibili.com/blackboard/activity-JqkUBmNTnK.html',
    # # #'华为': 'https://www.bilibili.com/blackboard/activity-GLFK4bkW7w.html',
    # # #'娱乐2_2': 'https://www.bilibili.com/blackboard/activity-YLJNH-PC.html',
    # # # '王者':'https://www.bilibili.com/blackboard/activity-z319DfWb3j.html',
    # # '交大': 'https://www.bilibili.com/blackboard/activity-P8htiIy0Eq.html',
    # # '敦煌': 'https://www.bilibili.com/blackboard/xunmengdunhuang_web.html',
    # # # '虚拟':'https://live.bilibili.com/blackboard/activity-9VZGeRGsyO.html',
    # # # '唯品':'https://www.bilibili.com/blackboard/activity-YOsNVhTNTs.html',
    # # # '创作':'https://www.bilibili.com/blackboard/topic/activity-DvU1PqmfTO.html',
    # # #'故事': 'https://www.bilibili.com/blackboard/gushi2021.html',
    # # # '必剪':'https://www.bilibili.com/blackboard/activity-5Fnq4FMBPO.html',
    # # # '虚拟偶像':'https://live.bilibili.com/blackboard/activity-9VZGeRGsyO.html',
    # # '千年': 'https://www.bilibili.com/blackboard/xunmengdunhuang_web.html',
    # # # '知识':'https://www.bilibili.com/blackboard/activity-Xef6oJxyPM.html',
    # # # '健身':'https://www.bilibili.com/blackboard/activity-asWUECSnKp.html',
    # # # '弹幕':'https://www.bilibili.com/blackboard/topic/activity-F1tof1SsPC.html',
    # # # '家具':'https://www.bilibili.com/blackboard/activity-wHq3OwadkW.html',
    # # '贴纸2': 'https://www.bilibili.com/blackboard/activity-aKykWDx3YI.html',
    # # # '独游': 'https://www.bilibili.com/blackboard/activity-El6zj1CX3x.html',
    # # '贴纸1': 'https://www.bilibili.com/blackboard/activity-Euson5i7eE.html',
    # # # '发发': 'https://www.bilibili.com/blackboard/activity-7cdVuG5dxe.html',
    # # # '和平': 'https://www.bilibili.com/blackboard/activity-gvjpq1iDp7.html',
    # # # '竞速': 'https://www.bilibili.com/blackboard/activity-JL1G2xGCSa.html',
    # # # '娱乐1':'https://www.bilibili.com/blackboard/activity-YQFUN-PC.html',
    # # #'娱乐2': 'https://www.bilibili.com/blackboard/activity-JYSBtWclC6.html'
}


class sanlianpan:
    @classmethod
    def mytimes(cls, ua, cookie, csrf, sid, key, value):
        url = 'https://api.bilibili.com/x/lottery/mytimes?csrf=' + csrf + '&sid=' + sid
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = requests.get(url=url, headers=headers)
        req = json.loads(req.text)
        print(req)
        if req.get('message') == '活动已结束':
            print(req.get('message'))
            print(sid)
            yijieshuhuodong.update({key: sid})
            times = 0
            return times
        if req.get('message') == '活动不存在':
            print(req.get('message'))
            print(sid)
            yijieshuhuodong.update({key: sid})
            times = 0
            return times
        if req.get('message') == '活动还未开始':
            print(req.get('message'))
            print(sid)
            times = 0
            return times
        else:
            times = req.get('data').get('times')
            print(req)
            return times

    @classmethod
    def do_lottery(cls, ua, cookie, csrf, sid):
        url = 'https://api.bilibili.com/x/lottery/do'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   }
        data = {
            'csrf': csrf,
            'sid': sid,
            'num': '1'}
        req = requests.post(url=url, data=data, headers=headers)
        req = json.loads(req.text)
        return req

    @classmethod
    def share_add(cls, ua, cookie, csrf, aid):  # 每日盘分享
        url = 'https://api.bilibili.com/x/web-interface/share/add'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'authority': 'api.bilibili.com',
                   'method': 'POST',
                   'path': '/x/web-interface/share/add',
                   'scheme': 'https',
                   'accept': 'application/json,text/plain,*/*',
                   'accept - encoding': 'gzip,deflate,br',
                   'accept - language': 'zh-CN,zh;q=0.9',
                   'origin': 'https://www.bilibili.com',
                   'referer': 'https://www.bilibili.com/video/av' + str(aid)
                   }
        data = {'aid': aid,
                'jsonp': "jsonp",
                'csrf': csrf,
                'csrf_token': csrf,
                'visit_id': ''
                }
        req = requests.post(url=url, data=data, headers=headers)
        print(req.text)

    @classmethod
    def get_newLottery_sid(cls, ua, cookie, _url):
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = requests.get(url=_url, headers=headers)
        try:
            sid = re.findall('"lotteryId":"(.*?)"', req.text, re.DOTALL)
            sid = list(set(sid))
        except:
            try:
                sid = re.findall('lotteryId:"(.*?)",', req.text, re.DOTALL)
                sid = list(set(sid))
            except:
                print(req.text)
                print(_url)
                print(
                    '\033[4;31;40mWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\n\033[0m')
                return 0
        if sid == [] or sid == None:
            print(_url)
        return sid

    @classmethod
    def thumb(cls, ua, fullcookie, csrf, uid, dynamic_ID):  # 为动态点赞标记
        thumbheader = {
            'authority': 'api.vc.bilibili.com',
            'method': 'POST',
            'path': '/dynamic_like/v1/dynamic_like/thumb',
            'scheme': 'https',
            'cookie': fullcookie,
            'user-agent': ua,
            'Connection': 'keep-alive',
            'origin': 'https://t.bilibili.com',
            'referer': 'https://t.bilibili.com/' + str(dynamic_ID) + '?tab=2'
        }
        thumbdata = {
            'uid': uid,
            'dynamic_id': dynamic_ID,
            'up': 1,
            'csrf_token': csrf,
            'csrf': csrf
        }
        thumburl = 'https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb'
        reqthumb = requests.request('POST', url=thumburl, data=thumbdata, headers=thumbheader)
        if reqthumb.text == '{"code":0,"msg":"","message":"","data":{"_gt_":0}}':
            print('点赞成功')
            print('https://t.bilibili.com/' + str(dynamic_ID) + '?tab=2')
        else:
            print('点赞失败')
            print(reqthumb.text)
            print('https://t.bilibili.com/' + str(dynamic_ID) + '?tab=2')

    @classmethod
    def fetch_dynamics(cls, ua, cookie, topicname, offset):
        url = 'https://api.vc.bilibili.com/topic_svr/v1/topic_svr/fetch_dynamics?topic_name=' + topicname + '&page_size=20&platform=h5&offset_dynamic_id=' + str(
            offset)
        data = {
            'topic_name': topicname,
            'page_size': 20,
            'platform': 'h5',
            'offset_dynamic_id': offset
        }
        headers = {'User-Agent': ua,
                   'cookie': cookie
                   }
        req = requests.get(url=url, headers=headers, data=data)
        req_dict = json.loads(req.text)
        return req_dict

    def do_sanlianpan(self, ua, cookie, csrf, uid, fullcookie):
        a = sanlianpan()
        for key in sanlianpanlianjie:
            print(key)
            topicname = key
            url = sanlianpanlianjie.get(key)
            try:
                dynamics = []
                aids = []
                offset = ''
                while len(dynamics) <= 5:
                    req_dict = a.fetch_dynamics(ua, cookie, topicname, offset)
                    cards = req_dict.get('data').get('cards')
                    offset = req_dict.get('data').get('offset')
                    for i in cards:
                        isliked = i.get('desc').get('is_liked')
                        if isliked != 0:
                            continue
                        try:
                            desc = i.get('desc')
                            type = desc.get('type')
                            if type == 8:
                                dynamic = desc.get('dynamic_id')
                                dynamics.append(dynamic)
                        except Exception as e:
                            print(e)
                            continue
                    time.sleep(random.choice(sleeptime))
                    for i in cards:
                        try:
                            card = i.get('card')
                            card_dict = json.loads(card)
                            aid = card_dict.get('aid')
                            if aid is not None:
                                aids.append(aid)
                        except:
                            continue
            except:
                print(
                    '\033[4;31;40mWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\n\033[0m')
                return 0
            time.sleep(random.choice(sleeptime))
            if (key == '人均操控大师' or key == '原来可以这样整活' or key == '2060未来玩家' or key == '许昕教你用夸克漂亮回击问题' or key == '问到底事务所'
                    or key == '新年优宇宙干杯选乳汽' or key == '一罐高能把把带劲'
                    or key == '益成长趣生活' or key == '2022要红奥'
            ):
                for i in range(5):
                    a.thumb(ua, fullcookie, csrf, uid, random.choice(dynamics))
                    time.sleep(random.choice(sleeptime))
                    a.share_add(ua, cookie, csrf, random.choice(aids))
                    time.sleep(random.choice(sleeptime))
            elif key == '春日种草游园会':
                for i in range(2):
                    a.thumb(ua, fullcookie, csrf, uid, random.choice(dynamics))
                    time.sleep(random.choice(sleeptime))
                    a.share_add(ua, cookie, csrf, random.choice(aids))
                    time.sleep(random.choice(sleeptime))
            else:
                a.thumb(ua, fullcookie, csrf, uid, random.choice(dynamics))
                time.sleep(random.choice(sleeptime))
                a.share_add(ua, cookie, csrf, random.choice(aids))
                time.sleep(random.choice(sleeptime))
            sids = a.get_newLottery_sid(ua, cookie, url)
            for sid in sids:
                if sid in past_sid_List:
                    continue
                print(sid)
                if sid == '':
                    print(
                        '\033[4;31;40mWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\nWarning\n\033[0m')
                    print({key: jifenpanlianjie.get(key)})
                    continue
                time.sleep(random.choice(sleeptime))
                try:
                    mytime = a.mytimes(ua, cookie, csrf, sid, key, sanlianpanlianjie.get(key))
                except Exception as e:
                    print(e)
                    mytime = 0
                print('剩余次数：' + str(mytime))
                if mytime == 0:
                    print(key)
                    print(sanlianpanlianjie.get(key))
                while 1:
                    res = a.do_lottery(ua, cookie, csrf, sid)
                    print(res)
                    code = res.get('code')
                    if code != 0:
                        break
                    time.sleep(6)
                print('\n\n\n')


class jifenpan:
    @classmethod
    def complettask(cls, ua, cookie, topicname):
        url = 'https://api.vc.bilibili.com/topic_svr/v1/topic_svr/fetch_dynamics?topic_name=' + topicname + '&sortby=2&page_size=20&platform=h5'
        data = {
            'topic_name': topicname,
            'sortby': 2,
            'page_size': 20,
            'platform': 'h5'
        }
        headers = {'User-Agent': ua,
                   'cookie': cookie
                   }
        req = requests.get(url=url, data=data, headers=headers)
        req = json.loads(req.text)
        dynamics = {}
        cards = req.get('data').get('cards')
        for i in cards:
            isliked = i.get('desc').get('is_liked')
            if isliked == 0:
                try:
                    card = i.get('card')
                    card_dict = json.loads(card)
                    aid = card_dict.get('aid')
                    if aid is not None or aid != '' or aid != [] or aid != ['']:
                        aid = aid
                except Exception as e:
                    print(e)
                    continue
                dynamic_id = i.get('desc').get('dynamic_id')
                dynamics.update({aid: dynamic_id})
        offset = req.get('data').get('offset')
        time.sleep(random.choice(sleeptime))
        while (len(dynamics) < 10):
            url = 'https://api.vc.bilibili.com/topic_svr/v1/topic_svr/fetch_dynamics?topic_name=' + topicname + '&sortby=2&page_size=20&platform=h5&offset=' + str(
                offset)
            data = {
                'topic_name': topicname,
                'sortby': 2,
                'page_size': 20,
                'platform': 'h5',
                'offset': offset
            }
            req = requests.get(url=url, data=data, headers=headers)
            req = json.loads(req.text)
            cards = req.get('data').get('cards')
            for i in cards:
                isliked = i.get('desc').get('is_liked')
                if isliked == 0:
                    try:
                        card = i.get('card')
                        card_dict = json.loads(card)
                        aid = card_dict.get('aid')
                        if aid is not None or aid != '' or aid != [] or aid != ['']:
                            aid = aid
                    except Exception as e:
                        print(e)
                        continue
                    dynamic_id = i.get('desc').get('dynamic_id')
                    dynamics.update({aid: dynamic_id})
            offset = req.get('data').get('offset')
            time.sleep(random.choice(sleeptime))
        return dynamics

    def do_jifenpan(self, ua, cookie, csrf, uid, fullcookie):
        a = sanlianpan()
        b = jifenpan()
        for key in jifenpanlianjie:
            print(key)
            url = jifenpanlianjie.get(key)
            dynamics = b.complettask(ua, cookie, key)
            print(dynamics)
            count = 0
            sids = a.get_newLottery_sid(ua, cookie, url)
            for sid in sids:
                if sid in past_sid_List:
                    continue
                print(sid)
                if sid == '':
                    yijieshuhuodong.update({key: sid})
                    continue
                for aid, dynamicid in dynamics.items():
                    a.thumb(ua, fullcookie, csrf, uid, dynamicid)
                    time.sleep(random.choice(sleeptime))
                    a.share_add(ua, cookie, csrf, aid)
                    time.sleep(random.choice(sleeptime))
                    count += 1
                    if count >= 10:
                        break
                time.sleep(random.choice(sleeptime))
                mytime = a.mytimes(ua, cookie, csrf, sid, key, jifenpanlianjie.get(key))
                print('剩余次数：' + str(mytime))
                if mytime == 0:
                    print(key)
                    print(jifenpanlianjie.get(key))
                while 1:
                    res = a.do_lottery(ua, cookie, csrf, sid)
                    print(res)
                    code = res.get('code')
                    if code != 0:
                        break
                    time.sleep(6)
                print('\n\n\n')


class meiripan:
    @classmethod
    def addtimes(cls, ua, cookie, csrf, sid):
        url = 'https://api.bilibili.com/x/lottery/addtimes'
        headers = {'User-Agent': ua,
                   'Cookie': cookie}
        data = {'sid': sid,
                'action_type': '3',
                'csrf': csrf}
        req = requests.post(url=url, headers=headers, data=data)
        req = json.loads(req.text)
        print(req)
        return req.get('data')

    def do_meiripan(self, ua, cookie, csrf):
        a = sanlianpan()
        c = meiripan()
        for name, url in meiripanlianjie.items():
            print(name)
            sids = a.get_newLottery_sid(ua, cookie, url)
            for sid in sids:
                if sid in past_sid_List:
                    print('过期盘子，跳过')
                    print(sid)
                    continue
                print(sid)
                print(sids)
                if sid == '':
                    yijieshuhuodong.update({name: sid})
                    continue
                time.sleep(random.choice(sleeptime))
                data = c.addtimes(ua, cookie, csrf, sid)
                time.sleep(random.choice(sleeptime))
                ztimes = 0
                while 1:
                    if data == {'add_num': 0}:
                        ztimes += 1
                    if ztimes >= 3:
                        time.sleep(random.choice(sleeptime))
                        break
                    if data == None:
                        time.sleep(random.choice(sleeptime))
                        break
                    data = c.addtimes(ua, cookie, csrf, sid)
                    time.sleep(random.choice(sleeptime))
                mytime = a.mytimes(ua, cookie, csrf, sid, name, url)
                print('剩余次数：' + str(mytime))
                time.sleep(random.choice(sleeptime))
                if mytime == 0:
                    print(name)
                    print(meiripanlianjie.get(name))
                while 1:
                    res = a.do_lottery(ua, cookie, csrf, sid)
                    print(res)
                    code = res.get('code')
                    message = res.get('message')
                    if message == '点击过快，请稍后重试':
                        time.sleep(random.choice(sleeptime) + 5)
                        print(name)
                        print(meiripanlianjie.get(name))
                        continue
                    if code != 0:
                        time.sleep(random.choice(sleeptime))
                        print(name)
                        print(meiripanlianjie.get(name))
                        break
                    time.sleep(6)
                print('\n\n\n')

        for n, u in qiandaolianjie.items():
            def reserve():
                _url = 'https://api.bilibili.com/x/activity/reserve'
                _data = {
                    'csrf': csrf,
                    'sid': '688112',
                    'spmid': '888.66630.0.0',
                }
                headers = {'User-Agent': ua,
                           'cookie': cookie
                           }
                req = requests.post(url=_url, data=_data, headers=headers)
                print(req.text)

            # reserve()
            # print(n)
            # sids = a.get_newLottery_sid(ua, cookie, u)
            # for sid in sids:
            #     print(sid)
            #     if sid == '':
            #         yijieshuhuodong.update({n: u})
            #         continue
            #     time.sleep(random.choice(sleeptime))
            #     mytime = a.mytimes(ua, cookie, csrf, sid, n, u)
            #     print('剩余次数：' + str(mytime))
            #     time.sleep(random.choice(sleeptime))
            #     if mytime == 0:
            #         print(n)
            #         print(qiandaolianjie.get(n))
            #     while 1:
            #         res = a.do_lottery(ua, cookie, csrf, sid)
            #         print(res)
            #         code = res.get('code')
            #         message = res.get('message')
            #         if message == '点击过快，请稍后重试':
            #             time.sleep(random.choice(sleeptime) + 5)
            #             print(n)
            #             print(qiandaolianjie.get(n))
            #             continue
            #         if code != 0:
            #             time.sleep(random.choice(sleeptime))
            #             print(n)
            #             print(qiandaolianjie.get(n))
            #             break
            #         time.sleep(6)
            #     print('\n\n\n')


if __name__ == '__main__':
    if not os.path.exists('./转盘日志'):
        os.makedirs('./转盘日志')
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

    a = sanlianpan()
    b = jifenpan()
    c = meiripan()
    sanlian1 = threading.Thread(target=a.do_sanlianpan, args=(ua1, cookie1, csrf1, uid1, fullcookie1))
    sanlian2 = threading.Thread(target=a.do_sanlianpan, args=(ua2, cookie2, csrf2, uid2, fullcookie2))
    sanlian3 = threading.Thread(target=a.do_sanlianpan, args=(ua3, cookie3, csrf3, uid3, fullcookie3))
    sanlian4 = threading.Thread(target=a.do_sanlianpan, args=(ua4, cookie4, csrf4, uid4, fullcookie4))
    meiri1 = threading.Thread(target=c.do_meiripan, args=(ua1, cookie1, csrf1))
    meiri2 = threading.Thread(target=c.do_meiripan, args=(ua2, cookie2, csrf2))
    meiri3 = threading.Thread(target=c.do_meiripan, args=(ua3, cookie3, csrf3))
    meiri4 = threading.Thread(target=c.do_meiripan, args=(ua4, cookie4, csrf4))
    jifen4 = threading.Thread(target=b.do_jifenpan, args=(ua4, cookie4, csrf4, uid4, fullcookie4))
    jifen3 = threading.Thread(target=b.do_jifenpan, args=(ua3, cookie3, csrf3, uid3, fullcookie3))
    jifen2 = threading.Thread(target=b.do_jifenpan, args=(ua2, cookie2, csrf2, uid2, fullcookie2))
    jifen1 = threading.Thread(target=b.do_jifenpan, args=(ua1, cookie1, csrf1, uid1, fullcookie1))

    #meiri1.start()
    #time.sleep(1)
    meiri2.start()
    time.sleep(1)
    meiri3.start()
    time.sleep(1)
    meiri4.start()

    #sanlian1.start()
    time.sleep(3)
    #sanlian1.join()
    sanlian2.start()
    time.sleep(3)
    sanlian2.join()
    sanlian3.start()
    time.sleep(3)
    sanlian3.join()
    sanlian4.start()
    sanlian4.join()

    jifen4.start()
    time.sleep(1)
    jifen3.start()
    time.sleep(1)
    jifen2.start()
    time.sleep(1)
    #jifen1.start()
    jifen4.join()
    jifen3.join()
    jifen2.join()
    #jifen1.join()
    #meiri1.join()
    meiri2.join()
    meiri3.join()
    meiri4.join()
    print('已结束活动：')
    try:
        f = open('./转盘日志/已结束的盘子.csv', 'a+', encoding='utf-8')
    except:
        f = open('./转盘日志/已结束的盘子.csv', 'w', encoding='utf-8')
    for k, v in yijieshuhuodong.items():
        print(k, v)
        f.writelines(f'{k},{v}\n')
    f.close()
