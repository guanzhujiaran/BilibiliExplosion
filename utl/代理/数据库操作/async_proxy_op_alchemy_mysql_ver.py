# -*- coding: utf-8 -*-
'''
异步sqlalchemy操作方法
'''
import ast
import asyncio
import datetime
import json
import random
import time
from copy import deepcopy
from enum import Enum
from typing import Union, List, Literal
from sqlalchemy import select, func, update, and_, or_, insert, bindparam
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from CONFIG import CONFIG, database
from fastapi接口.log.base_log import sql_log
from utl.redisTool.RedisManager import RedisManagerBase
from utl.代理.ProxyTool.ProxyObj import TypePDict
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab, SDGrpcStat
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def lock_wrapper(_func: callable) -> callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                async with SQLHelper.async_sem:
                    if _func.__name__ not in ["select_proxy", "_handle_update"]:
                        force = True if _func.__name__ in ['refresh_412_proxy'] else False
                        await SQLHelper.check_redis_data(force=force)
                    res = await _func(*args, **kwargs)
                return res
            except Exception as e:
                sql_log.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


def preprocess_ret_list_dict(ret_dict: dict) -> dict:
    '''
    对从数据库取出的数据处理，将str的dict转换回dict
    :param ret_dict:
    :return:
    '''
    for k, v in ret_dict.items():
        if type(v) == str:
            ret_dict[k] = ast.literal_eval(v)
    return ret_dict


def preprocess_list_dict(orig_list_dict: list[dict]) -> list[dict]:
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


