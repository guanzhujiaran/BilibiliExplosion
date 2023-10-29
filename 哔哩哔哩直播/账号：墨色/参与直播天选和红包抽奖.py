import asyncio
import json
import random
import re
import sys
import time
# noinspection PyUnresolvedReferences
import traceback
import tracemalloc
import copy
import threading as thd
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import numpy
import Bilibili_methods.all_methods

mymethod = Bilibili_methods.all_methods.methods()
import bili_live.bili_live_api as api

myapi = api.bili_live_api()


class Auto_lottery:
    def __init__(self):
        self.uid = gl.get_value('uid4')
        self.cookie = gl.get_value('cookie4')
        self.ua = gl.get_value('ua4')
        self.csrf = gl.get_value('csrf4')
        self.shortsleeptime = numpy.linspace(1, 3, 500, endpoint=True)
        self.Anchor_ignore_keyword = ["大蒜", "点播", "表情", "小游戏", "cos", "看号", "加速器", "优惠", "舰", "抵扣", "返券", "冬日热饮", "一起玩",
                                      "星际战甲", "上车", "搭配", "上船", "保温", "写真", "自画像", "自拍", "照", "总督", "提督", "一毛", "禁言",
                                      "代金", "通行证", "第五人格", "抵用"]
        self.money_min = 10
        self.canjiajiange = 10
        self.redpocket_queue = list()
        self.anchor_queue = list()
        self.jiangeshijian = 30  # 从服务器获取数据的间隔时间
        self.following_list = list()
        self.canjiaguode = list()
        ###############关注列表初始化
        try:
            followingf = open('关注者列表.txt', 'r+', encoding='utf-8')
            last_get_following_time = followingf.readlines().strip()
            if time.time() - int(last_get_following_time) > 7 * 24 * 60 * 60:
                followingf.close()
                followingf = open('关注者列表.txt', 'w', encoding='utf-8')
                uids = myapi.get_all_following(self.cookie, self.ua)
                followingf.writelines('{}\n'.format(time.time()))
                for i in uids:
                    followingf.writelines('{}\n'.format(i))
                    self.following_list.append(i)
                followingf.close()
            else:
                for i in followingf.readlines():
                    self.following_list.append(int(i.strip()))
                followingf.close()
        except:
            followingf = open('关注者列表.txt', 'w', encoding='utf-8')
            uids = myapi.get_all_following(self.cookie, self.ua)
            followingf.writelines('{}\n'.format(time.time()))
            for i in uids:
                followingf.writelines('{}\n'.format(i))
                self.following_list.append(i)
            followingf.close()
        #####################################
        self.fanmedal = dict()
        #####################################获取粉丝牌信息
        try:
            with open('粉丝勋章.txt', 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    self.fanmedal.update({i.strip().split('\t')[0]: i.strip().split('\t')[1]})
        except Exception as e:
            print(e)
        ######################################

    def contrust_lottery_data(self):
        lottery_data = myapi.get_data_from_server()
        l_dict = {'anchor': list(), 'popularity_red_pocket': list()}
        for i in lottery_data:
            if i.get('data') != '在线打卡':
                try:
                    if json.loads(i.get('data')).get('type') == 'anchor':
                        if json.loads(i.get('data')).get('current_time') + json.loads(i.get('data')).get('time') - int(
                                time.time()) > 0:  # 筛选出未开奖的天选
                            l_dict['anchor'].append(json.loads(i.get('data')))
                    elif json.loads(i.get('data')).get('type') == 'popularity_red_pocket':
                        if json.loads(i.get('data')).get('end_time') > int(time.time()):  # 筛选出为开奖的电池红包
                            red_pocket_dict = copy.deepcopy(json.loads(i.get('data')))
                            dtldict = {'id': i.get('id'), 'room_id': i.get('room_id')}
                            red_pocket_dict.update(dtldict)
                            l_dict['popularity_red_pocket'].append(red_pocket_dict)
                    else:
                        try:
                            with open('./log/未知的返回值.csv', 'a+', encoding='utf-8') as f:
                                f.writelines('{}\n'.format(i))
                        except:
                            f = open('./log/未知的返回值.csv', 'w+', encoding='utf-8')
                            f.close()
                            with open('./log/未知的返回值.csv', 'a+', encoding='utf-8') as f:
                                f.writelines('{}\n'.format(i))
                except Exception as e:
                    traceback.print_exc(limit=10, file=sys.stdout)
                    print(i.get('data'))
                    print(type(i.get('data')))
                    print(i)
                    # print(type(i))
            # else:
            #     yongjiaobendeuid = i.get('room_id')
            #     space_url = 'https://space.bilibili.com/{}'.format(i.get('room_id'))
            #     dakashijian = mymethod.timeshift(int(i.get('id')) / 1000)
            #     try:
            #         with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
            #             f.writelines(
            #                 '{0}\t{1}\t{2}\n'.format(dakashijian, yongjiaobendeuid, space_url))
            #     except:
            #         f = open('./log/使用脚本者.csv', 'w+', encoding='utf-8')
            #         f.writelines('脚本使用时间\t脚本者uid\t脚本者空间\n')
            #         f.close()
            #         with open('./log/使用脚本者.csv', 'a+', encoding='utf-8') as f:
            #             f.writelines(
            #                 '{0}\t{1}\t{2}\n'.format(dakashijian, yongjiaobendeuid, space_url))
        return l_dict

    async def get_data_from_server(self):
        while 1:
            l_dict = self.contrust_lottery_data()
            for i in l_dict.get('anchor'):
                self.lottery_filter(i)
            for i in l_dict.get('popularity_red_pocket'):
                self.lottery_filter(i)
            print(
                '\033[0;36;40m✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱♱⋰✧˖°⌖⋱\n\033[0m')
            await asyncio.sleep(self.jiangeshijian)


    def lottery_filter(self, l_data):  # 过滤并加入队列
        if l_data.get('type') == 'anchor':
            uid = l_data.get('uid')
            room_id = l_data.get('room_id')
            award_name = l_data.get('award_name')
            gift_price = l_data.get('gift_price')
            gift_num = l_data.get('gift_num')
            require_text = l_data.get('require_text')
            danmu = l_data.get('danmu')
            require_value = l_data.get('require_value')
            tianxuanid = l_data.get('id')
            print('{}\t\t【天选时刻】\n直播间：https://live.bilibili.com/{}\n奖品：{}\n要求：{}\n弹幕：{}\n金瓜子：{}'.format(
                mymethod.timeshift(time.time()), room_id,
                award_name,
                require_text,
                danmu,
                gift_price * gift_num))
            if tianxuanid in self.canjiaguode:
                print('【天选时刻】已参与\n')
                return 0
            for i in self.Anchor_ignore_keyword:
                if i in award_name:
                    print('【天选时刻】含有屏蔽词，不参与\n')
                    return 0
            if l_data.get('uid') in self.following_list:
                if l_data.get('require_type') == 1:
                    if uid in self.following_list:
                        if re.match('红包' or '元', award_name):
                            try:
                                money = re.findall('\d+', award_name)[0]
                                if int(money) < self.money_min:
                                    print('【天选时刻】红包金额小于{}元，不参加\n'.format(self.money_min))
                                    return 0
                            except:
                                print('【天选时刻】红包金额获取失败，不参与\n')
                                return 0
                        elif gift_price * gift_num == 0:
                            print('【天选时刻】成功加入队列\n')
                            self.anchor_queue.append(l_data)
                            return 0
                        else:
                            print('【天选时刻】付费的不参加\n')
                            return 0
                    else:
                        print('【天选时刻】未关注不参加\n')
                        return 0
                elif l_data.get('require_type') == 2:
                    if str(room_id) in self.fanmedal.keys():
                        if require_value <= int(self.fanmedal.get(str(room_id))):
                            if gift_price * gift_num == 0:
                                self.anchor_queue.append(l_data)
                                # myapi.join_anchor(tianxuanid, gift_id, gift_num, room_id, cookie, ua, csrf)
                                return 0
                            else:
                                print('【天选时刻】付费的不参加\n')
                                return 0
                        else:
                            print('【天选时刻】粉丝勋章等级不足，不参与\n')
                            return 0
                    else:
                        print('【天选时刻】未拥有粉丝勋章，不参与\n')
                        return 0
                elif l_data.get('require_type') == 3:
                    print('【天线时刻】大航海玩家，不参加\n')
                    return 0
            else:
                print('【天线时刻】未关注，不参加\n')
                return 0
            print('识别失败')
            print(l_data)
            return 0
            #################################################天选时刻过滤


        elif l_data.get('type') == 'popularity_red_pocket':
            anchor_uid = l_data.get('anchor_uid')
            total_price = l_data.get('total_price') / 1000
            room_id = l_data.get('room_id')
            hongbaoid = l_data.get('id')
            print('{}\n\t\t\t\t【电池红包】\n\t\t\t\t房间号： https://live.bilibili.com/{} \n\t\t\t\t金额：{}元'.format(
                mymethod.timeshift(time.time()),
                room_id, total_price))
            if hongbaoid in self.canjiaguode:
                print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t已参加，不再加入队列\n'.format(
                    mymethod.timeshift(time.time()), room_id))
                return 0
            if total_price >= 100:
                print(
                    '\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t超大红包成功加入队列\n'.format(
                        room_id))
                self.redpocket_queue.append(l_data)
            elif anchor_uid in self.following_list:
                if total_price >= self.money_min:
                    print('\t\t\t\t【电池红包】\n\t\t\t\t房间号： https://live.bilibili.com/{} \n\t\t\t\t关注者大红包成功加入队列\n'.format(
                        mymethod.timeshift(time.time()), room_id))
                else:
                    print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t关注者的小红包，不加入队列\n'.format(
                        mymethod.timeshift(time.time()), room_id))
            else:
                print('\t\t\t\t【电池红包】\n房间号： https://live.bilibili.com/{} \n\t\t\t\t未关注者小红包不加入队列\n'.format(room_id))
            return 0
        else:
            print('识别失败')
            print(l_data)
            return 0

    async def start_loop_and_darw(self, cookie, ua, csrf):
        while 1:
            await asyncio.sleep(10)
            print("\033[0;37;45m=====================================\033[0m")
            print(self.anchor_queue)
            if self.anchor_queue != []:
                for i in self.anchor_queue:
                    try:
                        with open('./log/参与天选记录.txt','a+',encoding='utf-8') as f:
                            f.writelines('{}\n'.format(i))
                    except:
                        f=open('./log/参与天选记录.txt','w',encoding='utf-8')
                        f.writelines('{}\n'.format(i))
                    tianxuanid = i.get('id')
                    self.canjiaguode.append(tianxuanid)
                    gift_id = i.get('gift_id')
                    gift_num = i.get('gift_num')
                    room_id = i.get('room_id')
                    thd.Timer(random.choice([1, 3, 5, 7, 9]), myapi.join_anchor,
                              (tianxuanid, gift_id, gift_num, room_id, cookie, ua, csrf,self.uid)).start()
                self.anchor_queue.clear()
            print(self.redpocket_queue)
            if self.redpocket_queue != []:
                for i in self.redpocket_queue:
                    try:
                        with open('./log/参与红包记录.txt','a+',encoding='utf-8') as f:
                            f.writelines('{}\n'.format(i))
                    except:
                        f=open('./log/参与红包记录.txt','w',encoding='utf-8')
                        f.writelines('{}\n'.format(i))
                    endtime = i.get('end_time')
                    id = i.get('id')
                    self.canjiaguode.append(id)
                    roomid = i.get('room_id')
                    ruid = i.get('anchor_uid')
                    thd.Timer(endtime - int(time.time()) - 30, myapi.popularity_red_pocket_join,
                              (self.uid,id, roomid, ruid, cookie, ua, csrf)).start()
                self.redpocket_queue.clear()
            print("\033[0;37;45m======================================\033[0m")

    async def main(self, cookie, ua, csrf):
        await asyncio.gather(my_lottery.get_data_from_server(),my_lottery.start_loop_and_darw(cookie, ua, csrf))
        #my_lottery.start_loop_and_darw(cookie, ua, csrf)

if __name__ == '__main__':
    my_lottery = Auto_lottery()
    asyncio.run(my_lottery.main(my_lottery.cookie,my_lottery.ua,my_lottery.csrf))
