# -*- coding: utf-8 -*-
import asyncio

import re

import json
from CONFIG import CONFIG
import pandas
import random
import datetime
import urllib.parse
import sys
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import os
import pandas as pd
import requests
import threading
import time
from loguru import logger
from utl.代理 import grpc_api
from grpc获取动态.src.DynObjectClass import dynAllDetail
from grpc获取动态.src.SqlHelper import SQLHelper, sql_log
from utl.代理.request_with_proxy import request_with_proxy


class lot_detail:
    """
    抽奖信息详情
    """

    def __init__(self, lottery_id, dynamic_id, lottery_time, first_prize, second_prize,
                 third_prize, first_prize_cmt, second_prize_cmt, third_prize_cmt, participants):
        self.lottery_id: int = lottery_id
        self.dynamic_id: str = dynamic_id
        self.lottery_time: int = lottery_time  # 时间戳
        self.first_prize: int = first_prize  # 一等奖人数
        self.second_prize: int = second_prize  # 二等奖人数
        self.third_prize: int = third_prize  # 三等奖人数
        self.first_prize_cmt: str = first_prize_cmt  # 奖品描述
        self.second_prize_cmt: str = second_prize_cmt
        self.third_prize_cmt: str = third_prize_cmt
        self.participants: int = participants  # 参加人数
        chance_number: int = 100 if int(participants) <= (
                int(first_prize) + int(second_prize) + int(third_prize)) else (
                                                                                      int(first_prize) + int(
                                                                                  second_prize) + int(
                                                                                  third_prize)) / int(
            participants) * 100
        self.chance: str = "%.2f%%" % chance_number


