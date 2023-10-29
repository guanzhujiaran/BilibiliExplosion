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

    def judge_lottery_time(self, Date_str):
        '''
        :param Date_str:
        :return: [bool:是否过期 , 日期格式]
        '''
        # today = datetime.datetime.today()
        # next_day = today + datetime.timedelta(days=1)
        lottery_end_date = datetime.datetime.strptime(Date_str, '%Y-%m-%d %H:%M:%S')
        return [lottery_end_date >= datetime.datetime.now(), lottery_end_date]  # 如果比当前时间大，返回True

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

            ret += f'<h1 style="text-align: center;"><span class="{selected_color_class_key}"><strong><span style="text-decoration: none" class="font-size-23">'
            ret += str(lottery_end_date)
            ret += '</span></strong></span></h1>'
            ret += '<ol class=" list-paddingleft-2">'
            for i in lottery_data_str_list:
                ret += f'<li><p><span class="font-size-12">'
                for split_content in i.split('\t'):
                    if 'https://t.bilibili.com' in split_content:
                        ret += f'<a href="{split_content.replace("https:", "")}">动态链接\t</a>'
                    elif 'https://space.bilibili.com' in split_content:
                        ret += f'<a href="{split_content.replace("https:", "")}">发布者空间\t</a>'
                    elif split_content != i.split('\t')[-1]:
                        ret += split_content + '\t'
                    else:
                        ret += split_content
                ret += '</span></p></li>'
            ret += '</ol>'
        return ret

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: list, limit_date_switch: bool = False,
                           limit_date: int = 10) -> dict:
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[抽奖文字1,抽奖文字2...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)
        for lottery_data in zhuanlan_data_order_by_date:
            time_index = 4
            try:
                lottery_end_date = datetime.datetime.strptime(lottery_data[5], '%Y-%m-%d %H:%M:%S')
                time_index = 5
            except:
                lottery_end_date = datetime.datetime.strptime(lottery_data[4], '%Y-%m-%d %H:%M:%S')
                time_index = 4
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            lottery_data[time_index] = lottery_end_date.strftime('%m-%d %H:%M')  # 修改原始时间格式
            lottery_data_str = '\t'.join(lottery_data)
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                oneDayList.get(str(lottery_end_date.date())).append(lottery_data_str)
            else:
                oneDayList.update({str(lottery_end_date.date()): [lottery_data_str]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}  # 去重
        for k, v in oneDayList.items():
            time_index = 4
            try:
                datetime.datetime.strptime(v[0].split('\t')[5], '%m-%d %H:%M')
                time_index = 5
            except:
                time_index = 4
            ret_List.update({k: sorted(list(set(v)), key=lambda x: x.split('\t')[time_index])}) #每一个日期里面的排序

        return ret_List

    def zhuanlan_data_sort_by_date(self,zhuanlan_data:list)-> list:
        '''
        将所有专栏抽奖数据按日期排序
        :return:
        '''
        time_index = 4
        try:
            datetime.datetime.strptime(zhuanlan_data[0][5], '%Y-%m-%d %H:%M:%S')
            time_index = 5
        except:
            time_index = 4
        return sorted(zhuanlan_data, key=lambda x: x[time_index])
    def charge_lottery(self):
        zhuanlan_data = []
        with open('充电抽奖.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data.append((dat[3:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data_list = self.zhuanlan_data_sort_by_date(zhuanlan_data)  # 按照时间排序
        zhuanlan_data = self.zhuanlan_date_sort(zhuanlan_data_list, True, 10)
        article_content = self.zhuanlan_format(zhuanlan_data)

        zhuanlan_data1 = []
        with open('充电抽奖更新内容.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data1.append((dat[3:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data1_list = self.zhuanlan_data_sort_by_date(zhuanlan_data1)   # 按照时间排序
        zhuanlan_data1 = self.zhuanlan_date_sort(zhuanlan_data1_list)
        article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1_list:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的充电抽奖（10天之内）'
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

    def official_lottery(self):
        zhuanlan_data = []
        with open('官方抽奖.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data.append((dat[3:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data_list = self.zhuanlan_data_sort_by_date(zhuanlan_data)  # 按照时间排序
        zhuanlan_data = self.zhuanlan_date_sort(zhuanlan_data_list, True, 10)
        article_content = self.zhuanlan_format(zhuanlan_data)

        zhuanlan_data1 = []
        with open('官方抽奖更新内容.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data1.append((dat[3:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data1_list = self.zhuanlan_data_sort_by_date(zhuanlan_data1)  # 按照时间排序
        zhuanlan_data1 = self.zhuanlan_date_sort(zhuanlan_data1_list)
        article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1_list:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的官方抽奖（10天之内）'
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

    def reserve_lottery(self):
        zhuanlan_data = []
        with open('预约抽奖.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data.append((dat[4:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data_list = self.zhuanlan_data_sort_by_date(zhuanlan_data)  # 按照时间排序
        zhuanlan_data = self.zhuanlan_date_sort(zhuanlan_data_list)
        article_content = self.zhuanlan_format(zhuanlan_data)

        zhuanlan_data1 = []
        with open('预约抽奖更新内容.csv', 'r', encoding='utf-8') as f:
            for i in f.readlines():
                dat = i.split('\t')
                try:
                    if not 'inf' in dat[10]:
                        dateJudge = self.judge_lottery_time(dat[8])
                        if dateJudge[0]:
                            zhuanlan_data1.append((dat[4:9]))
                except:
                    print(dat, 'zhuanlan_data')
                    continue
        zhuanlan_data1_list = self.zhuanlan_data_sort_by_date(zhuanlan_data1) # 按照时间排序
        zhuanlan_data1 = self.zhuanlan_date_sort(zhuanlan_data1_list)
        article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1_list:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的预约抽奖'
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


if __name__ == '__main__':
    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
    cookie3 = gl.get_value('cookie3')
    buvid3 = gl.get_value('buvid3_3')
    if cookie3 and csrf3 and ua3 and buvid3:
        gc = generate_cv(cookie3, ua3, csrf3, buvid3)
        gc.charge_lottery()
        gc.official_lottery()
        gc.reserve_lottery()
    else:
        print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)
