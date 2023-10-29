# -*- coding:utf- 8 -*-
import json
import random
import re
import sys
import threading
import time
import traceback
import urllib.parse
from multiprocessing import Pool
# noinspection PyUnresolvedReferences
import numpy
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import Bilibili_methods.all_methods
import b站cookie.b站cookie_
import b站cookie.globalvar as gl

BAPI = Bilibili_methods.all_methods.methods()
cookie1 = gl.get_value('cookie1').encode('utf-8')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1').encode('utf-8')
ua1 = gl.get_value('ua1').encode('utf-8')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
username1 = gl.get_value('uname1')
watch_cookie1 = gl.get_value('watch_cookie1').encode('utf-8')

cookie2 = gl.get_value('cookie2').encode('utf-8')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2').encode('utf-8')
ua2 = gl.get_value('ua2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
username2 = gl.get_value('uname2')
watch_cookie2 = gl.get_value('watch_cookie2').encode('utf-8')

cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3').encode('utf-8')
ua3 = gl.get_value('ua3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
username3 = gl.get_value('uname3')
watch_cookie3 = gl.get_value('watch_cookie3').encode('utf-8')

cookie4 = gl.get_value('cookie4')  # 墨色
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4').encode('utf-8')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
username4 = gl.get_value('uname4')
watch_cookie4 = gl.get_value('watch_cookie4').encode('utf-8')


def random_choice_dict(d):
    k_list = list()
    for k in d.keys():
        k_list.append(k)
    rand_k = random.choice(k_list)
    rand_v = d[rand_k]
    return {rand_k: rand_v}


# 3000392
class ip_score:
    def __init__(self):
        self.sleeptime = numpy.linspace(1, 2, 500, endpoint=False)
        self.uid = None
        self.s = requests.session()

    def warn(self, msg):
        print("\033[1;33m\n{}\n\033[0m".format(msg))

    def _task_detail(self, ipId, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/ip/task/list/get?_t={}&ipId={}&mVersion=129'.format(
            int(time.time() * 1000),
            ipId)
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'origin': 'https://mall.bilibili.com',
            'refer': 'https://mall.bilibili.com/xw/ip-fans/home/index.html?noTitleBar=1&from=cms_1047_M7BGEDnRiAvP_&ipId={}&msource=mall_5959_banner&outsideMall=no'.format(
                ipId),
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.get(url=url, headers=headers)
        if req.json().get('code') == 0:
            return req.json()
        else:
            self.warn(req.text)
            self.warn('任务获取失败')
            exit('任务获取失败')

    def task_dispatch(self, ipTaskId, ipid, jumpLiknType, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/ip/task/dispatch'
        data = {"ipTaskId": ipTaskId}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/json',
            'refer': 'https://mall.bilibili.com/detail.html?from=ip_{}&jumpLinkType={}&loadingShow=1&noTitleBar=1&ipTaskId={}&msource=bilibiliapp&outsideMall=no'.format(
                ipid, jumpLiknType, ipTaskId),
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        if req.json().get('code'):
            self.warn('任务完成失败')
            self.warn(ipTaskId)
            self.warn(req.text)
        else:
            print('任务完成')

    def wish_set(self, itemsId, ipId, Type, salesTag, shopname, cookie, ua):
        """
        添加收藏
        :param itemsId:
        :param ipId:
        :param Type: 1是收藏，2是取消收藏
        :param cookie:
        :param ua:
        :return:
        """
        url = 'https://mall.bilibili.com/mall-c/items/wish/set'
        if Type == 1:
            url = 'https://mall.bilibili.com/mall-c/items/wish/set'
        else:
            url = 'https://mall.bilibili.com/mall-c/items/wish/set/na'
        data = {"itemsId": str(itemsId), "wishType": Type, "shopId": 2233, "version": 1}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/json',
            'refer': 'https://mall.bilibili.com/detail.html?from=ip_{}&jumpLinkType=0&loadingShow=1&noTitleBar=1&msource=bilibiliapp&outsideMall=no'.format(
                ipId),
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, headers=headers, data=json.dumps(data))
        if req.json().get('code') == 0:
            if Type == 1:
                print(
                    '添加收藏成功 商品链接：https://mall.bilibili.com/detail.html?itemsId={}\n商品类型：{}\n商品名称：{}'.format(
                        itemsId,
                        salesTag,
                        shopname))
            else:
                print(
                    '取消收藏成功 商品链接：https://mall.bilibili.com/detail.html?itemsId={}\n商品类型：{}\n商品名称：{}'.format(
                        itemsId,
                        salesTag,
                        shopname))
        else:
            print(req.text)
            if Type == 1:
                self.warn(
                    '添加收藏失败 商品链接：https://mall.bilibili.com/detail.html?itemsId={}\n商品类型：{}\n商品名称：{}'.format(
                        itemsId,
                        salesTag,
                        shopname))
                self.warn(cookie)
            else:
                self.warn(
                    '取消收藏失败 商品链接：https://mall.bilibili.com/detail.html?itemsId={}\n商品类型：{}\n商品名称：{}'.format(
                        itemsId,
                        salesTag,
                        shopname))
                self.warn(cookie)
        return req.json()

    # wish_contentDetailId=948007;886003
    def wish_add(self, ipId, url, cookie, ua):
        """
            订阅商品
        :param url:
        :param cookie:
        :param ua:
        """
        # url = 'https://mall.bilibili.com/mall-c-community/content/wish/add?contentDetailId={}'.format(DetailId)
        try:
            itemsId = re.findall('contentDetailId=(.\d+)', url)[0]
        except:
            itemsId = None
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'accept-encoding': 'gzip, deflate',
            'refer': 'https://mall.bilibili.com/neul/index.html?page=firstlook_detail&noTitleBar=1&from=ip_faxian&msource=bilibiliapp&outsideMall=no',
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, headers=headers)
        if req.json().get('code') == 0:
            print('订阅商品成功')
        else:
            self.warn('订阅商品失败')
            self.warn(cookie)
            self.warn(req.text)
        if self.user_score_rights(ipId, cookie, ua):
            try:
                with open('./会员购ip任务log/订阅成功.csv', 'a+', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true\n'.format(
                            itemsId, ipId))
            except:
                with open('./会员购ip任务log/订阅成功.csv', 'w', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true\n'.format(
                            itemsId, ipId))
        else:
            try:
                with open('./会员购ip任务log/订阅失败.csv', 'a+', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true\n'.format(
                            itemsId, ipId))
            except:
                with open('./会员购ip任务log/订阅失败.csv', 'w', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true,\n'.format(
                            itemsId, ipId))

    def wish_del(self, url, cookie, ua):
        """
            取消订阅商品
        :param cookie:
        :param ua:
        """
        # url = 'https://mall.bilibili.com/mall-c-community/content/wish/del?contentDetailId={}'.format(DetailId)
        url = url.replace('add', 'del')
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'accept-encoding': 'gzip, deflate',
            'refer': 'https://mall.bilibili.com/neul/index.html?page=firstlook_detail&noTitleBar=1&from=ip_faxian&msource=bilibiliapp&outsideMall=no',
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, headers=headers)
        if req.json().get('code') == 0:
            print('取消订阅商品成功')
        else:
            self.warn('取消订阅商品失败')
            self.warn(cookie)
            self.warn(req.text)

    def content_detail(self, url, cookie, ua):
        """
            查询订阅状态
        :param url:
        :param cookie:
        :param ua:
        """
        url = url.replace('from=card_contentfeeds&', '')
        url = url.replace('wish/add', 'detail')
        url += '&v={}'.format(int(time.time() * 1000))
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'accept-encoding': 'gzip, deflate',
            'refer': 'https://mall.bilibili.com/neul/index.html?page=firstlook_detail&noTitleBar=1&from=ip_faxian&msource=bilibiliapp&outsideMall=no',
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.get(url=url, headers=headers)
        print('订阅状态：{}'.format(req.json().get('data').get('subscribed')))

    def _discovery_list(self, ipId):
        '''
        获取订阅商品url
        :param ipId:
        :return:
        '''
        url_list = list()
        for p_num in range(1, 3):
            url = 'https://mall.bilibili.com/mall-c-search/ip/discovery/list?mVersion=129'
            data = {"ipId": "0_{}".format(ipId), "pageNum": p_num, "pageSize": 46}
            headers = {
                'app-key': 'android64',
                'x-requested-with': 'tv.danmaku.bili',
                'content-type': 'application/json; charset=utf-8'
            }
            req = self.s.post(data=json.dumps(data), url=url, headers=headers)
            try:
                l = req.json().get('data').get('list')
                for i in l:
                    if i.get('type') == 'peak':
                        if i.get('indexButtons') == None:
                            continue
                        url_list.append(urllib.parse.unquote(i.get('indexButtons')[0].get('url')).replace('&mid=0', ''))
                time.sleep(random.choice(self.sleeptime))
            except:
                print(req.text)
                traceback.print_exc()
        return url_list

    def wish_add_task(self, ipId, cookie, ua):
        try:
            u_l = self._discovery_list(ipId)
            print('订阅商品列表：')
            for i in u_l:
                print(i)
            u = random.choice(u_l)
            self.wish_add(ipId, u, cookie, ua)
            # time.sleep(1)
            # self.content_detail(u, cookie, ua)
            time.sleep(random.choice(self.sleeptime))
            self.wish_del(u, cookie, ua)
            time.sleep(1)
            self.content_detail(u, cookie, ua)
            time.sleep(random.choice(self.sleeptime))
        except:
            print('订阅任务失败')
            traceback.print_exc()

    def shop_detail(self, ipId, pageIndex):
        """
        收藏商品任务
        获取商店ip home的信息
        :param pageIndex:
        :param ipId:
        :return:
        """
        url = 'https://mall.bilibili.com/mall-c-search/ip/home/feed'
        data = {"pageIndex": int(pageIndex),
                "scene": "ip",
                "sortOrder": "",
                "sortType": "totalrank",
                "termQueries": [
                    {"field": "ip",
                     "values": ["0_{}".format(ipId)]
                     }
                ]
                }
        headers = {
            'user-agent': 'Mozilla/5.0 BiliDroid/6.68.0 (bbcallen@gmail.com) mallVersion/6680400 os/android model/oppo '
                          'R11s Plus mobi_app/android build/6680400 channel/html5_app_bili innerVer/6680410 '
                          'osVer/6.0.1 network/2',
            'app-key': 'android64',
            'content-type': 'application/json; charset=utf-8',
            'env': 'prod',
            'accept-encoding': 'gzip',

        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        return req.json()

    def wish_set_task(self, ipId, cookie, ua):
        """
            会员购ip任务之收藏IP商品
        :param ipId:
        :param cookie:
        :param ua:
        """
        itemsId_list = list()
        for i in range(1, 3):
            home_info = self.shop_detail(ipId, i)
            if home_info.get('code') == 0:
                ipFeedVO = home_info.get('data').get('data')
                if ipFeedVO is None:
                    self.warn(home_info)
                    self.warn(ipId)
                else:
                    for i in ipFeedVO:
                        itemsId_list.append(i)
            time.sleep(3 * random.choice(self.sleeptime))
        item = random.choice(itemsId_list)
        itemsId = item.get('itemsId')
        try:
            itemsTags = item.get('tags').get('saleTypeTagNames')
        except:
            print(item)
            print(itemsId_list)
            traceback.print_exc()
            exit(114514)
        shopname = item.get('name')
        if itemsTags is None:
            itemsType = item.get('itemsType')
            if itemsType == 0:
                itemsTags = '现货'
            elif itemsType == 1:
                itemsTags = '预售'
            elif itemsType == 3:
                itemsTags = '不含tag魔力赏'
            else:
                print(item)
        print('商品列表：')
        for i in itemsId_list:
            print(itemsTags, i.get('name'), urllib.parse.unquote(i.get('jumpUrl')))
        self.wish_set(itemsId, ipId, 1, itemsTags, shopname, cookie, ua)
        time.sleep(3 * random.choice(self.sleeptime))
        self.wish_set(itemsId, ipId, 2, itemsTags, shopname, cookie, ua)
        time.sleep(3 * random.choice(self.sleeptime))
        if self.user_score_rights(ipId, cookie, ua):
            try:
                with open('./会员购ip任务log/收藏成功.csv', 'a+', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true,{},{}\n'.format(
                            itemsId, ipId, itemsTags, shopname))
            except:
                with open('./会员购ip任务log/收藏成功.csv', 'w', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true,{},{}\n'.format(
                            itemsId, ipId, itemsTags, shopname))
        else:
            try:
                with open('./会员购ip任务log/收藏失败.csv', 'a+', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true,{},{}\n'.format(
                            itemsId, ipId, itemsTags, shopname))
            except:
                with open('./会员购ip任务log/收藏失败.csv', 'w', encoding='utf-8') as f:
                    f.writelines(
                        'https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true,{},{}\n'.format(
                            itemsId, ipId, itemsTags, shopname))

    def daily_sign(self, ipId, cookie, ua):
        url = 'https://show.bilibili.com/api/activity/ip/sign/do'
        data = {"ipId": "0_{}".format(ipId)}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/json; charset=utf-8',
        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        if req.json().get('code') == 0:
            print('签到成功')
            print(req.json().get('data').get('dayContent'))
        else:
            self.warn('签到失败')
            self.warn(cookie)
            self.warn(req.text)
        return req.json()

    def user_score_rights(self, ipId, cookie, ua):
        _t = int(time.time() * 1000)
        url = 'https://show.bilibili.com/api/activity/ip/v2/user-score-rights?_t={}&ipId={}'.format(
            _t, ipId)
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/json',
            'refer': "https://mall.bilibili.com/xw/ip-fans/home/index.html?noTitleBar=1&from=jgw&ipId={}&msource=bilibiliapp&outsideMall=no".format(
                ipId),
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        data = {
            '_t': _t,
            'ipId': ipId

        }
        req = self.s.get(url=url, headers=headers, data=json.dumps(data))
        scoreUpInfo = req.json().get('data').get('scoreUpInfo')
        if scoreUpInfo:
            singleText = req.json().get('data').get('scoreUpInfo').get('singleText')
            print('获取积分：{}'.format(singleText))
            return singleText
        else:
            print('无新获取积分')
            return False

    def do_task(self, ipId, cookie, ua, uname):
        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = self.s.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                self.uid = res['data']['mid']
                print(f'登录成功,当前账号用户名为{name}\tUID：{self.uid}')
                return 1
            else:
                self.warn('登陆失败,请重新登录')
                sys.exit()

        login_check(cookie, ua)
        self.daily_sign(ipId, cookie, ua)
        time.sleep(random.choice(self.sleeptime))
        for _ in range(3):
            task_req_json = self._task_detail(ipId, cookie, ua)
            tasklist = task_req_json.get('data').get('tasks')
            for i in tasklist:
                ipTaskId = i.get('ipTaskId')
                taskType = i.get('taskType')
                taskStatus = i.get('taskStatus')
                jumpType = i.get('jumpType')
                taskName = i.get('taskName')
                print(BAPI.timeshift(time.time()))
                print('当前任务：{}'.format(taskName))
                print('任务状态：{}'.format(taskStatus))
                if taskStatus != 'done':
                    time.sleep(5)
                    if taskType == 2 or taskType == 3:
                        if ipTaskId is not None and jumpType is not None:
                            self.task_dispatch(ipTaskId, ipId, jumpType, cookie, ua)
                        else:
                            self.warn([ipTaskId, ipId, jumpType])
                            self.warn('传入参数错误')
                    self.user_score_rights(ipId, cookie, ua)
                    if taskType == 4:
                        time.sleep(5)
                        self.wish_set_task(ipId, cookie, ua)
                    self.user_score_rights(ipId, cookie, ua)
                    if taskType == 5:
                        time.sleep(5)
                        self.wish_add_task(ipId, cookie, ua)
                    if taskType == 6:
                        time.sleep(5)
                        self.comment_task(ipId, cookie, ua, self.uid, uname)
                time.sleep(random.choice(self.sleeptime))
        self.user_score_rights(ipId, cookie, ua)

    def content_add(self, itemsId, shopname, content, cookie, ua, uid, uname):
        '''
        写评论
        :return:
        '''
        url = 'https://mall.bilibili.com/mall-c/ugc/content/add'
        data = {"comments": [{"content": content, "imgs": "",
                              "score": 0,
                              "shopId": 0,
                              "subjectId": itemsId,
                              "subjectName": shopname,
                              "subjectType": 1}],
                "mid": int(uid), "uname": uname, "platform": 2, "version": "1.0", "device": "h5", "orderId": 0}
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'content-type': 'application/json',
            'refer': "https://mall.bilibili.com/neul/index.html?goFrom=na&shopId=2233&noTitleBar=1&page=mall_commentlist&recId=&outsideMall=no&itemsId={}".format(
                itemsId),
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        if req.json().get('code') == 0:
            print('评论成功')
            return req.json().get('data').get('ugcIds')[0]
        else:
            self.warn('评论失败')
            self.warn(cookie)
            self.warn(req.text)
            return None

    def content_delete(self, itemsId, ugcId, cookie, ua, uid):
        url = 'https://mall.bilibili.com/mall-c/ugc/content/delete'
        data = {
            "mid": int(uid),
            "parent": 0,
            "platform": 2,
            "root": int(ugcId),
            "subjectId": int(itemsId),
            "subjectType": 1,
            "ugcId": int(ugcId),
            "version": "1.0"
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'TE': 'trailers',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://mall.bilibili.com',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://mall.bilibili.com/neul/index.html?goFrom=na&noTitleBar=1&page=mall_commentlist&type=box&outsideMall=no&itemsId={}'.format(
                itemsId),
            'Connection': 'keep-alive',
        }
        req = self.s.post(url=url, headers=headers, data=json.dumps(data))
        if req.json().get('code') == 0:
            print('删除评论成功')
        else:
            self.warn(
                '删除评论失败\n链接 https://mall.bilibili.com/neul/index.html?goFrom=na&noTitleBar=1&page=mall_commentlist&type=box&outsideMall=no&itemsId={} \n楼层数：{}'.format(
                    itemsId, ugcId))
            self.warn(cookie)

    def web_interface_nav(self, cookie, ua):
        t = int(time.time()) * 1000
        url = 'https://api.bilibili.com/x/web-interface/nav?cross_domain=true&_={}'.format(t)
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'TE': 'trailers',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://mall.bilibili.com',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Referer': 'https://mall.bilibili.com/',
            'Connection': 'keep-alive'
        }

        req = self.s.get(url=url, headers=headers)
        try:
            if req.json().get('code') == 0:
                print('nav获取成功')
            else:
                self.warn('nav获取失败')
                self.warn(req.text)
        except:
            self.warn('nav获取失败')
            self.warn(cookie)
            self.warn(req.text)

    def content_operate(self, itemsId, ugcId, cookie, ua, uid):
        """
            opType=1是点赞2是取消点赞
        :param itemsId:
        :param ugcId:
        :param cookie:
        :param ua:
        :param uid:
        :return:
        """
        url = 'https://mall.bilibili.com/mall-c/ugc/content/operate'
        data = {
            "device": "h5",
            "mid": int(uid),
            "opType": 1,
            "platform": 2,
            "subjectId": itemsId,
            "subjectType": 1,
            "ugcId": ugcId,
            "version": "1.0"
        }
        headers = {
            'cookie': cookie,
            'user-agent': ua,
            'refer': 'https://mall.bilibili.com/neul/index.html?goFrom=na&noTitleBar=1&page=mall_commentlist&type=box&outsideMall=no&itemsId={}'.format(
                itemsId),
            'TE': 'trailers',
            'Origin': 'https://mall.bilibili.com',
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://mall.bilibili.com/neul/index.html?goFrom=na&noTitleBar=1&page=mall_commentlist&type=box&outsideMall=no&itemsId={}'.format(
                itemsId),
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
        }
        req = self.s.request('POST', url=url, data=json.dumps(data), headers=headers)
        if req.json().get('code') == 0:
            print('商品评论点赞成功')
        else:
            self.warn('商品评论点赞失败')
            self.warn(cookie)
            self.warn(req.text)
        return req.json()

    def content_all_list(self, itemsId):
        """
            通过itemsId获取商品无图评论
        :param itemsId:
        :return:
        """
        c_list = list()
        url = 'https://mall.bilibili.com/mall-dayu/ugc/items/comments/page'
        data = {
            "ugcId": 0,
            "device": "h5",
            "mid": -1,
            "pageNum": 1,
            "pageSize": 50,
            "ignoreEssenceIds": [],
            "ignoreHotIds": [],
            "platform": 2,
            "subPageSize": 2,
            "subjectId": itemsId,
            "subjectType": 1,
            "version": "1.1",
            "tagId": 0,
            "prePageLastFloorNo": 'null',
            "scene": "item_comment_page"
        }
        headers = {
            'refer': 'https://mall.bilibili.com/neul/index.html?goFrom=na&noTitleBar=1&page=mall_commentlist&type=box&outsideMall=no&itemsId={}'.format(
                itemsId),
            'content-type': 'application/json',
            'origin': 'https://mall.bilibili.com',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        commonList = req.json().get('data').get('commonList')
        for c in commonList:
            if c.get('imgs'):
                continue
            c_list.append(c.get('content'))
        return c_list

    def ip_home_feed(self, ipId):
        """
            返回商品名称和itemsId
            {itemsId:商品名}
        :param ipId:
        """
        s_d = dict()
        url = 'https://mall.bilibili.com/mall-c-search/ip/home/feed'
        data = {
            # "itemIds": "10082880",
            "pageIndex": 1,
            "scene": "ip",
            "sortOrder": "",
            "sortType": "sale",
            "termQueries": [
                {
                    "field": "ip",
                    "values": [
                        "0_{}".format(ipId)
                    ]
                }
            ]
        }
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'app-key': 'android64',
            'x-requested-with': 'tv.danmaku.bili',
        }
        req = self.s.post(url=url, data=json.dumps(data), headers=headers)
        shop_list = req.json().get('data').get('data')
        for i in shop_list:
            name = i.get('name')
            itemsId = i.get('itemsId')
            s_d.update({itemsId: name})
        return s_d

    def comment_task(self, ipId, cookie, ua, uid, uname):
        """
            评论任务和点赞任务
        :param ipId:
        :param cookie:
        :param ua:
        :param uid:
        :param uname:
        """
        ip_shop_dict = self.ip_home_feed(ipId)
        time.sleep(random.choice(self.sleeptime))
        rand_shop_dict = random_choice_dict(ip_shop_dict)
        for itemsId, shopname in rand_shop_dict.items():
            content_list = self.content_all_list(itemsId)
            if len(content_list) > 10:
                mycontent = random.choice(content_list)
            else:
                mycontent = random.choice(['日常打卡', '一起来打卡', '我真的好喜欢', '我真的，真的太喜欢这个了'])
            time.sleep(random.choice(self.sleeptime))
            print('商品名称：{}'.format(shopname))
            print(
                '商品链接：https://mall.bilibili.com/detail.html?from=card_item&jumpLinkType=0&loadingShow=1&noTitleBar=1#goFrom=na&itemsId={}&noReffer=true'.format(
                    itemsId))
            print('回复内容：{}'.format(mycontent))
            ucgId = self.content_add(itemsId, shopname, mycontent, cookie, ua, uid, uname)
            time.sleep(random.choice(self.sleeptime))
            if ucgId:
                self.web_interface_nav(cookie, ua)
                self.content_operate(itemsId, ucgId, cookie, ua, uid)
                time.sleep(random.choice(self.sleeptime))
                self.content_delete(itemsId, ucgId, cookie, ua, uid)
                time.sleep(random.choice(self.sleeptime))
            else:
                self.warn('ucgId获取失败')
                self.warn(cookie)


def s():
    ipId_list = [3000392, 3100967, 3000235, 3101500, 3100487]

    a = ip_score()
    for ipid in ipId_list:
        print(
            '\n\n\n\n\n\t\t\t\t\t\t\t\t当前ip https://mall.bilibili.com/ip.html?goFrom=na&noTitleBar=1&from=category&ip=0_{}\n\n\n\n'.format(
                ipid))
        t1 = threading.Thread(target=a.do_task, args=(ipid, cookie1, ua1, username1))
        t2 = threading.Thread(target=a.do_task, args=(ipid, cookie2, ua2, username2))
        t3 = threading.Thread(target=a.do_task, args=(ipid, cookie3, ua3, username3))
        t4 = threading.Thread(target=a.do_task, args=(ipid, cookie4, ua4, username4))
        t1.start()
        time.sleep(5)
        t2.start()
        time.sleep(5)
        t3.start()
        time.sleep(5)
        t4.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()


if __name__ == '__main__':
    # s()
    schedulers = BlockingScheduler()
    schedulers.add_job(s, CronTrigger.from_crontab('0 0 * * *'), misfire_grace_time=3600)
    schedulers.start()
