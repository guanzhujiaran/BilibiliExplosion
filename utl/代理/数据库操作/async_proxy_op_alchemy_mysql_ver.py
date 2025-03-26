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
from enum import Enum
from typing import List, Literal
import pytz
from sqlalchemy import select, func, update, and_, or_, delete
from sqlalchemy.exc import InternalError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from CONFIG import CONFIG, database
from fastapi接口.log.base_log import sql_log
from fastapi接口.models.v1.background_service.background_service_model import ProxyStatusResp
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict
from utl.redisTool.RedisManager import RedisManagerBase
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from apscheduler.schedulers.asyncio import AsyncIOScheduler

MIN_REFRESH_SUCCESS_TIME = -5  # 最低允许刷新状态的代理获取请求成功次数


def lock_wrapper(_func: callable) -> callable:
    async def wrapper(*args, **kwargs):
        while True:
            try:
                res = await _func(*args, **kwargs)
                return res
            except InternalError as internal_error:
                sql_log.exception(internal_error)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue
            except Exception as e:
                sql_log.exception(e)
                await asyncio.sleep(random.choice([5, 6, 7]))
                continue

    return wrapper


class SubRedisStore(RedisManagerBase):
    class RedisMap(str, Enum):
        bili_proxy = 'bili_proxy'  # String类型数据的字符前缀
        bili_proxy_zset = 'zset_bili_proxy'  # 有序集合类型数据的字符前缀，里面只存放可用的代理
        bili_proxy_black = 'bili_proxy_black'  # 代理黑名单，也就是那些412或者352的没法用了的代理
        bili_proxy_sync_ts = f'sync_ts:{bili_proxy}'
        bili_proxy_changed = 'bili_proxy_changed'  # 代理是否发生变化
        count_bili_proxy = 'count_bili_proxy_set'  # 代理数量相关的数据 字符串set，自己解析json

    def __init__(self):
        super().__init__(db=database.proxySubRedis.db)
        self.sync_ts = 0
        self.sync_sep_ts = 0.5 * 60 * 60  # 半小时同步一次 耗时基本2000秒，就是半个小时
        self.RedisTimeout = 600

    async def _get_redis_count_by_prefix(self, prefix: RedisMap):
        cursor = 0
        count = 0
        match_str = f"{prefix.value}*"
        while True:
            cursor, keys = await self._scan(cursor=cursor, match_str=match_str)
            count += len(keys)
            if cursor == 0:
                break
        return count

    def dict_2_model(self, d: dict) -> ProxyTab:
        return ProxyTab(**d)

    def _get_scheme_ip_port(self, proxy_info_dict: ProxyTab.proxy) -> str:
        inner_key = proxy_info_dict.get("https", proxy_info_dict.get("http", proxy_info_dict.get("socks5",
                                                                                                 proxy_info_dict.get(
                                                                                                     "sock5"))))
        return inner_key

    def _gen_proxy_key(self, proxy_info_dict: dict | str, is_black: bool = False, is_changed: bool = False):
        """

        :param proxy_info_dict:{http:xxx,https:xxx,socks5:xxx,sock5:xxx}
        :return:
        """
        try:
            if isinstance(proxy_info_dict, str):
                proxy_info_dict = ast.literal_eval(proxy_info_dict)
            inner_key = proxy_info_dict.get("https", proxy_info_dict.get("socks5"))
        except Exception as e:
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
                [self._gen_proxy_key(proxy_info_dict=x.proxy) for x in proxy_infos],
                [json.dumps(sqlalchemy_model_2_dict(x)) for x in proxy_infos])
            await self._zadd(
                self.RedisMap.bili_proxy_zset,
                {self._get_scheme_ip_port(proxy_info_dict=x.proxy): x.score if x.score else 0 for x in proxy_infos}
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
        return [
            ProxyTab(**ast.literal_eval(x)) for x in
            await self._get_all_val_with_prefix(self.RedisMap.bili_proxy.value)
        ]

    async def redis_get_all_changed_proxy(self) -> List[ProxyTab]:
        return [ProxyTab(**ast.literal_eval(x)) for x in
                await self._get_all_val_with_prefix(self.RedisMap.bili_proxy_changed.value)]

    async def redis_get_proxy_by_ip(self, ip_dict: ProxyTab.proxy) -> ProxyTab | None:
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
            return ProxyTab(**ast.literal_eval(
                redis_data
            ))
        return None

    async def redis_select_one_proxy(self) -> ProxyTab | None | dict:
        """
        随机获取一个可用的代理
        :return:
        """
        while 1:
            if p := await self._zrand(key=self.RedisMap.bili_proxy_zset.value):
                if proxy_tab_dict := await self._get(self._gen_proxy_key(p)):
                    return self.dict_2_model(ast.literal_eval(proxy_tab_dict))
                else:
                    sql_log.debug(f"没找到对应代理数据：{p}")
                    continue
            else:
                break  # 这里才是真的redis里面没代理能用了
        sql_log.critical("redis中无可用代理！")
        return None

    async def redis_select_score_top_proxy(self) -> ProxyTab | None:
        if top_score_ip_dict := await self._zget_top_score(
                key=self.RedisMap.bili_proxy_zset.value,
                rand=True
        ):
            if proxy_tab_dict := await self._get(self._gen_proxy_key(top_score_ip_dict)):
                return self.dict_2_model(ast.literal_eval(proxy_tab_dict))
            return None

    async def redis_update_proxy(self, proxy_tab: ProxyTab, score_change_num: int) -> bool:
        """

        :param proxy_tab:
        :param score_change_num:
        :return:
        """
        redis_data: ProxyTab = await self.redis_get_proxy_by_ip(proxy_tab.proxy)
        succ_times_num = 1 if score_change_num >= 0 else -1
        redis_data.status = proxy_tab.status
        redis_data.score += score_change_num
        redis_data.success_times += succ_times_num
        await self._set(
            key=self._gen_proxy_key(redis_data.proxy, is_changed=True),
            value=json.dumps(sqlalchemy_model_2_dict(redis_data))
        )  # 变更的key

        if proxy_tab.status != 0:
            await self._set(
                key=self._gen_proxy_key(redis_data.proxy, is_black=True),
                value=json.dumps(sqlalchemy_model_2_dict(redis_data))
            )  # 黑名单的key
            await self._zdel_elements(  # 这样就不会把不能用的代理再次取出来了
                self.RedisMap.bili_proxy_zset.value,
                self._get_scheme_ip_port(proxy_info_dict=redis_data.proxy)
            )
        else:
            await self._set(
                key=self._gen_proxy_key(redis_data.proxy),
                value=json.dumps(sqlalchemy_model_2_dict(redis_data))
            )  # 全局的key
            await self._zadd(self.RedisMap.bili_proxy_zset,
                             {self._get_scheme_ip_port(proxy_info_dict=redis_data.proxy): redis_data.score})

    async def redis_clear_all_proxy(self):
        await self.redis_clear_black_proxy()
        await self.redis_clear_changed_proxy()
        await self._del(self.RedisMap.bili_proxy_zset.value)
        return await self._del_keys_with_prefix(self.RedisMap.bili_proxy.value)

    async def redis_clear_black_proxy(self):
        return await self._del_keys_with_prefix(self.RedisMap.bili_proxy_black.value)

    async def redis_clear_changed_proxy(self):
        return await self._del_keys_with_prefix(self.RedisMap.bili_proxy_changed.value)

    async def set_proxy_status(self, m: ProxyStatusResp):
        await self._set(self.RedisMap.count_bili_proxy.value, json.dumps(m.model_dump(), ensure_ascii=False))

    async def get_proxy_status(self) -> ProxyStatusResp:
        """
                        ## 设置一次大概10秒钟，能够接受
        :return:
        """
        # 从Redis中获取代理状态
        result = await self._get(self.RedisMap.count_bili_proxy.value)
        # 如果获取到了结果，则将结果转换为ProxyStatusResp对象
        if result:
            ret_model = ProxyStatusResp(**ast.literal_eval(result))
        # 如果没有获取到结果，则将ret_model设置为None
        else:
            ret_model = None
        return ret_model

    async def refresh_proxy_database_redis(self):
        # 使用asyncio.gather并行获取MySQL和Redis中的代理状态
        (
            mysql_sync_redis_ts,
            proxy_black_count,
            proxy_unknown_count,
            free_proxy_fetch_ts
        ) = await asyncio.gather(
            self.get_sync_ts(),
            self._get_redis_count_by_prefix(self.RedisMap.bili_proxy_black),
            self._zcard(self.RedisMap.bili_proxy_zset),
            SQLHelper.get_latest_add_ts()
        )

        # 将获取到的代理状态转换为ProxyStatusResp对象
        ret_model = ProxyStatusResp(
            mysql_sync_redis_ts=mysql_sync_redis_ts,
            proxy_total_count=proxy_black_count + proxy_unknown_count,
            proxy_black_count=proxy_black_count,
            proxy_unknown_count=proxy_unknown_count,
            free_proxy_fetch_ts=free_proxy_fetch_ts,
            sync_ts=int(time.time())
        )
        # 将代理状态设置到Redis中
        await self.set_proxy_status(ret_model)


class SQLHelperClass:
    def __init__(self):
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
        self.schd = AsyncIOScheduler()
        self.schd.add_job(self.background_service, 'interval', seconds=600, next_run_time=datetime.datetime.now(),
                          misfire_grace_time=600)
        self.schd.start()
        self.sub_redis_store = SubRedisStore()
        self.lock = asyncio.Lock()
        self.is_sync = False

    async def sync_2_database(self):
        if all_proxy_infos := await self.sub_redis_store.redis_get_all_changed_proxy():
            async with self.session() as session:
                lst = [{
                    "proxy_id": proxy_info.proxy_id,
                    "status": proxy_info.status,
                    "update_ts": proxy_info.update_ts,
                    "score": proxy_info.score,
                    "success_times": proxy_info.success_times,
                } for proxy_info in all_proxy_infos if proxy_info.proxy_id and proxy_info.proxy]
                sql_log.debug(f'开始更新MySQL中数据，共{len(lst)}条数据需要更新')
                await session.run_sync(lambda s: s.bulk_update_mappings(
                    ProxyTab,
                    lst,
                ))
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
                    sql_log.debug(
                        f'上次同步时间：{datetime.datetime.fromtimestamp(redis_sync_ts, tz=pytz.UTC)}\n开始同步redis和mysql数据库')
                    start_ts = int(time.time())
                    sql_log.debug('开始将redis数据同步至MySQL中')
                    await self.sync_2_database()
                    sql_log.debug(f'将redis数据同步至MySQL中完成，耗时：{int(time.time() - start_ts)}秒！')

                    sql_log.debug(f'开始清空redis中数据')
                    await self.sub_redis_store.redis_clear_all_proxy()
                    sql_log.debug(f'清空redis中数据完成，耗时：{int(time.time() - start_ts)}秒！')

                    sql_log.debug(f'开始清理无法使用的mysql中的代理数据')
                    clean_unusable_proxy_num = await self.clear_unusable_proxy()
                    sql_log.debug(f'清理无法使用的mysql中的代理数据完成，清理了{clean_unusable_proxy_num}条无效代理，耗时：{int(time.time() - start_ts)}秒！')

                    sql_log.debug(f'开始获取MySQL中可用代理数据')
                    all_available_proxy_infos = await self.select_proxy(mode="all")
                    sql_log.debug(f'获取MySQL中可用代理数据完成，耗时：{int(time.time() - start_ts)}秒！')

                    sql_log.debug(f'开始将MySQL内容同步至redis中')
                    await self.sub_redis_store.sync_2_redis(all_available_proxy_infos)
                    sql_log.debug(f'将MySQL内容同步至redis中完成，耗时：{int(time.time() - start_ts)}秒！')
                    await self.sub_redis_store.set_sync_ts()
                    sql_log.debug(f'同步redis和mysqlMySQL完成，耗时{int(time.time() - start_ts)}秒！')
            except Exception as e:
                sql_log.exception(f'同步redis和mysql数据库失败！{e}')
                raise e
            finally:
                self.is_sync = False
                sql_log.debug(f'同步redis和mysql数据库任务完成！')
        else:
            sql_log.debug(
                f'上次同步时间：{datetime.datetime.fromtimestamp(self.sub_redis_store.sync_sep_ts, tz=pytz.UTC)}\n距离上次同步时间小于{self.sub_redis_store.sync_sep_ts}秒，无需同步')

    async def background_service(self):
        start_ts = int(time.time())
        sql_log.critical('开始后台定时任务')
        await asyncio.gather(
            *[
                self.refresh_proxy(),
                self.sync_proxy_database_redis(),
                self.refresh_proxy_status()
            ]
        )
        sql_log.critical(f'定时任务执行完毕，耗时：{int(time.time()) - start_ts}秒')

    @lock_wrapper
    async def clear_unusable_proxy(self) -> int:
        """
        清除数据库中的不可用的代理，根据score和success_times判断
        主要用于同步到redis之前，将不可用的清理掉
        :return:
        """
        async with self.session() as session:
            sql = delete(ProxyTab).where(
                and_(ProxyTab.score <= -10, ProxyTab.success_times < MIN_REFRESH_SUCCESS_TIME))  # 负分就删除了
            res = await session.execute(sql)
            await session.commit()
            return res.rowcount

    @lock_wrapper
    async def select_score_top_proxy(self) -> ProxyTab:
        if redis_data := await self.sub_redis_store.redis_select_score_top_proxy():
            return redis_data
        sql = select(ProxyTab).order_by(ProxyTab.score.desc()).limit(1)
        async with self.session() as session:
            res = await session.execute(sql)
        ret_list_dict = res.scalars().first()
        return ret_list_dict

    @lock_wrapper
    async def select_proxy(self, mode: Literal["single", "all", "rand"] = 'single', channel='bili') -> ProxyTab | List[
        ProxyTab] | None:
        """
        选择一个可用的代理
        :param channel:
        :param mode: single 就选择分数最高的未被风控的代理 默认是rand，改成single之后从分数最高的代理开始用，这样获取响应特别快
        :return:[{...}, {...}] proxy_dict
        """
        if mode != "all":
            if mode == "single":
                return await self.sub_redis_store.redis_select_score_top_proxy()
            if mode == "rand":
                return await self.sub_redis_store.redis_select_one_proxy()
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
        if mode == 'all':
            ret_list_dict = res.scalars().all()
            return list(ret_list_dict)
        else:
            ret_list_dict = res.scalars().first()
            if ret_list_dict:
                return ret_list_dict
            else:
                return None

    @lock_wrapper
    async def is_exist_proxy_by_proxy(self, proxy: ProxyTab.proxy) -> int:
        '''
        查询是否存在这个代理
        :param proxy:{'http':xxxx, 'https':xxxx}
        :return:int 1：存在 0：不存在
        '''
        sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.proxy == proxy)
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
                res = await session.execute(sql)
                original = res.scalars().all()
                if not original:
                    # sql_log.debug("grpc数据都在主表中！")
                    return True
                for record in original:
                    await session.delete(record)
            return True

    @lock_wrapper
    async def update_to_proxy_list(self, proxy_tab: ProxyTab, change_score_num=10) -> bool:
        '''
        更新数据 update 最好只用update，upsert会导致主键增长异常
        :param change_score_num: 修改的分
        :param proxy_tab:
        :return:
        '''
        try:
            is_update = await self.sub_redis_store.redis_update_proxy(proxy_tab, change_score_num)
            return is_update
        except Exception as e:
            sql_log.exception(e)
        succ_times_num = 1 if change_score_num >= 0 else -1
        sql = update(ProxyTab).where(
            ProxyTab.proxy_id == proxy_tab.proxy_id
        ).values(
            status=proxy_tab.status,
            score=ProxyTab.score + change_score_num,
            success_times=proxy_tab.success_times + succ_times_num,
            update_ts=proxy_tab.update_ts,
            add_ts=proxy_tab.add_ts
        )
        async with self.session() as session:
            async with session.begin():
                # async with self.async_lock:
                result = await session.execute(sql)
                updated_proxy_tab = result.scalars().all()
        return True

    @lock_wrapper
    async def add_to_proxy_tab_database(self, proxy_tab: ProxyTab) -> bool:
        '''
        添加数据
        :param proxy_tab:
        :return:
        '''
        async with self.session() as session:
            async with session.begin():
                session.add(proxy_tab)
                # 刷新自带的主键
                # async with self.async_lock:
                await session.flush()
                # 释放这个data数据
                session.expunge(proxy_tab)
        return True

    @lock_wrapper
    async def remove_proxy(self, proxy_tab: ProxyTab):
        '''
        删除
        :param proxy_tab:
        :return:
        '''
        async with self.session() as session:
            sql = select(ProxyTab).where(ProxyTab.proxy_id == proxy_tab.proxy_id)  # 删除无效代理，暂时先不用
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
            result = await session.execute(sql)
        res = result.scalars().first()
        return res

    async def get_latest_add_ts(self) -> int:
        try:
            sql = select(ProxyTab).order_by(ProxyTab.add_ts.desc()).limit(1)
            async with self.session() as session:
                result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res.add_ts
            else:
                return 0
        except Exception as e:
            sql_log.exception(e)
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

    # region 定时任务
    async def refresh_proxy(self):
        while 1:
            try:
                sql_log.critical('开始刷新数据库中代理')
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
                    ProxyTab.success_times >= MIN_REFRESH_SUCCESS_TIME
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
            except Exception as e:
                sql_log.exception(e)

    async def refresh_proxy_status(self):
        sql_log.critical('开始同步redis和数据库中代理状态的数据统计')
        await self.sub_redis_store.refresh_proxy_database_redis()

    async def sync_proxy_database_redis(self):
        sql_log.critical('开始同步redis和数据库中代理')

        await self.check_redis_data()

    # endregion

    @lock_wrapper
    async def get_proxy_by_ip(self, ip: str) -> ProxyTab | None:
        """

        :param ip: 像这种格式的ip地址加端口加scheme的str 'https://127.0.0.1:1234'
        :return:
        """
        ip = ip.replace('https', 'http')
        ip_dict = {
            'http': ip,
            'https': ip
        }
        redis_data: ProxyTab | None = await self.sub_redis_store.redis_get_proxy_by_ip(ip_dict=ip_dict)
        if redis_data:
            return redis_data
        str_dict = str(ip_dict)
        sql = select(ProxyTab).where(ProxyTab.proxy == str_dict).limit(1)
        async with self.session() as session:
            # async with self.async_lock:
            res = await session.execute(sql)
            result: ProxyTab | None = res.scalars().first()
        if result:
            return result
        else:
            return None


SQLHelper = SQLHelperClass()

if __name__ == '__main__':
    async def _test_other_evnet():
        while 1:
            print(int(time.time()))
            await asyncio.sleep(1)


    async def _test_available_num():
        result = await SQLHelper.get_available_proxy_nums()
        print(result)


    async def _test():
        task = asyncio.create_task(_test_other_evnet())
        ret = await SQLHelper.clear_unusable_proxy()
        print(ret)
        task.cancel()


    asyncio.run(_test())
