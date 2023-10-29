# -*- coding:utf- 8 -*-
import requests
import re
import random
import time
def timeshift(inputtime):
    inttime=re.search('\d+',inputtime)
    local_time=time.localtime(int(inttime.group()))
    realtime=time.strftime('%Y-%m-%d %H:%M:%S',local_time)
    return realtime
print(timeshift(str(time.time())))
overtime=86400*5
yuanshipingpinglun=[]
xiaoliwu=[]
n=0
zongchoujiang=[]
pinglunsuoxurenshu=5
sleeptime=[0]
a=open('tag非官方抽奖.csv','w',encoding='utf-8')
a.writelines('用户名\t动态地址\t转发人数\t发布时间\t动态内容\n')
User_Agent_List = ['Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
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
ua=random.choice(User_Agent_List)
def choujiangxinxipanduan(tcontent):  # 动态内容过滤条件
    matchobj_37 = re.match('.*弹幕抽.*送.*', tcontent)
    matchobj_36 = re.match('.*随机.*位小伙伴.*现金红包.*', tcontent)
    matchobj_35 = re.match('.*长按复制这条信息，打开手机陶宝下单//.*', tcontent)
    matchobj_34 = re.match('.*评论.*随机.*抽.*', tcontent)
    matchobj_33 = re.match('.*评论.*随机.*抓.*', tcontent)
    matchobj_32 = re.match('.*参与方式.*转发.*关注.*评论.*', tcontent)
    matchobj_31 = re.match('.*评论.*随机.*抓.*', tcontent)
    matchobj_30 = re.match('.*评论.*随机.*抽.*补贴.*', tcontent)
    matchobj_29 = re.match('.*评论区.*揪.*送.*', tcontent)
    matchobj_28 = re.match('.*转发.*评论.*揪.*送.*', tcontent)
    matchobj_25 = re.match('.*关注.*评论.*抽.*', tcontent)
    matchobj_24 = re.match('.*转发.*评论.*抽.*', tcontent)
    matchobj_23 = re.match('.*关注.*转发.*抽.*', tcontent)
    matchobj_22 = re.match('.*评论.*转发.*关注.*抽.*', tcontent)
    matchobj_21 = re.match('.*有奖转发.*', tcontent)
    matchobj_20=re.match('.*评论就有机会抽.*',tcontent)
    matchobj_19=re.match('.*转发.*关注.{0,10}选.*',tcontent)
    matchobj_18=re.match('.*关注+评论，随机选.*',tcontent)
    matchobj_17=re.match('.*互动抽奖.*评论.*抽.*',tcontent)
    matchobj_16=re.match('.*关注.*转发.*抽',tcontent)
    matchobj_15 = re.match('.*转.*评.*赞.*送', tcontent)
    matchobj_14 = re.match('.*评论区.*揪.{0,9}送.*', tcontent)
    matchobj_13 = re.match('.*关注.*评论.*抽.*', tcontent)
    matchobj_12 = re.match('.*评论转发点赞.*抽取.*送.*', tcontent)
    matchobj_11 = re.match('.*关注+评论.*随机选.*送.*', tcontent)
    matchobj_10 = re.match('.*揪.{0,9}送', tcontent)
    matchobj_9 = re.match('.*转发.*揪.*送.*', tcontent)
    matchobj_8 = re.match('.*评论.*关注.*揪', tcontent)
    matchobj_7 = re.match('.*评论.*关注.*抽.*', tcontent)
    matchobj_6 = re.match('.*评论区.{0,9}送.*', tcontent)
    matchobj_5 = re.match('.*转.*评.*送.*鲨鲨酱抱枕.*', tcontent)
    matchobj_4 = re.match('.*转发.*揪.*', tcontent)
    matchobj_3 = re.match('.*揪.*送.*', tcontent)
    matchobj_2 = re.match('.*评论区.*抽.*', tcontent)
    matchobj_1 = re.match('.*卷发.*关注.*', tcontent)
    matchobj = re.match('.*转发.*送.*', tcontent)
    matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent)
    matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent)
    matchobj2 = re.match('.*转.{0,3}评.*', tcontent)
    matchobj3 = re.match('.*本条.*送.*', tcontent)
    matchobj5 = re.match('.*抽.{0,9}送.*', tcontent)
    matchobj10 = re.match('.*钓鱼.*', tcontent)
    matchobj11 = re.match('.*领.*？奖.*', tcontent)
    matchobj23 = re.match('.*关注.*转发.*', tcontent)
    matchobj26 = re.match('.*生日直播.*上舰.*', tcontent)
    matchobj28 = re.match('.*开奖.*恭喜.*获得.*', tcontent)
    matchobj29 = re.match('.*最大贝者场游戏规则公告大家以后要来碰碰运气一定要记住按照最后在碗里可见的卷数为准垫底的卷无效喔快来许愿碰碰运气吧.*', tcontent)
    matchobj30 = re.match('.*恭喜.*获得.*', tcontent)
    matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent)
    matchobj34 = re.match('.*转发抽奖结果.*', tcontent)
    matchobj35 = re.match('.*预约直播.*抽奖', tcontent)
    matchobj36 = re.match('.*开奖啦！.*', tcontent)
    matchobj37 = re.match('.*奖品转送举报人.*', tcontent)
    matchobj38 = re.match('.*来开奖！.*', tcontent)
    matchobj39=re.match('.*200元优惠券.*',tcontent)
    matchobj40=re.match('.*恭喜.*中奖.*',tcontent)
    matchobj42=re.match('.*福利公示.*',tcontent)
    matchobj43 = re.match('.*不抽奖.*', tcontent)
    matchobj44 = re.match('.*求点赞关注转发.*', tcontent)
    matchobj45 = re.match('.*置顶动态抽个元.*', tcontent)
    if (matchobj_37 == None and matchobj_36 == None and matchobj_35 == None and matchobj_34 == None and matchobj_33 == None and matchobj_32 == None and  matchobj_31 == None and matchobj_30 == None and matchobj_29 == None and matchobj_28 == None and matchobj_25 == None and matchobj_24 == None and matchobj_23 == None and matchobj_22 == None and  matchobj_21 == None and matchobj_20 == None and matchobj_19 == None and matchobj_18 == None and matchobj_17 == None and matchobj_16 == None and matchobj_15 == None and matchobj_14 == None and matchobj_13 == None and matchobj_12 == None and matchobj_11 == None and matchobj_10 == None and matchobj_9 == None and matchobj_8 == None and matchobj_7 == None and matchobj_6 == None and matchobj_5 == None and matchobj_4 == None and matchobj_3 == None and matchobj_2 == None and matchobj_1 == None and matchobj == None and matchobj0 == None and matchobj23 == None and matchobj1 == None and matchobj2 == None and matchobj3 == None and matchobj5 == None or matchobj10 != None or matchobj11 != None or matchobj26 != None or matchobj28 != None or matchobj29 != None or matchobj30 != None or matchobj33 != None or matchobj34 != None or matchobj35 != None or matchobj36 != None or matchobj37 != None or matchobj38 != None or matchobj39!=None or matchobj40!=None or matchobj42!=None  or matchobj43!=None or matchobj44!=None or matchobj45!=None):
        return 1
    return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1
