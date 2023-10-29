# -*- coding:utf- 8 -*-
import requests
import re
import random
import time
def timeshift():
    inttime=re.search('\d+',str(time.time()))
    local_time=time.localtime(int(inttime.group()))
    realtime=time.strftime('%Y-%m-%d %H:%M:%S',local_time)
    return realtime
print(timeshift())
page=[2,3,4,5]#动态评论页面
yuzancishu=3#遇到点赞次数后停止
pinglunzhuanbiancishu=5
pinglunsuoxurenshu=30#动态下评论人数
uid=1905702375
global zhuanpingdongtaicishu
zhuanpingdongtaicishu=0
xiaoliwu=[]
sleeptime=[2]
csrf='03c7d35e2356c18331aab9c2cd366fcc'#填入自己的csrf
cookie="SESSDATA=39711a5b%2C1642327077%2C2fa6d*71;bili_jct=03c7d35e2356c18331aab9c2cd366fcc"
typelist=268435455
useragent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
fakeuseragent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
url='https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid='+str(uid)+'&type_list='+str(typelist)+'&from=weball&platform=web'
replycontent=['[原神_欸嘿]','[原神_喝茶]','好耶','来了','蹭蹭','冲鸭','来了来了','贴贴','冲','[原神_哼]','[原神_嗯][原神_哇][原神_哼]','[原神_哇][原神_哼]','[原神_哇]']
header = {"cookie": cookie,
          "user-agent": useragent
          }
