# -*- coding: utf-8 -*-
"""
发布抽奖专栏
"""
import re
import random
import datetime
import time
from opus新版官方抽奖.Base.generate_cv import GenerateCvBase
from opus新版官方抽奖.Model.OfficialLotModel import LotDetail


class GenerateOfficialLotCv(GenerateCvBase):
    def __init__(self, cookie, ua, csrf, buvid):
        super().__init__(cookie, ua, csrf, buvid)
        self.post_flag = True  # 是否直接发布

    def zhuanlan_format(self, zhuanlan_dict: dict, blank_space: int = 0) -> tuple[str, str]:
        """

        :param zhuanlan_dict:
        :param blank_space: 开头空几行
        :return:
        """
        ret = ''
        manual_ret_text = ''
        for _ in range(blank_space):
            ret += '<p><br></p><figure class="img-box focused" contenteditable="false"><img ' \
                   'src="//i0.hdslb.com/bfs/article/02db465212d3c374a43c60fa2625cc1caeaab796.png" ' \
                   'class="cut-off-6"></figure> '
            manual_ret_text += '\n'
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
            manual_ret_text += str(lottery_end_date) + '\n'
            for __lot_detail in __lot_detail_list:
                ret += f'<li><p><span class="font-size-12">'
                if __lot_detail.dynamic_id:
                    ret += f'<a href="https://t.bilibili.com/{__lot_detail.dynamic_id}?tab=1">动态链接\t</a>'
                    ret += f'<a href="https://www.bilibili.com/opus/{__lot_detail.dynamic_id}">opus链接\t</a>'
                else:
                    ret += f'链接迷路了喵\t'
                # ret += f'<a href="https://space.bilibili.com/{__lot_detail["upmid"]}/dynamic">发布者空间\t</a>'
                ret += str(__lot_detail.first_prize_cmt) + ' * ' + str(__lot_detail.first_prize) + '\t'
                manual_ret_text += f'https://www.bilibili.com/opus/{__lot_detail.dynamic_id}\t{__lot_detail.first_prize_cmt} * {__lot_detail.first_prize}\t'
                if __lot_detail.second_prize_cmt:
                    ret += str(__lot_detail.second_prize_cmt) + ' * ' + str(__lot_detail.second_prize) + '\t'
                    manual_ret_text += f'{__lot_detail.second_prize_cmt} * {__lot_detail.second_prize}\t'
                if __lot_detail.third_prize_cmt:
                    ret += str(__lot_detail.third_prize_cmt) + ' * ' + str(__lot_detail.third_prize) + '\t'
                    manual_ret_text += f'{__lot_detail.third_prize_cmt} * {__lot_detail.third_prize}\t'
                ret += f'概率:{__lot_detail.chance}\t'
                ret += __lot_detail.__dict__.get('etime_str')
                manual_ret_text += f'概率:{__lot_detail.chance}\t' + __lot_detail.__dict__.get('etime_str')
                manual_ret_text+='\n'
                ret += '</span></p></li>'
            ret += '</ol>'
            manual_ret_text+='\n'
        return ret, manual_ret_text

    def zhuanlan_date_sort(self, zhuanlan_data_order_by_date: [LotDetail], limit_date_switch: bool = False,
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

    def official_lottery(self, all_official_lot_detail: [LotDetail], latest_official_lot_detail: [LotDetail]):
        '''
        :return:
        '''
        all_official_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data = self.zhuanlan_date_sort(all_official_lot_detail)
        article_content, manual_article_content = self.zhuanlan_format(zhuanlan_data)

        latest_official_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data1 = self.zhuanlan_date_sort(latest_official_lot_detail)
        article_content1, manual_article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1:
            split_article_content, manual_spilt_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
            manual_spilt_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的官方抽奖'
        article_content = article_content + split_article_content + article_content1
        manual_article_content = manual_article_content + manual_spilt_article_content + manual_article_content1
        self.save_article_to_local(title + '_api_ver', article_content)
        self.save_article_to_local(title + '_手动专栏_ver', manual_article_content)
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

    def charge_lottery(self, all_charge_lot_detail: [LotDetail], latest_charge_lot_detail: [LotDetail]):
        '''
        :return:
        '''
        all_charge_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data = self.zhuanlan_date_sort(all_charge_lot_detail)
        article_content, manual_article_content = self.zhuanlan_format(zhuanlan_data)

        latest_charge_lot_detail.sort(key=lambda x: x.lottery_time, reverse=True)  # 降序
        zhuanlan_data1 = self.zhuanlan_date_sort(latest_charge_lot_detail)
        article_content1, manual_article_content1 = self.zhuanlan_format(zhuanlan_data1)

        if zhuanlan_data1:
            split_article_content, manual_split_article_content = self.zhuanlan_format({"更新内容": []}, 3)
        else:
            split_article_content = ''
            manual_split_article_content = ''
        today = datetime.datetime.today()
        _ = datetime.timedelta(days=1)
        next_day = today + _
        title = f'{next_day.date().month}.{next_day.date().day}之后的充电抽奖'
        article_content = article_content + split_article_content + article_content1
        manual_article_content = manual_article_content + manual_split_article_content + manual_article_content1
        self.save_article_to_local(title + '_api_ver', article_content)
        self.save_article_to_local(title + '_手动专栏_ver', manual_article_content)
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


