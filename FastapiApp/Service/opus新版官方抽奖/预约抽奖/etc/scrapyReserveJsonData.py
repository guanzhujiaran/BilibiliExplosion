# -*- coding: utf-8 -*-
import asyncio
import os
import time
from dataclasses import dataclass
from functools import reduce
from typing import AsyncGenerator
import aiofiles
import pandas

from Utils.CommMethods import methods
from dao.commStorageRedisObj import comm_storage_redis_obj
from log.base_log import reserve_lot_logger
from Models.base.custom_pydantic import CustomBaseModelHashable
from Service.BaseCrawler.CrawlerType import UnlimitedCrawler
from Service.BaseCrawler.model.base import WorkerStatus, WorkerModel
from Service.BaseCrawler.plugin.statusPlugin import StatsPlugin, SequentialNullStopPlugin
from Service.GrpcModule.Grpc.Bapi.BiliApi import reserve_relation_info
from Service.opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter, ProgressCounter
from Service.opus新版官方抽奖.预约抽奖.db.models import TReserveRoundInfo, TUpReserveRelationInfo
from Service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper
from Utils.Common import asyncio_gather

BAPI = methods()


class SuccCounter(BaseSuccCounter):
    first_reserve_id = 0
    latest_reserve_id: int = 0  # 最后的rid
    latest_succ_reserve_id: int = 0  # 最后获取成功的动态id


@dataclass
class DynamicTimestampInfo:
    dynamic_timestamp: int = 0
    ids: int = 0

    def get_time_str_until_now(self):
        return self.seconds_to_hms(int(time.time()) - self.dynamic_timestamp)

    def seconds_to_hms(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}小时{minutes:02d}分{secs:02d}秒"


class ReserveParams(CustomBaseModelHashable):
    reserve_id: int = 0

    def __hash__(self):
        return hash(self.reserve_id)


