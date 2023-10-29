# -*- coding:utf- 8 -*-
import json
import random
import re
import sys
import threading
import time
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
import numpy
import requests

import b站cookie.b站cookie_
import b站cookie.globalvar as gl

cookie1 = gl.get_value('cookie1')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1')
ua1 = gl.get_value('ua1')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
device_id1 = gl.get_value('device_id1')
cookie2 = gl.get_value('cookie2')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
device_id2 = gl.get_value('device_id2')
cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
device_id3 = gl.get_value('device_id3')
cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
device_id4 = gl.get_value('device_id4')
sleeptime = numpy.linspace(5, 7, 500, endpoint=False)


class ciyuanxingqiu:
    def __init__(self):
        self.invite_code = ['9o7owgt2kedol', '2x54gzpaxkgp1w', 'z2wy6e4ea8geow2', '7g4dxmkws5mn18d']

    # 1 2 3 4

    def foodchoose(self, cookie, ua):
        url = 'https://mall.bilibili.com/activity/resident/v2/food/choose'
        foodtype = 'f' + str(random.choice(range(1, 7)))
        print('选取食物：' + foodtype)
        data = {"foodType": foodtype}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        data = json.dumps(data)
        try:
            req = requests.request('POST', url=url, data=data, headers=headers)
            req_dict = req.json()
            print(req_dict.get('message'))
        except:
            print('选取食物失败')
            while 1:
                try:
                    time.sleep(eval(input('输入等待时间')))
                except:
                    print('输入错误')
                    continue
            return 0

    def yaoqingchifan(self, invite_code, cookie, ua):
        time.sleep(random.choice(sleeptime))
        url = 'https://mall.bilibili.com/activity/resident/v2/eat/do'
        data = {"inviteCode": invite_code}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        data = json.dumps(data)
        try:
            req = requests.request('POST', url=url, data=data, headers=headers)
            req_dict = req.json()
        except:
            print('邀请吃饭失败')
            while 1:
                try:
                    time.sleep(eval(input('输入等待时间')))
                except:
                    print('输入错误')
                    continue
            self.yaoqingchifan(invite_code, cookie, ua)
            return 0
        msg = req_dict.get('message')
        print('邀请吃饭结果：')
        if msg == 'SUCCESS':
            try:
                eatresult = req_dict.get('data').get('eatResult')
            except:
                print(req_dict)
                eatresult = {}
                print('邀请吃饭失败')
                while 1:
                    try:
                        time.sleep(eval(input('输入等待时间')))
                        break
                    finally:
                        print('输入错误')
                self.yaoqingchifan(invite_code, cookie, ua)
            try:
                print('邀请恰饭结果：')
                for o, v in eatresult.items():
                    print('{myobj}:{myres}'.format(myobj=o, myres=v))
            except:
                print(eatresult)
        elif msg == '不能和自己吃饭哦':
            print('msg')
        else:
            print(req_dict)

    def suijicengfan(self, cookie, ua):
        while 1:
            print('随机蹭饭中')
            url = 'https://mall.bilibili.com/activity/resident/v2/eat/do'
            time.sleep(random.choice(sleeptime))
            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/json"
            }
            req = requests.request('POST', url=url, headers=headers)
            req_dict = req.json()
            msg = req_dict.get('message')
            if msg == 'SUCCESS':
                try:
                    eatresult = req_dict.get('data').get('eatResult')
                except:
                    print(req_dict)
                    eatresult = {}
                    print('邀请吃饭失败')
                    while 1:
                        try:
                            time.sleep(eval(input('输入等待时间')))
                            break
                        finally:
                            print('输入错误')
                    self.suijicengfan(cookie, ua)
                try:
                    print('随机蹭饭结果：')
                    for o, v in eatresult.items():
                        print('{myobj}:{myres}'.format(myobj=o, myres=v))
                except:
                    print(eatresult)
            elif msg == '今天随机蹭饭次数达上限':
                print(msg)
                break
            else:
                print(req_dict)
                break
            time.sleep(random.choice(sleeptime))

    def sign(self, cookie, ua):
        url = 'https://mall.bilibili.com/activity/resident/v2/sign/reward'
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        try:
            req = requests.request('POST', url=url, headers=headers)
        except:
            print('签到失败')
            return 0
        try:
            print('签到奖励：')
            msg = req.json().get('message')
            if msg == 'SUCCESS':
                prize = req.json().get('data').get('prizeName')
                print(prize)
            elif msg == '今日已签到，记得明天来哦～':
                print(msg)
            else:
                print(req.json())
        except:
            print('签到失败')
            print(req.json())

    def get_task(self, cookie, ua):
        detail = []
        url = 'https://mall.bilibili.com/activity/resident/task-detail'
        headers = {"cookie": cookie,
                   "user-agent": ua
                   }
        req = requests.get(url=url, headers=headers)
        req = json.loads(req.text)
        try:
            data_dict = req.get('data')
            everyDayTaskList = data_dict.get('everyDayTaskList')
            introTask = data_dict.get('inviteEatModule').get('stages')
            newerTaskList = data_dict.get('newerTaskList')
            stages = data_dict.get('powerModule').get('stages')
            detail.append(everyDayTaskList)
            detail.append(introTask)
            detail.append(newerTaskList)
            detail.append(stages)
        except Exception as e:
            print(req)
            print('获取甜心任务失败')
            print(e)
        return detail

    def dispatch(self, cookie, ua, eventid, csrf, jumpurl):
        url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
        data = {"eventId": eventid
            , "csrf": csrf}
        headers = {'cookie': cookie,
                   "Content-Type": "application/json",
                   'user-agent': ua,
                   'origin': 'https://mall.bilibili.com',
                   'referer': jumpurl}
        data = json.dumps(data)
        req = requests.post(url=url, data=data, headers=headers)
        print(req.text)

    def draw_lottery(self, cookie, ua, activityid):
        while 1:
            url = 'https://mall.bilibili.com/activity/lottery/drawLottery'
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua}
            data = {"activityId": activityid
                , "bizInfo": {}}
            data = json.dumps(data)
            req = requests.post(url=url, headers=headers, data=data)
            time.sleep(2)
            try:
                req_dict = json.loads(req.text)
                prizelist = req_dict.get('data').get('prizeInfoDTOList')
                recordid = prizelist[0].get('recordId')
                prizename = prizelist[0].get('prizeName')
                print('奖品名称：{}'.format(prizename))
                # url = 'https://mall.bilibili.com/mall-dayu/mall-marketing-core/lottery_prize/draw_subsidy'
                # data = {"recordId": recordid}
                # data = json.dumps(data)
                # req = requests.post(url=url, data=data, headers=headers)
                # print(req.text)
                if req.json().get('code')!=0:
                    break
            except Exception as e:
                print('抽奖失败')
                print(req.text)
                break


    def receive(self, cookie, ua, fingerprint, prizeid):
        url = 'https://mall.bilibili.com/activity/resident/receive-reward'
        data = {"prizeId": prizeid,
                "deviceId": fingerprint}
        headers = {'cookie': cookie,
                   "Content-Type": "application/json",
                   'user-agent': ua,
                   'Origin': 'https://mall.bilibili.com',
                   'Referer': 'https://mall.bilibili.com/'
                   }
        data = json.dumps(data)
        req = requests.post(url=url, data=data, headers=headers)
        try:
            req = json.loads(req.text)
        except:
            print(req.text)
            print('领取奖励出错')
            return req.text
        return req

    def start(self, cookie, ua, fingerprint, csrf):
        self.sign(cookie, ua)
        time.sleep(random.choice(sleeptime))
        #self.foodchoose(cookie, ua)
        #time.sleep(random.choice(sleeptime))
        self.suijicengfan(cookie, ua)
        time.sleep(random.choice(sleeptime))
        for i in self.invite_code:
            self.yaoqingchifan(i, cookie, ua)
            time.sleep(random.choice(sleeptime))

        task = self.get_task(cookie, ua)
        for i in task:
            for j in i:
                status = j.get('status')
                jumpurl = j.get('jumpUrl')
                taskdesc = j.get('taskDesc')
                prizename = j.get('prizeName')
                buttonText = j.get('buttonText')
                if status == 'GOING' and jumpurl != '' and buttonText == '去浏览':
                    print('浏览现货会场10秒')
                    eventid = re.findall('eventId=(.*?)&', jumpurl)[0]
                    time.sleep(10)
                    self.dispatch(cookie, ua, eventid, csrf, jumpurl)
                    time.sleep(5)
        task = self.get_task(cookie, ua)
        time.sleep(2)
        for i in task:
            for j in i:
                status = j.get('status')
                prizeid = j.get('prizeId')
                if status == 'FINISHED':
                    print(self.receive(cookie, ua, fingerprint, prizeid))
                    time.sleep(3)

        self.draw_lottery(cookie, ua, '2022061431876004')
        time.sleep(5)
        self.draw_lottery(cookie, ua, '2022061431894001')
        time.sleep(5)


