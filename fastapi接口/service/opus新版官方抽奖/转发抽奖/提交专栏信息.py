import asyncio
import json
import os
import threading
import time
from copy import deepcopy
from typing import List

import pandas as pd

from fastapi接口.log.base_log import official_lot_logger
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.grpc_module.grpc.bapi.biliapi import get_lot_notice
from fastapi接口.service.grpc_module.grpc.grpc_api import bili_grpc
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from fastapi接口.service.grpc_module.src.SQLObject.models import Lotdata
from fastapi接口.service.grpc_module.src.getDynDetail import dyn_detail_scrapy
from fastapi接口.service.opus新版官方抽奖.Model.BaseLotModel import ProgressCounter
from fastapi接口.service.opus新版官方抽奖.Model.GenerateCvModel import CvContent
from fastapi接口.service.opus新版官方抽奖.Model.OfficialLotModel import LotDetail
from fastapi接口.service.opus新版官方抽奖.转发抽奖.生成专栏信息 import GenerateOfficialLotCv
from fastapi接口.utils.Common import asyncio_gather
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from utl.pushme.pushme import pushme


class ExtractOfficialLottery:
    def __init__(self):
        self.BiliGrpc = bili_grpc
        self.__dir = os.path.dirname(os.path.abspath(__file__))
        self.log_path = os.path.join(self.__dir, 'log')
        self.result_path = os.path.join(self.__dir, 'result')
        self.oringinal_official_lots: [dict] = []

        self.all_offcial_lots: [dict] = []  # 所有的抽奖
        self.last_update_offcial_lots: [dict] = []  # 最后一次更新的抽奖
        self.list_append_lock = threading.Lock()
        self.csv_sep_letter = '\t\t\t\t\t'

        self.stop_flag = False
        self.stop_flag_lock = threading.Lock()

        self.sql = grpc_sql_helper
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

        self.refresh_official_lot_progress: ProgressCounter | None = None

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

        with open(os.path.join(self.__dir, 'idsstart'), 'w', encoding='utf-8') as f:
            f.write(str(self.latest_rid))

    async def update_lot_notice(self, original_lot_notice: List[Lotdata]) -> List[Lotdata]:
        """
        更新抽奖
        :param original_lot_notice:
        :return: 更新抽奖
        """

        async def _solve_lot_data(lot_data: Lotdata, rs):
            """

            :param lot_data:
            """
            if lot_data.business_id and lot_data.business_type:
                new_lot_resp = await get_lot_notice(
                    business_type=lot_data.business_type,
                    business_id=lot_data.business_id,
                    origin_dynamic_id=lot_data.business_id,
                )
                new_lot_data_resp = new_lot_resp.get('data', {})

                if new_lot_data_resp:
                    self.log.info(
                        f'获取到新的抽奖数据，推送到upsert_official_reserve_charge_lot消息队列{new_lot_data_resp}')
                    await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                        new_lot_data_resp,
                        extra_routing_key="ExtractOfficialLottery.update_lot_notice.solve_lot_data"
                    )
                    new_lot_data: Lotdata = grpc_sql_helper.process_resp_data_dict_2_lotdata(new_lot_data_resp)
                    new_updated_lot_data.append(new_lot_data)
                else:
                    self.log.critical(f'获取到空数据，可能是api接口问题，请检查！使用原始抽奖数据！！！{lot_data}')
                    new_updated_lot_data.append(lot_data)
                rs['cur_num'] += 1
                self.log.info(f'当前更新了【{rs["cur_num"]}/{rs["total_num"]}】条官方抽奖数据')

        running_status = {
            'total_num': len(original_lot_notice),
            "cur_num": 0
        }
        self.log.info(f'开始更新抽奖，共计{running_status["total_num"]}条抽奖需要更新，开始重新通过b站api获取抽奖数据！')
        new_updated_lot_data = []
        task_list = []
        for da in original_lot_notice:
            task = asyncio.create_task(_solve_lot_data(da, running_status))
            task_list.append(task)
        await asyncio_gather(*task_list, log=official_lot_logger)
        return new_updated_lot_data

    async def get_repost_count(self, dynamic_id):
        dyn_detail = await self.sql.get_all_dynamic_detail_by_dynamic_id(dynamic_id)
        if not dyn_detail or not dyn_detail.dynData:
            return 0
        dyn_data = json.loads(dyn_detail.dynData, strict=False)
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

    async def construct_lot_detail(self, lot_data_list: List[dict], get_repost_count_flag: bool) -> list[LotDetail]:
        ret_list = []
        need_keys = [
            'lottery_id',
            'lottery_time',
            'first_prize',
            'second_prize',
            'third_prize',
            'first_prize_cmt',
            'second_prize_cmt',
            'third_prize_cmt',
            'article_pub_record'
        ]

        async def _construct_lot_detail_bulk(lot_data: dict):
            if not all(key in lot_data.keys() for key in need_keys):
                self.log.error(
                    f'lot_data:{lot_data} is not complete! missing key:{[key for key in need_keys if key not in lot_data.keys()]}')
            self.log.info(f'Constructing:{lot_data}')
            lottery_id = lot_data.get('lottery_id', '')
            dynamic_id = lot_data.get('business_id')
            lottery_time = lot_data.get('lottery_time', 0)
            first_prize = lot_data.get('first_prize', 0)
            second_prize = lot_data.get('second_prize', 0)
            third_prize = lot_data.get('third_prize', 0)
            first_prize_cmt = lot_data.get('first_prize_cmt', '')
            second_prize_cmt = lot_data.get('second_prize_cmt', '')
            third_prize_cmt = lot_data.get('third_prize_cmt', '')
            article_pub_record = lot_data.get('article_pub_record')
            if get_repost_count_flag:
                participants = await self.get_repost_count(dynamic_id)
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
                participants,
                article_pub_record
            )
            ret_list.append(result)

        await asyncio_gather(*[_construct_lot_detail_bulk(x) for x in lot_data_list], log=official_lot_logger)

        return ret_list

    async def get_all_lots(self, is_api_update: bool = True) -> tuple[
        List[LotDetail], List[LotDetail]]:
        """
        已经排除了开奖了的和失效了的抽奖了
        :return: 所有官方抽奖，最后更新的官方抽奖 , 所有充电抽奖,最后更新的充电抽奖
        """

        all_lots_with_no_business_id = await self.sql.get_all_lot_with_no_business_id()
        await asyncio_gather(
            *[
                dyn_detail_scrapy.resolve_dynamic_details_card(json.loads(x.bilidyndetail.dynData, strict=False),
                                                               is_running_scrapy=False) for x in
                all_lots_with_no_business_id
            ],
            log=official_lot_logger)
        all_official_lots_undrawn = await self.sql.get_all_lot_not_drawn()
        if is_api_update:
            async def __(lotdata: Lotdata):
                if not lotdata.bilidyndetail:
                    lot_data_resp = await get_lot_notice(
                        business_type=lotdata.business_type,
                        business_id=lotdata.business_id
                    )
                    if da := lot_data_resp.get('data'):
                        await self.sql.upsert_lot_detail(da)
                    else:
                        self.log.error(
                            f'{sqlalchemy_model_2_dict(lotdata)}lot_data_resp:{lot_data_resp} is not complete!')
                else:
                    await dyn_detail_scrapy.resolve_dynamic_details_card(
                        json.loads(lotdata.bilidyndetail.dynData, strict=False), is_running_scrapy=False)
                self.refresh_official_lot_progress.succ_count += 1

            self.refresh_official_lot_progress = ProgressCounter()
            self.refresh_official_lot_progress.total_num = len(all_official_lots_undrawn)
            await asyncio_gather(
                *[
                    __(x) for x in all_official_lots_undrawn
                ],
                log=official_lot_logger
            )
            self.refresh_official_lot_progress.is_running = False
        all_lot_official_data: List[Lotdata] = [x for x in all_official_lots_undrawn if
                                                x.status != 2 and x.status != -1 and x.business_type == 1]
        all_lot_charge_data: List[Lotdata] = [x for x in all_official_lots_undrawn if
                                              x.status != 2 and x.status != -1 and x.business_type == 12]
        all_official_lot_detail_result: list[LotDetail] = await self.construct_lot_detail(
            [x.__dict__ for x in all_lot_official_data], get_repost_count_flag=is_api_update)
        all_official_lot_detail: list[LotDetail] = deepcopy(all_official_lot_detail_result)
        all_charge_lot_detail: list[LotDetail] = await self.construct_lot_detail(
            [x.__dict__ for x in all_lot_charge_data], False)

        return all_official_lot_detail, all_charge_lot_detail

    async def save_article(self,
                           abstract: str = '',
                           is_api_update: bool = False,
                           save_dir: str = '',
                           pub_cv: bool = True,
                           save_to_local_file: bool = True,
                           ) -> tuple[CvContent, CvContent]:
        """

        :param latest_lots_judge_ts:
        :param abstract:
        :param is_api_update:  是否使用b站api更新一下数据库里的未开奖数据
        :return:
        """
        self.log.debug(f'开始提取官方抽奖和充电抽奖专栏信息！')
        if round_id := await self.sql.get_article_pub_record_round_id():
            round_id = round_id
        else:
            round_id = 1
        all_official_lot_detail, all_charge_lot_detail = await self.get_all_lots(
            is_api_update=is_api_update
        )  # 获取并更新抽奖信息！
        gc = GenerateOfficialLotCv('', '', '', '', abstract=abstract)
        if save_dir:
            gc.save_dir = save_dir
        official_cv_content = await gc.main(
            all_official_lot_detail,
            lot_type="官方抽奖",
            pub_cv=pub_cv,
            save_to_local_file=save_to_local_file
        )  # 官方抽奖
        charge_cv_content = await gc.main(
            all_charge_lot_detail,
            lot_type="充电抽奖",
            pub_cv=pub_cv,
            save_to_local_file=save_to_local_file
        )  # 充电抽奖
        await self.sql.upsert_article_pub_record(
            round_id,
            *[x.dynamic_id for x in all_official_lot_detail if not x.article_pub_record],
            *[x.dynamic_id for x in all_charge_lot_detail if not x.article_pub_record]
        )
        pushme('官方抽奖和充电抽奖已更新',
               f'{len(all_official_lot_detail)}个'
               f'\n充电抽奖：{len(all_charge_lot_detail)}个'
               f'\n更新内容：\n{[x.__dict__ for x in all_official_lot_detail if not x.article_pub_record]}\n{[x.__dict__ for x in all_charge_lot_detail if not x.article_pub_record]}')

        return official_cv_content, charge_cv_content


if __name__ == '__main__':
    __e = ExtractOfficialLottery()
    asyncio.run(__e.get_all_lots(is_api_update=True))
