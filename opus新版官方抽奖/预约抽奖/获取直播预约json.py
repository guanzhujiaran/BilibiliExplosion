# -*- coding: utf-8 -*-
# 发生sqlite不能在不同线程运行的时候，将sqlite_utils 里面的check_same_thread改成False
import ast
from functools import reduce

import threading

import queue

import json
import random
import re
import sys
from requests import session

from utl.代理.request_with_proxy import request_with_proxy

sys.path.append('C:/pythontest/')
import time
import traceback
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
from pylangtools.langconv import Converter
import requests
import os
import Bilibili_methods.all_methods
import atexit
import sqlite3

BAPI = Bilibili_methods.all_methods.methods()


class rid_get_dynamic:
    def __init__(self):
        self.ids_list = []
        self.ids_change_lock = threading.Lock()
        self.quit_lock = threading.Lock()
        self.quit_Flag = False
        self.proxy_request = request_with_proxy()
        self.proxy_request.mode = 'rand'
        self.sem = threading.Semaphore(50)  # 最大线程并发数
        # {"proxy":{"http":1.1.1.1},"status":"可用|-412|失效","update_ts":time.time(), }
        self.EndTimeSeconds = 1 * 3600  # 提前多久退出爬动态
        self.null_time_quit = 3000  # 遇到连续3000条data为None的sid 则退出
        self.null_timer = 0
        self.null_timer_lock = threading.Lock()
        self.highlight_word_list = ['jd卡', '京东卡', '红包', '主机', '显卡', '电脑', '天猫卡', '猫超卡', '现金',
                                    '见盘', '耳机', '鼠标', '手办', '景品', 'ps5', '内存', '风扇', '散热', '水冷',
                                    '主板', '电源', '机箱', 'fgo'
            , '折现', '樱瞳', '盈通', '🧧', '键盘']  # 需要重点查看的关键词列表
        cookie3 = gl.get_value('cookie3')  # 斯卡蒂
        ua3 = gl.get_value('ua3')

        def login_check(cookie, ua):
            headers = {
                'User-Agent': ua,
                'cookie': cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                name = res['data']['uname']
                self.username = name
                print('登录成功,当前账号用户名为%s' % name)
                return 1
            else:
                print('登陆失败,请重新登录')
                exit('登陆失败,请重新登录')

        # login_check(cookie3, ua3)
        atexit.register(self.quit)

        def get_attention(cookie, __ua):
            url = 'https://api.vc.bilibili.com/feed/v1/feed/get_attention_list'
            headers = {
                'cookie': cookie,
                'user-agent': __ua
            }
            req = requests.get(url=url, headers=headers)
            return req.json().get('data').get('list')

        # self.followed_list = get_attention(cookie3, ua3)  # 关注的列表
        # print(f'共{len(self.followed_list)}个关注')
        self.list_type_wrong = list()  # 出错动态内容
        self.list_deleted_maybe = list()  # 可能动态内容
        self.ids = int()
        self.times = 1
        self.btime = 0
        self.n = int()
        self.dynamic_timestamp = 0
        self.getfail = None  # 文件
        self.unknown = None  # 文件
        self.last_updated_reserve = None  # 文件
        self.all_reserve_relation = None  # 文件
        # 文件

        self.list_all_reserve_relation = list()  # 所有的动态内容，自己在后面加上是否是抽奖，官号等信息
        self.list_last_updated_reserve = list()  # 最后一次获取的rid内容
        self.list_getfail = list()
        self.list_unknown = list()
        # 内容

    def write_in_file(self):
        def my_write(path_Name, content_list, write_mode='a+'):
            with open(path_Name, mode=write_mode, encoding='utf-8') as f:
                for item in content_list:
                    f.writelines(f'{item}\n')

            content_list.clear()

        if self.list_all_reserve_relation:
            my_write(self.all_reserve_relation, self.list_all_reserve_relation)
        my_write(self.last_updated_reserve, self.list_last_updated_reserve, 'w')
        if self.list_getfail:
            my_write(self.getfail, self.list_getfail)
        if self.list_unknown:
            my_write(self.unknown, self.list_unknown)

    def mix_dict_resolve(self, my_dict: dict, parent_key=None) -> dict:
        '''
        多层dict解码，键名用.分割不同的key下内容
        :param my_dict:
        :param parent_key:
        :return:
        '''
        if parent_key is None:
            parent_key = []
        ret_dict = dict()
        for k, v in my_dict.items():
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except:
                    pass
            if isinstance(v, dict):
                parent_key.append(k)
                ret_dict.update(self.mix_dict_resolve(v, parent_key))
                continue
            key_prename = ''
            if parent_key:
                key_prename = '.'.join(parent_key) + '.'
            ret_dict.update({key_prename + k: str(v)})
        return ret_dict

    def resolve_dynamic(self, rid: int):
        '''
        解析动态json，然后以dict存到对应list里面
        :param rid:
        :param req1_dict:
        :return:
        '''
        # self.sem.acquire() ##这边加了一个上限锁之后，运行速度特别的慢，大概1秒钟1个，因为要返回结果之后，下一个线程才会继续进行

        req1_dict = self.reserve_relation_with_proxy(rid)
        # dynamic_data_dict = self.mix_dict_resolve(req1_dict)
        dynamic_data_dict = req1_dict
        # dynamic_data_dict.update({'update_time': BAPI.timeshift(time.time())})
        dynamic_data_dict.update({'ids': rid})
        try:
            dycode = req1_dict.get('code')
        except Exception as e:
            dycode = 404
            print(req1_dict)
            print('code获取失败')
        self.code_check(dycode)
        print('\n\t\t\t\t第' + str(self.times) + '次获取直播预约\t' + time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                    time.localtime()))
        print('\t\t\t\trid:{}'.format(rid))
        print('\n')
        self.times += 1
        dymsg = req1_dict.get('msg')
        dymessage = req1_dict.get('message')
        dydata = req1_dict.get('data')
        if dydata is None:
            if self.null_timer >= self.null_time_quit:
                self.quit()  # 遇到连续3000条data为None的sid 则退出
            else:
                with self.null_timer_lock:
                    self.null_timer += 1
                    print(f'当前已经有{self.null_timer}条data为None的sid')
        else:
            with self.null_timer_lock:
                self.null_timer = 0
        # try:
        #     dynamicid = req1_dict.get('data').get('card').get('desc').get('dynamic_id')
        # except Exception as e:  # {'code': 0, 'msg': '', 'message': '', 'data': {'_gt_': 0}}#type可能出错了
        #     if req1_dict.get('code') == 0 and req1_dict.get('msg') == '' and req1_dict.get('message') == '':
        #         self.list_type_wrong.append(dynamic_data_dict)
        #     dynamicid = 'None'
        #     traceback.print_exc()
        #     print(req1_dict)
        #     print('遇到动态类型可能出错的动态\n')
        #     print(BAPI.timeshift(time.time()))
        # print('https://t.bilibili.com/' + str(dynamicid) + '?tab=2')
        # self.sem.release()

        if dycode == 404:
            print(dycode, dymsg, dymessage)
            self.list_getfail.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
            self.list_deleted_maybe.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
            self.list_deleted_maybe.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == 0:
            self.n += 1
            try:
                self.dynamic_timestamp = dynamic_data_dict.get('data').get('list').get(str(rid)).get('stime')
                print(f"直播预约获取成功，直播预约创建时间：{BAPI.timeshift(self.dynamic_timestamp)}")
                if int(time.time()) - self.dynamic_timestamp <= 300:
                    self.quit()
            except:
                # self.dynamic_timestamp = 0
                print(f'直播预约失效，被删除:{req1_dict}')
            self.list_all_reserve_relation.append(dynamic_data_dict)
            self.list_last_updated_reserve.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == -412:
            self.code_check(dycode)
            print(req1_dict)
            self.list_getfail.append(dynamic_data_dict)
            return
        if dycode != 0:
            self.list_unknown.append(dynamic_data_dict)
        return

    def code_check(self, dycode):
        if self.btime > 500:
            self.quit()
        try:
            if dycode == 404:
                self.btime += 1
                return 0
        except Exception as e:
            print(dycode)
            print('未知类型代码')
            print(e)
        try:
            if dycode == 500205:
                self.btime += 1
                return 0
            else:
                self.btime = 0
        except Exception as e:
            print(dycode)
            print('未知类型代码')
            print(e)
        if dycode == -412:
            # time.sleep(eval(input('输入等待时间')))
            return -412
        elif dycode != 'None' and dycode != 500207 and \
                dycode != 500205 and dycode != 404 and dycode != -412 and self.dynamic_timestamp != 'None':
            if int(time.time()) - self.dynamic_timestamp < self.EndTimeSeconds:
                # if not self.quit_Flag:
                #     self.quit_Flag = True
                #     self.quit()
                # else:
                #     return
                pass

    def quit(self):
        """
            退出时必定执行
        """
        with self.quit_lock:
            if self.ids:
                if os.path.exists(self.unknown):
                    self.file_remove_repeat_contents(self.unknown)
                if os.path.exists(self.getfail):
                    self.file_remove_repeat_contents(self.getfail)
                if os.path.exists(self.last_updated_reserve):
                    self.file_remove_repeat_contents(self.last_updated_reserve)
                if os.path.exists(self.all_reserve_relation):
                    self.file_remove_repeat_contents(self.all_reserve_relation)

                # print(f'已获取到最近{self.EndTimeSeconds // 60}分钟为止的动态')
                with self.ids_change_lock:
                    self.ids = None

                print('共' + str(self.times - 1) + '次获取动态')
                print('其中' + str(self.n) + '个有效动态')
            else:
                return
        # os.system('shutdown /s /t 3600')
        # os.system('shutdown /s /t 60')

    def remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    def reserve_relation_with_proxy(self, ids, _type=2):
        print(f'reserve_relation_with_proxy\t当前ids:{ids}')
        url = 'https://api.bilibili.com/x/activity/up/reserve/relation/info?ids=' + str(ids)
        ua = random.choice(BAPI.User_Agent_List)
        headers = {
            'accept': 'text/html,application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        req_dict = self.proxy_request.request_with_proxy(method="GET", url=url, headers=headers)
        return req_dict

    def get_dynamic_with_thread(self):
        for ids_index in range(len(self.ids_list)):
            self.ids = self.ids_list[ids_index]
            self.null_timer = 0
            self.quit_Flag = False
            self.dynamic_timestamp = 0
            latest_rid = None
            while 1:
                self.resolve_dynamic(self.ids)  # 每次开启一轮多线程前先测试是否可用
                if self.ids is not None:
                    # with self.ids_change_lock:
                    #     self.ids += 1  # 每次多线程前先测试是否会412
                    #     latest_rid += 1
                    latest_rid = self.ids
                    pass
                else:
                    self.ids_list[ids_index] = latest_rid - self.null_timer
                    break
                if self.quit_Flag:
                    self.ids_list[ids_index] = latest_rid - self.null_timer
                    break
                thread_num = 500
                thread_list = []

                for t in range(thread_num):
                    thread = threading.Thread(target=self.resolve_dynamic, args=(self.ids,))
                    thread.daemon = True
                    with self.ids_change_lock:
                        self.ids += 1
                    thread_list.append(thread)
                    thread.start()

                for thread in thread_list:
                    thread.join()

                # if len(self.list_all_reserve_relation) > 1000:
                #     self.write_in_file()
                #     print('\n\n\t\t\t\t写入文件\n')

        print(
            f'已经达到{self.null_time_quit}条data为null信息或者最近预约时间只剩{int(time.time() - self.dynamic_timestamp)}秒，退出！')
        print(f'当前rid记录回滚{1000}条')
        ridstartfile = open('idsstart.txt', 'w', encoding='utf-8')
        ridstartfile.write("\n".join(str(e - (1000)) for e in self.ids_list))
        ridstartfile.close()
        self.write_in_file()
        print('\n\n\t\t\t\t写入文件\n')

    def file_remove_repeat_contents(self, filename: str):
        s = set()
        l = []
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line not in s:
                    s.add(line)
                    l.append(line)
        if l:
            with open(filename, "w", encoding="utf-8") as f:
                for line in l:
                    f.write(line + "\n")

    def init(self):
        '''
        初始化信息
        :return:
        '''
        if not os.path.exists('log'):
            os.mkdir('log')

        self.unknown = 'log/未知类型.csv'

        self.getfail = 'log/获取失败.csv'

        self.all_reserve_relation = '所有直播预约.csv'

        self.last_updated_reserve = '最后一次更新的直播预约.csv'

        try:
            ridstartfile = open('idsstart.txt', 'r', encoding='utf-8')
            with self.ids_change_lock:
                self.ids_list.extend([int(x) for x in ridstartfile.readlines()])
                self.ids = self.ids_list[0]
            ridstartfile.close()
            print('获取rid开始文件成功\nids开始值：{}'.format(self.ids))
            if self.ids <= 0:
                print('获取rid开始文件失败')
                sys.exit('获取rid开始文件失败')
        except:
            print('获取rid开始文件失败')
            sys.exit('获取rid开始文件失败')


if __name__ == "__main__":
    rid_run = rid_get_dynamic()
    rid_run.init()
    rid_run.get_dynamic_with_thread()
