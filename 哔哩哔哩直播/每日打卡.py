import random

import os

import json
import re
import sys
import time

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import bili_live.bili_live_api as api
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import threading as thd
import Bilibili_methods.all_methods
from CONFIG import CONFIG

myapi = api.bili_live_api()
BAPI = Bilibili_methods.all_methods.methods()


class daily_reward:
    def __init__(self):
        self.session = requests.session()
        self.uid = None

    def login_check(self, _cookie, _ua):
        headers = {
            'User-Agent': _ua,
            'cookie': _cookie
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        _res = self.session.get(url=url, headers=headers).json()
        if _res['data']['isLogin'] == True:
            name = _res['data']['uname']
            self.uid = _res['data']['mid']
            print('登录成功,当前账号用户名为%s' % name)
            return 1
        else:
            print('登陆失败,请重新登录\n'+_cookie)
            sys.exit('登陆失败,请重新登录')

    def _start(self, cookie, ua, csrf):

        self.login_check(cookie, ua)
        print('主站登陆、分享视频：')
        self.mainStationSign(cookie, ua, csrf)
        print('直播区签到：')
        res = myapi.Dosign(cookie, ua)
        if res.get('code') == -101:
            print(cookie)
        else:
            print(res)
        print('应援团签到：')
        print(myapi.sign_in(cookie, ua))
        print(myapi.silvertocoin(cookie, ua, csrf, myapi.get_visit_id(self.uid)))
        print('漫画签到：')
        BAPI.Activity_ClockIn(cookie, ua)
        print('魔晶签到：')
        self.mall_c_sign(cookie, ua)
        print('魔晶每日任务：')
        self.daily_task_molishang(cookie, ua, csrf)

        print('魔晶战令任务：')
        self.war_order(cookie, ua, csrf)

        print('活动签到任务：')
        activity_id_list = [
            # "212"
        ]
        if self.uid:
            for activity_id in activity_id_list:
                self.meet_sign_in(self.uid, activity_id, cookie, ua)
                time.sleep(1)
        else:
            print('uid获取失败')

    def meet_sign_in(self, uid, activity_id, cookie, ua):
        url = 'https://cm.bilibili.com/meet/api/open_api/v1/activity/sign_in'
        data = {
            'mid': uid,
            'activity_id': activity_id
        }
        headers = {
            'accept-encoding': 'gzip, deflate',
            "Content-Type": "application/json",
            'cookie': cookie,
            'accept-language': 'zh-CN,zh;q=0.9',
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/',
            'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua
        }
        req = self.session.post(url=url, headers=headers, data=json.dumps(data))
        print(req.json())
        if req.json().get('code') != 0:
            exit('活动签到失败')

    def war_order(self, cookie, ua, csrf):
        def dispatch(eventid, _csrf):
            url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
            data = {"eventId": eventid
                , "csrf": _csrf}
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua,
                       'origin': 'https://mall.bilibili.com',
                       'referer': 'https://mall.bilibili.com/',
                       'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
                       'sec-ch-ua-mobile': '?0',
                       'sec-ch-ua-platform': '\"Windows\"',
                       'sec-fetch-dest': 'empty',
                       'sec-fetch-mode': 'cors',
                       'sec-fetch-site': 'same-origin',
                       }
            data = json.dumps(data)
            req = self.session.post(url=url, data=data, headers=headers)
            print(req.text)
            if req.json().get('code') == 0:
                print(req.json().get('message'))
                print('魔晶每日任务完成')
            else:
                print(req.json())
            return req.json()

        def report_detail(_taskId):
            _url = 'https://show.bilibili.com/api/activity/hercules/task/report-detail'
            params = {
                'taskId': _taskId,
                '_': int(time.time()) * 1000
            }
            headers = {
                'accept-encoding': 'gzip, deflate, br',
                'cookie': cookie,
                'accept-language': 'zh-CN,zh;q=0.9',
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/',
                'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': ua
            }
            req = self.session.get(url=_url, headers=headers, params=params)
            return req.json()

        def get_activity_task_list():
            _url = 'https://mall.bilibili.com/mall-magic-c/internet/mls_pm/war_order/activity_task_list'
            data = {}
            headers = {
                'accept-encoding': 'gzip, deflate, br',
                'content-type': 'application/json',
                'cookie': cookie,
                'accept-language': 'zh-CN,zh;q=0.9',
                'origin': 'https://mall.bilibili.com',
                'referer': 'https://mall.bilibili.com/neul-next/index.html?page=boxmagicorder_detail',
                'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': ua
            }
            req = self.session.post(url=_url, headers=headers, data=json.dumps(data))
            return req.json()

        all_tasks_list = get_activity_task_list().get('data').get('taskList').get('normalTasks')
        for task in all_tasks_list:
            taskName = task.get('taskName')
            guideButtonText = task.get('guideButtonText')
            guideLink = task.get('guideLink')
            if guideButtonText == "已完成":
                continue
            if "欧气爆款种草10秒" in taskName:
                task_id = ''.join(re.findall('.*=(.*)', guideLink))
                if task_id:
                    eventId = report_detail(task_id).get('data').get('eventId')
                    time.sleep(10)
                    dispatch_res = dispatch(eventId, csrf)
                    if dispatch_res['code'] == 0:
                        print(dispatch_res)
                        print(f'任务：{taskName}\t完成')
                    else:
                        print(f'任务：{taskName}\t失败')
            elif taskName == "欧气许愿好物1次":
                pass

    def daily_task_molishang(self, cookie, ua, csrf):
        def dispatch(cookie, ua, eventid, csrf):
            url = 'https://show.bilibili.com/api/activity/fire/common/event/dispatch'
            data = {"eventId": eventid
                , "csrf": csrf}
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua,
                       'origin': 'https://mall.bilibili.com',
                       'referer': 'https://mall.bilibili.com/'}
            data = json.dumps(data)
            req = self.session.post(url=url, data=data, headers=headers)
            print(req.text)
            if req.json().get('code') == 0:
                print(req.json().get('message'))
                print('魔晶每日任务完成')
            else:
                print(req.json())
            return req.json()

        def get_task(cookie, ua):
            url = 'https://mall.bilibili.com/mall-c/blind_box_activity/task/mls_pm/aggregate_page_info'
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua,
                       'origin': 'https://mall.bilibili.com',
                       'referer': 'https://mall.bilibili.com/neul/index.html?noTitleBar=1&page=box_magicmap&share_plat=ios&share_source=COPY&share_tag=s_i'}
            data = {
                'taskGroupType': ""
            }
            req = self.session.post(url=url, data=json.dumps(data), headers=headers)
            return req.json()

        def batch_receive_prize(_activityId, _userTaskId, cookie, ua):
            url = 'https://mall.bilibili.com/mall-c/blind_box_activity/task/mls_pm/batch_receive_prize'
            data = {"prizeReceiveReqList": [{"activityId": _activityId, "userTaskId": _userTaskId}]}
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua,
                       'origin': 'https://mall.bilibili.com',
                       'referer': 'https://mall.bilibili.com/neul/index.html?noTitleBar=1&page=box_magicmap&share_plat=ios&share_source=COPY&share_tag=s_i'}
            req = self.session.post(url=url, data=json.dumps(data), headers=headers)
            return req.json()

        def get_hevent_id(_taskId, cookie, ua):
            url = f'https://show.bilibili.com/api/activity/hercules/task/report-detail?taskId={_taskId}&_={int(time.time() * 1000)}'
            # guideLink里的taskid
            headers = {'cookie': cookie,
                       "Content-Type": "application/json",
                       'user-agent': ua,
                       'origin': 'https://mall.bilibili.com',
                       'referer': 'https://mall.bilibili.com/'}
            req = self.session.get(url, headers=headers)
            return req.json()

        task_req = get_task(cookie, ua)
        if task_req.get('code'):
            print(task_req)
            print('每日魔晶任务失败')
            return
        if not task_req.get('data').get('taskList'):
            print(task_req)
            print('任务结束')
            return
        normalTasks = task_req.get('data').get('taskList').get('normalTasks')

        for normalTask in normalTasks:
            taskName = normalTask.get('taskName')
            if taskName == "再买30元即可领奖":
                print('购物任务，不执行')
                continue
            elif taskName != '欧气爆款种草10秒':
                print('未知任务：', normalTask)
                return
            activityId = normalTask.get('activityId')
            prize = normalTask.get('prize').get('prizeName')
            print(prize)
            userTaskStatus = normalTask.get('userTaskStatus')
            userTaskId = normalTask.get('userTaskId')
            guideLink = normalTask.get('guideLink')
            taskId = re.findall('herculesId=(.*)', guideLink, re.S)[0]
            if not taskId:
                print(f'taskId为空，{prize}领取失败')
                return
            hevent_id = get_hevent_id(taskId, cookie, ua)
            if hevent_id.get('code'):
                print(f'hevent_id获取失败，{prize}领取失败')
                return
            hevent_id = hevent_id.get('data').get('eventId')
            print('{}：参数准备好了，休息15秒'.format(taskName))
            time.sleep(15)
            if dispatch(cookie, ua, hevent_id, csrf).get('code'):
                return
            if userTaskStatus != 4:
                res = batch_receive_prize(activityId, userTaskId, cookie, ua)
                if res.get('code'):
                    print(res)
                    print('奖励领取失败')
                else:
                    print(f'{prize}到手')

    def mall_c_sign(self, cookie, ua):
        url = 'https://mall.bilibili.com/mall-c/sign/detail'
        data = {}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'origin': 'https://mall.bilibili.com',
            'referer': 'https://mall.bilibili.com/neul/index.html?noTitleBar=1&from=cms_880_MTPHopabFLVt_&page'
                       '=box_magicmap&msource=mall_6107_banner&outsideMall=no',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': 'Windows',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'content-type': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
        }
        req = self.session.post(url=url, headers=headers, data=data)
        try:
            signed = req.json().get('data').get('signed')
        except:
            print(req.text)
            signed = True
        if signed:
            print('签过到了')
            return 0
        taskId = req.json().get('data').get('taskId')
        time.sleep(1)
        url = 'https://mall.bilibili.com/mall-c/sign/achieve'
        if taskId:
            data = {"taskId": taskId}
        else:
            print('taskId出错')
            print(req.text)
        req = self.session.post(url=url, data=json.dumps(data), headers=headers)
        if req.json().get('code') == 0:
            print('签到成功')
        else:
            print(taskId)
            print('签到出错')
            print(req.text)

    def account_choose(self, accountname):
        cookie_file_name_list = os.listdir(CONFIG.root_dir+'b站cookie/cookie_path')
        for _i in range(1, len(cookie_file_name_list) + 1):
            exec(f"cookie{_i} = gl.get_value('cookie{_i}')")
            exec(f"fullcookie{_i} = gl.get_value('fullcookie{_i}')")
            exec(f"ua{_i} = gl.get_value('ua{_i}')")
            exec(f"fingerprint{_i} = gl.get_value('fingerprint{_i}')")
            exec(f"csrf{_i} = gl.get_value('csrf{_i}')")
            exec(f"watch_cookie{_i} = gl.get_value('watch_cookie{_i}')")
            exec(f"device_id{_i} = gl.get_value('device_id{_i}')")
            exec(f"buvid3_{_i} = gl.get_value('buvid3_{_i}')")

        exec(f"self._start(cookie{accountname}, ua{accountname}, csrf{accountname})")

    def mainStationSign(self, cookie, ua, csrf):
        def x_now_login(_cookie, _ua):
            _url = 'https://api.bilibili.com/x/report/click/now'
            data = {'jsonp': 'jsonp'}
            headers = {
                'accept-encoding': 'gzip, deflate',
                "Content-Type": "application/json",
                'cookie': _cookie,
                'accept-language': 'zh-CN,zh;q=0.9',
                'origin': 'https://www.bilibili.com',
                'referer': 'https://www.bilibili.com/',
                'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': _ua
            }
            return self.session.get(url=_url, data=data, params=data, headers=headers)

        def share_video(aid, _cookie, _ua, _csrf):
            _url = 'https://api.bilibili.com/x/web-interface/share/add'
            data = {
                'aid': aid,
                #'jsonp': 'jsonp',
                'csrf': _csrf
            }
            headers = {
                'accept-encoding': 'gzip, deflate',
                "content-Type": "application/x-www-form-urlencoded",
                'cookie': _cookie,
                'accept-language': 'zh-CN,zh;q=0.9',
                'origin': 'https://www.bilibili.com',
                'referer': f'https://www.bilibili.com/video/av{aid}?spm_id_from=333.788',
                'sec-ch-ua': '\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\"Windows\"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': _ua
            }
            return self.session.post(url=_url, data=data, headers=headers)

        mainStationLoginResDict = x_now_login(cookie, ua)
        if mainStationLoginResDict.json().get('code') != 0:
            print(f'主站登陆失败：{mainStationLoginResDict.json()}')
        else:
            print(f'主站登陆结果：{mainStationLoginResDict.json()}')
        shareVideoResDict = share_video(
            random.choice([775527811, 520378341, 390477986, 647763578, 305707086, 347777375, 902704545]), cookie, ua,
            csrf)
        if shareVideoResDict.json().get('code') != 0:
            print(f'分享视频失败：{shareVideoResDict.json()}')
        else:
            print(f'分享视频结果：{shareVideoResDict.json()}')
def s():
    my_dail = daily_reward()
    tlist = list()
    for i in range(2, 13):
        t = thd.Thread(target=my_dail.account_choose, args=(i,))
        tlist.append(t)
    for th in tlist:
        th.start()
        time.sleep(60)
    for th in tlist:
        th.join()
if __name__ == '__main__':
    # s()
    schedulers = BlockingScheduler()
    schedulers.add_job(s, CronTrigger.from_crontab('0 0 * * *'), misfire_grace_time=3600)
    schedulers.start()

# 114514臭完了
