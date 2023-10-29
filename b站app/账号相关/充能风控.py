# noinspection PyUnresolvedReferences
import random
import time

import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import requests
import Bilibili_methods.all_methods as myapi

api = myapi.methods()

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


def get_buvid():
    s = [''] * 37
    for i in range(len(s)):
        if i == 0:
            s[0] = 'X'
        else:
            s[i] = random.choice('1234567890ABCDEFG')
    return ''.join(s)


def charge_start(ac_key, cookie, ua, csrf):
    url = 'https://api.bilibili.com/x/fission/charge/start'
    data = {
        'access_key': ac_key,
        'activity_uid': 'charge',
        'prize_id': 25,
        'buvid': get_buvid(),
        'appKey': '1d8b6e7d45233436',
        'csrf': csrf,
        'ts': int(time.time())
    }
    data = api.client_query(data)
    headers = {
        'native_api_from': 'h5',
        'cookie': cookie,
        'env': 'prod',
        'app-key': 'android64',
        'refer': 'https://www.bilibili.com/blackboard/powerup.html?from=wode&native.theme=1#/select',
        'user-agent': ua,
        'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
        'accept-encoding': 'gzip'
    }
    req = requests.post(url=url, headers=headers, data=data)
    print(data)
    print(req.text)


#get_buvid()
charge_start('83b05d0b1f84a507e61d79c04e623681',
             '{"DedeUserID": "1905702375", "DedeUserID__ckMd5": "e66cfea7736b82c2", "SESSDATA": "9c36b453%2C1673157144%2Cd69a9%2A71", "bili_jct": "4dc41d46d793bbd802c8e40d9935ae89", "sid": "6u9nxve9"}',
             'Mozilla/5.0 (Linux; Android 6.0.1; oppo R11s Plus Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/89.0.4389.72 MBrowser/6.2 TBS/045947 Mobile Safari/537.36 os/android model/oppo R11s Plus build/6890300 osVer/6.0.1 sdkInt/23 network/2 BiliApp/6890300 mobi_app/android channel/html5_app_bili Buvid/XZ7EEF279C87294D4E446DD9A1DE907314BA3 sessionID/04498744 innerVer/6890310 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 6.89.0 os/android model/oppo R11s Plus mobi_app/android build/6890300 channel/html5_app_bili innerVer/6890310 osVer/6.0.1 network/2',
             '4dc41d46d793bbd802c8e40d9935ae89')
