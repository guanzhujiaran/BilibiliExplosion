"""
    通过grpc获取所有的图片动态
"""
import asyncio
import copy
import datetime
import json
import random
import time
import urllib.parse
from typing import Any

from CONFIG import CONFIG
from fastapi接口.log.base_log import official_lot_logger
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from fastapi接口.service.common_utils.dynamic_id_caculate import dynamic_id_2_ts
from fastapi接口.service.grpc_module.grpc.bapi.biliapi import appsign, get_lot_notice, reserve_relation_info
from fastapi接口.service.grpc_module.grpc.grpc_api import bili_grpc
from fastapi接口.service.grpc_module.src.DynObjectClass import dynAllDetail
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from fastapi接口.service.grpc_module.src.根据日期获取抽奖动态.getLotDynSortByDate import LotDynSortByDate
from fastapi接口.service.opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter, BaseStopCounter
from fastapi接口.service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from fastapi接口.utils.Common import sem_gen, asyncio_gather
from utl.pushme.pushme import pushme
from utl.代理.request_with_proxy import request_with_proxy


class StopCounter(BaseStopCounter):
    def __init__(self):
        super().__init__(30)


class SuccCounter(BaseSuccCounter):
    first_dyn_id = 0
    latest_rid: int = 0  # 最后的rid
    latest_succ_dyn_id: int = 0  # 最后获取成功的动态id

    def __init__(self):
        super().__init__()

    def show_text(self) -> str:
        return f"平均获取速度：{self.show_pace():.2f} s/个动态\t最初的动态：{self.first_dyn_id}\t获取时间：{datetime.datetime.fromtimestamp(self.start_ts).strftime('%Y-%m-%d %H:%M:%S')}"


