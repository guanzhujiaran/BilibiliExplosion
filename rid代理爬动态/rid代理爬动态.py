# -*- coding: utf-8 -*-
import atexit
import datetime
import json
import os
import random
import sys
import threading
# sys.path.append('C:/pythontest/')
import time
import uuid
from functools import reduce

import requests

import Bilibili_methods.all_methods
import b站cookie.globalvar as gl
from utl.代理.request_with_proxy import request_with_proxy

BAPI = Bilibili_methods.all_methods.methods()


class rid_get_dynamic:
    def __init__(self):
        self.User_Agent_List = [
            # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.43',
            # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57',
            # 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67',
            # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'


            'Mozilla/5.0'

            # 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/115.0.0.0',
            # 'Mozilla/5.0 (Linux; Android 7.0; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/48.0.2564.116 Mobile Safari/537.36 T7/10.3 SearchCraft/2.6.2 (Baidu; P1 7.0)',
            # 'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            # 'Mozilla/5.0 (Linux; Android 5.0; SM-N9100 Build/LRX21V) > AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 > Chrome/37.0.0.0 Mobile Safari/537.36 > MicroMessenger/6.0.2.56_r958800.520 NetType/WIFI'
        ]
        self.Write_LOCK = threading.Lock()
        self.quit_Flag = False
        self.first_round = True
        self.proxy_request = request_with_proxy()
        self.proxy_request.timeout = 10  # 超时
        self.proxy_request.mode = 'single'  # 使用随机的代理策略 single||rand
        self.sem = threading.Semaphore(10)  # 最大线程并发数
        # {"proxy":{"http":1.1.1.1},"status":"可用|-412|失效","update_ts":time.time(), }
        self.EndTimeSeconds = 2 * 3600  # 提前多久退出爬动态
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
        self.list_deleted_maybe = list()  # 可能动态内容
        self.rid = int()
        self.times = 1
        self.btime = 0
        self.n = int()
        self.dynamic_timestamp = int()
        self.getfail = None  # 文件
        self.unknown = None  # 文件
        self.last_updated_dynamic = None  # 文件
        self.all_rid_dynamic = None  # 文件
        # 文件

        self.list_all_rid_dynamic = list()  # 所有的动态内容，自己在后面加上是否是抽奖，官号等信息
        self.list_last_updated_dynamic = list()  # 最后一次获取的rid内容
        self.list_getfail = list()
        self.list_unknown = list()
        # 内容

    def write_in_file(self):
        def my_write(path_Name, content_list, write_mode='a+'):
            with open(path_Name, mode=write_mode, encoding='utf-8') as f:
                for item in content_list:
                    f.writelines(f'{item}\n')

            content_list.clear()

        with self.Write_LOCK:
            if self.list_all_rid_dynamic:
                my_write(self.all_rid_dynamic, self.list_all_rid_dynamic)
            if self.list_last_updated_dynamic:
                if self.first_round:
                    my_write(self.last_updated_dynamic, self.list_last_updated_dynamic, 'w')
                    self.first_round = False
                else:
                    my_write(self.last_updated_dynamic, self.list_last_updated_dynamic)
            if self.list_getfail:
                my_write(self.getfail, self.list_getfail)
            if self.list_deleted_maybe:
                my_write(self.getfail, self.list_deleted_maybe)
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

    def resolve_dynamic_by_doc(self, rid: int):
        '''
        解析动态json，然后以dict存到对应list里面
        :param rid:
        :return:
        '''
        with self.sem:
            req1_dict = self.rid_dynamic_by_doc_with_proxy(rid)
            # dynamic_data_dict = self.mix_dict_resolve(req1_dict)

            dynamic_data_dict = req1_dict
            # dynamic_data_dict.update({'update_time': BAPI.timeshift(time.time())})
            dynamic_data_dict.update({'rid': rid})
            try:
                dycode = req1_dict.get('code')
            except Exception as e:
                dycode = 404
                print(req1_dict)
                print('code获取失败')
            self.code_check(dycode)
            print(
                f'第{str(self.times)}次获取动态\t\t\t\t\t\t\t\t\t\t\t\t\t{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\trid:{rid}\tCode:{dycode}')
            if dycode != 0:
                print(f'{rid}:{req1_dict}\t动态code不为0请注意！')
            self.times += 1
            dymsg = req1_dict.get('msg')
            dymessage = req1_dict.get('message')
            dydata = req1_dict.get('data')
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
                self.dynamic_timestamp = dynamic_data_dict.get('data').get('item').get('upload_timestamp')
                print(
                    f"rid:{rid}\thttps://h.bilibili.com/{rid}\t动态获取成功，动态创建时间：{BAPI.timeshift(self.dynamic_timestamp)}\t\t\t\t\t当前时间：{self.proxy_request._timeshift(time.time())}")
            except:
                self.dynamic_timestamp = 0
                print(f'动态失效，被删除或type不匹配:{req1_dict}')
            self.list_all_rid_dynamic.append(dynamic_data_dict)
            self.list_last_updated_dynamic.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == -1:
            self.code_check(dycode)
        if dycode == -412:
            self.code_check(dycode)
            print(req1_dict)
            self.list_getfail.append(dynamic_data_dict)
            return
        if dycode != 0:
            self.list_unknown.append(dynamic_data_dict)
        return

    def resolve_dynamic_by_polymer(self, rid: int):
        '''
        解析动态json，然后以dict存到对应list里面
        :param rid:
        :return:
        '''
        with self.sem:
            req1_dict = self.rid_dynamic_by_polymer_with_proxy(rid)
            # dynamic_data_dict = self.mix_dict_resolve(req1_dict)

            dynamic_data_dict = req1_dict
            # dynamic_data_dict.update({'update_time': BAPI.timeshift(time.time())})
            dynamic_data_dict.update({'rid': rid})
            try:
                dycode = req1_dict.get('code')
            except Exception as e:
                dycode = 404
                print(req1_dict)
                print('code获取失败')
            self.code_check(dycode)
            print(
                f'第{str(self.times)}次获取动态\t\t\t\t\t\t\t\t\t\t\t\t\t{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\trid:{rid}\tCode:{dycode}')
            if dycode != 0:
                print(f'{rid}:{req1_dict}\t动态code不为0请注意！')
            self.times += 1
            dymsg = req1_dict.get('msg')
            dymessage = req1_dict.get('message')
            dydata = req1_dict.get('data')
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
                self.dynamic_timestamp = dynamic_data_dict.get('data').get('item').get('modules').get(
                    'module_author').get('pub_ts')
                print(
                    f"rid:{rid}\thttps://h.bilibili.com/{rid}\t动态获取成功，动态创建时间：{BAPI.timeshift(self.dynamic_timestamp)}\t\t\t\t\t当前时间：{self.proxy_request._timeshift(time.time())}")
            except:
                self.dynamic_timestamp = 0
                print(f'动态失效，被删除或type不匹配:{req1_dict}')
            self.list_all_rid_dynamic.append(dynamic_data_dict)
            self.list_last_updated_dynamic.append(dynamic_data_dict)
            self.code_check(dycode)
            return
        if dycode == -1:
            self.code_check(dycode)
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
            self.quit_Flag = True
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
            if dycode == 500205 or dycode == -1:
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
                if not self.quit_Flag:
                    self.quit_Flag = True
                    self.quit()
                else:
                    return

    def quit(self):
        """
            退出时必定执行
        """
        with self.Write_LOCK:
            if self.rid:
                print(f'已获取到最近{self.EndTimeSeconds // 60}分钟为止的动态')
                print('rid记录回滚10000条')
                self.rid -= 10000
                self.write_in_file()
                print(f'写入rid：{self.rid}')
                ridstartfile = open('ridstart.txt', 'w')
                ridstartfile.write(str(self.rid - 5000))
                ridstartfile.close()
                self.rid = None
            else:
                return
        print('共' + str(self.times - 1) + '次获取动态')
        print('其中' + str(self.n) + '个有效动态')

        # os.system('shutdown /s /t 3600')
        # os.system('shutdown /s /t 60')
        return

    def remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    def rid_dynamic_by_doc_with_proxy(self, rid, _type=2):
        '''
        使用doc/detail的api获取动态内容，现在好像也不行了——————2023-06-19
        :param rid:
        :param _type:
        :return:
        '''
        print(f'rid_dynamic_with_proxy\t当前rid:{rid}\t\t\t\t\t{self.proxy_request._timeshift(time.time())}')
        url = 'http://api.vc.bilibili.com/link_draw/v1/doc/detail?doc_id=' + str(rid)
        ua = random.choice(self.User_Agent_List)
        fake_cookie = {
            "buvid3": "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999)),
            "DedeUserID": "{}".format(random.randint(1, 99999))
        }
        fake_cookie_str = ""
        for k, v in fake_cookie.items():
            fake_cookie_str += f'{k}={v}; '
        headers = {
            'accept': 'text/html,application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            "origin": "https://h.bilibili.com",
            "referer": "https://h.bilibili.com/",
            'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            'cookie': fake_cookie_str,
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        req_dict = self.proxy_request.sync_request_with_proxy(method="GET", url=url, headers=headers)
        return req_dict

    def rid_dynamic_by_polymer_with_proxy(self, rid, _type=2):
        '''
        通过polymer获取动态，现在似乎没有什么大的问题————2023-06-19
        :param rid:
        :param _type:
        :return:
        '''
        url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&platform=h5&rid={rid}&type=2&gaia_source=Athena'
        # fake_cookie = {
        #     "buvid3": "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999)),
        #     "DedeUserID": "{}".format(random.randint(1, 99999))
        # }
        # fake_cookie_str = ""
        # for k, v in fake_cookie.items():
        #     fake_cookie_str += f'{k}={v}; '
        ua = random.choice(self.User_Agent_List)
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            'cookie': 'fake_cookie_str'
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        req_dict = self.proxy_request.sync_request_with_proxy(method='get', url=url, headers=headers)
        return req_dict

    def rid_dynamic_by_polymer_opus_h5_with_proxy(self, rid):
        '''
        https://api.bilibili.com/x/polymer/web-dynamic/v1/opus/detail?id=185434542991531621&platform=h5&timezone_offset=-480
        获取动态，这个不太行，一定要有id，rid不可以
        :return:
        '''
        url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&platform=h5&rid={rid}&type=2&gaia_source=Athena'
        # fake_cookie = {
        #     "buvid3": "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999)),
        #     "DedeUserID": "{}".format(random.randint(1, 99999))
        # }
        # fake_cookie_str = ""
        # for k, v in fake_cookie.items():
        #     fake_cookie_str += f'{k}={v}; '
        ua = random.choice(self.User_Agent_List)
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "\"Windows\"",
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
            'cookie': 'fake_cookie_str'
            # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
            #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
            # 'From': 'bingbot(at)microsoft.com',
        }
        req_dict = self.proxy_request.sync_request_with_proxy(method='get', url=url, headers=headers)
        return req_dict

    def get_dynamic_with_thread(self):
        counter = 0
        while not self.quit_Flag:
            counter += 1
            print(f'第{counter}轮开启多线程！\n当前线程数量：{len(threading.enumerate())}')
            if self.quit_Flag:
                break

            if not self.rid:
                break
            thread_num = 15
            thread_list = []

            for t in range(thread_num):
                if self.quit_Flag:
                    break
                if self.rid:
                    now_rid = self.rid
                    thread = threading.Thread(target=self.resolve_dynamic_by_polymer, args=(now_rid,))
                    thread.daemon = True
                    self.rid += 1
                    thread_list.append(thread)
                    thread.start()
            print(f'当前剩余可开启线程数量：{self.sem._value}')
            for t in thread_list:
                if self.quit_Flag:
                    t.join()
                if self.sem._value == 0:
                    t.join()
            if self.times%500==0:
                time.sleep(30)
            if len(self.list_all_rid_dynamic) > 1000:
                self.write_in_file()
                print('\n\n\t\t\t\t写入文件\n')
            if self.quit_Flag:
                self.write_in_file()
                print('\n\n\t\t\t\t写入文件\n')

    def init(self):
        '''
        初始化信息
        :return:
        '''
        if not os.path.exists('log'):
            os.mkdir('log')

        self.unknown = 'log/未知类型.csv'

        self.getfail = 'log/获取失败.csv'

        self.all_rid_dynamic = '所有rid动态(polymer).csv'

        self.last_updated_dynamic = '最后一次更新的rid动态(polymer).csv'

        try:
            ridstartfile = open('ridstart.txt', 'r')
            self.rid = int(ridstartfile.readline())
            ridstartfile.close()
            print('获取rid开始文件成功\nrid开始值：{}'.format(self.rid))
            if self.rid <= 0:
                print('获取rid开始文件失败')
                sys.exit('获取rid开始文件失败')
        except:
            print('获取rid开始文件失败')
            sys.exit('获取rid开始文件失败')

    def gennerate_article_and_start_next_turn(self):
        from opus新版官方抽奖.官方抽奖.提取疑似官方抽奖rid import exctract_official_lottery
        from opus新版官方抽奖.官方抽奖.提交官方抽奖专栏 import generate_cv
        from rid疑似抽奖动态.提取rid疑似抽奖动态 import extract_rid_lottery_dynamic

        m = exctract_official_lottery()
        # m.Get_All_Flag = True  # 为True时重新获取所有的抽奖，为False时将更新的内容附加在所有的后面
        m.main()

        ua3 = gl.get_value('ua3')
        csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
        cookie3 = gl.get_value('cookie3')
        buvid3 = gl.get_value('buvid3_3')
        if cookie3 and csrf3 and ua3 and buvid3:
            gc = generate_cv(cookie3, ua3, csrf3, buvid3)
            gc.official_lottery()
        else:
            print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)

        e = extract_rid_lottery_dynamic()
        e.main()

        now_time = int(time.time())
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_zero = time.mktime(tomorrow.timetuple())
        T = threading.Timer(tomorrow_zero - now_time, rid_get_dynamic_main)
        T.start()
        T.join()


def rid_get_dynamic_main():
    rid_run = rid_get_dynamic()
    rid_run.init()
    rid_run.get_dynamic_with_thread()


if __name__ == "__main__":
    rid_get_dynamic_main()
