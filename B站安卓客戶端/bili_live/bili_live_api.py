import asyncio
import atexit
import json
import random
import time
import traceback

import execjs
import numpy
import requests
import Bilibili_methods.all_methods
from CONFIG import CONFIG

mymethod = Bilibili_methods.all_methods.methods()


class bili_live_api:
    def __init__(self):
        self.p = [
            {'http': 'http://218.7.171.91:3128'},
            {'http': 'http://59.124.224.205:3128'},
            # {'http': 'http://47.57.188.208:80'},
            {'http': 'http://47.92.113.71:80'},
            {'http': 'http://218.244.147.59:3128'},
            # {'http': 'http://58.220.95.8:10174'},
            # {'http': 'http://58.220.95.32:10174'},
            {'http': 'http://221.5.80.66:3128'},
            {'http': 'http://58.220.95.79:10000'},
            {'http': 'http://58.220.95.86:9401'}
        ]
        self.shortsleeptime = numpy.linspace(1, 3, 500, endpoint=True)
        self.room_id2ruid_dict = dict()
        self.unknown_roomid = dict()
        try:
            with open(CONFIG.root_dir+'哔哩哔哩直播/roomd_id对应ruid.txt', 'r', encoding='utf-8') as r:
                if r:
                    for i in r:
                        self.room_id2ruid_dict.update({i.split('\t')[0]: i.split('\t')[1]})
        except:
            f = open(CONFIG.root_dir+'哔哩哔哩直播/roomd_id对应ruid.txt', 'w', encoding='utf-8')
            f.close()
        atexit.register(self.quit_write_in_file)

    def quit_write_in_file(self):
        for i, j in self.unknown_roomid.items():
            with open(CONFIG.root_dir+'哔哩哔哩直播/roomd_id对应ruid.txt', 'a+', encoding='utf-8') as r:
                r.writelines('{}\t{}\n'.format(i, j))

    def Dosign(self, cookie, ua):
        url = 'https://api.live.bilibili.com/xlive/web-ucenter/v1/sign/DoSign'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        # code: 0
        # data: {text: "3000点用户经验,2根辣条,50根辣条", specialText: "", allDays: 28, hadSignDays: 20, isBonusDay: 1}
        # allDays: 28
        # hadSignDays: 20
        # isBonusDay: 1
        # specialText: ""
        # text: "3000点用户经验,2根辣条,50根辣条"
        # message: "0"
        # ttl: 1
        return req.json()

    def silvertocoin(self, cookie, ua, csrf, visit_id):
        url = 'https://api.live.bilibili.com/xlive/revenue/v1/wallet/silver2coin'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        data = {
            'csrf_token': csrf,
            'csrf': csrf,
            'visit_id': visit_id
        }
        req = requests.post(url=url, data=data, headers=headers)
        return req.json()

    def get_data_from_server(self):  # 1.12.36.165
        url = 'http://1.12.36.165:1369/sync/get_users/kasfdhjakwda1qwsd15wad4q5aqfhhjc?skip=0&limit=80'  # 1.117.77.42
        headers = {
            "Content-Type": "application/json", "Connection": "close",
                   # 'Host':'1.12.36.165:1369',
                   }
        while 1:
            try:
                myp = random.choice(self.p)
                print(myp)
                time.sleep(1)
                req = requests.get(url=url, headers=headers, proxies=random.choice(self.p), timeout=5)
                break
            except Exception as e:
                print('获取服务器资源失败')
                # print(e)
                print(self.p)
                # traceback.print_exc(limit=5)
                time.sleep(0)
                # self.p.remove(myp)
                return self.get_data_from_server()
        # [{'id': 1645289295787, 'room_id': 1205562960, 'data': '在线打卡', 'updated_at': '2022-02-19T16:48:16', 'created_at': '2022-02-19T16:48:16'}, {'id': 1645289288926, 'room_id': 1653298746, 'data': '在线打卡', 'updated_at': '2022-02-19T16:48:10', 'created_at': '2022-02-19T16:48:10'}]
        #
        try:
            return req.json()
        except:
            #print(req.text)
            #print(myp)
            return []

    def daka(self):
        url = 'https://1.12.36.165:1369/sync/input/'
        data = {'id': int(time.time()), 'room_id': 208259, 'data': "在线打卡"}
        headers = {"Content-Type": "application/json", "Connection": "close"}
        req = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=2)
        print(req.text)

    @classmethod
    def link_group(cls, cookie, ua):
        url = 'https://api.live.bilibili.com/link_group/v1/member/my_groups'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        return req.json()

    # def check_data_form_qunserver(self):
    #    url = 'https://1.117.77.42:1369/sync/get_users/?skip=0&limit=80'
    #    headers = {"Content-Type": "application/json", "Connection": "close"}
    #    req = requests.get(url=url, headers=headers)
    #    return req.json()

    def _FollowRelation(self, uid, ruid, cookie, ua):
        url = 'https://api.live.bilibili.com/xlive/lottery-interface/v1/popularityRedPocket/FollowRelation'
        data = {
            'uid': uid,
            'target_uid': ruid
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
        }
        req = requests.get(url=url, data=data, headers=headers)
        print(req.text)
        return req.json()

    def popularity_red_pocket_join(self, uid, id, roomid, ruid, cookie, ua, csrf_token):  # //参加直播间红包
        if uid is not None and id is not None and roomid is not None and ruid is not None and cookie is not None and ua is not None and csrf_token is not None:
            self.roomEntryAction(cookie, ua, csrf_token, roomid)
            time.sleep(random.choice(self.shortsleeptime))
            self._FollowRelation(uid, ruid, cookie, ua)
            time.sleep(1)
            url = 'https://api.live.bilibili.com/xlive/lottery-interface/v1/popularityRedPocket/FollowRelation?uid={}&target_uid={}'.format(
                uid, ruid)
            headers = {
                'cookie': cookie,
                'user-agent': ua,
            }
            print(requests.get(url=url, headers=headers).json())

            url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/popularityRedPocket/RedPocketDraw"
            data = {
                'ruid': ruid,
                'room_id': roomid,
                'lot_id': id,
                'spm_id': '444.8.red_envelope.extract',
                'jump_from': '',
                'session_id': '',
                'csrf_token': csrf_token,
                'csrf': csrf_token,
                'visit_id': ''}
            data = json.dumps(data)
            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/json"
            }
            req = requests.post(url=url, data=data, headers=headers)

            # {'code': 1009106, 'message': '参数错误', 'ttl': 1, 'data': None}
            # {'code': 1009108, 'message': '不在抽奖时间段内', 'ttl': 1, 'data': None}
            # {'code': 0, 'message': '0', 'ttl': 1, 'data': {'join_status': 1}}
            if req.json() != {"code": 0, "message": "0", "ttl": 1, "data": {"join_status": 1}}:
                print('【电池红包】参与失败')
                print(req.json())
            else:
                print('\t\t\t\t【电池红包】\n\t\t\t\t房间号： https://live.bilibili.com/{} \n\t\t\t\t关注者大红包加入队列\n'.format(
                    mymethod.timeshift(time.time()), roomid))
                print('\t\t\t\t【电池红包】参与成功')
        else:
            print('【电池红包】传入参数错误，参与失败')
            return 0
        return req.json()

    def sign_in(self, cookie, ua):  # 应援团签到
        f = open('./log/应援团签到失败.csv', 'w', encoding='utf-8')
        f.close()
        url = 'https://api.live.bilibili.com/link_setting/v1/link_setting/sign_in'
        req = self.link_group(cookie, ua)  # 获取应援团
        time.sleep(2)
        if not req.get('code'):
            group_list = req.get('data').get('list')
            for group in group_list:
                group_id = group.get('group_id')
                owner_uid = group.get('owner_uid')
                group_type = group.get('group_type')
                group_level = group.get('group_level')
                fans_medal_name = group.get('fans_medal_name')
                data = {
                    'group_id': group_id,
                    'owner_id': owner_uid
                }
                headers = {
                    'cookie': cookie,
                    'user-agent': ua,
                    "Content-Type": "application/json"
                }
                data = json.dumps(data)
                sign_req = requests.get(url=url, data=data, headers=headers)
                if not sign_req.json().get('code'):
                    print('粉丝勋章：{}的应援团签到结果：{}'.format(fans_medal_name, sign_req.json().get('message')))
                else:
                    with open('./log/应援团签到失败.csv', 'a+', encoding='utf-8') as f:
                        f.writelines('粉丝勋章：{}的应援团签到结果：{}\n'.format(fans_medal_name, sign_req.json().get('message')))
                time.sleep(random.choice(self.shortsleeptime))
        else:
            print('应援团签到失败')
            return 0
        return 114514

    def roomEntryAction(self, cookie, ua, visitid, csrf, room_id):
        url = 'https://api.live.bilibili.com/room/v1/Room/room_entry_action'
        data = {
            'room_id': room_id,
            'platform': 'pc',
            'csrf_token': csrf,
            'csrf': csrf,
            'visit_id': ''
        }
        headers = {
            'authority': 'api.live.bilibili.com',
            'method': 'POST',
            'path': '/xlive/web-room/v1/index/roomEntryAction',
            'scheme': 'https',
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://live.bilibili.com',
            'referer': 'https://live.bilibili.com/{}?visit_id={}'.format(room_id, visitid),
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site'
        }
        req = requests.post(url=url, data=data, headers=headers)
        return req.json()

    def get_visit_id(self, uid):
        js = execjs.compile('''
         function getvisit_id(name = NAME) {
                let str = "xxxxxxxxxxxx".replace(/[x]/g, (function (name) {
                    let randomInt = 16 * Math.random() | 0;
                    return ("x" === name ? randomInt : 3 & randomInt | 8).toString(16).toLowerCase()
                }))
                return str
            };
        ''')
        res = js.call('getvisit_id', int(uid))
        return res

    def getOnlineGoldRank(self, ruid, room_id, cookie, ua):
        url = 'https://api.live.bilibili.com/xlive/general-interface/v1/rank/getOnlineGoldRank?ruid={ruid}&roomId={room_id}&page=1&pageSize=50'.format(
            ruid=ruid, room_id=room_id)
        headers = {
            'cookie': cookie,
            'user-agent': ua,
        }
        req = requests.get(url=url, headers=headers)
        print(req.text)
        return req.json()

    def join_anchor(self, tianxuanid, gift_id, gift_num, room_id, cookie, ua, csrf, uid):  # 参加天选时刻
        if tianxuanid is not None and gift_id is not None and gift_num is not None and room_id is not None and cookie is not None and ua is not None and csrf is not None:
            visit_id = self.get_visit_id(uid)
            req = self.roomEntryAction(cookie, ua, visit_id, csrf, room_id)
            if not req.get('code'):
                print('进入直播间： https://live.bilibili.com/{} 成功'.format(room_id))
            else:
                print('进入直播间： https://live.bilibili.com/{} 失败'.format(room_id))
                print(req)
                print(cookie, ua, csrf, room_id)
            time.sleep(2 * random.choice(self.shortsleeptime))
            # self.single_sendmsg_with_emoji(random.choice(['official_135','official_109','official_113','official_149','official_106']),room_id,csrf,cookie,ua)
            # time.sleep(2 * random.choice(self.shortsleeptime))
            url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/Anchor/Join"
            print('\t\t\t\tvisit_id:{}'.format(visit_id))
            if gift_id != 0:
                data = {
                    'id': tianxuanid,
                    'gift_id': gift_id,
                    'gift_num': gift_num,
                    'room_id': room_id,
                    'platform': 'pc',
                    'session_id': '',
                    'spm_id': '444.8.interaction.anchor_draw_auto',
                    'csrf_token': csrf,
                    'csrf': csrf,
                    'visit_id': visit_id,
                    'jump_from_str': '',
                    'follow': 'true'
                }
            else:
                data = {
                    'id': tianxuanid,
                    'follow': 'true',
                    'platform': 'pc',
                    'room_id': room_id,
                    'jump_from_str': '',
                    'session_id': '',
                    'spm_id': '444.8.interaction.anchor_draw_auto',
                    'csrf_token': csrf,
                    'csrf': csrf,
                    'visit_id': visit_id
                }
            # data=json.dumps(data)
            headers = {
                'cookie': cookie,
                'user-agent': ua,
                "Content-Type": "application/x-www-form-urlencoded",
                'origin': 'https://live.bilibili.com',
                'referer': 'https://live.bilibili.com/',
                'host': 'api.live.bilibili.com',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "Windows",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'path': '/xlive/lottery-interface/v1/Anchor/Join',
                'scheme': 'https',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'method': 'POST',
                'authority': 'api.live.bilibili.com'
            }
            # data = json.dumps(data)
            # {'code': 0, 'data': {'discount_id': 0, 'gold': 0, 'silver': 0, 'cur_gift_num': 0, 'goods_id': -99998, 'new_order_id': '-99998'}, 'message': '', 'msg': ''}
            req = requests.post(url=url, data=data, headers=headers)
            if req.json().get('code'):
                print('【天选时刻】参与失败')
                print(tianxuanid, gift_id, room_id, uid)
                print(req.json())
            else:
                print('\t\t\t\t【天选时刻】参与成功')
        else:
            print('\t\t\t\t【天选时刻】传入参数错误，参与失败')
            return 0
        ruid = self.room_id2ruid_dict.get(str(room_id))
        if ruid == None:
            roominfo = self.room_ruid_info(room_id)
            ruid = roominfo.get('data').get('uid')
            self.room_id2ruid_dict.update({str(room_id): str(ruid)})
            self.unknown_roomid.update({str(room_id): str(ruid)})
        else:
            ruid = int(ruid)
        if ruid and room_id and cookie and ua:
            rank_req = self.getOnlineGoldRank(ruid, room_id, cookie, ua)
            if rank_req.get('code') == 0:
                print('观看人数：{}'.format(rank_req.get('data').get('onlineNum')))
                print('贡献值：{}'.format(rank_req.get('data').get('ownInfo').get('score')))
                print('排名：{}'.format(rank_req.get('data').get('ownInfo').get('rank')))
        else:
            print((ruid, room_id, cookie, ua))
            print('直播间排名获取失败')
        return req.json()

    def get_all_following(self, cookie, ua):
        url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id=378850887566971408'
        headers = {
            'cookie': cookie,
            'user-agent': ua,
        }
        req = requests.get(url=url, headers=headers)
        uids = req.json().get('data').get('attentions').get('uids')
        return uids

    def room_ruid_info(self, roomid):
        '''
        通过room_id获取uid等信息
        :return:
        '''
        url = 'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={}&from=room'.format(roomid)
        req = requests.get(url=url)
        return req.json()

    def send_msg_without_emoji(self, msg, rid, cookie, csrf, ua):
        url = 'https://api.live.bilibili.com/msg/send'
        data = {
            'bubble': '0',
            'msg': msg,
            'color': '16777215',
            'mode': '1 ',
            'rnd': int(time.time()),
            'fontsize': '25',
            'roomid': rid,
            'csrf': csrf,
            'csrf_token': csrf
        }
        headers = {
            "cookie": cookie,
            "user-agent": ua,
            # 'content-type': 'multipart/form-data'
        }
        response = requests.request("POST", url, headers=headers, data=data)
        response_dict = json.loads(response.text)
        print(response_dict)

    def single_sendmsg_with_emoji(self, msg, roomid, csrf, cookie, ua):
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
        req = requests.request("POST", url=url, data=data, headers=headers)
        if req.json().get('message') == '':
            print('发送成功\t弹幕内容：{msg}'.format(msg=msg))
            m = req.json().get('message')
            print(m)
            return req.json().get('message')

    def getLotteryInfoWeb(self, roomid):
        url = f"https://api.live.bilibili.com/xlive/lottery-interface/v1/lottery/getLotteryInfoWeb?roomid={roomid}"
        req = requests.get(url=url)
        return req.json()

    def anchor_check(self, roomid):
        '''
        {
    "code": 0,
    "data": {
        "id": 3212854,
        "room_id": 21604429,
        "status": 1,
        "asset_icon": "https://i0.hdslb.com/bfs/live/627ee2d9e71c682810e7dc4400d5ae2713442c02.png",
        "award_name": "康师傅红烧牛肉大食桶",
        "award_num": 10,
        "award_image": "",
        "danmu": "",
        "time": 0,
        "current_time": 1663678552,
        "join_type": 0,
        "require_type": 1,
        "require_value": 0,
        "require_text": "关注主播",
        "gift_id": 0,
        "gift_name": "",
        "gift_num": 1,
        "gift_price": 0,
        "cur_gift_num": 0,
        "goaway_time": 96,
        "award_users": [
            {
                "uid": 31336763,
                "uname": "风挽雪丶",
                "face": "http://i0.hdslb.com/bfs/baselabs/e85a41bcda4a690bcc22c8c6a358121273b2c8c7.png",
                "level": 9,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 312788816,
                "uname": "乔南溪",
                "face": "http://i2.hdslb.com/bfs/face/a198e79dbc02d8d150c4372472cf8aab563f0eac.jpg",
                "level": 7,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 970408,
                "uname": "UP主的颜粉",
                "face": "http://i0.hdslb.com/bfs/baselabs/54d85de29296104571cbaaafa077b9d80d0add93.png",
                "level": 11,
                "color": 6406234,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 693216575,
                "uname": "反复横条的智齿-1",
                "face": "http://i2.hdslb.com/bfs/face/e281b2bd1b0343aaad209459b0367bbbcdff9189.jpg",
                "level": 14,
                "color": 6406234,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 1242646656,
                "uname": "很久很久很久0",
                "face": "http://i0.hdslb.com/bfs/face/e9b4696f79f30095c1b83ba1330444b8ecbf6ea6.jpg",
                "level": 1,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 15153428,
                "uname": "神奇的友人",
                "face": "http://i2.hdslb.com/bfs/face/376792d592f8af1a61fa2f7592ead237378610f0.jpg",
                "level": 2,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 1368289313,
                "uname": "小园丁之艾玛伍兹",
                "face": "http://i2.hdslb.com/bfs/face/db5cbe1a39e29826fbf09657452333f0fe71ed1a.jpg",
                "level": 0,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 1427362153,
                "uname": "这是我能中的吗",
                "face": "http://i1.hdslb.com/bfs/face/f6b143f6b858af66e8fb10ee61e3ade076be38fd.jpg",
                "level": 12,
                "color": 6406234,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 1496963770,
                "uname": "为了改名中奖不寒碜",
                "face": "http://i1.hdslb.com/bfs/face/9c9b3ad297becc359d4c07f00fbef4003b37193c.jpg",
                "level": 4,
                "color": 9868950,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            },
            {
                "uid": 470506589,
                "uname": "纾婳",
                "face": "http://i2.hdslb.com/bfs/face/03d03053cfa98e04dc9d601f094c8e8a4122cdc4.jpg",
                "level": 11,
                "color": 6406234,
                "bag_id": 0,
                "gift_id": 0,
                "num": 1
            }
        ],
        "show_panel": 1,
        "url": "https://live.bilibili.com/p/html/live-lottery/anchor-join.html?is_live_half_webview=1&hybrid_biz=live-lottery-anchor&hybrid_half_ui=1,5,100p,100p,000000,0,30,0,0,1;2,5,100p,100p,000000,0,30,0,0,1;3,5,100p,100p,000000,0,30,0,0,1;4,5,100p,100p,000000,0,30,0,0,1;5,5,100p,100p,000000,0,30,0,0,1;6,5,100p,100p,000000,0,30,0,0,1;7,5,100p,100p,000000,0,30,0,0,1;8,5,100p,100p,000000,0,30,0,0,1",
        "lot_status": 2,
        "web_url": "https://live.bilibili.com/p/html/live-lottery/anchor-join.html",
        "send_gift_ensure": 0,
        "goods_id": 0,
        "award_type": 0,
        "award_price_text": "",
        "ruid": 406745134
    },
    "message": "ok",
    "msg": "ok"
}
        :param roomid:
        :return:
        '''
        url = 'https://api.live.bilibili.com/xlive/lottery-interface/v1/Anchor/Check?roomid={}'.format(roomid)
        headers = {
            'user-agent': 'Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)'
        }
        req = requests.get(url=url, headers=headers)
        return req.json()
