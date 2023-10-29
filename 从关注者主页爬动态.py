# -*- coding:utf- 8 -*-
import time
import re
import requests
import random
global uid
jiangeshijian=86400*1.5
uid=1905702375             #填入自己的uid
csrf='03c7d35e2356c18331aab9c2cd366fcc'#填入自己的csrf
cookie="497E01B3-E062-B3A8-4AE1-B3683F4FFE7683211infoc; buvid3=220C5F13-6424-4BD0-8872-4B40887E6C1E148807infoc; sid=awdnjday; fingerprint=380d542bb0d17199fb0d6ab6680e23e8; buvid_fp=220C5F13-6424-4BD0-8872-4B40887E6C1E148807infoc; buvid_fp_plain=220C5F13-6424-4BD0-8872-4B40887E6C1E148807infoc; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; SESSDATA=39711a5b%2C1642327077%2C2fa6d*71; bili_jct=03c7d35e2356c18331aab9c2cd366fcc; fingerprint3=2dc893b3ef15c8936026c78127d69b52; fingerprint_s=43748e5e8f5d67b1590069d6d48d559e; bp_t_offset_1905702375=549485772118562055; LIVE_BUVID=AUTO7616267760598581; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(J|)kmuY)uY0J'uYkY~)|uJk; bfe_id=1e33d9ad1cb29251013800c68af42315; PVID=13"
#填入自己的cookie
yuanshipingpinglun=[]
global allfollowing
global headers
global dongtaistamptime
global oidcuowu
oidcuowu=[]
choujiangdongtai=[]
replycontent=['[原神_欸嘿]','[原神_喝茶]','好耶','来了','蹭蹭','冲鸭','来了来了','贴贴','冲','[原神_哼]','转发动态','[原神_嗯][原神_哇][原神_哼]','[原神_哇][原神_哼]','[原神_哇]']#评论内容
f=open('非官方抽奖动态'+str(time.time())+'.csv','w',encoding='utf-8')
p=open('oid变化得动态'+str(time.time())+'.csv','w',encoding='utf-8')
q=open('原视频下方评论'+str(time.time())+'.csv','w',encoding='utf-8')
f.writelines('发布者uid'+'\t'+'动态链接'+'\t'+'动态内容'+'\t'+'发布时间'+'\n')
def huifuneirong(content):#回复内容的判断
    mobj_1=re.match('.*评论#.*#.*',content)
    mobj = re.match('.*在评论区打出#.*#.*', content)
    mobj1=re.match('.*评论区刷#.*#.*',content)
    mobj2=re.match('.*带tag#.*#.*',content)
    mobj3=re.match('.*带话题#.*#.*',content)
    mobj4=re.match('.*带#.*#.*',content)
    mobj5=re.match('.*为.*加油.*',content)
    mobj6=re.match('.*随机数方式抽取到.*',content)
    mobj7=re.match('.*评论话题#.*#.*',content)
    mobj8=re.match('.*奥迪双钻AULDEY.*',content)
    mobj9=re.match('.*说说.*计划.*',content)
    mobj10=re.match('.*预告.*',content)
    mobj11=re.match('.*长按复制这条信息.*',content)
    mobj12=re.match('.*把.*打在评论区.*',content)
    mobj13=re.match('.*华为.*系列.*',content)
    mobj14=re.match('.*生日祝福.*',content)
    if mobj_1!=None:
        msg=re.findall(r'评论#(.*?)#，', content)
        msg1='#'+str(msg[0])+'#'
        return msg1
    if mobj != None:
        msg = re.findall(r'在评论区打出#(.*?)#，', content)
        msg1='#'+str(msg[0])+'#'
        return msg1
    if mobj1!=None:
        msg=re.findall(r'评论区刷#(.*?)#，',content)
        msg1=msg[0]
        return msg1
    if mobj2!=None:
        msg=re.findall(r'带tag#(.*?)#',content)
        msg1='#'+str(msg[0])+'#'
        return msg1
    if mobj3!=None:
        msg = re.findall(r'带话题#(.*?)#', content)
        msg1 = '#' + str(msg[0]) + '#'
        return msg1
    if mobj4!=None:
        msg=re.findall(r'带#(.*?)#', content)
        msg1='#' + str(msg[0]) + '#'
        return msg1
    if mobj7!=None:
        msg = re.findall(r'评论话题#(.*?)#', content)
        msg1 = '#' + str(msg[0]) + '#'
        return msg1
    if mobj14!=None:
        msg='生日快乐！'
        return msg
    if mobj5 != None:
        msg = '加油！'
        return msg
    if mobj6 != None:
        msg = '恭喜'
        return msg
    if mobj8!=None:
        msglist=['奥迪双钻，我的伙伴[doge]','拉低中奖率']
        return random.choise(msglist)
    if mobj9!=None:
        msg='宅家'
        return msg
    if mobj10!=None:
        msg='期待[星星眼]'
        return msg
    if mobj11!=None:
        msglist1=['买了买了','太划算啦','确实挺便宜','有点心动']
        msg=random.choice(msglist1)
        return msg
    if mobj12!=None:
        msg=re.findall(r'把(.*)打在评论区',content)
        msg1=str(msg[0])
        return msg1
    if mobj13!=None:
        msg='华为加油！'
        return msg
    else:
        msg=random.choice(replycontent)
        return msg