class mengwuzhongcao:
    def do_task(self, activityId, cookie, ua, csrf, device_id):
        def login_check(_cookie, ua):
            headers = {
                'User-Agent': ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie, ua)
        task_list = self.get_task(activityId, cookie, ua)
        for t in task_list:
            if t.get('isLocked'):
                continue
            else:
                jumpurl = t.get('jumpUrl')
                for m in t.get('tasks'):
                    if m.get('taskStatus') != 0:
                        continue
                    if not '10秒' in m.get('description') and not '6个' in m.get(
                            'description'):
                        taskid_list = self.get_view_task_id(jumpurl)
                        for i in taskid_list:
                            self.get_and_view(i, cookie, ua, csrf, device_id)
                            time.sleep(random.choice(sleeptime))
                    elif '10秒' in m.get('description'):
                        _jumpurl = m.get('jumpUrl')
                        eventId = re.findall('eventId=(.*?)&', _jumpurl)
                        if eventId:
                            eventId = eventId[0]
                            self.dispatch(cookie, ua, eventId, csrf, _jumpurl)
                        else:
                            print('eventId获取失败')
                            print(_jumpurl)
                    elif '6个' in m.get('description'):
                        _jumpurl = m.get('jumpUrl')

                        def get_cevent_id(a):
                            url = a
                            req = requests.get(url)
                            cEventId = re.findall('cEventId:"(.*?)".', req.text)[0]
                            return cEventId

                        eventId = get_cevent_id(_jumpurl)
                        for i in range(6):
                            self.dispatch(cookie, ua, eventId, csrf, _jumpurl)
                            time.sleep(random.choice(sleeptime))
        task_list = self.get_task(activityId, cookie, ua)
        for t in task_list:
            inner_task = t.get('tasks')
            for i in inner_task:
                if i.get('taskStatus') == 1:
                    print('领取小星星')
                    self.pick_star(activityId, t.get('starId'), i.get('taskId'), csrf, cookie, ua)
                    time.sleep(random.choice(sleeptime))

    def pick_star(self, activityId, starId, taskId, csrf, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/fire/universe/pick-star'
        data = {
            'activityId': activityId,
            'csrf': csrf,
            'starId': starId,
            'taskId': taskId,
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/',
            'content-type': 'application/json',

        }
        req = requests.post(url=url, data=json.dumps(data), headers=headers)
        print(req.json().get('message'))

    def get_view_task_id(self, jumpurl):
        url = jumpurl
        req = requests.get(url=url)
        l = re.findall('activeId:"(.{10})"', req.text, re.S)
        l = list(set(l))
        return l

    def get_task(self, activityId, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/fire/universe/home?activityId={}&_={}'.format(activityId,
                                                                                                    int(time.time()))
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        stars = req.json().get('data').get('stars')
        return stars

    def get_and_view(self, taskid, cookie, ua, csrf, device_id):
        url = 'https://show.bilibili.com/api/activity/index/collect/detailV2?id={taskid}&_={timestp}'.format(
            taskid=taskid, timestp=int(time.time_ns() / 1000000))
        data = {'id': taskid,
                '_': int(time.time_ns() / 1000000)}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        req = requests.request('GET', url=url, data=data, headers=headers)
        viewid = req.json().get('data').get('id')
        taskId = req.json().get('data').get('reward').get('taskId')
        TYPE = req.json().get('data').get('reward').get('type')
        assocId = req.json().get('data').get('reward').get('assocId')
        isReward = req.json().get('data').get('isReward')
        status = req.json().get('data').get('status')
        if not isReward:
            if viewid != '':
                itemlist = req.json().get('data').get('itemList')
                for i in itemlist:
                    itemName = i.get('itemName')
                    print(itemName)
                    isdone = i.get('isDone')
                    if isdone:
                        print(isdone)
                        print('任务已完成')
                        continue
                    print(isdone)
                    itemid = i.get('itemId')
                    self.view(viewid, itemid, cookie, ua)
                    time.sleep(random.choice(sleeptime))
                time.sleep(random.choice(sleeptime))
                url = 'https://show.bilibili.com/api/activity/index/collect/detailV2?id={taskid}&_={timestp}'.format(
                    taskid=taskid, timestp=int(time.time_ns() / 1000000))
                data = {'id': taskid,
                        '_': int(time.time_ns() / 1000000)}
                req = requests.request('GET', url=url, data=data, headers=headers)
                viewid = req.json().get('data').get('id')
                taskId = req.json().get('data').get('reward').get('taskId')
                TYPE = req.json().get('data').get('reward').get('type')
                assocId = req.json().get('data').get('reward').get('assocId')
                isReward = req.json().get('data').get('isReward')
                if taskId and TYPE and assocId:
                    time.sleep(random.choice(sleeptime))
                    self.receive_v3(taskId, TYPE, assocId, csrf, cookie, ua, device_id)
                    time.sleep(random.choice(sleeptime))
                    print('领取奖励成功')
                else:
                    print('领取奖励失败')
                    print(taskid, TYPE, assocId)
                    print(req.json())
                    print('\n\n')
            elif status == 'wait':
                print('正在等待中的任务')
                print(taskid)
            else:
                print('viewid出错')
                print(taskid)
                print(req.text)
        else:
            print('奖励已领取')

    def receive_v3(self, taskId, TYPE, assocId, csrf, cookie, ua, device_id):
        url = 'https://show.bilibili.com/api/activity/index/reward/receiveV3?_={}'.format(
            int(time.time_ns() / pow(10, 6)))
        data = {
            'taskId': taskId,
            'type': TYPE,
            'assocId': assocId,
            'deviceId': device_id,
            'csrf': csrf,
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.post(url=url, headers=headers, data=data)
        print(req.text)
        return req.json()

    def view(self, viewid, itemid, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/index/collect/view?id={viewid}%3D&itemId={itemid}&_={timestp}'.format(
            viewid=viewid, itemid=itemid, timestp=int(time.time_ns() / 1000000) - 10)
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        data = {
            'id': viewid,
            'itemId': itemid,
            '_': int(time.time_ns() / 1000000) - 10
        }
        data = json.dumps(data)
        req = requests.request('GET', url=url, data=data, headers=headers)
        print(req.text)

    def dispatch(self, cookie, ua, eventid, csrf, jumpurl):
        url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
        data = {"eventId": eventid
            , "csrf": csrf}
        headers = {'cookie': cookie,
                   "Content-Type": "application/json",
                   'user-agent': ua,
                   'origin': 'https://mall.bilibili.com',
                   'referer': jumpurl}
        data = json.dumps(data)
        req = requests.post(url=url, data=data, headers=headers)
        print(req.text)


class suipian:
    def get_egg(self, csrf, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/index/share/egg'
        data = {
            'id': "yqgp8wu7q6",
            'csrf': csrf
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))
        data = {
            'id': "90ydykf204",
            'csrf': csrf
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))
        data = {
            'id': "z05xpxfory",
            'csrf': csrf
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))
        data = {
            'id': "xqkd93u3r9",
            'csrf': csrf
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))
        data = {
            'id': "dqz1x5clrx",
            'csrf': csrf
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))
        data = {
            'id': "er8l74axq7",
            'csrf': csrf
        }
        req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
        print(req.json())
        time.sleep(random.choice(sleeptime))




