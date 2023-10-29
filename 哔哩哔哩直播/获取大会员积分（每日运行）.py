import json
import sys
import threading
import time

import requests

import Bilibili_methods.all_methods

myapi = Bilibili_methods.all_methods.methods()


class get_dahuiyuan_score:
    def sign(self, access_key, csrf, cookie, ua):
        url = 'https://api.bilibili.com/pgc/activity/score/task/sign'
        query = myapi.client_query({
            'access_key': access_key,
            'appkey': '1d8b6e7d45233436',
            'csrf': csrf,
            'disable_rcmd': 0,
            #'build':6830300,
            'statistics': '{"appId":1,"platform":3,"version":"6.83.0","abtest":""}',
            'ts': int(time.time()),
        })
        headers = {
            'native_api_from': 'h5',
            'cookie': cookie,
            'referer': 'https://big.bilibili.com/mobile/bigPoint/task',
            'env': 'prod',
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            'accept-encoding': 'gzip',
        }
        req = requests.post(url=url + '?{}'.format(query), headers=headers)
        print(req.text)

    def task_complete(self, taskCode, access_key, cookie, ua, csrf):
        url = 'https://api.bilibili.com/pgc/activity/deliver/task/complete'
        # data = {"csrf": csrf, "ts": int(time.time()), "taskCode": taskCode}
        query = myapi.client_query({
            'access_key': access_key,
            'appkey': '1d8b6e7d45233436',
            #'csrf': csrf,
            'build': 6830300,
            'mobi_app':'android',
            'platform':'android',
            'c_locale':'zh_CN',
            'disable_rcmd': 0,
            'position':'tv_channel',
            'statistics': '{"appId":1,"platform":3,"version":"6.83.0","abtest":""}',
            'ts': int(time.time()),
        })
        headers = {
            'app-key': 'android64',
            'cookie': cookie,
            # 'referer': 'https://big.bilibili.com/mobile/bigPoint/task',
            'fp_local': '40f1c1339ba4d10e133d2364abd3e8c520220730222401956934b05cc6cf27ff',
            'fp_remote': '40f1c1339ba4d10e133d2364abd3e8c520220730222401956934b05cc6cf27f',
            'env': 'prod',
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            'accept-encoding': 'gzip',
        }
        req = requests.post(url=url, headers=headers, data=json.dumps(data))
        print(req.text)

    def task_receive(self, taskCode, cookie, ua, csrf):
        url = 'https://api.bilibili.com/pgc/activity/score/task/receive'
        data = {"csrf": csrf, "ts": int(time.time()), "taskCode": taskCode}
        headers = {
            'native_api_from': 'h5',
            'cookie': cookie,
            'referer': 'https://big.bilibili.com/mobile/bigPoint/task',
            'env': 'prod',
            'user-agent': ua,
            'content-type': 'application/json; charset=utf-8',
            'accept-encoding': 'gzip',
        }
        req = requests.post(url=url, headers=headers, data=json.dumps(data))
        print(req.text)

    def get_task_list(self, access_key, csrf, cookie, ua):
        url = 'https://api.bilibili.com/x/vip_point/task/combine'
        query = myapi.client_query({
            'access_key': access_key,
            'appkey': '1d8b6e7d45233436',
            'csrf': csrf,
            'disable_rcmd': 0,
            'statistics': '{"appId":1,"platform":3,"version":"6.76.0","abtest":""}',
            'ts': int(time.time()),
        })
        headers = {
            'native_api_from': 'h5',
            'cookie': cookie,
            'referer': 'https://big.bilibili.com/mobile/bigPoint/task',
            'env': 'prod',
            'user-agent': ua,
            'content-type': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip',
            'app-key': 'android64'
        }
        req = requests.get(url=url + '?{}'.format(query), headers=headers)
        return req.json()

    def do(self, access_key, csrf, cookie, ua):
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
        time.sleep(1)
        print('签到：')
        self.sign(access_key, csrf, cookie, ua)
        time.sleep(3)
        print('获取任务：')
        task_req = self.get_task_list(access_key, csrf, cookie, ua)
        if task_req.get('code') != 0:
            print(task_req)
            exit('任务获取失败')
        print('当前积分：{}'.format(task_req.get('data').get('point_info').get('point')))
        for ta in task_req.get('data').get('task_info').get('modules'):
            print('当前任务模块：{}'.format(ta.get('module_title')))
            for i in ta.get('common_task_item'):
                task_code = i.get('task_code')
                state = i.get('state')
                print('当前任务名称：{}'.format(i.get('title')))
                if task_code == 'vipmallbuy':
                    print('危险任务，不做跳过')
                    print(i)
                    continue
                if task_code == 'tvodbuy':
                    print('危险任务，不做跳过')
                    print(i)
                    continue
                if task_code =='subscribe':
                    print('危险任务，不做跳过')
                    print(i)
                    continue
                if state == 3:
                    print('已完成')
                    continue
                elif state == 1:
                    print('未完成')
                elif state == 0:
                    print('未领取')
                    self.task_receive(task_code, cookie, ua, csrf)
                    time.sleep(3)
                else:
                    print('未知状态：{}'.format(state))
                    continue
                time.sleep(1)
                if task_code == 'ogvwatch':
                    for shabilini in range(2):
                        time.sleep(15 * 60)
                        self.task_complete(task_code, cookie, ua, csrf)
                    continue
                self.task_complete(task_code, cookie, ua, csrf)
                time.sleep(15)


