# -*- coding: utf-8 -*-
# 发生sqlite不能在不同线程运行的时候，将sqlite_utils 里面的check_same_thread改成False
import asyncio
import pandas
from dataclasses import dataclass
from functools import reduce
import sys
from fastapi接口.log.base_log import reserve_lot_logger
from grpc获取动态.grpc.bapi.biliapi import reserve_relation_info
from opus新版官方抽奖.Model.BaseLotModel import BaseSuccCounter
from opus新版官方抽奖.预约抽奖.db.models import TReserveRoundInfo, TUpReserveRelationInfo
from utl.代理.request_with_proxy import request_with_proxy
import time
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import requests
import os
import Bilibili_methods.all_methods
from opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper

BAPI = Bilibili_methods.all_methods.methods()


class SuccCounter(BaseSuccCounter):
    first_reserve_id = 0
    latest_reserve_id: int = 0  # 最后的rid
    latest_succ_reserve_id: int = 0  # 最后获取成功的动态id


@dataclass
class dynamic_timestamp_info:
    dynamic_timestamp: int = 0
    ids: int = 0

    def get_time_str_until_now(self):
        return time.strftime("%H小时%M分钟%S秒", time.gmtime(int(time.time()) - self.dynamic_timestamp))


class ReserveScrapyRobot:
    def __init__(self):
        self.is_running = False
        self.succ_counter = SuccCounter()
        self.sqlHlper = bili_reserve_sqlhelper
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.now_round_id = 0
        self.ids_list = []
        self.ids_change_lock = asyncio.Lock()
        self.quit_lock = asyncio.Lock()
        self.quit_Flag = False
        self.proxy_request = request_with_proxy()
        self.proxy_request.mode = 'rand'
        # {"proxy":{"http":1.1.1.1},"status":"可用|-412|失效","update_ts":time.time(), }
        self.EndTimeSeconds = 3 * 3600  # 提前多久退出爬动态 （现在不应该按照这个作为退出的条件，因为预约现在有些是乱序排列的，所以应该以data为None作为判断标准）
        self.null_time_quit = 150  # 遇到连续100条data为None的sid 则退出
        self.sem_max_val = 50  # 最大同时运行的线程数
        self.sem = asyncio.Semaphore(self.sem_max_val)
        self.null_timer = 0
        self.null_list: list[dict[int:bool]] = []
        self.rollback_num = 100  # 获取完之后的回滚数量
        self.null_timer_lock = asyncio.Lock()
        self.dynamic_ts_lock = asyncio.Lock()
        self.highlight_word_list = ['jd卡', '京东卡', '红包', '主机', '显卡', '电脑', '天猫卡', '猫超卡', '现金',
                                    '见盘', '耳机', '鼠标', '手办', '景品', 'ps5', '内存', '风扇', '散热', '水冷',
                                    '主板', '电源', '机箱', 'fgo'
            , '折现', '樱瞳', '盈通', '🧧', '键盘']  # 需要重点查看的关键词列表
        self.list_type_wrong = list()  # 出错动态内容
        self.list_deleted_maybe = list()  # 可能动态内容
        self.ids = int()
        self.times = 1
        self.btime = 0
        self.n = int()
        self.dynamic_timestamp: dynamic_timestamp_info = dynamic_timestamp_info()
        self.getfail = None  # 文件
        self.unknown = None  # 文件

        # 文件

        self.list_getfail = list()
        self.list_unknown = list()

        # 内容
        self.file_list_lock = asyncio.Lock()

    def write_in_file(self):
        def my_write(path_Name, content_list: list, write_mode='a+'):
            with open(path_Name, mode=write_mode, encoding='utf-8') as f:
                f.writelines('\n'.join(str(i) for i in content_list))

            content_list.clear()

        if self.list_getfail:
            my_write(self.getfail, self.list_getfail)
        if self.list_unknown:
            my_write(self.unknown, self.list_unknown)

    async def resolve_dynamic_with_sem(self, rid: int):
        await self.resolve_dynamic(rid)
        self.sem.release()

    async def resolve_dynamic(self, rid: int):
        '''
        解析动态json，然后以dict存到对应list里面
        :param rid:
        :return:
        '''
        self.succ_counter.latest_reserve_id = rid
        has_reserve_relation_ids = await self.sqlHlper.get_reserve_by_ids(rid)
        if has_reserve_relation_ids and has_reserve_relation_ids.code == 0 and has_reserve_relation_ids.sid != None:
            req1_dict = has_reserve_relation_ids.raw_JSON
        else:
            req1_dict = await reserve_relation_info(rid)
            req1_dict.update({'ids': rid})
            await self.sqlHlper.add_reserve_info_by_resp_dict(req1_dict, self.now_round_id)  # 添加预约json到数据库

        async with self.file_list_lock:
            dynamic_data_dict = req1_dict
            try:
                dycode = req1_dict.get('code')
            except Exception as e:
                dycode = 404
                reserve_lot_logger.info(f'code获取失败{req1_dict}')
            self.code_check(dycode)
            self.times += 1
            dymsg = req1_dict.get('msg')
            dymessage = req1_dict.get('message')
            dydata = req1_dict.get('data')
            if dydata is None:
                async with self.null_timer_lock:
                    self.null_timer += 1
                    reserve_lot_logger.info(
                        '\n\t\t\t\t第' + str(self.times) + '次获取直播预约\t' + time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                              time.localtime()) +
                        '\t\t\t\trid:{}'.format(rid) + '\n'
                        + f'当前已经有{self.null_timer}条data为None的sid，最近的动态时间距离现在{self.dynamic_timestamp.get_time_str_until_now()}！')
                    list(filter(lambda x: list(x.keys())[0] == rid, self.null_list))[0].update({rid: False})
                if await self.check_null_timer(self.null_time_quit):
                    async with self.null_timer_lock:
                        async with self.dynamic_ts_lock:
                            if int(time.time()) - self.dynamic_timestamp.dynamic_timestamp <= self.EndTimeSeconds:  # 如果超过了最大data
                                if self.null_timer > 1000:
                                    await self.quit()
                            else:
                                reserve_lot_logger.debug(
                                    f"当前null_timer（{self.null_timer}）没满{self.null_time_quit}或最近的预约时间间隔过长{self.dynamic_timestamp.get_time_str_until_now()}")
                        if self.null_timer > 1000 and self.ids and self.ids < 3000000:  # 太多的data为None的数据了
                            await self.quit()
                        elif self.null_timer > 10000:
                            await self.quit()

            else:
                async with self.null_timer_lock:
                    self.null_timer = 0
                    list(filter(lambda x: list(x.keys())[0] == rid, self.null_list))[0].update({rid: True})
            if dycode == 404:
                reserve_lot_logger.info(f'{dycode}\n {dymsg}\n {dymessage}')
                self.list_getfail.append(dynamic_data_dict)
                self.code_check(dycode)
                return
            if dycode == 500207:  # {"code":500207,"msg":"","message":"","data":{}}#感觉像是彻底不存在的
                self.list_deleted_maybe.append(dynamic_data_dict)
                self.code_check(dycode)
                return
            if dycode == 500205:  # {"code":500205,"msg":"找不到动态信息","message":"找不到动态信息","data":{}}#感觉像是没过审或者删掉了
                self.list_deleted_maybe.append(dynamic_data_dict)
                self.code_check(dycode)
                return
            if dycode == 0:
                self.n += 1
                self.succ_counter.succ_count += 1
                self.succ_counter.latest_succ_reserve_id += 1
                try:
                    dynamic_timestamp = dynamic_data_dict.get('data').get('list').get(str(rid)).get('stime')
                    async with self.dynamic_ts_lock:
                        if rid > self.dynamic_timestamp.ids:
                            self.dynamic_timestamp.dynamic_timestamp = dynamic_timestamp
                            self.dynamic_timestamp.ids = rid
                    reserve_lot_logger.info(
                        '\n\t\t\t\t第' + str(self.times) + '次获取直播预约\t' + time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                              time.localtime()) +
                        '\t\t\t\trid:{}'.format(rid) + '\n'
                        + f"直播预约[{rid}]获取成功，直播预约创建时间：{BAPI.timeshift(self.dynamic_timestamp.dynamic_timestamp)}")
                    # with self.dynamic_ts_lock:
                    #     if int(time.time()) - self.dynamic_timestamp <= self.EndTimeSeconds and int(time.time()) - self.dynamic_timestamp>=0:
                    #         self.quit()
                except:
                    # self.dynamic_timestamp = 0
                    reserve_lot_logger.info(
                        f'\n\t\t\t\t第{self.times}次获取直播预约\t' + time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                    time.localtime()) +
                        '\t\t\t\trid:{}'.format(rid) + '\n' +
                        f'直播预约失效，被删除:{req1_dict}\n当前已经有{self.null_timer}条data为None的sid'
                    )
                self.code_check(dycode)
                return
            if dycode == -412:
                self.code_check(dycode)
                reserve_lot_logger.info(req1_dict)
                self.list_getfail.append(dynamic_data_dict)
                return
            if dycode != 0:
                self.list_unknown.append(dynamic_data_dict)
            return

    def code_check(self, dycode):
        if dycode == 404:
            self.btime += 1
            reserve_lot_logger.info(f'未知类型代码{dycode}')
            return 0
        try:
            if dycode == 500205:
                self.btime += 1
                return 0
            else:
                self.btime = 0
        except Exception as e:
            reserve_lot_logger.exception(f'未知类型代码：{dycode}')
        if dycode == -412:
            # time.sleep(eval(input('输入等待时间')))
            return -412
        elif dycode != 'None' and dycode != 500207 and \
                dycode != 500205 and dycode != 404 and dycode != -412 and self.dynamic_timestamp.dynamic_timestamp != 'None':
            pass
            # with self.dynamic_ts_lock:
            #     if int(time.time()) - self.dynamic_timestamp <= self.EndTimeSeconds and int(time.time()) - self.dynamic_timestamp >= 0:
            #         if not self.quit_Flag:
            #             self.quit_Flag = True
            #             self.quit()
            #         else:
            #             return 0

    async def quit(self):
        """
            退出时必定执行
        """
        async with self.quit_lock:
            if self.ids:
                if os.path.exists(self.unknown):
                    self.file_remove_repeat_contents(self.unknown)
                if os.path.exists(self.getfail):
                    self.file_remove_repeat_contents(self.getfail)

                # reserve_lot_log.info(f'已获取到最近{self.EndTimeSeconds // 60}分钟为止的动态')
                async with self.ids_change_lock:
                    reserve_lot_logger.info(f'退出抽奖！当前ids：{self.ids}')
                    self.ids = None

                reserve_lot_logger.info('共' + str(self.times - 1) + '次获取动态')
                reserve_lot_logger.info('其中' + str(self.n) + '个有效动态')
            else:
                return

    def remove_list_dict_duplicate(self, list_dict_data):
        """
        对list格式的dict进行去重

        """
        run_function = lambda x, y: x if y in x else x + [y]
        return reduce(run_function, [[], ] + list_dict_data)

    async def get_dynamic_with_thread(self):
        await self._init()
        now_round: TReserveRoundInfo = await self.sqlHlper.get_latest_reserve_round()
        round_start_ts = int(time.time()) if now_round.is_finished else now_round.round_start_ts
        self.now_round_id = now_round.round_id + 1 if now_round.is_finished else now_round.round_id
        None_num1 = 0
        task_list: list[asyncio.Task] = []
        for ids_index in range(len(self.ids_list)):
            None_num1 = await self._get_None_data_number()
            async with self.ids_change_lock:
                self.ids = self.ids_list[ids_index]
            async with self.null_timer_lock:
                self.null_timer = 0
                self.null_list = []
            async with self.quit_lock:
                self.quit_Flag = False
            async with self.dynamic_ts_lock:
                self.dynamic_timestamp = dynamic_timestamp_info()
            latest_rid = None
            self.succ_counter.first_reserve_id = self.ids_list[ids_index]
            while 1:
                # self.resolve_dynamic(self.ids)  # 每次开启一轮多线程前先测试是否可用
                async with self.ids_change_lock:
                    if self.ids is not None:
                        # with self.ids_change_lock:
                        #     self.ids += 1  # 每次多线程前先测试是否会412
                        #     latest_rid += 1
                        latest_rid = self.ids
                        pass
                    else:
                        self.ids_list[ids_index] = latest_rid - self.null_timer
                        break
                if self.quit_Flag:
                    self.ids_list[ids_index] = latest_rid - self.null_timer
                    break
                thread_num = 100

                for t in range(thread_num):
                    await self.sem.acquire()  ##这边加了一个上限锁之后，运行速度特别的慢，大概1秒钟1个，因为要返回结果之后，下一个线程才会继续进行 (只是看起来这样，实际上是50个线程同时在跑，等结果
                    async with self.ids_change_lock:
                        async with self.null_timer_lock:
                            if not self.ids:
                                break
                            self.null_list.append({
                                self.ids: None
                            })
                    Task = asyncio.create_task(self.resolve_dynamic_with_sem(self.ids))
                    async with self.ids_change_lock:
                        if not self.ids:
                            break
                        self.ids += 1
                    task_list.append(Task)

                task_list = list(filter(lambda x: not x.done(), task_list))

                reserve_lot_logger.debug(f'当前线程存活数量：{len(task_list)}')
                # if len(task_list) > self.sem_max_val:
                #     for Task in task_list:
                #         await Task
                if await self._get_checking_number() > self.sem_max_val + 5:
                    await asyncio.gather(*task_list)
            task_list = list(filter(lambda x: not x.done(), task_list))
            reserve_lot_logger.debug(f'任务已经完成，当前线程存活数量：{len(task_list)}，正在等待剩余线程完成任务')
            await asyncio.gather(*task_list)
            # if len(self.list_all_reserve_relation) > 1000:
            #     self.write_in_file()
            #     log.info('\n\n\t\t\t\t写入文件\n')
        None_num2 = await self._get_None_data_number()
        reserve_lot_logger.info(
            f'已经达到{self.null_timer}/{self.null_time_quit}条data为null信息或者最近预约时间只剩{self.dynamic_timestamp.get_time_str_until_now()}秒，退出！')
        reserve_lot_logger.info(
            f'当前rid记录分别回滚{self.rollback_num + None_num1}和{self.rollback_num + None_num2}条')
        ridstartfile = open(os.path.join(self.current_dir, 'idsstart.txt'), 'w', encoding='utf-8')
        finnal_rid_list = [
            str(self.ids_list[0] - self.rollback_num - None_num1),
            str(self.ids_list[1] - self.rollback_num - None_num2)
        ]
        ridstartfile.write("\n".join(
            finnal_rid_list))
        ridstartfile.close()

        self.write_in_file()
        reserve_lot_logger.info('\n\n\t\t\t\t写入文件\n')
        latest_reserve_lots = await self.generate_update_reserve_lotterys_by_round_id(self.now_round_id)
        new_round_info = TReserveRoundInfo(
            round_id=self.now_round_id,
            is_finished=True,
            round_start_ts=round_start_ts,
            round_add_num=self.times - 1 - None_num1 - None_num2,
            round_lot_num=len(latest_reserve_lots),
        )
        await self.sqlHlper.add_reserve_round_info(new_round_info)
        self.is_running = False

    async def generate_update_reserve_lotterys_by_round_id(self, round_id) -> list[TUpReserveRelationInfo]:
        """
        获取特定round更新的预约抽奖并写入文件，如果本次round更新的抽奖数量为0,则报错退出！
        :return:
        """
        exclude_attrs = ['new_field', 'reserve_round', 'reserve_round_id',
                         'raw_JSON']
        latest_reserve_lottery = await self.sqlHlper.get_reserve_lotterys_by_round_id(round_id)
        newly_updated_reserve_list = self.sqlHlper.SqlAlchemyObjList2DictList(
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

    def file_remove_repeat_contents(self, filename: str):
        s = set()
        l = []
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line not in s:
                    s.add(line)
                    l.append(line)
        if l:
            with open(filename, "w", encoding="utf-8") as f:
                for line in l:
                    f.write(line + "\n")

    async def _init(self):
        '''
        初始化信息
        :return:
        '''
        self.is_running = True
        if not os.path.exists(os.path.join(self.current_dir, 'log')):
            os.mkdir(os.path.join(self.current_dir, 'log'))

        self.unknown = os.path.join(self.current_dir, 'log/未知类型.csv')

        self.getfail = os.path.join(self.current_dir, 'log/获取失败.csv')

        try:
            ridstartfile = open(os.path.join(self.current_dir, 'idsstart.txt'), 'r', encoding='utf-8')
            async with self.ids_change_lock:
                self.ids_list.extend([int(x) for x in ridstartfile.readlines()])
                self.ids = self.ids_list[0]
            ridstartfile.close()
            reserve_lot_logger.info('获取rid开始文件成功\nids开始值：{}'.format(self.ids))
            if self.ids <= 0:
                reserve_lot_logger.info('获取rid开始文件失败')
                sys.exit('获取rid开始文件失败')
        except:
            reserve_lot_logger.info('获取rid开始文件失败')
            sys.exit('获取rid开始文件失败')

    async def check_null_timer(self, null_quit_time):
        '''
        检查最近的100个是否到达连续值
        :param null_quit_time:
        :return:
        '''
        async with self.null_timer_lock:
            self.null_list = sorted(self.null_list, key=lambda x: list(x.keys())[0], reverse=True)  # 排序
            result = list(map(lambda x: list(x.values())[0], self.null_list))

            return any(all(i is False for i in sublist) for sublist in zip(*[iter(result)] * null_quit_time))

    async def _get_checking_number(self) -> int:
        '''
        获取正在查询的数量
        :return:
        '''
        async with self.null_timer_lock:
            result = list(map(lambda x: list(x.values())[0], self.null_list))
            return len(list(filter(lambda x: x is None, result)))

    async def _get_None_data_number(self) -> int:
        '''
        获取最后数据为None的数量
        :return:
        '''
        async with self.null_timer_lock:
            result = list(map(lambda x: list(x.values())[0], self.null_list))
            return len(list(filter(lambda x: x is False, result)))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    rid_run = ReserveScrapyRobot()
    loop.run_until_complete(rid_run.get_dynamic_with_thread())