class DynDetailScrapy(UnlimitedCrawler):
    async def handle_fetch(self, rid: int):
        detail = (await self.get_grpc_single_dynDetail(rid))[0]
        await self.Sqlhelper.upsert_DynDetail(
            doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
            dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
            dynamic_created_time=detail.get('dynamic_created_time')
        )

    async def key_params_gen(self, latest_rid: int):
        latest_rid -= 500
        while 1:
            yield latest_rid
            latest_rid += 1

    async def is_stop(self) -> bool:
        return self.stop_counter.stop_flag

    def __init__(self):
        max_sem = 100
        self.offset = 10  # 每次获取rid的数量，数值最好不要超过10，太大的话传输会出问题
        self.proxy_req = request_with_proxy()
        self.BiliGrpc = bili_grpc
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
        self.Sqlhelper = grpc_sql_helper
        self.stop_counter: StopCounter = StopCounter()  # 停止标志
        self.stop_Flag_lock = asyncio.Lock()
        self.scrapy_sem = sem_gen(100)  # 同时运行的协程数量
        self.stop_limit_time = 2 * 3600  # 提前多少时间停止
        self.succ_counter = SuccCounter()
        self._BiliLotDataPublisher = None
        self.status_plugin = StatsPlugin(self)
        super().__init__(
            max_sem=max_sem,
            _logger=official_lot_logger,
            plugins=[self.status_plugin]
        )

    @property
    def BiliLotDataPublisher(self):
        if not self._BiliLotDataPublisher:
            from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
            self._BiliLotDataPublisher = BiliLotDataPublisher
        return self._BiliLotDataPublisher

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

    async def resolve_dynamic_details_card(self, dynData: dict, is_running_scrapy=True):
        """
        解析grpc返回的data里面的东西
        :param is_running_scrapy:
        :param dynData:
        :return: temp_rid, lot_id, dynamic_id, dynamic_created_time
        """
        try:
            temp_rid = dynData.get('extend').get('businessId')
            dynamic_id = dynData.get('extend').get('dynIdStr')
            dynamic_calculated_ts = dynamic_id_2_ts(int(dynamic_id))
            if is_running_scrapy:
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
                            lot_notice_res = await get_lot_notice(
                                business_type=12,
                                business_id=lot_rid,
                                origin_dynamic_id=dynamic_id
                            )
                            lot_data = lot_notice_res.get('data')
                            lot_id = lot_data.get('lottery_id')
                        elif cardType == 'reserve':  # 所有的预约
                            if moduleAdditional.get('up').get('lotteryType') is not None:  # 10是预约抽奖
                                lot_rid = moduleAdditional.get('up').get('rid')
                                lot_notice_res = await get_lot_notice(business_type=10, business_id=lot_rid,
                                                                      origin_dynamic_id=dynamic_id)
                                has_reserve_relation_ids = await bili_reserve_sqlhelper.get_reserve_by_ids(lot_rid)
                                if has_reserve_relation_ids and has_reserve_relation_ids.code == 0 and has_reserve_relation_ids.sid != None:
                                    req1_dict = has_reserve_relation_ids.raw_JSON
                                else:
                                    req1_dict = await reserve_relation_info(lot_rid)
                                    req1_dict.update({'ids': lot_rid})
                                    await bili_reserve_sqlhelper.add_reserve_info_by_resp_dict(
                                        req1_dict,
                                        1
                                    )  # 添加预约json到数据库
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
                                lot_notice_res = await get_lot_notice(business_type=2, business_id=lot_rid,
                                                                      origin_dynamic_id=dynamic_id)
                                lot_data = lot_notice_res.get('data')
                                if lot_data:
                                    lot_id = lot_data.get('lottery_id')
                if module.get('moduleItemNull'):
                    self.log.error(
                        f'出错提醒的moduleItem： http://www.bilibili.com/opus/{dynamic_id}\t{json.dumps(module)}')
            if dynData.get('extend').get('origDesc') and not lot_id:  # 获取官方抽奖，这里的可能会漏掉开头的官方抽奖
                for descNode in dynData.get('extend').get('origDesc'):
                    if descNode.get('type') == 'desc_type_lottery':
                        lot_id = descNode.get('rid')
                        lot_rid = dynData.get('extend').get('businessId')
                        lot_notice_res = await get_lot_notice(business_type=2, business_id=lot_rid,
                                                              origin_dynamic_id=dynamic_id)
                        lot_data = lot_notice_res.get('data')
                        if lot_data:
                            lot_id = lot_data.get('lottery_id')
            if lot_data:
                self.log.debug(f'抽奖动态！{lot_data}')
                await self.BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                    lot_data,
                    extra_routing_key='DynDetailScrapy.resolve_dynamic_details_card'
                )
            return temp_rid, lot_id, dynamic_id, dynamic_created_time
        except Exception as e:
            self.log.exception(f'{dynData}\n解析动态详情出错：{e}')
            pushme(f'解析动态详情出错：{e}', f'{dynData}\n{e}')
            return 0, 0, 0, self._timeshift(0)

    async def get_grpc_dynDetails(self, rid_dyn_ids: list[dict]) -> list[dict]:
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

    async def get_dynamic_ids_by_rids(self, rids: list[int]) -> list[dict]:
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

    async def get_grpc_single_dynDetail(self, rid: int) -> list[dict[str, Any] | dict[str, int | str]]:
        """
        获取单个grpc的动态详情
        :param rid:
        :return:
        """
        self.log.info(f'当前获取rid：{rid}，跳转连接：http://t.bilibili.com/{rid}?type=2')
        resp_list = await self.BiliGrpc.grpc_get_dynamic_detail_by_type_and_rid(
            rid=rid, dynamic_type=2
        )
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
            self.succ_counter.latest_succ_dyn_id = dynamic_id
            self.succ_counter.first_dyn_id = dynamic_id if not self.succ_counter.first_dyn_id else self.succ_counter.first_dyn_id
            self.log.info(
                f"{self.succ_counter.show_text()}\n总共成功获取{self.succ_times}次\t{rid} 获取单个动态详情成功！http://www.bilibili.com/opus/{dynamic_id} {dynamic_created_time if dynamic_created_time else ''}")
        else:
            self.succ_counter.succ_count += 1
            self.log.info(
                f"{self.succ_counter.show_text()}\n总共成功获取{self.succ_times}次\t获取单个动态详情成功，但动态被删除了！\t{resp_list}\thttp://t.bilibili.com/{rid}?type=2")
        return ret_dict_list

    async def get_grpc_single_dynDetail_by_dynamic_id(self, dynamic_id: int | str) -> dict:
        """
        获取单个grpc的动态详情
        通过这个获取的rid是负数，防止干扰正常rid
        :param rid:
        :return:
        """
        self.log.info(f'当前获取dynamic_id：{dynamic_id}，跳转连接：http://t.bilibili.com/{dynamic_id}')
        rid = dynamic_id
        resp_list = await self.BiliGrpc.grpc_get_dynamic_detail_by_dynamic_id(
            dynamic_id=dynamic_id
        )
        ret_dict_list = []
        dynamic_created_time = None
        if resp_list.get('item'):
            resp_data = resp_list.get('item')
            temp_rid, lot_id, dynamic_id, dynamic_created_time = await self.resolve_dynamic_details_card(
                resp_data)
            temp_detail_dict = dynAllDetail(
                rid=temp_rid,
                dynamic_id=dynamic_id,
                dynData=resp_data,
                lot_id=lot_id if lot_id else None,
                dynamic_created_time=dynamic_created_time
            )
            ret_dict_list.append(temp_detail_dict.__dict__)
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
        return ret_dict_list[0]

    # endregion
    async def get_single_detail_by_rid_list(self, rid_list: list[int]) -> list[int] | None:
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
                    await self.Sqlhelper.upsert_DynDetail(doc_id=detail.get('rid'),
                                                          dynamic_id=detail.get('dynamic_id'),
                                                          dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                                          dynamic_created_time=detail.get('dynamic_created_time'))
                return rid_list
            except Exception as e:
                self.log.exception(e)

    async def get_all_details_by_rid_list(self, rid_list: list[int]) -> list[int]:
        async with self.scrapy_sem:
            try:
                rid_dynamic_id_dict_list = await self.get_dynamic_ids_by_rids(rid_list)
                # self.log.debug(f'\n获取rid_dynamic列表：\n{rid_dynamic_id_dict_list}')
                all_detail_list = await self.get_grpc_dynDetails(rid_dynamic_id_dict_list)
                for detail in all_detail_list:
                    await self.Sqlhelper.upsert_DynDetail(
                        doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                        dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                        dynamic_created_time=detail.get('dynamic_created_time')
                    )
            except Exception as e:
                self.log.exception(e)
            return rid_list

    async def get_discontious_dynamics(self):
        all_rids = await self.Sqlhelper.get_discountious_rids()
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
        await asyncio_gather(*task_list, log=self.log)

    async def get_discontious_dynamics_by_single_detail(self):
        """
        通过获取单个rid动态的方式获取不连续的缺失动态
        :return:
        """
        all_rids = await self.Sqlhelper.get_discountious_rids()
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
        await asyncio_gather(*task_list, log=self.log)
        # for t in thread_list:
        #     t.join()

    async def get_lost_lottery_notice(self, limit_ts: int = 7 * 3600 * 24):
        '''
        重新获取有lot_id，但是lotdata没存进去的抽奖
        :return:
        '''
        self.log.debug("开始获取缺失的抽奖信息！")

        all_lots = await self.Sqlhelper.get_lost_lots(limit_ts)
        self.log.debug(f'共有{len(all_lots)}条缺失抽奖信息！')
        task_list = []
        for all_detail in all_lots:
            task = asyncio.create_task(
                self.resolve_dynamic_details_card(
                    json.loads(all_detail.dynData if all_detail.dynData else "null", strict=False)))
            task_list.append(task)
        await asyncio_gather(*task_list, log=self.log)

    async def handle_single_dynDetail_by_dynamic_id(self, dynamic_id):
        detail = (await self.get_grpc_single_dynDetail_by_dynamic_id(dynamic_id))[0]
        await self.Sqlhelper.upsert_DynDetail(
            doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
            dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
            dynamic_created_time=detail.get('dynamic_created_time')
        )

    async def main(self):
        try:
            latest_rid = int(await self.Sqlhelper.get_latest_rid())
            task_list = []
            if not latest_rid or int(latest_rid) < 339283794:
                self.log.debug("未获取到最后一个rid或太小，启用默认值！")
                latest_rid = 339283794
                self.log.info('开始重新获取失败的动态！')
                task1 = asyncio.create_task(self.get_discontious_dynamics_by_single_detail())
                task_list.append(task1)
                await asyncio.sleep(30)
                self.log.info('重新获取有lot_id，但是lotdata没存进去的抽奖！')
                task2 = asyncio.create_task(self.get_lost_lottery_notice())
                task_list.append(task2)
            self.succ_counter = SuccCounter()
            self.succ_counter.is_running = True
            self.log.info('开始执行获取动态详情')
            self.log.debug(f'爬虫，启动！最后的rid为：{latest_rid}\t往前回滚500个rid！')
            task3 = asyncio.create_task(self.run(latest_rid))
            task_list.append(task3)
            await asyncio_gather(*task_list, log=self.log)
            self.log.error('爬取动态任务全部完成！')
        except Exception as e:
            self.log.error(f'爬取动态任务出错：{e}')
            pushme(title='爬取动态任务出错', content=f'爬取动态任务出错：{e}')
        finally:
            self.succ_counter.is_running = False
        lot_dyn_sort_by_date = LotDynSortByDate()
        await lot_dyn_sort_by_date.main()

    # region 测试用
    async def _testget_dynamics_by_spec_rids(self, all_rids: list[int]):
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
        await asyncio_gather(*task_list, log=self.log)

    async def _test_run(self):
        latest_rid = int(await self.Sqlhelper.get_latest_rid())
        self.succ_counter = SuccCounter()
        self.log.info(1)
        asyncio.get_event_loop().call_later(10, self.stop_counter.set_max_stop_num, )
        self.log.info(2)
        await asyncio.create_task(self.run(latest_rid))

    # endregion


dyn_detail_scrapy = DynDetailScrapy()

if __name__ == "__main__":
    asyncio.run(dyn_detail_scrapy._test_run())
