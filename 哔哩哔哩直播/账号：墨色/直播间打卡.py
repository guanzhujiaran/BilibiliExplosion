# -*- coding:utf- 8 -*-
import json
import random
import time

import numpy
import requests

# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl


class feed:
    def __init__(self):
        self.page = 1
        self.dakashibai = {}
        self.page_fail = []
        self.msg = '.'
        open('粉丝勋章.txt', 'w', encoding='utf-8')

    def get_medal(self, cookie, ua):
        url = 'https://api.live.bilibili.com/xlive/app-ucenter/v1/user/GetMyMedals?page={page}&page_size=10'.format(
            page=self.page)
        data = {
            'page': self.page,
            'page_size': '10'
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "Content-Type": "application/json"
        }
        req = requests.request("GET", url=url, data=json.dumps(data), headers=headers)
        req_dict = req.json()
        return req_dict

    def main(self, msg, csrf, cookie, ua):
        req_dict = self.get_medal(cookie, ua)
        items = req_dict.get('data').get('items')
        if items != None:
            self.sendmsg(items, csrf, cookie, ua)
            time.sleep(random.choice(sleeptime))
        else:
            print('第{page}获取失败'.format(page=self.page))
            self.page_fail.append(self.page)
            print(req_dict)
            while 1:
                try:
                    # time.sleep(int(input('输入等待时间')))
                    time.sleep(1)
                    break
                except:
                    print('输入错误')
        total_page = req_dict.get('data').get('page_info').get('total_page')
        for self.page in range(2, total_page + 1):
            req_dict = self.get_medal(cookie, ua)
            items = req_dict.get('data').get('items')
            if items != None:
                self.sendmsg(items, csrf, cookie, ua)
                time.sleep(random.choice(sleeptime))
            else:
                print('第{page}获取失败'.format(page=self.page))
                self.page_fail.append(self.page)
                print(req_dict)
                while 1:
                    try:
                        # time.sleep(int(input('输入等待时间')))
                        time.sleep(1)
                        break
                    except:
                        print('输入错误')
                time.sleep(random.choice(sleeptime))
        print('打卡失败：')
        for i, j in self.dakashibai.items():
            print(i, j)
        print('获取失败页数：')
        print(self.page_fail)

    def sendmsg(self, itemlist, csrf, cookie, ua):
        for myitem in itemlist:
            msg = self.randemo()
            try:
                target_name = myitem.get('uname')
                level = myitem.get('level')
                roomid = myitem.get('roomid')
                today_feed = myitem.get('today_feed')
            except Exception as e:
                print(e)
                self.page_fail.append(self.page)
                print('第{page}数据获取失败'.format(page=self.page))
                continue
            if today_feed >= 100:
                sign_status = '已打卡'
            else:
                sign_status = '未打卡'
            print('主播昵称：{uname}\t房间号：{roomid}\t勋章等级：{level}\t今日打卡状态：{sign_status}'.format(uname=target_name,
                                                                                          roomid=roomid, level=level,
                                                                                          sign_status=sign_status))
            if sign_status == '已打卡':
                continue
            if roomid == 0:
                print('直播间不存在')
                continue
            print('打卡中......')
            real_roomid_dict = self.get_real_roomid(roomid)
            with open('粉丝勋章.txt', 'a+', encoding='utf-8') as f:
                f.writelines('{}\t{}\n'.format(real_roomid_dict, level))
            try:
                if real_roomid_dict.get('code') != 0 or real_roomid_dict.get('code') is None:
                    print('获取真实房间号失败')
                else:
                    roomid = real_roomid_dict.get('data').get('room_id')
                    live_time = real_roomid_dict.get('data').get('live_time')
                    live_status = real_roomid_dict.get('data').get('live_status')

                    if live_status == 1:
                        print('正在直播\t直播时长：{livetime}小时'.format(livetime=(int(time.time()) - live_time) / 3600))
                    elif live_time == 2:
                        print('未直播：\t轮播投稿视频中')
                    else:
                        print('未直播')
            except:
                print('主播昵称：{name}\t获取真实房间号失败'.format(name=target_name))
                self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                while 1:
                    try:
                        # time.sleep(int(input('输入等待时间')))
                        time.sleep(1)
                        break
                    except:
                        print('输入错误')
            url = 'https://api.live.bilibili.com/msg/send'
            data = {
                'bubble': 0,
                'msg': msg,
                'color': 5816798,
                'mode': 1,
                'dm_type': 1,
                'fontsize': 25,
                'rnd': int(time.time()),
                'roomid': roomid,
                'csrf': csrf,
                'csrf_token': csrf
            }
            headers = {
                'cookie': cookie,
                'user-agent': ua,
            }
            try:
                req = requests.request("POST", url=url, data=data, headers=headers)
                if req.json().get('message') == '' and req.json().get('code') == 0:
                    print('打卡成功\t弹幕内容：{msg}'.format(msg=msg))
                elif req.json().get('message') == 'k' and req.json().get('code') != 1100:
                    print('弹幕可能被屏蔽\n尝试换弹幕重新打卡')
                    msg1 = '1'
                    time.sleep(random.choice(sleeptime))
                    res = self.single_sendmsg(target_name, roomid, csrf, cookie, ua)
                    if res == 'k':
                        time.sleep(random.choice(sleeptime))
                        self.dakashibai.update(
                            {target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                        print(req.json())
                        print('打卡失败')
                        while 1:
                            try:
                                # time.sleep(int(input('输入等待时间')))
                                time.sleep(1)
                                break
                            except:
                                print('输入错误')
                    elif res == '':
                        print('再次打卡成功\t弹幕内容：{msg}'.format(msg=msg1))
                        time.sleep(random.choice(sleeptime))
                        continue
                    else:
                        self.dakashibai.update(
                            {target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                        print(res)
                        print('打卡失败')
                        while 1:
                            try:
                                # time.sleep(int(input('输入等待时间')))
                                time.sleep(1)
                                break
                            except:
                                print('输入错误')
                        continue
                elif req.json().get('code') == -403:
                    self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                    print('打卡失败\t原因：{message}'.format(message=req.json().get('message')))
                else:
                    self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                    print(req.json())
                    print('打卡失败')
                    while 1:
                        try:
                            # time.sleep(int(input('输入等待时间')))
                            time.sleep(1)
                            break
                        except:
                            print('输入错误')
            except:
                print('房间：https://live.bilibili.com/{roomid}  弹幕发送失败'.format(roomid=roomid))
                self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                while 1:
                    try:
                        # time.sleep(int(input('输入等待时间')))
                        time.sleep(1)
                        break
                    except:
                        print('输入错误')
            time.sleep(random.choice(sleeptime))

    def single_sendmsg(self, target_name, roomid, csrf, cookie, ua):
        url = 'https://api.live.bilibili.com/msg/send'
        msg = self.randemo()
        data = {
            'bubble': 0,
            'msg': msg,
            'color': 5816798,
            'mode': 1,
            'dm_type': 1,
            'fontsize': 25,
            'rnd': int(time.time()),
            'roomid': roomid,
            'csrf': csrf,
            'csrf_token': csrf
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
        }
        try:
            req = requests.request("POST", url=url, data=data, headers=headers)
            if req.json().get('message') == '':
                print('打卡成功\t弹幕内容：{msg}'.format(msg=msg))
                req.json().get('message')
                return req.json().get('message')
            elif req.json().get('message') == 'k':
                self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                print(req.json())
                print('打卡失败')
                return req.json().get('message')
            elif req.json().get('code') == -403:
                self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                print('打卡失败\t原因：{message}'.format(message=req.json().get('message')))
            else:
                self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
                print(req.json())
                print('打卡失败')
                return req.json().get('message')
        except Exception as e:
            print(e)
            print('房间：https://live.bilibili.com/{roomid}  弹幕发送失败'.format(roomid=roomid))
            self.dakashibai.update({target_name: 'https://live.bilibili.com/{roomid}'.format(roomid=roomid)})
            while 1:
                try:
                    # time.sleep(int(input('输入等待时间')))
                    time.sleep(1)
                    break
                except:
                    print('输入错误')
        time.sleep(random.choice(sleeptime))

    def get_real_roomid(self, roomid):
        url = 'https://api.live.bilibili.com/room/v1/Room/room_init?id={roomid}'.format(roomid=roomid)
        req = requests.get(url=url)
        return req.json()

    def account_choose(self, accountname, *msg):
        if msg == ():
            msg = self.msg
        cookie1 = gl.get_value('cookie1')  # 星瞳
        fullcookie1 = gl.get_value('fullcookie1')
        ua1 = gl.get_value('ua1')
        fingerprint1 = gl.get_value('fingerprint1')
        csrf1 = gl.get_value('csrf1')
        uid1 = gl.get_value('uid1')
        cookie2 = gl.get_value('cookie2')  # 保加利亚
        fullcookie2 = gl.get_value('fullcookie2')
        ua2 = gl.get_value('ua2')
        fingerprint2 = gl.get_value('fingerprint2')
        csrf2 = gl.get_value('csrf2')
        uid2 = gl.get_value('uid2')
        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        fullcookie3 = gl.get_value('fullcookie3')
        ua3 = gl.get_value('ua3')
        fingerprint3 = gl.get_value('fingerprint3')
        csrf3 = gl.get_value('csrf3')
        uid3 = gl.get_value('uid3')
        cookie4 = gl.get_value('cookie4')  # 墨色
        fullcookie4 = gl.get_value('fullcookie4')
        ua4 = gl.get_value('ua4')
        fingerprint4 = gl.get_value('fingerprint4')
        csrf4 = gl.get_value('csrf4')
        uid4 = gl.get_value('uid4')
        if accountname == 1:
            print(uid1)
            self.main(msg, csrf1, cookie1, ua1)
        elif accountname == 2:
            print(uid2)
            self.main(msg, csrf2, cookie2, ua2)
        elif accountname == 3:
            print(uid3)
            self.main(msg, csrf3, cookie3, ua3)
        elif accountname == 4:
            print(uid4)
            self.main(msg, csrf4, cookie4, ua4)

    def randemo(self):
        return 'official_' + random.choice(
            ['124', '109', '113', '103', '128', '133', '120', '102', '121', '137', '118', '129', '108', '104', '105',
             '106', '114', '107', '110', '111', '136', '115',
             '116', '117', '119', '122', '123', '125', '126', '127', '131', '134', '135', '138'

             ])


if __name__ == '__main__':
    sleeptime = numpy.linspace(1.2, 1.3, 500, endpoint=False)
    myfeed = feed()
    myfeed.account_choose(4)
    # 1：星瞳
    # 2：保加利亚
    # 3：斯卡蒂
    # 4：墨色
