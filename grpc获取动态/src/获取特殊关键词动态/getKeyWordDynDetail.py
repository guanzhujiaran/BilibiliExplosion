# -*- coding: utf-8 -*-
import json
import time

import pandas as pd

import Bilibili_methods.all_methods
from grpc获取动态.src.DynObjectClass import lotDynData
from grpc获取动态.src.SqlHelper import SQLHelper

"""
使用reg查询动态保存下来
"""
import os


class SearchKeyWordDyn:
    def __init__(self, ):
        self.BAPI = Bilibili_methods.all_methods.methods()
        if not os.path.exists('result'):
            os.makedirs('result')
        self.sql = SQLHelper()

    def flatten_dict(self, d: dict, parent_key='', sep='.'):
        """
        扁平化字典
        :param d:
        :param parent_key:
        :param sep:
        :return:
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            items.extend(self.flatten_dict(item, new_key, sep=sep).items())
                        else:
                            items.append((new_key, item))
                else:
                    items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                if isinstance(v, str):
                    items.append((new_key, repr(v)))
                else:
                    items.append((new_key, v))
        return dict(items)

    def solve_dynData(self,dyn):
        dynData = json.loads(dyn.get('dynData'), strict=False)
        if not dynData.get('extend').get('origDesc'):
            return lotDynData()
        dynamic_content = ''
        if dynData.get('extend').get('opusSummary').get('title'):
            dynamic_content += ''.join([x.get('rawText') for x in
                                        dynData.get('extend').get('opusSummary').get('title').get('text').get(
                                            'nodes')])
        dynamic_content += ''.join([x.get('rawText') for x in
                                    dynData.get('extend').get('opusSummary').get('summary').get('text').get(
                                        'nodes')])
        author_name = dynData.get('extend').get('origName')
        author_space = f"https://space.bilibili.com/{dynData.get('extend').get('uid')}/dynamic"

        moduels = dynData.get('modules')
        lot_rid = ''
        lot_type = ''
        forward_count = '0'
        comment_count = '0'
        like_count = '0'
        official_verify_type = ''
        for module in moduels:
            if module.get('moduleAdditional'):
                moduleAdditional = module.get('moduleAdditional')
                if moduleAdditional.get('type') == 'additional_type_up_reservation':
                    # lot_id不能在这里赋值，需要在底下判断是否为抽奖之后再赋值
                    cardType = moduleAdditional.get('up').get('cardType')
                    if cardType == 'upower_lottery':  # 12是充电抽奖
                        lot_rid = moduleAdditional.get('up').get('dynamicId')
                        lot_type = '充电抽奖'
                    elif cardType == 'reserve':  # 所有的预约
                        if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                            lot_rid = moduleAdditional.get('up').get('rid')
                            lot_type = '预约抽奖'
            if module.get('moduleButtom'):
                moduleState = module.get('moduleButtom').get('moduleStat')
                if moduleState:
                    forward_count = moduleState.get('repost') if moduleState.get('repost') else '0'
                    like_count = moduleState.get('like') if moduleState.get('like') else '0'
                    comment_count = moduleState.get('reply') if moduleState.get('reply') else '0'
            if module.get('moduleAuthor'):
                author = module.get('moduleAuthor').get('author')
                if author:
                    official_verify_type = str(author.get('official').get('type')) if author.get(
                        'official') and author.get('official').get('type') else '0'
        if dynData.get('extend').get('origDesc'):
            for descNode in dynData.get('extend').get('origDesc'):
                if descNode.get('type') == 'desc_type_lottery':
                    lot_rid = dynData.get('extend').get('businessId')
                    lot_type = '官方抽奖'

        dynamic_calculated_ts = int(
            (int(dynData.get('extend').get('dynIdStr')) + 6437415932101782528) / 4294939971.297)
        pub_time = self.BAPI.timeshift(dynamic_calculated_ts)

        high_lights_list = []
        LotDynData = lotDynData()
        LotDynData.dyn_url = f"https://t.bilibili.com/{dynData.get('extend').get('dynIdStr')}"
        LotDynData.lot_rid = str(lot_rid)
        LotDynData.dynamic_content = repr(dynamic_content)
        LotDynData.lot_type = str(lot_type)
        LotDynData.premsg = ''
        LotDynData.forward_count = str(forward_count)
        LotDynData.comment_count = str(comment_count)
        LotDynData.like_count = str(like_count)
        LotDynData.high_lights_list = high_lights_list
        LotDynData.Manual_judge = ''
        LotDynData.pub_time = str(pub_time)
        LotDynData.official_verify_type = str(official_verify_type)
        LotDynData.author_name = author_name
        LotDynData.author_space = author_space
        return LotDynData


    def main(self, key_word_list: [str], between_ts=None):
        if between_ts is None:
            between_ts = [int(time.time()) - 7 * 24 * 3600, int(time.time())]
        result_gen = self.sql.query_dynData_by_key_word(key_word_list, between_ts)
        result_list = []
        for result in result_gen:
            res_dict = self.solve_dynData(result)

            result_list.append(res_dict.__dict__)
        df = pd.DataFrame(result_list)
        df.to_csv('result/获取结果.csv', sep='\t', index=False)


if __name__ == '__main__':
    a = SearchKeyWordDyn()
    a.main(['招聘'], [int(time.time()) - 7 * 24 * 3600, int(time.time())])
