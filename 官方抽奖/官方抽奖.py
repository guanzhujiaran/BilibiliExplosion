import sys
sys.path.append('C:/pythontest/')
import json
import os
import random
import time
import traceback
import requests
import Bilibili_methods.all_methods

class official_lottery:
    def __init__(self):
        self.write_in_file_dict = {'reserve_result': [],  # 预约抽奖结果
                                   'reserve_lottery': [],  # 预约抽奖
                                   'newly_update_reserve_lottery': [],  # 更新的预约抽奖
                                   'official_lottery_result': [],  # 官方抽奖结果
                                   'official_lottery': [],  # 官方抽奖
                                   'newly_update_official_lottery': [],  # 更新的官方抽奖
                                   'charge_lottery_result': [],  # 充电抽奖结果
                                   'charge_lottery': [],  # 充电抽奖
                                   'newly_update_charge_lottery': [],  # 更新的充电抽奖
                                   }
        self.highlight_uid_list = [404177026]
        if not os.path.exists('./log'):
            os.makedirs('./log')
        self.BAPI = Bilibili_methods.all_methods.methods()
        try:
            with open('lotteryid_start.txt', 'r', encoding='utf-8') as lotteryidstart:
                self.start = int(lotteryidstart.readline()) - 2000
                print('回滚2000条记录')
        except:
            print('获取文件失败')
            self.start = 107393
        self.recorded_dynamic_id = []
        try:
            with open('log/rocorded_dynamic_id.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.recorded_dynamic_id.append(_.strip())
        except:
            print('recorded_dynamic_id获取失败')
            exit()
            pass
        self.end_lottery_dynamic_id = []
        try:
            with open('log/end_lottery_dynamic_id.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.end_lottery_dynamic_id.append(_.strip())
        except:
            print('end_lottery_dynamic_id获取失败')
            exit()
            pass

        self.recorded_reserve_lottery = []
        try:
            with open('log/recorded_reserve_lottery.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.recorded_reserve_lottery.append(_.strip())
        except:
            print('recorded_reserve_lottery获取失败')
            exit()
            pass

        self.end_reserve_lottery = []
        try:
            with open('log/end_reserve_lottery.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.end_reserve_lottery.append(_.strip())
        except:
            print('end_reserve_lottery获取失败')
            exit()
            pass

        self.maybe_lottery = []
        try:
            with open('log/maybe_lottery.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.maybe_lottery.append(_.strip())
        except:
            print('maybe_lottery获取失败')
            exit()
            pass

        self.recorded_charge_lottery = []
        try:
            with open('log/recorded_charge_lottery.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.recorded_charge_lottery.append(_.strip())
        except:
            print('maybe_lottery获取失败')
            exit()
            pass

        self.end_charge_lottery = []
        try:
            with open('log/end_charge_lottery.txt', 'r', encoding='utf-8') as f:
                for _ in f.readlines():
                    self.end_charge_lottery.append(_.strip())
        except:
            print('end_charge_lottery获取失败')
            exit()
            pass

        self.end = sys.maxsize  # 创建具有最大大小的list
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
        w = open('每日可能被删的抽奖.csv', 'w', encoding='utf-8')  # 清空文件
        w.writelines('1\n')
        w.close()
        self.detail_by_lid_url = 'https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/detail_by_lid?lottery_id='

    def write_recorded_dynamic_id(self):
        def log_writer(record_list, filepath, write_mode='w'):
            record_list = record_list[-10000:]
            with open(filepath, write_mode, encoding='utf-8') as f:
                for _ in record_list:
                    f.writelines(f'{_}\n')

        if self.recorded_dynamic_id:
            log_writer(self.recorded_dynamic_id, 'log/rocorded_dynamic_id.txt')
            self.recorded_dynamic_id.clear()

        if self.end_lottery_dynamic_id:
            log_writer(self.end_lottery_dynamic_id, 'log/end_lottery_dynamic_id.txt')
            self.end_lottery_dynamic_id.clear()

        if self.recorded_reserve_lottery:
            log_writer(self.recorded_reserve_lottery, 'log/recorded_reserve_lottery.txt')
            self.recorded_reserve_lottery.clear()

        if self.end_reserve_lottery:
            log_writer(self.end_reserve_lottery, 'log/end_reserve_lottery.txt')
            self.end_reserve_lottery.clear()

        if self.maybe_lottery:
            log_writer(self.maybe_lottery, 'log/maybe_lottery.txt')
            self.maybe_lottery.clear()

        if self.recorded_charge_lottery:
            log_writer(self.recorded_charge_lottery, 'log/recorded_charge_lottery.txt')
            self.recorded_charge_lottery.clear()

        if self.end_charge_lottery:
            log_writer(self.end_charge_lottery, 'log/end_charge_lottery.txt')
            self.end_charge_lottery.clear()

    def write_result(self):
        try:
            with open('./log/预约抽奖开奖结果.csv', 'a+', encoding='utf-8') as reserve_result:
                reserve_result.writelines(self.write_in_file_dict.get('reserve_result'))
        except:
            with open('./log/预约抽奖开奖结果.csv', 'w', encoding='utf-8') as reserve_result:
                reserve_result.writelines(self.write_in_file_dict.get('reserve_result'))

        with open('预约抽奖.csv', 'a+', encoding='utf-8') as reserve_lottery:
            reserve_lottery.writelines(self.write_in_file_dict.get('reserve_lottery'))

        with open('预约抽奖更新内容.csv', 'w', encoding='utf-8') as newly_update_official_lottery:
            newly_update_official_lottery.writelines('1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\n')
            newly_update_official_lottery.writelines(self.write_in_file_dict.get('newly_update_reserve_lottery'))

        try:
            with open('./log/官方抽奖开奖结果.csv', 'a+', encoding='utf-8') as official_lottery_result:
                official_lottery_result.writelines(self.write_in_file_dict.get('official_lottery_result'))
        except:
            official_lottery_result.writelines(self.write_in_file_dict.get('official_lottery_result'))

        with open('官方抽奖.csv', 'a+', encoding='utf-8') as official_lottery:
            official_lottery.writelines(self.write_in_file_dict.get('official_lottery'))

        with open('官方抽奖更新内容.csv', 'w', encoding='utf-8') as newly_update_official_lottery:
            newly_update_official_lottery.writelines('1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\n')
            newly_update_official_lottery.writelines(self.write_in_file_dict.get('newly_update_official_lottery'))

        try:
            with open('./log/充电抽奖开奖结果.csv', 'a+', encoding='utf-8') as charge_lottery_result:
                charge_lottery_result.writelines(self.write_in_file_dict.get('charge_lottery_result'))
        except:
            with open('./log/充电抽奖开奖结果.csv', 'w', encoding='utf-8') as charge_lottery_result:
                charge_lottery_result.writelines(self.write_in_file_dict.get('charge_lottery_result'))

        try:
            with open('充电抽奖.csv', 'a+', encoding='utf-8') as charge_lottery:
                charge_lottery.writelines(self.write_in_file_dict.get('charge_lottery'))
        except:
            with open('充电抽奖.csv', 'w', encoding='utf-8') as charge_lottery:
                charge_lottery.writelines('1\n')
                charge_lottery.writelines(self.write_in_file_dict.get('charge_lottery'))

        with open('充电抽奖更新内容.csv', 'w', encoding='utf-8') as newly_update_charge_lottery:
            newly_update_charge_lottery.writelines('1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\t13\n')
            newly_update_charge_lottery.writelines(self.write_in_file_dict.get('newly_update_charge_lottery'))

    def chaxunzhuanfacishu(self, dynamic_id, lottery_url):
        # 无法通过此接口查询是否被删除
        while 1:
            url = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail/forward?id={dynamic_id}'
            headers = {
                'origin': 'https://t.bilibili.com',
                'referer': 'https://t.bilibili.com/{}?spm_id_from=444.41.0.0'.format(dynamic_id),
                'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': "\"Windows\"",
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate', 
                'accept-language': 'zh-CN,zh;q=0.9',
            }
            req = requests.request('GET', url=url, headers=headers)
            time.sleep(5)
            if req.json().get('code') != 0:
                try:
                    with open('log/dynamic_detail_req.csv', 'a+', encoding='utf-8') as f:
                        f.writelines(f'{url}\t{lottery_url}\t{req.json()}\t{self.BAPI.timeshift(int(time.time()))}\n')
                except:
                    with open('log/dynamic_detail_req.csv', 'w', encoding='utf-8') as f:
                        f.writelines(f'{url}\t{lottery_url}\t{req.json()}\t{self.BAPI.timeshift(int(time.time()))}\n')
                if req.json().get('code') == 4101131:  # 不存在
                    print(url, req.json(),'不存在的动态')
                    return None
                if req.json().get('code') == 500:  # 被删除
                    print(url, req.json(),'被删除的动态')
                    return None
                if req.json().get('code')==4101128: #不存在
                    print(url, req.json(),'不存在的动态')
                    return None
                if req.json().get('code') ==-412:
                    print(f'-412风控 {req.json()} {url} {self.BAPI.timeshift(time.time())}')
                    time.sleep(5*60)
                    continue
                print(req.text)
                print('chaxunzhuanfacishu 动态详情code未知', url)
                time.sleep(60)
                continue
            try:
                forward_count = req.json().get('data').get('total')
            except:
                forward_count = None
                print(req.text)
                print('forward_count获取失败 ', url)
            return forward_count

    def chaxunyuyuerenshu(self, business_id):
        while 1:
            url = 'https://api.bilibili.com/x/activity/up/reserve/relation/info?ids=' + str(business_id)
            req = requests.get(url=url, headers={
                'user-agent': random.choice(self.User_Agent_List)
            })
            if req.json().get('code') != 0:
                print(req.text)
                print('chaxunyuyuerenshu 预约人数code未知', url)
                time.sleep(60)
                continue
            try:
                for k, v in req.json().get('data').get('list').items():
                    return v.get('total')
            except:
                print("查询人数失败"+url+'\n'+req.text)
                return None
            return None
    def main(self):
        nowtime = self.BAPI.timeshift(int(time.time()))
        i = 0
        n = 0
        j = 0
        l = 0
        o = 0
        # f.writelines(str(timeshift()) + '\n\n\n')
        # p.writelines(str(timeshift()) + '\n\n\n')
        # q.writelines(str(timeshift()) + '\n\n\n')
        # f.writelines('抽奖链接\t发布者主页\t一等奖\t二等奖\t三等奖\t开奖时间\t预约人数\t概率(%)\n')
        # p.writelines('发布者主页\t动态链接\t一等奖\t二等奖\t三等奖\t开奖时间\t转发次数\t概率(%)\n')
        # q.writelines('发布者主页\t动态链接\t总金额\t参与人数\t开奖时间\t转发次数\t概率(%)\n')

        for tid in range(self.start, int(self.end)):
            ua = random.choice(self.User_Agent_List)
            newurl = self.detail_by_lid_url + str(tid)
            headers = {
                "user-agent": ua
            }
            breaktime = 0
            while 1:
                req = requests.request("GET", newurl, headers=headers)
                if ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">' in req.text):
                    if breaktime > 5:
                        break
                    time.sleep(60)
                    breaktime += 1
                    continue
                try:
                    req.json().get('code')
                except:
                    print(req.text)
                    print('获取抽奖url code未知')
                    print(newurl, headers)
                    req = json.dumps({'code': -9999})
                    traceback.print_exc()
                if req.json().get('code') == 600003:
                    print(f'{newurl}\n600003{req.json()}\n接口可能被风控')
                    time.sleep(60)
                else:
                    break
            if req.json().get('code') == -9999:
                with open('lotteryid_start.txt', 'w', encoding='utf-8') as lotteryidstart:
                    lotteryidstart.write(str(tid))
                break
            req_data = req.json().get('data')
            business_id = req_data.get('business_id')
            business_type = req_data.get('business_type')
            status = req_data.get('status')
            lottery_detail_url = req_data.get('lottery_detail_url')
            sender = req_data.get('sender_uid')

            highlight_flag = ''
            #  print(f'sender:{sender}\t{req.text}')
            if sender:
                if int(sender) in self.highlight_uid_list:
                    highlight_flag = '重点关注对象'

            need_post = req_data.get('need_post')  # 未知参数
            pay_status = req_data.get('pay_status')  # 未知参数

            senderhomepage = 'https://space.bilibili.com/' + str(sender) + '/dynamic'
            lottery_time = req_data.get('lottery_time')
            lottery_time = self.BAPI.timeshift(lottery_time)
            first_prize = req_data.get('first_prize_cmt')
            second_prize = req_data.get('second_prize_cmt')
            third_prize = req_data.get('third_prize_cmt')
            fprize = req_data.get('first_prize')
            sprize = req.json().get('data').get('second_prize')
            tprize = req_data.get('third_prize')
            first_prize_format = f'{first_prize} * {fprize}'.replace('\t', '')
            if sprize != 0:
                second_prize_fromat = f'{second_prize} * {sprize}'.replace('\t', '')
            else:
                second_prize_fromat = ''
            if tprize != 0:
                third_prize_format = f'{third_prize} * {tprize}'.replace('\t', '')
            else:
                third_prize_format = ''
            try:
                allprize = int(fprize) + int(sprize) + int(tprize)
            except:
                print('\033[1;31m'+req.text,end='\033[1;31m')
                print('获取奖品数目失败')
                print(newurl)
                allprize=1
            lottery_result = req_data.get('lottery_result')
            fp_uid_list = []
            fp_name_list = []
            sp_uid_list = []
            sp_name_list = []
            tp_uid_list = []
            tp_name_list = []
            if lottery_result:
                fp_result = lottery_result.get('first_prize_result')
                sp_result = lottery_result.get('second_prize_result')
                tp_result = lottery_result.get('third_prize_result')
                if fp_result:
                    for opq in fp_result:
                        fp_uid_list.append(opq.get('uid'))
                        fp_name_list.append(opq.get('name'))
                if sp_result:
                    for opq in sp_result:
                        sp_uid_list.append(opq.get('uid'))
                        sp_name_list.append(opq.get('name'))
                if tp_result:
                    for opq in tp_result:
                        tp_uid_list.append(opq.get('uid'))
                        tp_name_list.append(opq.get('name'))

            if business_type == 10:  # 预约抽奖
                if status == 2:
                    if str(business_id) in self.end_reserve_lottery:
                        print('过期的预约抽奖')
                        continue
                    yuyuerenshu = self.chaxunyuyuerenshu(business_id)
                    try:
                        gailv = allprize / (yuyuerenshu + 1) / 100
                    except:
                        gailv = 'inf'
                    self.write_in_file_dict.get('reserve_result').append(
                        f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{lottery_detail_url}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{yuyuerenshu}\t{gailv}%\t{fp_uid_list}|{fp_name_list}\t{sp_uid_list}|{sp_name_list}\t{tp_uid_list}|{tp_name_list}\n')
                    self.end_reserve_lottery.append(business_id)
                elif status == -1:
                    print('撤销的预约抽奖')
                else:
                    if str(business_id) in self.recorded_reserve_lottery:
                        print('记录过的预约抽奖')
                        continue
                    yuyuerenshu = self.chaxunyuyuerenshu(business_id)
                    if len(str(business_id)) < 18 and yuyuerenshu != None:
                        zhuanfarenshu = 1
                    else:
                        zhuanfarenshu = self.chaxunzhuanfacishu(business_id, self.detail_by_lid_url + str(
                            tid))  # 如果转发人数也不是None那么可以记录
                    print(
                        f'{self.detail_by_lid_url}{tid}\nhttps://t.bilibili.com/{business_id}\n转发人数:{zhuanfarenshu}\n预约人数:{yuyuerenshu}')
                    if yuyuerenshu is not None and zhuanfarenshu is not None:
                        self.recorded_reserve_lottery.append(business_id)
                        try:
                            gailv = allprize / (yuyuerenshu + 1) * 100
                        except:
                            gailv = 'inf'
                    else:
                        print(f'{req_data}\nhttps://t.bilibili.com/{business_id}\t被删除的动态')
                        gailv = 'inf'
                    if str(gailv) not in 'inf':
                        self.write_in_file_dict.get('reserve_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{lottery_detail_url}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{yuyuerenshu}\t{gailv}%\tstatus:{status}\t{nowtime}\n')
                        self.write_in_file_dict.get('newly_update_reserve_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{lottery_detail_url}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{yuyuerenshu}\t{gailv}%\tstatus:{status}\t{nowtime}\n')
                        i += 1
            elif business_type == 1:  # 官方抽奖
                if status == 2:
                    if str(business_id) in self.end_lottery_dynamic_id:
                        print('文件记录过的开奖动态')
                        continue
                    zhuanfarenshu = self.chaxunzhuanfacishu(business_id, self.detail_by_lid_url + str(tid))
                    print(
                        f'{self.detail_by_lid_url}{tid}\nhttps://t.bilibili.com/{business_id}\n转发人数:{zhuanfarenshu}')
                    try:
                        gailv = allprize / (zhuanfarenshu + 1) / 100
                    except:
                        print(f'https://t.bilibili.com/{business_id}\t被删除的动态')
                        gailv = 'inf'
                    self.write_in_file_dict.get('official_lottery_result').append(
                        f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{zhuanfarenshu}\t{gailv}%\t{fp_uid_list}|{fp_name_list}\t{sp_uid_list}|{sp_name_list}\t{tp_uid_list}|{tp_name_list}\n')
                    self.end_lottery_dynamic_id.append(business_id)
                elif status == -1:
                    print('撤销或未过审的官方抽奖')
                else:
                    if str(business_id) in self.recorded_dynamic_id:
                        print('文件记录过的官方抽奖')
                        continue
                    zhuanfarenshu = self.chaxunzhuanfacishu(business_id, self.detail_by_lid_url + str(tid))
                    print(
                        f'{self.detail_by_lid_url}{tid}\nhttps://t.bilibili.com/{business_id}\n转发人数:{zhuanfarenshu}')
                    if zhuanfarenshu:  # 有转发人数，获取的动态有效的时候才记录
                        self.recorded_dynamic_id.append(business_id)
                        try:
                            gailv = allprize / (zhuanfarenshu + 1) / 100
                        except:
                            gailv = 'inf'
                    else:
                        print(f'{req_data}\nhttps://t.bilibili.com/{business_id}\t被删除的动态')
                        gailv = 'inf'

                    if str(gailv) not in 'inf':
                        self.write_in_file_dict.get('official_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}?tab=1\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{zhuanfarenshu}\t{gailv}%\tstatus:{status}\t{nowtime}\t{highlight_flag}\n')
                        self.write_in_file_dict.get('newly_update_official_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}?tab=1\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{zhuanfarenshu}\t{gailv}%\tstatus:{status}\t{nowtime}\t{highlight_flag}\n')
                        j += 1
            elif business_type == 12:  # 充电抽奖
                if status == 2:
                    if str(business_id) in self.end_charge_lottery:
                        print('文件记录过的充电开奖动态')
                        continue
                    participants = req_data.get('participants')
                    try:
                        gailv = allprize / (participants + 1) / 100
                    except:
                        gailv = 'inf'
                    self.write_in_file_dict.get('charge_lottery_result').append(
                        f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{participants}\t{gailv}%\t{fp_uid_list}|{fp_name_list}\t{sp_uid_list}|{sp_name_list}\t{tp_uid_list}|{tp_name_list}\n')
                    self.end_charge_lottery.append(business_id)
                elif status == -1:
                    print('撤销或未过审的充电抽奖')
                else:
                    if str(business_id) in self.recorded_charge_lottery:
                        print('文件记录过的充电抽奖')
                        continue
                    participants = req_data.get('participants')
                    zhuanfarenshu = self.chaxunzhuanfacishu(business_id,
                                                            self.detail_by_lid_url + str(tid))  # 如果转发人数也不是None那么可以记录
                    print(
                        f'{self.detail_by_lid_url}{tid}\nhttps://t.bilibili.com/{business_id}\n转发人数:{zhuanfarenshu}')
                    if participants is not None and zhuanfarenshu is not None:  # 有参加人数时，获取的动态有效的时候才记录
                        self.recorded_charge_lottery.append(business_id)
                        try:
                            gailv = allprize / (participants + 1) / 100
                        except:
                            gailv = 'inf'
                    else:
                        print(f'{req_data}\nhttps://t.bilibili.com/{business_id}\t被删除的充电抽奖动态')
                        gailv = 'inf'
                    if str(gailv) not in 'inf':
                        self.write_in_file_dict.get('charge_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}?tab=2\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{participants}\t{gailv}%\tstatus:{status}\t{nowtime}\t{highlight_flag}\n')
                        self.write_in_file_dict.get('newly_update_charge_lottery').append(
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\thttps://t.bilibili.com/{business_id}?tab=2\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\t{participants}\t{gailv}%\tstatus:{status}\t{nowtime}\t{highlight_flag}\n')
                        o += 1
            elif business_id == 0:
                try:
                    with open('未过审或者删掉了的官方抽奖.csv', 'a+', encoding='utf-8') as f:  # 也可能是其他类型的抽奖
                        f.writelines((
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
                except:
                    with open('未过审或者删掉了的官方抽奖.csv', 'w', encoding='utf-8') as f:
                        f.writelines((
                            f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
            else:
                print(f'sender:{sender}\t{req.text}')
                if str(tid) not in self.maybe_lottery:
                    print('未记录的疑似lottery_id')
                    try:
                        with open('每日可能被删的抽奖.csv', 'a+', encoding='utf-8') as f:  # 也可能是其他类型的抽奖
                            f.writelines((
                                f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
                    except:
                        with open('每日可能被删的抽奖.csv', 'w', encoding='utf-8') as f:
                            f.writelines((
                                f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
                    self.maybe_lottery.append(str(tid))
                else:
                    try:
                        with open('未知.csv', 'a+', encoding='utf-8') as f:  # 也可能是其他类型的抽奖
                            f.writelines((
                                f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
                    except:
                        with open('未知.csv', 'w', encoding='utf-8') as f:
                            f.writelines((
                                f'need_post:{need_post}\tpay_status:{pay_status}\t{tid}\t{senderhomepage}\t{first_prize_format}\t{second_prize_fromat}\t{third_prize_format}\t{lottery_time}\tstatus:{status}\t{nowtime}\t{req.text}\n'))
            if tid % 500 == 0:
                time.sleep(10)
            n += 1
            # print('第' + str(n) + '次获得抽奖信息')
            # print('抽奖ID：' + str(tid))

        print('共计' + str(j) + '条官方抽奖信息')
        print('共计' + str(i) + '条预约抽奖信息')
        # print('共计' + str(l) + '条红包抽奖信息')
        print('共计' + str(o) + '条充电抽奖信息')
        self.write_result()
        self.write_recorded_dynamic_id()


def schedule():
    official = official_lottery()
    official.main()
    time.sleep(60)
    import 提交专栏
    import b站cookie.b站cookie_
    import b站cookie.globalvar as gl
    ua3 = gl.get_value('ua3')
    csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
    cookie3 = gl.get_value('cookie3')
    buvid3 = gl.get_value('buvid3_3')
    if cookie3 and csrf3 and ua3 and buvid3:
        gc = 提交专栏.generate_cv(cookie3, ua3, csrf3, buvid3)
        gc.charge_lottery()
        gc.official_lottery()
        gc.reserve_lottery()
    else:
        print(cookie3, '\n', csrf3, '\n', ua3, '\n', buvid3)


if __name__ == '__main__':
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    # schedule()
    print('使用内置定时器,开启定时任务,等待时间到达后执行')
    schedulers = BlockingScheduler()
    schedulers.add_job(schedule, 'cron', hour=20, minute=50, misfire_grace_time=1200)
    schedulers.start()