class generate_cv:
    def __init__(self, cookie, ua, csrf, buvid):
        self.csrf = csrf
        self.buvid = buvid
        self.ua = ua
        self.cookie = cookie
        self.s = requests.Session()
        self.username = ''
        self.uid = ''
        self.post_flag = True  # 是否直接发布

        def login_check(_cookie, _ua):
            headers = {
                'User-Agent': _ua,
                'cookie': _cookie
            }
            url = 'https://api.bilibili.com/x/web-interface/nav'
            res = requests.get(url=url, headers=headers).json()
            if res['data']['isLogin'] == True:
                self.username = res['data']['uname']
                self.uid = res['data']['mid']
                print(f'登录成功,当前账号用户名为{self.username}\tuid:{self.uid}')
                return 1
            else:
                print('登陆失败,请重新登录')
                sys.exit('登陆失败,请重新登录')

        login_check(self.cookie, self.ua)

    def judge_lottery_time(self, Date_str):
        '''
        过期了返回True,没过期返回False
        :param Date_str: %Y-%m-%d %H:%M:%S 格式的日期
        :return: bool: 是否过期
        '''
        # today = datetime.datetime.today()
        # next_day = today + datetime.timedelta(days=1)
        lottery_end_date = datetime.datetime.strptime(Date_str, '%Y-%m-%d %H:%M:%S')
        return lottery_end_date < datetime.datetime.now()  # 如果比当前时间大，返回True

    def zhuanlan_format(self, zhuanlan_dict: dict, blank_space: int = 0) -> str:
        """

        :param zhuanlan_dict:
        :param blank_space: 开头空几行
        :return:
        """
        ret = ''
        for _ in range(blank_space):
            ret += '<p><br></p><figure class="img-box focused" contenteditable="false"><img ' \
                   'src="//i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png" ' \
                   'class="cut-off-6"></figure> '

        color_dict = {
            'color-purple-01': 'rgb(255, 160, 208)',
            'color-purple-02': 'rgb(234, 0, 119)',
            'color-purple-03': 'rgb(203, 41, 122)',
            'color-purple-04': 'rgb(153, 25, 94)',
            'color-blue-01': 'rgb(137, 212, 255)',
            'color-blue-02': 'rgb(11, 132, 237)',
            'color-blue-03': 'rgb(1, 118, 186)',
            'color-blue-04': 'rgb(0, 78, 128)',
            'color-lblue-02': 'rgb(24, 231, 207)',
            'color-lblue-03': 'rgb(6, 143, 134)',
            'color-lblue-04': 'rgb(1, 124, 118)',
            'color-pink-01': 'rgb(255, 150, 141)',
            'color-pink-02': 'rgb(255, 101, 78)',
            'color-pink-03': 'rgb(238, 35, 13)',
            'color-pink-04': 'rgb(180, 23, 0)',
            'color-yellow-04': 'rgb(255, 146, 1)',
            'color-green-03': 'rgb(29, 177, 0)',
            'color-green-04': 'rgb(1, 112, 1)',
        }  # 颜色代码

        for lottery_end_date, __lot_detail_list in zhuanlan_dict.items():
            selected_color_class_key = random.choice(list(color_dict.keys()))
            # 'code', 'message', 'ttl', 'sid', 'name', 'total', 'stime', 'etime',
            # 'isFollow', 'state', 'oid', 'type', 'upmid', 'reserveRecordCtime',
            # 'livePlanStartTime', 'upActVisible', 'lotteryType', 'text', 'jumpUrl',
            # 'dynamicId', 'reserveTotalShowLimit', 'desc', 'start_show_time', 'hide',
            # 'subType', 'productIdPrice', 'ids', 'reserve_products' , 'etime_str'
            ret += f'<h1 style="text-align: center;"><span class="{selected_color_class_key}"><strong><span style="text-decoration: none" class="font-size-23">'
            ret += str(lottery_end_date)
            ret += '</span></strong></span></h1>'
            ret += '<ol class=" list-paddingleft-2">'
            for __lot_detail in __lot_detail_list:
                ret += f'<li><p><span class="font-size-12">'
                if __lot_detail.dynamic_id:
                    ret += f'<a href="https://t.bilibili.com/{__lot_detail.dynamic_id}?tab=1">动态链接\t</a>'
                    ret += f'<a href="https://www.bilibili.com/opus/{__lot_detail.dynamic_id}">opus链接\t</a>'
                else:
                    ret += f'链接迷路了喵\t'
                # ret += f'<a href="https://space.bilibili.com/{__lot_detail["upmid"]}/dynamic">发布者空间\t</a>'
                ret += str(__lot_detail.first_prize_cmt) + ' * ' + str(__lot_detail.first_prize) + '\t'
                if __lot_detail.second_prize_cmt:
                    ret += str(__lot_detail.second_prize_cmt) + ' * ' + str(__lot_detail.second_prize) + '\t'
                if __lot_detail.third_prize_cmt:
                    ret += str(__lot_detail.third_prize_cmt) + ' * ' + str(__lot_detail.third_prize) + '\t'
                ret += f'概率:{__lot_detail.chance}\t'
                ret += __lot_detail.__dict__.get('etime_str')
                ret += '</span></p></li>'
            ret += '</ol>'
        return ret

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: [lot_detail], limit_date_switch: bool = False,
                           limit_date: int = 10) -> dict:
        '''
        为字典添加了etime_str的日期文字格式
        :param zhuanlan_data_order_by_date: 必须将这个数据按照日期排序先
        :param limit_date_switch:
        :param limit_date:
        :return: {'日期':[lot_detail...]}
        '''
        zhuanlan_data_order_by_date.sort(key=lambda x: x.lottery_time)
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[lot_detail...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)
        for lottery_data in zhuanlan_data_order_by_date:
            lottery_end_date = datetime.datetime.strptime(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(lottery_data.lottery_time))), '%Y-%m-%d %H:%M:%S')
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            if int(lottery_data.lottery_time) < time.time():
                # 如果过期了进入下一条
                continue
            lottery_data.__dict__.update({'etime_str': lottery_end_date.strftime('%m-%d %H:%M')})  # 修改原始时间格式
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                chongfu_Flag = False  # False表示没有重复
                for __ in oneDayList.get(str(lottery_end_date.date())):
                    if __.dynamic_id == lottery_data.dynamic_id:
                        chongfu_Flag = True
                if not chongfu_Flag:
                    oneDayList.get(str(lottery_end_date.date())).append(lottery_data)
            else:
                oneDayList.update({str(lottery_end_date.date()): [lottery_data]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}  # 去重
        for k, v in oneDayList.items():  # {'日期':[lot_detail...]}
            ret_List.update({k: sorted(v, key=lambda x: x.lottery_time)})  # 每一个日期里面的排序
        return ret_List

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        return sorted(zhuanlan_data, key=lambda x: x['etime'])

    def pandas_file_writer(self, file_path, new_df, mode='w', sep='滹'):
        if not os.path.exists(file_path):
            mode = 'w'
        if mode == 'a+' or mode == 'a':
            old_df = pandas.read_csv(file_path, index_col=0, dtype=str, sep=sep)
            new_df = pandas.concat([old_df, new_df])
        new_df.to_csv(file_path, header=True, encoding='utf-8', sep=sep)

    def official_lottery(self, all_official_lot_detail: [lot_detail], latest_official_lot_detail: [lot_detail]):
        '''
        :return:
        '''
        all_official_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data = self.zhuanlan_date_sort(all_official_lot_detail)
        article_content = self.zhuanlan_format(zhuanlan_data)

        latest_official_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data1 = self.zhuanlan_date_sort(latest_official_lot_detail)
        article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的官方抽奖'
        article_content = article_content + split_article_content + article_content1
        banner_url = ''
        summary = ''.join(re.findall('>(.*?)<', article_content)).replace(' ', '').replace('\t', ' ')[0:500]
        words = len(
            ''.join(re.findall('>(.*?)<', article_content)).replace(' ', '').replace('\t', '').replace('\n', ''))
        category = 0
        list_id = 0
        tid = 5
        reprint = 0
        tags = ''
        image_urls = ''
        origin_image_urls = ''
        dynamic_intro = ''
        media_id = ''
        spoiler = ''
        original = 0
        top_video_bvid = ''

        aid = self.get_cv_aid(title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                              image_urls,
                              origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, self.csrf)
        up_reply_closed = 0
        comment_selected = 0
        publish_time = 0
        items = ''
        platform = 'web'
        buvid = self.buvid
        device = ''
        build = ''
        mobi_app = ''
        csrf = self.csrf
        self.submit_cv(title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                       image_urls,
                       origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, aid,
                       up_reply_closed, comment_selected,
                       publish_time, items, platform, buvid, device, build, mobi_app, csrf)

    def charge_lottery(self, all_charge_lot_detail: [lot_detail], latest_charge_lot_detail: [lot_detail]):
        '''
        :return:
        '''
        all_charge_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data = self.zhuanlan_date_sort(all_charge_lot_detail)
        article_content = self.zhuanlan_format(zhuanlan_data)

        latest_charge_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data1 = self.zhuanlan_date_sort(latest_charge_lot_detail)
        article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的充电抽奖'
        article_content = article_content + split_article_content + article_content1
        banner_url = ''
        summary = ''.join(re.findall('>(.*?)<', article_content)).replace(' ', '').replace('\t', ' ')[0:500]
        words = len(
            ''.join(re.findall('>(.*?)<', article_content)).replace(' ', '').replace('\t', '').replace('\n', ''))
        category = 0
        list_id = 0
        tid = 5
        reprint = 0
        tags = ''
        image_urls = ''
        origin_image_urls = ''
        dynamic_intro = ''
        media_id = ''
        spoiler = ''
        original = 0
        top_video_bvid = ''

        aid = self.get_cv_aid(title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                              image_urls,
                              origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, self.csrf)
        up_reply_closed = 0
        comment_selected = 0
        publish_time = 0
        items = ''
        platform = 'web'
        buvid = self.buvid
        device = ''
        build = ''
        mobi_app = ''
        csrf = self.csrf
        self.submit_cv(title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                       image_urls,
                       origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, aid,
                       up_reply_closed, comment_selected,
                       publish_time, items, platform, buvid, device, build, mobi_app, csrf)

    def get_cv_aid(self, title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                   image_urls,
                   origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, csrf):
        url = 'https://api.bilibili.com/x/article/creative/draft/addupdate'
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.cookie,
            'origin': 'https://member.bilibili.com',
            'referer': 'https://member.bilibili.com/',
            'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': self.ua,
        }
        data = {
            'title': title,
            'banner_url': banner_url,
            'content': article_content,
            'summary': summary,
            'words': words,
            'category': category,
            'list_id': list_id,
            'tid': tid,
            'reprint': reprint,
            'tags': tags,
            'image_urls': image_urls,
            'origin_image_urls': origin_image_urls,
            'dynamic_intro': dynamic_intro,
            'media_id': media_id,
            'spoiler': spoiler,
            'original': original,
            'top_video_bvid': top_video_bvid,
            'csrf': csrf
        }
        data = urllib.parse.urlencode(data)
        req = self.s.post(url=url,
                          data=data,
                          headers=headers
                          )
        print(req.text)
        if req.json().get('code') == 0:
            return req.json().get('data').get('aid')
        else:
            print(req.text, 'get_cv_aid')
            exit(req.text)

    def submit_cv(self, title, banner_url, article_content, summary, words, category, list_id, tid, reprint, tags,
                  image_urls,
                  origin_image_urls, dynamic_intro, media_id, spoiler, original, top_video_bvid, aid, up_reply_closed,
                  comment_selected, publish_time, items, platform, buvid, device, build, mobi_app, csrf):
        data = {
            'title': title,
            'banner_url': banner_url,
            'content': article_content,
            'summary': summary,
            'words': words,
            'category': category,
            'list_id': list_id,
            'tid': tid,
            'reprint': reprint,
            'tags': tags,
            'image_urls': image_urls,
            'origin_image_urls': origin_image_urls,
            'dynamic_intro': dynamic_intro,
            'media_id': media_id,
            'spoiler': spoiler,
            'original': original,
            'top_video_bvid': top_video_bvid,
            'aid': aid,
            'up_reply_closed': up_reply_closed,
            'comment_selected': comment_selected,
            'publish_time': publish_time,
            'items': items,
            'platform': platform,
            'buvid': buvid,
            'device': device,
            'build': build,
            'mobi_app': mobi_app,
            'csrf': csrf
        }
        data = urllib.parse.urlencode(data)
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.cookie,
            'origin': 'https://member.bilibili.com',
            'referer': 'https://member.bilibili.com/',
            'sec-ch-ua': '\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '\"Windows\"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': self.ua,
        }
        if self.post_flag:
            req = self.s.post(url='https://api.bilibili.com/x/article/creative/article/submit',
                              data=data,
                              headers=headers
                              )

            if req.json().get('code') == 0:
                print(req.text)
                return True
            else:
                print(req.text, 'submit_cv')
                exit(req.text)
        return True


