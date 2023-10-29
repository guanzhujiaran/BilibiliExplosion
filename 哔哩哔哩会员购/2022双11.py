# -*- coding:utf- 8 -*-
import datetime

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
        print(req.text)
        exit('获取eventid失败')


def dispatch(_cookie, _ua, _eventid, _csrf, _jumpurl):
    url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
    data = {"eventId": _eventid
        , "csrf": _csrf}
    headers = {'cookie': _cookie,
               "Content-Type": "application/json",
               'user-agent': _ua,
               'origin': 'https://mall.bilibili.com',
               'referer': _jumpurl,
               'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
               'sec-ch-ua-mobile': '?0',
               'sec-ch-ua-platform': '\"Windows\"',
               'sec-fetch-dest': 'empty',
               'sec-fetch-mode': 'cors',
               'sec-fetch-site': 'same-site',
               }
    data = json.dumps(data)
    req = requests.post(url=url, data=data, headers=headers)
    print(req.text)
    if req.json().get('code') == 0:
        print('任务提交完成')
    else:
        exit('任务完成失败')


class main_page:
    '''
    主会场
    tngjw5ih1u
    '''

    def main_task(self, activityId, cookie, ua, csrf):
        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie,
                'Connection': 'close'
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

        def get_task(_activityId, _cookie, _ua):
            '''

            :param _activityId:
            :param _cookie:
            :param _ua:
            :return:
            '''
            _url = 'https://show.bilibili.com/api/activity/hercules/task/get'
            _params = {
                'activityId': _activityId,
                'mVersion': 0,
                '_': int(time.time() * 1000)
            }
            _headers = {
                'cookie': _cookie,
                "Content-Type": "application/json",
                'user-agent': _ua,
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/',
                'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }
            req = requests.get(url=_url, headers=_headers, params=_params)
            if req.json().get('code') == 0:
                return req.json()
            else:
                exit('主页任务获取失败')

        def task_do(task_detail, _cookie, _ua, _csrf):
            taskid = ''.join(re.findall('herculesId=(.*)', task_detail.get('data').get('url')))
            eventid = ''
            if taskid != '':
                eventid = get_eventID(taskid, _cookie, _ua)
            else:
                exit('taskid获取失败')
            if eventid:
                print('===执行任务中===')
                dispatch(_cookie, _ua, eventid, _csrf, task_detail.get('data').get('url'))
            else:
                exit('eventid出错')

        def task_receive(task_detail, _activityId, _cookie, _ua):
            _nodeId = task_detail.get('nodeId')
            _url = 'https://show.bilibili.com/api/activity/hercules/task/receive'
            _data = {'activityId': _activityId,
                     'nodeId': _nodeId
                     }
            _headers = {
                'cookie': _cookie,
                "Content-Type": "application/json",
                'user-agent': _ua,
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/',
                'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }
            req = requests.post(url=_url, headers=_headers, data=json.dumps(_data))
            if req.json().get('code') == 0:
                print('奖励领取成功')
            else:
                print(req.text)
                pprint(_data)
                print(task_detail, _activityId, _cookie, _ua)
                exit('奖励领取失败')

        login_check(cookie, ua)
        main_task_req = get_task(activityId, cookie, ua)
        tasks = main_task_req.get('data').get('tasks')
        for task in tasks:
            description = task.get('description')
            print(f'当前任务：{description}')
            buttonStyle = task.get('buttonStyle')
            if buttonStyle == 'go':
                task_do(task, cookie, ua, csrf)

        time.sleep(random.choice(sleeptime))
        main_task_req = get_task(activityId, cookie, ua)
        tasks = main_task_req.get('data').get('tasks')
        for task in tasks:
            buttonStyle = task.get('buttonStyle')
            if buttonStyle == 'receive':
                prizeName = task.get('prize').get('prizeName')
                print(f'当前领取奖励：{prizeName}')
                task_receive(task, activityId, cookie, ua)


class h5_browser_task:
    def get_view_task_id(self, jumpurl):
        url = jumpurl
        req = requests.get(url=url)
        l = re.findall('"activeId":"(.{10})"', req.text, re.S)
        l = list(set(l))
        return l

    def get_and_view(self, taskid, cookie, ua, csrf, device_id):
        url = 'https://show.bilibili.com/api/activity/index/collect/detailV2?id={taskid}&_={timestp}'.format(
            taskid=taskid, timestp=int(time.time_ns() / 1000000))
        data = {'id': taskid,
                '_': int(time.time_ns() / 1000000)}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json",
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/',
            'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
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
                    # time.sleep(random.choice(sleeptime))
                    self.receive_v3(taskId, TYPE, assocId, csrf, cookie, ua, device_id)
                    # time.sleep(random.choice(sleeptime))
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
            'user-agent': ua,
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/',
            'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
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
            "Content-Type": "application/json",
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/',
            'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        }
        data = {
            'id': viewid,
            'itemId': itemid,
            '_': int(time.time_ns() / 1000000) - 10
        }
        data = json.dumps(data)
        req = requests.request('GET', url=url, data=data, headers=headers)
        print(req.text)

    def main(self, url_list, cookie, ua, csrf, device_id):
        for u in url_list:
            myli = self.get_view_task_id(u)
            thread_task_list = []
            for myta in myli:
                thread_task_list.append(
                    threading.Thread(target=self.get_and_view, args=(myta, cookie, ua, csrf, device_id)))
            for t in thread_task_list:
                t.start()
            for t in thread_task_list:
                t.join()


class draw:
    def draw_lottery(self, _cookie, _ua, _activityid):
        while 1:
            url = 'https://mall.bilibili.com/activity/lottery/drawLottery'
            headers = {'cookie': _cookie,
                       "Content-Type": "application/json",
                       'user-agent': _ua}
            data = {"activityId": _activityid
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

    def exchange(self, gameId, itemId, itemType, deviceId, cookie, ua, csrf):
        while 1:
            url = 'https://mall.bilibili.com/activity/game/chip_exchange/exchange'

            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/json",
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/',
                'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }

            data = {"gameId": gameId,
                    "itemId": itemId, "itemType": itemType,
                    "num": 1,
                    "deviceInfoDTO": {
                        "build": 0,
                        "deviceId": deviceId,
                        "platform": "Win32",
                        "ua": ua},
                    "csrf": csrf
                    }
            req = requests.post(url=url, headers=headers, data=json.dumps(data))
            if req.json().get('code')==83110057:
                print(f"碎片兑换完了，只剩下{req.json().get('data').get('effectiveChips')}片碎片了")
                return
            if req.json().get('code') != 0:
                print(req.text)
                exit("换取抽奖机会失败")
            if req.json().get('data').get('effectiveChips') - req.json().get('data').get('usedChips') < req.json().get('data').get('usedChips'):
                print(f"碎片兑换完了，只剩下{req.json().get('data').get('effectiveChips')}片碎片了")
                return

    def main(self, activity_id, gameId, itemId, itemType, deviceId, cookie, ua, csrf, draw_flag):
        '''

        :param activity_id:
        :param gameId:
        :param itemId:
        :param itemType:
        :param deviceId:
        :param cookie:
        :param ua:
        :param csrf:
        :param draw_flag: 是否抽掉，True是抽掉，False不抽
        :return:
        '''
        self.exchange(gameId, itemId, itemType, deviceId, cookie, ua, csrf)
        if draw_flag:
            self.draw_lottery(cookie, ua, activity_id)


if __name__ == '__main__':
    while 1:
        __time = datetime.datetime.now().strftime('%H:%M:%S')
        if __time == '00:00:00':
            my_main_page = main_page()
            thread_list = []
            thread_list.append(
                threading.Thread(target=my_main_page.main_task, args=('tngjw5ih1u', cookie3, ua3, csrf3)))
            thread_list.append(
                threading.Thread(target=my_main_page.main_task, args=('tngjw5ih1u', cookie2, ua2, csrf2)))

            liulan_url_list = [
                'https://mall.bilibili.com/act/aicms/3dvnEgKv7L.html',
                'https://mall.bilibili.com/act/aicms/6HwfmYzLN.html',
                'https://mall.bilibili.com/act/aicms/aaeKxHFe2UB.html',
                'https://mall.bilibili.com/act/aicms/EiwQHJdAK.html',
            ]
            box_activity_id_list = [
                '2022102632126001'
            ]
            gameId_list = [
                '2022102632131001'
            ]
            itemId_list = [
                2932023
            ]
            my_browser = h5_browser_task()
            thread_list.append(
                threading.Thread(target=my_browser.main, args=(liulan_url_list, cookie3, ua3, csrf3, device_id3)))
            thread_list.append(
                threading.Thread(target=my_browser.main, args=(liulan_url_list, cookie2, ua2, csrf2, device_id2)))
            for thread in thread_list:
                thread.start()
            for thread in thread_list:
                thread.join()

            my_draw = draw()
            my_draw.main(box_activity_id_list[0], gameId_list[0], itemId_list[0], 4, device_id2, cookie2, ua2, csrf2,
                         False)
            my_draw.main(box_activity_id_list[0], gameId_list[0], itemId_list[0], 4, device_id3, cookie3, ua3, csrf3,
                         False)
        time.sleep(0.1)