class ReserveScrapyRobot(UnlimitedCrawler[ReserveParams]):
    async def on_run_end(self, end_param):
        """
            退出时必定执行
        """
        reserve_lot_logger.critical(f'开始将日志写入文件')
        await self.write_in_file()
        reserve_lot_logger.critical(f'日志写入文件完成')
        reserve_lot_logger.critical(f'开始获取本轮统计信息')
        latest_reserve_lots = await self.generate_update_reserve_lotterys_by_round_id(self.now_round_id)
        new_round_info = TReserveRoundInfo(
            round_id=self.now_round_id,
            is_finished=True,
            round_start_ts=self.round_start_ts,
            round_add_num=self.totoal_count1 + self.totoal_count2 - 1 - self.none_num1 - self.none_num2,
            round_lot_num=len(latest_reserve_lots),
        )
        await self.sqlHelper.add_reserve_round_info(new_round_info)
        reserve_lot_logger.critical(f'本轮统计信息获取结束')
        reserve_lot_logger.critical(f'开始刷新未开奖的预约抽奖')
        await self.refresh_not_drawn_lottery()
        reserve_lot_logger.critical(f'刷新未开奖的预约抽奖结束')
        if os.path.exists(self.unknown):
            await self.file_remove_repeat_contents(self.unknown)
        if os.path.exists(self.getfail):
            await self.file_remove_repeat_contents(self.getfail)
        reserve_lot_logger.info(f'共{self.stats_plugin.processed_items_count}次获取动态'
                                f'其中{self.stats_plugin.succ_count} 个有效动态')
        await super().on_run_end(end_param)

    async def is_stop(self) -> bool:
        async with self.dynamic_ts_lock:
            if int(time.time()) - self.dynamic_timestamp.dynamic_timestamp <= self.EndTimeSeconds:  # 如果超过了最大data
                self.encounter_end_time_seconds_times += 1
                if self.encounter_end_time_seconds_times > 10 and self.null_stop_plugin.sequential_null_count > 30:
                    return True
                else:
                    return False
            else:
                reserve_lot_logger.debug(
                    f"最近的预约时间间隔过长{self.dynamic_timestamp.get_time_str_until_now()}")
        return False

    async def key_params_gen(self, params: ReserveParams) -> AsyncGenerator[ReserveParams, None]:
        reserve_id = params.reserve_id
        while 1:
            reserve_id += 1
            yield ReserveParams(reserve_id=reserve_id)

    async def handle_fetch(self, params: ReserveParams) -> WorkerStatus:
        return await self.resolve_reserve(params.reserve_id)

    def __init__(self):
        # region 统计类数据
        self.totoal_count2 = 0
        self.totoal_count1 = 0
        self.none_num2 = 0
        self.none_num1 = 0
        self.round_start_ts = 0
        # endregion

        self.sem_limit = 1  # 因为用的是自己的代理，所以速度可以慢点
        self.stats_plugin = StatsPlugin(self)
        self.null_time_quit = 10000  # 遇到连续n条data为None的树据 则退出
        self.null_stop_plugin = SequentialNullStopPlugin(self, self.null_time_quit)
        super().__init__(
            plugins=[self.stats_plugin, self.null_stop_plugin],
            max_sem=self.sem_limit,
            _logger=reserve_lot_logger
        )

        self._use_custom_proxy = True
        self._is_use_available_proxy = False  # 是否套用急需完成的api的那套设置
        self.sqlHelper = bili_reserve_sqlhelper
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.now_round_id = 0
        self.ids_list:list[ReserveParams] = []
        self.ids_change_lock = asyncio.Lock()
        self.EndTimeSeconds = 3 * 3600  # 提前多久退出爬动态 （现在不应该按照这个作为退出的条件，因为预约现在有些是乱序排列的，所以应该以data为None作为判断标准）
        self.encounter_end_time_seconds_times = 0
        self.rollback_num = 100  # 获取完之后的回滚数量
        self.dynamic_ts_lock = asyncio.Lock()
        self.highlight_word_list = ['jd卡', '京东卡', '红包', '主机', '显卡', '电脑', '天猫卡', '猫超卡', '现金',
                                    '见盘', '耳机', '鼠标', '手办', '景品', 'ps5', '内存', '风扇', '散热', '水冷',
                                    '主板', '电源', '机箱', 'fgo'
            , '折现', '樱瞳', '盈通', '🧧', '键盘']  # 需要重点查看的关键词列表
        self.list_type_wrong = list()  # 出错动态内容
        self.list_deleted_maybe = list()  # 可能动态内容
        self.reserve_params: ReserveParams | None = None
        self.dynamic_timestamp: DynamicTimestampInfo = DynamicTimestampInfo()
        self.unknown = os.path.join(self.current_dir, 'log/未知类型.csv')  # 未知类型
        self.getfail = os.path.join(self.current_dir, 'log/获取失败.csv')  # 获取失败
        # 文件
        self.list_getfail = list()
        self.list_unknown = list()
        # 内容
        self.file_list_lock = asyncio.Lock()

        self.refresh_progress_counter: ProgressCounter | None = None

    async def write_in_file(self):
        async def my_write(path_name, content_list: list, write_mode='a+'):
            async with aiofiles.open(path_name, mode=write_mode, encoding='utf-8') as f:
                await f.writelines('\n'.join(str(i) for i in content_list))

            content_list.clear()

        if self.list_getfail:
            await my_write(self.getfail, self.list_getfail)
        if self.list_unknown:
            await my_write(self.unknown, self.list_unknown)

    async def resolve_reserve(self, sid: int, is_refresh=False) -> WorkerStatus:
        result = await self.resolve_reserve_by_sid(sid, is_refresh=is_refresh)
        if self.refresh_progress_counter and self.refresh_progress_counter.is_running:
            self.refresh_progress_counter.succ_count += 1
        return result

    async def resolve_reserve_by_sid(self, sid: int, is_refresh=False) -> WorkerStatus:
        '''
        解析动态json，然后以dict存到对应list里面
        :param is_refresh:
        :param sid:
        :return:
        '''
        is_force_api = False
        while 1:
            if not is_refresh:
                has_reserve_relation_ids = await self.sqlHelper.get_reserve_by_ids(sid)
                round_id = self.now_round_id
            else:  # 如果是刷新
                has_reserve_relation_ids = None
                round_id = None
            if not is_force_api and has_reserve_relation_ids and has_reserve_relation_ids.code == 0 and has_reserve_relation_ids.sid is not None:
                req1_dict = has_reserve_relation_ids.raw_JSON
            else:
                req1_dict = await reserve_relation_info(
                    sid,
                )
                req1_dict.update({'ids': sid})
                await self.sqlHelper.add_reserve_info_by_resp_dict(req1_dict, round_id)  # 添加预约json到数据库
            if is_refresh:
                return WorkerStatus.complete
            async with self.file_list_lock:
                dynamic_data_dict = req1_dict
                try:
                    dycode = req1_dict.get('code')
                except Exception as e:
                    dycode = 404
                    reserve_lot_logger.info(f'code获取失败{req1_dict}')
                self.code_check(dycode)
                dymsg = req1_dict.get('msg')
                dymessage = req1_dict.get('message')
                dydata = req1_dict.get('data')
                if dydata is None:
                    return WorkerStatus.nullData
                if dycode == 404:
                    reserve_lot_logger.info(f'{dycode}\n {dymsg}\n {dymessage}')
                    self.list_getfail.append(dynamic_data_dict)
                    self.code_check(dycode)
                    return WorkerStatus.fail
                if dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
                    self.list_deleted_maybe.append(dynamic_data_dict)
                    self.code_check(dycode)
                    return WorkerStatus.nullData
                if dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
                    self.list_deleted_maybe.append(dynamic_data_dict)
                    self.code_check(dycode)
                    return WorkerStatus.complete
                if dycode == 0:
                    try:
                        if str(sid) not in [str(x) for x in list(dydata.get('list', {}).keys())]:
                            reserve_lot_logger.critical(
                                f"\n\t\t\t\t第{str(self.stats_plugin.processed_items_count)}次获取直播预约\t{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\t\t\t\trid:{sid}\n直播预约[{sid}]获取失败，响应不匹配！"
                                f"{req1_dict}")
                            is_force_api = True  # 强制使用api获取数据，不信任数据库内数据了
                            continue
                        dynamic_timestamp = dynamic_data_dict.get('data').get('list').get(str(sid)).get('stime')
                        async with self.dynamic_ts_lock:
                            if sid > self.dynamic_timestamp.ids and dynamic_timestamp:
                                self.dynamic_timestamp.dynamic_timestamp = dynamic_timestamp
                                self.dynamic_timestamp.ids = sid
                        reserve_lot_logger.info(
                            f"\n\t\t\t\t第{str(self.stats_plugin.processed_items_count)}次获取直播预约\t{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\t\t\t\trid:{sid}\n直播预约[{sid}]获取成功，直播预约创建时间：{BAPI.timeshift(self.dynamic_timestamp.dynamic_timestamp)}")
                    except Exception as e:
                        reserve_lot_logger.exception(
                            f'{e}\n\t\t\t\t第{self.stats_plugin.processed_items_count}次获取直播预约\t' + time.strftime(
                                '%Y-%m-%d %H:%M:%S',
                                time.localtime()) +
                            '\t\t\t\trid:{}'.format(sid) + '\n' +
                            f'直播预约失效，被删除:{req1_dict}\n当前已经有{self.null_stop_plugin.sequential_null_count}条data为None的sid'
                        )
                    self.code_check(dycode)
                    return WorkerStatus.complete
                if dycode == -412:
                    self.code_check(dycode)
                    reserve_lot_logger.info(req1_dict)
                    self.list_getfail.append(dynamic_data_dict)
                    return WorkerStatus.fail
                if dycode != 0:
                    self.list_unknown.append(dynamic_data_dict)
                return WorkerStatus.fail

    def code_check(self, dycode):
        """
        没问题的业务码就返回0，有问题的返回非0
        """
        if dycode == 0:
            return 0
        if dycode == 404:
            reserve_lot_logger.critical(f'未知类型代码{dycode}')
            return 0
        if dycode == 500205:
            return 0
        else:
            reserve_lot_logger.critical(f'未知类型代码：{dycode}')
        if dycode == -412:
            return -412
        elif dycode != 'None' and dycode != 500207 and \
                dycode != 500205 and dycode != 404 and dycode != -412 and self.dynamic_timestamp.dynamic_timestamp != 'None':
            pass

    def remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    async def main(self):
        await self._params_init()
        now_round: TReserveRoundInfo = await self.sqlHelper.get_latest_reserve_round()
        self.round_start_ts = int(time.time()) if now_round.is_finished else now_round.round_start_ts
        self.now_round_id = now_round.round_id + 1 if now_round.is_finished else now_round.round_id
        self.none_num1 = 0
        self.totoal_count1 = 0
        for ids_index in range(len(self.ids_list)):
            self.none_num1 = self.null_stop_plugin.sequential_null_count if int(
                time.time()) - self.dynamic_timestamp.dynamic_timestamp < self.EndTimeSeconds else - self.null_time_quit
            async with self.ids_change_lock:
                self.reserve_params = self.ids_list[ids_index]
            async with self.dynamic_ts_lock:
                self.dynamic_timestamp = DynamicTimestampInfo()
            await self.run(self.ids_list[ids_index])
            self.reserve_params = self.stats_plugin.end_params  # 加上这个才是最终的ids，否则ids并不会改变
            self.totoal_count1 = self.stats_plugin.succ_count
            self.ids_list[ids_index] = self.reserve_params
            reserve_lot_logger.critical(
                f'{self.reserve_params}已经达到{self.null_stop_plugin.sequential_null_count}/{self.null_time_quit}条data为null信息或者最近预约时间只剩'
                f'{self.dynamic_timestamp.get_time_str_until_now()}\n'
                f'最终成功的ids：http://api.bilibili.com/x/activity/up/reserve/relation/info?ids={self.stats_plugin.end_success_params}\n'
                f'最终ids: http://api.bilibili.com/x/activity/up/reserve/relation/info?ids={self.stats_plugin.end_params}\n'
            )
        none_num2 = self.null_stop_plugin.sequential_null_count if int(
            time.time()) - self.dynamic_timestamp.dynamic_timestamp < self.EndTimeSeconds else - self.null_time_quit
        self.totoal_count2 = self.stats_plugin.succ_count
        finnal_rid_list = [
            str(self.ids_list[0].reserve_id - self.rollback_num - self.none_num1),
            str(self.ids_list[1].reserve_id - self.rollback_num - self.none_num2)
        ]
        reserve_lot_logger.critical(
            f'{self.ids_list}已经达到{self.null_stop_plugin.sequential_null_count}/{self.null_time_quit}条data为null信息或者最近预约时间只剩'
            f'{self.dynamic_timestamp.get_time_str_until_now()}秒，'
            f'ids：{self.dynamic_timestamp.ids}，退出！'
            f'当前rid记录分别回滚{self.rollback_num + self.none_num1}和{self.rollback_num + none_num2}条'
            f'最终写入文件rid记录：{finnal_rid_list}')
        reserve_lot_logger.critical(f'开始设置结束rid')
        await comm_storage_redis_obj.set_val(
            comm_storage_redis_obj.RedisMap.reserve_scrapy_bot_rid_ls,
            "\n".join(
                finnal_rid_list)
        )
        reserve_lot_logger.critical(f'结束rid设置完成')

    async def generate_update_reserve_lotterys_by_round_id(self, round_id) -> list[TUpReserveRelationInfo]:
        """
        获取特定round更新的预约抽奖并写入文件，如果本次round更新的抽奖数量为0,则报错退出！
        :return:
        """
        exclude_attrs = ['new_field', 'reserve_round', 'reserve_round_id',
                         'raw_JSON']
        latest_reserve_lottery = await self.sqlHelper.get_reserve_lotterys_by_round_id(round_id)
        newly_updated_reserve_list = self.sqlHelper.SqlAlchemyObjList2DictList(
            latest_reserve_lottery,
            TUpReserveRelationInfo,
            exclude_attrs
        )
        if not os.path.exists(os.path.join(self.current_dir, 'result')):
            os.mkdir(os.path.join(self.current_dir, 'result'))
        newly_updated_reserve_file_name = os.path.join(self.current_dir, 'result/最后一次更新的直播预约抽奖.csv')
        if len(newly_updated_reserve_list) == 0:
            reserve_lot_logger.error('更新抽奖数量为0，检查代码！')
        df = pandas.DataFrame(newly_updated_reserve_list)
        open(newly_updated_reserve_file_name, 'w').close()
        df.to_csv(newly_updated_reserve_file_name, header=True, encoding='utf-8', index=False, sep='\t')
        return newly_updated_reserve_list

    async def file_remove_repeat_contents(self, filename: str):
        s = set()
        l = []
        async with aiofiles.open(filename, "r", encoding="utf-8") as f:
            for line in await f.readlines():
                line = line.strip()
                if line not in s:
                    s.add(line)
                    l.append(line)
        if l:
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                for line in l:
                    await f.write(line + "\n")

    async def refresh_not_drawn_lottery(self):
        self.refresh_progress_counter = ProgressCounter()
        all_not_drawn_reserve_lottery = await self.sqlHelper.get_all_undrawn_reserve_lottery()
        all_num = len(all_not_drawn_reserve_lottery)
        self.refresh_progress_counter.total_num = all_num
        running_num = 0
        reserve_lot_logger.debug(f'开始刷新未开奖的预约内容，共计{all_num}条')
        task_list = []
        for reserve_lottery in all_not_drawn_reserve_lottery:
            task = asyncio.create_task(self.resolve_reserve(reserve_lottery.sid, is_refresh=True))
            task_list.append(task)
            running_num += 1
        await asyncio_gather(*task_list, log=self.log)
        self.refresh_progress_counter.is_running = False

    async def _params_init(self):
        '''
        初始化信息
        :return:
        '''
        if not os.path.exists(os.path.join(self.current_dir, 'log')):
            os.mkdir(os.path.join(self.current_dir, 'log'))

        try:
            if file_contents := await comm_storage_redis_obj.get_val(
                    comm_storage_redis_obj.RedisMap.reserve_scrapy_bot_rid_ls):
                self.ids_list = [ReserveParams(reserve_id=int(x)) for x in file_contents.split('\n')]
                self.reserve_params = self.ids_list[0]
            else:
                self.ids_list = [1871812, 4996187]
                reserve_lot_logger.info(f'获取rid开始文件失败，使用默认值：{self.reserve_params}')
            reserve_lot_logger.info('获取rid开始文件成功\nids开始值：{}'.format(self.reserve_params))
            if self.reserve_params.reserve_id <= 0:
                reserve_lot_logger.exception(f'rid开始文件内容不正确：{self.ids_list}，使用默认值：{self.reserve_params}')
                self.ids_list = [1871812, 4996187]
        except Exception as e:
            reserve_lot_logger.exception(f'获取rid开始文件失败，使用默认值：{self.reserve_params}')
            self.ids_list = [1871812, 4996187]


reserve_robot = ReserveScrapyRobot()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    rid_run = ReserveScrapyRobot()
    loop.run_until_complete(rid_run.main())