class LOTSqlHelper(SQLHelper):
    """
    获取抽奖信息用的sql，继承自grpc的SQLHelper
    """

    def __init__(self):
        super().__init__()

    @sql_log.catch
    def get_official_and_charge_lot_not_drawn(self) -> [dict]:
        ret_list_dict = [row for row in
                         self.op_lot_table.rows_where(
                             where='lottery_result is Null and status=0 and business_type!=10',
                             order_by='lottery_id'
                         )]
        return ret_list_dict

class exctract_official_lottery:
    def __init__(self):
        self.BiliGrpc = grpc_api.BiliGrpc()
        self.__dir = CONFIG.root_dir + 'opus新版官方抽奖/转发抽奖/'
        if not os.path.exists('log'):
            os.mkdir('log')
        if not os.path.exists('result'):
            os.mkdir('result')
        self.oringinal_official_lots: [dict] = []

        self.all_offcial_lots: [dict] = []  # 所有的抽奖
        self.last_update_offcial_lots: [dict] = []  # 最后一次更新的抽奖
        self.list_append_lock = threading.Lock()
        self.csv_sep_letter = '\t\t\t\t\t'

        self.stop_flag = False
        self.stop_flag_lock = threading.Lock()

        self.sql = LOTSqlHelper()
        self.proxy_request = request_with_proxy()
        self.common_log = logger.bind(user=__name__+"common_log")
        # self.common_log_handle = logger.add(sys.stderr, level="INFO",
        #                                         filter=lambda record: record["extra"].get('user') == __name__+ "common_log")
        self.error_log = logger.bind(user="error_log")
        # self.error_log_handler1 = logger.add(sys.stderr, level="INFO",
        #                                         filter=lambda record: record["extra"].get('user') == __name__ + "error_log")
        # self.error_log_handler2 =logger.add(
        #     "log/error_log.log",
        #     encoding="utf-8",
        #     enqueue=True,
        #     rotation="500MB",
        #     compression="zip",
        #     retention="15 days",
        #     filter=lambda record: record["extra"].get('user') == "error_log"
        # )
        self.__no_lot_timer = 0
        self.__no_lot_timer_lock = threading.Lock()
        self.limit_no_lot_times = 3000  # 3000个rid没有得到抽奖信息就退出
        self.limit_lot_ts = 3 * 3600  # 只获取到离当前时间3个小时前的抽奖
        self.set_latest_lot_time_lock = threading.Lock()
        self.latest_lot_time = 0
        self.latest_rid = 0

        self.comm_headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0",
        }

    def _get_dynamic_created_ts_by_dynamic_id(self, dynamic_id) -> int:
        return int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def write_in_file(self):
        if self.all_offcial_lots:
            df1 = pd.DataFrame(self.all_offcial_lots)
            if os.path.isfile('/result/全部转发抽奖.csv'):
                df1.to_csv('/result/全部转发抽奖.csv', index=False, sep=self.csv_sep_letter)
            else:
                df1.to_csv('/result/全部转发抽奖.csv', index=False, mode='a+', header=False, sep=self.csv_sep_letter)

        if self.last_update_offcial_lots:
            df2 = pd.DataFrame(self.last_update_offcial_lots)
            df2.to_csv('/result/更新的转发抽奖.csv', index=False, sep=self.csv_sep_letter)

        with open('idsstart.txt', 'w', encoding='utf-8') as f:
            f.write(str(self.latest_rid))

    async def get_lot_notice(self, bussiness_type: int, business_id: str):
        """
        获取抽奖notice
        :param bussiness_type:
        :param business_id:
        :return:
        """
        while 1:
            url = 'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice'
            params = {
                'business_type': bussiness_type,
                'business_id': business_id,
            }
            resp = await self.proxy_request.request_with_proxy(url=url, method='get', params=params,
                                                               headers={'user-agent': random.choice(CONFIG.UA_LIST)})
            if resp.get('code') != 0:
                self.error_log.error(f'get_lot_notice Error:\t{resp}\t{bussiness_type, business_id}')
                time.sleep(10)
                if resp.get('code') == -9999:
                    return resp
                continue
            return resp

    async def update_lot_notice(self, original_lot_notice: [dict]) -> [dict]:
        """
        更新抽奖
        :param original_lot_notice:
        :return: 更新抽奖
        """

        async def solve_lot_data(lotData):
            """

            :param lotData:
            """
            newly_lot_resp = await self.get_lot_notice(lotData['business_type'], lotData['business_id'])
            newly_lotData = newly_lot_resp['data']

            if newly_lotData:
                await self.proxy_request.upsert_lot_detail(newly_lotData)

            async with data_lock:
                newly_updated_lot_data.append(newly_lotData)

        self.common_log.info(f'开始更新抽奖，共计{len(original_lot_notice)}条抽奖需要更新')
        data_lock = asyncio.Lock()
        newly_updated_lot_data = []
        thread_num = 50
        task_list = []
        for idx in range(len(original_lot_notice) // thread_num + 1):
            task_data = original_lot_notice[idx * thread_num:(idx + 1) * thread_num]
            for da in task_data:
                task = solve_lot_data(da)
                task_list.append(task)
        await asyncio.gather(*task_list)

        return newly_updated_lot_data

    async def get_lot_dict(self, all_lots: [lot_detail]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
        """
        获取最新的抽奖的dict，这个函数没有问题
        :param all_lots:数据库的抽奖信息
        :return: 所有官方抽奖，最后更新的官方抽奖 , 所有充电抽奖,最后更新的充电抽奖
        """
        update_lots_lot_ids = [int(x['lottery_id']) for x in all_lots if (int(time.time()) - int(x['ts'])) <= 20 * 3600] # 24小时之内更新进去的都算？
        # 获取到的更新抽奖的lot_id
        if len(update_lots_lot_ids) == len(all_lots):
            update_lots_lot_ids = []

        freshed_all_lot_datas = await self.update_lot_notice(all_lots)  # 更新抽奖

        self.common_log.info(f'更新完成，当前抽奖剩余{len(freshed_all_lot_datas)}条')
        all_lot_official_data = [x for x in freshed_all_lot_datas if
                                 x['status'] != 2 and x['status'] != -1 and x['business_type'] == 1]
        latest_updated_official_lot_data = [x for x in all_lot_official_data if
                                            int(x['lottery_id']) in update_lots_lot_ids]

        all_lot_charge_data = [x for x in freshed_all_lot_datas if
                               x['status'] != 2 and x['status'] != -1 and x['business_type'] == 12]
        latest_updated_charge_lot_data = [x for x in all_lot_charge_data if int(x['lottery_id']) in update_lots_lot_ids]

        df1 = pd.DataFrame(all_lot_official_data)
        df1.to_csv('log/全部官抽.csv', index=False, header=True)
        df2 = pd.DataFrame(latest_updated_official_lot_data)
        df2.to_csv('log/更新官抽.csv', index=False, header=True)
        df3 = pd.DataFrame(all_lot_charge_data)
        df3.to_csv('log/全部充电.csv', index=False, header=True)
        df4 = pd.DataFrame(latest_updated_charge_lot_data)
        df4.to_csv('log/更新充电.csv', index=False, header=True)

        return all_lot_official_data, latest_updated_official_lot_data, all_lot_charge_data, latest_updated_charge_lot_data

    async def resolve_dynamic_details_card(self, dynData):
        temp_rid = dynData.get('extend').get('businessId')
        dynamic_id = dynData.get('extend').get('dynIdStr')
        dynamic_calculated_ts = int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)
        dynamic_created_time = self._timeshift(dynamic_calculated_ts)  # 通过公式获取大致的时间，误差大概20秒左右
        moduels = dynData.get('modules')
        lot_id = None
        if dynData.get('extend').get('origDesc'):
            for descNode in dynData.get('extend').get('origDesc'):
                if descNode.get('type') == 'desc_type_lottery':
                    lot_id = descNode.get('rid')
                    lot_rid = dynData.get('extend').get('businessId')
                    lot_notice_res = await self.get_lot_notice(2, lot_rid)
                    lot_data = lot_notice_res.get('data')
                    if lot_data:
                        lot_id = lot_data.get('lottery_id')
        return temp_rid, lot_id, dynamic_id, dynamic_created_time

    def get_repost_count(self, dynamic_id):
        dynDetail = self.sql.get_all_dynamic_detail_by_dynamic_id(dynamic_id)
        dynData = json.loads(dynDetail.get('dynData'), strict=False)
        repost_count = 0
        for module in dynData.get('modules'):
            if module.get('moduleType') == 'module_stat':
                if module.get('moduleStat').get('repost'):
                    repost_count = module.get('moduleStat').get('repost')
            if module.get('moduleButtom'):
                if module.get('moduleButtom').get('moduleStat'):
                    if module.get('moduleButtom').get('moduleStat').get('repost'):
                        repost_count = module.get('moduleButtom').get('moduleStat').get('repost')
        return repost_count

    def construct_lot_detail(self, lot_data_list: [dict], get_repost_count_flag: bool) -> list[lot_detail]:
        ret_list = []
        for lot_data in lot_data_list:
            self.common_log.info(f'Constructing:{lot_data}')
            lottery_id = lot_data['lottery_id']
            dynamic_id = lot_data.get('dynamic_id') or lot_data.get('business_id')
            lottery_time = lot_data['lottery_time']
            first_prize = lot_data['first_prize']
            second_prize = lot_data['second_prize']
            third_prize = lot_data['third_prize']
            first_prize_cmt = lot_data['first_prize_cmt']
            second_prize_cmt = lot_data['second_prize_cmt']
            third_prize_cmt = lot_data['third_prize_cmt']
            if get_repost_count_flag:
                participants = self.get_repost_count(dynamic_id)
            else:
                participants = lot_data['participants']
            result = lot_detail(
                lottery_id,
                dynamic_id,
                lottery_time,
                first_prize,
                second_prize,
                third_prize,
                first_prize_cmt,
                second_prize_cmt,
                third_prize_cmt,
                participants
            )
            ret_list.append(result)
        return ret_list

    async def get_and_update_all_details_by_dynamic_id_list(self, all_dynamic_ids: [int]):
        async def thread_get_details(dynamic_ids):
            """
            需要放进thread里面跑
            :param dynamic_ids:
            :return:
            """
            ret_dict_list = []
            resp_list = await self.BiliGrpc.grpc_api_get_DynDetails(dynamic_ids)
            if resp_list.get('list'):
                for resp_data in resp_list['list']:
                    temp_rid, lot_id, dynamic_id, dynamic_created_time = self.resolve_dynamic_details_card(
                        resp_data)
                    tempdetail_dict = dynAllDetail(
                        rid=temp_rid,
                        dynamic_id=dynamic_id,
                        dynData=resp_data,
                        lot_id=lot_id if lot_id else None,
                        dynamic_created_time=dynamic_created_time
                    )
                    ret_dict_list.append(tempdetail_dict.__dict__)
            for detail in ret_dict_list:
                self.sql.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                          dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                          dynamic_created_time=detail.get('dynamic_created_time'))

        task_args_list = []  # [[1,2,3,4,5,6,7,8],[9,10,11,12,13,14,15],...]
        offset = 10
        for rid_index in range(len(all_dynamic_ids) // offset + 1):
            rids_list = all_dynamic_ids[offset * rid_index:offset * (rid_index + 1)]
            task_args_list.append(rids_list)

        thread_num = 50
        task_list = []
        for task_index in range(len(task_args_list) // thread_num + 1):
            args_list = task_args_list[
                        thread_num * task_index:thread_num * (task_index + 1)]  # 将task切片成[[0...49],[50....99]]
            print(f'args_list:{args_list}')
            for args in args_list:
                print(args)
                if not args[0]:
                    continue
                task = asyncio.create_task(thread_get_details(args))
                task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_all_lots(self) -> tuple[[lot_detail], [lot_detail], [lot_detail], [lot_detail]]:
        """
        已经排除了开奖了的和失效了的抽奖了
        :return: 所有官方抽奖，最后更新的官方抽奖 , 所有充电抽奖,最后更新的充电抽奖
        """
        all_official_lots_undrawn = self.sql.get_official_and_charge_lot_not_drawn()
        all_lot_official_data, latest_updated_official_lot_data, all_lot_charge_data, latest_updated_charge_lot_data = await self.get_lot_dict(
            all_official_lots_undrawn)  # 更新抽奖信息
        official_lot_dynamic_ids = [x['business_id'] for x in all_lot_official_data if x['status'] != 2]
        charge_lot_dynamic_ids = [x['business_id'] for x in all_lot_charge_data if x['status'] != 2]
        await self.get_and_update_all_details_by_dynamic_id_list(
            [official_lot_dynamic_ids.extend(charge_lot_dynamic_ids)])  # 更新抽奖的动态

        all_official_lot_detail_result: list[lot_detail] = self.construct_lot_detail(all_lot_official_data, True)
        all_official_lot_detail: list[lot_detail] = [x for x in all_official_lot_detail_result]
        latest_official_lot_dynamic_ids = [x['business_id'] for x in latest_updated_official_lot_data]
        latest_official_lot_detail: list[lot_detail] = [x for x in all_official_lot_detail if
                                                        x.dynamic_id in latest_official_lot_dynamic_ids]

        all_charge_lot_detail: list[lot_detail] = self.construct_lot_detail(all_lot_charge_data, False)
        latest_charge_lot_dynamic_ids = [x['business_id'] for x in latest_updated_charge_lot_data]
        latest_charge_lot_detail: list[lot_detail] = [x for x in all_charge_lot_detail if
                                                      x.dynamic_id in latest_charge_lot_dynamic_ids]

        return all_official_lot_detail, latest_official_lot_detail, all_charge_lot_detail, latest_charge_lot_detail


    async def main(self):
        """
        函数入口
        """
        # from grpc获取动态.src.getDynDetail import dynDetailScrapy
        # d = dynDetailScrapy()
        # d.main()# 爬取最新的动态

        all_official_lot_detail, latest_official_lot_detail, all_charge_lot_detail, latest_charge_lot_detail = await self.get_all_lots()  # 获取并更新抽奖信息！

        ua3 = gl.get_value('ua3')
        csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
        cookie3 = gl.get_value('cookie3')
        buvid3 = gl.get_value('buvid3_3')
        if cookie3 and csrf3 and ua3 and buvid3:
            gc = generate_cv(cookie3, ua3, csrf3, buvid3)
            # gc.post_flag = False  # 不直接发布
            gc.official_lottery(all_official_lot_detail, latest_official_lot_detail)  # 官方抽奖
            gc.charge_lottery(all_charge_lot_detail, latest_charge_lot_detail)  # 充电抽奖
        else:
            print('获取登陆信息失败！', cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)


if __name__ == '__main__':
    m = exctract_official_lottery()
    # m.Get_All_Flag = True  # 为True时重新获取所有的抽奖，为False时将更新的内容附加在所有的后面
    asyncio.run(m.main())
