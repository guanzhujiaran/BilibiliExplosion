import asyncio
import os.path
from typing import Dict
import time
import pandas
import re
import sys

from opus新版官方抽奖.Base.generate_cv import GenerateCvBase
from opus新版官方抽奖.预约抽奖.db.models import TUpReserveRelationInfo
from opus新版官方抽奖.预约抽奖.db.sqlHelper import SqlHelper

sys.path.append('C:/pythontest/')
import random
import requests
import urllib.parse
import datetime
import b站cookie.b站cookie_
import b站cookie.globalvar as gl


class GenerateReserveLotCv(GenerateCvBase):
    def __init__(self, cookie, ua, csrf, buvid):
        super().__init__(cookie, ua, csrf, buvid)
        self.target_timeformat = '%m-%d %H:%M'  # 专栏的最终时间格式
        self.post_flag = True  # 是否直接发布
        self.sqlhelper = SqlHelper()

    def zhuanlan_format(self, zhuanlan_dict: Dict[str, list[TUpReserveRelationInfo]], blank_space: int = 0) -> str:
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
        for lottery_end_date, reserve_info_list in zhuanlan_dict.items():
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
            for i in reserve_info_list:
                ret += f'<li><p><span class="font-size-12">'
                if pandas.notna(i.dynamicId):
                    ret += f'<a href="https://t.bilibili.com/{i.dynamicId}?tab=2">动态链接\t</a>'
                else:
                    ret += f'链接迷路了喵\t'
                ret += f'<a href="https://space.bilibili.com/{i.upmid}/dynamic">发布者空间\t</a>'
                ret += i.text[5:] + '\t'
                ret += datetime.datetime.fromtimestamp(i.etime).strftime(self.target_timeformat)
                ret += '</span></p></li>'
            ret += '</ol>'
        return ret

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: list[TUpReserveRelationInfo],
                           limit_date_switch: bool = False,
                           limit_date: int = 10) -> Dict[str, list[TUpReserveRelationInfo]]:
        '''
        为字典添加了etime_str的日期文字格式
        :param zhuanlan_data_order_by_date:
        :param limit_date_switch:
        :param limit_date:
        :return:
        '''
        oneDayList = {}  # 放入同一天的抽奖内容{'日期':[抽奖文字1,抽奖文字2...]}
        today = datetime.datetime.today()
        next_day = today + datetime.timedelta(days=1)

        for reserve_info in zhuanlan_data_order_by_date:
            lottery_end_date = datetime.datetime.strptime(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(reserve_info.etime))), '%Y-%m-%d %H:%M:%S')
            only_date = lottery_end_date.date()
            if limit_date_switch:
                if (only_date - next_day.date()).days > limit_date:  # 大于指定天数的抽奖不放进去
                    continue
            if int(reserve_info.etime) < time.time():
                # 如果过期了进入下一条
                continue
            if oneDayList.get(str(lottery_end_date.date())):  # 如果存在当前抽奖日期，则直接append上去
                oneDayList.get(str(lottery_end_date.date())).append(reserve_info)
            else:
                oneDayList.update({str(lottery_end_date.date()): [reserve_info]})  # 如果不存在就新建一个key把它存进去
        ret_List = {}
        for k, v in oneDayList.items():
            ret_List.update({k: sorted(v, key=lambda x: x.etime)})  # 每一个日期里面的数据按照开奖时间升序排列
        return ret_List

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        return sorted(zhuanlan_data, key=lambda x: x['etime'])

    async def reserve_lottery(self):
        '''
        state含义：
            -100 ：失效
            150 ：已经开奖
            -110 ：也是开奖了的
            100 ：未开
            -300 ：已经失效
        :return:
        '''
        last_round = await self.sqlhelper.get_latest_reserve_round(readonly=True)
        zhuanlan_data: list[
            TUpReserveRelationInfo] = await self.sqlhelper.get_all_available_reserve_lotterys()  # 获取所有有效的预约抽奖 （按照etime升序排列
        zhuanlan_data_date_sort = self.zhuanlan_date_sort(zhuanlan_data)
        article_content = self.zhuanlan_format(zhuanlan_data_date_sort)

        zhuanlan_data1 = [x for x in zhuanlan_data if x.reserve_round_id == last_round.round_id]
        zhuanlan_data_date_sort1 = self.zhuanlan_date_sort(zhuanlan_data1)
        article_content1 = self.zhuanlan_format(zhuanlan_data_date_sort1)

        if zhuanlan_data_date_sort1:
            split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的预约抽奖'
        article_content = article_content + split_article_content + article_content1
        self.save_article_to_local(title, article_content)
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


async def submit_reserve__lot_main(is_post=True):
    """
    提交专栏
    :param is_post:是否直接发布
    :return:
    """
    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
    cookie3 = gl.get_value('cookie3')
    buvid3 = gl.get_value('buvid3_3')
    gc = GenerateReserveLotCv(cookie3, ua3, csrf3, buvid3)
    gc.post_flag = is_post
    await gc.reserve_lottery()
    print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)


if __name__ == '__main__':
    asyncio.run(submit_reserve__lot_main(True))
