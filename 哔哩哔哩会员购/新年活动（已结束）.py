# -*- coding:utf- 8 -*-
import json
import random
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


# https://mall.bilibili.com/zq/starpartying-newYear2022/?noTitleBar=1&loadingShow=1&inviteCode=2x54gzpaxkgp1w&invietType=eat

class ciyuanxingqiu:
    def __init__(self):
        self.invite_code = ['9o7owgt2kedol', '2x54gzpaxkgp1w', 'z2wy6e4ea8geow2', '7g4dxmkws5mn18d']
        # 1 2 3 4

    def foodchoose(self, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/fire/resident/v2/food/choose'
        foodtype = 'f' + str(random.choice(range(1, 10)))
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
        except:
            print('选取食物失败')
            while 1:
                try:
                    time.sleep(eval(input('输入等待时间')))
                except:
                    print('输入错误')
                    continue
            self.foodchoose(cookie, ua)
            return 0

    def yaoqingchifan(self, invite_code, cookie, ua):
        self.foodchoose(cookie, ua)
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

    def start(self, cookie, ua):
        self.sign(cookie, ua)
        time.sleep(random.choice(sleeptime))
        self.suijicengfan(cookie, ua)
        time.sleep(random.choice(sleeptime))
        for i in self.invite_code:
            self.yaoqingchifan(i, cookie, ua)
            time.sleep(random.choice(sleeptime))



class mengwuzhongcao:
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
                    self.reveive_v3(taskId, TYPE, assocId, csrf, cookie, ua, device_id)
                    time.sleep(random.choice(sleeptime))
                    print('领取奖励成功')
                else:
                    print('领取奖励失败')
                    print(taskid, TYPE, assocId)
                    print(req.json())
                    print('\n\n')
            else:
                print('viewid出错')
                print(taskid)
        else:
            print('奖励已领取')

    def reveive_v3(self, taskId, TYPE, assocId, csrf, cookie, ua, device_id):
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


class zhuanpan:
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
                print(prizename)
                msg = req_dict.get('message')
                print(msg)
                if msg == '机会用光啦～':
                    time.sleep(random.choice(sleeptime))
                    break
            except Exception as e:
                print('抽奖失败')
                print(req.text)
                time.sleep(random.choice(sleeptime))
                break
            time.sleep(random.choice(sleeptime))


if __name__ == '__main__':
    sleeptime = numpy.linspace(5, 7, 500, endpoint=False)

    myciyuanxingqiu = ciyuanxingqiu()
    # myciyuanxingqiu.start(cookie1, ua1)
    # myciyuanxingqiu.start(cookie2, ua2)
    # myciyuanxingqiu.start(cookie3, ua3)
    # myciyuanxingqiu.start(cookie4, ua4)

    # print('浏览任务')
    # myview = mengwuzhongcao()
    # viewlist = ['mv3x334xlz', '24v02dlxzy', '24v02ylxzy', '8g9x9d30o7', 'qrjx7n501k']
    # for viewtask in viewlist:
    #     # ；；；
    #     # ；；；
    #     # ；；；
    #     # ；；；
    #     # ；；；
    #     t1 = threading.Thread(target=myview.get_and_view, args=(viewtask, cookie1, ua1, csrf1, device_id1))
    #     t2 = threading.Thread(target=myview.get_and_view, args=(viewtask, cookie2, ua2, csrf2, device_id2))
    #     t3 = threading.Thread(target=myview.get_and_view, args=(viewtask, cookie3, ua3, csrf3, device_id3))
    #     t4 = threading.Thread(target=myview.get_and_view, args=(viewtask, cookie4, ua4, csrf4, device_id4))
    #     t1.start()
    #     t2.start()
    #     t3.start()
    #     t4.start()
    #     t1.join()
    #     t2.join()
    #     t3.join()
    #     t4.join()

    # mysuipian=suipian()
    # print('彩蛋')
    # mysuipian.get_egg(csrf1,cookie1,ua1)
    # mysuipian.get_egg(csrf2, cookie2, ua2)
    # mysuipian.get_egg(csrf3, cookie3, ua3)
    # mysuipian.get_egg(csrf4, cookie4, ua4)

    # "2022011431484001"#"2022011731485002"#"2022011731490001"
    # myzhuanpan = zhuanpan()
    # drawlist = ["2022011431484001", "2022011731485002", "2022011731490001"]
    # for gameid in drawlist:
    #     myzhuanpan.draw_lottery(cookie1, ua1, gameid)
    #     myzhuanpan.draw_lottery(cookie2, ua2, gameid)
    #     myzhuanpan.draw_lottery(cookie3, ua3, gameid)
    #     myzhuanpan.draw_lottery(cookie4, ua4, gameid)
    #     time.sleep(random.choice(sleeptime))