def choujiangxinxipanduan(tcontent):#动态内容过滤条件
    matchobj_3=re.match('.*揪.*送.*',tcontent)
    matchobj_2=re.match('.*评论区.*抽.*',tcontent)
    matchobj_1=re.match('.*卷发.*关注.*',tcontent)
    matchobj=re.match('.*转发.*送.*',tcontent)
    matchobj0=re.match('.*转发.*抽.*',tcontent)
    matchobj1=re.match('.*关.*抽.*',tcontent)
    matchobj2 = re.match('.*转.{0,3}评.*', tcontent)
    matchobj3 = re.match('.*本条.*送.*', tcontent)
    matchobj5=re.match('.*抽.*送.*',tcontent)
    matchobj6=re.match('.*照片.*',tcontent)
    matchobj7=re.match('.*签名照.*',tcontent)
    matchobj8=re.match('.*玩偶.*',tcontent)
    matchobj9=re.match('.*机器人.*',tcontent)
    matchobj10=re.match('.*钓鱼.*',tcontent)
    matchobj11=re.match('.*领.*？奖.*',tcontent)
    matchobj12=re.match('.*直播间.*',tcontent)
    matchobj13=re.match('.*门票.*',tcontent)
    matchobj14=re.match('.*电影票.*',tcontent)
    matchobj15 = re.match('.*抱枕.*', tcontent)
    matchobj16=re.match('.*评论前.*',tcontent)
    matchobj17=re.match('.*公仔.*',tcontent)
    matchobj18=re.match('.*面膜.*',tcontent)
    matchobj19=re.match('.*补光灯.*',tcontent)
    matchobj20=re.match('.*珍贵影像.*',tcontent)
    matchobj23 = re.match('.*关注.*转发.*', tcontent)
    matchobj24=re.match('.*签名照.*',tcontent)
    matchobj26=re.match('.*生日直播.*上舰.*',tcontent)
    matchobj27=re.match('.*明信片.*',tcontent)
    matchobj28=re.match('.*开奖.*恭喜.*获得.*',tcontent)
    if (matchobj_3==None and matchobj_2==None and matchobj_1==None and matchobj==None and matchobj0 ==None and matchobj23==None and matchobj1==None and matchobj2==None and matchobj3==None and matchobj5==None or matchobj6!=None or matchobj7!=None or matchobj8!=None or matchobj9!=None or matchobj10!=None or matchobj11!=None or matchobj12!=None or matchobj13!=None or matchobj14!=None or matchobj15!=None or matchobj16!=None or matchobj17!=None or matchobj18!=None or matchobj19!=None or matchobj20!=None or matchobj24!=None or matchobj26!=None or matchobj27!=None or matchobj28!=None):
        return 1
    return None#抽奖信息判断      是抽奖返回None 不是抽奖返回1
def get_dynamic_detail(dy):
    dyurl = 'http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id=' + str(dy)
    dyreq=requests.request('GET',dyurl,headers=headers1,data={"dynamic_id":str(dy)})
    return dyreq.text
