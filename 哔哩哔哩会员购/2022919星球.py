# -*- coding:utf- 8 -*-
import json
import random
import re
import sys
import threading
import time
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
from pprint import pprint

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


def get_eventID(_taskId, __cookie, __ua):
    _url = f'https://show.bilibili.com/api/activity/hercules/task/report-detail?taskId={_taskId}&_={int(time.time_ns() * 1000)}'
    headers = {
        'user-agent': __ua,
        'cookie': __cookie
    }
    req = requests.get(_url, headers=headers)
    if req.json().get('code') == 0:
        if req.json().get('data').get('eventId'):
            return req.json().get('data').get('eventId')
        else:
            print('获取eventid失败')
            req.json().get('data').get('eventId')
    else:
        print('获取eventid失败')
        pprint(req.json())


class ciyuanxingqiu:
    def __init__(self):
        self.invite_code = ['9w1ykz5z', '6w6qno5', 'nge614pr', 'jnqn5p']

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

    def yaoqingjiaru(self, invite_code, cookie, ua):
        time.sleep(random.choice(sleeptime))
        url = 'https://mall.bilibili.com/activity/resident/v3/help/do'
        data = {
            'token': invite_code
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        data = json.dumps(data)
        req = requests.request('post', url=url, data=data, headers=headers)
        req_dict = req.json()
        msg = req_dict.get('message')
        print('邀请加入结果：')
        if msg == 'SUCCESS':
            print(msg)
            # print(req_dict)
        if req_dict.get('code') == 800505001:
            print(msg)
        if req_dict.get('code') == 8004070101:
            print(msg)
        else:
            print('未知结果')
            print(req_dict)

    def roll_touzi(self, cookie, ua):
        def get_latticeId():
            u = 'https://mall.bilibili.com/activity/resident/v3/home'
            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/json",
                'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/',
                'accept': 'application/json, text/plain, */*'
            }
            _req = requests.get(url=u, headers=headers)
            try:
                _req.json().get('data').get('richManModule').get('nowLatticeId')
            except:
                print(_req.json())
            return _req.json().get('data').get('richManModule').get('nowLatticeId')

        while 1:
            print('roll骰子')
            url = 'https://mall.bilibili.com/activity/resident/v3/rich-man/roll'
            time.sleep(random.choice(sleeptime))
            latticeid = get_latticeId()
            data = {'latticeId': latticeid}
            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/json",
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/',
            }
            req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
            req_dict = req.json()
            msg = req_dict.get('message')
            if msg == 'SUCCESS':
                print('roll骰子成功')

            elif req_dict.get('code') == 83110054:
                print(msg)
                break
            else:
                print(data)
                pprint(req_dict)
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

    def self_grow(self, cookie, ua):
        url = 'https://mall.bilibili.com/activity/resident/v3/hanabi/self-grow'
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json",
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/',
        }
        req = requests.post(url=url, headers=headers)
        print(req.json())

    def get_task(self, cookie, ua):
        detail = []
        url = 'https://mall.bilibili.com/activity/resident/task-detail'
        headers = {"cookie": cookie,
                   "user-agent": ua,
                   'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/'
                   }
        req = requests.get(url=url, headers=headers)
        req = json.loads(req.text)
        try:
            data_dict = req.get('data')
            everyDayTaskList = data_dict.get('everyDayTaskList')
            introTask = data_dict.get('inviteJoinModule').get('stages')
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
                if req.json().get('code') != 0:
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

    def share_callback(self, cookie, ua):
        print('分享活动')
        url = 'https://mall.bilibili.com/activity/resident/task/share-callback'
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json",
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/',
        }
        req = requests.get(url=url, headers=headers)
        print(req.json())

    def check_login(self, cookie, ua):
        url = 'https://mall.bilibili.com/activity/resident/v3/check-login'
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json",
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/zq/starpartying-2022919/',
        }
        req = requests.get(url=url, headers=headers)
        print(req.json())

    def start(self, cookie, ua, fingerprint, csrf):
        self.check_login(cookie, ua)
        self.sign(cookie, ua)
        self.share_callback(cookie, ua)
        time.sleep(random.choice(sleeptime))
        # self.foodchoose(cookie, ua)
        # time.sleep(random.choice(sleeptime))
        for i in self.invite_code:
            self.yaoqingjiaru(i, cookie, ua)
            time.sleep(random.choice(sleeptime))

        task = self.get_task(cookie, ua)
        print('开始做日常任务')
        pprint(task)
        for i in task:
            # detail.append(everyDayTaskList)
            # detail.append(introTask)
            # detail.append(newerTaskList)
            # detail.append(stages)
            for j in i:
                status = j.get('status')
                jumpurl = j.get('jumpUrl')
                taskdesc = j.get('taskDesc')
                prizename = j.get('prizeName')
                buttonText = j.get('buttonText')
                taskId = j.get('taskId')
                if status == 'GOING' and jumpurl != '' and buttonText == '去完成':
                    print(taskdesc)
                    eventid = get_eventID(taskId, cookie, ua)
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

        print('收取里程数')
        self.self_grow(cookie, ua)

        self.roll_touzi(cookie, ua)
        time.sleep(random.choice(sleeptime))

        self.draw_lottery(cookie, ua, '2022092332060004')
        time.sleep(5)
        self.draw_lottery(cookie, ua, '2022092232075002')
        time.sleep(5)


