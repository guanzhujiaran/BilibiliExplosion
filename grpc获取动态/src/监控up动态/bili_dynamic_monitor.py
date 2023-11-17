# -*- coding: utf-8 -*-
import time

import threading

import json

import os

from grpc获取动态.grpc.grpc_api import BiliGrpc
from utl.pushme.pushme import pushme
from CONFIG import CONFIG
from loguru import logger


class monitor:
    def __init__(self):
        self.dir_path = CONFIG.root_dir + 'grpc获取动态/src/监控up动态/'
        if not os.path.exists(self.dir_path + 'data/'):
            os.makedirs(self.dir_path + 'data/')
        self.uid_list = [370877395]  # 监控的up的uid
        self.monitor_uid_list=None
        if os.path.exists(self.dir_path + 'data/monitor_uid_list.json'):
            with open(self.dir_path + 'data/monitor_uid_list.json', 'r',encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    self.monitor_uid_list = json.loads(content)
        if not self.monitor_uid_list:
            self.monitor_uid_list = [{'uid': uid, 'latest_dynamic_id_list': []} for uid in self.uid_list]

        self.grpc_api = BiliGrpc()
        self.sep_time = 3 * 60  # 间隔时间3分钟，一天总共获取20 * 24 = 480次，间隔比较适中
        self.lock = threading.Lock()

    def timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def save_monitor_uid_list(self):
        with open(self.dir_path + 'data/monitor_uid_list.json', 'w',encoding='utf-8') as f:
            f.write(json.dumps(self.monitor_uid_list,indent='\t'))

    def push_dyn_notify(self, dynamic_item):
        cardType = dynamic_item.get('cardType')
        author_name = dynamic_item.get('extend').get('origName')
        author_space = f"https://space.bilibili.com/{dynamic_item.get('extend').get('uid')}/dynamic"
        dynIdStr = dynamic_item.get('extend').get('dynIdStr')
        dynamic_calculated_ts = int(
            (int(dynIdStr) + 6437415932101782528) / 4294939971.297)
        pub_time = self.timeshift(dynamic_calculated_ts)
        dynamic_content = ''
        if dynamic_item.get('extend').get('opusSummary'):
            if dynamic_item.get('extend').get('opusSummary').get('title'):
                dynamic_content += ''.join([x.get('rawText') for x in
                                            dynamic_item.get('extend').get('opusSummary').get('title').get('text').get(
                                                'nodes')])
            if dynamic_item.get('extend').get('opusSummary').get('summary'):
                dynamic_content += ''.join([x.get('rawText') for x in
                                            dynamic_item.get('extend').get('opusSummary').get('summary').get(
                                                'text').get(
                                                'nodes')])
        elif dynamic_item.get('extend').get('origDesc'):
            dynamic_content += ''.join([x.get('text') for x in
                                        dynamic_item.get('extend').get('origDesc')])

        pushme(f'【Bilibili】你关注的up主 {author_name}有新的动态！',
               f'|信息|内容|\n|---|---|\n|跳转APP|[__点击跳转app__](bilibili://opus/detail/{dynIdStr})|\n|动态类型|{cardType}|\n|up昵称|{author_name}|\n|空间主页|{author_space}|\n|发布时间|{pub_time}|\n|动态内容|{dynamic_content.replace("&#124;", "|")}|',
               'markdown'
               )

    def monitor_main(self, uid):
        latest_dynamic_id_list = []
        for i in self.monitor_uid_list:
            if i.get('uid') == uid:
                latest_dynamic_id_list = i.get('latest_dynamic_id_list')
        first_round = False
        while 1:
            space_hist_resp = self.grpc_api.grpc_get_space_dyn_by_uid(uid)
            resp_list = space_hist_resp.get('list')
            if resp_list:
                logger.info(f'获取到了up主 https://space.bilibili.com/{uid} 的{len(resp_list)}条动态')
                for i in resp_list:
                    dynIdStr = i.get('extend').get('dynIdStr')
                    if dynIdStr not in latest_dynamic_id_list:
                        if not first_round:
                            self.push_dyn_notify(i)
                        with self.lock:
                            latest_dynamic_id_list.append(dynIdStr)
                            if len(latest_dynamic_id_list) > 30:
                                latest_dynamic_id_list.pop(0)
                            self.save_monitor_uid_list()
            time.sleep(self.sep_time)
            first_round = False

    def main(self):
        th_list = []
        for i in self.monitor_uid_list:
            th = threading.Thread(target=self.monitor_main, args=(i.get('uid'),))
            th.start()
            th_list.append(th)
        for t in th_list:
            t.join()


if __name__ == '__main__':
    a = monitor()
    a.main()
