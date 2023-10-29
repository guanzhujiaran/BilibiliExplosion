import json
import random
import re
import time
import traceback

import js2py
import requests
import Bilibili_methods.paddlenlp
import Bilibili_methods.all_methods


class module_pf:
    def __init__(self):
        self.nlp = Bilibili_methods.paddlenlp.my_paddlenlp()
        self.copy_comment_chance = 0.5  # 抄评论概率
        self.BAPI = Bilibili_methods.all_methods.methods()
        self.ero_pic_up_list = [1242384245, 37743601, 129060, 1930483018, 44714970]  # 色图up
        self.random_crate_dynamic_content = ['中', '我', '你', '。', '，']  # 自己创建动态的随机内容
        self.yunxingshijian = 0.5 * 3600  # 默认运行时间为半小时
        self.ero_pic_num = random.choice(range(6, 12))  # 色图的存量
        self.popvideo_info_list = []
        self.ero_pic_dynamic_detail_list = []
        self.item_id_list = []  # 头像挂件列表
        self.pendant_templist = []

    def share(self, share_content, shareaid, sharemid, cookie, ua, csrf):
        """
        分享视频api
        :param share_content:
        :param shareaid:
        :param sharemid:
        :param cookie:
        :param ua:
        :param csrf:
        :return:
        """
        shareheader = {'cookie': cookie,
                       "user-agent": ua
                       }
        sharedata = {
            'csrf_token': csrf,
            'platform': 'pc',
            'uid': sharemid,
            'type': '8',
            'content': share_content,
            'repost_code': '20000',
            'rid': shareaid,
        }
        shareurl = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/share'
        sharereq = requests.request('POST', url=shareurl, headers=shareheader, data=sharedata)
        shareresult = re.findall('errmsg":"(.*?)","dynamic_id"', sharereq.text)
        print('分享动态结果：' + str(shareresult))
        if sharereq.json().get('code') == 0:
            return True
        else:
            print(sharereq.json())
            return False

    def get_comment(self, aid):
        """
            获取视频评论
        :param aid:
        :return:
        """

        def get_pinglunreq(_aid, _pn):
            url = 'https://api.bilibili.com/x/v2/reply/main?jsonp=jsonp&next={pn}&type=1&oid={aid}&mode=2&plat=1&_={timestp}'.format(
                pn=_pn, aid=_aid, timestp=int(time.time()))
            pinglun_req = requests.get(url=url).text
            return pinglun_req

        pn = 0
        pinglun_req = get_pinglunreq(aid, pn)
        time.sleep(random.choice(self.BAPI.sleeptime))
        try:
            pinglun_dict = json.loads(pinglun_req)
            pinglun_count = pinglun_dict.get('data').get('cursor').get('prev')
        except Exception as e:
            print(e)
            print(pinglun_req)
            print(aid, pn)
            print('获取评论失败')
            return '[吃瓜]'
        if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
            if pinglun_count != 0:
                i = 0
                while True:
                    i += 1
                    if i > 3:
                        print('抄评论失败')
                        return '分享动态'
                    pnlist = list(range(int(pinglun_count * 0.2), int(pinglun_count * 0.90)))
                    if not pnlist:
                        print('动态下评论过少，评论获取失败')
                        break
                    pn = random.choice(pnlist)
                    pinglun_req = get_pinglunreq(aid, pn)
                    time.sleep(random.choice(self.BAPI.sleeptime))
                    pinglun_dict = json.loads(pinglun_req)
                    reply_content = []
                    if pinglun_req != '{"code":-404,"message":"啥都木有","ttl":1}':
                        pinglun_list = pinglun_dict.get('data').get('replies')
                        for reply in pinglun_list:
                            reply_content.append(reply.get('content').get('message'))
                    else:
                        print('获取评论失败')
                    if reply_content:
                        for p in range(len(reply_content)):
                            while 1:
                                msg = ''.join(random.choice(reply_content))
                                sums = 0
                                for wordcount in reply_content:
                                    sums += len(re.sub('\[.*?]| ', '', wordcount))
                                if len(re.sub('\[.*?]| ', '', msg)) <= int(
                                        sums / len(reply_content)):  # 抄短评论还是长评论
                                    break
                            biaoqingbao = re.findall('(?<=\[)(.*?)(?=\])', msg, re.DOTALL)
                            if biaoqingbao:
                                tihuanbiaoqing = self.BAPI.panduanbiaoqingbao(biaoqingbao)
                                if tihuanbiaoqing:
                                    for noemo in tihuanbiaoqing:
                                        msg = msg.replace(noemo, random.choice(self.BAPI.changyongemo))
                            # msg += '[' + random.choice(changyongemo) + ']'
                            if '@' in msg:
                                continue
                            if msg != '' and msg not in self.BAPI.hasemo:
                                print('抄的评论：' + msg)
                                if self.nlp.msg_filter(input_Msg=msg) == '':
                                    continue
                                if self.nlp.sentiment_analysis(msg):
                                    print('通过情感分析抄的评论：' + msg)
                                    return msg
                            else:
                                continue

                    if reply_content == []:
                        print('获取评论为空\t动态类型：' + str(type))
                    time.sleep(random.choice(self.BAPI.sleeptime))

    def video_info_resolution(self, video_info):
        """
            将api返回的视频信息解构
        :param video_info:
        :return:
        """
        aid = video_info.get('aid')
        if aid == None:
            aid = video_info.get('id')
        try:
            mid = video_info.get('owner').get('mid')
            uname = video_info.get('owner').get('name')
            videourl = video_info.get('short_link')
            if videourl==None:
                videourl = video_info.get('uri')
            title = video_info.get('title')
            duration = video_info.get('duration')
            return {uname: {'aid': aid, 'mid': mid, '标题': title, 'video_url': videourl, '时长': duration}}
        except:
            print(video_info)
            traceback.print_exc()
    def share_single_video(self, temp_video, cookie, ua, csrf):
        """
            分享单个视频
        :param temp_video:
        :param cookie:
        :param ua:
        :param csrf:
        """
        for k, v in temp_video.items():
            v_info = v
            aid = v_info.get('aid')
            mid = v_info.get('mid')
            duration = v_info.get('时长')
            if self.copy_comment_chance > random.random():
                sharecontent = self.get_comment(aid)
            else:
                sharecontent = '分享动态'
            if self.share(sharecontent, aid, mid, cookie, ua, csrf):
                print('分享成功')
            else:
                exit('分享失败')
            print('分享视频：\n用户名：{uname}\t标题：{title}\n分享内容：{sharecontent}\t链接：{url}\t时长：{duration}'.format(uname=k,
                                                                                                        title=v_info.get(
                                                                                                            '标题'),
                                                                                                        sharecontent=sharecontent,
                                                                                                        url=v_info.get(
                                                                                                            'video_url'),
                                                                                                        duration=duration))
            return duration

    def module_share_popvideo(self, cookie, ua, csrf):
        """
            分享热门视频
        :param cookie:
        :param ua:
        :param csrf:
        :return:
        """

        def get_popvideo(_page, _cookie, _ua):
            geturl = 'https://api.bilibili.com/x/web-interface/popular?ps=20&pn=' + str(_page)
            getdata = {'ps': '20',
                       'pn': _page}
            headers = {
                'cookie': _cookie,
                'user-agent': _ua
            }
            getreq = requests.request('GET', url=geturl, data=getdata, headers=headers)
            return getreq.json().get('data').get('list')

        def get_rcmd_video(_cookie, _ua):
            url = 'https://api.bilibili.com/x/web-interface/index/top/feed/rcmd'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': _cookie,
                'origin': 'https://www.bilibili.com',
                'referer': 'https://www.bilibili.com/?liteVersion=true&spm_id_from=888.73213.0.0',
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': _ua,
            }
            params = {
                'y_num': 5,
                'fresh_type': 3,
                'feed_version': 'V4',
                'fresh_idx_1h': 6,
                'fetch_row': 1,
                'fresh_idx': 6,
                'brush': 3,
                'homepage_ver': 1,
                'ps': 11,
            }
            req = requests.get(url=url, headers=headers, params=params)
            return req.json().get('data').get('item')

        if not self.popvideo_info_list:
            for page in range(1, 5):
                print('获取第{page}页热门视频\n\n'.format(page=page))
                popvideo_list = get_popvideo(page, cookie, ua)
                for video in popvideo_list:
                    v_info=self.video_info_resolution(video)
                    if v_info:
                        self.popvideo_info_list.append(v_info)
                    # print({uname: {'aid': aid, 'mid': mid, '标题': title, 'video_url': videourl, '时长': duration}})
                time.sleep(2)
            for i in range(0, 5):
                print('获取第{page}次推荐视频\n\n'.format(page=i))
                popvideo_list = get_rcmd_video(cookie, ua)
                for video in popvideo_list:
                    v_info = self.video_info_resolution(video)
                    if v_info:
                        self.popvideo_info_list.append(v_info)
                    # print({uname: {'aid': aid, 'mid': mid, '标题': title, 'video_url': videourl, '时长': duration}})
                time.sleep(2)
            random.shuffle(self.popvideo_info_list)
        print(f'共剩余{len(self.popvideo_info_list)}条视频\n\n')
        temp_video = random.choice(self.popvideo_info_list)
        self.popvideo_info_list.remove(temp_video)
        return self.share_single_video(temp_video, cookie, ua, csrf)

    def module_share_ero_pic(self, uid, cookie, ua, csrf):
        if not self.ero_pic_dynamic_detail_list:  # 当库存为空时进行获取
            offset = ''
            while 1:
                if not self.ero_pic_up_list:
                    break
                temp_up = random.choice(self.ero_pic_up_list)
                self.ero_pic_up_list.remove(temp_up)
                res = self.BAPI.feed_space_without_cookie(temp_up, offset)
                offset = res.get('offset')
                has_more = res.get('has_more')
                for i in res.get('data'):
                    if str(i.get('type')) == '2':  # 2是图片，8是视频
                        self.ero_pic_dynamic_detail_list.append(i)
                if not has_more:
                    break
                if len(self.ero_pic_dynamic_detail_list) >= self.ero_pic_num:
                    break
                time.sleep(random.choice(self.BAPI.sleeptime))

        if self.ero_pic_dynamic_detail_list:
            temp_dynamic_detail = random.choice(self.ero_pic_dynamic_detail_list)
            self.ero_pic_dynamic_detail_list.remove(temp_dynamic_detail)
            dynamic_id = temp_dynamic_detail.get('dynamic_id')
            self.BAPI.reply_feed_create_dyn(uid, dynamic_id, '转发动态', cookie, ua, csrf)
        else:
            print('色图存量为空，请再添加一点色图up')

    def module_random_crate_dynamic(self, crate_content, cookie, ua, csrf, uid):
        """
        随机创建新动态
        :param crate_content:
        :param cookie:
        :param ua:
        :param csrf:
        :param uid:
        :return:
        """

        def submit_dynamic(content, _cookie, _ua, _csrf, _uid):
            js_1 = js2py.EvalJs()
            js_1.execute('''
                function a(){return Math.floor(1e4 * Math.random())}
            ''')
            url = 'https://api.bilibili.com/x/dynamic/feed/create/dyn?csrf={}'.format(_csrf)
            data = {"dyn_req": {"content": {"contents": [{"raw_text": content, "type": 1, "biz_id": ""}]}, "scene": 1,
                                "attach_card": None, "upload_id": "{}_{}_{}".format(_uid, int(time.time()), js_1.a()),
                                "meta": {"app_meta": {"from": "create.dynamic.web", "mobi_app": "web"}}}}
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json;charset=UTF-8',
                'cookie': _cookie,
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/?spm_id_from=444.42.0.0',
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': _ua,
            }
            req = requests.post(url=url, data=json.dumps(data), headers=headers)
            print(req.text)
            return req.json()

        submit_dynamic(crate_content, cookie, ua, csrf, uid)

    def module_change_pendant(self, cookie, ua, csrf):
        if not self.item_id_list:
            self.item_id_list = self.BAPI.get_pendant_item_id_list(cookie, ua, csrf)
            time.sleep(random.choice(self.BAPI.sleeptime))
        if not self.pendant_templist:
            for i in range(random.choice([2, 3, 4])):
                self.pendant_templist.append(random.choice(self.item_id_list))
        print(self.BAPI.dynamic_equip_share(random.choice(self.pendant_templist), cookie, ua, csrf))
