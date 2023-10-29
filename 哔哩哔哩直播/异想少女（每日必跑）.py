# -*- coding:utf-8 -*-
import ctypes
import inspect
import sys
import threading
import time
import requests
import json
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds

BAPI = my_methonds.methods()


def _async_raise(tid, exctype):
    """Raises an exception in the threads with id tid"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


class shipinshichang:
    def __init__(self):
        self.s = requests.session()
        self.played_time = 0
        self.real_played_time = 0
        self.play_type = 1
        self.auto_continued_play = 0
        self.from_spmid = str()

    def heartbeat(self, ua, cookie, data, mid):
        url = 'https://api.bilibili.com/x/report/web/heartbeat'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Referer': 'https://www.bilibili.com/video/{}?spm_id_from=444.42.0.0'.format(self.bvid),
                   'Origin': 'https://www.bilibili.com',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                   }
        datadict = dict()
        for i in data.split('&'):
            try:
                datadict.update({i.split('=')[0]: i.split('=')[1]})
            except:
                datadict.update({i.split('=')[0]: repr(i.split('=')[1])})
        req = self.s.request("POST", url=url, headers=headers, data=datadict)
        req_dict = json.loads(req.text)
        code = req_dict.get('code')
        if code == 0:
            print(req_dict)
            print('uid：' + str(mid))
        else:
            print('\n\n\n\n\n观看失败，错误信息：\n\n\n\n')
            print(req.text)
            exit('观看失败，退出')

    def account_choose(self, accountname, bvid, spmid, timeout):
        cookie1 = gl.get_value('cookie1').encode('utf-8')  # 星瞳
        fullcookie1 = gl.get_value('fullcookie1').encode('utf-8')
        ua1 = gl.get_value('ua1').encode('utf-8')
        fingerprint1 = gl.get_value('fingerprint1')
        csrf1 = gl.get_value('csrf1')
        uid1 = gl.get_value('uid1')
        username1 = gl.get_value('uname1')
        watch_cookie1 = gl.get_value('watch_cookie1').encode('utf-8')

        cookie2 = gl.get_value('cookie2').encode('utf-8')  # 保加利亚
        fullcookie2 = gl.get_value('fullcookie2').encode('utf-8')
        ua2 = gl.get_value('ua2')
        fingerprint2 = gl.get_value('fingerprint2')
        csrf2 = gl.get_value('csrf2')
        uid2 = gl.get_value('uid2')
        username2 = gl.get_value('uname2')
        watch_cookie2 = gl.get_value('watch_cookie2').encode('utf-8')

        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        fullcookie3 = gl.get_value('fullcookie3').encode('utf-8')
        ua3 = gl.get_value('ua3')
        fingerprint3 = gl.get_value('fingerprint3').encode('utf-8')
        csrf3 = gl.get_value('csrf3')
        uid3 = gl.get_value('uid3')
        username3 = gl.get_value('uname3')
        watch_cookie3 = gl.get_value('watch_cookie3').encode('utf-8')

        cookie4 = gl.get_value('cookie4')  # 墨色
        fullcookie4 = gl.get_value('fullcookie4').encode('utf-8')
        ua4 = gl.get_value('ua4')
        fingerprint4 = gl.get_value('fingerprint4').encode('utf-8')
        csrf4 = gl.get_value('csrf4')
        uid4 = gl.get_value('uid4')
        username4 = gl.get_value('uname4')
        watch_cookie4 = gl.get_value('watch_cookie4').encode('utf-8')

        if accountname == 1:
            print(uid1)
            self._doit(ua1, watch_cookie1, bvid,  csrf1, spmid, timeout)
        elif accountname == 2:
            print(uid2)
            self._doit(ua2, watch_cookie2, bvid,  csrf2, spmid, timeout)
        elif accountname == 3:
            print(uid3)
            self._doit(ua3, watch_cookie3, bvid,  csrf3, spmid, timeout)
        elif accountname == 4:
            print(uid4)
            self._doit(ua4, watch_cookie4, bvid,  csrf4, spmid, timeout)

    def _get_video_info(self, bvid):
        v_info = BAPI.view_bvid(bvid)
        if v_info.get('code') == 0:
            aid = v_info.get('data').get('aid')
            cid = v_info.get('data').get('cid')
            duration = v_info.get('data').get('duration')
            return {'bvid': bvid, 'aid': aid, 'cid': cid, 'duration': duration}
        else:
            print(v_info)
            return None

    def send_heartbeat_interval(self, ua, cookie, bvid, uid, csrf, spmid):
        t = 1
        pt = 15
        if self.duration > 15:
            if pt > self.duration:
                pt = pt - self.duration
        else:
            pt %= self.duration
        while 1:
            time.sleep(15)
            p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=pt, real_played_time=t,
                realtime=t, start_ts=self.start_ts, type=3, dt=2, play_type=t, csrf=csrf,
                from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
            self.heartbeat(ua, cookie, p_data, uid)
            t += 15
            pt += 15
            if self.duration > 15:
                if pt > self.duration:
                    pt = pt - self.duration
            else:
                pt %= self.duration

    def _doit(self, ua, cookie, bvid, csrf, spmid, timeout):

        def login_check(cookie,ua):
            headers = {
                'User-Agent': ua,
                'cookie': cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = self.s.get(url=url, headers=headers).json()
            _uid=None
            name =None
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                _uid = res['data']['mid']
                print('登录成功,当前账号用户名为%s' % name)
                return {'uid':_uid,'name':name}
            else:
                print('登陆失败,请重新登录')
                #sys.exit('登陆失败,请重新登录')
                exit('登陆失败,请重新登录')
            return  {'uid':_uid,'name':name}
        uid = login_check(cookie,ua).get('uid')
        now = time.time()
        self.bvid = bvid
        self.start_ts = int(time.time())
        self.played_time = 0
        self.real_played_time = 0
        self.play_type = 1
        self.auto_continued_play = 0
        if self.from_spmid == None:
            self.from_spmid = spmid
        v_info = self._get_video_info(bvid)
        if v_info:
            self.aid = v_info.get('aid')
            self.cid = v_info.get('cid')
            self.duration = v_info.get('duration')
            self.duration -= 1
            p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                real_played_time=self.real_played_time,
                realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2, play_type=self.play_type,
                csrf=csrf,
                from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
            self.heartbeat(ua, cookie, p_data, uid)
            myt = threading.Thread(target=self.send_heartbeat_interval, args=(ua, cookie, bvid, uid, csrf, spmid))
            myt.start()
            if self.duration >= 15:
                while 1:
                    if time.time() - now >= timeout:
                        stop_thread(myt)
                        print('结束观看')
                        break
                    if self.played_time < self.duration - 15:
                        time.sleep(15)
                        self.real_played_time += 15
                        self.played_time += 15
                        self.play_type = 1
                    else:
                        time.sleep(self.duration % 15)
                        self.played_time = self.duration
                        self.play_type = 0
                        p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                            aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                            real_played_time=self.real_played_time,
                            realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2,
                            play_type=self.play_type, csrf=csrf,
                            from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
                        self.heartbeat(ua, cookie, p_data, uid)
                        self.real_played_time += self.duration - self.played_time
                        self.played_time = -1
                        self.play_type = 4
                        p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                            aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                            real_played_time=self.real_played_time,
                            realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2,
                            play_type=self.play_type, csrf=csrf,
                            from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
                        self.heartbeat(ua, cookie, p_data, uid)
                        if '.video.player_loop' not in self.from_spmid:
                            self.from_spmid = spmid + '.video.player_loop'
                        self.auto_continued_play = 1
                        self.played_time = 0
                        self.play_type = 1
                        p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                            aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                            real_played_time=self.real_played_time,
                            realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2,
                            play_type=self.play_type, csrf=csrf,
                            from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
                        self.heartbeat(ua, cookie, p_data, uid)
                        print(
                            'https://www.bilibili.com/{} 累计播放时长：{} 视频总时长：{} 播放次数{}'.format(bvid, self.real_played_time,
                                                                                           self.duration,
                                                                                           int(self.real_played_time / self.duration)))
            else:
                while 1:
                    if time.time() - now >= timeout:
                        stop_thread(myt)
                        print('结束观看')
                        break
                    time.sleep(self.duration)
                    self.real_played_time += self.duration - self.played_time
                    self.played_time = -1
                    self.play_type = 4
                    p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                        aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                        real_played_time=self.real_played_time,
                        realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2, play_type=self.play_type,
                        csrf=csrf,
                        from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
                    self.heartbeat(ua, cookie, p_data, uid)
                    self.from_spmid = spmid + '.video.player_loop'
                    self.auto_continued_play = 1
                    self.played_time = 0
                    self.play_type = 1
                    p_data = 'aid={aid}&cid={cid}&bvid={bvid}&mid={mid}&csrf={csrf}&played_time={played_time}&real_played_time={real_played_time}&realtime={realtime}&start_ts={start_ts}&type={type}&dt={dt}&play_type={play_type}&from_spmid={from_spmid}&spmid={spmid}&auto_continued_play={auto_continued_play}&refer_url=https://t.bilibili.com/&bsource=share_source_copy_link'.format(
                        aid=self.aid, cid=self.cid, bvid=bvid, mid=uid, played_time=self.played_time,
                        real_played_time=self.real_played_time,
                        realtime=self.real_played_time, start_ts=self.start_ts, type=3, dt=2, play_type=self.play_type,
                        csrf=csrf,
                        from_spmid=self.from_spmid, spmid=spmid, auto_continued_play=self.auto_continued_play)
                    self.heartbeat(ua, cookie, p_data, uid)
        else:
            exit('视频信息获取错误')

    def start(self, account_choose, bvid, from_spmid, spmid, timeout):
        a = shipinshichang()
        a.from_spmid = from_spmid
        a.account_choose(account_choose, bvid, spmid, timeout)



class yixiangshaonv:
    def __init__(self):
        self.s = requests.session()

    def get_allinfo(self, ua, cookie):
        url = 'https://show.bilibili.com/api/activity/athena/home'
        data = {}
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request('GET', data=data, url=url, headers=headers)
        req_dict = json.loads(req.text)
        jsondata = req_dict.get('data')
        # "data": {
        # "uid": 9295261,
        # "canJoin": false,
        # "athenaId": 3,
        # "faceImg": "//i1.hdslb.com/bfs/face/41f2c3feb91b2b1ee3f9e1dd86fee257cb0e2bf3.jpg",
        # "nickName": "保加利亚人妖王",
        # "grade": 3,
        # "nowExp": 150,
        # "currentExp": 180,
        # "maxExp": 480,
        # "strength": 34,
        # "roleBone": "//activity.hdslb.com/blackboard/static/20210317/6e7ecf1078ee9a956aa61d78b47a472d/roleC_lv0.sk",
        # "roleImg": "//i0.hdslb.com/bfs/openplatform/202103/R3Gb5Gyh1616157732014.png",
        # "callName": "master",
        # "greetText": null,
        # "birthdayText": null,
        # "signTaskId": "sr_ll9ap12wh9",
        # "amount": 351,
        # "taskListId": "kxg015wr9o",
        # "prizeCenterUrl": "https://mall.bilibili.com/prizecenter.html?noTitleBar=1",
        # "gameRuleUrl": "https://www.bilibili.com/blackboard/activity-RJi06QJzqX.html",
        # "feedbackUrl": "https://show.bilibili.com/m/platform/feedback.html?from=mall&noTitleBar=1",
        # "questionUrl": "https://www.bilibili.com/blackboard/activity-8xcRhirCib.html",
        # "shopUrl": "https://mall.bilibili.com/activities/robotgirl/shop/shop.html?noTitleBar=1",
        # "backpackUrl": "https://mall.bilibili.com/activities/robotgirl/warehouse/warehouse.html?noTitleBar=1",
        # "adventureBone": "https://i0.hdslb.com/bfs/activity-plat/static/20210322/b70fea2c025a012f6c0b0a9caa6ca7bc/role_C.sk",
        # "strengthPerDay": null,
        # "storeGuideTips": ""}
        if jsondata == None:
            print(req_dict)
        return jsondata

    def get_signtaskid(self, ua, longcookie):
        url = 'https://show.bilibili.com/api/activity/athena/v2/sign/detail'
        data = {}
        headers = {
            'User - Agent': ua,
            'Cookie': longcookie,
            'Content-Type': 'application/json'
        }
        data = json.dumps(data)
        req = self.s.request('GET', headers=headers, data=data, url=url)
        req_dict = json.loads(req.text)
        print(req_dict)
        return req_dict.get('data')

    def sign_do(self, ua, longcookie):  # 签到
        signdetail = self.get_signtaskid(ua, longcookie)
        SignTaskId = signdetail.get('taskId')
        isSigned = signdetail.get('isSigned')
        if isSigned:
            return '今日已签到'
        url = 'https://show.bilibili.com/api/activity/athena/sign/do'
        data = {"taskId": SignTaskId}
        headers = {
            'User - Agent': ua,
            'Cookie': longcookie,
            'Content-Type': 'application/json'
        }
        data = json.dumps(data)
        req = self.s.request('POST', headers=headers, data=data, url=url)
        req_dict = json.loads(req.text)
        code = req_dict.get('code')
        errno = req_dict.get('errno')
        msg = req_dict.get('msg')
        detail = {'code': code, 'errno': errno, 'msg': msg}
        if code != 0:
            print(req_dict)
            print(SignTaskId)
        return detail.get('msg')

    def food_step1(self, ua, longcookie, i):
        url = 'https://show.bilibili.com/api/activity/athena/feed/step1?i=' + str(i)
        data = {}
        headers = {'Cookie': longcookie,
                   'User-Agent': ua,
                   'Content-Type': 'application/json'}
        req = self.s.request('GET', url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        jsondata = req_dict.get('data')
        foodid = jsondata.get('foodId')
        return jsondata

    def feed_step2(self, ua, longcookie):
        url = 'https://show.bilibili.com/api/activity/athena/feed/step2'
        headers = {'Cookie': longcookie,
                   'User-Agent': ua,
                   'Content-Type': 'application/json'}
        detaillist = []
        i = 0
        while 1:
            foodstep1_dict = self.food_step1(ua=ua, longcookie=longcookie, i=i)
            foodid = foodstep1_dict.get('foodId')
            isdayfeed = foodstep1_dict.get('isDayFeed')
            if isdayfeed:
                return '今日亲密度已经喂满了'
            data = {'foodId': foodid}
            data = json.dumps(data)
            req = self.s.request('POST', data=data, headers=headers, url=url)
            req_dict = json.loads(req.text)
            code = req_dict.get('code')
            errno = req_dict.get('errno')
            msg = req_dict.get('msg')
            detail = {'code': code, 'errno': errno, 'msg': msg}
            detaillist.append(detail)
            print('foodid:' + str(foodid))
            time.sleep(2)
            i += 1

    def get_taskstatus(self, ua, longcookie, tasklistid):
        url = 'https://mall.bilibili.com/mall-dayu/ticket-activity/activity/v2/taskset/get?id=' + str(tasklistid)
        headers = {'Cookie': longcookie,
                   'User-Agent': ua,
                   'Content-Type': 'application/json'}
        req = self.s.request('GET', url=url, data={}, headers=headers)
        req_dict = json.loads(req.text)
        datalist = req_dict.get('inner')
        return datalist

    def sign_v2(self, ua, longcookie):
        url = 'https://show.bilibili.com/api/activity/athena/v4/sign/detail'
        headers = headers = {'Cookie': longcookie,
                             'User-Agent': ua,
                             'Content-Type': 'application/json'}
        req = self.s.get(url=url, headers=headers)
        req_dict = json.loads(req.text)
        issigned = req_dict.get('data').get('isSigned')
        if issigned:
            print('今日已签到')
            return 0
        time.sleep(2)
        batchId = req_dict.get('data').get('batchId')
        url = 'https://show.bilibili.com/api/activity/athena/v4/sign/do'
        data = {'batchId': batchId}
        data = json.dumps(data)
        req = self.s.post(url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        if req_dict.get('msg') == 'SUCCESS':
            print('v2签到成功')

    def doview(self, ua, cookie, taskid, viewtime):
        url = 'https://show.bilibili.com/api/activity/index/view/do?_=' + str(int(time.time()))
        data = {
            'id': taskid,
            'viewTime': viewtime
        }
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        data = json.dumps(data)
        req = self.s.request('POST', url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        msg = req_dict.get('msg')
        errno = req_dict.get('errno')
        if msg == '该浏览任务不存在':
            print(taskid)
        if errno == 0:
            return '浏览10s成功'
        return req_dict

    def start(self, ua, cookie, count):
        url = 'https://show.bilibili.com/api/activity/athena/adventure/start'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        data = {"count": count, "placeId": "", "propIds": []}
        data = json.dumps(data)
        req = self.s.request('POST', url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        msg = req_dict.get('msg')
        return msg

    def forest_strength(self, ua, cookie):
        url = 'https://show.bilibili.com/api/activity/athena/strength/forest'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request('GET', url=url, data={}, headers=headers)
        req_dict = json.loads(req.text)
        datalist = req_dict.get('data')
        backlist = []
        if datalist != None:
            for i in datalist:
                ids = i.get('ids')
                backlist.append(ids)
            return backlist
        else:
            return []

    def receive_strength(self, ua, cookie, strengthlist):
        url = 'https://show.bilibili.com/api/activity/athena/receive/strength/'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        msglist = []
        if strengthlist != []:
            for i in strengthlist:
                idata = json.dumps(i)
                print(idata)
                req = self.s.request('POST', url=url, data=idata, headers=headers)
                req_dict = json.loads(req.text)
                msg = req_dict.get('msg')
                msglist.append(msg)
                time.sleep(3)
        else:
            return None
        return msglist

    def heartbeat(self, ua, cookie, aid, cid, bvid, mid, csrf, playtime, start_ts):
        url = 'https://api.bilibili.com/x/click-interface/web/heartbeat'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   }
        playedtime = 0
        for i in range(int(playtime / 15)):
            playedtime += 15
            data = {'aid': aid,
                    'cid': cid,
                    'bvid': bvid,
                    'mid': mid,
                    'csrf': csrf,
                    'played_time': playedtime,
                    'real_played_time': playedtime,
                    'realtime': playedtime,
                    'start_ts': start_ts,
                    'type': 3,
                    'dt': 2,
                    'play_type': 3,
                    'auto_continued_play': 1}
            try:
                req = self.s.request("POST", url=url, headers=headers, data=data)
            except Exception as e:
                print(e)
                time.sleep(eval(input('输入等待时间')))
                continue
            req_dict = json.loads(req.text)
            code = req_dict.get('code')
            if code == 0:
                print(req_dict)
                print('uid：' + str(mid) + '\n15秒观看完成')
            else:
                print('观看失败，错误信息：')
                print(req.text)
            time.sleep(15)

    def furniture_home(self, ua, cookie):  # 返回手办furnitureid
        url = 'https://show.bilibili.com/api/activity/index/furniture/home'
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request("GET", url=url, headers=headers)
        jsondata = json.loads(req.text).get('data')
        list = jsondata.get('list')
        furnituredict = {}
        for i in list:
            categoryname = i.get('categoryName')
            furnitureid = i.get('userFurnitureId')
            apenddict = {categoryname: furnitureid}
            furnituredict.update(apenddict)
        return furnituredict.get('手办')

    def putdown_furniture(self, ua, cookie, furnitureid):
        url = 'https://show.bilibili.com/api/activity/index/furniture/putDown'
        data = {"userFurnitureId": furnitureid}
        data = json.dumps(data)
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request("POST", url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        errno = req_dict.get('errno')
        if errno == 0:
            return '手办拿下成功'
        print(req_dict)
        print(furnitureid)

    def place_furniture(self, ua, cookie, furniturid):
        url = 'https://show.bilibili.com/api/activity/index/furniture/place'
        data = {"userFurnitureId": furniturid, "latticeId": "1022"}  # 15899095   手办  1018  为手办柜左上第一
        data = json.dumps(data)
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request("POST", url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        errno = req_dict.get('errno')
        if errno == 0:
            return '手办安装成功'
        print(req_dict)
        print(furniturid)

    def view_ip(self, ua, cookie, taskid, itemid):
        url = 'https://show.bilibili.com/api/activity/index/share/viewIp'
        data = {"id": taskid,
                "url": "bilibili://mall/ip/home?ip=0_" + str(itemid) + "&viewId=" + str(taskid) + "&viewTime=3&tab=4",
                "iosBuildNo": 0,
                "androidBuildNo": 0,
                "viewTime": 3,
                "itemId": itemid}
        data = json.dumps(data)
        headers = {'User-Agent': ua,
                   'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req = self.s.request("POST", url=url, data=data, headers=headers)
        req_dict = json.loads(req.text)
        errno = req_dict.get('errno')
        if errno == 0:
            return '会员购ip浏览3S任务完成'
        return req_dict, taskid, itemid


def main(ua, cookie):
    print('\n\n\n')
    account = yixiangshaonv()
    allinfo = account.get_allinfo(ua, cookie)
    uid = allinfo.get('uid')
    amount0 = allinfo.get('amount')
    nickname = allinfo.get('nickName')
    strength = allinfo.get('strength')
    tasklistid = allinfo.get('taskListId')
    time.sleep(2)
    print('用户名：' + str(nickname) + '\n' + '当前体力：' + str(strength) + '\n' + '当前金币：' + str(amount0) + '\n' + '开始执行任务')

    tasklist = account.get_taskstatus(ua, cookie, tasklistid)
    task910data = tasklist.get('910').get('data')
    task912data = tasklist.get('912').get('data')
    # task914data = tasklist.get('914').get('data')
    print('任务状态：')
    task910desc = task910data.get('description')
    task910buttontext = task910data.get('buttonText')
    task910id = task910data.get('data').get('id')
    task910viewtime = task910data.get('data').get('viewTime')
    task912title = task912data.get('title')
    task912buttontext = task912data.get('buttonText')
    task912id = task912data.get('data').get('id')
    task912itemid = task912data.get('data').get('itemId')
    # task914title = task914data.get('title')
    # task914buttontext = task914data.get('buttonText')
    # task914id = task914data.get('data').get('id')
    # task914itemid = task914data.get('data').get('itemId')
    print('任务一：' + str(task910desc) + '\t状态：' + str(task910buttontext))
    print('任务二：' + str(task912title) + '\t状态：' + str(task912buttontext))
    print('任务三：' + str(task912title) + '\t状态：' + str(task912buttontext))

    # print('当前任务：签到')
    # signresult=account.sign_do(ua,cookie)
    # print('任务结果：'+str(signresult))
    # time.sleep(2)
    print('当前任务：签到v2')
    print('任务结果：')
    account.sign_v2(ua, cookie)
    time.sleep(2)
    print('当前任务：好感度')
    feedresult = account.feed_step2(ua, cookie)
    print('任务结果：' + str(feedresult))
    time.sleep(2)
    print('当前任务：装修小屋')
    figireid = account.furniture_home(ua, cookie)
    time.sleep(1)
    print(account.putdown_furniture(ua, cookie, figireid))
    time.sleep(2)
    print(account.place_furniture(ua, cookie, figireid))
    time.sleep(2)
    print('查看森林中体力')
    strengthlist = account.forest_strength(ua=ua, cookie=cookie)
    print(strengthlist)
    if strengthlist != []:
        print('当前任务：获取森林气泡体力值')
        bubbleresult = account.receive_strength(ua, cookie, strengthlist)
        print('任务结果：' + str(bubbleresult))
    time.sleep(2)

    print('当前任务：' + str(task910desc))
    if task910buttontext != '已完成':
        time.sleep(10)
        doviewresult = account.doview(ua, cookie, task910id, task910viewtime)
        print(doviewresult)
    else:
        print(task910buttontext)
    time.sleep(3)
    tasklist = account.get_taskstatus(ua, cookie, tasklistid)
    task910data = tasklist.get('910').get('data')
    task910buttontext = task910data.get('buttonText')
    print('任务结果：' + str(task910buttontext))
    while task912buttontext != '已完成':
        time.sleep(5)
        print('当前任务：' + str(task912title))
        print(account.view_ip(ua, cookie, task912id, task912itemid))
        time.sleep(1)
        tasklist = account.get_taskstatus(ua, cookie, tasklistid)
        task912data = tasklist.get('912').get('data')
        task912title = task912data.get('title')
        task912buttontext = task912data.get('buttonText')
        task912id = task912data.get('data').get('id')
        task912itemid = task912data.get('data').get('itemId')

    allinfo = account.get_allinfo(ua, cookie)
    strength = allinfo.get('strength')
    print('目前体力值：' + str(strength))

    # while (strength >= 6):#探险获得金币
    #     print('开始探险')
    #     i = int(strength / 6)
    #     if i > 5:
    #         i = 5
    #     advantureresult = account.start(ua, cookie, i)
    #     time.sleep(2)
    #     print('探险结果：' + str(advantureresult))
    #     allinfo = account.get_allinfo(ua, cookie)
    #     strength = allinfo.get('strength')
    #     print('目前体力值：' + str(strength))
    #     time.sleep(5)
    # else:
    #     print('体力值不够探险')
    # allinfo = account.get_allinfo(ua, cookie)
    # amount1 = allinfo.get('amount')
    # print('当前金币：' + str(amount1))
    # print('今日获取金币：' + str(amount1 - amount0))

def s():
    thread_list = list()
    # cookie1 = gl.get_value('cookie1').encode('utf-8')  # 星瞳
    # fullcookie1 = gl.get_value('fullcookie1').encode('utf-8')
    # ua1 = gl.get_value('ua1').encode('utf-8')
    # fingerprint1 = gl.get_value('fingerprint1')
    # csrf1 = gl.get_value('csrf1')
    # uid1 = gl.get_value('uid1')
    # username1 = gl.get_value('uname1')
    # watch_cookie1 = gl.get_value('watch_cookie1').encode('utf-8')

    cookie2 = gl.get_value('cookie2').encode('utf-8')  # 保加利亚
    fullcookie2 = gl.get_value('fullcookie2').encode('utf-8')
    ua2 = gl.get_value('ua2')
    #fingerprint2 = gl.get_value('fingerprint2')
    csrf2 = gl.get_value('csrf2')
    uid2 = gl.get_value('uid2')
    username2 = gl.get_value('uname2')
    watch_cookie2 = gl.get_value('watch_cookie2').encode('utf-8')

    cookie3 = gl.get_value('cookie3')  # 斯卡蒂
    fullcookie3 = gl.get_value('fullcookie3').encode('utf-8')
    ua3 = gl.get_value('ua3')
    # fingerprint3 = gl.get_value('fingerprint3').encode('utf-8')
    csrf3 = gl.get_value('csrf3')
    uid3 = gl.get_value('uid3')
    username3 = gl.get_value('uname3')
    watch_cookie3 = gl.get_value('watch_cookie3').encode('utf-8')

    cookie4 = gl.get_value('cookie4')  # 墨色
    fullcookie4 = gl.get_value('fullcookie4').encode('utf-8')
    ua4 = gl.get_value('ua4')
    # fingerprint4 = gl.get_value('fingerprint4').encode('utf-8')
    csrf4 = gl.get_value('csrf4')
    uid4 = gl.get_value('uid4')
    username4 = gl.get_value('uname4')
    watch_cookie4 = gl.get_value('watch_cookie4').encode('utf-8')
    print('观看视频中')
    nowtime = int(time.time())
    # ac1 = threading.Thread(target=yixiangshaonv.heartbeat, args=(
    # yixiangshaonv, ua4, watch_cookie4, 253457292, 492074807, 'BV1AY41187b3', 1178256718, csrf4, 630, nowtime-5))
    # ac2 = threading.Thread(target=yixiangshaonv.heartbeat, args=(
    # yixiangshaonv, ua3, watch_cookie3, 338268359, 490174375, 'BV12R4y1M7jZ', 1905702375, csrf3, 630, nowtime-5))
    # ac3 = threading.Thread(target=yixiangshaonv.heartbeat, args=(
    # yixiangshaonv, ua2, watch_cookie2, 253457292, 492074807, 'BV1AY41187b3', 9295261, csrf2, 630, nowtime-5))
    # ac4 = threading.Thread(target=yixiangshaonv.heartbeat, args=(
    # yixiangshaonv, ua1, watch_cookie1, 635969070, 492485108, 'BV1Zb4y177WW', 4237378, csrf1, 630, nowtime-5))
    s = shipinshichang()
    # t1 = threading.Thread(target=s.start, args=(1, 'BV1Zb4y177WW', '444.42.0.0', '333.788.0.0', 60 * 10 + 30))
    # t2 = threading.Thread(target=s.start, args=(2, 'BV178411Y7QB', '444.42.0.0', '333.788.0.0', 60 * 10 + 30))
    # t3 = threading.Thread(target=s.start, args=(3, 'BV1xG411c7Vo', '444.42.0.0', '333.788.0.0', 60 * 10 + 30))
    # t4 = threading.Thread(target=s.start, args=(4, 'BV1AY41187b3', '444.42.0.0', '333.788.0.0', 60 * 10 + 30))
    # thread_list.append(t1)
    # thread_list.append(t2)
    # thread_list.append(t3)
    # thread_list.append(t4)
    # t1.start()
    # time.sleep(3)
    # t2.start()
    # time.sleep(3)
    # t3.start()
    # time.sleep(3)
    # t4.start()
    # t1.join()
    # main(ua=ua1, cookie=cookie1)
    main(ua=ua2, cookie=cookie2)
    main(ua=ua3, cookie=cookie3)
    main(ua=ua4, cookie=cookie4)
    exit(1)


if __name__ == '__main__':
    # s()
    schedulers = BlockingScheduler()
    schedulers.add_job(s, CronTrigger.from_crontab('0 0 * * *'), misfire_grace_time=3600)
    schedulers.start()