def xinxichuli(text):
    global n,timebool, pinglunrenshu
    dongtaineirong=''
    dytime=re.findall(r'"timestamp":(.*?),', text)[0]
    print('\n动态时间'+str(timeshift(dytime)))
    dynamic_id = re.findall(r'"uid":.+?dynamic_id":(.*?),', text)[0]
    uname = re.findall(r'"uname":"(.*?)"', text)[0]
    print('用户名：'+uname)
    repost=re.findall(r'"repost":(.*?),',text)[0]
    fuid = re.findall(r'"uid":(.*?),', text)[0]
    if int(time.time())-int(dytime)>= overtime:
        timebool=False
        print('\t\t\t遇到超时动态\n')
        return 502
    type = re.findall('"uid":.+?type":(\d+?),"rid',text)
    typeif = type[0]
    print('动态type：' + str(typeif))
    if typeif == '1':
        dongtaicontent = re.findall(r'"uid":.+?"type":1.*?content\\": \\"(.*?)\\",', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)
        if pinglunrenshu == [] or pinglunrenshu == ['']:
            pinglunrenshu = 0
        else:
            pinglunrenshu = pinglunrenshu[0]
        print(dongtaineirong)
        print('转发动态或转发视频 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '2':
        dongtaicontent = re.findall(r'"uid":.+?"type":2.*?description\\":\\"(.*?)\\",', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)
        if pinglunrenshu==[] or pinglunrenshu==['']:
            pinglunrenshu=0
        else:pinglunrenshu=pinglunrenshu[0]
        print(dongtaineirong)
        print('带图原创动态 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '4':
        dongtaicontent = re.findall(r'"uid":.+?"type":4,.*?"content\\": \\"(.*?)\\",', text)
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)
        if pinglunrenshu==[] or pinglunrenshu==['']:
            pinglunrenshu=0
        else:pinglunrenshu=pinglunrenshu[0]
        print(dongtaineirong)
        print('不带图的原创动态 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '8':
        dongtaicontent1 = re.findall(r'"uid":.*?"type":8.*?ctime.*?desc\\":\\"(.*?)\\",', text)  # 动态内容
        dongtaicontent2 = re.findall(r'"uid":.*?"type":8.*?ctime.*?desc\\":\\".*?\\".*?dynamic\\":\\"(.*?)\\",', text)
        dongtaicontent = str(dongtaicontent1[0]) + str(dongtaicontent2[0])
        dongtaineirong = ''.join(re.findall('[\u4e00-\u9fa5]+', str(dongtaicontent)))
        print(dongtaineirong)
        print('原创视频 https://t.bilibili.com/' + str(dynamic_id))
        pinglunrenshu = re.findall(r'"reply\\":(.*?),', text)
        if pinglunrenshu==[] or pinglunrenshu==['']:
            pinglunrenshu=0
        else:pinglunrenshu=pinglunrenshu[0]
    elif typeif == '64':
        print('专栏动态 https://t.bilibili.com/' + str(dynamic_id))
        n += 1
        print('第' + str(n) + '次获取动态' + '\n')
        time.sleep(random.choice(sleeptime))
        return 1
    elif typeif == '4308':
        print('直播动态 https://t.bilibili.com/' + str(dynamic_id))
        n += 1
        print('第' + str(n) + '次获取动态' + '\n')
        time.sleep(random.choice(sleeptime))
        return 1
    elif typeif == '2048':
        dongtaicontent = re.findall(r'"uid":.*?"type":2048.*?\\"vest\\".*?"content\\": \\"(.*?)\\"', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)
        if pinglunrenshu==[] or pinglunrenshu==['']:
            pinglunrenshu=0
        else:pinglunrenshu=pinglunrenshu[0]
        print(dongtaineirong)
        print('带简报的动态 https://t.bilibili.com/' + str(dynamic_id))
    if re.match(r'.*\\\\/\\\\/@.*', str(dongtaineirong)) != None:
        dongtaineirong = re.findall(r'(.*?)\\\\/\\\\/@', dongtaineirong)[0]
    if choujiangxinxipanduan(str(dongtaineirong))!=None:
        n += 1
        print('第' + str(n) + '次获取动态')
        print('不含抽奖信息，跳过\n')
        time.sleep(random.choice(sleeptime))
        return 1
    if int(pinglunrenshu) <= pinglunsuoxurenshu:
        n += 1
        print('第' + str(n) + '次获取动态' + '\n')
        time.sleep(random.choice(sleeptime))
        lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
        yuanshipingpinglun.append(lianjie)
        print('假的抽奖：' + str(lianjie) + '\n')
        return -1
    else:
        a.writelines(str(uname)+'\t'+'https://t.bilibili.com/'+str(dynamic_id)+'\t'+repost+'\t'+str(timeshift(dytime))+'\t'+str(dongtaineirong)+'\n')
        zongchoujiang.append(str(uname)+'\t'+'https://t.bilibili.com/'+str(dynamic_id)+'\t'+repost+'\t'+str(timeshift(dytime))+'\t'+str(dongtaineirong)+'\n')
        matchobj001 = re.match('.*转发评论视频.*', str(dongtaineirong))
        matchobj002 = re.match('.*视频评论.*抽.*', str(dongtaineirong))
        matchobj003 = re.match('.*在原视频下.*', str(dongtaineirong))
        matchobj004 = re.match('.*转发.*评论.*弹幕.*视频.*', str(dongtaineirong))
        obj1 = re.match('.*原视频.*', str(dongtaineirong))
        obj2 = re.match('.*在.*视频下.*转.*评.*', str(dongtaineirong))
        obj3 = re.match('.*转发https:\\/\\/.*', str(dongtaineirong))
        obj4=re.match('.*原视频.*评.*抽',str(dongtaineirong))
        obj5=re.match('.*在视频.*抽.*',str(dongtaineirong))
        obj6=re.match('.*点开视频.*评论区.*弹幕.*',str(dongtaineirong))
        obj7=re.match('.*关注+转发+评论以下视频.*',str(dongtaineirong))
        obj8=re.match('.*在视频弹幕区和评论区.*',str(dongtaineirong))
        obj9=re.match('.*原动态.*',str(dongtaineirong))
        obj10=re.match('.*关注.*转发.*评论视频',str(dongtaineirong))
        obj11=re.match('.*来下方动态.*参加抽奖.*',str(dongtaineirong))
        obj12 = re.match('.*参与.*话题互动.*并@.*', str(dongtaineirong))
        obj13 = re.match('.*评论、弹幕、转发.*从中选出.*', str(dongtaineirong))
        obj14 = re.match('.*直播间.*', str(dongtaineirong))
        obj15 = re.match('.*三连里面抽.*', str(dongtaineirong))
        obj16 = re.match('.*转发.*评论.*下方视频.*', str(dongtaineirong))
        obj17 = re.match('.*评论.*弹幕.*', str(dongtaineirong))
        obj18 = re.match('.*点赞最高.*', str(dongtaineirong))
        obj19 = re.match('.*在评论下面.*', str(dongtaineirong))
        obj20 = re.match('.*转关评本专栏文章.*', str(dongtaineirong))
        obj21 = re.match('.*弹幕.*揪.*送.*', str(dongtaineirong))
        obj22 = re.match('.*点赞并评论视频.*', str(dongtaineirong))
        obj23 = re.match('.*弹幕抽.*', str(dongtaineirong))
        if (obj10!=None or obj9!=None or obj8!=None or obj7!=None or obj6!=None or obj5!=None or obj1 != None or obj2 != None or obj3 != None or obj4!=None or matchobj001 != None or matchobj002 != None or matchobj003 != None or matchobj004 != None or obj11!=None or obj12!=None or obj13!=None or obj15!=None or obj16!=None
            or obj17!=None or obj18!=None or obj19!=None or obj20!=None or obj21!=None or obj22!=None or obj23!=None):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            yuanshipingpinglun.append(lianjie)
            print('原视频抽奖：' + str(lianjie) + '\n')
            time.sleep(random.choice(sleeptime))
            return 1
        if (obj14!=None):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            yuanshipingpinglun.append(lianjie)
            print('直播间抽奖：' + str(lianjie) + '\n')
            time.sleep(random.choice(sleeptime))
            return 1
        xiaoliwuobj=re.match('.*香囊.*', str(dongtaineirong))
        xiaoliwuobj1 = re.match('.*vlog套装.*', str(dongtaineirong))
        xiaoliwuobj2 = re.match('.*盲盒.*', str(dongtaineirong))
        xiaoliwuobj3 = re.match('.*狼人杀限量版联名卡牌.*', str(dongtaineirong))
        xiaoliwuobj4 = re.match('.*美的口袋挂脖风扇.*', str(dongtaineirong))
        xiaoliwuobj5 = re.match('.*绿源周边礼品.*', str(dongtaineirong))
        xiaoliwuobj6 = re.match('.*帆布袋.*', str(dongtaineirong))
        xiaoliwuobj7 = re.match('.*点娘十二生肖大礼包.*', str(dongtaineirong))
        xiaoliwuobj8 = re.match('.*一个人的古典.*', str(dongtaineirong))
        xiaoliwuobj9 = re.match('.*周边礼盒.*', str(dongtaineirong))
        xiaoliwuobj10 = re.match('.*航线召唤礼包.*', str(dongtaineirong))
        xiaoliwuobj11 = re.match('.*名校周边大礼包.*', str(dongtaineirong))
        xiaoliwuobj12 = re.match('.*吉祥文化书签一套.*', str(dongtaineirong))
        xiaoliwuobj13 = re.match('.*小招喵抱枕.*', str(dongtaineirong))
        xiaoliwuobj14 = re.match('.*RD定制腰枕.*', str(dongtaineirong))
        xiaoliwuobj15 = re.match('.*可爱果味猫爪杯.*', str(dongtaineirong))
        xiaoliwuobj16 = re.match('.*鹅博士公仔.*', str(dongtaineirong))
        xiaoliwuobj17 = re.match('.*招募令礼包.*', str(dongtaineirong))
        xiaoliwuobj18 = re.match('.*雁翎甲礼包.*', str(dongtaineirong))
        xiaoliwuobj19 = re.match('.*明信片.*', str(dongtaineirong))
        xiaoliwuobj21 = re.match('.*补光灯.*', str(dongtaineirong))
        xiaoliwuobj22 = re.match('.*珍贵影像.*', str(dongtaineirong))
        xiaoliwuobj23 = re.match('.*签名照.*', str(dongtaineirong))
        xiaoliwuobj24 = re.match('.*门票.*', str(dongtaineirong))
        xiaoliwuobj25 = re.match('.*照片.*', str(dongtaineirong))
        xiaoliwuobj26 = re.match('.*玩偶.*', str(dongtaineirong))
        xiaoliwuobj27 = re.match('.*手持小风扇.*', str(dongtaineirong))
        xiaoliwuobj28 = re.match('.*SKG品牌抱枕.*', str(dongtaineirong))
        xiaoliwuobj29 = re.match('.*古茗千里江山图周边.*', str(dongtaineirong))
        xiaoliwuobj30 = re.match('.*讯飞鼠标垫.*', str(dongtaineirong))
        xiaoliwuobj31 = re.match('.*狼人杀卡牌.*', str(dongtaineirong))
        xiaoliwuobj32 = re.match('.*抱枕.*', str(dongtaineirong))
        xiaoliwuobj33 = re.match('.*狼人杀限量版限量礼盒.*', str(dongtaineirong))
        xiaoliwuobj34 = re.match('.*茗茗.*奶茶.*', str(dongtaineirong))
        xiaoliwuobj35 = re.match('.*炎天鼠标垫.*', str(dongtaineirong))
        xiaoliwuobj36 = re.match('.*素乐桌面风扇.*', str(dongtaineirong))
        xiaoliwuobj37 = re.match('.*鹅博士手提袋.*', str(dongtaineirong))
        xiaoliwuobj38 = re.match('.*马克杯.*', str(dongtaineirong))
        xiaoliwuobj39 = re.match('.*蔬菜精灵玩偶抱枕.*', str(dongtaineirong))
        xiaoliwuobj40 = re.match('.*人人视频周边礼包.*', str(dongtaineirong))
        xiaoliwuobj41 = re.match('.*TT周边.*', str(dongtaineirong))
        xiaoliwuobj42 = re.match('.*微泡抱枕.*', str(dongtaineirong))
        xiaoliwuobj43 = re.match('.*七工匠精美周边.*', str(dongtaineirong))
        xiaoliwuobj44 = re.match('.*品牌周边.*', str(dongtaineirong))
        xiaoliwuobj45 = re.match('.*小风扇.*', str(dongtaineirong))
        xiaoliwuobj46 = re.match('.*美的熊小美加油鸭杯.*', str(dongtaineirong))
        xiaoliwuobj47 = re.match('.*小红龙玩偶.*', str(dongtaineirong))
        xiaoliwuobj48 = re.match('.*阴阳师叠叠乐.*', str(dongtaineirong))
        xiaoliwuobj49 = re.match('.*帽子.*', str(dongtaineirong))
        xiaoliwuobj50 = re.match('.*累计视频播放时长排行、视频互动指标排行、动态互动指标排行.*', str(dongtaineirong))
        xiaoliwuobj51 = re.match('.*捞一下明天开.*', str(dongtaineirong))
        if (xiaoliwuobj != None or xiaoliwuobj1 != None or xiaoliwuobj2 != None or xiaoliwuobj3 != None
        or xiaoliwuobj4 != None or xiaoliwuobj5 != None or xiaoliwuobj6 != None or xiaoliwuobj7 != None or xiaoliwuobj8 != None
        or xiaoliwuobj9 != None  or xiaoliwuobj10 != None  or xiaoliwuobj11 != None  or xiaoliwuobj12 != None  or xiaoliwuobj13 != None
        or xiaoliwuobj14 != None  or xiaoliwuobj15!= None  or xiaoliwuobj16 != None  or xiaoliwuobj17 != None  or xiaoliwuobj18 != None
        or xiaoliwuobj19 != None or xiaoliwuobj21 != None or xiaoliwuobj22 != None or xiaoliwuobj23 != None
        or xiaoliwuobj24 != None or xiaoliwuobj25 != None or xiaoliwuobj26 != None or xiaoliwuobj27 != None or xiaoliwuobj28 != None
        or xiaoliwuobj29 != None or xiaoliwuobj30 != None or xiaoliwuobj31 != None or xiaoliwuobj32 != None or xiaoliwuobj33 != None
        or xiaoliwuobj34 != None or xiaoliwuobj35 != None or xiaoliwuobj36 != None or xiaoliwuobj37 != None or xiaoliwuobj38 != None
        or xiaoliwuobj39 != None or xiaoliwuobj40 != None or xiaoliwuobj41 != None or xiaoliwuobj42 != None or xiaoliwuobj43 != None
        or xiaoliwuobj44 != None or xiaoliwuobj45 != None or xiaoliwuobj46 != None or xiaoliwuobj47 != None or xiaoliwuobj48 != None
        or xiaoliwuobj49 != None or xiaoliwuobj50 != None or xiaoliwuobj51 != None
        ):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            xiaoliwu.append(lianjie)
            print('小礼物：' + str(lianjie) + '\n')
            time.sleep(random.choice(sleeptime))
            return 1
        n += 1
        print('https://space.bilibili.com/' + str(fuid) + '\t' + 'https://t.bilibili.com/' + str(dynamic_id) + '\t' + str(dongtaineirong) + '\t')
        return 1
def hashtag(offset,times,topicname,topic_url):
    global shengyupanduan
    ua=random.choice(User_Agent_List)
    spiderurl = 'https://api.vc.bilibili.com/topic_svr/v1/topic_svr/topic_history?topic_name='+str(topic_url)+'&offset_dynamic_id=' + str(
        offset)#+'&sortby=2'#1按时间    2按热度    3按视频动态
    spiderdata = {
        'topic_name': topicname,
        'offset_dynamic_id': offset,
        #'sortby':'2'
    }
    spiderheader = {
        'user - agent':ua
    }
    spiderreq = requests.request('GET', url=spiderurl, headers=spiderheader, data=spiderdata)
    detailtext = re.findall(r'desc":{(.*?),"up_act_button', spiderreq.text)
    print('第' + str(times) + '次获取动态\n' + '此页共' + str(detailtext.__len__()) + '条\n\n')
    if detailtext.__len__() == 0:
        shengyupanduan=False
        return -1
    for i in detailtext:
        if xinxichuli(i)==502:
            return 502
        if n%500==0:
            ua=random.choice(User_Agent_List)
            time.sleep(60)
    time.sleep(random.choice(sleeptime))
    print("\033[1;31;47m\n\n\t\t\t进入下一页\n\n\033[0m")
    offset = re.findall(r'"offset":"(.*?)"', spiderreq.text)[0]
    return offset

timebool=True
shengyupanduan=True
class spidera:
    offset = ''
    times = 1
    a.writelines('\t\t\t互动抽奖tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '互动抽奖', '%E4%BA%92%E5%8A%A8%E6%8A%BD%E5%A5%96')
        if next_offset == 502:
            break
        offset = next_offset
        print('offset=' + str(offset))
        times += 1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t供电局福利社tag\n')
    while True:
        if shengyupanduan!=True:
            break
        if timebool!=True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset=hashtag(offset,times,'供电局福利社','%E4%BE%9B%E7%94%B5%E5%B1%80%E7%A6%8F%E5%88%A9%E7%A4%BE')
        if next_offset==502:
            break
        offset=next_offset
        times+=1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t转发抽奖tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '转发抽奖', '%E8%BD%AC%E5%8F%91%E6%8A%BD%E5%A5%96')
        if next_offset == 502:
            break
        offset = next_offset
        times += 1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t转发+关注抽奖tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '转发+关注抽奖', '%E8%BD%AC%E5%8F%91%2B%E5%85%B3%E6%B3%A8%E6%8A%BD%E5%A5%96')
        if next_offset == 502:
            break
        offset = next_offset
        times += 1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t评论抽奖tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '评论抽奖', '%E8%AF%84%E8%AE%BA%E6%8A%BD%E5%A5%96')
        if next_offset == 502:
            break
        offset = next_offset
        times += 1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t关注抽奖tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '关注抽奖', '%E5%85%B3%E6%B3%A8%E6%8A%BD%E5%A5%96')
        if next_offset == 502:
            break
        offset = next_offset
        times += 1
    offset = ''
    timebool = True
    shengyupanduan = True
    a.writelines('\t\t\t抽奖活动tag\n')
    while True:
        if shengyupanduan != True:
            break
        if timebool != True:
            print('\t\t\t遇到超时动态\n')
            break
        next_offset = hashtag(offset, times, '抽奖活动', '%E6%8A%BD%E5%A5%96%E6%B4%BB%E5%8A%A8')
        if next_offset == 502:
            break
        offset = next_offset
        times += 1
a.close()
print(zongchoujiang.__len__())