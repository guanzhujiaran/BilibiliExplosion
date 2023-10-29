# -*- coding: utf-8 -*-
import time

import json
import os
from CONFIG import CONFIG
import pandas as pd
import requests
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as m

MYAPI = m.methods()


class extract_rid_lottery_dynamic:
    def __init__(self):
        self.__dir = CONFIG.root_dir+'rid代理爬动态/rid疑似抽奖动态/'
        self.Get_All_Flag = False  # 如果是True 则从头开始重新获取所有的抽奖信息
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

        login_check(cookie3, ua3)

        def get_attention(cookie, __ua):
            url = 'https://api.vc.bilibili.com/feed/v1/feed/get_attention_list'
            headers = {
                'cookie': cookie,
                'user-agent': __ua
            }
            req = requests.get(url=url, headers=headers)
            return req.json().get('data').get('list')

        self.followed_list = []
        self.followed_list = get_attention(cookie3, ua3)  # 关注的列表
        print(f'当前关注数量：{len(self.followed_list)}')

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
            id_str = doc_request_dict.get("data").get("item").get("id_str")
            if id_str:
                dynamic_url = f'https://www.bilibili.com/opus/{id_str}'
            else:
                id_str = doc_request_dict.get("data").get("item").get("doc_id")
                dynamic_url = f'https://t.bilibili.com/{id_str}?type=2'
        except:
            id_str = '0'
            dynamic_url = f'https://t.bilibili.com/{doc_request_dict.get("data").get("item").get("doc_id")}?type=2'
        try:
            name = doc_request_dict.get("data").get("item").get("modules").get("module_author").get("name")
        except:
            name = doc_request_dict.get("data").get("user").get("name")
        try:
            module_dynamic = doc_request_dict.get("data").get("item").get("modules").get('module_dynamic')
        except:
            module_dynamic = doc_request_dict.get("data").get("item")
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
        try:
            official_verify = doc_request_dict.get("data").get("item").get("modules").get("module_author").get(
                "official_verify").get('type')
        except:
            official_verify = -1
        ret_dict.update({
            'space_url': space_url,
            'dynamic_url': dynamic_url,
            'id_str': id_str,
            'name': name,
            'module_dynamic': module_dynamic,
            'like_count': like_count,
            'comment_count': comment_count,
            'forward_count': forward_count,
            'upload_time': upload_time,
            'rid': doc_request_dict.get('rid'),
            'uid': uid,
            "official_verify": official_verify,
        })
        return ret_dict

    def construct_my_write_in_dict(self, doc_dict: dict) -> dict:
        '''
        'space_url': space_url,
        'dynamic_url': dynamic_url,
        'name': name,
        'module_dynamic': module_dynamic,
        'like_count': like_count,
        'comment_count': comment_count,
        'forward_count': forward_count,
        'upload_time': upload_time,
        'rid': doc_request_dict.get('rid'),
        'uid': uid,
        "official_verify": official_verify,
        :param doc_dict:
        :return:
        '''
        ret_dict = dict()

        def get_dynamic_content(__module_dynamic: dict) -> str:
            if __module_dynamic.get('desc'):
                desc = __module_dynamic.get('desc').get('text')
            else:
                desc = __module_dynamic.get('major').get('blocked').get('hint_message')
            return desc

        islot = '否'
        is_following = '未关注'
        is_highlighted_keyword = ''
        uid = doc_dict.get('uid')
        name = doc_dict.get('name')
        upload_time = doc_dict.get('upload_time')
        upload_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(upload_time))
        official_verify = doc_dict.get('official_verify')
        if official_verify == 1:
            official_verify_str = '蓝v'
        elif official_verify == 0:
            official_verify_str = '黄v'
        elif official_verify == -1:
            official_verify_str = '普通用户'
        else:
            official_verify_str = '未知类型用户'
        like_count = doc_dict.get('like_count')
        comment_count = doc_dict.get('comment_count')
        forward_count = doc_dict.get('forward_count')
        module_dynamic = doc_dict.get('module_dynamic')
        dynamic_url = doc_dict.get('dynamic_url')
        description = get_dynamic_content(module_dynamic)
        rid = doc_dict.get('rid')
        id_str = doc_dict.get('id_str')
        if not MYAPI.choujiangxinxipanduan(description):
            islot = '是'
        if doc_dict.get('uid') in self.followed_list:
            is_following = '已关注'
        for i in self.highlight_word_list:
            if i in description:
                is_highlighted_keyword += f'{i};'
        description = description.replace('\n', '\\r\\n').replace('\r', '\\r\\n')
        ret_dict.update({
            'uid': uid,
            '发布者昵称': name,
            '发布者账号类型': official_verify_str,
            '动态rid': rid,
            '发布时间': upload_time_str,
            '动态内容': description,
            '新版动态链接': dynamic_url,
            '旧版动态链接': f'https://t.bilibili.com/{id_str}',
            '是否是抽奖': islot,
            '关注状态': is_following,
            '特别想要的奖品关键词': is_highlighted_keyword,
            '点赞数': like_count,
            '评论数': comment_count,
            '转发数': forward_count,
        })
        return ret_dict

    def main(self):
        if self.Get_All_Flag:
            all_lot_write_in_list = []
            with open(os.path.join(self.__dir, '../所有rid动态(polymer).csv'), 'r', encoding='utf8') as f:
                for rid_req in f.readlines():
                    rid_dict = eval(rid_req)
                    doc_dict = self.construct_my_doc_dict(rid_dict)
                    all_lot_write_in_list.append(self.construct_my_write_in_dict(doc_dict))
            all_df = pd.DataFrame(all_lot_write_in_list, dtype='str')
            all_df.drop_duplicates(keep='last', inplace=True)
            all_df.to_csv(self.__dir + 'result/所有rid动态的疑似抽奖(polymer).csv', index=False, encoding='utf8',
                          header=True)
            all_lot_write_in_list.clear()
            all_df = None

        last_lot_write_in_list = []
        with open(os.path.join(self.__dir, '../最后一次更新的rid动态(polymer).csv'), 'r', encoding='utf-8') as f:
            for rid_req in f.readlines():
                rid_dict = eval(rid_req)
                doc_dict = self.construct_my_doc_dict(rid_dict)
                last_lot_write_in_list.append(self.construct_my_write_in_dict(doc_dict))
        last_df = pd.DataFrame(last_lot_write_in_list, dtype='str')
        last_df.drop_duplicates(keep='last', inplace=True)
        last_df.to_csv(self.__dir + 'result/最后一次更新rid动态的疑似抽奖(polymer).csv', index=False, encoding='utf8',
                       header=True)
        last_lot_write_in_list.clear()

        if not self.Get_All_Flag:  # 如果不需要获取所有的信息就只将更新的信息添加在所有的信息后面
            if os.path.exists(self.__dir + 'result/所有rid动态的疑似抽奖(polymer).csv'):
                last_df.to_csv(self.__dir + 'result/所有rid动态的疑似抽奖(polymer).csv', index=False, encoding='utf-8',
                               header=False,
                               mode='a+')
            else:
                last_df.to_csv(self.__dir + 'result/所有rid动态的疑似抽奖(polymer).csv', index=False, encoding='utf8',
                               header=True)


if __name__ == '__main__':
    extract_rid_lottery_dynamic().main()