f=open('非官方抽奖动态.csv','w',encoding='utf-8')
p=open('oid变化得动态.csv','w',encoding='utf-8')
q=open('原视频下方评论.csv','w',encoding='utf-8')
r=open('无需转发.csv','w',encoding='utf-8')
commentf=open('评论相关.csv','w',encoding='utf-8')
xiaowanyi=open('小礼物.csv','w',encoding='utf-8')
f.writelines('发布者uid'+'\t'+'动态链接'+'\t'+'动态内容''\n')
def huifuneirong(content,detail,_type):#回复内容的判断
    MAX = page.__len__() - 1
    ctype = 17
    if str(_type) == '8':
        ctype = 1
    elif str(_type) == '4' or str(_type) == '1':
        ctype = 17
    elif str(_type) == '2':
        ctype = 11
    elif str(_type) == '64':
        ctype = 12
    while True:
        pn = page[MAX]
        rid = re.findall('"card":{"desc":{"uid":.*?"rid":(.*?),', detail)[0]
        dynamid = re.findall(r'"desc":{"uid":.+?dynamic_id":(.*?),"timestamp', detail)[0]
        if len(rid)==len(dynamid):
            oid=dynamid
        else:oid = rid
        pinglunheader = {
            'user-agent':fakeuseragent}
        pinglunurl = 'https://api.bilibili.com/x/v2/reply/main?next=' + str(pn) + '&type=' + str(ctype) + '&oid=' + str(oid) + '&mode=3&plat=1&_=' + str(time.time())
        pinglundata = {
            'jsonp': 'jsonp',
            'next': pn,
            'type': ctype,
            'oid': oid,
            'mode': 3,
            'plat': 1,
            '_': time.time()
        }
        pinglunreq = requests.request("GET", url=pinglunurl, data=pinglundata, headers=pinglunheader)
        if pinglunreq.text!='{"code":-404,"message":"啥都木有","ttl":1}':
            pinglunreq1 = ''.join(re.findall(r'{"code":0,"message":"0","ttl":1,"data":(.*),"top":', pinglunreq.text)[0])
            pinglun=re.findall(r'"root":0.*?"content":{"message":"(.*?)"',pinglunreq1)
        else:
            print('获取评论失败')
        if pinglun != []:
            if pinglun!=[]:
                for i in range(pinglunzhuanbiancishu):
                    msg = random.choice(pinglun)
                    msg=eval(repr(msg).replace('\\\\', '\\'))
                    biaoqingbao = re.findall('(?<=\[)(.*?)(?=\])',msg)
                    if biaoqingbao!=[]:
                        tihuanbiaoqing=panduanbiaoqingbao(biaoqingbao)
                        if tihuanbiaoqing != []:
                            changyongemo=['doge','脱单doge','妙啊','吃瓜','嗑瓜子','tv_doge']
                            for noemo in tihuanbiaoqing:
                                msg = msg.replace(noemo, random.choice(changyongemo))
                    print('抄的评论：'+msg)
                    return msg
        if pinglun==[]:
            print('获取评论为空\t评论类型：'+str(ctype))
        MAX-=1
        time.sleep(random.choice(sleeptime))
        if MAX<0:
            break
    mobj_6=re.match('.*七夕.*',content)
    mobj_5=re.match('.*许愿格式：有趣的愿望+愿望实现城市！.*',content)
    mobj_4 = re.match('.*带话题 #.*#.*', content)
    mobj_2=re.match('.*带话题  #.*#.*',content)
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
    if mobj_6!=None:
        msg='浪漫七夕'
        return msg
    if mobj_5!=None:
        msg='中个大奖 上海'
        return msg
    if mobj_4!=None:
        msg = re.findall(r'带话题 #(.*?)#', content)
        msg1 = '#' + str(msg[0]) + '#'
        return msg1
    if mobj_2!=None:
        msg = re.findall(r'带话题  #(.*?)#', content)
        msg1 = '#' + str(msg[0]) + '#'
        return msg1
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
        msglist=['奥迪双钻，我的伙伴[doge]','老板大气']
        return random.choice(msglist)
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
def panduanbiaoqingbao(emo):
    hasemo = ['12周年', '藏狐', 'doge', '微笑', 'OK', '星星眼', '妙啊', '辣眼睛', '吃瓜', '滑稽', '喜欢', '嘟嘟', '给心心', '笑哭', '脱单doge',
              '嗑瓜子', '调皮', '歪嘴', '打call', '呲牙', '酸了', '哦呼', '嫌弃', '大哭', '害羞', '疑惑', '喜极而泣', '奸笑', '笑', '偷笑', '点赞', '无语',
              '惊喜', '大笑', '抠鼻', '呆', '囧', '阴险', '捂脸', '惊讶', '鼓掌', '尴尬', '灵魂出窍', '委屈', '傲娇', '疼', '冷', '生病', '吓', '吐',
              '撇嘴', '难过', '墨镜', '奋斗', '哈欠', '翻白眼', '再见', '思考', '嘘声', '捂眼', '抓狂', '生气', '口罩', '牛年', '2021', '水稻', '福到了',
              '鸡腿', '雪花', '视频卫星', '拥抱', '支持', '保佑', '响指', '抱拳', '加油', '胜利', '锦鲤', '爱心', '干杯', '跪了', '跪了', '怪我咯', '黑洞',
              '老鼠', '来古-沉思', '来古-呆滞', '来古-疑问', '来古-震撼', '来古-注意', '哭泣', '原神_嗯', '原神_哼', '原神_哇', '高兴', '气愤', '耍帅', '亲亲',
              '羞羞', '狗子', '哈哈', '原神_欸嘿', '原神_喝茶', '原神_生气', '热词系列_河南加油', '热词系列_豫你一起', '热词系列_仙人指路', '热词系列_饮茶先啦',
              '热词系列_知识增加', '热词系列_再来亿遍', '热词系列_好耶', '热词系列_你币有了', '热词系列_吹爆', '热词系列_妙啊', '热词系列_你细品', '热词系列_咕咕',
              '热词系列_标准结局', '热词系列_张三', '热词系列_害', '热词系列_问号', '热词系列_奥力给', '热词系列_猛男必看', '热词系列_有内味了', '热词系列_我裂开了',
              '热词系列_我哭了', '热词系列_高产', '热词系列_不愧是你', '热词系列_真香', '热词系列_我全都要', '热词系列_神仙UP', '热词系列_锤', '热词系列_秀', '热词系列_爷关更',
              '热词系列_我酸了', '热词系列_大师球', '热词系列_完结撒花', '热词系列_我太南了', '热词系列_镇站之宝', '热词系列_有生之年', '热词系列_知识盲区', '热词系列_“狼火”',
              '热词系列_你可真星', 'tv_白眼', 'tv_doge', 'tv_坏笑', 'tv_难过', 'tv_生气', 'tv_委屈', 'tv_斜眼笑', 'tv_呆', 'tv_发怒', 'tv_惊吓',
              'tv_笑哭', 'tv_亲亲', 'tv_调皮', 'tv_抠鼻', 'tv_鼓掌', 'tv_大哭', 'tv_疑问', 'tv_微笑', 'tv_思考', 'tv_呕吐', 'tv_晕', 'tv_点赞',
              'tv_害羞', 'tv_睡着', 'tv_色', 'tv_吐血', 'tv_无奈', 'tv_再见', 'tv_流汗', 'tv_偷笑', 'tv_发财', 'tv_可爱', 'tv_馋', 'tv_腼腆',
              'tv_鄙视', 'tv_闭嘴', 'tv_打脸', 'tv_困', 'tv_黑人问号', 'tv_抓狂', 'tv_生病', 'tv_流鼻血', 'tv_尴尬', 'tv_大佬', 'tv_流泪',
              'tv_冷漠', 'tv_皱眉', 'tv_鬼脸', 'tv_调侃', 'tv_目瞪口呆','坎公骑冠剑_吃鸡','坎公骑冠剑_钻石','坎公骑冠剑_无语','热词系列_不孤鸟','热词系列_对象']
    tihuanbiaoqing = []
    for biaoqing in emo:
        if (biaoqing not in hasemo):
            tihuanbiaoqing.append(biaoqing)
    return tihuanbiaoqing