class mengwuzhongcao:
    '''
    萌物种草外加星球浏览
    '''

    def do_task(self, activityId, cookie, ua, csrf, device_id):
        task_list = self.get_task(activityId, cookie, ua)
        for t in task_list:
            if t.get('isLocked'):
                continue
            else:
                jumpurl = t.get('jumpUrl')
                for m in t.get('tasks'):
                    if m.get('taskStatus') != 0:
                        print('已完成')
                        continue
                    print(f"当前任务：{m.get('description')}")
                    if not '10秒' in m.get('description') and not '6个' in m.get(
                            'description'):
                        taskid_list = self.get_view_task_id(jumpurl)
                        for i in taskid_list:
                            self.get_and_view(i, cookie, ua, csrf, device_id)
                            time.sleep(random.choice(sleeptime))
                    elif '10秒' in m.get('description'):
                        _jumpurl = m.get('jumpUrl')
                        taskId = m.get('taskId')
                        eventId = get_eventID(taskId, cookie, ua)
                        if eventId:
                            self.dispatch(cookie, ua, eventId, csrf, _jumpurl)
                        else:
                            print('eventId获取失败')
                            print(eventId)
                    elif '6个' in m.get('description'):
                        _jumpurl = m.get('jumpUrl')

                        def get_cevent_id(a):
                            req = requests.get(a)
                            cEventId = re.findall('"cEventId":"(.*?)"', req.text)[0]
                            return cEventId

                        eventId = get_cevent_id(_jumpurl)
                        if eventId:
                            for i in range(6):
                                self.dispatch(cookie, ua, eventId, csrf, _jumpurl)
                                time.sleep(random.choice(sleeptime))
                        else:
                            print('eventId获取失败')
                            print(eventId)
        task_list = self.get_task(activityId, cookie, ua)
        for t in task_list:
            inner_task = t.get('tasks')
            for i in inner_task:
                if i.get('taskStatus') == 1:
                    print('领取小星星')
                    self.pick_star(activityId, t.get('starId'), i.get('taskId'), csrf, cookie, ua)
                    time.sleep(random.choice(sleeptime))

    def pick_star(self, activityId, starId, taskId, csrf, cookie, ua):
        url = 'https://mall.bilibili.com/activity/universe/v2/pick-star'
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
        l = re.findall('"activeId":"(.{10})"', req.text, re.S)
        l = list(set(l))
        return l

    def get_task(self, activityId, cookie, ua):
        url = 'https://mall.bilibili.com/activity/universe/v2/home?activityId={}&_={}'.format(activityId,
                                                                                              int(time.time()))
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        task_list = []
        brandStars = req.json().get('data').get('brandStars')
        dimensionStars = req.json().get('data').get('dimensionStars')
        task_list.extend(brandStars)
        task_list.extend(dimensionStars)
        return task_list

    def get_and_view(self, taskid, cookie, ua, csrf, device_id):
        def login_check(_cookie, _ua):
            _headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            _url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=_url, headers=_headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie, ua)
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
            elif status == 'end':
                print('已结束任务')
            else:
                print('viewid出错')
                print(taskid)
                pprint(req.json())
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
        if req.json().get('code') == 0:
            print('任务完成')
        else:
            pprint(req.json())


class suipian:
    def get_egg(self, csrf, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/index/share/egg'
        egg_id_list = ['xrv2zka3q3', 'lrl9o6t9r1', '20jjo4fw03']
        for id in egg_id_list:
            data = {
                'id': id,
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
    thread_task_list = []
    liulan = mengwuzhongcao()

    print('看商品任务：')
    # https://mall.bilibili.com/act/aicms/j6K887T55X.html
    url_list = [
        'https://mall.bilibili.com/act/aicms/j6K887T55X.html',
        'https://mall.bilibili.com/act/aicms/vJBXI5caAX.html',
        'https://mall.bilibili.com/act/aicms/37XlXLO7m.html',
        'https://mall.bilibili.com/act/aicms/Gc9h6GQX8n.html',
        'https://mall.bilibili.com/act/aicms/Ps76aypqi.html',
        'https://mall.bilibili.com/act/aicms/auRPHdgWz.html',
    ]
    for u in url_list:
        myli = liulan.get_view_task_id(u)
        for myta in myli:
            for s in range(2, 5):
                eval(
                    'thread_task_list.append(threading.Thread(target=liulan.get_and_view,args=(myta, cookie{z}, ua{z}, csrf{z}, device_id{z})))'.format(
                        z=s))

    for t in thread_task_list:
        t.start()
        t.join()
    thread_task_list.clear()
    for e in range(2, 5):
        eval(
            'thread_task_list.append(threading.Thread(target=liulan.do_task,args=("2022-919-prod", cookie{n}, ua{n}, csrf{n}, device_id{n})))'.format(
                n=e))
    for t in thread_task_list:
        t.start()
        t.join()
    thread_task_list.clear()
    print('星球主任务：')
    xq = ciyuanxingqiu()
    for e in range(2, 5):
        eval(
            'thread_task_list.append(threading.Thread(target=xq.start,args=(cookie{n},ua{n},fingerprint{n},csrf{n})))'.format(
                n=e))
    for t in thread_task_list:
        t.start()
        t.join()
    thread_task_list.clear()
    print('彩蛋碎片：')
    s = suipian()
    for e in range(2, 5):
        eval('thread_task_list.append(threading.Thread(target=s.get_egg,args=(csrf{n},cookie{n},ua{n})))'.format(n=e))

    for t in thread_task_list:
        t.start()
        t.join()
    thread_task_list.clear()