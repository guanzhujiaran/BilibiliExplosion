# -*- coding: utf-8 -*-
"""
    通过grpc获取所有的图片动态
"""
import asyncio
import copy
import datetime
import json
import os
import random
import time
import urllib.parse
from loguru import logger
from CONFIG import CONFIG
from grpc获取动态.grpc.bapi.biliapi import appsign, get_lot_notice
from grpc获取动态.src.DynObjectClass import *
from grpc获取动态.src.SqlHelper import SQLHelper
from utl.代理.grpc_api import BiliGrpc
from utl.代理.request_with_proxy import request_with_proxy


class StopCounter:
    _stop_flag: bool = False
    _max_stop_continuous_num: int = 30  # 短时间内超过30个动态都满足条件，则将stop_flag设置为True
    cur_stop_continuous_num: int = 0

    @property
    def stop_flag(self) -> bool:
        if self.cur_stop_continuous_num >= self._max_stop_continuous_num:
            return True
        return False

    def set_max_stop_num(self):
        """
        直接设置达到最大连续次数
        即设置_stop_flag为True
        :return:
        """
        self.cur_stop_continuous_num = self._max_stop_continuous_num


class SuccCounter:
    start_ts = int(time.time())
    succ_count = 0
    first_dyn_id = 0

    def __init__(self):
        self.start_ts = int(time.time())
        self.succ_count = 0
        self.first_dyn_id = 0

    def show_pace(self) -> float:
        """
        获取一个动态需要花多少秒
        :return:
        """
        now_ts = int(time.time())
        spend_ts = now_ts - self.start_ts
        if spend_ts > 0:
            pace_per_sec = spend_ts / self.succ_count
            return pace_per_sec
        else:
            return 0.0

    def show_text(self) -> str:
        return f"平均获取速度：{self.show_pace():.2f} s/个动态\t最初的动态：{self.first_dyn_id}\t获取时间：{datetime.datetime.fromtimestamp(self.start_ts).strftime('%Y-%m-%d %H:%M:%S')}"