def thumbstatus(dydetail):#查询点赞状态，点过的返回1，没点过的返回0
    thumbtype=re.findall(r'"desc":.*"is_liked":(.+?),"dynamic_id',dydetail)
    print(thumbtype)
    thumbtype=thumbtype[0]
    if thumbtype=='1':
        print('已点赞的动态')
    else:print('未点赞的动态')
    return thumbtype
def thumb(dynamic_ID):#为动态点赞标记
    thumbdata={
        'uid': uid,
        'dynamic_id': dynamic_ID,
        'up': '1',
        'csrf_token': csrf,
        'csrf': csrf
    }
    thumburl='https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb'
    reqthumb=requests.request('POST',url=thumburl,data=thumbdata,headers=headers1)
    print(reqthumb.text)
    if(reqthumb.text)=='{"code":0,"msg":"","message":"","data":{"_gt_":0}}':
        print('点赞成功')
    else:
        print('点赞失败')
def comment(dy,msg,type,detail):#发送评论
    global oidcuowu
    commentheader = {
        'authority': 'api.bilibili.com',
        'method': 'POST',
        'path': '/x/v2/reply/add',
        'scheme': 'https',
        'accept': 'application / json, text / javascript, * / *; q = 0.01',
        'cookie': cookie,
        'user - agent': 'Mozilla / 5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 91.0.4472.164Safari / 537.36'
    }
    ctype=17
    rid=dy
    if type==8:
        ctype=1
    elif type==4 or type==1:
        ctype=17
    elif type==2:
        ctype=11
    commentdata = {
            'oid': rid,
            'type': ctype,
            'message': msg,
            'ordering': 'heat',
            'jsonp': 'jsonp',
            'plat': '1',
            'csrf': csrf,
            }
    commenturl='https://api.bilibili.com/x/v2/reply/add'
    reqcomment=requests.request('POST',commenturl,data=commentdata,headers=commentheader)
    commentresult=re.findall('success_toast":"(.*?)","need_captcha"',reqcomment.text)
    if commentresult[0] == '':
        rid=re.findall('{"desc":{"uid":.*?rid":(\d+)', detail)
        if rid!=[]:
            rid=rid[0]
            commentdata = {
                'oid': rid,
                'type': ctype,
                'message': msg,
                'ordering': 'heat',
                'jsonp': 'jsonp',
                'plat': '1',
                'csrf': csrf,
            }
            commenturl = 'https://api.bilibili.com/x/v2/reply/add'
            reqcomment = requests.request('POST', commenturl, data=commentdata, headers=commentheader)
            commentresult = re.findall('success_toast":"(.*?)","need_captcha"', reqcomment.text)
    if commentresult[0]=='':
        cuowuid='https://t.bilibili.com/'+str(dy)
        oidcuowu.append(cuowuid)
        print('oid变化')
    print('评论动态结果：'+str(commentresult)+'评论类型：'+str(ctype))
def repost(dy,msg):
    repostdata={
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
    reposturl='https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/reply'
    reqrepost=requests.request('POST',reposturl,headers=headers1,data=repostdata)
    repostresult = re.findall('errmsg":"(.*?),"dynamic_id"', reqrepost.text)
    print('转发动态结果：'+str(repostresult))
headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}
headers1={"cookie": cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
         }
