# -*- coding:utf- 8 -*-
import ast
import json
import random
import re

import requests
import time

breaktime = float('inf')
sleeptime = 0


class accquire_weblog:
    def __init__(self):
        self.User_Agent_List = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
            'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
            'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
            'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
            'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
            'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999'
        ]

    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def base62_encode(self, num, alphabet=ALPHABET):
        """Encode a number in Base X

        `num`: The number to encode
        `alphabet`: The alphabet to use for encoding
        """
        if (num == 0):
            return alphabet[0]
        arr = []
        base = len(alphabet)
        while num:
            rem = num % base
            num = num // base
            arr.append(alphabet[rem])
        arr.reverse()
        return ''.join(arr)

    def base62_decode(self, string, alphabet=ALPHABET):
        """Decode a Base X encoded string into the number

        Arguments:
        - `string`: The encoded string
        - `alphabet`: The alphabet to use for encoding
        """
        base = len(alphabet)
        strlen = len(string)
        num = 0

        idx = 0
        for char in string:
            power = (strlen - (idx + 1))
            num += alphabet.index(char) * (base ** power)
            idx += 1

        return num

    def get_weblogdetail(self, lottery_id):
        url = 'https://lottery.media.weibo.com/lottery/h5/aj/history/index?id={}&sign=1'.format(lottery_id)
        # data = re.findall(r'window.__DATA__ = {(.*)}', req.content.decode('utf-8'), re.S)[0]
        # data_json = '{' + data.replace('\n', '').replace('\t', '').replace('\b', '').replace(' ', '').replace('\r',
        #                                                                                                       '').strip() + '}'
        # data_dict = ast.literal_eval(data_json)
        # headers={
        #     'cookie':'SUB=_2A25PAnm1DeRhGeNH41AV9SfEyz2IHXVsdux9rDV8PUNbmtAKLU3ZkW9NSmefRmCoNEuMrx60LxK2FhSJgTiVtkAK',
        #     'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Mobile Safari/537.36 Edg/98.0.1108.43'
        #          }
        req = requests.get(url=url)
        if req.json().get('code') == 100000:
            return req.json().get('data')
        elif '不存在' in req.json().get('msg'):
            with open('lottery_id开始.txt', 'w', encoding='utf-8') as l:
                l.writelines('{}'.format(lottery_id - 1))
            exit(1)
        else:
            print(req.json())
            return req.json().get('code')

    def mid_to_url(self, midint):
        midint = str(midint)[::-1]
        size = len(midint) / 7 if len(midint) % 7 == 0 else len(midint) / 7 + 1
        result = []
        for i in range(int(size)):
            s = midint[i * 7: (i + 1) * 7][::-1]
            s = self.base62_encode(int(s))
            s_len = len(s)
            if i < size - 1 and len(s) < 4:
                s = '0' * (4 - s_len) + s
            result.append(s)
        result.reverse()
        return ''.join(result)