class DynDetailScrapy:
    def __init__(self):
        if not os.path.exists('log'):
            os.makedirs('log')
        self.dir_path = os.path.dirname(os.path.abspath(__file__))
        self.offset = 10  # 每次获取rid的数量，数值最好不要超过10，太大的话传输会出问题
        self.__rootPath = CONFIG.root_dir + 'grpc获取动态'
        self.proxy_req = request_with_proxy()
        self.BiliGrpc = BiliGrpc()
        self.succ_times = 0
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
            "user-agent": CONFIG.rand_ua,
        }
        self.Sqlhelper = SQLHelper()
        self.stop_counter: StopCounter = StopCounter()  # 停止标志
        self.stop_Flag_lock = asyncio.Lock()
        self.scrapy_sem = asyncio.Semaphore(20)  # 同时运行的协程数量
        # self.thread_sem = threading.Semaphore(50)
        self.stop_limit_time = 2 * 3600  # 提前多少时间停止
        self.log = logger.bind(user='官方抽奖')

        self.succ_counter = SuccCounter()

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

    # region 从api获取信息操作
    async def get_dynamic_id_by_doc_id(self, doc_id):
        """
        通过doc_id获取dynamic_id的接口，现在被加上了大概5-10s左右的限制！
        :param doc_id:
        :return:
        """

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
        if time.time() - dynamic_calculated_ts < self.stop_limit_time and time.time() - dynamic_calculated_ts > 0:
            async with self.stop_Flag_lock:
                self.log.debug(f'遇到终止动态！连续终止数+1！\n{dynData}')
                self.stop_counter.cur_stop_continuous_num += 1

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
                        lot_notice_res = await get_lot_notice(12, lot_rid)
                        lot_data = lot_notice_res.get('data')
                        lot_id = lot_data.get('lottery_id')
                    elif cardType == 'reserve':  # 所有的预约
                        if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                            lot_rid = moduleAdditional.get('up').get('rid')
                            lot_notice_res = await get_lot_notice(10, lot_rid)
                            lot_data = lot_notice_res.get('data')
                            lot_id = lot_data.get('lottery_id')
                    else:
                        self.log.error(
                            f'Unknown card type： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_ugc':
                    self.log.info(
                        f'视频卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_common':
                    self.log.info(
                        f'游戏/装扮卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_goods':
                    self.log.info(
                        f'会员购商品卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_vote':
                    self.log.info(
                        f'投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'addition_vote_type_word':
                    self.log.info(
                        f'文字投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'addition_vote_type_default':
                    self.log.info(
                        f'默认投票卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                elif moduleAdditional.get('type') == 'additional_type_esport':
                    self.log.info(
                        f'电子竞技赛事卡片： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(moduleAdditional)}')
                else:
                    self.log.error(
                        f'未知module： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(module)}')
            if module.get('moduleDesc'):
                moduleDesc = module.get('moduleDesc')
                desc = moduleDesc.get('desc')
                if desc:
                    for descNode in desc:
                        if descNode.get('type') == 'desc_type_lottery':  # 获取官方抽奖，这里的比较全
                            lot_id = descNode.get('rid')
                            lot_rid = dynData.get('extend').get('businessId')
                            lot_notice_res = await get_lot_notice(2, lot_rid)
                            lot_data = lot_notice_res.get('data')
                            if lot_data:
                                lot_id = lot_data.get('lottery_id')
            if module.get('moduleItemNull'):
                self.log.error(f'出错提醒的moduleItem： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(module)}')
        if dynData.get('extend').get('origDesc') and not lot_id:  # 获取官方抽奖，这里的可能会漏掉开头的官方抽奖
            for descNode in dynData.get('extend').get('origDesc'):
                if descNode.get('type') == 'desc_type_lottery':
                    lot_id = descNode.get('rid')
                    lot_rid = dynData.get('extend').get('businessId')
                    lot_notice_res = await get_lot_notice(2, lot_rid)
                    lot_data = lot_notice_res.get('data')
                    if lot_data:
                        lot_id = lot_data.get('lottery_id')
        if lot_data:
            self.log.debug(f'抽奖动态！{lot_data}')
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

    async def get_dynamic_ids_by_rids(self, rids: [int]) -> [dict]:
        """
        通过rid列表获取dynamic_id然后再获取动态id列表 # 已经失效了
        :param rids:
        :return: [{'rid': rid:int, 'dynamic_id': doc_id_2_dynamic_id_resp.get('data').get('dynamic_id')}:str,...]
        """
        async with self.stop_Flag_lock:
            if self.stop_counter.stop_flag:
                self.log.debug('遇到停止标志，不进行动态获取')
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
                    self.log.exception(f'动态响应没有动态id了，停止爬取！\n{doc_id_2_dynamic_id_resp}')
                    self.stop_counter.set_max_stop_num()  # 没有动态id了，停止爬取
            else:
                self.log.error(
                    f'http://api.vc.bilibili.com/link_draw/v2/doc/dynamic_id?doc_id={rid}\tInvalid Response:{json.dumps(doc_id_2_dynamic_id_resp)}')
        return ret_dynamic_ids

    async def get_grpc_single_dynDetail(self, rid: int) -> [dict]:
        """
        获取单个grpc的动态详情
        :param rid:
        :return:
        """
        self.log.info(f'当前获取rid：{rid}，跳转连接：http://t.bilibili.com/{rid}?type=2')
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
        self.succ_times += 1
        dynamic_id = ret_dict_list[0].get('dynamic_id')
        if dynamic_id != '-1':
            self.succ_counter.succ_count += 1
            self.succ_counter.first_dyn_id = dynamic_id if not self.succ_counter.first_dyn_id else self.succ_counter.first_dyn_id
            self.log.info(
                f"{self.succ_counter.show_text()}\n总共成功获取{self.succ_times}次\t{rid} 获取单个动态详情成功！http://www.bilibili.com/opus/{dynamic_id} {dynamic_created_time if dynamic_created_time else ''}")
        else:
            self.succ_counter.succ_count += 1
            self.log.info(
                f"{self.succ_counter.show_text()}\n总共成功获取{self.succ_times}次\t获取单个动态详情成功，但动态被删除了！\t{resp_list}\thttp://t.bilibili.com/{rid}?type=2")
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
                    self.log.debug(
                        f"当前执行【{rid_list.index(rid) + 1}/{len(rid_list)}】：动态rid列表：{rid_list}\n跳转连接：http://t.bilibili.com/{rid}?type=2")
                    detail = (await self.get_grpc_single_dynDetail(rid))[0]
                    await asyncio.to_thread(self.Sqlhelper.upsert_DynDetail, doc_id=detail.get('rid'),
                                            dynamic_id=detail.get('dynamic_id'),
                                            dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                            dynamic_created_time=detail.get('dynamic_created_time'))
                return rid_list
            except Exception as e:
                self.log.exception(e)

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
            # self.log.debug(f'\n获取rid_dynamic列表：\n{rid_dynamic_id_dict_list}')
            all_detail_list = self.get_grpc_dynDetails(rid_dynamic_id_dict_list)
            for detail in all_detail_list:
                await asyncio.to_thread(self.Sqlhelper.upsert_DynDetail,
                                        doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                        dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                        dynamic_created_time=detail.get('dynamic_created_time')
                                        )
        except Exception as e:
            self.log.exception(e)
        self.scrapy_sem.release()
        return rid

    async def get_all_details_by_rid_list(self, rid_list: [int]) -> int:
        async with self.scrapy_sem:
            try:
                rid_dynamic_id_dict_list = await self.get_dynamic_ids_by_rids(rid_list)
                # self.log.debug(f'\n获取rid_dynamic列表：\n{rid_dynamic_id_dict_list}')
                all_detail_list = await self.get_grpc_dynDetails(rid_dynamic_id_dict_list)
                for detail in all_detail_list:
                    await asyncio.to_thread(
                        self.Sqlhelper.upsert_DynDetail,
                        doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                        dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                        dynamic_created_time=detail.get('dynamic_created_time')
                    )
            except Exception as e:
                self.log.exception(e)
            return rid_list

    async def get_discontious_dynamics(self) -> [int]:
        all_rids = await asyncio.to_thread(self.Sqlhelper.get_discountious_rids)
        self.log.info(f'共有{len(all_rids)}条缺失动态')
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
                self.log.info(args)
                task = asyncio.create_task(self.get_all_details_by_rid_list(args))
                task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_discontious_dynamics_by_single_detail(self) -> [int]:
        """
        通过获取单个rid动态的方式获取不连续的缺失动态
        :return:
        """
        all_rids = await asyncio.to_thread(self.Sqlhelper.get_discountious_rids)
        self.log.info(f'共有{len(all_rids)}条缺失动态')
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
                self.log.info(args)
                task = self.get_single_detail_by_rid_list(args)
                task_list.append(task)
        self.log.info(f'共创建{len(task_list)}个进程！')
        await asyncio.gather(*task_list)
        # for t in thread_list:
        #     t.join()

    async def get_lost_lottery_notice(self):
        '''
        重新获取有lot_id，但是lotdata没存进去的抽奖（最近30万条）
        :return:
        '''
        self.log.debug("开始获取抽奖信息！")
        all_lots = await asyncio.to_thread(self.Sqlhelper.get_lost_lots)
        self.log.debug(f'共有{len(all_lots)}条缺失抽奖信息！')
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
            if self.stop_counter.stop_flag:
                self.log.debug('遇到停止标志，不进行动态获取')
                return []
        offset = self.offset
        rids_list = []
        for i in range(offset):
            rids_list.append(rid)
            rid += 1
        try:
            for rid in rids_list:
                detail = (await self.get_grpc_single_dynDetail(rid))[0]
                await asyncio.to_thread(self.Sqlhelper.upsert_DynDetail,
                                        doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                        dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                        dynamic_created_time=detail.get('dynamic_created_time')
                                        )
        except Exception as e:
            self.log.exception(e)
        self.scrapy_sem.release()
        # self.thread_sem.release()
        return rid

    def run_async_in_thread(self, async_task, *args, **kargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_task(*args, **kargs))
        loop.close()

    async def main_get_dynamic_detail_by_rid(self):
        latest_rid = int(await asyncio.to_thread(self.Sqlhelper.get_latest_rid))
        if not latest_rid:
            self.log.debug("未获取到最后一个rid，启用默认值！")
            latest_rid = 260977479
        self.log.debug(f'爬虫，启动！最后的rid为：{latest_rid}\t往前回滚500个rid！')
        latest_rid -= 500
        thread_num = 10
        turn_times = 0
        task_list = []
        while 1:
            async with self.stop_Flag_lock:
                if self.stop_counter.stop_flag:
                    self.log.info('遇到停止标志，等待剩余任务完成！')
                    break
            turn_times += 1
            self.log.info(
                f'第{turn_times}轮获取动态（每轮获取{thread_num * self.offset}个动态）当前共获取{thread_num * self.offset * turn_times}条动态')
            for i in range(thread_num):
                await self.scrapy_sem.acquire()
                # self.thread_sem.acquire() # 获得线程，可用线程数减1
                task = asyncio.create_task(self.get_single_dynDetail_by_rid_start(latest_rid))
                # task = threading.Thread(target=self.run_async_in_thread,args=(self.get_single_dynDetail_by_rid_start,latest_rid))
                # task.start()
                latest_rid += self.offset
                task_list.append(task)
            self.log.debug(f'当前可开启线程数剩余：{self.scrapy_sem._value}')
            # task_list = list(filter(lambda _t: not _t.is_alive(), task_list))
            task_list = list(filter(lambda _t: not _t.done(), task_list))
            if self.stop_counter.stop_flag:
                # for t in task_list:
                #     t.join()
                while task_list:
                    task_list = list(filter(lambda _t: not _t.done(), task_list))
                    self.log.info(f'遇到停止标志，等待剩余任务{len(task_list)}个完成！')
                    await asyncio.sleep(10)
                await asyncio.gather(*task_list)

    async def main(self):
        self.succ_counter = SuccCounter()
        self.log.info('开始重新获取失败的动态！')
        task1 = asyncio.create_task(self.get_discontious_dynamics_by_single_detail())
        await asyncio.sleep(30)
        self.log.info('重新获取有lot_id，但是lotdata没存进去的抽奖！')
        task2 = asyncio.create_task(self.get_lost_lottery_notice())
        self.log.info('开始执行获取动态详情')
        task3 = asyncio.create_task(self.main_get_dynamic_detail_by_rid())
        await asyncio.gather(task1, task2, task3)
        self.log.error('爬取任务全部完成！')

    # region 测试用
    async def get_dynamics_by_spec_rids(self, all_rids: [int]):
        """
        根据指定的rid列表获取动态信息，并存到数据库里面
        :param all_rids:
        :return:
        """
        # all_rids = self.Sqlhelper.get_discountious_rids()
        self.log.info(f'共有{len(all_rids)}条缺失动态')
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
                self.log.info(args)
                task = self.get_single_detail_by_rid_list(args)
                task_list.append(task)
        self.log.info(f'共创建{len(task_list)}个进程！')
        await asyncio.gather(*task_list)
    # endregion


# def test_get_all_details():
#     dyn_detail_scrapy = DynDetailScrapy()
#     resp = dyn_detail_scrapy.get_lot_notice(2, '260978218')
#     lot_data = resp.get('data')
#     dyn_detail_scrapy.Sqlhelper.upsert_lot_detail(lot_data)


if __name__ == "__main__":
    dynDetailScrapy = DynDetailScrapy()
    # asyncio.run(dynDetailScrapy.get_dynamics_by_spec_rids([
    #     325483528,
    #     325481936,
    #     325473511,
    #     325452985,
    #     325446168,
    #     325445813,
    #     325440446,
    #     325439609,
    #     325439036,
    #     325433473,
    #     325427350,
    #     325419991,
    #     325404541,
    #     325402641,
    #     325399204,
    #     325393851,
    #     325386302,
    #     325382976,
    #     325380300,
    #     325378880,
    #     325378217,
    #     325375855,
    #     325373785,
    #     325364580,
    #     325357863,
    #     325350848,
    #     325349079,
    #     325341619,
    #     325319760,
    #     325311724,
    #     325308919,
    #     325307033,
    #     325302260,
    #     325297393,
    #     325285710,
    #     325284984,
    #     325281482,
    #     325280543,
    #     325271998,
    #     325269171,
    #     325264111,
    #     325260546,
    #     325241853,
    #     325241524,
    #     325219139,
    #     325217535,
    #     325213760,
    #     325205121,
    #     325200202,
    #     325185897,
    #     325184133,
    #     325178731,
    #     325178368,
    #     325178046,
    #     325171727,
    #     325159707,
    #     325158427,
    #     325157783,
    #     325157106,
    #     325156779,
    #     325156540,
    #     325146973,
    #     325146747,
    #     325127792,
    #     325125614,
    #     325123196,
    #     325122777,
    #     325118599,
    #     325114052,
    #     325108081,
    #     325103031,
    #     325078246,
    #     325073597,
    #     325067170,
    #     325063019,
    #     325056154,
    #     325048867,
    #     325046425,
    #     325039979,
    #     325038910,
    #     325032771,
    #     325028137,
    #     325022896,
    #     325011752,
    #     325011465,
    #     325011039,
    #     325007127,
    #     325007043,
    #     325005969,
    #     325004069,
    #     325001402,
    #     324989656,
    #     324987685,
    #     324981163,
    #     324975563,
    #     324974866,
    #     324971286,
    #     324961612,
    #     324942626,
    #     324934630,
    #     324934072,
    #     324930176,
    #     324927725,
    #     324926715,
    #     324912143,
    #     324904921,
    #     324893788,
    #     324883306,
    #     324875042,
    #     324865536,
    #     324863502,
    #     324862631,
    #     324862336,
    #     324861909,
    #     324861101,
    #     324860885,
    #     324855868,
    #     324851087,
    #     324845106,
    #     324827819,
    #     324824802,
    #     324814728,
    #     324802478,
    #     324783316,
    #     324781320,
    #     324775207,
    #     324759956,
    #     324758665,
    #     324754078,
    #     324743064,
    #     324737444,
    #     324737025,
    #     324736170,
    #     324728654,
    #     324727735,
    #     324727339,
    #     324726552,
    #     324718253,
    #     324715273,
    #     324712587,
    #     324702382,
    #     324701259,
    #     324700086,
    #     324698278,
    #     324691173,
    #     324689239,
    #     324684084,
    #     324652717,
    #     324631974,
    #     324630286,
    #     324627023,
    #     324620975,
    #     324619065,
    #     324617297,
    #     324614202,
    #     324614034,
    #     324613020,
    #     324607814,
    #     324606885,
    #     324603050,
    #     324599692,
    #     324598001,
    #     324595911,
    #     324591046,
    #     324588989,
    #     324588981,
    #     324587611,
    #     324586940,
    #     324582652,
    #     324559094,
    #     324555278,
    #     324547108,
    #     324544503,
    #     324539153,
    #     324538836,
    #     324533272,
    #     324526860,
    #     324519054,
    #     324518588,
    #     324518085,
    #     324509863,
    #     324506035,
    #     324505418,
    #     324502278,
    #     324499825,
    #     324497608,
    #     324495724,
    #     324491335,
    #     324486191,
    #     324472785,
    #     324468402,
    #     324464432,
    #     324462360,
    #     324458459,
    #     324453515,
    #     324444983,
    #     324441627,
    #     324434983,
    #     324432275,
    #     324427003,
    #     324425630,
    #     324423764,
    #     324422601,
    #     324410718,
    #     324409307,
    #     324408395,
    #     324400581,
    #     324399048,
    #     324395114,
    #     324394986,
    #     324394102,
    #     324390819,
    #     324387205,
    #     324382835,
    #     324379919,
    #     324376000,
    #     324365689,
    #     324365452,
    #     324363886,
    #     324361922,
    #     324361118,
    #     324356516,
    #     324356160,
    #     324355614,
    #     324350406,
    #     324329279,
    #     324312881,
    #     324312423,
    #     324306800,
    #     324306259,
    #     324303425,
    #     324291808,
    #     324286188,
    #     324283132,
    #     324281591,
    #     324276090,
    #     324275428,
    #     324273341,
    #     324272417,
    #     324264071,
    #     324251064,
    #     324250709,
    #     324249194,
    #     324247989,
    #     324246447,
    #     324245360,
    #     324244542,
    #     324242325,
    #     324240700,
    #     324240666,
    #     324239930,
    #     324239417,
    #     324238884,
    #     324238663,
    #     324235800,
    #     324225116,
    #     324223093,
    #     324220338,
    #     324218944,
    #     324217377,
    #     324212559,
    #     324210533,
    #     324209859,
    #     324201973,
    #     324194533,
    #     324188259,
    #     324187359,
    #     324177817,
    #     324166440,
    #     324165710,
    #     324162053,
    #     324161659,
    #     324161225,
    #     324158844,
    #     324156793,
    #     324155097,
    #     324154280,
    #     324145821,
    #     324116590,
    #     324095171,
    #     324092679,
    #     324090431,
    #     324088610,
    #     324082958,
    #     324082629,
    #     324079183,
    #     324079076,
    #     324070633,
    #     324069426,
    #     324066006,
    #     324065675,
    #     324064783,
    #     324064004,
    #     324051873,
    #     324050125,
    #     324046331,
    #     324030354,
    #     324023933,
    #     324017110,
    #     324016549,
    #     324015746,
    #     324015574,
    #     324014795,
    #     324003282,
    #     324001047,
    #     323989864,
    #     323987044,
    #     323981799,
    #     323978066,
    #     323977979,
    #     323967091,
    #     323960562,
    #     323959256,
    #     323953612,
    #     323941096,
    #     323934428,
    #     323931015,
    #     323929252,
    #     323927962,
    #     323926714,
    #     323926517,
    #     323925448,
    #     323917389,
    #     323914687,
    #     323913037,
    #     323911047,
    #     323904630,
    #     323902234,
    #     323901703,
    #     323896845,
    #     323889772,
    #     323889202,
    #     323888845,
    #     323875948,
    #     323873059,
    #     323870053,
    #     323869365,
    #     323859797,
    #     323856293,
    #     323854333,
    #     323853197,
    #     323846865,
    #     323840446,
    #     323839706,
    #     323838901,
    #     323836603,
    #     323834802,
    #     323828199,
    #     323828132,
    #     323818481,
    #     323815850,
    #     323814367,
    #     323811900,
    #     323805239,
    #     323786329,
    #     323781660,
    #     323779893,
    #     323779711,
    #     323766445,
    #     323758442,
    #     323756040,
    #     323750360,
    #     323739908,
    #     323732789,
    #     323729421,
    #     323729257,
    #     323728675,
    #     323720355,
    #     323719658,
    #     323719559,
    #     323718170,
    #     323712999,
    #     323709692,
    #     323708240,
    #     323706158,
    #     323687912,
    #     323683712,
    #     323669922,
    #     323663539,
    #     323643964,
    #     323642476,
    #     323635823,
    #     323627183,
    #     323626204,
    #     323617598,
    #     323616318,
    #     323600389,
    #     323599722,
    #     323592335,
    #     323584381,
    #     323572900,
    #     323572696,
    #     323569464,
    #     323568048,
    #     323566915,
    #     323562800,
    #     323558028,
    #     323557727,
    #     323554531,
    #     323550675,
    #     323549671,
    #     323529288,
    #     323528329,
    #     323520842,
    #     323518978,
    #     323516893,
    #     323504624,
    #     323501709,
    #     323500115,
    #     323489135,
    #     323481710,
    #     323476584,
    #     323471099,
    #     323469075,
    #     323468970,
    #     323460935,
    #     323433432,
    #     323415288,
    #     323395636,
    #     323394265,
    #     323390502,
    #     323381990,
    #     323371122,
    #     323356698,
    #     323341619,
    #     323327496,
    #     323324415,
    #     323306917,
    #     323297479,
    #     323286671,
    #     323286063,
    #     323276320,
    #     323271709,
    #     323265045,
    #     323255723,
    #     323246897,
    #     323238641,
    #     323237404,
    #     323235663,
    #     323234132,
    #     323230174,
    #     323230061,
    #     323226120,
    #     323202179,
    #     323182032,
    #     323156314,
    #     323149556,
    #     323138263,
    #     323136217,
    #     323133015,
    #     323130739,
    #     323122982,
    #     323122196,
    #     323121110,
    #     323118079,
    #     323115074,
    #     323113339,
    #     323110663,
    #     323106277,
    #     323101214,
    #     323098582,
    #     323096353,
    #     323089689,
    #     323083953,
    #     323074744,
    #     323073681,
    #     323073491,
    #     323052763,
    #     323047820,
    #     323046005,
    #     323039311,
    #     323039175,
    #     323036032,
    #     323033747,
    #     323029492,
    #     323026042,
    #     323024247,
    #     323020200,
    #     323015564,
    #     323009422,
    #     322994098,
    #     322985600,
    #     322982956,
    #     322979982,
    #     322976686,
    #     322963429,
    #     322959633,
    #     322950121,
    #     322947533,
    #     322946747,
    #     322945911,
    #     322941392,
    #     322935876,
    #     322933167,
    #     322926899,
    #     322926106,
    #     322924103,
    #     322920782,
    #     322918985,
    #     322918224,
    #     322918056,
    #     322915692,
    #     322901693,
    #     322900154,
    #     322899647,
    #     322899136,
    #     322881492,
    #     322881244,
    #     322866839,
    #     322848897,
    #     322844467,
    #     322833046,
    #     322831423,
    #     322826110,
    #     322804302,
    #     322801665,
    #     322794021,
    #     322790687,
    #     322786460,
    #     322786296,
    #     322785484,
    #     322780240,
    #     322774006,
    #     322773719,
    #     322761505,
    #     322745963,
    #     322734296,
    #     322726615,
    #     322717950,
    #     322711467,
    #     322709466,
    #     322694511,
    #     322671455,
    #     322666686,
    #     322666203,
    #     322657541,
    #     322639403,
    #     322637470,
    #     322636189,
    #     322626092,
    #     322615178,
    #     322613125,
    #     322611191,
    #     322598791,
    #     322595300,
    #     322588753,
    #     322582628,
    #     322580890,
    #     322579384,
    #     322578212,
    #     322575438,
    #     322557634,
    #     322542685,
    #     322540908,
    #     322528905,
    #     322522684,
    #     322521724,
    #     322521701,
    #     322519953,
    #     322515429,
    #     322513269,
    #     322509898,
    #     322509041,
    #     322503978,
    #     322501642,
    #     322498841,
    #     322468683,
    #     322466368,
    #     322460758,
    #     322448855,
    #     322443714,
    #     322416811,
    #     322415982,
    #     322408849,
    #     322403172,
    #     322400843,
    #     322386439,
    #     322382473,
    #     322375887,
    #     322375260,
    #     322366409,
    #     322365706,
    #     322358798,
    #     322358300,
    #     322331706,
    #     322301287,
    #     322300611,
    #     322299332,
    #     322296979,
    #     322293697,
    #     322293019,
    #     322264395,
    #     322258458,
    #     322257813,
    #     322256785,
    #     322254652,
    #     322251161,
    #     322249368,
    #     322244840,
    #     322221364,
    #     322219503,
    #     322210314,
    #     322199994,
    #     322199929,
    #     322198477,
    #     322193720,
    #     322193358,
    #     322186885,
    #     322183003,
    #     322182614,
    #     322168071,
    #     322164422,
    #     322161091,
    #     322161048,
    #     322159908,
    #     322158288,
    #     322155290,
    #     322154587,
    #     322153268,
    #     322151428,
    #     322149833,
    #     322149758,
    #     322148444,
    #     322141919,
    #     322140493,
    #     322136606,
    #     322136299,
    #     322108301,
    #     322095280,
    #     322084044,
    #     322076452,
    #     322070854,
    #     322067804,
    #     322065176,
    #     322058405,
    #     322053730,
    #     322053599,
    #     322050348,
    #     322049240,
    #     322037491,
    #     322024639,
    #     322024590,
    #     322023334,
    #     322002325,
    #     321996397,
    #     321995000,
    #     321985499,
    #     321976549,
    #     321969507,
    #     321954680,
    #     321938905,
    #     321932783,
    #     321929222,
    #     321910198,
    #     321894862,
    #     321884405,
    #     321883153,
    #     321882051,
    #     321852788,
    #     321848315,
    #     321847756,
    #     321843673,
    #     321835080,
    #     321832786,
    #     321814735,
    #     321786504,
    #     321785357,
    #     321770521,
    #     321769645,
    #     321759628,
    #     321759563,
    #     321748508,
    #     321745933,
    #     321744805,
    #     321743864,
    #     321743206,
    #     321743027,
    #     321708938,
    #     321708682,
    #     321701104,
    #     321680723,
    #     321677284,
    #     321671328,
    #     321641798,
    #     321636401,
    #     321634081,
    #     321622560,
    #     321618145,
    #     321616004,
    #     321615981,
    #     321615488,
    #     321610409,
    #     321609461,
    #     321608099,
    #     321607196,
    #     321607044,
    #     321606826,
    #     321605283,
    #     321603980,
    #     321600487,
    #     321583797,
    #     321580382,
    #     321576655,
    #     321567081,
    #     321564313,
    #     321563977,
    #     321557573,
    #     321555195,
    #     321555028,
    #     321540235,
    #     321529858,
    #     321523275,
    #     321519229,
    #     321501922,
    #     321488939,
    #     321481798,
    #     321466116,
    #     321464699,
    #     321463111,
    #     321461055,
    #     321460566,
    #     321454868,
    #     321451818,
    #     321438873,
    #     321436562,
    #     321432685,
    #     321432451,
    #     321427618,
    #     321422083,
    #     321418313,
    #     321415095,
    #     321413780,
    #     321409518,
    #     321404133,
    #     321403966,
    #     321401830,
    #     321399833,
    #     321397821,
    #     321390726,
    #     321390235,
    #     321374944,
    #     321373093,
    #     321370276,
    #     321361361,
    #     321349281,
    #     321348376,
    #     321341465,
    #     321336873,
    #     321330846,
    #     321329251,
    #     321328117,
    #     321325708,
    #     321324547,
    #     321323257,
    #     321309438,
    #     321308933,
    #     321306365,
    #     321305398,
    #     321298854,
    #     321297669,
    #     321279182,
    #     321277866,
    #     321272600,
    #     321264872,
    #     321262303,
    #     321257215,
    #     321256276,
    #     321248745,
    #     321237136,
    #     321228329,
    #     321228077,
    #     321228029,
    #     321220703,
    #     321220539,
    #     321216395,
    #     321204753,
    #     321202664,
    #     321199979,
    #     321197702,
    #     321160540,
    #     321155456,
    #     321155127,
    #     321153647,
    #     321149116,
    #     321146520,
    #     321144972,
    #     321140699,
    #     321137181,
    #     321130840,
    #     321130494,
    #     321130034,
    #     321124417,
    #     321123868,
    #     321122302,
    #     321121795,
    #     321121626,
    #     321119769,
    #     321118084,
    #     321111257,
    #     321110719,
    #     321108244,
    #     321107510,
    #     321104473,
    #     321097817,
    #     321096236,
    #     321094138,
    #     321090875,
    #     321088564,
    #     321083047,
    #     321079186,
    #     321076660,
    #     321063963,
    #     321056117,
    #     321045102,
    #     321044666,
    #     321041716,
    #     321040414,
    #     321040290,
    #     321031573,
    #     321025168,
    #     321020470,
    #     321017832,
    #     321014071,
    #     321012148,
    #     321011988,
    #     321002729,
    #     320999553,
    #     320990001,
    #     320988908,
    #     320976162,
    #     320967696,
    #     320963362,
    #     320960639,
    #     320959765,
    #     320951491,
    #     320951303,
    #     320950423,
    #     320942686,
    #     320939220,
    #     320939143,
    #     320920175,
    #     320918909,
    #     320917443,
    #     320914521,
    #     320914400,
    #     320911363,
    #     320910239,
    #     320908359,
    #     320900423,
    #     320896055,
    #     320895084,
    #     320895057,
    #     320875849,
    #     320868974,
    #     320868878,
    #     320865035,
    #     320863712,
    #     320861400,
    #     320860730,
    #     320859109,
    #     320851666,
    #     320851585,
    #     320850787,
    #     320848164,
    #     320845968,
    #     320845513,
    #     320835633,
    #     320834234,
    #     320833559,
    #     320833406,
    #     320831333,
    #     320828858,
    #     320823266,
    #     320822659,
    #     320821237,
    #     320816779,
    #     320814451,
    #     320791744,
    #     320790539,
    #     320783856,
    #     320782446,
    #     320781750,
    #     320771498,
    #     320767627,
    #     320763979,
    #     320761468,
    #     320759597,
    #     320754997,
    #     320754815,
    #     320753938,
    #     320752181,
    #     320746222,
    #     320745015,
    #     320744325,
    #     320742518,
    #     320739585,
    #     320735639,
    #     320734895,
    #     320732768,
    #     320731259,
    #     320726505,
    #     320725988,
    #     320723833,
    #     320607477,
    #     320554277,
    #     320482982,
    #     320400760,
    #     320152252,
    #     320036805,
    #     319983375,
    #     319880403,
    #     319857312,
    #     319812719,
    #     319580602,
    #     319463392,
    #     319462492,
    #     319462246,
    #     319461806,
    #     319460944,
    #     319413554,
    #     319381558,
    #     319324042,
    #     319011960,
    #     318805722,
    #     318638203,
    #     318576202,
    #     318517018,
    #     318339984,
    #     318202633,
    #     318185788,
    #     318068475,
    #     318000862,
    #     317921990,
    #     317902844,
    #     317894593,
    #     317885484,
    #     317564248,
    #     317560762,
    #     317467496,
    #     317467436,
    #     317400385,
    #     317290920,
    #     317188984,
    #     317030052,
    #     316918941,
    #     316710231,
    #     316704416,
    #     316699723,
    #     316676712,
    #     316646002,
    #     316532322,
    #     316432708,
    #     316403154,
    #     316334228,
    #     316280464,
    #     316054155,
    #     315971749,
    #     315926130,
    #     315851376,
    #     315748313,
    #     315659977,
    #     315522358,
    #     315511955,
    #     315443984,
    #     315314593,
    #     315081324,
    #     315019524,
    #     314894820,
    #     314844823,
    #     314646095,
    #     314608223,
    #     314300466,
    #     313987057,
    #     313940061,
    #     313932842,
    #     313926162,
    #     313838634,
    #     313649688,
    #     313475821,
    #     313396289,
    #     313396064,
    #     313365511,
    #     313358418,
    #     313357578,
    #     313351773,
    #     313342636,
    #     313328227,
    #     313328210,
    #     313321879,
    #     313316914,
    #     313291067,
    #     313274751,
    #     313270105,
    #     313264441,
    #     313251918,
    #     313226926,
    #     313226155,
    #     313220236,
    #     313211922,
    #     313176113,
    # ]))
    asyncio.run(dynDetailScrapy.main())
