import json
import random
import sys
import time

import numpy
import requests
import Bilibili_methods.all_methods
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl

BAPI = Bilibili_methods.all_methods.methods()


class thumb_dynamic_from_space:
    def __init__(self):
        self.sparetime = 10 * 24 * 60 * 60
        self.n = 0
        self.sleeptime = numpy.linspace(2, 6, 500, endpoint=False)
        self.is_liked_limit = 2
        self.is_liked_count = 0
        self.User_Agent_List = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) '
            'Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 '
            'Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 '
            'Safari/535.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; '
            '.NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, '
            'like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) '
            'Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) '
            'Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, '
            'like Gecko) Version/4.0 Mobile Safari/533.1',
            'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
            'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
            'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
            'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
            'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999'
        ]

    def _do_task(self, uid, cookie, ua, csrf):
        def login_check(_cookie, _ua):
            _headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=_headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(cookie, ua)
        offset = 0
        while 1:
            data = {
                'visitor_uid': uid,
                'host_uid': uid,
                'offset_dynamic_id': offset,
                'need_top': 0,
                'platform': 'web'
            }
            headers = {'user-agent': ua,
                       'cookie': cookie,
                       }
            url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=0&host_uid={mid}' \
                  '&offset_dynamic_id={offset}&need_top=0'.format(mid=uid, offset=offset)
            req = requests.request('GET', url=url, headers=headers, data=data)
            req_dict = json.loads(req.text)
            cards = req_dict.get('data').get('cards')
            has_more = req_dict.get('data').get('has_more')
            if has_more:
                pass
            else:
                exit('无更多动态')
            offset = req_dict.get('data').get('next_offset')
            for card in cards:
                try:
                    dynamic_id = str(eval(card.get('desc').get('dynamic_id_str')))
                    dynamic_url = 'https://t.bilibili.com/' + dynamic_id + '?tab=2'
                    dynamic_rid = str(card.get('desc').get('rid'))
                    dynamic_repostcount = card.get('desc').get('repost')
                    dynamic_commentcount = card.get('desc').get('comment')
                    dynamic_is_liked = card.get('desc').get('is_liked')
                    dynamic_type = str(card.get('desc').get('type'))
                    card_stype=''
                    if dynamic_type==8:
                        card_stype='DYNAMIC_TYPE_AV'
                    elif dynamic_type==2:
                        card_stype='DYNAMIC_TYPE_DRAW'
                    elif dynamic_type==1:
                        card_stype='DYNAMIC_TYPE_FORWARD'
                    elif dynamic_type==64:
                        card_stype='DYNAMIC_TYPE_ARTICLE'
                    dynamic_timestamp = card.get('desc').get('timestamp')
                    dynamic_uname = card.get('desc').get('user_profile').get('info').get('uname')
                    dynamic_uid = card.get('desc').get('user_profile').get('info').get('uid')
                    self.n += 1
                    print('第' + str(self.n) + '次获取动态')
                    print(BAPI.timeshift(time.time()))
                    print('up主：{name}'.format(name=dynamic_uname))
                    print('空间主页：https://space.bilibili.com/{uid}'.format(uid=dynamic_uid))
                    print('动态url：' + dynamic_url)
                    print('发布时间：' + BAPI.timeshift(dynamic_timestamp))
                except Exception as e:
                    print('获取个人信息失败：')
                    print(card)
                    print(e)
                    time.sleep(eval(input('输入等待时间')))
                    break
                if dynamic_type == '2048':
                    print('换装扮动态跳过')
                    continue
                if int(time.time()) - dynamic_timestamp >= self.sparetime:
                    exit('十天前的动态')
                if self.is_liked_count >= self.is_liked_limit:
                    exit('超出遇到点赞过的动态上限')
                if str(dynamic_is_liked) == '1':
                    self.is_liked_count += 1
                    print('遇到点过赞的动态')
                    continue
                else:
                    print('未点赞的动态')
                BAPI.thumb(dynamic_id, cookie, ua, uid, csrf,card_stype)
                time.sleep(random.choice(self.sleeptime))
            time.sleep(3 * random.choice(self.sleeptime))

    def account_choose(self, accountname):
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
            self._do_task(uid=uid1, csrf=csrf1, cookie=cookie1, ua=ua1)
        elif accountname == 2:
            print(uid2)
            self._do_task(uid=uid2, csrf=csrf2, cookie=cookie2, ua=ua2)
        elif accountname == 3:
            print(uid3)
            self._do_task(uid=uid3, csrf=csrf3, cookie=cookie3, ua=ua3)
        elif accountname == 4:
            print(uid4)
            self._do_task(uid=uid4, csrf=csrf4, cookie=cookie4, ua=ua4)


if __name__ == '__main__':
    myt = thumb_dynamic_from_space()
    myt.account_choose(4)