if __name__ == "__main__":
    # with open('微博每日抽奖.csv', 'w+', encoding='utf-8') as f:
    with open('微博每日抽奖.csv', 'a+', encoding='utf-8') as f:
        # f.writelines('原微博网址\t奖品名称\t奖品数量\t奖品类型\t参与条件\t开奖时间\t创建时间\t开奖网址\t微博mid\t转发\t评论\t点赞\t博主\t认证类型\n')
        with open('lottery_id开始.txt', 'r', encoding='utf-8') as l:
            lottery_idstart = int(l.readline().strip())
        start = accquire_weblog()
        btime = 0
        searchtime = 0
        while lottery_idstart:
            searchtime += 1
            print('第' + str(searchtime) + '次获取微博\turl：https://lottery.media.weibo.com/lottery/h5/aj/history/index?id={}&sign=1'.format(lottery_idstart))
            res = start.get_weblogdetail(lottery_idstart)
            lottery_idstart += 1
            if not isinstance(res, int):


                if res.get('weibo') and not res.get('list'):
                    weibo_mid = res.get('weibo').get('mid')
                    weibo_reposts_count = res.get('weibo').get('reposts_count')
                    weibo_comments_count = res.get('weibo').get('comments_count')
                    weibo_attitudes_count = res.get('weibo').get('attitudes_count')
                    user_name = res.get('weibo').get('user').get('name')
                    user_verified = res.get('weibo').get('user').get('verified_type')
                    user_id = res.get('weibo').get('user').get('id')
                    with open('无list的微博抽奖.csv','a+',encoding='utf-8') as nolist:
                        nolist.writelines(
                                '{weibo_mid}\t{weibo_reposts_count}\t{weibo_comments_count}\t{weibo_attitudes_count}\t{user_name}\t{user_verified}\n'.format(

                                    weibo_mid=weibo_mid, weibo_attitudes_count=weibo_attitudes_count,
                                    weibo_comments_count=weibo_comments_count, weibo_reposts_count=weibo_reposts_count,
                                    user_name=user_name, user_verified=user_verified))


                if not res.get('weibo') and res.get('list'):
                    with open('无微博抽奖.csv','a+',encoding='utf-8') as g:
                        weibo_list = res.get('list')[0]
                        prize_name = weibo_list.get('name')
                        prize_total = weibo_list.get('total')
                        if weibo_list.get('prize_type_desc'):
                            prize_type_desc = '【非实物抽奖】'
                        else:
                            prize_type_desc = weibo_list.get('prize_type_desc')
                        lottery_filter = weibo_list.get('filter')
                        lottery_time = weibo_list.get('time')
                        result_url = weibo_list.get('result_url')
                        lottery_status = res.get('list')[0].get('status')
                        g.writelines(
                                'https://lottery.media.weibo.com/lottery/h5/aj/history/index?id={lottery_id}&sign=1\t{prize_name}\t{prize_total}\t{prize_type_desc}\t{lottery_filter}\t{lottery_status}\t{lottery_time}\n'.format(
                                    lottery_id=lottery_idstart-1,
                                    prize_name=prize_name, prize_total=prize_total, prize_type_desc=prize_type_desc,
                                    lottery_filter=lottery_filter, lottery_status=lottery_status,
                                    lottery_time=lottery_time))


                if res.get('list') and res.get('weibo'):
                    try:
                        all_weibo_list = res.get('list')
                        for weibo_list in all_weibo_list:
                            prize_name = weibo_list.get('name')
                            prize_total = weibo_list.get('total')
                            if weibo_list.get('prize_type_desc'):
                                prize_type_desc = '【非实物抽奖】'
                            else:
                                prize_type_desc = weibo_list.get('prize_type_desc')
                            lottery_filter = weibo_list.get('filter')
                            lottery_time = weibo_list.get('time')
                            result_url = weibo_list.get('result_url')
                            weibo_mid = res.get('weibo').get('mid')
                            weibo_reposts_count = res.get('weibo').get('reposts_count')
                            weibo_comments_count = res.get('weibo').get('comments_count')
                            weibo_attitudes_count = res.get('weibo').get('attitudes_count')
                            user_name = res.get('weibo').get('user').get('name')
                            user_verified = res.get('weibo').get('user').get('verified_type')
                            user_id = res.get('weibo').get('user').get('id')
                            lottery_status = res.get('list')[0].get('status')
                            lottery_url = 'https://weibo.com/{user_id}/{mid_to_url}'.format(user_id=user_id,
                                                                                            mid_to_url=start.mid_to_url(
                                                                                                weibo_mid))
                            lottery_create_time=res.get('weibo').get('created_at')
                            with open('微博所有抽奖.csv', 'a+', encoding='utf-8') as p:
                                p.writelines(
                                    '{lottery_url}\t{prize_name}\t{prize_total}\t{prize_type_desc}\t{lottery_filter}\t{lottery_status}\t{lottery_time}\t{create_time}\t{weibo_mid}\t{weibo_reposts_count}\t{weibo_comments_count}\t{weibo_attitudes_count}\t{user_name}\t{user_verified}\t{result_url}\n'.format(
                                        lottery_url=lottery_url,
                                        prize_name=prize_name, prize_total=prize_total, prize_type_desc=prize_type_desc,
                                        lottery_filter=lottery_filter, lottery_status=lottery_status,
                                        lottery_time=lottery_time,create_time=lottery_create_time,
                                        weibo_mid=weibo_mid, weibo_attitudes_count=weibo_attitudes_count,
                                        weibo_comments_count=weibo_comments_count, weibo_reposts_count=weibo_reposts_count,
                                        user_name=user_name, user_verified=user_verified, result_url=result_url))
                            print(
                                    '{lottery_url}\t{prize_name}\t{prize_total}\t{prize_type_desc}\t{lottery_filter}\t{lottery_status}\t{lottery_time}\t{create_time}\t{weibo_mid}\t{weibo_reposts_count}\t{weibo_comments_count}\t{weibo_attitudes_count}\t{user_name}\t{user_verified}\t{result_url}\n'.format(
                                        lottery_url=lottery_url,
                                        prize_name=prize_name, prize_total=prize_total, prize_type_desc=prize_type_desc,
                                        lottery_filter=lottery_filter, lottery_status=lottery_status,
                                        lottery_time=lottery_time,create_time=lottery_create_time,
                                        weibo_mid=weibo_mid, weibo_attitudes_count=weibo_attitudes_count,
                                        weibo_comments_count=weibo_comments_count, weibo_reposts_count=weibo_reposts_count,
                                        user_name=user_name, user_verified=user_verified, result_url=result_url))
                            if lottery_status != 1 and lottery_status != 2 and lottery_status != 4 and lottery_status != 9:
                                print('写入文件\n\n\n')
                                f.writelines(
                                    '{lottery_url}\t{prize_name}\t{prize_total}\t{prize_type_desc}\t{lottery_filter}\t{lottery_time}\t{create_time}\t{weibo_mid}\t{weibo_reposts_count}\t{weibo_comments_count}\t{weibo_attitudes_count}\t{user_name}\t{user_verified}\t{result_url}\n'.format(
                                        lottery_url=lottery_url,
                                        prize_name=prize_name, prize_total=prize_total, prize_type_desc=prize_type_desc,
                                        lottery_filter=lottery_filter,
                                        lottery_time=lottery_time,create_time=lottery_create_time,
                                        weibo_mid=weibo_mid, weibo_attitudes_count=weibo_attitudes_count,
                                        weibo_comments_count=weibo_comments_count, weibo_reposts_count=weibo_reposts_count,
                                        user_name=user_name, user_verified=user_verified, result_url=result_url))
                    except:
                        try:
                            weibodtl = res.get('weibo')
                            if weibodtl:
                                lottery_status = res.get('list')[0].get('status')
                                if lottery_status == 0:
                                    print('未开奖')
                                    print(res)
                                    print('\n\n\n\n')
                                elif lottery_status == 1:
                                    print('已开奖')
                                    continue
                                elif lottery_status == 2:
                                    print('抽奖已删除')
                                    continue
                                elif lottery_status == 9:
                                    print('抽奖异常,已取消')
                                    continue
                                    # 3：审核中
                                    # 4：开过了
                            else:
                                print('原微博已删除')
                                print(weibodtl)
                        finally:
                            print(lottery_idstart)
                            print('获取抽奖微博出错')
            elif res == 0:
                continue
            else:
                print(res)
                break
            # time.sleep(0)
