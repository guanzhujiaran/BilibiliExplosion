# -*- coding: utf-8 -*-
"""
异步sqlalchemy操作方法
"""
import ast
import asyncio
import datetime
import json
import time
from enum import StrEnum
from typing import List, Literal
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, update, and_, or_, delete
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from CONFIG import CONFIG
from dao.base.sqlHelperBase import SqlHelperBase
from log.base_log import sql_log
from Models.v1.background_service.background_service_model import ProxyStatusResp
from Utils.通用.Common import GLOBAL_SCHEDULER, log_sql_retry_wrapper, asyncio_gather
from Utils.数据库.SqlalchemyTool import sqlalchemy_model_2_dict
from Utils.redisTool.RedisManager import RedisManagerBase
from Utils.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab, AvailableProxy
from Utils.代理.数据库操作.available_proxy_sql_helper import sql_helper
from Utils.代理.数据库操作.comm import get_scheme_ip_port_form_proxy_dict

MIN_REFRESH_SUCCESS_TIME = -3  # 最低允许刷新状态的代理获取请求成功次数
MIN_REFRESH_SCORE = 0  # 最低允许刷新状态的代理分数
DEFAULT_CHUNK_SIZE = 1000  # Adjust as needed

database = CONFIG.database
class SubRedisStore(RedisManagerBase):
    class RedisMap(StrEnum):
        bili_proxy_available_hm = 'bili_proxy_available_hm'  # 存放可用代理的hash表（虽说是可用，但是还没确认
        bili_proxy_black_hm = 'bili_proxy_black_hm'  # 存放黑名单的hash表
        bili_proxy_changed_hm = 'bili_proxy_changed_hm'  # 存放代理发生变化的hash表
        bili_proxy_sync_ts = f'sync_ts:bili_proxy'
        bili_proxy_zset = 'zset_bili_proxy'  # 有序集合类型数据的字符前缀，里面只存放可用的代理

    async def get_bili_proxy_all_num(self):
        return await self.get_bili_proxy_black_num() + await self._hlen(
            self.RedisMap.bili_proxy_available_hm.value)

    async def get_bili_proxy_black_num(self):
        return await self._hlen(self.RedisMap.bili_proxy_black_hm.value)

    def __init__(self):
        super().__init__(db=database.proxySubRedis.db)
        self.sync_ts = 0
        self.sync_sep_ts = 0.5 * 60 * 60  # 0.5小时同步一次，同步的时候锁死无法获取代理
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

    def _gen_proxy_key(self, proxy_info_dict: dict | str, is_black: bool = False, is_changed: bool = False):
        """

        :param proxy_info_dict:{http:xxx,https:xxx,socks5:xxx,sock5:xxx}
        :return:
        """
        try:
            if isinstance(proxy_info_dict, str):
                proxy_info_dict = json.loads(proxy_info_dict)
            inner_key = get_scheme_ip_port_form_proxy_dict(proxy_info_dict)
        except Exception as e:
            inner_key = str(proxy_info_dict)
        if is_black:
            # return f'{self.RedisMap.bili_proxy_black.value}:{inner_key}'
            return self.RedisMap.bili_proxy_black_hm.value, inner_key
        if is_changed:
            # return f'{self.RedisMap.bili_proxy_changed.value}:{inner_key}'
            return self.RedisMap.bili_proxy_changed_hm.value, inner_key
        # return f'{self.RedisMap.bili_proxy.value}:{inner_key}'
        return self.RedisMap.bili_proxy_available_hm.value, inner_key

    @log_sql_retry_wrapper()
    async def sync_2_redis(self, proxy_infos: List[ProxyTab]):
        """
        同步代理到redis
        :param proxy_infos:
        :return:
        """
        if proxy_infos:
            await self._hmset_bulk_batch(
                hm_name=self.RedisMap.bili_proxy_available_hm.value,
                hm_k_v_List=[
                    {
                        self._gen_proxy_key(x.proxy)[1]: json.dumps(sqlalchemy_model_2_dict(x))
                    } for x in proxy_infos
                ]
            )
            await self._zadd(
                self.RedisMap.bili_proxy_zset.value,
                {get_scheme_ip_port_form_proxy_dict(proxy_info_dict=x.proxy): x.score if x.score is None else 0 for x in
                 proxy_infos}
            )

    @log_sql_retry_wrapper()
    async def set_sync_ts(self):
        self.sync_ts = int(time.time())
        await self._set(self.RedisMap.bili_proxy_sync_ts.value, self.sync_ts)

    @log_sql_retry_wrapper()
    async def get_sync_ts(self) -> int:
        if self.sync_ts:
            return self.sync_ts
        _ = await self._get(self.RedisMap.bili_proxy_sync_ts.value)
        return int(_) if _ else 0

    async def redis_get_all_changed_proxy(self) -> List[ProxyTab]:
        all_changed_proxy_dict = await self._hgetall(self.RedisMap.bili_proxy_changed_hm.value)
        ret_list = []
        for k, v in all_changed_proxy_dict.items():
            ret_list.append(ProxyTab(**json.loads(v)))
        del all_changed_proxy_dict
        return ret_list

    async def redis_get_proxy_by_ip(self, ip_dict: ProxyTab.proxy, from_changed=False) -> ProxyTab | None:
        """
        ip_dict = {
            'http': ip_str,
            'https': ip_str
        }
        :param from_changed:
        :param ip_dict:
        :return:
        """
        redis_data = await self._hmget(
            *self._gen_proxy_key(proxy_info_dict=ip_dict, is_changed=from_changed)
        )
        if redis_data:
            redis_dict = json.loads(redis_data)
            return ProxyTab(**redis_dict)
        return None

    async def redis_bili_proxy_zset_count(self) -> int:
        total_count = await self._zcard(key=self.RedisMap.bili_proxy_zset.value)
        if total_count:
            return int(total_count)
        else:
            return 0

    async def redis_select_one_proxy(self) -> ProxyTab | None:
        """
        随机获取一个可用的代理
        :return:
        """
        while 1:
            total_count = await self.redis_bili_proxy_zset_count()
            if total_count <= 300:
                return None
            rand_redis_proxy = await self._zrand_member(key=self.RedisMap.bili_proxy_zset.value, count=1)
            p = rand_redis_proxy[0] if rand_redis_proxy and type(rand_redis_proxy) is list and len(
                rand_redis_proxy) > 0 else None
            if p:
                if proxy_tab_dict := await self._hmget(
                        *self._gen_proxy_key(proxy_info_dict=p)
                ):
                    return self.dict_2_model(json.loads(proxy_tab_dict))

    async def redis_select_score_top_proxy(self) -> ProxyTab | None:
        if top_score_ip_dict := await self._zget_top_score(
                key=self.RedisMap.bili_proxy_zset.value,
                rand=True
        ):
            if proxy_tab_dict := await self._hmget(
                    *self._gen_proxy_key(proxy_info_dict=top_score_ip_dict)
            ):
                return self.dict_2_model(json.loads(proxy_tab_dict))
            return None

    async def redis_update_proxy(self, proxy_tab: ProxyTab, score_change_num: int) -> bool | None:
        """

        :param proxy_tab:
        :param score_change_num:
        :return:
        """
        redis_data: ProxyTab = await self.redis_get_proxy_by_ip(proxy_tab.proxy, from_changed=True)
        if not redis_data:
            redis_data: ProxyTab = await self.redis_get_proxy_by_ip(proxy_tab.proxy, from_changed=False)
            if not redis_data:
                return False
        succ_times_num = 1 if score_change_num >= 0 else -1
        redis_data.status = proxy_tab.status
        redis_data.score += score_change_num
        if redis_data.score > 10000:
            redis_data.score = 10000
        redis_data.success_times = (redis_data.success_times or 0) + succ_times_num
        await self._hmset(
            name=self.RedisMap.bili_proxy_changed_hm.value,
            field_values={
                self._gen_proxy_key(redis_data.proxy, is_changed=True)[1]: json.dumps(
                    sqlalchemy_model_2_dict(redis_data))
            }
        )
        if proxy_tab.status != 0:
            await self._hmset(
                name=self.RedisMap.bili_proxy_black_hm.value,
                field_values={self._gen_proxy_key(redis_data.proxy, is_black=True)[1]: json.dumps(
                    sqlalchemy_model_2_dict(redis_data))}
            )  # 黑名单的key
            await self._hdel(*self._gen_proxy_key(redis_data.proxy))
            await self._zdel_elements(  # 这样就不会把不能用的代理再次取出来了
                self.RedisMap.bili_proxy_zset.value,
                get_scheme_ip_port_form_proxy_dict(proxy_info_dict=redis_data.proxy)
            )
        else:
            await self._hmset(
                name=self.RedisMap.bili_proxy_available_hm,
                field_values={
                    self._gen_proxy_key(redis_data.proxy)[1]: json.dumps(sqlalchemy_model_2_dict(redis_data))
                }
            )  # 全局的key
            await self._zadd(
                self.RedisMap.bili_proxy_zset.value,
                {get_scheme_ip_port_form_proxy_dict(proxy_info_dict=redis_data.proxy): redis_data.score})

    @log_sql_retry_wrapper()
    async def redis_clear_all_proxy(self):
        # await self._zdel_range(self.RedisMap.bili_proxy_zset.value, 0, -1)
        # await self._del_keys_with_prefix(self.RedisMap.bili_proxy.value)
        await self.redis_clear_black_proxy()
        await self.redis_clear_changed_proxy()

    async def redis_clear_black_proxy(self):
        return await self._delete(self.RedisMap.bili_proxy_black_hm.value)

    async def redis_clear_changed_proxy(self):
        return await self._delete(self.RedisMap.bili_proxy_changed_hm.value)