# class dianliang:
#     def dispatch(self, cookie, ua, eventid, csrf, jumpurl):
#         url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
#         data = {"eventId": eventid
#             , "csrf": csrf}
#         headers = {'cookie': cookie,
#                    "Content-Type": "application/json",
#                    'user-agent': ua,
#                    'origin': 'https://mall.bilibili.com',
#                    'referer': jumpurl}
#         data = json.dumps(data)
#         req = requests.post(url=url, data=data, headers=headers)
#         print(req.text)
#
#     def get_task_detail(self,cookie,ua):
#         url='https://mall.bilibili.com/activity/lighten/home/detail?_t={}&activityId=lit_oedd471g5omv'.format(int(time.time()*1000))
#         headers={
#             'cookie':cookie,
#             'user-agent':ua
#         }
#         req=requests.get(url,headers=headers)
#         return req.json()
#
#     def share_light(self,cookie,ua):


if __name__ == '__main__':
    print('浏览任务：')
    liulan = mengwuzhongcao()
    for e in range(2, 5):
        eval('liulan.do_task("2022626prod", cookie{n}, ua{n}, csrf{n}, device_id{n})'.format(n=e))

    print('星球主任务：')
    xq = ciyuanxingqiu()
    for e in range(2, 5):
        eval('xq.start(cookie{n},ua{n},fingerprint{n},csrf{n})'.format(n=e))

    print('看商品任务：')
    url_list = ['https://mall.bilibili.com/act/aicms/3iaa6fvpSp.html', ]
    for u in url_list:
        myli = liulan.get_view_task_id(u)
        for myta in myli:
            for s in range(2, 5):
                eval('liulan.get_and_view(myta, cookie{z}, ua{z}, csrf{z}, device_id{z})'.format(z=s))
                time.sleep(random.choice(sleeptime))

#https://mall.bilibili.com/xw/birthday-card/home/index.html?activityId=lit_oedd471g5omv&noTitleBar=1&inviteCode=lpl48o7oh3g6ljksx&share_source=weibo&share_medium=h5&bbid=&ts=1655516611138
