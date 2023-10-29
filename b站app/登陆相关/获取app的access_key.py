import math
import random
import time
from hashlib import md5
import requests
import Bilibili_methods.all_methods as myapi
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl

BAPI = myapi.methods()


class BilibiliToken:
    def __init__(self, cookie):
        def get_csrf(_cookie):
            c_s = _cookie.split(';')
            for i in c_s:
                if i != '':
                    k = i.split('=')[0].strip()
                    v = i.split('=')[1].strip()
                    if k == "bili_jct":
                        return v

        self.csrf = get_csrf(cookie)
        self.fingerprint = self.RandomID(62)
        self.__loginSecretKey = '59b43e04ad6965f34319062b478f83dd'
        self.loginAppKey = '4409e2ce8ffd12b8'
        self.__secretKey = '560c52ccd288fed045859ed18bffd973'
        self.appKey = '1d8b6e7d45233436'
        self.build = '102401'
        self.channel = 'master'
        self.device = 'Sony'
        self.deviceName = 'J9110'
        self.devicePlatform = 'Android10SonyJ9110'
        self.mobiApp = 'android_tv_yst'
        self.networkstate = 'wifi'
        self.platform = 'android'
        self.buvid = self.get_buvid()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 BiliDroid/6.73.1 (bbcallen@gmail.com) os/android model/Mi 10 Pro mobi_app/android build/6731100 channel/xiaomi innerVer/6731110 osVer/12 network/2',
            'APP-KEY': self.mobiApp,
            'Buvid': self.buvid,
            'env': 'prod',
            'cookie': cookie
        }
        self.biliLocalId = self.RandomID(20)
        self.deviceId = self.RandomID(20)
        self.this_LoginQuery = self.loginQuery()

    def getAuthCode(self):
        url = 'https://passport.bilibili.com/x/passport-tv-login/qrcode/auth_code'
        data = self.signLoginQuery()
        req = requests.post(url=url + '?' + data, headers=self.headers)
        if req.status_code == 200 and req.json().get('code') == 0:
            return req.json().get('data').get('auth_code')
        else:
            print(req.json())
            print(data)
            exit('二维码获取失败')

    def get_buvid(self):
        return self.RandomID(37).upper()

    def RandomID(self, length):
        words = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        randomID = ''
        randomID += words[math.floor(random.random() * 61) + 1]
        for i in range(length):
            randomID += words[math.floor(random.random() * 62)]
        return randomID

    def signQuery(self, params, ts=True, secretKey='59b43e04ad6965f34319062b478f83dd'):
        paramsSort = params
        p_dict = dict()
        for i in paramsSort.split('&'):
            p_dict.update({i.split('=')[0]: i.split('=')[1]})
        k = p_dict.keys()
        a = sorted(k)
        for i in range(len(a)):
            a[i] += f'={p_dict[a[i]]}'
        paramsSort = '&'.join(a)
        if (ts):
            paramsSort = f'{paramsSort}&ts={int(time.time())}'
        paramsSecret = paramsSort + secretKey
        paramsHash = md5(paramsSecret.encode())
        return f'{paramsSort}&sign={paramsHash.hexdigest()}'

    def loginQuery(self):
        biliLocalId = self.biliLocalId
        buvid = self.get_buvid()
        fingerprint = self.fingerprint
        return f'''appkey={self.loginAppKey}&bili_local_id={biliLocalId}&build={self.build}&buvid={buvid}&channel={self.channel}&device={biliLocalId}&device_id={self.deviceId}&device_name={self.deviceName}&device_platform={self.devicePlatform}&fingerprint={self.fingerprint}&guid={buvid}&local_fingerprint={fingerprint}&local_id={buvid}&mobi_app={self.mobiApp}&networkstate={self.networkstate}&platform={self.platform}'''

    def signLoginQuery(self, *params):
        if params == ():
            paramsBase = self.this_LoginQuery
        else:
            paramsBase = f'{params[0]}&{self.this_LoginQuery}'
        return self.signQuery(paramsBase, True, self.__loginSecretKey)

    def qrcodeConfirm(self, authCode, csrf):
        url = 'https://passport.bilibili.com/x/passport-tv-login/h5/qrcode/confirm'
        data = f'auth_code={authCode}&csrf={csrf}'
        headers = self.headers
        req = requests.post(url=url + '?' + data, data=data, headers=headers)
        if req.status_code == 200 and req.json().get('code') == 0:
            return req.json().get('data').get('gourl')
        else:
            print(req.json())
            print(authCode, csrf)
            exit('二维码确认失败')

    def qrcodePoll(self, authCode):
        url = 'https://passport.bilibili.com/x/passport-tv-login/qrcode/poll'
        data = self.signLoginQuery(f'auth_code={authCode}')
        req = requests.post(url=url + '?' + data, headers=self.headers, data=data)
        if req.status_code == 200 and req.json().get('code') == 0:
            return req.json().get('data')
        else:
            print(req.headers)
            print(req.json())
            print(authCode)
            print(data)
            exit('获取token失败')

    def getToken(self):
        authCode = self.getAuthCode()
        if authCode == None:
            exit('authCode==None')
        time.sleep(3)
        confirm = self.qrcodeConfirm(authCode, self.csrf)
        if confirm == None:
            exit('confirm==None')
        time.sleep(3)
        token = self.qrcodePoll(authCode)
        if token == None:
            exit('token==None')
        print(token)
        return token.get('access_token')


if __name__ == '__main__':
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

    cookie5 = gl.get_value('cookie5')
    fullcookie5 = gl.get_value('fullcookie5')
    ua5 = gl.get_value('ua5')
    fingerprint5 = gl.get_value('fingerprint5')
    csrf5 = gl.get_value('csrf5')
    a = BilibiliToken(cookie5)
    print(a.getToken())