class SQLHelperClass(SqlHelperBase):
    def __init__(self):
        mysql_db_url = CONFIG.database.MYSQL.proxy_db_URI
        # 爬虫专用连接池，设置 is_crawler=True
        super().__init__(mysql_db_url=mysql_db_url, is_crawler=True)
        self._lock = asyncio.Lock()
        self._underscore_spe_time = 24 * 3600  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600  # 0分以上但是"-412"风控的代理休眠时间
        self.engine.dialect.supports_sane_rowcount = False  # 避免了批量update报错stableData
        GLOBAL_SCHEDULER.add_job(self.refresh_proxy, 'interval', seconds=600, next_run_time=datetime.datetime.now(),
                                 misfire_grace_time=600)
        GLOBAL_SCHEDULER.add_job(self.sync_proxy_database_redis, 'interval', seconds=1 * 60 * 60,
                                 next_run_time=datetime.datetime.now(),
                                 misfire_grace_time=600)
        self.sub_redis_store = SubRedisStore()
        self.is_checking_redis_data = False

    @log_sql_retry_wrapper()
    async def sync_2_database(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Fetches changed proxy info from Redis and bulk updates them in the database.
        Processes data in chunks to manage memory for very large datasets.
        """
        try:
            all_proxy_infos = await self.sub_redis_store.redis_get_all_changed_proxy()
            if not all_proxy_infos:
                sql_log.info("No proxy data changes found in Redis to sync.")
                return

            # Prepare data efficiently (using a generator expression initially if memory is a concern)
            # However, bulk methods need a list, so we'll chunk the final list.
            update_mappings = [
                {
                    "proxy_id": proxy_info.proxy_id,
                    "status": proxy_info.status,
                    "update_ts": proxy_info.update_ts,
                    "score": proxy_info.score,
                    "success_times": proxy_info.success_times,
                    # Add other fields relevant to ProxyTab here
                }
                for proxy_info in all_proxy_infos
                if proxy_info.proxy_id and proxy_info.proxy  # Your filter condition
            ]
            # Clear the large list from memory if it helps (Python's GC usually handles this)
            del all_proxy_infos
            total_proxies_to_update = len(update_mappings)
            if not total_proxies_to_update:
                sql_log.info("Filtered proxy list is empty. No updates to perform.")
                return

            async def _update_single(cur_chunk: int):
                chunk = update_mappings[_: _ + chunk_size]
                if not chunk:
                    return
                while 1:
                    try:
                        async with self.async_session() as session:
                            # sql_log.critical(
                            #     f"Processing chunk {cur_chunk // chunk_size + 1}/{total_proxies_to_update // chunk_size}: {len(chunk)}")
                            # Use run_sync for the synchronous bulk operation
                            await session.run_sync(
                                lambda s: s.bulk_update_mappings(ProxyTab, chunk)
                            )
                            await session.commit()
                            # sql_log.critical(
                            #     f"Processing chunk {cur_chunk // chunk_size + 1}/{total_proxies_to_update // chunk_size}: {len(chunk)} success!")
                        break
                    except Exception as e:
                        sql_log.error(f"An unexpected error occurred: {e}")
                        await asyncio.sleep(10)

            try:
                tasks = set()
                for _ in range(0, total_proxies_to_update, chunk_size):
                    tasks.add(asyncio.create_task(_update_single(_)))
                await asyncio_gather(*tasks, log=sql_log)
            except Exception as err:
                # Catch other potential errors during processing
                sql_log.error(f"An unexpected error occurred: {err}")
        except Exception as err:
            # Catch errors during Redis fetch or initial data processing
            sql_log.error(f"Error during sync_2_database setup: {err}")
            # Handle error appropriately

    async def check_redis_data(self, force=False):
        if not self.sub_redis_store.sync_ts:
            async with self._lock:
                if not self.sub_redis_store.sync_ts:
                    self.sub_redis_store.sync_ts = await self.sub_redis_store.get_sync_ts()
        if not self.is_checking_redis_data:
            async with self._lock:
                if not self.is_checking_redis_data:
                    if int(time.time()) - self.sub_redis_store.sync_sep_ts > self.sub_redis_store.sync_ts or force or self.sub_redis_store.sync_ts == 0:
                        self.is_checking_redis_data = True
                        try:
                            redis_sync_ts = await self.sub_redis_store.get_sync_ts()
                            if redis_sync_ts < int(time.time()) - self.sub_redis_store.sync_sep_ts or force:
                                await self.sync_2_database()
                                await self.sub_redis_store.redis_clear_all_proxy()  # 不清除还没使用的代理
                                await self.clear_unusable_proxy()
                                all_available_proxy_infos = await self.select_proxy(mode="all")
                                await self.sub_redis_store.sync_2_redis(all_available_proxy_infos)
                                await self.sub_redis_store.set_sync_ts()
                        except Exception as e:
                            sql_log.exception(f'同步redis和mysql数据库失败！{e}')
                            raise e
                        finally:
                            self.is_checking_redis_data = False
                    else:
                        sql_log.debug(
                            f'上次同步时间：{datetime.datetime.fromtimestamp(self.sub_redis_store.sync_ts, tz=ZoneInfo("Asia/Shanghai"))}\n距离上次同步时间小于{self.sub_redis_store.sync_sep_ts}秒，无需同步')

    @log_sql_retry_wrapper()
    async def clear_unusable_proxy(self):
        """
        清除数据库中的不可用的代理，根据score和success_times判断
        主要用于同步到redis之前，将不可用的清理掉
        :return:
        """
        async with self.async_session() as session:
            # 查找所有将要被删除的 proxy_tab_id
            stmt = select(ProxyTab.proxy_id).where(
                or_(ProxyTab.score <= MIN_REFRESH_SCORE, ProxyTab.success_times < MIN_REFRESH_SUCCESS_TIME)
            )
            result = await session.execute(stmt)
            proxy_ids_to_delete = [row[0] for row in result.all()]

            if not proxy_ids_to_delete:
                return 0
            # 先删除子表数据
            delete_available_proxy = delete(AvailableProxy).where(
                AvailableProxy.proxy_tab_id.in_(proxy_ids_to_delete)
            )
            await session.execute(delete_available_proxy)

            # 再删除父表数据
            delete_proxy_tab = delete(ProxyTab).where(
                ProxyTab.proxy_id.in_(proxy_ids_to_delete)
            )
            res = await session.execute(delete_proxy_tab)

            await session.commit()
            return res.rowcount

    @log_sql_retry_wrapper()
    async def select_score_top_proxy(self) -> ProxyTab:
        if redis_data := await self.sub_redis_store.redis_select_score_top_proxy():
            return redis_data
        sql = select(ProxyTab).order_by(ProxyTab.score.desc()).limit(1)
        async with self.async_session() as session:
            res = await session.execute(sql)
        ret_list_dict = res.scalars().first()
        return ret_list_dict

    @log_sql_retry_wrapper()
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
        async with self.async_session() as session:
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

    @log_sql_retry_wrapper()
    async def is_exist_proxy_by_proxy(self, proxy: ProxyTab.proxy) -> int:
        '''
        查询是否存在这个代理
        :param proxy:{'http':xxxx, 'https':xxxx}
        :return:int 1：存在 0：不存在
        '''
        proxy_str = get_scheme_ip_port_form_proxy_dict(proxy)
        sql = select(func.count(ProxyTab.proxy_id)).where(
            ProxyTab.computed_proxy_str == proxy_str
        )
        async with self.async_session() as session:
            res = await session.execute(sql)
            exist_num = res.scalars().first()
        return exist_num or 0

    @log_sql_retry_wrapper()
    async def remove_list_dict_data_by_proxy(self) -> bool:
        '''
        根据proxy列对数据库table去重
        :return:
        '''
        subquery = select(func.max(ProxyTab.proxy_id)).group_by(ProxyTab.proxy)
        sql = select(ProxyTab).where(ProxyTab.proxy_id.not_in(subquery))
        async with self.async_session() as session:
            async with session.begin():
                res = await session.execute(sql)
                original = res.scalars().all()
                if not original:
                    sql_log.info("代理数据重复记录不存在")
                    return True
                for record in original:
                    await session.delete(record)
        return True

    @log_sql_retry_wrapper()
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
            success_times=(proxy_tab.success_times or 0) + succ_times_num,
            update_ts=proxy_tab.update_ts,
            add_ts=proxy_tab.add_ts
        )
        async with self.async_session() as session:
            async with session.begin():
                # async with self.async_lock:
                await session.execute(sql)
        return True

    @log_sql_retry_wrapper()
    async def add_to_proxy_tab_database(self, proxy_tab: ProxyTab) -> bool:
        '''
        添加数据（带 MySQL ON DUPLICATE KEY UPDATE）
        :param proxy_tab:
        :return:
        '''
        async with self.async_session() as session:
            async with session.begin():
                # 通过 MySQL 方言实现幂等 upsert
                data_dict = sqlalchemy_model_2_dict(proxy_tab)
                # 过滤掉 MySQL 生成列，避免 (3105) 错误
                data_dict.pop("computed_proxy_str", None)
                stmt = mysql_insert(ProxyTab.__table__).values(**data_dict)
                # 非主键字段使用 INSERT 值更新，同时排除生成列
                update_cols = {
                    c.name: stmt.inserted[c.name]
                    for c in ProxyTab.__table__.columns
                    if not c.primary_key and c.name != "computed_proxy_str"
                }
                await session.execute(stmt.on_duplicate_key_update(**update_cols))
                # 刷新生成的主键或其它服务器端默认值
                await session.flush()
                # 释放这个data数据，避免持久化会话耦合

        return True

    @log_sql_retry_wrapper()
    async def remove_proxy(self, proxy_tab: ProxyTab):
        """
        删除
        :param proxy_tab:
        :return:
        """
        async with self.async_session() as session:
            sql = select(ProxyTab).where(ProxyTab.proxy_id == proxy_tab.proxy_id)  # 删除无效代理，暂时先不用
            async with session.begin():
                res = await session.execute(sql)
                original = res.scalars().all()
                if original:
                    for record in original:
                        # async with self.async_lock:
                        await session.delete(record)

    @log_sql_retry_wrapper()
    async def get_412_proxy_num(self) -> int:
        sql = select(func.count(ProxyTab.proxy_id)).where(ProxyTab.status == -412)
        async with self.async_session() as session:
            result = await session.execute(sql)
        res = result.scalars().first()
        return res

    async def get_latest_add_ts(self) -> int:
        try:
            sql = select(ProxyTab).order_by(ProxyTab.add_ts.desc()).limit(1)
            async with self.async_session() as session:
                result = await session.execute(sql)
            res = result.scalars().first()
            if res:
                return res.add_ts
            else:
                return 0
        except Exception as e:
            sql_log.exception(e)
            return 0

    @log_sql_retry_wrapper()
    async def get_all_proxy_nums(self) -> int:
        sql = select(func.count(ProxyTab.proxy_id))
        async with self.async_session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        if res:
            return res
        else:
            return 0

    @log_sql_retry_wrapper()
    async def get_available_proxy_nums(self):
        sql = select(func.count(ProxyTab.proxy_id)).where(and_(ProxyTab.score >= 0, ProxyTab.status != -412))
        async with self.async_session() as session:
            # async with self.async_lock:
            result = await session.execute(sql)
        res = result.scalars().first()
        if res:
            return res
        else:
            return 0

    # region 定时任务
    @log_sql_retry_wrapper()
    async def refresh_proxy(self):
        start_ts = int(time.time())
        avaliable_score = -50
        available_status = 0
        now = int(time.time())
        _412_sep_time = self._412_sep_time
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
        async with self.async_session() as session:
            async with session.begin():
                await session.execute(___sql)  # 刷新超过两小时的412风控代理 不改变分数，只改变status
                await session.execute(__sql)  # 刷新超过12小时的无效代理，改变status和score
                await session.commit()
        return

    async def sync_proxy_database_redis(self):
        await self.check_redis_data()

    # endregion

    @log_sql_retry_wrapper()
    async def get_proxy_by_ip(self, ip: str) -> ProxyTab | None:
        """

        :param ip: 像这种格式的ip地址加端口加scheme的str 'https://127.0.0.1:1234'
        :return:
        """
        ip_dict = {
            'http': ip,
            'https': ip
        }
        redis_data: ProxyTab | None = await self.sub_redis_store.redis_get_proxy_by_ip(ip_dict=ip_dict)
        if redis_data:
            return redis_data
        sql = select(ProxyTab).where(ProxyTab.proxy.like(ip)).limit(1)
        async with self.async_session() as session:
            # async with self.async_lock:
            res = await session.execute(sql)
            result: ProxyTab | None = res.scalars().first()
        if result:
            return result
        else:
            return None

    async def get_proxy_database_redis(self) -> ProxyStatusResp:
        # 使用asyncio_gather并行获取MySQL和Redis中的代理状态
        (
            mysql_sync_redis_ts,
            proxy_black_count,
            proxy_unknown_count,
            free_proxy_fetch_ts,
            proxy_usable_count
        ) = await asyncio_gather(
            self.sub_redis_store.get_sync_ts(),
            self.sub_redis_store.get_bili_proxy_black_num(),
            self.sub_redis_store.redis_bili_proxy_zset_count(),
            SQLHelper.get_latest_add_ts(),
            sql_helper.get_num(True),  # 获取可用代理的数量
            log=sql_log
        )
        # 将获取到的代理状态转换为ProxyStatusResp对象
        ret_model = ProxyStatusResp(
            mysql_sync_redis_ts=mysql_sync_redis_ts,
            proxy_total_count=proxy_black_count + proxy_unknown_count,
            proxy_black_count=proxy_black_count,
            proxy_unknown_count=proxy_unknown_count,
            proxy_usable_count=proxy_usable_count,
            free_proxy_fetch_ts=free_proxy_fetch_ts,
            sync_ts=int(time.time()),
        )
        return ret_model


SQLHelper = SQLHelperClass()

if __name__ == "__main__":
    async def _test_redis_select_one_proxy():
        print(await SQLHelper.sub_redis_store.redis_select_one_proxy())


    async def _test_redis_get_proxy_by_ip():
        print(await SQLHelper.sub_redis_store.redis_get_proxy_by_ip(
            ip_dict={
                "http": "http://116.203.206.103:8080",
                "https": "http://116.203.206.103:8080"
            }
        ))


    asyncio.run(_test_redis_get_proxy_by_ip())
