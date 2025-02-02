from typing import List

from fastapi接口.log.base_log import official_lot_logger
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from grpc获取动态.grpc.bapi.biliapi import get_lot_notice
from grpc获取动态.grpc.grpc_api import bili_grpc
from utl.pushme.pushme import pushme
import time
from opus新版官方抽奖.Model.OfficialLotModel import LotDetail
from opus新版官方抽奖.转发抽奖.生成专栏信息 import GenerateOfficialLotCv
import pandas as pd
import threading
import os
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import json
import asyncio
from grpc获取动态.src.DynObjectClass import dynAllDetail
from utl.代理.request_with_proxy import request_with_proxy
from grpc获取动态.src.SqlHelper import grpc_sql_helper


class ExctractOfficialLottery:
    def __init__(self):
        self.BiliGrpc = bili_grpc
        self.__dir = os.path.dirname(os.path.abspath(__file__))
        self.log_path = os.path.join(self.__dir, 'log')
        self.result_path = os.path.join(self.__dir, 'result')
        if not os.path.exists(self.log_path):
            os.mkdir(self.log_path)
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)
        self.oringinal_official_lots: [dict] = []

        self.all_offcial_lots: [dict] = []  # 所有的抽奖
        self.last_update_offcial_lots: [dict] = []  # 最后一次更新的抽奖
        self.list_append_lock = threading.Lock()
        self.csv_sep_letter = '\t\t\t\t\t'

        self.stop_flag = False
        self.stop_flag_lock = threading.Lock()

        self.sql = grpc_sql_helper
        self.proxy_request = request_with_proxy()
        self.log = official_lot_logger
        self.__no_lot_timer = 0
        self.__no_lot_timer_lock = threading.Lock()
        self.limit_no_lot_times = 3000  # 3000个rid没有得到抽奖信息就退出
        self.limit_lot_ts = 3 * 3600  # 只获取到离当前时间3个小时前的抽奖
        self.set_latest_lot_time_lock = threading.Lock()
        self.latest_lot_time = 0
        self.latest_rid = 0

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
            "user-agent": "Mozilla/5.0",
        }

    def _get_dynamic_created_ts_by_dynamic_id(self, dynamic_id) -> int:
        return int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)

    def _timeshift(self, timestamp):
        local_time = time.localtime(timestamp)
        realtime = time.strftime('%Y-%m-%d %H:%M:%S', local_time)
        return realtime

    def write_in_file(self):
        if self.all_offcial_lots:
            df1 = pd.DataFrame(self.all_offcial_lots)
            if os.path.isfile(os.path.join(self.__dir, 'result/全部转发抽奖.csv')):
                df1.to_csv(os.path.join(self.__dir, 'result/全部转发抽奖.csv'), index=False, sep=self.csv_sep_letter)
            else:
                df1.to_csv(os.path.join(self.__dir, 'result/全部转发抽奖.csv'), index=False, mode='a+', header=False,
                           sep=self.csv_sep_letter)

        if self.last_update_offcial_lots:
            df2 = pd.DataFrame(self.last_update_offcial_lots)
            df2.to_csv(os.path.join(self.__dir, 'result/更新的转发抽奖.csv'), index=False, sep=self.csv_sep_letter)

        with open(os.path.join(self.__dir, 'idsstart.txt'), 'w', encoding='utf-8') as f:
            f.write(str(self.latest_rid))

    async def update_lot_notice(self, original_lot_notice: [dict]) -> [dict]:
        """
        更新抽奖
        :param original_lot_notice:
        :return: 更新抽奖
        """

        async def solve_lot_data(lot_data):
            """

            :param lot_data:
            """
            newly_lot_resp = await get_lot_notice(
                business_type=lot_data['business_type'],
                business_id=lot_data['business_id'],
                origin_dynamic_id=lot_data['business_id'],
            )
            newly_lotData = newly_lot_resp.get('data', {})

            if newly_lotData:
                await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                    newly_lotData,
                    extra_routing_key="ExctractOfficialLottery.update_lot_notice.solve_lot_data"
                )

                async with data_lock:
                    newly_updated_lot_data.append(newly_lotData)
            else:
                self.log.critical(f'获取到空数据，可能是api接口问题，请检查！使用原始抽奖数据！！！{lot_data}')
                newly_updated_lot_data.append(lot_data)

        self.log.info(f'开始更新抽奖，共计{len(original_lot_notice)}条抽奖需要更新，开始重新通过b站api获取抽奖数据！')
        data_lock = asyncio.Lock()
        newly_updated_lot_data = []
        thread_num = 50
        task_list = []
        for idx in range(len(original_lot_notice) // thread_num + 1):
            task_data = original_lot_notice[idx * thread_num:(idx + 1) * thread_num]
            for da in task_data:
                task = solve_lot_data(da)
                task_list.append(task)
        await asyncio.gather(*task_list)

        return newly_updated_lot_data

    async def get_lot_dict(self, all_lots: [LotDetail], latest_lots_judge_ts=20 * 3600, is_api_update: bool = True) -> \
            tuple[
                list[dict], list[dict], list[dict], list[dict]]:
        """
        获取最新的抽奖的dict
        :param latest_lots_judge_ts: 判断更新抽奖的间隔时间
        :param all_lots:数据库的抽奖信息
        :return: 所有官方抽奖，最后更新的官方抽奖 , 所有充电抽奖,最后更新的充电抽奖
        """
        update_lots_lot_ids = [int(x['lottery_id']) for x in all_lots if
                               (int(time.time()) - int(x['ts']))
                               <= latest_lots_judge_ts]  # x['ts'] 是api请求之后生成的时间戳
        # 获取到的更新抽奖的lot_id
        if len(update_lots_lot_ids) == len(all_lots):
            update_lots_lot_ids = []
        if is_api_update:
            freshed_all_lot_datas = await self.update_lot_notice(all_lots)  # 更新抽奖
        else:
            freshed_all_lot_datas = all_lots
        self.log.info(f'更新完成，当前抽奖剩余{len(freshed_all_lot_datas)}条')
        all_lot_official_data = [x for x in freshed_all_lot_datas if
                                 x['status'] != 2 and x['status'] != -1 and x['business_type'] == 1]
        latest_updated_official_lot_data = [x for x in all_lot_official_data if
                                            int(x['lottery_id']) in update_lots_lot_ids]
        all_lot_charge_data = [x for x in freshed_all_lot_datas if
                               x['status'] != 2 and x['status'] != -1 and x['business_type'] == 12]
        latest_updated_charge_lot_data = [x for x in all_lot_charge_data if int(x['lottery_id']) in update_lots_lot_ids]
        df1 = pd.DataFrame(all_lot_official_data)
        df1.to_csv(os.path.join(self.__dir, 'log/全部官抽.csv'), index=False, header=True)
        df2 = pd.DataFrame(latest_updated_official_lot_data)
        df2.to_csv(os.path.join(self.__dir, 'log/更新官抽.csv'), index=False, header=True)
        df3 = pd.DataFrame(all_lot_charge_data)
        df3.to_csv(os.path.join(self.__dir, 'log/全部充电.csv'), index=False, header=True)
        df4 = pd.DataFrame(latest_updated_charge_lot_data)
        df4.to_csv(os.path.join(self.__dir, 'log/更新充电.csv'), index=False, header=True)

        return all_lot_official_data, latest_updated_official_lot_data, all_lot_charge_data, latest_updated_charge_lot_data

    async def resolve_dynamic_details_card(self, dynData):
        temp_rid = dynData.get('extend').get('businessId')
        dynamic_id = dynData.get('extend').get('dynIdStr')
        dynamic_calculated_ts = int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)
        dynamic_created_time = self._timeshift(dynamic_calculated_ts)  # 通过公式获取大致的时间，误差大概20秒左右
        moduels = dynData.get('modules')
        lot_id = None
        if dynData.get('extend').get('origDesc'):
            for descNode in dynData.get('extend').get('origDesc'):
                if descNode.get('type') == 'desc_type_lottery':
                    lot_id = descNode.get('rid')
                    lot_rid = dynData.get('extend').get('businessId')
                    lot_notice_res = await get_lot_notice(business_type=2, business_id=lot_rid,
                                                          origin_dynamic_id=dynamic_id)
                    lot_data = lot_notice_res.get('data')
                    if lot_data:
                        lot_id = lot_data.get('lottery_id')
        return temp_rid, lot_id, dynamic_id, dynamic_created_time

    def get_repost_count(self, dynamic_id):
        dyn_detail = self.sql.get_all_dynamic_detail_by_dynamic_id(dynamic_id)
        if not dyn_detail.get('dynData'):
            return 114514
        dyn_data = json.loads(dyn_detail.get('dynData'), strict=False)
        repost_count = 0
        for module in dyn_data.get('modules'):
            if module.get('moduleType') == 'module_stat':
                if module.get('moduleStat').get('repost'):
                    repost_count = module.get('moduleStat').get('repost')
            if module.get('moduleButtom'):
                if module.get('moduleButtom').get('moduleStat'):
                    if module.get('moduleButtom').get('moduleStat').get('repost'):
                        repost_count = module.get('moduleButtom').get('moduleStat').get('repost')
        return repost_count

    def construct_lot_detail(self, lot_data_list: [dict], get_repost_count_flag: bool) -> list[LotDetail]:
        ret_list = []
        need_keys = [
            'lottery_id',
            'lottery_time',
            'first_prize',
            'second_prize',
            'third_prize',
            'first_prize_cmt',
            'second_prize_cmt',
            'third_prize_cmt'
        ]
        for lot_data in lot_data_list:
            if not all(key in lot_data.keys() for key in need_keys):
                self.log.error(
                    f'lot_data:{lot_data} is not complete! missing key:{[key for key in need_keys if key not in lot_data.keys()]}')
            self.log.info(f'Constructing:{lot_data}')
            lottery_id = lot_data.get('lottery_id', '')
            dynamic_id = lot_data.get('dynamic_id') or lot_data.get('business_id')
            lottery_time = lot_data.get('lottery_time', 0)
            first_prize = lot_data.get('first_prize', 0)
            second_prize = lot_data.get('second_prize', 0)
            third_prize = lot_data.get('third_prize', 0)
            first_prize_cmt = lot_data.get('first_prize_cmt', '')
            second_prize_cmt = lot_data.get('second_prize_cmt', '')
            third_prize_cmt = lot_data.get('third_prize_cmt', '')
            if get_repost_count_flag:
                participants = self.get_repost_count(dynamic_id)
            else:
                participants = lot_data.get('participants', 0)
            result = LotDetail(
                lottery_id,
                dynamic_id,
                lottery_time,
                first_prize,
                second_prize,
                third_prize,
                first_prize_cmt,
                second_prize_cmt,
                third_prize_cmt,
                participants
            )
            ret_list.append(result)
        return ret_list

    async def get_and_update_all_details_by_dynamic_id_list(self, all_dynamic_ids: [int]):
        async def thread_get_details(dynamic_ids):
            """
            需要放进thread里面跑
            :param dynamic_ids:
            :return:
            """
            ret_dict_list = []
            resp_list = await self.BiliGrpc.grpc_api_get_DynDetails(dynamic_ids)
            if resp_list.get('list'):
                for resp_data in resp_list['list']:
                    temp_rid, lot_id, dynamic_id, dynamic_created_time = self.resolve_dynamic_details_card(
                        resp_data)
                    tempdetail_dict = dynAllDetail(
                        rid=temp_rid,
                        dynamic_id=dynamic_id,
                        dynData=resp_data,
                        lot_id=lot_id if lot_id else None,
                        dynamic_created_time=dynamic_created_time
                    )
                    ret_dict_list.append(tempdetail_dict.__dict__)
            for detail in ret_dict_list:
                self.sql.upsert_DynDetail(doc_id=detail.get('rid'), dynamic_id=detail.get('dynamic_id'),
                                          dynData=detail.get('dynData'), lot_id=detail.get('lot_id'),
                                          dynamic_created_time=detail.get('dynamic_created_time'))

        task_args_list = []  # [[1,2,3,4,5,6,7,8],[9,10,11,12,13,14,15],...]
        offset = 10
        for rid_index in range(len(all_dynamic_ids) // offset + 1):
            rids_list = all_dynamic_ids[offset * rid_index:offset * (rid_index + 1)]
            task_args_list.append(rids_list)

        thread_num = 50
        task_list = []
        for task_index in range(len(task_args_list) // thread_num + 1):
            args_list = task_args_list[
                        thread_num * task_index:thread_num * (task_index + 1)]  # 将task切片成[[0...49],[50....99]]
            print(f'args_list:{args_list}')
            for args in args_list:
                print(args)
                if not args[0]:
                    continue
                task = asyncio.create_task(thread_get_details(args))
                task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_all_lots(self, latest_lots_judge_ts=20 * 3600, is_api_update: bool = True) -> tuple[
        List[LotDetail], List[LotDetail], List[LotDetail], List[LotDetail]]:
        """
        已经排除了开奖了的和失效了的抽奖了
        :return: 所有官方抽奖，最后更新的官方抽奖 , 所有充电抽奖,最后更新的充电抽奖
        """
        all_official_lots_undrawn = self.sql.get_official_and_charge_lot_not_drawn()
        all_lot_official_data, latest_updated_official_lot_data, all_lot_charge_data, latest_updated_charge_lot_data = \
            await self.get_lot_dict(
                all_official_lots_undrawn,
                latest_lots_judge_ts,
                is_api_update=is_api_update
            )  # 更新抽奖信息
        official_lot_dynamic_ids = [x['business_id'] for x in all_lot_official_data if x['status'] != 2]
        charge_lot_dynamic_ids = [x['business_id'] for x in all_lot_charge_data if x['status'] != 2]
        if is_api_update:
            await self.get_and_update_all_details_by_dynamic_id_list(
                [official_lot_dynamic_ids.extend(charge_lot_dynamic_ids)]
            )  # 更新抽奖的动态

        all_official_lot_detail_result: list[LotDetail] = self.construct_lot_detail(all_lot_official_data, True)
        all_official_lot_detail: list[LotDetail] = [x for x in all_official_lot_detail_result]
        latest_official_lot_dynamic_ids = [x['business_id'] for x in latest_updated_official_lot_data]
        latest_official_lot_detail: list[LotDetail] = [x for x in all_official_lot_detail if
                                                       x.dynamic_id in latest_official_lot_dynamic_ids]

        all_charge_lot_detail: list[LotDetail] = self.construct_lot_detail(all_lot_charge_data, False)
        latest_charge_lot_dynamic_ids = [x['business_id'] for x in latest_updated_charge_lot_data]
        latest_charge_lot_detail: list[LotDetail] = [x for x in all_charge_lot_detail if
                                                     x.dynamic_id in latest_charge_lot_dynamic_ids]

        return all_official_lot_detail, latest_official_lot_detail, all_charge_lot_detail, latest_charge_lot_detail

    async def main(
            self,
            latest_lots_judge_ts: int = 20 * 3600,
            force_push: bool = False,
            debug_mode: bool = False
    ) -> tuple[list[LotDetail], list[LotDetail]]:
        """
         函数入口
        :param debug_mode:
        :param latest_lots_judge_ts:
        :param force_push: 是否强制推送
        :return:
        """
        # from grpc获取动态.src.getDynDetail import dynDetailScrapy
        # d = dynDetailScrapy()
        # d.main()# 爬取最新的动态
        self.log.debug(f'开始提取官方抽奖和充电抽奖专栏信息！')
        all_official_lot_detail, latest_official_lot_detail, all_charge_lot_detail, latest_charge_lot_detail = await self.get_all_lots(
            latest_lots_judge_ts)  # 获取并更新抽奖信息！
        if debug_mode:
            return latest_official_lot_detail, latest_charge_lot_detail
        ua3 = gl.get_value('ua3')
        csrf3 = gl.get_value('csrf3')  # 填入自己的csrf
        cookie3 = gl.get_value('cookie3')
        buvid3 = gl.get_value('buvid3_3')
        gc = GenerateOfficialLotCv(cookie3, ua3, csrf3, buvid3)
        # gc.post_flag = False  # 不直接发布
        fabu_text = ''
        # if latest_official_lot_detail or force_push:

        gc.official_lottery(all_official_lot_detail, latest_official_lot_detail)  # 官方抽奖
        fabu_text += '官方抽奖专栏\n'
        # if latest_charge_lot_detail or force_push:
        gc.charge_lottery(all_charge_lot_detail, latest_charge_lot_detail)  # 充电抽奖
        fabu_text += '充电抽奖专栏\n'
        if fabu_text:
            fabu_text = '已发布专栏：\n' + fabu_text
        else:
            fabu_text = '更新内容为空，不发布专栏，去检查日志是否有问题！\n'
        self.log.error(fabu_text)
        pushme('官方抽奖和充电抽奖已更新',
               f'{fabu_text}官方抽奖：'
               f'距离上次更新抽奖时间为：{round(latest_lots_judge_ts / 3600, 2)}小时！'
               f'{len(all_official_lot_detail)}个，最后更新的：{len(latest_official_lot_detail)}个'
               f'\n充电抽奖：{len(all_charge_lot_detail)}个，最后更新的：{len(latest_charge_lot_detail)}个'
               f'\n更新内容：\n{[x.__dict__ for x in latest_official_lot_detail]}\n{[x.__dict__ for x in latest_charge_lot_detail]}')

        return latest_official_lot_detail, latest_charge_lot_detail

    async def save_article(self, latest_lots_judge_ts: int = 20 * 3600, abstract: str = ''):
        self.log.debug(f'开始提取官方抽奖和充电抽奖专栏信息！')
        all_official_lot_detail, latest_official_lot_detail, all_charge_lot_detail, latest_charge_lot_detail = await self.get_all_lots(
            latest_lots_judge_ts,
            is_api_update=False
        )  # 获取并更新抽奖信息！
        gc = GenerateOfficialLotCv('', '', '', '', abstract=abstract)
        gc.official_lottery(all_official_lot_detail, latest_official_lot_detail)  # 官方抽奖
        gc.charge_lottery(all_charge_lot_detail, latest_charge_lot_detail)  # 充电抽奖
        return latest_official_lot_detail, latest_charge_lot_detail


if __name__ == '__main__':
    __e = ExctractOfficialLottery()
    asyncio.run(__e.main())