def choujiangxinxipanduan(tcontent):  # 动态内容过滤条件
    matchobj_44 = re.match('.*揪.{0,10}小可爱.*每人.*', tcontent)
    matchobj_43 = re.match('.*#抽奖#.*关注.*抽.*', tcontent)
    matchobj_42 = re.match('.*关注.*平论.*揪.*打.*', tcontent)
    matchobj_41 = re.match('.*转发.*评论.*关注.*抽.*获得.*', tcontent)
    matchobj_40 = re.match('.*关注.*转发.*点赞.*揪.*送.*', tcontent)
    matchobj_39 = re.match('.*转发评论点赞本条动态.*送.*', tcontent)
    matchobj_38 = re.match('.*挑选.*评论.*送出.*', tcontent)
    matchobj_37 = re.match('.*弹幕抽.*送.*', tcontent)
    matchobj_36 = re.match('.*随机.*位小伙伴.*现金红包.*', tcontent)
    matchobj_34 = re.match('.*评论.*随机.*抽.*', tcontent)
    matchobj_33 = re.match('.*评论.*随机.*抓.*', tcontent)
    matchobj_32 = re.match('.*参与方式.*转发.*关注.*评论.*', tcontent)
    matchobj_31 = re.match('.*评论.*随机.*抓.*', tcontent)
    matchobj_30 = re.match('.*评论.*随机.*抽.*补贴.*', tcontent)
    matchobj_29 = re.match('.*评论区.*揪.*送.*', tcontent)
    matchobj_28 = re.match('.*转发.*评论.*揪.*送.*', tcontent)
    matchobj_27 = re.match('.*互动抽奖.*', tcontent)
    matchobj_26 = re.match('.*#供电局福利社#.*', tcontent)
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
    matchobj_10 = re.match('.*揪.{0,10}送', tcontent)
    matchobj_9 = re.match('.*转发.*揪.*送.*', tcontent)
    matchobj_8 = re.match('.*评论.*关注.*揪', tcontent)
    matchobj_7 = re.match('.*评论.*关注.*抽.*', tcontent)
    matchobj_6 = re.match('.*评论区.{0,9}送.*', tcontent)
    matchobj_5 = re.match('.*转.*评.*送.*鲨鲨酱抱枕.*', tcontent)
    matchobj_4 = re.match('.*转发.*揪.*', tcontent)
    matchobj_3 = re.match('.*揪.*送.*', tcontent)
    matchobj_2 = re.match('.*评论区{0,9}抽.*', tcontent)
    matchobj_1 = re.match('.*卷发.*关注.*', tcontent)
    matchobj = re.match('.*转发.*送.*', tcontent)
    matchobj0 = re.match('.*转发.{0,30}抽.*', tcontent)
    matchobj1 = re.match('.*关注.{0,7}抽.*', tcontent)
    matchobj2 = re.match('.*转.{0,3}评.*', tcontent)
    matchobj3 = re.match('.*本条.*送.*', tcontent)
    matchobj5 = re.match('.*抽.{3,7}送.*', tcontent)
    matchobj10 = re.match('.*钓鱼.*', tcontent)
    matchobj11 = re.match('.*领.*？奖.*', tcontent)
    matchobj23 = re.match('.*关注.*转发.*抽.*送.*', tcontent)
    matchobj26 = re.match('.*生日直播.*上舰.*', tcontent)
    matchobj28 = re.match('.*开奖.*恭喜.*获得.*', tcontent)
    matchobj29 = re.match('.*最大贝者场游戏规则公告大家以后要来碰碰运气一定要记住按照最后在碗里可见的卷数为准垫底的卷无效喔快来许愿碰碰运气吧.*', tcontent)
    matchobj30 = re.match('.*恭喜.*获得.*', tcontent)
    matchobj33 = re.match('.*快快点击传送门一起抽大奖！！.*', tcontent)
    matchobj34 = re.match('.*转发抽奖结果.*', tcontent)
    matchobj36 = re.match('.*开奖啦！.*', tcontent)
    matchobj37 = re.match('.*奖品转送举报人.*', tcontent)
    matchobj38 = re.match('.*来开奖！.*', tcontent)
    matchobj39=re.match('.*200元优惠券.*',tcontent)
    matchobj40=re.match('.*恭喜.*中奖.*',tcontent)
    matchobj42=re.match('.*福利公示.*',tcontent)
    matchobj43 = re.match('.*不抽奖.*', tcontent)
    matchobj44 = re.match('.*求点赞关注转发.*', tcontent)
    matchobj45 = re.match('.*置顶动态抽个元.*', tcontent)
    matchobj46 = re.match('.*开奖.*祝贺.*获得.*', tcontent)
    if (matchobj_44 == None and matchobj_43 == None and matchobj_42 == None and matchobj_41 == None and matchobj_40 == None and matchobj_39 == None and matchobj_38 == None and matchobj_37 == None and matchobj_36 == None
        and matchobj_34 == None and matchobj_33 == None and matchobj_32 == None and  matchobj_31 == None
        and matchobj_30 == None and matchobj_29 == None and matchobj_28 == None and matchobj_27 == None
        and matchobj_26 == None and matchobj_25 == None and matchobj_24 == None and matchobj_23 == None
        and matchobj_22 == None and  matchobj_21 == None and matchobj_20 == None and matchobj_19 == None
        and matchobj_18 == None and matchobj_17 == None and matchobj_16 == None and matchobj_15 == None
        and matchobj_14 == None and matchobj_13 == None and matchobj_12 == None and matchobj_11 == None
        and matchobj_10 == None and matchobj_9 == None and matchobj_8 == None and matchobj_7 == None
        and matchobj_6 == None and matchobj_5 == None and matchobj_4 == None and matchobj_3 == None
        and matchobj_2 == None and matchobj_1 == None and matchobj == None and matchobj0 == None
        and matchobj23 == None and matchobj1 == None and matchobj2 == None and matchobj3 == None
        and matchobj5 == None or matchobj10 != None or matchobj11 != None or matchobj26 != None
        or matchobj28 != None or matchobj29 != None or matchobj30 != None or matchobj33 != None
        or matchobj34 != None or matchobj36 != None or matchobj37 != None
        or matchobj38 != None or matchobj39!=None or matchobj40!=None or matchobj42!=None
        or matchobj43!=None or matchobj44!=None or matchobj45!=None or matchobj46!=None):
        return 1
    return None  # 抽奖信息判断      是抽奖返回None 不是抽奖返回1
