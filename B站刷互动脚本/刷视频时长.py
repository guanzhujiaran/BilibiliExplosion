# -*- coding:utf- 8 -*-
import copy
import json
import random
import re
import shlex
import sys
import threading
import time
import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds
import threading

BAPI = my_methonds.methods()


def login_check(accountNo):
    cookie=None
    ua=None
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
    if accountNo == 1:
        cookie = cookie1
        ua = ua1
    elif accountNo == 2:
        cookie = cookie2
        ua = ua2
    elif accountNo == 3:
        cookie = cookie3
        ua = ua3
    elif accountNo == 4:
        cookie = cookie4
        ua = ua4
    headers = {
        'User-Agent': ua,
        'cookie': cookie
    }
    url = 'https://api.bilibili.com/x/web-interface/nav'
    res = requests.get(url=url, headers=headers).json()
    threading.Timer(30 * 60, login_check, args=(cookie, ua)).start()
    if res['data']['isLogin'] == True:
        name = res['data']['uname']
        print('登录成功,当前账号用户名为%s' % name)
        return 1
    else:
        print('登陆失败,请重新登录')
        sys.exit('登陆失败,请重新登录')


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


class shipinshichang:
    def __init__(self):
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
        req = requests.request("POST", url=url, headers=headers, data=datadict)
        req_dict = json.loads(req.text)
        code = req_dict.get('code')
        if code == 0:
            print(req_dict)
            print('uid：' + str(mid))
        else:
            print('\n\n\n\n\n观看失败，错误信息：\n\n\n\n')
            print(req.text)
            exit('观看失败，退出')

    def account_choose(self, accountNo, bvid, spmid):
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

        if accountNo == 1:
            print(uid1)
            self._doit(ua1, watch_cookie1, bvid, uid1, csrf1, spmid)
        elif accountNo == 2:
            print(uid2)
            self._doit(ua2, watch_cookie2, bvid, uid2, csrf2, spmid)
        elif accountNo == 3:
            print(uid3)
            self._doit(ua3, watch_cookie3, bvid, uid3, csrf3, spmid)
        elif accountNo == 4:
            print(uid4)
            self._doit(ua4, watch_cookie4, bvid, uid4, csrf4, spmid)

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

    def _doit(self, ua, cookie, bvid, uid, csrf, spmid):
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
            threading.Thread(target=self.send_heartbeat_interval, args=(ua, cookie, bvid, uid, csrf, spmid),
                             daemon=True).start()
            if self.duration >= 15:
                while 1:
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
                        print('https://www.bilibili.com/{} 累计播放时长：{}小时 视频总时长：{} 播放次数{}'.format(bvid,
                                                                                               self.real_played_time / 3600,
                                                                                               self.duration,
                                                                                               int(self.real_played_time / self.duration)))
            else:
                while 1:
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

    def start(self, account_choose, bvid_list, from_spmid, spmid):
        for bvid in bvid_list:
            a = shipinshichang()

            # b = shipinshichang()
            # c = shipinshichang()
            # d = shipinshichang()
            # e = shipinshichang()
            a.from_spmid = from_spmid
            # b.from_spmid = from_spmid
            # c.from_spmid = from_spmid
            # d.from_spmid = from_spmid
            # e.from_spmid = from_spmid
            if login_check(account_choose):
                pass
            else:
                exit('登陆失败')
            t = threading.Thread(target=a.account_choose, args=(account_choose, bvid, spmid), daemon=True)
            t.start()
            time.sleep(3)
            # threading.Thread(target=b.account_choose, args=(account_choose, bvid, spmid)).start()
            # time.sleep(3)
            # t = threading.Thread(target=c.account_choose, args=(account_choose, bvid, spmid))
            # t.start()
            # time.sleep(3)
            # threading.Thread(target=d.account_choose, args=(account_choose, bvid, spmid)).start()
            # time.sleep(3)
            # t = threading.Thread(target=e.account_choose, args=(account_choose, bvid, spmid))
            # t.start()
            # time.sleep(3)
            t.join()


# BV1Zq4y1v7uB
if __name__ == '__main__':
    s0 = shipinshichang()
    t0 = threading.Thread(target=s0.start, args=(3, 'BV1i54y1f7yR', '444.42.0.0', '333.788.0.0'), daemon=True)  # 尾哥模玩
    t0.start()

    s1 = shipinshichang()
    t1 = threading.Thread(target=s1.start, args=(3, 'BV1HS4y1h7CN', '444.42.0.0', '333.788.0.0'), daemon=True)  # 平安小财娘
    # t1.start()

    s2 = shipinshichang()
    # t2 = threading.Thread(target=s1.start, args=(3, 'BV1QY411P72v', '333.999.0.0', '333.788.0.0'))#小龙坎火锅
    # t2.start()

    s3 = shipinshichang()
    t3 = threading.Thread(target=s3.start, args=(3, 'BV1m34y1a7rz', '333.999.0.0', '333.788.0.0'),
                          daemon=True)  # ALIENWARE外星人
    # t3.start()

    s4 = shipinshichang()
    t4 = threading.Thread(target=s4.start, args=(3, 'BV1qa411e7zE', '333.999.0.0', '333.788.0.0'),
                          daemon=True)  # 智行火车票官方账号
    # t4.start()

    s5 = shipinshichang()
    t5 = threading.Thread(target=s5.start, args=(3, 'BV1Zq4y1v7uB', '333.999.0.0', '333.788.0.0'),
                          daemon=True)  # DURGOD杜伽
    # t5.start()

    s6 = shipinshichang()
    t6 = threading.Thread(target=s6.start, args=(3, 'BV1xZ4y1h7GD', '333.999.0.0', '333.788.0.0'),
                          daemon=True)  # 哔哩哔哩游戏
    t6.start()

    s7 = shipinshichang()
    t7 = threading.Thread(target=s7.start, args=(3, 'BV1mS4y1c7hf', '333.999.0.0', '333.788.0.0'), daemon=True)  # 虾米大模王
    t7.start()

    s8 = shipinshichang()
    t8 = threading.Thread(target=s8.start, args=(3, 'BV1fU4y127hp', '333.999.0.0', '333.788.0.0'),
                          daemon=True)  # 苟校长想要你的关注
    t8.start()

    t0.join()
    t1.join()
    # t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    t7.join()
    t8.join()