class SubRedisStore(RedisManagerBase):
    class RedisMap(str, Enum):
        bili_proxy = 'bili_proxy'  # String类型数据的字符前缀
        bili_proxy_zset = 'zset_bili_proxy'  # 有序集合类型数据的字符前缀，里面只存放可用的代理
        bili_proxy_black = 'bili_proxy_black'  # 代理黑名单，也就是那些412或者352的没法用了的代理
        bili_proxy_sync_ts = f'sync_ts:{bili_proxy}'
        bili_proxy_changed = 'bili_proxy_changed'  # 代理是否发生变化

    def __init__(self):
        super().__init__(db=database.proxySubRedis.db)
        self.sync_ts = 0
        self.sync_sep_ts = 60 * 60  # 60分钟同步一次
        self.RedisTimeout = 600

    def dict_2_model(self, d: dict):
        return ProxyTab(**preprocess_list_dict([d])[0])

    def model_2_dict(self, model: ProxyTab) -> dict:
        return preprocess_ret_list_dict(model.to_dict())

    def _gen_proxy_key(self, proxy_info_dict: dict | str, is_black: bool = False, is_changed: bool = False):
        """

        :param proxy_info_dict:{http:xxx,https:xxx,socks5:xxx,sock5:xxx}
        :return:
        """
        try:
            if isinstance(proxy_info_dict, str):
                proxy_info_dict = ast.literal_eval(proxy_info_dict)
            inner_key = proxy_info_dict.get("https", proxy_info_dict.get("socks5"))
        except:
            inner_key = str(proxy_info_dict)
        if is_black:
            return f'{self.RedisMap.bili_proxy_black}:{inner_key}'
        if is_changed:
            return f'{self.RedisMap.bili_proxy_changed}:{inner_key}'
        return f'{self.RedisMap.bili_proxy.value}:{inner_key}'

    async def sync_2_redis(self, proxy_infos: List[ProxyTab]):
        """
        同步代理到redis
        :param proxy_infos:
        :return:
        """
        if proxy_infos:
            await self._set(
                [self._gen_proxy_key(proxy_info_dict=self.model_2_dict(x).get('proxy')) for x in proxy_infos],
                [json.dumps(self.model_2_dict(x)) for x in proxy_infos])
            await self._zadd(
                self.RedisMap.bili_proxy_zset,
                {x.proxy: x.score if x.score else 0 for x in proxy_infos}
            )

    async def set_sync_ts(self):
        self.sync_ts = int(time.time())
        await self._set(self.RedisMap.bili_proxy_sync_ts, self.sync_ts)

    async def get_sync_ts(self) -> int:
        if self.sync_ts:
            return self.sync_ts
        _ = await self._get(self.RedisMap.bili_proxy_sync_ts)
        return int(_) if _ else 0

    async def redis_get_all_proxy(self) -> List[ProxyTab]:
        return [ProxyTab(**preprocess_list_dict([ast.literal_eval(x)])[0]) for x in
                await self._get_all_val_with_prefix(self.RedisMap.bili_proxy.value)]

    async def redis_get_all_changed_proxy(self) -> List[ProxyTab]:
        return [ProxyTab(**preprocess_list_dict([ast.literal_eval(x)])[0]) for x in
                await self._get_all_val_with_prefix(self.RedisMap.bili_proxy_changed.value)]

    async def redis_get_proxy_by_ip(self, ip_dict: dict) -> dict | None:
        """
        ip_dict = {
            'http': ip_str,
            'https': ip_str
        }
        :param ip_dict:
        :return:
        """
        redis_data = await self._get(
            self._gen_proxy_key(proxy_info_dict=ip_dict)
        )
        if redis_data:
            return ast.literal_eval(
                redis_data
            )
        return None

    async def redis_select_one_proxy(self, raw=False) -> ProxyTab | None | dict:
        """
        随机获取一个可用的代理
        :return:
        """
        if p := await self._zrand(key=self.RedisMap.bili_proxy_zset.value):
            if proxy_tab_dict := await self._get(self._gen_proxy_key(ast.literal_eval(p))):
                if raw:
                    return self.dict_2_model(ast.literal_eval(proxy_tab_dict))
                return ast.literal_eval(proxy_tab_dict)
        sql_log.critical("redis中无可用代理！")
        if raw:
            return None
        return {}

    async def redis_select_score_top_proxy(self, raw=False) -> ProxyTab | None | dict:
        if top_score_ip_dict := await self._zget_top_score(
                key=self.RedisMap.bili_proxy_zset.value,
                rand=True
        ):
            if proxy_tab_dict := await self._get(self._gen_proxy_key(ast.literal_eval(top_score_ip_dict))):
                if raw:
                    return self.dict_2_model(ast.literal_eval(proxy_tab_dict))
                return ast.literal_eval(proxy_tab_dict)
        if raw:
            return None
        return {}

    async def redis_update_proxy(self, proxy_tab_dict: dict, score_change_num: int) -> bool:
        """

        :param proxy_tab_dict: proxy属性为dict
        :param score_change_num:
        :return:
        """
        redis_data = await self.redis_get_proxy_by_ip(proxy_tab_dict.get('proxy'))
        is_update = False
        if redis_data:
            await self._del(self._gen_proxy_key(proxy_tab_dict.get('proxy')))
            if proxy_tab_dict.get('status') and proxy_tab_dict.get('status') != 0:
                await self._set(
                    key=self._gen_proxy_key(proxy_tab_dict.get('proxy'), is_black=True),
                    value=json.dumps(preprocess_list_dict([proxy_tab_dict])[0])
                )
            proxy_tab_dict['score'] = redis_data.get('score', 0) + score_change_num
        else:
            redis_data = preprocess_list_dict([proxy_tab_dict])[0]
        await self._set(self._gen_proxy_key(proxy_tab_dict.get('proxy')), json.dumps(redis_data))  # 全局的key
        await self._set(self._gen_proxy_key(proxy_tab_dict.get('proxy'), is_changed=True),
                        json.dumps(redis_data))  # 变更的key
        await self._zadd(self.RedisMap.bili_proxy_zset, {str(proxy_tab_dict.get('proxy')): redis_data.get('score', 0)})
        return is_update

    async def redis_clear_black_proxy(self):
        return await self._del_keys_with_prefix(self.RedisMap.bili_proxy_black.value)

    async def redis_clear_changed_proxy(self):
        return await self._del_keys_with_prefix(self.RedisMap.bili_proxy_changed.value)


