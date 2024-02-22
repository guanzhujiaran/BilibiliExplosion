# -*- coding: utf-8 -*-
'''
异步sqlalchemy操作方法
'''
import ast
import asyncio
import random
import sqlite3
import threading
import traceback
import time
from copy import deepcopy
from typing import Union
import sqlalchemy
from loguru import logger
from sqlalchemy import select, func, update, text, and_, or_, insert, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from CONFIG import CONFIG
from utl.代理.ProxyTool.ProxyObj import TypePDict
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab, SDGrpcStat
from sqlalchemy.pool import AsyncAdaptedQueuePool

async_lock = asyncio.Lock()

sql_log = logger.bind(user='sqlite3')


# logger.add(
# CONFIG.root_dir + "utl/代理/log/sqlite3.log",
# encoding="utf-8",
# enqueue=True,
# rotation="500MB",
# compression="zip",
# retention="15 days",
# filter=lambda record: record["extra"].get('user') == "sqlite3"
# )

def lock_wrapper(func: callable) -> callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                sql_log.critical(traceback.format_exc())
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


class SQLHelper:

    def __init__(self):

        self._underscore_spe_time = 8 * 3600  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600  # 0分以上但是"-412"风控的代理休眠时间
        self.async_egn = create_async_engine(CONFIG.database.MYSQL.proxy_db_URI,
                                             echo=False,
                                             poolclass=AsyncAdaptedQueuePool,
                                             max_overflow=-1,
                                             future=True,
                                             pool_pre_ping=True,
                                             pool_recycle=1800,
                                             connect_args={
                                                 "connect_timeout":200,
                                             }
                                             )
        self.session = sessionmaker(self.async_egn,
                                    class_=AsyncSession,
                                    expire_on_commit=False,
                                    )

    def __preprocess_list_dict(self, orig_list_dict: list[dict]) -> list[dict]:
        '''
        对存入数据预处理，将dict转化为str(dict)
        :param orig_list_dict:
        :return:
        '''
        for _dic in orig_list_dict:
            for k, v in _dic.items():
                if type(v) == dict:
                    _dic[k] = str(v).replace('"', "'")
        return orig_list_dict

    def __preprocess_ret_list_dict(self, ret_dict: dict) -> dict:
        '''
        对从数据库取出的数据处理，将str的dict转换回dict
        :param ret_dict:
        :return:
        '''
        for k, v in ret_dict.items():
            if type(v) == str:
                ret_dict[k] = ast.literal_eval(v)
        return ret_dict

    async def select_score_top_proxy(self) -> dict:
        async with self.session() as session:
            sql = select(ProxyTab).order_by(ProxyTab.score.desc()).limit(1)
            res = await session.execute(sql)
            ret_list_dict = res.scalars().first()
        return self.__preprocess_ret_list_dict(ret_list_dict.to_dict())

    @lock_wrapper
    async def select_one_proxy(self, mode='single', channel='bili') -> dict:
        '''
        选择一个可用的代理
        :param channel:
        :param mode: single 就选择分数最高的未被风控的代理
        :return:[{...}, {...}] proxy_dict
        '''
        available_status = 0
        available_score = 0
        _412_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time
        async with self.session() as session:
            sql = select(ProxyTab).where(
                or_(and_(ProxyTab.status == available_status, ProxyTab.score >= available_score),
                    and_(ProxyTab.status == _412_status, ProxyTab.score >= available_score,
                         int(time.time()) - ProxyTab.update_ts >= _412_sep_time),
                    and_(ProxyTab.score < available_score, int(
                        time.time()) - ProxyTab.update_ts >= _underscore_spe_time)
                    ))
            if channel == 'zhihu':
                sql = select(ProxyTab).where(
                    and_(ProxyTab.zhihu_status == available_status, ProxyTab.score >= available_score,
                         ProxyTab.success_times > 0))
            if mode == 'single':
                sql = sql.order_by(ProxyTab.score.desc(), ProxyTab.update_ts.desc()).limit(20).order_by(func.random())
            else:
                sql = sql.order_by(func.random()).limit(1)

            res = await session.execute(sql)
            ret_list_dict = res.scalars().first()
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict.to_dict())
        else:
            return {}

    @lock_wrapper
    async def select_rand_proxy(self) -> dict:
        async with self.session() as session:
            sql = select(ProxyTab).order_by(func.random()).limit(1)
            res = await session.execute(sql)
            ret_list_dict = res.scalars().first()
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict.to_dict())
        else:
            return {}

    @lock_wrapper
    async def is_exist_proxy_by_proxy(self, proxy: dict) -> int:
        '''
        查询是否存在这个代理
        :param proxy:{'http':xxxx, 'https':xxxx}
        :return:int 1：存在 0：不存在
        '''

        async with self.session() as session:
            sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.proxy == str(proxy))
            res = await session.execute(sql)
            exist_num = res.scalars().first()
        return exist_num

    @lock_wrapper
    async def remove_list_dict_data_by_proxy(self) -> bool:
        '''
        根据proxy列对数据库table去重
        :return:
        '''
        async with self.session() as session:
            async with session.begin():
                subquery = select(func.max(ProxyTab.proxy_id)).group_by(ProxyTab.proxy)
                sql = select(ProxyTab).where(ProxyTab.proxy_id.not_in(subquery))
                res = await session.execute(sql)
                original = res.scalars().all()
                if not original:
                    sql_log.warning("代理数据重复记录不存在")
                    return True
                for record in original:
                    await session.delete(record)
        return True

    @lock_wrapper
    async def refresh_412_proxy(self) -> int:
        '''
        更新412和负分的代理，返回更新的数量
        :return:
        '''
        avaliable_score = 0
        available_status = 0
        now = int(time.time())
        unavaliable_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time
        async with self.session() as session:
            async with session.begin():
                sql = update(ProxyTab).where(
                    and_(ProxyTab.status == unavaliable_status,
                         now - ProxyTab.update_ts >= _412_sep_time,
                         ProxyTab.score >= avaliable_score)
                ).values(
                    status=available_status,
                    update_ts=now)
                await session.execute(sql)

                sql = update(ProxyTab).where(
                    and_(ProxyTab.score < avaliable_score,
                         now - ProxyTab.update_ts >= _underscore_spe_time)
                ).values(
                    status=available_status,
                    update_ts=now,
                    score=50
                )
                await session.execute(sql)  # 刷新超过12小时的无效代理，改变status和score
                # sql = select(ProxyTab).where(ProxyTab.score<avaliable_score and ProxyTab.success_times<-3) # 删除无效代理，暂时先不用
                # res = await session.execute(sql)
                # original = res.scalars().all()
                # if original:
                #     await session.delete(original)

                sub_sql = select(ProxyTab.proxy_id)
                sql = select(SDGrpcStat).where(SDGrpcStat.proxy_id.not_in(sub_sql))  # 删除不在主表中的grpc代理数据
                res = await session.execute(sql)
                original = res.scalars().all()
                if not original:
                    # sql_log.debug("grpc数据都在主表中！")
                    return True
                for record in original:
                    await session.delete(record)
            return True

    @lock_wrapper
    async def grpc_refresh_412_proxy(self) -> int:
        '''
        更新412和负分的代理，返回更新的数量
        :return:
        '''
        avaliable_score = 0
        available_status = 0
        now = int(time.time())
        unavaliable_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time
        async with self.session() as session:
            async with session.begin():
                sql = update(SDGrpcStat).where(
                    and_(
                        SDGrpcStat.sd_status == unavaliable_status,
                        now - SDGrpcStat.sd_update_ts >= _412_sep_time,
                        SDGrpcStat.sd_score >= avaliable_score)
                ).values(
                    status=available_status,
                    update_ts=now)
                await session.execute(sql)  # 刷新超过两小时的412风控代理 不改变分数，只改变status

                sql = update(ProxyTab).where(
                    and_(ProxyTab.score < avaliable_score,
                         now - ProxyTab.update_ts >= _underscore_spe_time)
                ).values(
                    status=available_status,
                    update_ts=now,
                    score=50
                )
                await session.execute(sql)  # 刷新超过12小时的无效代理，改变status和score

            # sql = select(ProxyTab).where(ProxyTab.score<avaliable_score and ProxyTab.success_times<-3) # 删除无效代理，暂时先不用
            # res = await session.execute(sql)
            # original = res.scalars().all()
            # if original:
            #     await session.delete(original)
        return 1

    @lock_wrapper
    async def update_to_proxy_list(self, proxy_dict: dict, change_score_num=10) -> bool:
        '''
        更新数据 update 最好只用update，upsert会导致主键增长异常
        :param score_plus_Flag:
        :param change_score_num: 修改的分
        :param score_minus_Flag:
        :param proxy_dict:
        :return:
        '''
        proxy_dict = deepcopy(proxy_dict)
        proxy_dict = self.__preprocess_list_dict([proxy_dict])[0]
        proxy = proxy_dict.get('proxy', 0)
        async with self.session() as session:
            async with session.begin():
                sql = update(ProxyTab).where(
                    ProxyTab.proxy == proxy
                ).values(
                    status=proxy_dict.get('status', 0),
                    score=ProxyTab.score + change_score_num,
                    success_times=proxy_dict.get('success_times', 0) + 1,
                    update_ts=proxy_dict.get('update_ts', int(time.time())),
                    add_ts=proxy_dict.get('add_ts', int(time.time()))
                )
                await session.execute(sql)
        return True

    @lock_wrapper
    async def add_to_proxy_list(self, proxy_dict: dict) -> bool:
        '''
        添加数据
        :param proxy_dict:
        :return:
        '''
        proxy_dict = deepcopy(proxy_dict)
        proxy_dict = self.__preprocess_list_dict([proxy_dict])[0]
        async with self.session() as session:
            async with session.begin():
                P = ProxyTab(
                    **proxy_dict
                )
                session.add(P)
                # 刷新自带的主键
                await session.flush()
                # 释放这个data数据
                session.expunge(P)
        return True

    #
    # def insert_all_proxy(self, info_dict_list: list[dict]) -> bool:
    #     '''
    #     增加
    #     :param info_dict_list: # [{'http': 'http://120.196.186.248:9091', 'https': 'http://120.196.186.248:9091'}...]
    #     :return:
    #     '''
    #     self.op_db_table.insert_all(self.__preprocess_list_dict(info_dict_list))
    #     return True

    @lock_wrapper
    async def remove_proxy(self, proxy: dict):
        '''
        删除
        :param proxy:
        :return:
        '''
        async with self.session() as session:
            async with session.begin():
                sql = select(ProxyTab).where(ProxyTab.proxy == str(proxy).replace('"', "'"))  # 删除无效代理，暂时先不用
                res = await session.execute(sql)
                original = res.scalars().all()
                if original:
                    for record in original:
                        await session.delete(record)

    @lock_wrapper
    async def get_412_proxy_num(self) -> int:
        async with self.session() as session:
            sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.status == -412)
            result = await session.execute(sql)
            res = result.scalars().first()
        return res

    @lock_wrapper
    async def grpc_get_412_proxy_num(self) -> int:
        async with self.session() as session:
            sql = select(func.count(SDGrpcStat.proxy_id)).where(SDGrpcStat.sd_status == -412)
            result = await session.execute(sql)
            res = result.scalars().first()
        return res

    @lock_wrapper
    async def get_latest_add_ts(self) -> int:
        async with self.session() as session:
            sql = select(ProxyTab).order_by(ProxyTab.add_ts.desc()).limit(1)
            result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res.add_ts
            else:
                return 0

    @lock_wrapper
    async def get_all_proxy_nums(self) -> int:
        async with self.session() as session:
            sql = select(func.count(ProxyTab.proxy_id))
            result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res
            else:
                return 0

    @lock_wrapper
    async def grpc_get_all_proxy_nums(self):
        async with self.session() as session:
            sql = select(func.count(SDGrpcStat.proxy_id))
            result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res
            else:
                return 0

    @lock_wrapper
    async def get_available_proxy_nums(self):
        async with self.session() as session:
            sql = select(func.count(ProxyTab.proxy_id)).where(and_(ProxyTab.score >= 0, ProxyTab.status != -412))
            result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res
            else:
                return 0

    # region grpc_proxy

    @lock_wrapper
    async def get_one_rand_grpc_proxy(self) -> Union[TypePDict, dict]:
        available_status = 0
        available_score = 0
        _412_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time

        async def fresh_grpc_proxy():
            avaliable_score = 0
            available_status = 0
            now = int(time.time())
            unavaliable_status = -412
            _412_sep_time = self._412_sep_time
            async with self.session() as session:
                async with session.begin():
                    ___sql = update(SDGrpcStat).where(and_
                                                      (SDGrpcStat.sd_status == unavaliable_status,
                                                       now - SDGrpcStat.sd_update_ts >= _412_sep_time,
                                                       SDGrpcStat.sd_score >= avaliable_score)
                                                      ).values(
                        status=available_status,
                        update_ts=now
                    )
                    await session.execute(___sql)  # 刷新超过两小时的412风控代理 不改变分数，只改变status

                    ___sql = update(SDGrpcStat).where(
                        and_(SDGrpcStat.sd_score < avaliable_score,
                             now - SDGrpcStat.sd_update_ts >= _underscore_spe_time)
                    ).values(
                        status=available_status,
                        update_ts=now,
                        score=50
                    )
                    await session.execute(___sql)  # 刷新超过12小时的无效代理，改变status和score

        async with self.session() as session:
            sql = select(func.count(SDGrpcStat.proxy_id)).where(
                and_(SDGrpcStat.sd_score >= 0,
                     SDGrpcStat.sd_status != -412)
            )
            result = await session.execute(sql)
            res = result.scalars().first()
            if res == 0:
                await fresh_grpc_proxy()


            #             sql_str = f"""
            # select * from(select
            # proxy_tab.proxy_id,
            # proxy_tab.proxy,
            # ifnull(SD_grpc_stat.status,0) as status,
            # SD_grpc_stat.update_ts as update_ts,ifnull(SD_grpc_stat.success_times,0) as success_times,
            # ifnull(SD_grpc_stat.score,50) as score
            # from proxy_tab
            # left join SD_grpc_stat on proxy_tab.proxy_id=SD_grpc_stat.proxy_id)
            # where (status={available_status} and score>={available_score})
            # or (status={_412_status} and score>={available_score} and strftime('%s','now')-update_ts >={_412_sep_time})
            # or (score<0 and strftime('%s','now')-update_ts >={_underscore_spe_time})
            # order by random()
            # limit 1
            #     """.format(
            #                 available_status=available_status,
            #                 available_score=available_score,
            #                 _412_status=_412_status,
            #                 _412_sep_time=_412_sep_time,
            #                 _underscore_spe_time=_underscore_spe_time,
            #             )
        async with self.session() as session:
            sql = select(ProxyTab).where(
                or_(and_(SDGrpcStat.status == available_status, SDGrpcStat.score >= available_score),
                    and_(SDGrpcStat.status == _412_status, SDGrpcStat.score >= available_score,
                         int(time.time()) - SDGrpcStat.update_ts >= _underscore_spe_time),
                    and_(SDGrpcStat.score < 0, int(time.time()) - SDGrpcStat.update_ts >= _underscore_spe_time))
            ).order_by(func.random()).limit(1)
            result = await session.execute(sql)
            ret_list_dict = result.scalars().first()
            # if ret_list_dict:
            #     ret_list_dict = {
            #         'proxy_id': ret_list_dict[0],
            #         'proxy': ret_list_dict[1],
            #         'status': ret_list_dict[2],
            #         'update_ts': ret_list_dict[3],
            #         'success_times': ret_list_dict[4],
            #         'score': ret_list_dict[5]
            #     }
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict.to_dict())
        else:
            return {}

    @lock_wrapper
    async def get_grpc_proxy_by_ip(self, ip: str) -> Union[TypePDict, dict]:
        '''

        :param ip: 像这种格式的ip地址加端口 '127.0.0.1:1234'
        :return:
        '''
        async with self.session() as session:
            ip = ip.replace('https', 'http')
            ip_str = ip if 'http' in ip else f'http://{ip}'
            str_dict = str({
                'http': ip_str,
                'https': ip_str
            })
            sql = select(SDGrpcStat).where(SDGrpcStat.proxy == str_dict).limit(1)
            res = await session.execute(sql)
            result = res.scalars().first()
            if result:
                return self.__preprocess_ret_list_dict(result.to_dict())
            else:
                return {}

    @lock_wrapper
    async def upsert_grpc_proxy_status(self, proxy_id: int, status: int, score_change: int = 0):
        '''

        :param proxy_id:
        :param status:
        :param score_change:修改的分数值，+10，-10，或者不变
        :return:
        '''
        async with self.session() as session:
            async with session.begin():
                sql = select(SDGrpcStat).where(SDGrpcStat.proxy_id == proxy_id).limit(1)
                res = await session.execute(sql)
                grpc_proxy_detail: SDGrpcStat = res.scalars().first()
                if grpc_proxy_detail:
                    success_times = grpc_proxy_detail.sd_success_times
                    if score_change > 0:
                        success_times += 1
                    else:
                        success_times -= 1
                    if grpc_proxy_detail.sd_score > 100:
                        score_change = 100 - grpc_proxy_detail.sd_score
                    elif grpc_proxy_detail.sd_score < -50:
                        score_change = -50 - grpc_proxy_detail.sd_score
                    grpc_proxy_detail.sd_status = status
                    grpc_proxy_detail.sd_score = grpc_proxy_detail.sd_score + score_change
                    grpc_proxy_detail.sd_success_times = success_times
                    grpc_proxy_detail.sd_update_ts = int(time.time())
                    await session.flush()
                    return
                else:
                    sql = insert(SDGrpcStat).values(
                        proxy_id=proxy_id,
                        sd_status=status,
                        sd_score=score_change,
                        sd_success_times=1 if score_change >= 0 else 0,
                        sd_update_ts=int(time.time()),
                    )
                    await session.execute(sql)
                    # 刷新自带的主键
                    await session.flush()

    # endregion

    async def test(self):
        # {'http': 'http://188.166.197.129:3128', 'https': 'http://188.166.197.129:3128'}
        #for i in range(1000000):
        res = await self.get_one_rand_grpc_proxy(
        )
        print(res)


if __name__ == '__main__':
    sq = SQLHelper()
    asyncio.run(sq.test())