choujiangdongtai=[]
global end
global oidcuowu
dianzanshibai=[]
oidcuowu=[]
end=0
yuanshipingpinglun=[]
global n
n=0
wuxuzhuanfa=[]
def get_dynamic_detail(dy):
    dyurl = 'http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id=' + str(dy)
    dyreq=requests.request('GET',dyurl,headers=header,data={"dynamic_id":str(dy)})
    return dyreq.text
def thumb(dynamic_ID):#为动态点赞标记
    thumbheader={
    'authority': 'api.vc.bilibili.com',
    'method': 'POST',
    'cookie':"SESSDATA=39711a5b%2C1642327077%2C2fa6d*71;bili_jct=03c7d35e2356c18331aab9c2cd366fcc",
    'user-agent':useragent
    }
    thumbdata={
        'uid': uid,
        'dynamic_id': dynamic_ID,
        'up': '1',
        'csrf_token': csrf,
        'csrf': csrf
    }
    thumburl='https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb'
    reqthumb=requests.request('POST',url=thumburl,data=thumbdata,headers=thumbheader)
    if(reqthumb.text)=='{"code":0,"msg":"","message":"","data":{"_gt_":0}}':
        print('点赞成功')
    else:
        print('点赞失败')
        lianjie='https://t.bilibili.com/'+str(dynamic_ID)
        dianzanshibai.append((lianjie))
