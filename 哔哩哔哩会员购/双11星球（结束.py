# -*- coding:utf- 8 -*-
import json
import re
import time
import requests
import threading

cookie1 = "SESSDATA=42cf407e%2C1651592331%2C32e71%2Ab1; bili_jct=a7f26cd629a3bd2f22cd1cd711632e44"  # 星瞳
ua1 = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
fingerprint1 = "6fa96349870c171da6cbb5b9e5e2ffc5"
csrf1 = 'a7f26cd629a3bd2f22cd1cd711632e44'
cookie2 = "SESSDATA=c356c770%2C1642774741%2C1f708%2A71;bili_jct=62a12e951547a821766e96d357b3ebf9"  # 保加利亚
ua2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
fingerprint2 = "d1fa3b0ab0a0d2381a3e5c6b0d8c8f2b"
csrf2 = '62a12e951547a821766e96d357b3ebf9'
cookie3 = "SESSDATA=39711a5b%2C1642327077%2C2fa6d*71;bili_jct=03c7d35e2356c18331aab9c2cd366fcc"  # 斯卡蒂
ua3 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
fingerprint3 = "47538e1dae68a064f0c04d34624ce6aa"
csrf3 = '03c7d35e2356c18331aab9c2cd366fcc'
cookie4 = "SESSDATA=81555c44%2C1643861438%2C46da9%2A81;bili_jct=5aef2590e38b30bf81da9faf5df34025"  # 墨色
ua4 = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3872.400 QQBrowser/10.8.4476.400"
fingerprint4 = "7f03261cac94d1a678410d4e5f269c5f"
csrf4 = '5aef2590e38b30bf81da9faf5df34025'
shareids = ['qg6yvdo3or', 'qdxm1y856r', '304lzg9mwq', 'm0eyny8kq4', 'qg5gzn51o0', '032pgwpvoq', '0j32y75g8q',
            '50oknm6vlq', '50ove1315r', 'wqd7m946xq', 'wqdm4dvxxq', 'r7pp73y5lr']


class shuang11:
    @classmethod
    def get_task(cls, cookie, ua):
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
            introTask = data_dict.get('introTask').get('stages')
            newerTaskList = data_dict.get('newerTaskList')
            stages = data_dict.get('powerModule').get('stages')
            detail.append(everyDayTaskList)
            detail.append(introTask)
            detail.append(newerTaskList)
            detail.append(stages)
        except Exception as e:
            print(req)
            print(e)
        return detail

    @classmethod
    def pk(cls, cookie, ua, deviceprint, shareid):
        url = 'https://show.bilibili.com/api/activity/fire/resident/pk'
        data = {'deviceId': deviceprint,
                'opponentCode': shareid
                }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "accept - encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "content - length": "75",
            "sec - ch - ua - platform": "android",
            "origin": "https: // mall.bilibili.com",
            "referer": "https://mall.bilibili.com/zq/starpartying20211111/?noTitleBar=1&fightCode=" + str(shareid),
            "accept - language": "zh - CN, zh;q = 0.9"
        }
        data = json.dumps(data)
        req = requests.post(url=url, data=data, headers=headers)
        req = json.loads(req.text)
        print(req.get('message'))
        return req.get('message')

    @classmethod
    def dailypk(cls, cookie, ua, deviceprint):  # 10次
        url = 'https://show.bilibili.com/api/activity/fire/resident/pk'
        data = {'deviceId': deviceprint,
                }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            "accept - encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "content - length": "75",
            "sec - ch - ua - platform": "android",
            "origin": "https: // mall.bilibili.com",
            "referer": "https://mall.bilibili.com/zq/starpartying20211111/?noTitleBar=1",
            "accept - language": "zh - CN, zh;q = 0.9"
        }
        data = json.dumps(data)
        req = requests.post(url=url, data=data, headers=headers)
        req = json.loads(req.text)
        print(req.get('message'))

    @classmethod
    def receive(clf, cookie, ua, fingerprint, prizeid):
        url = 'https://show.bilibili.com/api/activity/fire/resident/receive-reward'
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
            return req.text
        return req

    @classmethod
    def dispatch(cls, cookie, ua, eventid, csrf, jumpurl):
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

    @classmethod
    def draw_lottery(cls, cookie, ua, activityid):
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
            url = 'https://mall.bilibili.com/mall-dayu/mall-marketing-core/lottery_prize/draw_subsidy'
            data = {"recordId": recordid}
            data = json.dumps(data)
            req = requests.post(url=url, data=data, headers=headers)
            print(req.text)
        except Exception as e:
            print('抽奖失败')
            print(req.text)

    def start(self, cookie, ua, csrf, fingerprint):
        print('日常PK')
        for i in range(15):
            shuang11.dailypk(cookie=cookie, ua=ua, deviceprint=fingerprint)
            time.sleep(3)
        print('邀请pk')
        for i in shareids:
            time.sleep(5)
            res = shuang11.pk(cookie, ua, fingerprint, i)
            time.sleep(10)
            if res == '今日应战次数已经达到上限':
                break
        task = shuang11.get_task(cookie, ua)
        for i in task:
            for j in i:
                status = j.get('status')
                jumpurl = j.get('jumpUrl')
                taskdesc = j.get('taskDesc')
                prizename = j.get('prizeName')
                if status == 'GOING' and jumpurl != '' and prizename == '6魔晶':
                    print('浏览现货会场10秒')
                    eventid = re.findall('eventId=(.*?)&', jumpurl)[0]
                    time.sleep(10)
                    shuang11.dispatch(cookie, ua, eventid, csrf, jumpurl)
                    time.sleep(5)
        task = shuang11.get_task(cookie, ua)
        time.sleep(2)
        for i in task:
            for j in i:
                status = j.get('status')
                prizeid = j.get('prizeId')
                if status == 'FINISHED':
                    print(shuang11.receive(cookie, ua, fingerprint, prizeid))
                    time.sleep(3)
        shuang11.draw_lottery(cookie, ua, '2021103131212003')
        time.sleep(5)
        shuang11.draw_lottery(cookie, ua, '2021103131233004')
        time.sleep(5)


if __name__ == '__main__':
    b23 = shuang11()
    ac1 = threading.Thread(target=b23.start, args=(cookie1, ua1, csrf1, fingerprint1))
    ac2 = threading.Thread(target=b23.start, args=(cookie2, ua2, csrf2, fingerprint2))
    ac3 = threading.Thread(target=b23.start, args=(cookie3, ua3, csrf3, fingerprint3))
    ac4 = threading.Thread(target=b23.start, args=(cookie4, ua4, csrf4, fingerprint4))
    ac1.start()
    time.sleep(10)
    ac2.start()
    time.sleep(10)
    ac3.start()
    time.sleep(10)
    ac4.start()
    ac1.join()
    ac2.join()
    ac3.join()
    ac4.join()
