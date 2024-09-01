# -*- coding: utf-8 -*-
import datetime
import json
import random
import time
import urllib.parse
from typing import Union

from opus新版官方抽奖.Base.GenerateCvModel import CvContent, OpusType
from utl.pushme.pushme import pushme
import requests
import sys

from utl.加密.wbi加密 import get_wbi_params


class GenerateCvBase:
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

    def upload_id_gen(self):
        """
        b站专栏前端生成upload_id的算法
        源代码：
        ```javascript
         uo = function(t) {
                            return "".concat(t || 0, "_").concat(Math.floor(Date.now() / 1e3), "_").concat(Math.floor(1e4 * Math.random()))
                        }
        ```
        :return:
        """
        return f'{self.uid if self.uid else 0}_{int(time.time())}_{int(1e4 * random.random())}'

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

    def zhuanlan_format(self, *args, **kwargs) -> str:
        """

        :param zhuanlan_dict:
        :param blank_space: 开头空几行
        :return:
        """
        raise NotImplementedError(f'没有实现方法【{self.zhuanlan_format.__name__}】')

    def zhuanlan_date_sort(self, *args, **kwargs):
        '''
        为字典添加了etime_str的日期文字格式
        :param zhuanlan_data_order_by_date: 必须将这个数据按照日期排序先
        :param limit_date_switch:
        :param limit_date:
        :return: {'日期':[lot_detail...]}
        '''
        raise NotImplementedError(f'没有实现方法【{self.zhuanlan_date_sort.__name__}】')

    def zhuanlan_data_sort_by_date(self, zhuanlan_data: list) -> list:
        '''
        将所有专栏抽奖数据按开奖日期日期排序
        :return:
        '''
        raise NotImplementedError(f'没有实现方法【{self.zhuanlan_data_sort_by_date.__name__}】')

    # region 提交专栏方法，只有在api接口发送变动的情况下需要修改（已经是老的api接口了，悲T_T
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
            pushme(f'提交专栏【{title}】失败！', req.text)

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
                pushme(f'提交专栏【{title}】失败！', req.text)
        return True

    # endregion

    # region 新版专栏的发布和保存
    async def article_creative_draft_addupdate(self, title: str,
                                               banner_url: str,
                                               article_content: CvContent,
                                               summary: str = "", words: int = 0,
                                               category: int = 15,
                                               list_id: int = 0,
                                               tid: int = 3, reprint: int = 0, tags: str = '',
                                               image_urls: str = '',
                                               origin_image_urls: str = '', media_id: str = '', spoiler: str = "",
                                               original: int = 0,
                                               top_video_bvid: str = '', ) -> int:
        """
        获取aid主要是
        :param title:
        :param banner_url:
        :param article_content:
        :param summary:
        :param words:
        :param category:
        :param list_id:
        :param tid:
        :param reprint:
        :param tags:
        :param image_urls:
        :param origin_image_urls:
        :param media_id:
        :param spoiler:
        :param original:
        :param top_video_bvid:
        :param csrf:
        :return:
        """
        url = 'https://api.bilibili.com/x/article/creative/draft/addupdate'
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
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
            'type': 3,
            'title': title,
            'banner_url': banner_url,
            'content': article_content.model_dump_json(exclude_unset=True, by_alias=True),
            'summary': summary,
            'words': words,
            'category': category,
            'list_id': list_id,
            'tid': tid,
            'reprint': reprint,
            'tags': tags,
            'image_urls': image_urls,
            'origin_image_urls': origin_image_urls,
            'media_id': media_id,
            'spoiler': spoiler,
            'original': original,
            'top_video_bvid': top_video_bvid,
            'up_reply_closed': 0,
            'comment_selected': 0,
            'csrf': self.csrf,
        }
        data = urllib.parse.urlencode(data)
        wbi_sign = await get_wbi_params({})
        params = {
            'w_rid': wbi_sign['w_rid'],
            'wts': wbi_sign['wts']
        }
        req = self.s.post(url=url,
                          params=params,
                          data=data,
                          headers=headers
                          )
        print(req.text)
        if req.json().get('code') == 0:
            return req.json().get('data').get('aid')
        else:
            pushme(f'保存专栏【{title}】失败！', req.text)

    async def dynamic_feed_create_opus(self, draft_id_str: Union[str, int], title: str, article_content: CvContent,
                                       category: int = 15, list_id: int = 0):
        url = 'https://api.bilibili.com/x/dynamic/feed/create/opus'
        upload_id = self.upload_id_gen()
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/json',
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
        params = {
            'csrf': self.csrf,
            'gaia_source': 'main_web',
            'w_opus_req.upload_id': upload_id,
        }
        data: dict = {
            'draft_id_str': str(draft_id_str),
            'opus_req': {
                'meta': {
                    'app_meta': {
                        "from": "create.article.web",
                        "mobi_app": "web"
                    }
                },
                "option": {},
                "opus": {
                    "article": {
                        "category_id": category,
                        "list_id": list_id,
                        "originality": 0,
                        "reproduced": 0,
                        "biz_tags": []
                    },
                    "content": article_content.toOpusContent(OpusType.ARTICLE),
                    "opus_source": 2,
                    "pub_info": {},
                    "title": title
                },
                "scene": 12,
                "upload_id": "4237378_1725165179_3369"
            },
            'raw_content': article_content.model_dump_json(exclude_unset=True, by_alias=True),
        }
        wbi = await get_wbi_params(params)
        params.update(wbi)
        req = self.s.post(url=url,
                          params=params,
                          json=data,
                          headers=headers
                          )
        print(req.text)
        if req.json().get('code') == 0:
            return req.json().get('data').get('aid')
        else:
            pushme(f'提交专栏【{title}】失败！', req.text)

    # endregion