def comment(dy,msg,type,detail):#发送评论
    global oidcuowu
    rid=re.findall('{"desc":{"uid":.*?rid":(\d+),', detail)[0]
    if len(rid)==len(dy):
        oid=dy
    else:oid=rid
    commentheader = {
        'authority': 'api.bilibili.com',
        'method': 'POST',
        'path': '/x/v2/reply/add',
        'scheme': 'https',
        'accept': 'application / json, text / javascript, * / *; q = 0.01',
        'cookie': "SESSDATA=39711a5b%2C1642327077%2C2fa6d*71;bili_jct=03c7d35e2356c18331aab9c2cd366fcc",
        'user-agent':useragent
    }
    ctype=17
    if type=='8':
        ctype=1
    elif type=='4' or type=='1':
        ctype=17
    elif type=='2':
        ctype=11
    commentdata = {
            'oid': oid,
            'type': ctype,
            'message': msg,
            'ordering': 'time',
            'jsonp': 'jsonp',
            'plat': '1',
            'csrf': csrf,
            }
    commenturl='https://api.bilibili.com/x/v2/reply/add'
    reqcomment=requests.request('POST',commenturl,data=commentdata,headers=commentheader)
    commentresult=re.findall('success_toast":"(.*?)","need_captcha"',reqcomment.text)
    if commentresult==[''] or commentresult==[]:
        cuowuid='https://t.bilibili.com/'+str(dy)
        oidcuowu.append(cuowuid)
        print('评论失败\noid变化： https://t.bilibili.com/'+str(dy))
    print('评论动态结果：'+str(commentresult)+'评论类型：'+str(ctype))
def repost(dy,msg):
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
    reposturl = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/reply'
    reqrepost = requests.request('POST', reposturl, headers=header, data=repostdata)
    repostresult = re.findall('errmsg":"(.*?),"dynamic_id"', reqrepost.text)
    print('转发动态结果：' + str(repostresult))