if __name__ == '__main__':
    a = get_dahuiyuan_score()

    # a2 = 'a573f5ef87a3e8b88d7e087cc1ec1471'
    # csrf2 = '12417f18057aa968b83fb61ffd143c6a'
    # cookie2 = "SESSDATA=beef50c7%2C1673626044%2C30a43171; bili_jct=12417f18057aa968b83fb61ffd143c6a; DedeUserID=9295261; DedeUserID__ckMd5=3bfb1ad10a04371c; sid=5rdd0g9o; Buvid=XZ8DEF78CA41F969EDAE3BDCAB6EFD7D5AC7E"
    # ua2 = 'Mozilla/5.0 (Linux; Android 6.0.1; MuMu Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Mobile Safari/537.36 os/android model/MuMu build/6750300 osVer/6.0.1 sdkInt/23 network/2 BiliApp/6750300 mobi_app/android channel/html5_search_baidu Buvid/XZ8DEF78CA41F969EDAE3BDCAB6EFD7D5AC7E sessionID/4215d3d1 innerVer/6750310 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 6.75.0 os/android model/MuMu mobi_app/android build/6750300 channel/html5_search_baidu innerVer/6750310 osVer/6.0.1 network/2'
    #
    # a3 = '680bc812e0980f5f88a9684f1def3171'
    # csrf3 = 'e824ac97526ba888842b37360394a69e'
    # cookie3 = "SESSDATA=9b911090%2C1673805615%2C03857071; bili_jct=e824ac97526ba888842b37360394a69e; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; sid=g5vdct6g; Buvid=XZ7EEF279C87294D4E446DD9A1DE907314BA3"
    # ua3 = 'Mozilla/5.0 (Linux; Android 6.0.1; oppo R11s Plus Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Mobile Safari/537.36 os/android model/oppo R11s Plus build/6760200 osVer/6.0.1 sdkInt/23 network/2 BiliApp/6760200 mobi_app/android channel/html5_app_bili Buvid/XZ7EEF279C87294D4E446DD9A1DE907314BA3 sessionID/69e6b0cb innerVer/6760210 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 6.76.0 os/android model/oppo R11s Plus mobi_app/android build/6760200 channel/html5_app_bili innerVer/6760210 osVer/6.0.1 network/2'

    a1 = 'f6e073c2df05183961bdb41e36b2d171'
    csrf1 = '70c36b823afc783e47cbefbb1c0c616a'
    cookie1 = "SESSDATA=30a464c6%2C1674744749%2C52dfdb71; bili_jct=70c36b823afc783e47cbefbb1c0c616a; DedeUserID=4237378; DedeUserID__ckMd5=94093e21fe6687f9; sid=gcbk4bcy; Buvid=XZ03DA107F60CD4A53D3E2CC798D89505A521"
    ua1 = "Mozilla/5.0 BiliDroid/6.83.0 (bbcallen@gmail.com) os/android model/MuMu mobi_app/android build/6830300 channel/html5_search_baidu innerVer/6830310 osVer/6.0.1 network/2"

    t = threading.Thread(target=a.do, args=(a1, csrf1, cookie1, ua1))
    t.start()
    t.join()
    # t1=threading.Thread(target=a.do,args=(a2, csrf2, cookie2, ua2))
    # t2=threading.Thread(target=a.do,args=(a3,csrf3,cookie3,ua3))
    # t1.start()
    # t2.start()
    # t1.join()
    # t2.join()