class SQLHelperClass:
    def __init__(self):
        self.async_sem = asyncio.Semaphore(100)
        self._underscore_spe_time = 5 * 3600  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600  # 0分以上但是"-412"风控的代理休眠时间
        self.async_egn = create_async_engine(
            CONFIG.database.MYSQL.proxy_db_URI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self.async_egn.dialect.supports_sane_rowcount = False  # 避免了批量update报错stableData
        self.session = async_sessionmaker(
            self.async_egn,
            expire_on_commit=False,
        )
        self.sched = AsyncIOScheduler()
        self.sched.add_job(self.background_service, 'interval', seconds=600, next_run_time=datetime.datetime.now(),
                           misfire_grace_time=600)
        self.sub_redis_store = SubRedisStore()
        self.lock = asyncio.Lock()
        self.is_sync = False

    async def sync_2_database(self):
        @lock_wrapper
        async def _handle_update(_proxy_info):
            stmt = select(ProxyTab).where(ProxyTab.proxy_id == _proxy_info.proxy_id).limit(1)
            res = await session.execute(stmt)
            proxy_tab = res.scalars().first()
            if proxy_tab:
                proxy_tab.status = _proxy_info.status
                proxy_tab.update_ts = _proxy_info.update_ts
                proxy_tab.score = _proxy_info.score
                proxy_tab.success_times = _proxy_info.success_times

        if all_proxy_infos := await self.sub_redis_store.redis_get_all_changed_proxy():
            async with self.session() as session:
                lst = [{
                    "proxy_id": proxy_info.proxy_id,
                    "status": proxy_info.status,
                    "update_ts": proxy_info.update_ts,
                    "score": proxy_info.score,
                    "success_times": proxy_info.success_times,
                } for proxy_info in all_proxy_infos if proxy_info.proxy_id and proxy_info.proxy]
                sql_log.debug(f'开始更新MySQL中数据，共{len(lst)}条')
                await session.run_sync(lambda s: s.bulk_update_mappings(
                    ProxyTab,
                    lst,
                ))
                # sql_log.debug(f'开始更新MySQL中数据，共{len(all_proxy_infos)}条')
                # await asyncio.gather(*[_handle_update(proxy_info) for proxy_info in all_proxy_infos])
                await session.commit()

    async def check_redis_data(self, force=False):
        if int(time.time()) - self.sub_redis_store.sync_sep_ts > self.sub_redis_store.sync_ts or force:
            async with self.lock:
                if self.is_sync:
                    return
                self.is_sync = True
            try:
                redis_sync_ts = await self.sub_redis_store.get_sync_ts()
                if redis_sync_ts < int(time.time()) - self.sub_redis_store.sync_sep_ts or force:
                    sql_log.debug('上次同步时间：{}\n开始同步redis和mysql数据库')
                    start_ts = int(time.time())
                    sql_log.debug('开始将redis数据同步至MySQL中')
                    await self.sync_2_database()
                    sql_log.debug(f'将redis数据同步至MySQL中完成，耗时：{int(time.time() - start_ts)}秒！')
                    sql_log.debug(f'开始获取MySQL中可用代理数据')
                    all_available_proxy_infos = await self.select_proxy(mode="all", raw=True)
                    sql_log.debug(f'获取MySQL中可用代理数据完成，耗时：{int(time.time() - start_ts)}秒！')
                    sql_log.debug(f'开始将MySQL内容同步至redis中')
                    await self.sub_redis_store.sync_2_redis(all_available_proxy_infos)
                    sql_log.debug(f'将MySQL内容同步至redis中完成，耗时：{int(time.time() - start_ts)}秒！')
                    sql_log.debug(f'开始清除redis中不可用代理数据')
                    await self.sub_redis_store.redis_clear_black_proxy()
                    await self.sub_redis_store.redis_clear_changed_proxy()
                    sql_log.debug(f'清除redis中不可用代理数据完成，耗时：{int(time.time() - start_ts)}秒！')
                    await self.sub_redis_store.set_sync_ts()
                    sql_log.debug(f'同步redis和mysqlMySQL完成，耗时{int(time.time() - start_ts)}秒！')
            except Exception as e:
                sql_log.error(f'同步redis和mysql数据库失败！{e}')
                raise e
            finally:
                self.is_sync = False

    async def background_service(self):
        await asyncio.gather(
            *[
                self.fresh_proxy()
            ]
        )

    @lock_wrapper
    async def select_score_top_proxy(self) -> dict:
        if redis_data := await self.sub_redis_store.redis_select_score_top_proxy():
            return redis_data
        sql = select(ProxyTab).order_by(ProxyTab.score.desc()).limit(1)
        async with self.session() as session:
            res = await session.execute(sql)
        ret_list_dict = res.scalars().first()
        return preprocess_ret_list_dict(ret_list_dict.to_dict())

    @lock_wrapper
    async def select_proxy(self, mode: Literal["single", "all", "rand"] = 'single', channel='bili', raw=False) -> dict | \
                                                                                                                  List[
                                                                                                                      dict] | ProxyTab | \
                                                                                                                  List[
                                                                                                                      ProxyTab]:
        '''
        选择一个可用的代理
        :param raw:
        :param channel:
        :param mode: single 就选择分数最高的未被风控的代理 默认是rand，改成single之后从分数最高的代理开始用，这样获取响应特别快
        :return:[{...}, {...}] proxy_dict
        '''
        if mode != "all":
            if mode == "single":
                return preprocess_ret_list_dict(await self.sub_redis_store.redis_select_score_top_proxy(raw=raw))
            if mode == "rand":
                return preprocess_ret_list_dict(await self.sub_redis_store.redis_select_one_proxy(raw=raw))
        available_status = 0
        available_score = 0
        _412_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time
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
            sql = sql.order_by(ProxyTab.score.desc(), ProxyTab.update_ts.desc()).limit(1).order_by(func.random())
        elif mode == "all":
            # sql = sql.limit(10000).order_by(func.random())  # 1万条一取差不多，多了没啥用
            pass
        else:
            sql = sql.order_by(func.random()).limit(1)
        async with self.session() as session:
            res = await session.execute(sql)
        if raw:
            if mode == 'all':
                ret_list_dict = res.scalars().all()
                return list(ret_list_dict)
            else:
                ret_list_dict = res.scalars().first()
                if ret_list_dict:
                    return ret_list_dict
                else:
                    return {}
        else:
            if mode == 'all':
                ret_list_dict = res.scalars().all()
                return [preprocess_ret_list_dict(x.to_dict()) for x in ret_list_dict]
            else:
                ret_list_dict = res.scalars().first()
                if ret_list_dict:
                    return preprocess_ret_list_dict(ret_list_dict.to_dict())
                else:
                    return {}

    # @lock_wrapper
    # async def select_rand_proxy(self) -> dict:
    #     sql = select(ProxyTab).order_by(func.random()).limit(1)
    #     async with self.session() as session:
    #         res = await session.execute(sql)
    #     ret_list_dict = res.scalars().first()
    #     if ret_list_dict:
    #         return self.preprocess_ret_list_dict(ret_list_dict.to_dict())
    #     else:
    #         return {}

    @lock_wrapper
    async def is_exist_proxy_by_proxy(self, proxy: dict) -> int:
        '''
        查询是否存在这个代理
        :param proxy:{'http':xxxx, 'https':xxxx}
        :return:int 1：存在 0：不存在
        '''
        sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.proxy == str(proxy))
        async with self.session() as session:
            res = await session.execute(sql)
        exist_num = res.scalars().first()
        return exist_num

    @lock_wrapper
    async def remove_list_dict_data_by_proxy(self) -> bool:
        '''
        根据proxy列对数据库table去重
        :return:
        '''
        subquery = select(func.max(ProxyTab.proxy_id)).group_by(ProxyTab.proxy)
        sql = select(ProxyTab).where(ProxyTab.proxy_id.not_in(subquery))
        async with self.session() as session:
            async with session.begin():
                # async with self.async_lock:
                res = await session.execute(sql)
                original = res.scalars().all()
                if not original:
                    sql_log.info("代理数据重复记录不存在")
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
        sql = update(ProxyTab).where(
            and_(ProxyTab.status == unavaliable_status,
                 now - ProxyTab.update_ts >= _412_sep_time,
                 ProxyTab.score >= avaliable_score,
                 ProxyTab.success_times >= 5
                 )
        ).values(
            status=available_status,
            update_ts=now)
        sub_sql = select(ProxyTab.proxy_id)
        sec_sql = select(SDGrpcStat).where(SDGrpcStat.proxy_id.not_in(sub_sql))  # 删除不在主表中的grpc代理数据
        async with self.session() as session:
            async with session.begin():
                # async with self.async_lock:
                await session.execute(sql)
                # sql = update(ProxyTab).where(
                #     and_(ProxyTab.score < avaliable_score,
                #          now - ProxyTab.update_ts >= _underscore_spe_time)
                # ).values(
                #     status=available_status,
                #     update_ts=now,
                #     score=50
                # )
                # async with self.async_lock:
                # await session.execute(sql)  # 刷新超过12小时的无效代理，改变status和score
                # sql = select(ProxyTab).where(ProxyTab.score<avaliable_score and ProxyTab.success_times<-3) # 删除无效代理，暂时先不用
                # res = await session.execute(sql)
                # original = res.scalars().all()
                # if original:
                #     await session.delete(original)
                # async with self.async_lock:
                res = await session.execute(sec_sql)
                original = res.scalars().all()
                if not original:
                    # sql_log.debug("grpc数据都在主表中！")
                    return True
                for record in original:
                    await session.delete(record)
            return True

    # @lock_wrapper
    # async def grpc_refresh_412_proxy(self) -> int:
    #     '''
    #     更新412和负分的代理，返回更新的数量
    #     :return:
    #     '''
    #     avaliable_score = 0
    #     available_status = 0
    #     now = int(time.time())
    #     unavaliable_status = -412
    #     _412_sep_time = self._412_sep_time
    #     _underscore_spe_time = self._underscore_spe_time
    #     sql = update(SDGrpcStat).where(
    #         and_(
    #             SDGrpcStat.sd_status == unavaliable_status,
    #             now - SDGrpcStat.sd_update_ts >= _412_sep_time,
    #             SDGrpcStat.sd_score >= avaliable_score)
    #     ).values(
    #         status=available_status,
    #         update_ts=now)
    #     sec_sql = update(ProxyTab).where(
    #         and_(ProxyTab.score < avaliable_score,
    #              now - ProxyTab.update_ts >= _underscore_spe_time)
    #     ).values(
    #         status=available_status,
    #         update_ts=now,
    #         score=50
    #     )
    #     async with self.session() as session:
    #         async with session.begin():
    #             # async with self.async_lock:
    #             await session.execute(sql)  # 刷新超过两小时的412风控代理 不改变分数，只改变status
    #             # async with self.async_lock:
    #             await session.execute(sec_sql)  # 刷新超过12小时的无效代理，改变status和score
    #         # sql = select(ProxyTab).where(ProxyTab.score<avaliable_score and ProxyTab.success_times<-3) # 删除无效代理，暂时先不用
    #         # res = await session.execute(sql)
    #         # original = res.scalars().all()
    #         # if original:
    #         #     await session.delete(original)
    #     return 1

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
        try:
            is_update = await self.sub_redis_store.redis_update_proxy(proxy_dict, change_score_num)
            return is_update
        except Exception as e:
            sql_log.exception(e)
        proxy_dict = preprocess_list_dict([proxy_dict])[0]
        proxy = proxy_dict.get('proxy', 0)
        sql = update(ProxyTab).where(
            ProxyTab.proxy == proxy
        ).values(
            status=proxy_dict.get('status', 0),
            score=ProxyTab.score + change_score_num,
            success_times=proxy_dict.get('success_times', 0) + 1,
            update_ts=proxy_dict.get('update_ts', int(time.time())),
            add_ts=proxy_dict.get('add_ts', int(time.time()))
        )
        async with self.session() as session:
            async with session.begin():
                # async with self.async_lock:
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
        proxy_dict = preprocess_list_dict([proxy_dict])[0]
        P = ProxyTab(
            **proxy_dict
        )
        async with self.session() as session:
            async with session.begin():
                session.add(P)
                # 刷新自带的主键
                # async with self.async_lock:
                await session.flush()
                # 释放这个data数据
                session.expunge(P)
        return True

    @lock_wrapper
    async def remove_proxy(self, proxy: dict):
        '''
        删除
        :param proxy:
        :return:
        '''
        async with self.session() as session:
            sql = select(ProxyTab).where(ProxyTab.proxy == str(proxy).replace('"', "'"))  # 删除无效代理，暂时先不用
            async with session.begin():
                res = await session.execute(sql)
                original = res.scalars().all()
                if original:
                    for record in original:
                        # async with self.async_lock:
                        await session.delete(record)

    @lock_wrapper
    async def get_412_proxy_num(self) -> int:
        sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.status == -412)
        async with self.session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        return res

    # @lock_wrapper
    # async def grpc_get_412_proxy_num(self) -> int:
    #     sql = select(func.count(SDGrpcStat.proxy_id)).where(SDGrpcStat.sd_status == -412)
    #
    #     async with self.session() as session:
    #         # async with self.async_lock:
    #         result = await session.execute(sql)
    #     res = result.scalars().first()
    #     return res

    @lock_wrapper
    async def get_latest_add_ts(self) -> int:
        sql = select(ProxyTab).order_by(ProxyTab.add_ts.desc()).limit(1)
        async with self.session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        if res:
            return res.add_ts
        else:
            return 0

    @lock_wrapper
    async def get_all_proxy_nums(self) -> int:
        sql = select(func.count(ProxyTab.proxy_id))
        async with self.session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        if res:
            return res
        else:
            return 0

    @lock_wrapper
    async def get_available_proxy_nums(self):
        sql = select(func.count(ProxyTab.proxy_id)).where(and_(ProxyTab.score >= 0, ProxyTab.status != -412))
        async with self.session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        if res:
            return res
        else:
            return 0

    async def fresh_proxy(self):
        avaliable_score = -50
        available_status = 0
        now = int(time.time())
        unavaliable_status = -412
        _412_sep_time = self._412_sep_time
        nums = 0
        # async with self.session() as session:
        #     async with session.begin():
        #         del_num = 0
        #         ____sql = delete(ProxyTab).where(and_(
        #             ProxyTab.status != 0,
        #             ProxyTab.success_times < -50
        #         ))
        #         del_num += (await session.execute(____sql)).rowcount  # 刷新超过12小时的无效代理，改变status和score
        #         await session.commit()
        # sql_log.debug(f'【刷新代理池】\t删除无效代理，影响数量：{del_num}个！')
        ___sql = update(ProxyTab).where(and_(
            ProxyTab.status != available_status,
            now - ProxyTab.update_ts >= _412_sep_time,
            ProxyTab.score >= avaliable_score,
            ProxyTab.success_times >= 5  # 必须是成功过的代理才刷新
        ),
        ).values(
            status=available_status,
            update_ts=now
        )
        __sql = update(ProxyTab).where(
            and_(ProxyTab.score < avaliable_score,
                 now - ProxyTab.update_ts >= self._underscore_spe_time)
        ).values(
            status=available_status,
            update_ts=now,
            score=50
        )
        async with self.session() as session:
            async with session.begin():
                nums += (await session.execute(___sql)).rowcount  # 刷新超过两小时的412风控代理 不改变分数，只改变status
                nums += (await session.execute(__sql)).rowcount  # 刷新超过12小时的无效代理，改变status和score
                await session.commit()
        sql_log.debug(f'【刷新代理池】\t刷新代理，影响数量：{nums}个！')
        return nums

    # region grpc_proxy
    # @lock_wrapper
    # async def get_one_rand_grpc_proxy(self) -> Union[TypePDict, dict]:
    #     if self.sched.state == 0:
    #         self.sched.start()
    #     available_status = 0
    #     available_score = 0
    #     _412_status = -412
    #     _412_sep_time = self._412_sep_time
    #     _underscore_spe_time = self._underscore_spe_time
    #
    #     sql = select(ProxyTab).where(
    #         or_(and_(ProxyTab.status == available_status, ProxyTab.score >= available_score),
    #             and_(ProxyTab.status == _412_status, ProxyTab.score >= available_score,
    #                  int(time.time()) - ProxyTab.update_ts >= _underscore_spe_time),
    #             and_(ProxyTab.score < 0, int(time.time()) - ProxyTab.update_ts >= _underscore_spe_time))
    #     ).order_by(func.random()).limit(1)
    #     async with self.session() as session:
    #         # async with self.async_lock:
    #         result = await session.execute(sql)
    #     ret_list_dict = result.scalars().first()
    #     # if ret_list_dict:
    #     #     ret_list_dict = {
    #     #         'proxy_id': ret_list_dict[0],
    #     #         'proxy': ret_list_dict[1],
    #     #         'status': ret_list_dict[2],
    #     #         'update_ts': ret_list_dict[3],
    #     #         'success_times': ret_list_dict[4],
    #     #         'score': ret_list_dict[5]
    #     #     }
    #     if ret_list_dict:
    #         return self.preprocess_ret_list_dict(ret_list_dict.to_dict())
    #     else:
    #         return {}
    # @lock_wrapper
    # async def upsert_grpc_proxy_status(self, proxy_id: int, status: int, score_change: int = 0):
    #     '''
    #
    #     :param proxy_id:
    #     :param status:
    #     :param score_change:修改的分数值，+10，-10，或者不变
    #     :return:
    #     '''
    #     async with self.session() as session:
    #         sql = select(ProxyTab).where(ProxyTab.proxy_id == proxy_id).limit(1)
    #         async with session.begin():
    #             # async with self.async_lock:
    #             res = await session.execute(sql)
    #             grpc_proxy_detail: ProxyTab = res.scalars().first()
    #             if grpc_proxy_detail:
    #                 success_times = grpc_proxy_detail.success_times
    #                 if score_change > 0:
    #                     success_times += 1
    #                 else:
    #                     success_times -= 1
    #                 if grpc_proxy_detail.success_times > 100:
    #                     score_change = 100 - grpc_proxy_detail.score
    #                 elif grpc_proxy_detail.score < -50:
    #                     score_change = -50 - grpc_proxy_detail.score
    #                 await session.execute(
    #                     update(
    #                         ProxyTab
    #                     ).where(
    #                         ProxyTab.proxy_id == grpc_proxy_detail.proxy_id
    #                     ).values(
    #                         status=status,
    #                         score=grpc_proxy_detail.score + score_change,
    #                         success_times=success_times,
    #                         update_ts=int(time.time())
    #                     )
    #                 )
    #                 # async with self.async_lock:
    #                 await session.commit()
    #                 return
    #             # else:
    #             #     sql = insert(SDGrpcStat).values(
    #             #         proxy_id=proxy_id,
    #             #         sd_status=status,
    #             #         sd_score=score_change,
    #             #         sd_success_times=1 if score_change >= 0 else 0,
    #             #         sd_update_ts=int(time.time()),
    #             #     )
    #             #     # async with self.async_lock:
    #             #     await session.execute(sql)
    #             #     # 刷新自带的主键
    #             #     await session.flush()
    # @lock_wrapper
    # async def grpc_get_all_proxy_nums(self):
    #     sql = select(func.count(SDGrpcStat.proxy_id))
    #     async with self.session() as session:
    #         # async with self.async_lock:
    #         result = await session.execute(sql)
    #     res = result.scalars().first()
    #     if res:
    #         return res
    #     else:
    #         return 0
    # endregion
    @lock_wrapper
    async def get_proxy_by_ip(self, ip: str) -> Union[TypePDict, dict]:
        '''

                :param ip: 像这种格式的ip地址加端口 '127.0.0.1:1234'
                :return:
                '''
        ip = ip.replace('https', 'http')
        ip_str = ip if 'http' in ip else f'http://{ip}'
        ip_dict = {
            'http': ip_str,
            'https': ip_str
        }
        redis_data = await self.sub_redis_store.redis_get_proxy_by_ip(ip_dict=ip_dict)
        if redis_data:
            return preprocess_ret_list_dict(redis_data)
        sql_log.critical(f"get_proxy_by_ip redis get proxy failed, ip: {ip_dict}")
        str_dict = str(ip_dict)
        sql = select(ProxyTab).where(ProxyTab.proxy == str_dict).limit(1)
        async with self.session() as session:
            # async with self.async_lock:
            res = await session.execute(sql)
        result = res.scalars().first()
        if result:
            return preprocess_ret_list_dict(result.to_dict())
        else:
            return {}


SQLHelper = SQLHelperClass()

if __name__ == '__main__':
    async def _test_other_evnet():
        while 1:
            print(int(time.time()))
            await asyncio.sleep(0.5)
    async def _test_available_num():
        result = await SQLHelper.get_available_proxy_nums()
        print(result)

    async def _test():
        task = asyncio.create_task(_test_other_evnet())
        ret = await SQLHelper.check_redis_data(force=True)
        print(ret)
        task.cancel()


    asyncio.run(_test_available_num())