data={

}
class getfollowings:
    global allfollowing
    allfollowing=[]
    url1='https://api.bilibili.com/x/relation/stat?vmid='+str(uid)+'&jsonp=jsonp'
    req0=requests.request('GET',url1,headers=headers,data=data)
    followings=re.findall(r'"following":(.+?),"whisper":0,',req0.text)
    fnumber=re.search('\d+', str(followings)).group()
    print (fnumber)
    page=int(int(fnumber)/20)+1
    for x in range(1,page+1):
        uniqueheader={
        'authority': 'api.bilibili.com',
        'method': 'GET',
        'path': '/ x / relation / followings?vmid = uid & pn = '+str(x)+' & ps = 20 & order = desc & order_type = attention & jsonp = jsonp',
        'scheme': 'https',
        'accept': 'text / html, application / xhtml + xml, application / xml;q = 0.9, image / avif, image / webp, image / apng, * / *;q = 0.8, application / signed - exchange;v = b3;q = 0.9',
        'accept - encoding': 'gzip, deflate, br',
        'accept - language': 'zh - CN, zh;q = 0.9',
        'cookie': cookie,
        'sec - ch - ua': '" Not;A Brand";v = "99", "Google Chrome";v = "91", "Chromium";v = "91"',
        'sec - ch - ua - mobile': '?0',
        'sec - fetch - dest': 'document',
        'sec - fetch - mode': 'navigate',
        'sec - fetch - site': 'none',
        'sec - fetch - user': '?1',
        'upgrade - insecure - requests': '1',
        'user - agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 91.0.4472.164Safari / 537.36'
        }
        url2='https://api.bilibili.com/x/relation/followings?vmid='+str(uid)+'&pn='+str(x)+'&ps=20&order=desc&order_type=attention&jsonp=jsonp'
        fdata = {
        'vmid': uid,
        'pn': x,
        'ps': '20',
        'order': 'desc',
        'order_type': 'attention',
        'jsonp': 'jsonp'
        }
        req1=requests.request('GET',url2,headers=uniqueheader,data=fdata)
        followinguid= re.findall(r'"mid":(.*?),"attribute":',req1.text)
        allfollowing=followinguid+allfollowing
        time.sleep(1)
    print('共获取'+str(allfollowing.__len__())+'个关注uid')
