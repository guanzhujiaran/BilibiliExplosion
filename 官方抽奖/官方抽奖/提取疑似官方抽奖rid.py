# -*- coding: utf-8 -*-
import copy

import time

from copy import deepcopy
from CONFIG import CONFIG
import random
import pandas as pd
import os
from utl.代理.request_with_proxy import request_with_proxy


class exctract_official_lottery:
    def __init__(self):
        self.__dir = CONFIG.root_dir+'opus新版官方抽奖/官方抽奖/'
        self.Get_All_Flag = False  # 是否获取所有的rid
        if not os.path.exists('log'):
            os.mkdir('log')
        if not os.path.exists('result'):
            os.mkdir('result')
        self.oringinal_official_lots: [dict] = []
        if os.path.exists('result/全部官方抽奖.csv'):
            self.oringinal_official_lots = pd.read_csv(self.__dir+'result/全部官方抽奖.csv', encoding='utf-8',
                                                        dtype='str')
            self.oringinal_official_lots.duplicated(subset=['rid'],keep='last')
        self.all_offcial_lots: [dict] = []  # 所有的抽奖
        self.maybe_all_offcial_lots: [dict] = []
        self.all_offcial_lots_req_dict: [dict] = []
        self.last_update_offcial_lots: [dict] = []  # 最后一次更新的抽奖
        self.maybe_last_update_offcial_lots: [dict] = []
        self.last_update_offcial_lots_req_dict: [dict] = []

        self.proxy_request = request_with_proxy()

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def get_maybe_official_lots(self):
        '''
        读取文件，写入内存中
        :return:
        '''
        with open(os.path.join(self.__dir,'../../rid代理爬动态/最后一次更新的rid动态(polymer).csv'), 'r', encoding='utf-8') as f:
            for i in f.readlines():
                if '互动抽奖 ' in i or '\u200b互动抽奖' in i or '互動抽獎 ' in i or '\u200b互動抽獎' in i or r'\u200b互動抽獎' in i or r'\u200b互动抽奖' in i:
                    self.maybe_last_update_offcial_lots.append(eval(i))
        if self.Get_All_Flag:
            with open(os.path.join(self.__dir,'../../rid代理爬动态/所有rid动态(polymer).csv'), 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    if '互动抽奖 ' in i or '\u200b互动抽奖' in i or '互動抽獎 ' in i or '\u200b互動抽獎' in i or r'\u200b互動抽獎' in i or r'\u200b互动抽奖' in i:
                        self.maybe_all_offcial_lots.append(eval(i))
            with open(os.path.join(self.__dir,'../../rid代理爬动态/所有rid动态.csv'), 'r', encoding='utf-8') as f:
                for i in f.readlines():
                    if '互动抽奖 ' in i or '\u200b互动抽奖' in i or '互動抽獎 ' in i or '\u200b互動抽獎' in i or r'\u200b互動抽獎' in i or r'\u200b互动抽奖' in i:
                        self.maybe_all_offcial_lots.append(eval(i))
        else:
            self.maybe_all_offcial_lots = copy.deepcopy(self.maybe_last_update_offcial_lots)

    def construct_my_doc_dict(self, doc_request_dict: dict) -> dict:
        '''
        like_count/collect_count/
        vote_count才是点赞数
        comment_count是评论数
        :param doc_request_dict:
        :return:
        '''
        ret_dict = dict()
        try:
            space_url = f'https://space.bilibili.com/{doc_request_dict.get("data").get("item").get("modules").get("module_author").get("mid")}/dynamic'
        except:
            space_url = f'https://space.bilibili.com/{doc_request_dict.get("data").get("user").get("uid")}/dynamic'
        try:
            id_str = doc_request_dict.get("rid")
            if id_str:
                dynamic_url = f'https://t.bilibili.com/{id_str}?type=2'
            else:
                id_str = doc_request_dict.get("data").get("item").get("doc_id")
                dynamic_url = f'https://t.bilibili.com/{id_str}?type=2'
        except:
            dynamic_url = f'https://t.bilibili.com/{doc_request_dict.get("data").get("item").get("doc_id")}?type=2'
        try:
            name = doc_request_dict.get("data").get("item").get("modules").get("module_author").get("name")
        except:
            name = doc_request_dict.get("data").get("user").get("name")
        try:
            description = doc_request_dict.get("data").get("item").get("modules")
            if not description:
                description = doc_request_dict.get("data").get("item")
        except:
            description = doc_request_dict.get("data").get("item")
        try:
            like_count = doc_request_dict.get("data").get("item").get("modules").get("module_stat").get("like").get(
                "count")
        except:
            like_count = 0
        try:
            comment_count = doc_request_dict.get("data").get("item").get("modules").get("module_stat").get(
                "comment").get("count")
        except:
            comment_count = 0
        try:
            forward_count = doc_request_dict.get("data").get("item").get("modules").get("module_stat").get(
                "forward").get("count")
        except:
            forward_count = 0
        try:
            upload_time = doc_request_dict.get("data").get("item").get("modules").get("module_author").get("pub_ts")
        except:
            upload_time = doc_request_dict.get("data").get("item").get('upload_timestamp')
        try:
            uid = doc_request_dict.get("data").get("item").get("modules").get("module_author").get("mid")
        except:
            uid = doc_request_dict.get("data").get("user").get("uid")
        ret_dict.update({
            'space_url': space_url,
            'dynamic_url': dynamic_url,
            'name': name,
            'description': description,
            'like_count': like_count,
            'comment_count': comment_count,
            'forward_count': forward_count,
            'upload_time': upload_time,
            'rid': doc_request_dict.get('rid'),
            'uid': uid,
        })
        return ret_dict

    def check_mybe_lots(self):
        '''
        检查是否是抽奖，code==0如果是抽奖则添加至req_dict的list中，然后写入log里
        :return:
        '''
        checked_dict = dict()
        times = 1
        original_rid_list = list(self.oringinal_official_lots['rid'])
        for i in self.maybe_last_update_offcial_lots:
            print(f'当前进度：【{times}/{len(self.maybe_last_update_offcial_lots)}】')
            times += 1
            rid = i.get('rid')
            if str(rid) in original_rid_list:
                print("已经获取到的rid")
                continue
            doc_detail = self.construct_my_doc_dict(i)
            if str(rid) not in list(checked_dict.keys()):
                url = f'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type=2&business_id={rid}'
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
                    'user-agent': CONFIG.rand_ua,
                }
                req_dict = self.proxy_request.sync_request_with_proxy(method='get', url=url, headers=headers)
                print(url, req_dict)
                req_dict.update(doc_detail)
                checked_dict.update({str(rid): req_dict})
                if req_dict.get('code') == 0:
                    self.last_update_offcial_lots_req_dict.append(req_dict)
            else:
                if checked_dict.get(str(rid)).get('code') == 0:
                    self.last_update_offcial_lots_req_dict.append(checked_dict.get(str(rid)))

        if self.Get_All_Flag:
            times = 0
            for i in self.maybe_all_offcial_lots:
                print(f'当前进度：【{times}/{len(self.maybe_all_offcial_lots)}】')
                times += 1
                rid = i.get('rid')
                doc_detail = self.construct_my_doc_dict(i)
                if str(rid) not in list(checked_dict.keys()):
                    url = f'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type=2&business_id={rid}'
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
                        'user-agent': CONFIG.rand_ua,
                    }
                    req_dict = self.proxy_request.sync_request_with_proxy(method='get', url=url, headers=headers)
                    print(url, req_dict)
                    req_dict.update(doc_detail)
                    checked_dict.update({str(rid): req_dict})
                    if req_dict.get('code') == 0:
                        self.all_offcial_lots_req_dict.append(req_dict)
                        if str(rid) not in original_rid_list:  # 如果原来的文件里面没有，那么添加回更新内容中
                            self.last_update_offcial_lots_req_dict.append(req_dict)
                else:
                    if checked_dict.get(str(rid)).get('code') == 0:
                        self.all_offcial_lots_req_dict.append(checked_dict.get(str(rid)))
        else:
            self.all_offcial_lots_req_dict = deepcopy(self.last_update_offcial_lots_req_dict)

        all_lottery_path = self.__dir+'log/all_lottery_notice_req_dict.csv'
        last_update_lottery_path = self.__dir+'log/last_update_lottery_notice_req_dict.csv'
        if self.all_offcial_lots_req_dict:
            if os.path.exists(all_lottery_path):
                with open(all_lottery_path, 'a+', encoding='utf-8') as f:
                    for item in self.all_offcial_lots_req_dict:
                        f.writelines(f'{item}\n')
            else:
                with open(all_lottery_path, 'w', encoding='utf-8') as f:
                    for item in self.all_offcial_lots_req_dict:
                        f.writelines(f'{item}\n')
        if self.last_update_offcial_lots_req_dict:
            with open(last_update_lottery_path, 'w', encoding='utf-8') as f:
                for item in self.last_update_offcial_lots_req_dict:
                    f.writelines(f'{item}\n')

        if not os.path.exists(self.__dir+'log/疑似抽奖'):
            os.mkdir(self.__dir+'log/疑似抽奖')
        maybe_all_lottery_path = self.__dir+'log/疑似抽奖/maybe_all_offcial_lots.csv'
        maybe_last_update_lottery_path = self.__dir+'log/疑似抽奖/maybe_last_update_offcial_lots.csv'
        if self.maybe_all_offcial_lots:
            if os.path.exists(maybe_all_lottery_path):
                with open(maybe_all_lottery_path, 'a+', encoding='utf-8') as f:
                    for item in self.maybe_all_offcial_lots:
                        f.writelines(f'{item}\n')
            else:
                with open(maybe_all_lottery_path, 'w', encoding='utf-8') as f:
                    for item in self.maybe_all_offcial_lots:
                        f.writelines(f'{item}\n')

        if self.maybe_last_update_offcial_lots:
            with open(maybe_last_update_lottery_path, 'w', encoding='utf-8') as f:
                for item in self.maybe_last_update_offcial_lots:
                    f.writelines(f'{item}\n')
        self.maybe_last_update_offcial_lots.clear()
        self.maybe_all_offcial_lots.clear()

    def resolve_official_lottery_form_polymer_dynamic(self, lottery_dict: dict) -> dict:
        '''
        解析lottery_notice_dict
        :param lottery_dict:
        :return:
        '''
        ret_dict = dict()
        rid = lottery_dict.get('rid')
        lottery_id = lottery_dict.get('data').get('lottery_id')
        business_id = lottery_dict.get('data').get('business_id')
        sender_uid = lottery_dict.get('data').get('sender_uid')
        status = lottery_dict.get('data').get('status')
        lottery_time = self._timeshift(lottery_dict.get('data').get('lottery_time'))
        lottery_at_num = lottery_dict.get('data').get('lottery_at_num')

        first_prize = lottery_dict.get('data').get('first_prize')  # 奖品数量
        second_prize = lottery_dict.get('data').get('second_prize')  # 奖品数量
        third_prize = lottery_dict.get('data').get('third_prize')  # 奖品数量

        first_prize_cmt = lottery_dict.get('data').get('first_prize_cmt')  # 奖品描述
        second_prize_cmt = lottery_dict.get('data').get('second_prize_cmt')  # 奖品描述
        third_prize_cmt = lottery_dict.get('data').get('third_prize_cmt')  # 奖品描述

        business_type = lottery_dict.get('data').get('business_type')  # 官抽类型

        lottery_result = lottery_dict.get('data').get('lottery_result')
        updata_time = self._timeshift(lottery_dict.get('data').get('ts'))  # 获取的时间

        ret_dict.update({
            'lottery_id': lottery_id,
            'business_id': business_id,
            'sender_uid': sender_uid,
            'status': status,
            'lottery_time': lottery_time,
            'lottery_at_num': lottery_at_num,
            'first_prize': first_prize,
            'second_prize': second_prize,
            'third_prize': third_prize,
            'first_prize_cmt': first_prize_cmt,
            'second_prize_cmt': second_prize_cmt,
            'third_prize_cmt': third_prize_cmt,
            'business_type': business_type,
            'lottery_result': lottery_result,
            'updata_time': updata_time,
            'rid': rid,
        })
        return ret_dict

    def write_in_official_lottery(self):
        for i in self.last_update_offcial_lots_req_dict:
            self.last_update_offcial_lots.append(self.resolve_official_lottery_form_polymer_dynamic(i))
        for i in self.all_offcial_lots_req_dict:
            self.all_offcial_lots.append(self.resolve_official_lottery_form_polymer_dynamic(i))
        last_update_df = pd.DataFrame(self.last_update_offcial_lots, dtype='str')
        last_update_df.to_csv(self.__dir+'result/更新的官方抽奖.csv', mode='w', encoding='utf-8', index=False, header=True)

        all_df = pd.concat([self.oringinal_official_lots,pd.DataFrame(self.all_offcial_lots, dtype='str')])
        all_df.duplicated(subset=['rid'],keep='last')

        all_df.to_csv(self.__dir+'result/全部官方抽奖.csv', mode='w', encoding='utf-8', index=False, header=True)

    def main(self):
        print('获取所有疑似的')
        self.get_maybe_official_lots()  # 获取所有疑似的
        print('检查疑似的并将相应写入文件里')
        self.check_mybe_lots()  # 检查疑似的并将相应写入文件里
        print('将检查完的内容以csv的格式保存到文件')
        self.write_in_official_lottery()  # 将检查完的内容以csv的格式保存到文件


if __name__ == '__main__':
    m = exctract_official_lottery()
    # m.Get_All_Flag = True  # 为True时重新获取所有的抽奖，为False时将更新的内容附加在所有的后面
    m.main()