def xinxichuli(text):
    global end, n, zhuanpingdongtaicishu,wuxuzhuanfa
    dongtaineirong=''
    dynamic_id = re.findall(r'"desc":{"uid":.+?dynamic_id":(.*?),', text)[0]
    thumbtype = re.findall(r'"desc":.*"is_liked":(.+?),"dynamic_id', text)
    thumbstatus=thumbtype[0]
    fuid = re.findall(r'"desc":{"uid":(.*?),', text)[0]
    type = re.findall('"desc":{"uid":.+?type":(\d+?),"rid',text)
    typeif = type[0]
    print('动态type：' + str(typeif))
    if typeif == '1':
        dongtaicontent = re.findall(r'"desc":{"uid":.+?"type":1.*?content\\": \\"(.*?)\\",', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)[0]
        print(dongtaineirong)
        print('转发动态或转发视频 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '2':
        dongtaicontent = re.findall(r'"desc":{"uid":.+?"type":2.*?description\\":\\"(.*?)\\",', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)[0]
        print(dongtaineirong)
        print('带图原创动态 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '4':
        dongtaicontent = re.findall(r'"desc":{"uid":.+?"type":4,.*?"content\\": \\"(.*?)\\",', text)
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)[0]
        print(dongtaineirong)
        print('不带图的原创动态 https://t.bilibili.com/' + str(dynamic_id))
    elif typeif == '8':
        dongtaicontent1 = re.findall(r'"desc":{"uid":.*?"type":8.*?ctime.*?desc\\":\\"(.*?)\\",', text)  # 动态内容
        dongtaicontent2 = re.findall(r'"desc":{"uid":.*?"type":8.*?ctime.*?desc\\":\\".*?\\".*?dynamic\\":\\"(.*?)\\",', text)
        dongtaicontent = str(dongtaicontent1[0]) + str(dongtaicontent2[0])
        dongtaineirong = ''.join(re.findall('[\u4e00-\u9fa5]+', str(dongtaicontent)))
        print(dongtaineirong)
        print('原创视频 https://t.bilibili.com/' + str(dynamic_id))
        pinglunrenshu = re.findall(r'"reply\\":(.*?),', text)[0]
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
        dongtaicontent = re.findall(r'"desc":{"uid":.*?"type":2048.*?\\"vest\\".*?"content\\": \\"(.*?)\\"', text)  # 动态内容
        dongtaineirong = ''.join(str(dongtaicontent[0]))
        pinglunrenshu = re.findall(r'comment":(.*?),"', text)[0]
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
    if thumbstatus == '1':
        end += 1
        n += 1
        print('第' + str(n) + '次获取动态' + '\n')
        print('第'+str(end)+'遇到点过赞的动态' + dynamic_id + '\n')
        time.sleep(random.choice(sleeptime))
        return -1
    if int(pinglunrenshu) <= pinglunsuoxurenshu:
        n += 1
        print('第' + str(n) + '次获取动态' + '\n')
        time.sleep(random.choice(sleeptime))
        lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
        yuanshipingpinglun.append(lianjie)
        print('原视频抽奖：' + str(lianjie) + '\n')
        q.writelines(lianjie + '\n')
        return -1
    else:
        matchobj000 = re.match('.*直播抽奖.*', str(dongtaineirong))
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
        obj24 = re.match('.*视频.*一键三连.*抽.*', str(dongtaineirong))
        obj25 = re.match('.*关注.*转发.*评论.*本视频.*', str(dongtaineirong))
        obj26 = re.match('.*下方视频.*抽.*送.*', str(dongtaineirong))
        obj27 = re.match('.*视频.*一键三连.*', str(dongtaineirong))
        obj28 = re.match('.*置顶动态.*抽奖.*', str(dongtaineirong))
        obj29 = re.match('.*三连.*转发.*', str(dongtaineirong))
        obj30 = re.match('.*点击下方动态链接.*抽奖.*', str(dongtaineirong))
        obj31 = re.match('.*视频.*的评论底下.*揪.*', str(dongtaineirong))
        if (obj10!=None or obj9!=None or obj8!=None or obj7!=None or obj6!=None or obj5!=None or obj1 != None or
            obj2 != None or obj3 != None or obj4!=None or matchobj001 != None or matchobj002 != None or matchobj003 != None
            or matchobj004 != None or obj11!=None or obj12!=None or obj13!=None or obj15!=None or obj16!=None
            or obj17!=None or obj18!=None or obj19!=None or obj20!=None or obj21!=None or obj22!=None or obj23!=None
            or obj24 != None or obj25 != None or obj26 != None or obj27 != None or obj28 != None or obj29 != None
            or obj30 != None or obj31 != None
        ):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            yuanshipingpinglun.append(lianjie)
            print('原视频抽奖：' + str(lianjie) + '\n')
            q.writelines(lianjie + '\n')
            time.sleep(random.choice(sleeptime))
            return 1
        if (obj14!=None or matchobj000!=None):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            yuanshipingpinglun.append(lianjie)
            print('直播间抽奖：' + str(lianjie) + '\n')
            q.writelines(lianjie + '\n')
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
        xiaoliwuobj52 = re.match('.*新衣福袋.*', str(dongtaineirong))
        xiaoliwuobj53 = re.match('.*小米静态积木飞鱼座穿梭器.*', str(dongtaineirong))
        xiaoliwuobj54 = re.match('.*茗千里江山图周边.*', str(dongtaineirong))
        xiaoliwuobj55 = re.match('.*公仔.*', str(dongtaineirong))
        xiaoliwuobj56 = re.match('.*KiWi EV限定徽章.*', str(dongtaineirong))
        xiaoliwuobj57 = re.match('.*南光周边.*', str(dongtaineirong))
        xiaoliwuobj58 = re.match('.*超好用.*手机支架.*', str(dongtaineirong))
        xiaoliwuobj60 = re.match('.*「芬达」周边礼包.*', str(dongtaineirong))
        xiaoliwuobj61 = re.match('.*帆软周边.*', str(dongtaineirong))
        xiaoliwuobj62 = re.match('.*百闻牌挂画.*', str(dongtaineirong))
        xiaoliwuobj63 = re.match('.*长腿风筝.*', str(dongtaineirong))
        xiaoliwuobj64 = re.match('.*DMZJ限量法披.*', str(dongtaineirong))
        xiaoliwuobj65 = re.match('.*命题小作文.*', str(dongtaineirong))
        xiaoliwuobj66 = re.match('.*车模.*', str(dongtaineirong))
        xiaoliwuobj67 = re.match('.*小蓝×脉动联名周边三件套.*', str(dongtaineirong))
        xiaoliwuobj68 = re.match('.*特斯拉神秘手稿.*', str(dongtaineirong))
        xiaoliwuobj69 = re.match('.*吉祥文化书签.*', str(dongtaineirong))
        xiaoliwuobj70 = re.match('.*0元半鸡兑换券.*', str(dongtaineirong))
        xiaoliwuobj71 = re.match('.*古龙香水.*', str(dongtaineirong))
        xiaoliwuobj72 = re.match('.*求职打气包.*', str(dongtaineirong))
        xiaoliwuobj73 = re.match('.*春秋航空机模.*', str(dongtaineirong))
        xiaoliwuobj74 = re.match('.*九霄环佩.*', str(dongtaineirong))
        xiaoliwuobj75 = re.match('.*转发赠书.*', str(dongtaineirong))
        xiaoliwuobj76 = re.match('.*牛蒙蒙运动周边.*', str(dongtaineirong))
        xiaoliwuobj77 = re.match('.*香皂.*', str(dongtaineirong))
        xiaoliwuobj78 = re.match('.*拯救者电竞手机x狼人杀联名卡牌.*', str(dongtaineirong))
        xiaoliwuobj79 = re.match('.*数码宝贝食玩.*', str(dongtaineirong))
        xiaoliwuobj80 = re.match('.*都市时报周边.*', str(dongtaineirong))
        xiaoliwuobj81 = re.match('.*飞机模型.*', str(dongtaineirong))
        xiaoliwuobj82 = re.match('.*浩瀚周边礼包.*', str(dongtaineirong))
        xiaoliwuobj83 = re.match('.*派乐礼盒.*', str(dongtaineirong))
        xiaoliwuobj84 = re.match('.*七工匠周边.*', str(dongtaineirong))
        if (xiaoliwuobj != None or xiaoliwuobj1 != None or xiaoliwuobj2 != None or xiaoliwuobj3 != None
        or xiaoliwuobj4 != None or xiaoliwuobj5 != None or xiaoliwuobj6 != None or xiaoliwuobj7 != None or xiaoliwuobj8 != None
        or xiaoliwuobj9 != None or xiaoliwuobj10 != None or xiaoliwuobj11 != None or xiaoliwuobj12 != None or xiaoliwuobj13 != None
        or xiaoliwuobj14 != None or xiaoliwuobj15!= None or xiaoliwuobj16 != None or xiaoliwuobj17 != None or xiaoliwuobj18 != None
        or xiaoliwuobj19 != None or xiaoliwuobj21 != None or xiaoliwuobj22 != None or xiaoliwuobj23 != None or xiaoliwuobj24 != None
        or xiaoliwuobj25 != None or xiaoliwuobj26 != None or xiaoliwuobj27 != None or xiaoliwuobj28 != None or xiaoliwuobj29 != None
        or xiaoliwuobj30 != None or xiaoliwuobj31 != None or xiaoliwuobj32 != None or xiaoliwuobj33 != None or xiaoliwuobj34 != None
        or xiaoliwuobj35 != None or xiaoliwuobj36 != None or xiaoliwuobj37 != None or xiaoliwuobj38 != None or xiaoliwuobj39 != None
        or xiaoliwuobj40 != None or xiaoliwuobj41 != None or xiaoliwuobj42 != None or xiaoliwuobj43 != None or xiaoliwuobj44 != None
        or xiaoliwuobj45 != None or xiaoliwuobj46 != None or xiaoliwuobj47 != None or xiaoliwuobj48 != None or xiaoliwuobj49 != None
        or xiaoliwuobj50 != None or xiaoliwuobj51 != None or xiaoliwuobj52 != None or xiaoliwuobj53 != None or xiaoliwuobj54 != None
        or xiaoliwuobj55 != None or xiaoliwuobj56 != None or xiaoliwuobj57 != None or xiaoliwuobj58 != None
        or xiaoliwuobj60 != None or xiaoliwuobj61 != None or xiaoliwuobj62 != None or xiaoliwuobj63 != None or xiaoliwuobj64 != None
        or xiaoliwuobj65 != None or xiaoliwuobj66 != None or xiaoliwuobj67 != None or xiaoliwuobj68 != None or xiaoliwuobj69 != None
        or xiaoliwuobj70 != None or xiaoliwuobj71 != None or xiaoliwuobj72 != None or xiaoliwuobj73 != None or xiaoliwuobj74 != None
        or xiaoliwuobj75 != None or xiaoliwuobj76 != None or xiaoliwuobj77 != None or xiaoliwuobj78 != None or xiaoliwuobj79 != None
        or xiaoliwuobj80 != None or xiaoliwuobj81 != None or xiaoliwuobj82 != None or xiaoliwuobj83 != None or xiaoliwuobj84 != None


        ):
            n += 1
            print('第' + str(n) + '次获取动态')
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            xiaoliwu.append(lianjie)
            print('小礼物：' + str(lianjie) + '\n')
            xiaowanyi.writelines(lianjie +'\t'+ str(dongtaineirong)+'\n')
            time.sleep(random.choice(sleeptime))
            return 1
        n += 1
        print('https://space.bilibili.com/' + str(fuid) + '\t' + 'https://t.bilibili.com/' + str(dynamic_id) + '\t' + str(dongtaineirong) + '\t')
        f.writelines('https://space.bilibili.com/' + str(fuid) + '\t' + 'https://t.bilibili.com/' + str(dynamic_id) + '\t' + str(dongtaineirong) + '\t' + '\n')
        time.sleep(random.choice(sleeptime))
        msg = huifuneirong(str(dongtaineirong),text,typeif)
        print('回复转发内容：' + str(msg))
        comment(dynamic_id, msg, typeif, text)
        commentf.writelines('https://t.bilibili.com/'+str(dynamic_id)+'\t'+str(msg)+'\t'+str(dongtaineirong)+'\n')
        time.sleep(random.choice(sleeptime))
        zhuanfapanduan1 = re.match('.*转发.*', str(dongtaineirong))
        zhuanfapanduan2 = re.match('.*卷发.*', str(dongtaineirong))
        zhuanfapanduan3 = re.match('.*转.*', str(dongtaineirong))
        if (zhuanfapanduan1 != None or zhuanfapanduan2 != None or zhuanfapanduan3 != None):
            repost(dynamic_id, msg)
        else:
            print('无需转发：https://t.bilibili.com/' + str(dynamic_id))
            lianjie = 'https://t.bilibili.com/' + str(dynamic_id)
            wuxuzhuanfa.append(lianjie)
            r.writelines(str(lianjie))
        time.sleep(random.choice(sleeptime))
        thumb(dynamic_id)
        choujianglianjie='https://t.bilibili.com/'+str(dynamic_id)
        choujiangdongtai.append(choujianglianjie)
        zhuanpingdongtaicishu+=1
        print('\n')
        time.sleep(random.choice(sleeptime))
        return 1

class start:
    xunhuancishu=1
    a=1
    while True:
        if xunhuancishu>=10:
            print('\n\t\t已经循环十遍，继续请按1,退出随便按\n')
            a=input()
            xunhuancishu=1
        if a!=1:
            break
        dongtaidata = {
            'uid': uid,
            'type_list': typelist,
            'from': 'weball',
            'platform': 'web',
        }
        req = requests.request("GET", url=url, data=dongtaidata, headers=header)
        offset = re.findall(r'"history_offset":(.*?)"', req.text)[0]
        dynamic_id = re.findall(r'"desc":{"uid":.+?dynamic_id":(.*?),"timestamp', req.text)
        print('此页共有'+str(dynamic_id.__len__())+'条动态')
        for dynamic in dynamic_id:
            dydetail=get_dynamic_detail(dynamic)
            xinxichuli(dydetail)
        while True:
            if end>yuzancishu or end==yuzancishu:
                print('到达指定遇赞次数，结束')
                break
            offseturl = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid=' + str(
                uid) + '&offset_dynamic_id=' + offset + '&type=' + str(typelist) + '&from=weball&platform=web'
            offsetdata = {
                'uid': uid,
                'offset_dynamic_id': str(offset),
                'type': typelist,
                'from': 'weball',
                'platform': 'web'
            }
            req = requests.request("GET", url=offseturl, data=offsetdata, headers=header)
            offset = re.findall(r'"next_offset":(.*?),"', req.text)[0]
            print('\n\n\n' + 'next_offset:' + offset)
            dynamic_id = re.findall(r'"desc":{"uid":.+?dynamic_id":(.*?),"timestamp', req.text)
            print('此页共有' + str(dynamic_id.__len__()) + '条动态')
            for dynamic in dynamic_id:
                dydetail = get_dynamic_detail(dynamic)
                xinxichuli(dydetail)
                if n%500==0:
                    print('到达500条休息30秒\n\n\n\n\n')
                    time.sleep(30)
        print('共有'+str(choujiangdongtai.__len__())+'条非官方抽奖动态')
        print(choujiangdongtai)
        print('评论失败：'+str(oidcuowu))
        print('原视频抽奖：')
        print(yuanshipingpinglun)
        print('点赞失败：')
        print(dianzanshibai)
        print('总转发评论数：'+str(zhuanpingdongtaicishu))
        p.writelines(oidcuowu)
        print('小东西：'+str(xiaoliwu))
        print('无需转发：'+str(wuxuzhuanfa)+'\n\n\n\n\n\n')
        time.sleep(600)
        xunhuancishu+=1
f.close()
xiaowanyi.close()
p.close()
q.close()
r.close()
commentf.close()