class jianchadongtai:
    n=0
    for fuid in allfollowing:
        offset = '0'
        shijianpanduan = False
        while True:
            if shijianpanduan:
                print('遇到超时动态，进入下一个关注者')
                time.sleep(3)
                break
            dongtaidata = {
                'visitor_uid': uid,
                'host_uid': fuid,
                'offset_dynamic_id': offset,
                'need_top': '0',
                'platform': 'web'
            }
            url1 = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=' + str(uid) + '&host_uid=' + str(fuid) + '&offset_dynamic_id='+str(offset)+'&need_top=0'
            req1 = requests.request('GET', url1, headers=headers, data=dongtaidata)
            if req1.text=='{"code":500003,"msg":"请求数据发生错误，请刷新或稍后重试","message":"请求数据发生错误，请刷新或稍后重试","data":{}}':
                print('请求数据发生错误')
                time.sleep(5)
                break
            type=re.findall('"desc":{"uid":.+?type":(\d+?),"rid',req1.text)
            type1num=0
            type2num=0
            type4num=0
            type8num=0
            next_offset = re.findall(r'"next_offset":(.*?),"_gt_":', req1.text)
            offset = 'str(next_offset[0])'
            for i in range(0,type.__len__()):
                typeif=type[i]
                print('动态type：'+str(typeif))
                if typeif=='1':
                    dongtaicontent = re.findall(r'"desc":{"uid":.+?"type":1.*?content\\": \\"(.*?)\\"', req1.text)  # 动态内容
                    dongtaineirong=dongtaicontent[type1num]
                    print(dongtaineirong)
                    type1num+=1
                    print('转发动态或转发视频')
                elif typeif=='2':
                    dongtaicontent = re.findall(r'"desc":{"uid":.+?"type":2.*?description\\":\\"(.*?)\\"', req1.text)  # 动态内容
                    dongtaineirong = dongtaicontent[type2num]
                    print(dongtaineirong)
                    type2num+=1
                    print('带图原创动态')
                elif typeif=='4':
                    dongtaicontent=re.findall(r'"desc":{"uid":.+?"type":4,.*?"content\\": \\"(.*?)\\"',req1.text)
                    dongtaineirong=dongtaicontent[type4num]
                    print(dongtaineirong)
                    type4num+=1
                    print('不带图的原创动态')
                elif typeif=='8':
                    dongtaicontent=re.findall(r'"desc":{"uid":.+?"type":8.*?ctime.*?desc\\":\\"(.*?)\\"',req1.text)# 动态内容
                    dongtaineirong =''.join(re.findall('[\u4e00-\u9fa5]',str(dongtaicontent[type8num])))
                    print(dongtaineirong)
                    type8num+=1
                    print('原创视频')
                elif typeif=='64':
                    print('专栏动态')
                    n+=1
                    print('第' + str(n) + '次获取动态')
                    continue
                elif typeif=='4308':
                    print('直播动态')
                    n+=1
                    print('第' + str(n) + '次获取动态')
                dynamic_id=re.findall(r'"desc":{"uid":.*?dynamic_id":(.*?),"timestamp', req1.text)
                dydetail=get_dynamic_detail(dynamic_id[i])
                print('https://t.bilibili.com/'+str(dynamic_id[i]))
                if thumbstatus(dydetail)=='1':
                    print('已点赞标记，跳过')
                    shijianpanduan=True
                    break
                dongtaishijian = re.findall(r'dynamic_id":.+?,"timestamp":(\d+?),"', dydetail)
                dongtaistamptime = dongtaishijian[0]
                inttime = re.search('\d+', str(dongtaishijian[0]))
                local_time = time.localtime(int(inttime.group()))
                realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)#发布时间
                shijianpanduan=(int(time.time())-int(dongtaistamptime)>int(jiangeshijian))#时间判断
                if shijianpanduan:
                    n+= 1
                    print('第' + str(n) + '次获取动态')
                    print('超时动态')
                    shijianpanduan = True
                    break
                if re.match(r'.*\\\\/\\\\/.*', str(dongtaineirong))!=None:
                    dongtaineirong = re.findall(r'(.*?)\\\\/\\\\/', dongtaineirong)[0]
                if choujiangxinxipanduan(str(dongtaineirong)):
                    n += 1
                    print('第' + str(n) + '次获取动态')
                    print('不含抽奖信息，跳过')
                    time.sleep(1)
                    continue
                else:
                    matchobj001 = re.match('.*转发评论视频.*', str(dongtaineirong))
                    matchobj002= re.match('.*视频评论.*抽.*', str(dongtaineirong))
                    matchobj003=re.match('.*在原视频下.*',str(dongtaineirong))
                    matchobj004=re.match('.*转发.*评论.*弹幕.*视频.*',str(dongtaineirong))
                    obj1=re.match('.*原视频.*',str(dongtaineirong))
                    obj2=re.match('.*在.*视频下.*转.*评.*',str(dongtaineirong))
                    obj3=re.match('.*转发https:\\/\\/.*',str(dongtaineirong))
                    if (matchobj001!=None or matchobj002!=None or matchobj003!=None or matchobj004!= None):
                        n += 1
                        print('第' + str(n) + '次获取动态')
                        print('不含抽奖信息，跳过')
                        time.sleep(1)
                        lianjie='https://t.bilibili.com/'+str(dynamic_id[i])
                        yuanshipingpinglun.append(lianjie)
                        print('原视频抽奖：'+str(yuanshipingpinglun))
                        q.writelines(lianjie+'\n')
                        continue
                    n+=1
                    print ('第'+str(n)+'次获取动态')
                    print('https://space.bilibili.com/'+str(fuid)+'\t'+'https://t.bilibili.com/'+str(dynamic_id[i])+'\t'+str(dongtaineirong)+'\t'+str(realtime))
                    f.writelines('https://space.bilibili.com/'+str(fuid)+'\t'+'https://t.bilibili.com/'+str(dynamic_id[i])+'\t'+str(dongtaineirong)+'\t'+str(realtime)+'\n')
                    time.sleep(1)
                    msg=huifuneirong(str(dongtaineirong))
                    print('回复转发内容：'+str(msg))
                    comment(dynamic_id[i],msg,typeif,dydetail)
                    time.sleep(0.1)
                    repost(dynamic_id[i],msg)
                    choujiangdongtai.append(dynamic_id[i])
                    time.sleep(1)
                    thumb(dynamic_id[i])
                    time.sleep(2)
            time.sleep(1)
f.close()
print(choujiangdongtai)
print('共有'+str(choujiangdongtai.__len__())+'条非官方抽奖动态')
print('oid改变：'+str(oidcuowu))
print('原视频抽奖：')
print(yuanshipingpinglun)
p.writelines(oidcuowu)
p.close()
q.close()