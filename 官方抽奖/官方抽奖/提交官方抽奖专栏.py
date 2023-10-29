import os.path
import time

import pandas
import re
import sys

sys.path.append('C:/pythontest/')

import json
import random

import requests
import urllib.parse

import datetime
import b站cookie.b站cookie_
import b站cookie.globalvar as gl


class generate_cv:
    def __init__(self, cookie, ua, csrf, buvid):
        self.csrf = csrf
        self.buvid = buvid
        self.ua = ua
        self.cookie = cookie
        self.s = requests.Session()
        self.username = ''
        self.uid = ''

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

    def file_remove_repeat_contents(self, filename):
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
                   'src="//article.biliimg.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png" ' \
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
        for lottery_end_date, lottery_data_str_list in zhuanlan_dict.items():
            selected_color_class_key = random.choice(list(color_dict.keys()))
            # lottery_id,business_id,sender_uid,status,lottery_time,lottery_at_num,first_prize,
            # second_prize,third_prize,first_prize_cmt,second_prize_cmt,third_prize_cmt,business_type,
            # lottery_result,updata_time
            ret += f'<h1 style="text-align: center;"><span class="{selected_color_class_key}"><strong><span style="text-decoration: none" class="font-size-23">'
            ret += str(lottery_end_date)
            ret += '</span></strong></span></h1>'
            ret += '<ol class=" list-paddingleft-2">'
            for i in lottery_data_str_list:
                ret += f'<li><p><span class="font-size-12">'
                if pandas.notna(i['business_id']):
                    ret += f'<a href="https://t.bilibili.com/{i["business_id"]}?tab=1">动态链接\t</a>'
                    ret += f'<a href="https://www.bilibili.com/opus/{i["business_id"]}">opus动态链接\t</a>'
                else:
                    ret += f'动态链接迷路了\t'
                ret += f'<a href="https://space.bilibili.com/{i["sender_uid"]}/dynamic">发布者空间\t</a>'

                ret += i['first_prize_cmt'] + ' * ' + i['first_prize'] + '\t'
                if pandas.notna(i['second_prize_cmt']):
                    ret += i['second_prize_cmt'] + ' * ' + i['second_prize'] + '\t'
                else:
                    ret += '\t'
                if pandas.notna(i['third_prize_cmt']):
                    ret += i['third_prize_cmt'] + ' * ' + i['third_prize'] + '\t'
                else:
                    ret += '\t'
                ret += i['etime_str']
                ret += '</span></p></li>'
            ret += '</ol>'
        return ret

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: list, limit_date_switch: bool = False,
                           limit_date: int = 10) -> dict:
        '''
        lottery_id,business_id,sender_uid,status,lottery_time,lottery_at_num,
        first_prize,second_prize,third_prize,first_prize_cmt,second_prize_cmt,
        third_prize_cmt,business_type,lottery_result,updata_time
        :param zhuanlan_data_order_by_date:专栏数据
        :param limit_date_switch:是否开启只提交n天之内的内容
        :param limit_date:限制的天数n
        :return:
        '''
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[抽奖文字1,抽奖文字2...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)
        for lottery_data in zhuanlan_data_order_by_date:
            lottery_end_date = datetime.datetime.strptime(lottery_data['lottery_time'], '%Y-%m-%d %H:%M:%S')
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            if int(time.mktime(time.strptime(lottery_data['lottery_time'], '%Y-%m-%d %H:%M:%S'))) < time.time():
                # 如果过期了进入下一条
                continue
            lottery_data.update({'etime_str': lottery_end_date.strftime('%m-%d %H:%M')})  # 修改原始时间格式
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                chongfu_Flag = False  # False表示没有重复
                for __ in oneDayList.get(str(lottery_end_date.date())):
                    if __.get('lottery_id') == lottery_data.get('lottery_id'):
                        chongfu_Flag = True
                if not chongfu_Flag:
                    oneDayList.get(str(lottery_end_date.date())).append(lottery_data)
            else:
                oneDayList.update({str(lottery_end_date.date()): [lottery_data]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}  # 去重
        for k, v in oneDayList.items():
            new_v = [dict(t) for t in set([tuple(d.items()) for d in v])]
            ret_List.update({k: sorted(new_v, key=lambda x: x['etime_str'])})  # 每一个日期里面的排序

        return ret_List

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        return sorted(zhuanlan_data, key=lambda x: x['lottery_time'])

    def sort_reserve_lottery(self, zhuanlan_data: [dict], up_dated_flag=False):
        '''
        官方抽奖数据分类
        lottery_id,business_id,sender_uid,status,lottery_time,lottery_at_num,
        first_prize,second_prize,third_prize,first_prize_cmt,second_prize_cmt,
        third_prize_cmt,business_type,lottery_result,updata_time

        :param up_dated_flag: 是否更新log
        :param zhuanlan_data:
        :return:
        '''
        invalid_reserve_list = []
        invalid_reserve_file_path = 'log/未知status的官方抽奖.csv'
        drawn_reserve_list = []
        drawn_reserve_file_path = 'log/开了的官方抽奖.csv'
        undrawn_reserve_list = []

        for reserve_data in zhuanlan_data:
            if str(reserve_data['status']) != '0' and str(reserve_data['status']) != '2':
                invalid_reserve_list.append(reserve_data)
            elif str(reserve_data['status']) == '2':
                drawn_reserve_list.append(reserve_data)
            else:
                undrawn_reserve_list.append(reserve_data)
        if up_dated_flag:
            self.pandas_file_writer(invalid_reserve_file_path, pandas.DataFrame(invalid_reserve_list), 'a+')  # 写入
            self.pandas_file_writer(drawn_reserve_file_path, pandas.DataFrame(drawn_reserve_list), 'a+')

            self.file_remove_repeat_contents(invalid_reserve_file_path)  # 去重
            self.file_remove_repeat_contents(drawn_reserve_file_path)

        return undrawn_reserve_list

    def pandas_file_writer(self, file_path, new_df, mode='w'):
        if not os.path.exists(file_path):
            mode = 'w'
        if mode == 'a+' or mode == 'a':
            old_df = pandas.read_csv(file_path, index_col=0, dtype=str)
            new_df = pandas.concat([old_df, new_df])
        new_df.to_csv(file_path, header=True, encoding='utf-8')

    def official_lottery(self):
        '''
        state含义：
            -100 ：失效
            150 ：已经开奖
            -110 ：也是开奖了的
            100 ：未开
            -300 ：已经失效
        :return:
        '''
        zhuanlan_data = pandas.read_csv('result/全部官方抽奖.csv', dtype=str).to_dict('records')
        zhuanlan_data = self.sort_reserve_lottery(zhuanlan_data, up_dated_flag=False)  # 排除开了的和失效的
        zhuanlan_data_list = self.zhuanlan_data_sort_by_date(zhuanlan_data)  # 按照时间排序
        zhuanlan_data = self.zhuanlan_date_sort(zhuanlan_data_list, limit_date_switch=False)
        article_content = self.zhuanlan_format(zhuanlan_data)

        zhuanlan_data1_list = None
        article_content1 = ''
        if os.path.getsize('result/更新的官方抽奖.csv'):
            zhuanlan_data1 = pandas.read_csv('result/更新的官方抽奖.csv', dtype=str).to_dict('records')
            zhuanlan_data1 = self.sort_reserve_lottery(zhuanlan_data1, up_dated_flag=True)  # 排除开了的和失效的
            zhuanlan_data1_list = self.zhuanlan_data_sort_by_date(zhuanlan_data1)  # 按照时间排序
            zhuanlan_data1 = self.zhuanlan_date_sort(zhuanlan_data1_list, limit_date_switch=False)
            article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1_list:
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
        # req = self.s.post(url='https://api.bilibili.com/x/article/creative/article/submit',
        #                   data=data,
        #                   headers=headers
        #                   )
        #
        # if req.json().get('code') == 0:
        #     print(req.text)
        #     return True
        # else:
        #     print(req.text, 'submit_cv')
        #     exit(req.text)
        return True


if __name__ == '__main__':
    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
    cookie3 = gl.get_value('cookie3')
    buvid3 = gl.get_value('buvid3_3')
    if cookie3 and csrf3 and ua3 and buvid3:
        gc = generate_cv(cookie3, ua3, csrf3, buvid3)
        gc.official_lottery()
    else:
        print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)
# -*- coding: utf-8 -*-
