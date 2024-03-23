# -*- coding: utf-8 -*-
"""
    通过grpc获取所有的图片动态
"""
import sys

import asyncio
import copy
import datetime
import hashlib
import json
import os
import random
import threading
import time
import traceback
import urllib.parse
from loguru import logger
from CONFIG import CONFIG
from grpc获取动态.src.DynObjectClass import *
from grpc获取动态.src.SqlHelper import SQLHelper
from utl.代理.grpc_api import BiliGrpc
from utl.代理.request_with_proxy import request_with_proxy


class DynDetailScrapy:
    def __init__(self):
        if not os.path.exists('log'):
            os.makedirs('log')
        self.dir_path = CONFIG.root_dir + 'grpc获取动态/src/'
        self.offset = 10  # 每次获取rid的数量，数值最好不要超过10，太大的话传输会出问题
        self.__rootPath = CONFIG.root_dir + 'grpc获取动态'
        self.proxy_req = request_with_proxy()
        self.BiliGrpc = BiliGrpc()
        self.succ_times=0
        self.comm_headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": random.choice(CONFIG.UA_LIST),
        }
        self.Sqlhelper = SQLHelper()
        self.stop_Flag = False  # 停止标志
        self.stop_Flag_lock = asyncio.Lock()
        self.scrapy_sem = asyncio.Semaphore(300)  # 单个请求的超时时间是10秒，也就是平均10秒钟内的并发数，除以10应该就是每秒的并发了吧，大概
        # self.thread_sem = threading.Semaphore(50)
        self.stop_limit_time = 1 * 3600  # 提前多少时间停止
        self.common_log = logger.bind(user='全局日志')
        self.common_log_handler = logger.add(sys.stderr, level="DEBUG",filter=lambda record: record["extra"].get('user')=="全局日志")
        self.doc_id_2_dynamic_id_log=logger.bind(user='doc_id转dynamic_id日志')
        self.doc_id_2_dynamic_id_log_handler = logger.add(sys.stderr, level="INFO",filter=lambda record: record["extra"].get('user')=="doc_id转dynamic_id日志")
        self.unknown_module_log=logger.bind(user='unknown_module')
        self.unknown_module_log_handler = logger.add(sys.stderr, level="INFO",filter=lambda record: record["extra"].get('user')=="unknown_module")
        self.unknown_card_log=logger.bind(user='unknown_card')
        self.unknown_card_log_handler  = logger.add(sys.stderr, level="INFO",filter=lambda record: record["extra"].get('user')=="unknown_card")
        self.common_error_log=logger.bind(user='common_error_log')
        self.common_error_log_handler  =logger.add(sys.stderr, level="INFO",filter=lambda record: record["extra"].get('user')=="common_error_log")
        self.additional_module_log = logger.bind(user='additional_module_log')
        self.additional_module_log_handler = logger.add(sys.stderr, level="INFO",filter=lambda record: record["extra"].get('user')=="common_error_log")
        self.log_init()

    def _timeshift(self, timestamp: int) -> str:
        '''
        时间戳转换日期
        :param timestamp:
        :return:
        '''
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def _timeunshift(self, datetime_str: str) -> int:
        timeArray = time.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    def log_init(self):
        '''
        初始化日志，根据不同名称区分日志
        :return:
        '''
        # self.doc_id_2_dynamic_id_log.add(
        #     self.dir_path + "log/doc_id转dynamic_id日志.log",
        #     encoding="utf-8",
        #     enqueue=True,
        #     rotation="500MB",
        #     compression="zip",
        #     retention="15 days",
        #     filter=lambda record: record["extra"].get('user') == "doc_id转dynamic_id日志"
        # )

        # self.unknown_module_log.add(
        #     self.dir_path + "log/unknown_module.log",
        #     encoding="utf-8",
        #     enqueue=True,
        #     rotation="500MB",
        #     compression="zip",
        #     retention="15 days",
        #     filter=lambda record: record["extra"].get('user') == "unknown_module"
        #
        # )

        # self.unknown_card_log.add(
        #     self.dir_path + "log/unknown_card.log",
        #     encoding="utf-8",
        #     enqueue=True,
        #     rotation="500MB",
        #     compression="zip",
        #     retention="15 days",
        #     filter=lambda record: record["extra"].get('user') == "unknown_card"
        # )

        self.common_error_log.add(
            self.dir_path + "log/common_error_log.log",
            encoding="utf-8",
            enqueue=True,
            rotation="500MB",
            compression="zip",
            retention="15 days",
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["extra"].get('user') == "common_error_log"
        )

        # self.additional_module_log.add(
        #     self.dir_path + "log/additional_module_log.log",
        #     encoding="utf-8",
        #     enqueue=True,
        #     rotation="500MB",
        #     compression="zip",
        #     retention="15 days",
        #     filter=lambda record: record["extra"].get('user') == "additional_module_log"
        # )

    # region 从api获取信息操作
    async def get_dynamic_id_by_doc_id(self, doc_id):
        """
        通过doc_id获取dynamic_id的接口，现在被加上了大概5-10s左右的限制！
        :param doc_id:
        :return:
        """

        def appsign(params, appkey='1d8b6e7d45233436', appsec='560c52ccd288fed045859ed18bffd973'):
            '为请求参数进行 APP 签名'
            params.update({'appkey': appkey})
            params = dict(sorted(params.items()))  # 按照 key 重排参数
            query = urllib.parse.urlencode(params)  # 序列化参数
            sign = hashlib.md5((query + appsec).encode()).hexdigest()  # 计算 api 签名
            params.update({'sign': sign})
            return params

        pm = {
            '_device': 'android',
            'appkey': '1d8b6e7d45233436',
            'build': 7380300,
            'doc_id': doc_id,
            'platform': 'android',
            '_hwid': 'SX1NL0wuHCsaKRt4BHhIfRguTXxOfj5WN1BkBTdLfhstTn9NfUouFiUV',
            'mobi_app': 'android',
            'ts': int(time.time()),
            'version': '7.38.0',
            'trace_id': f"{datetime.datetime.now().strftime('%Y%m%d%M%S')}000{random.randint(0, 9)}{random.randint(0, 9)}",
            'src': 'meizu'
        }
        signed_params = appsign(pm)

        url = 'http://api.vc.bilibili.com/link_draw/v2/doc/dynamic_id' + '?' + urllib.parse.urlencode(signed_params)
        new_headers = copy.deepcopy(self.comm_headers)
        new_headers.update({
            'Referer': 'http://www.bilibili.com/',
            "user-agent": "Mozilla/5.0 BiliDroid/7.38.0 (bbcallen@gmail.com)",
        })
        return await self.proxy_req.request_with_proxy(url=url, method='get', headers=new_headers, params=signed_params)

    async def resolve_dynamic_details_card(self, dynData):
        """
        解析grpc返回的data里面的东西
        :param dynData:
        :return: temp_rid, lot_id, dynamic_id, dynamic_created_time
        """
        temp_rid = dynData.get('extend').get('businessId')
        dynamic_id = dynData.get('extend').get('dynIdStr')
        dynamic_calculated_ts = int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)
        if time.time() - dynamic_calculated_ts < self.stop_limit_time:
            async with self.stop_Flag_lock:
                self.common_log.debug(f'遇到终止动态！{dynData}')
                self.stop_Flag = True
        dynamic_created_time = self._timeshift(dynamic_calculated_ts)  # 通过公式获取大致的时间，误差大概20秒左右
        moduels = dynData.get('modules')
        lot_id = None
        lot_data = {}
        for module in moduels:
            if module.get('moduleAdditional'):
                moduleAdditional = module.get('moduleAdditional')
                if moduleAdditional.get('type') == 'additional_type_up_reservation':
                    # lot_id不能在这里赋值，需要在底下判断是否为抽奖之后再赋值
                    cardType = moduleAdditional.get('up').get('cardType')
                    if cardType == 'upower_lottery':  # 12是充电抽奖
                        lot_rid = moduleAdditional.get('up').get('dynamicId')
                        lot_notice_res = await self.get_lot_notice(12, lot_rid)
                        lot_data = lot_notice_res.get('data')
                        lot_id = lot_data.get('lottery_id')
                    elif cardType == 'reserve':  # 所有的预约
                        if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                            lot_rid = moduleAdditional.get('up').get('rid')
                            lot_notice_res = await self.get_lot_notice(10, lot_rid)
                            lot_data = lot_notice_res.get('data')
                            lot_id = lot_data.get('lottery_id')
                    else:
                        self.unknown_card_log.error(
                            f'Unknown card type： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_ugc':
                    self.additional_module_log.info(
                        f'视频卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_common':
                    self.additional_module_log.info(
                        f'游戏/装扮卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_goods':
                    self.additional_module_log.info(
                        f'会员购商品卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_vote':
                    self.additional_module_log.info(
                        f'投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'addition_vote_type_word':
                    self.additional_module_log.info(
                        f'文字投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'addition_vote_type_default':
                    self.additional_module_log.info(
                        f'默认投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_esport':
                    self.additional_module_log.info(
                        f'电子竞技赛事卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                else:
                    self.unknown_module_log.error(
                        f'未知module： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(module)}')
            if module.get('moduleDesc'):
                moduleDesc = module.get('moduleDesc')
                desc = moduleDesc.get('desc')
                if desc:
                    for descNode in desc:
                        if descNode.get('type') == 'desc_type_lottery':  # 获取官方抽奖，这里的比较全
                            lot_id = descNode.get('rid')
                            lot_rid = dynData.get('extend').get('businessId')
                            lot_notice_res = await self.get_lot_notice(2, lot_rid)
                            lot_data = lot_notice_res.get('data')
                            if lot_data:
                                lot_id = lot_data.get('lottery_id')
        if dynData.get('extend').get('origDesc') and not lot_id:  # 获取官方抽奖，这里的可能会漏掉开头的官方抽奖
            for descNode in dynData.get('extend').get('origDesc'):
                if descNode.get('type') == 'desc_type_lottery':
                    lot_id = descNode.get('rid')
                    lot_rid = dynData.get('extend').get('businessId')
                    lot_notice_res = await self.get_lot_notice(2, lot_rid)
                    lot_data = lot_notice_res.get('data')
                    if lot_data:
                        lot_id = lot_data.get('lottery_id')
        if lot_data:
            self.common_log.debug(f'抽奖动态！{lot_data}')
            await self.proxy_req.upsert_lot_detail(lot_data)
        return temp_rid, lot_id, dynamic_id, dynamic_created_time

    async def get_grpc_dynDetails(self, rid_dyn_ids: [dict]) -> [dict]:
        """
        通过ridlist对grpc返回的动态详情内容进行处理，并查询抽奖动态，保存抽奖内容
        :param rid_dyn_ids: [{'rid': rid:int, 'dynamic_id': doc_id_2_dynamic_id_resp.get('data').get('dynamic_id')}:str,...]
        :return:
        """
        if len(rid_dyn_ids) == 0:
            return []
        ret_dict_list = []
        dyn_ids = [x['dynamic_id'] for x in rid_dyn_ids if x['dynamic_id'] != -1]
        rid_dyn_ids = [{'rid': str(x['rid']), 'dynamic_id': x['dynamic_id']} for x in rid_dyn_ids]
        if len(dyn_ids) == 0:
            return rid_dyn_ids
        resp_list = await self.BiliGrpc.grpc_api_get_DynDetails(dyn_ids)
        if resp_list.get('list'):
            for resp_data in resp_list['list']:
                temp_rid, lot_id, dynamic_id, dynamic_created_time = await self.resolve_dynamic_details_card(
                    resp_data)
                tempdetail_dict = dynAllDetail(
                    rid=temp_rid,
                    dynamic_id=dynamic_id,
                    dynData=resp_data,
                    lot_id=lot_id if lot_id else None,
                    dynamic_created_time=dynamic_created_time
                )
                ret_dict_list.append(tempdetail_dict.__dict__)

        has_detail_rid_str_list = [x['rid'] for x in ret_dict_list]
        for rid_dyn in rid_dyn_ids:
            if rid_dyn['rid'] not in has_detail_rid_str_list:  # 如果获取的动态详情里没有对应的动态id，那么就添加进去
                ret_dict_list.append(rid_dyn)
        ret_dict_list.sort(key=lambda x: x['rid'])
        return ret_dict_list

    async def get_lot_notice(self, bussiness_type: int, business_id: str):
        """
        获取抽奖notice
        :param bussiness_type:
        :param business_id:
        :return:
        """
        while 1:
            url = 'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice'
            params = {
                'business_type': bussiness_type,
                'business_id': business_id,
            }
            resp = await self.proxy_req.request_with_proxy(url=url, method='get', params=params,
                                                           headers=self.comm_headers)
            if resp.get('code') != 0:
                self.common_error_log.error(f'get_lot_notice Error:\t{resp}\t{bussiness_type, business_id}')
                time.sleep(10)
                if resp.get('code') == -9999:
                    return resp # 只允许code为-9999的或者是0的响应返回！其余的都是有可能代理服务器的响应而非b站自己的响应
                continue
            return resp

    async def get_dynamic_ids_by_rids(self, rids: [int]) -> [dict]:
        """
        通过rid列表获取dynamic_id然后再获取动态id列表 # 已经失效了
        :param rids:
        :return: [{'rid': rid:int, 'dynamic_id': doc_id_2_dynamic_id_resp.get('data').get('dynamic_id')}:str,...]
        """
        async with self.stop_Flag_lock:
            if self.stop_Flag:
                self.common_log.debug('遇到停止标志，不进行动态获取')
                return []
        ret_dynamic_ids = []
        for rid in rids:
            doc_id_2_dynamic_id_resp = await self.get_dynamic_id_by_doc_id(rid)
            cd = doc_id_2_dynamic_id_resp.get('code')
            if cd == 0:
                ret_dynamic_ids.append(
                    {'rid': rid, 'dynamic_id': doc_id_2_dynamic_id_resp.get('data').get('dynamic_id')})
            elif cd == -1:  # -1就是没有这个dynamic_id
                ret_dynamic_ids.append(
                    {'rid': rid, 'dynamic_id': -1})
            elif cd == -9999:
                async with self.stop_Flag_lock:
                    self.stop_Flag = True  # 没有动态id了，停止爬取
            else:
                self.doc_id_2_dynamic_id_log.error(
                    f'http://api.vc.bilibili.com/link_draw/v2/doc/dynamic_id?doc_id={rid}\tInvalid Response:{json.dumps(doc_id_2_dynamic_id_resp)}')
        return ret_dynamic_ids

    async def get_grpc_single_dynDetail(self, rid: int) -> [dict]:
        """
        获取单个grpc的动态详情
        :param rid:
        :return:
        """
        self.common_log.info(f'当前获取rid：{rid}，跳转连接：http://t.bilibili.com/{rid}?type=2')
        resp_list = await self.BiliGrpc.grpc_get_dynamic_detail_by_type_and_rid(rid)
        ret_dict_list = []
        dynamic_created_time = None
        if resp_list.get('item'):
            resp_data = resp_list.get('item')
            temp_rid, lot_id, dynamic_id, dynamic_created_time = await self.resolve_dynamic_details_card(
                resp_data)
            tempdetail_dict = dynAllDetail(
                rid=temp_rid,
                dynamic_id=dynamic_id,
                dynData=resp_data,
                lot_id=lot_id if lot_id else None,
                dynamic_created_time=dynamic_created_time
            )
            ret_dict_list.append(tempdetail_dict.__dict__)
        else:
            ret_dict_list.append({'rid': rid, 'dynamic_id': '-1'})
        self.succ_times+=1
        if ret_dict_list[0].get('dynamic_id') != '-1':
            self.common_log.debug(
                f"总共成功获取{self.succ_times}次\t{rid} 获取单个动态详情成功！http://www.bilibili.com/opus/{ret_dict_list[0].get('dynamic_id')} {dynamic_created_time if dynamic_created_time else ''}")
        else:
            self.common_log.debug(f"总共成功获取{self.succ_times}次\t获取单个动态详情成功，但动态被删除了！http://t.bilibili.com/{rid}?type=2")
        return ret_dict_list

    # endregion
    async def get_single_detail_by_rid_list(self, rid_list: [int]) -> int:
        """
        通过ridlist直接获取动态详情
        :param rid_list:
        :return:
        """
        async with self.scrapy_sem:
            try:
                for rid in rid_list:
                    self.common_log.debug(
                        f"当前执行【{rid_list.index(rid) + 1}/{len(rid_list)}】：动态rid列表：{rid_list}\n跳转连接：http://t.bilibili.com/{rid}?type=2")
                    detail = (await self.get_grpc_single_dynDetail(rid))[0]
                    self.Sqlhelper.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                                    dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                                    dynamic_created_time=detail.get('dynamic_created_time'))
                return rid_list
            except:
                self.common_error_log.error(traceback.format_exc())

    async def get_dyndetails_by_rid_start(self, rid: int) -> int:
        """
        通过rid和type获取单个动态
        :param rid:
        :return:
        """
        offset = self.offset
        rids_list = []
        for i in range(offset):
            rids_list.append(rid)
            rid += 1
        try:
            rid_dynamic_id_dict_list = await self.get_dynamic_ids_by_rids(rids_list)
            # self.common_log.debug(f'\n获取rid_dynamic列表：\n{rid_dynamic_id_dict_list}')
            all_detail_list = self.get_grpc_dynDetails(rid_dynamic_id_dict_list)
            for detail in all_detail_list:
                self.Sqlhelper.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                                dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                                dynamic_created_time=detail.get('dynamic_created_time'))
        except:
            self.common_error_log.error(traceback.format_exc())
        self.scrapy_sem.release()
        return rid

    async def get_all_details_by_rid_list(self, rid_list: [int]) -> int:
        async with self.scrapy_sem:
            try:
                rid_dynamic_id_dict_list = await self.get_dynamic_ids_by_rids(rid_list)
                # self.common_log.debug(f'\n获取rid_dynamic列表：\n{rid_dynamic_id_dict_list}')
                all_detail_list = await self.get_grpc_dynDetails(rid_dynamic_id_dict_list)
                for detail in all_detail_list:
                    self.Sqlhelper.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                                    dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                                    dynamic_created_time=detail.get('dynamic_created_time'))
            except:
                self.common_error_log.error(traceback.format_exc())
            return rid_list

    async def get_discontious_dynamics(self) -> [int]:
        all_rids = self.Sqlhelper.get_discountious_rids()
        print(f'共有{len(all_rids)}条缺失动态')
        task_args_list = []  # [[1,2,3,4,5,6,7,8],[9,10,11,12,13,14,15],...]
        for rid_index in range(len(all_rids) // self.offset + 1):
            rids_list = all_rids[self.offset * rid_index:self.offset * (rid_index + 1)]
            task_args_list.append(rids_list)
        thread_num = 50
        task_list = []
        for task_index in range(len(task_args_list) // thread_num + 1):
            args_list = task_args_list[
                        thread_num * task_index:thread_num * (task_index + 1)]  # 将task切片成[[0...49],[50....99]]
            for args in args_list:
                print(args)
                task = asyncio.create_task(self.get_all_details_by_rid_list(args))
                task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_discontious_dynamics_by_single_detail(self) -> [int]:
        """
        通过获取单个rid动态的方式获取不连续的缺失动态
        :return:
        """
        all_rids = self.Sqlhelper.get_discountious_rids()
        print(f'共有{len(all_rids)}条缺失动态')
        task_args_list = []  # [[1,2,3,4,5,6,7,8],[9,10,11,12,13,14,15],...]
        for rid_index in range(len(all_rids) // self.offset + 1):
            rids_list = all_rids[self.offset * rid_index:self.offset * (rid_index + 1)]
            task_args_list.append(rids_list)
        thread_num = 50
        task_list = []
        for task_index in range(len(task_args_list) // thread_num + 1):
            args_list = task_args_list[
                        thread_num * task_index:thread_num * (task_index + 1)]  # 将task切片成[[0...49],[50....99]]
            for args in args_list:
                print(args)
                task = self.get_single_detail_by_rid_list(args)
                task_list.append(task)
        print(f'共创建{len(task_list)}个进程！')
        await asyncio.gather(*task_list)
        # for t in thread_list:
        #     t.join()

    async def get_lost_lottery_notice(self):
        '''
        重新获取有lot_id，但是lotdata没存进去的抽奖（最近30万条）
        :return:
        '''
        self.common_log.debug("开始获取抽奖信息！")
        all_lots = self.Sqlhelper.get_lost_lots()
        self.common_log.debug(f'共有{len(all_lots)}条缺失抽奖信息！')
        task_list = []
        for all_detail in all_lots:
            task = asyncio.create_task(
                self.resolve_dynamic_details_card(json.loads(all_detail.get('dynData'), strict=False)))
            task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_single_dynDetail_by_rid_start(self, rid):
        """
        通过单个rid获取动态详情
        :param rid:
        :return:
        """
        async with self.stop_Flag_lock:
            if self.stop_Flag:
                self.common_log.debug('遇到停止标志，不进行动态获取')
                return []
        offset = self.offset
        rids_list = []
        for i in range(offset):
            rids_list.append(rid)
            rid += 1
        try:
            for rid in rids_list:
                detail = (await self.get_grpc_single_dynDetail(rid))[0]
                self.Sqlhelper.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                                dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                                dynamic_created_time=detail.get('dynamic_created_time'))
        except:
            self.common_error_log.critical(traceback.format_exc())
        self.scrapy_sem.release()
        # self.thread_sem.release()
        return rid

    def run_async_in_thread(self,async_task,*args,**kargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_task(*args,**kargs))
        loop.close()

    async def main_get_dynamic_detail_by_rid(self):
        latest_rid = int(self.Sqlhelper.get_latest_rid())
        if not latest_rid:
            self.common_log.debug("未获取到最后一个rid，启用默认值！")
            latest_rid = 260977479
        self.common_log.debug(f'爬虫，启动！最后的rid为：{latest_rid}\t往前回滚500个rid！')
        latest_rid -= 500
        thread_num = 50
        turn_times = 0
        task_list = []
        while 1:
            async with self.stop_Flag_lock:
                if self.stop_Flag:
                    print('遇到停止标志！')
                    break
            turn_times += 1
            self.common_log.info(
                f'第{turn_times}轮获取动态（每轮获取{thread_num * self.offset}个动态）当前共获取{thread_num * self.offset * turn_times}条动态')
            for i in range(thread_num):
                await self.scrapy_sem.acquire()
                # self.thread_sem.acquire() # 获得线程，可用线程数减1
                task = asyncio.create_task(self.get_single_dynDetail_by_rid_start(latest_rid))
                # task = threading.Thread(target=self.run_async_in_thread,args=(self.get_single_dynDetail_by_rid_start,latest_rid))
                # task.start()
                latest_rid += self.offset
                task_list.append(task)
            print(f'当前可开启线程数剩余：{self.scrapy_sem._value}')
            # task_list = list(filter(lambda _t: not _t.is_alive(), task_list))
            task_list=list(filter(lambda _t: not _t.done(), task_list))
            if self.stop_Flag:
                # for t in task_list:
                #     t.join()
                await asyncio.gather(*task_list)

    async def main(self):
        print('开始重新获取失败的动态！')
        task1 = asyncio.create_task(self.get_discontious_dynamics_by_single_detail())
        await asyncio.sleep(30)
        print('重新获取有lot_id，但是lotdata没存进去的抽奖！')
        task2 = asyncio.create_task(self.get_lost_lottery_notice())
        print('开始执行获取动态详情')
        task3 = asyncio.create_task(self.main_get_dynamic_detail_by_rid())
        await asyncio.gather(task1, task2, task3)

    # region 测试用
    async def test_get_all_details(self):
        rid_start = 260977479
        print(await self.get_single_dynDetail_by_rid_start(rid_start))
    # endregion


# def test_get_all_details():
#     dyn_detail_scrapy = DynDetailScrapy()
#     resp = dyn_detail_scrapy.get_lot_notice(2, '260978218')
#     lot_data = resp.get('data')
#     dyn_detail_scrapy.Sqlhelper.upsert_lot_detail(lot_data)


if __name__ == "__main__":
    dynDetailScrapy = DynDetailScrapy()
    asyncio.run(dynDetailScrapy.main())
