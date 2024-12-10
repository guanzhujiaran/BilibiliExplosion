import json
import random
import re
import threading
import time
# noinspection PyUnresolvedReferences
import traceback
import Bilibili_methods.all_methods
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import numpy
import requests
import Bilibili_methods.all_methods as m
from fastapi接口.log.base_log import get_rm_following_list_logger as logger
from utl.代理.request_with_proxy import request_with_proxy
mapi = m.methods()


class rmfollow:
    def __init__(self):
        self.fileWriteLock = threading.Lock()
        self.BAPI = Bilibili_methods.all_methods.methods()
        self.n = 0
        self.sleeptime = numpy.linspace(2, 3, 500, endpoint=False)
        self.sparetime = 86400 * 30  # 标记多少天未发动态的up主
        self.request_with_proxy = request_with_proxy()

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def get_following(self, cookie, ua):
        accinfo = mapi.login_check(cookie, ua)
        uid = accinfo['uid']
        url = 'https://api.bilibili.com/x/relation/stat?vmid=' + str(uid) + '&jsonp=jsonp'
        headers = {
            'user-agent': 'Mozilla/5.0'
        }
        try:
            req_dict = self.request_with_proxy.sync_request_with_proxy(method='GET', url=url, headers=headers)
        except Exception as e:
            req_dict = json.dumps({'error': '获取关注人数失败'})
            logger.info(
                '\033[4;31;40m获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n\033[0m')
            logger.info(e)
            exit(1)
        try:
            following = req_dict.get('data').get('following')
            logger.info(following)
            page = int(int(following) / 20) + 1
            logger.info('共有{page}页'.format(page=page))
        except Exception as e:
            traceback.print_exc()
            logger.info(req_dict)
            logger.info(
                '\033[4;31;40m获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n获取关注人数失败\n'
                '获取关注人数失败\n\033[0m')
            page = 0
            following = 0
            logger.info(e)
            exit(0)
        time.sleep(random.choice(self.sleeptime))
        try:
            followingfile = open('所有关注者.csv', 'w', encoding='utf-8')
            for x in range(1, page + 1):
                logger.info('正在获取第{x}页的关注者'.format(x=x))
                headers = {
                    "Content-Type": "application/json",
                    'cookie': cookie,
                    'user-agent': ua,
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate',
                    'accept-language': 'zh-CN,zh;q=0.9',
                    'referer': f'https://space.bilibili.com/{uid}/fans/follow?tagid=-1',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': "Windows",
                    'sec-fetch-dest': 'script',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-site': 'same-site',
                }
                url = 'https://api.bilibili.com/x/relation/tag?mid={}&tagid=0&pn={}&ps=20&jsonp=jsonp'.format(uid, x)
                data = {
                    'vmid': uid,
                    'pn': x,
                    'ps': '20',
                    'order': 'desc',
                    'order_type': 'attention',
                    'jsonp': 'jsonp'
                }
                req = requests.request(method='GET', url=url, headers=headers, data=data)
                req_dict = json.loads(req.text)
                dylist = req_dict.get('data')
                for DICT in dylist:
                    mid = DICT.get('mid')
                    uname = DICT.get('uname')
                    officialtype = DICT.get('official_verify').get('type')
                    if officialtype == 1:
                        official = '蓝V'
                    elif officialtype == 0:
                        official = '黄V'
                    elif officialtype == -1:
                        official = '没有V'
                    else:
                        official = officialtype
                    url1 = 'https://api.bilibili.com/x/relation/stat?vmid={mid}&jsonp=jsonp'.format(
                        mid=mid)
                    headers = {
                        "Content-Type": "application/json;charset=utf-8",
                        # 'cookie': cookie,
                        # 'user-agent': random.choice(self.User_Agent_List),
                        'user-agent': 'Mozilla/5.0',
                        'referer': 'https://space.bilibili.com/{uid}/fans/follow'.format(uid=uid)
                    }
                    data = {
                        'vmid': mid,
                        'jsonp': 'jsonp',
                        'callback': '__jp{jp}'.format(jp=dylist.index(DICT) + 1)
                    }
                    statreq = self.request_with_proxy.sync_request_with_proxy(method='GET', url=url1, headers=headers,
                                                                         data=data)
                    time.sleep(0.5)
                    stat_dict = statreq
                    upfans = stat_dict.get('data').get('follower')
                    logger.info('{mid}\t{uname}\t{official}\t{fans}'.format(mid=mid, uname=uname, official=official,
                                                                            fans=upfans))
                    followingfile.writelines('https://space.bilibili.com/' +
                                             str(mid) + '\t' + str(uname) + '\t' + str(official) + '\t' + str(
                        upfans) + '\n')
                logger.info('此页共{lenoflist}个关注'.format(lenoflist=len(dylist)))
                time.sleep(3 * random.choice(self.sleeptime))
            logger.info('获取完毕，共{following}个关注'.format(following=following))
            followingfile.close()
        except Exception as e:
            logger.info(e)
            logger.info(traceback.print_exc())
            exit(3)

    def judge_lottery_up(self, mids, nonlottery_upfile, get_dy_fail, relationchange):
        lottery_up = False
        offset = 0
        dynamic_timestamp = None
        content_list = []
        record_sign = False
        while 1:
            logger.info('offset:{}'.format(offset))
            mid = mids.split('\t')[0]
            if 'http' in mid:
                mid = mid.split('/')[-1]
            data = {
                'visitor_uid': 0,
                'host_uid': mid,
                'offset_dynamic_id': str(offset),
                'need_top': 0,
                'platform': 'web'
            }
            headers = {'user-agent': 'Mozilla/5.0'}
            url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=0&host_uid={mid}' \
                  '&offset_dynamic_id={offset}&need_top=0'.format(mid=mid, offset=offset)
            try:
                req_dict = self.request_with_proxy.sync_request_with_proxy(method='GET', url=url, headers=headers,
                                                                      data=data)
            except:
                req_dict = {'请求出错': 404, 'data': {}}
            try:
                cards = req_dict.get('data').get('cards')
                offset = req_dict.get('data').get('next_offset')
                has_more = req_dict.get('data').get('has_more')
            except:
                logger.info(req_dict)
                logger.info(mapi.timeshift(time.time()))
                logger.info('风控休息30分钟')
                time.sleep(30 * 60)
                continue
                # req = requests.request('GET', url=url, headers=headers, data=data)
                # req_dict = json.loads(req.text)
                # cards = req_dict.get('data').get('cards')
                # offset = req_dict.get('data').get('next_offset')
                # has_more = req_dict.get('data').get('has_more')
            if cards is None:
                logger.info(req_dict)
            try:
                for card in cards:
                    try:
                        self.n += 1
                        logger.info('第' + str(self.n) + '次获取动态')
                        dynamic_id = str(eval(card.get('desc').get('dynamic_id_str')))
                        dynamic_url = 'https://t.bilibili.com/' + dynamic_id + '?tab=2'
                        dynamic_rid = str(card.get('desc').get('rid'))
                        dynamic_repostcount = card.get('desc').get('repost')
                        dynamic_commentcount = card.get('desc').get('comment')
                        dynamic_is_liked = card.get('desc').get('is_liked')
                        dynamic_type = str(card.get('desc').get('type'))
                        dynamic_timestamp = card.get('desc').get('timestamp')
                        dynamic_uname = card.get('desc').get('user_profile').get('info').get('uname')
                        dynamic_uid = card.get('desc').get('user_profile').get('info').get('uid')
                    except Exception as e:
                        logger.info('获取个人信息失败：')
                        logger.info(card)
                        logger.info(e)
                        with self.fileWriteLock:
                            get_dy_fail.writelines(mids)
                        # time.sleep(eval(input('输入等待时间')))
                        break
                    logger.info('up主：{name}'.format(name=dynamic_uname))
                    logger.info('空间主页：https://space.bilibili.com/{uid}'.format(uid=dynamic_uid))
                    logger.info('动态url：' + dynamic_url)
                    logger.info('发布时间：' + self.timeshift(dynamic_timestamp))
                    if record_sign:
                        pass
                    elif int(time.time()) - dynamic_timestamp >= self.sparetime:
                        with self.fileWriteLock:
                            relationchange.writelines('{}'.format(mids))
                    record_sign = True
                    try:
                        card = json.loads(card.get('card'))
                        if dynamic_type == '1':
                            dynamic_content = card.get('item').get('content')
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('转发动态或转发视频：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '2':
                            dynamic_content = card.get('item').get('description')
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('带图原创动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '4':
                            dynamic_content = card.get('item').get('content')
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('不带图的原创动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '8':
                            dynamic_content1 = card.get('desc')
                            dynamic_content2 = card.get('dynamic')
                            if len(dynamic_rid) == len(dynamic_id):
                                oid = dynamic_id
                            else:
                                oid = dynamic_rid
                            time.sleep(random.choice([1, 2]))
                            dynamic_content3 = self.BAPI.get_topcomment_proxy(str(dynamic_id), str(oid), str(0),
                                                                              str(dynamic_type),
                                                                              dynamic_uid)
                            time.sleep(random.choice([1, 2]))
                            if dynamic_content3 != 'null':
                                dynamic_content = dynamic_content1 + dynamic_content2 + dynamic_content3
                            else:
                                dynamic_content = dynamic_content1 + dynamic_content2
                            dynamic_commentcount = card.get('stat').get('reply')
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('原创视频：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '64':
                            dynamic_content = card.get('summary')
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('专栏动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '4308':
                            dynamic_content = '直播间标题，无视'
                            logger.info('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info(card.get('live_play_info').get('title'))
                            logger.info('✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('直播动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        elif dynamic_type == '2048':
                            dynamic_content = card.get('vest').get('content')
                            logger.info(dynamic_content)
                            logger.info(
                                '动态内容：\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n' + dynamic_content + '\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱')
                            logger.info('带简报的动态：https://t.bilibili.com/' + str(dynamic_id) + '?tab=2')
                        else:
                            dynamic_content = 'Error'
                            logger.info('\n\n')
                        content_list.append(dynamic_content)
                    except Exception as e:
                        logger.info(e)
                        logger.info(card)
                        with self.fileWriteLock:
                            get_dy_fail.writelines(mids)
                        # time.sleep(eval(input('输入等待时间')))
                        continue
                    for i in content_list:
                        if self.BAPI.choujiangxinxipanduan(i) is None:
                            lottery_up = True
                            content_list.clear()
                            break
                    if int(time.time()) - dynamic_timestamp >= self.sparetime:  # 超过时间的直接跳过
                        break
            except Exception as e:
                if has_more == 0:
                    break
                logger.info(e)
                logger.info(cards)
                logger.info(req_dict)
                with self.fileWriteLock:
                    get_dy_fail.writelines(mids)
                # time.sleep(eval(input('输入等待时间')))
                logger.info('出了点问题，休息个30分钟')
                time.sleep(30 * 60)
                offset = req_dict.get('data').get('next_offset')
                if not offset:
                    break
                continue
            for i in content_list:
                if self.BAPI.choujiangxinxipanduan(i) is None:
                    lottery_up = True
                    content_list.clear()
                    logger.info('是抽奖up，下一个')
                    break
            # time.sleep(3 * random.choice(self.sleeptime)) # 因为使用代理获取的动态，所以不需要等待
            content_list.clear()
            if dynamic_timestamp is not None:
                if int(time.time()) - dynamic_timestamp >= self.sparetime:
                    break
            if has_more == 0:
                break
        if lottery_up is False:
            logger.info('不怎么抽奖的up')
            with self.fileWriteLock:
                nonlottery_upfile.writelines(mids)

    def get_dynamic_from_following(self):
        followingfile = open('所有关注者.csv', 'r', encoding='utf-8')
        relationchange = open('取关对象.csv', 'w', encoding='utf-8')
        get_dy_fail = open('获取动态失败.csv', 'w', encoding='utf-8')
        nonlottery_upfile = open('不怎么抽奖的up.csv', 'w', encoding='utf-8')
        get_time = 1
        f_len = len(followingfile.readlines())
        followingfile.close()
        followingfile = open('所有关注者.csv', 'r', encoding='utf-8')
        thread_list = []
        for mids in followingfile:
            thread = threading.Thread(target=self.judge_lottery_up,
                                      args=(mids, nonlottery_upfile, get_dy_fail, relationchange))
            thread.start()
            thread_list.append(thread)
        for t in thread_list:
            t.join()
        followingfile.close()
        relationchange.close()
        get_dy_fail.close()
        nonlottery_upfile.close()

    def start(self, accountname):
        cookie1 = gl.get_value('cookie1')  # 星瞳
        fullcookie1 = gl.get_value('fullcookie1')
        ua1 = gl.get_value('ua1')
        fingerprint1 = gl.get_value('fingerprint1')
        csrf1 = gl.get_value('csrf1')
        cookie2 = gl.get_value('cookie2')  # 保加利亚
        fullcookie2 = gl.get_value('fullcookie2')
        ua2 = gl.get_value('ua2')
        fingerprint2 = gl.get_value('fingerprint2')
        csrf2 = gl.get_value('csrf2')
        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        fullcookie3 = gl.get_value('fullcookie3')
        ua3 = gl.get_value('ua3')
        fingerprint3 = gl.get_value('fingerprint3')
        csrf3 = gl.get_value('csrf3')
        cookie4 = gl.get_value('cookie4')  # 墨色
        fullcookie4 = gl.get_value('fullcookie4')
        ua4 = gl.get_value('ua4')
        fingerprint4 = gl.get_value('fingerprint4')
        csrf4 = gl.get_value('csrf4')
        if accountname == 1:
            self.get_following(cookie1, ua1)
            self.get_dynamic_from_following()

        elif accountname == 2:
            self.get_following(cookie2, ua2)
            self.get_dynamic_from_following()

        elif accountname == 3:
            self.get_following(cookie3, ua3)
            self.get_dynamic_from_following()

        elif accountname == 4:
            self.get_following(cookie4, ua4)
            self.get_dynamic_from_following()




if __name__ == '__main__':
    myrmfollowing = rmfollow()
    myrmfollowing.start(2)
    # 1：星瞳
    # 2：保加利亚
    # 3：斯卡蒂
    # 4：墨色
