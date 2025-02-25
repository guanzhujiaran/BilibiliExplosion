# -*- coding: utf-8 -*-
import asyncio
import datetime
from typing import Literal, List, Sequence, Union
import numpy as np
from sqlalchemy import select, and_, exists, func, String, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import joinedload
from fastapi接口.log.base_log import myfastapi_logger
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticRankTypeEnum
from fastapi接口.service.common_utils.dynamic_id_caculate import ts_2_fake_dynamic_id
import time
import ast
import sqlite_utils
from CONFIG import CONFIG
from grpc获取动态.src.SQLObject.models import Bilidyndetail, Lotdata
import json

sql_log = myfastapi_logger


@sql_log.catch
def lock_wrapper(_func: callable) -> callable:
    # 定义一个异步函数wrapper，接收任意数量和类型的参数
    async def wrapper(*args, **kwargs):
        # 无限循环
        while 1:
            try:
                # 调用传入的函数，并返回结果
                res = await _func(*args, **kwargs)
                return res
            except Exception as e:
                # 捕获异常，并记录日志
                sql_log.exception(e)
                # 等待10秒
                await asyncio.sleep(10)

    # 返回wrapper函数
    return wrapper


class SQLHelper:
    def __init__(self, db_path: str = CONFIG.database.dynDetail,
                 main_table_name: str = 'biliDynDetail'):
        _SQLURI = CONFIG.database.MYSQL.dyn_detail
        self._engine = create_async_engine(
            _SQLURI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self._session = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

        self.main_table_name = main_table_name
        self.lot_table_name = 'lotData'
        self._underscore_spe_time = 8 * 3600 * 3 * 2  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600 * 2  # 0分以上但是"-412"风控的代理休眠时间
        self.db_path = db_path
        self.op_db = sqlite_utils.Database(self.db_path)
        self.op_db_table = self.op_db[self.main_table_name]
        self.op_lot_table = self.op_db[self.lot_table_name]

    # region 返回和提交内容预处理

    def _process_2_save_data(self, orig_list_dict: list[dict]) -> list[dict]:
        '''
        对存入数据预处理，将dict转化为str(dict)
        :param orig_list_dict:
        :return:
        '''
        for _dic in orig_list_dict:
            for k, v in _dic.items():
                if type(v) == dict or type(v) == list:
                    _dic[k] = json.dumps(v, ensure_ascii=False)
        return orig_list_dict

    def _preprocess_ret_data(self, ret_dict: dict) -> dict:
        '''
        对取出的数据中的str转为dict
        :param ret_dict:
        :return:
        '''
        for k, v in ret_dict.items():
            if type(v) == str:
                try:
                    literal_value = ast.literal_eval(v)
                except:
                    continue
                if type(literal_value) == dict:
                    ret_dict[k] = ast.literal_eval(v)
        return ret_dict

    # endregion

    # region 查询相关信息
    @lock_wrapper
    async def get_lost_lots(self, limit_ts: int = 7 * 3600 * 24) -> Sequence[Union[Bilidyndetail, Lotdata]]:
        """
        获取主表中lot_id存在，但抽奖信息表中不存在数据的lot_id和rid信息
        :return:
        """
        if limit_ts:
            target_ts = int(time.time()) - limit_ts
            fake_dynamic_id = ts_2_fake_dynamic_id(int(target_ts))
        else:
            fake_dynamic_id = 0
        # 使用左连接，并过滤掉Lotdata表中存在对应lottery_id的记录
        query = (
            select(Bilidyndetail)
            .join(Lotdata, Bilidyndetail.lot_id == Lotdata.lottery_id, isouter=True)
            .where(
                and_(
                    Bilidyndetail.lot_id.isnot(None),
                    Lotdata.lottery_id.is_(None),
                    Bilidyndetail.dynamic_id_int > fake_dynamic_id
                )
            )
            .order_by(Bilidyndetail.dynamic_id_int.desc())
        )

        async with self._session() as session:
            result = await session.execute(query)
            return result.scalars().all()

    @lock_wrapper
    async def get_discountious_rids(self) -> Sequence[int]:
        """
        获取最大值和最小值之间不连续的rid，也就是那些可能获取失败了rid（rid最近的30万条数据）
        :return:
        """
        async with self._session() as session:
            # 子查询：获取最近的30万条记录
            subquery = (
                select(Bilidyndetail.rid)
                .order_by(Bilidyndetail.rid.desc())
                .limit(300000)
                .alias('t1')
            )
            # 主查询：查找缺失的rid值
            query = (
                select((subquery.c.rid + 1).label('x'))
                .where(
                    and_(
                        ~exists().where(Bilidyndetail.rid == (subquery.c.rid + 1)),
                        (subquery.c.rid + 1) > 0,
                        func.length(func.cast(subquery.c.rid + 1, String)) < 18
                    )
                )
                .order_by('x')
            )

            async with self._session() as session:
                result = await session.execute(query)
                ret_row = [int(row.x) for row in result]

            return ret_row

    @lock_wrapper
    async def get_all_dynamic_detail_by_dynamic_id(self, dynamic_id: str) -> Bilidyndetail | None:
        '''
        根据动态id获取特定动态详情
        :param dynamic_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        '''
        async with self._session() as session:
            sql = select(Bilidyndetail).where(Bilidyndetail.dynamic_id == dynamic_id).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @lock_wrapper
    async def get_all_dynamic_detail_by_rid(self, rid: str) -> Bilidyndetail | None:
        '''
        根据动态id获取特定动态详情
        :param rid: 动态rid
        :return: Bilidyndetail
        '''
        async with self._session() as session:
            sql = select(Bilidyndetail).where(Bilidyndetail.rid == rid).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @lock_wrapper
    async def get_lotDetail_by_lot_id(self, lot_id: int) -> Lotdata | None:
        '''
        根据动态id获取所有详情
        :param lot_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        '''
        async with self._session() as session:
            sql = select(Lotdata).where(Lotdata.lottery_id == lot_id).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @lock_wrapper
    async def get_latest_rid(self) -> int | None:
        batch_size = 1000
        async with self._session() as session:
            # 查询指定数量的rid，按降序排列
            result = await session.execute(
                select(Bilidyndetail.rid)
                .where(func.length(Bilidyndetail.rid_int) < 18)
                .order_by(Bilidyndetail.rid_int.desc())
                .limit(batch_size)
            )

            rids = np.array([int(row[0]) for row in result], dtype=np.int64)  # 将rid转换为NumPy数组

            if len(rids) == 0:
                return None

            # 计算相邻rid之间的差异
            differences = rids[:-1] - rids[1:]

            # 找到第一个不连续的位置
            first_non_consecutive_idx = np.where(differences != 1)[0]

            if len(first_non_consecutive_idx) > 0:
                max_consecutive_id = rids[first_non_consecutive_idx[0]]
            else:
                max_consecutive_id = rids[-1]

            return max_consecutive_id + 1  # +1 是最大的一个，不加一是第二大的

    @lock_wrapper
    async def query_dynData_by_key_word(self, key_word_list: [str], between_ts: List[int] | None = None) -> Sequence[
        Bilidyndetail]:
        """
        通过like查询需要的动态
        :param key_word_list:
        :param between_ts:
        :return:
        """
        async with self._session() as session:
            stmt = select(Bilidyndetail)
            # 动态生成like条件
            conditions = [Bilidyndetail.dynData.like(f"%{keyword}%") for keyword in key_word_list]
            if between_ts and type(between_ts) == list and len(between_ts) == 2:
                between_ts.sort()
                conditions.append(
                    and_(
                        func.STR_TO_DATE(Bilidyndetail.dynamic_created_time, '%Y-%m-%d %H:%i:%s') >= func.FROM_UNIXTIME(
                            between_ts[0]),
                        func.STR_TO_DATE(Bilidyndetail.dynamic_created_time, '%Y-%m-%d %H:%i:%s') <= func.FROM_UNIXTIME(
                            between_ts[1])
                    )
                )
            stmt = stmt.where(and_(*conditions)).order_by(Bilidyndetail.dynamic_id_int.desc())

            result = await session.execute(stmt)
            return result.scalars().all()

    @lock_wrapper
    async def query_dynData_by_date(self, between_ts: list[int] = None) -> Sequence[Bilidyndetail]:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        async with self._session() as session:
            if between_ts is None:
                today = datetime.datetime.now().date()
                tomorrow = today + datetime.timedelta(days=1)
                yesterday_end_time = int(time.mktime(today.timetuple())) - 1
                today_start_time = yesterday_end_time + 1
                today_end_time = int(time.mktime(tomorrow.timetuple())) - 1
                between_ts = [today_start_time, today_end_time]

            if len(between_ts) != 2:
                raise ValueError('错误的日期间隔')

                # 使用 FROM_UNIXTIME 将 Unix 时间戳转换为 MySQL 的日期时间格式
            stmt = select(Bilidyndetail).where(
                and_(
                    func.STR_TO_DATE(Bilidyndetail.dynamic_created_time, '%Y-%m-%d %H:%i:%s') >= func.FROM_UNIXTIME(
                        between_ts[0]),
                    func.STR_TO_DATE(Bilidyndetail.dynamic_created_time, '%Y-%m-%d %H:%i:%s') <= func.FROM_UNIXTIME(
                        between_ts[1])
                )
            ).order_by(func.STR_TO_DATE(Bilidyndetail.dynamic_created_time, '%Y-%m-%d %H:%i:%s').desc())

            result = await session.execute(stmt)
            return result.scalars().all()

    @lock_wrapper
    async def query_lot_data_by_business_id(self, business_id: int | str) -> Lotdata | None:
        async with self._session() as session:
            sql = select(Lotdata).where(
                Lotdata.business_id == business_id
            ).order_by(Lotdata.business_id.desc()).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @lock_wrapper
    async def query_official_lottery_by_timelimit(self, time_limit: int = 24 * 3600) -> Sequence[Lotdata]:
        """
        通过日期查询需要的动态，默认查询当天
        :return:
        """
        async with self._session() as session:
            now_ts = int(time.time())
            target_ts = now_ts + time_limit

            stmt = select(Lotdata).where(
                and_(
                    Lotdata.status == 0,
                    Lotdata.business_type == 1,
                    Lotdata.lottery_time >= now_ts,
                    Lotdata.lottery_time <= target_ts
                )
            ).order_by(Lotdata.lottery_time.desc())

            result = await session.execute(stmt)
            return result.scalars().all()

    @lock_wrapper
    async def query_official_lottery_by_timelimit_page_offset(
            self,
            time_limit: int = 24 * 3600,
            page_number: int = 0,
            page_size: int = 0
    ) -> tuple[Sequence[Lotdata], int]:
        """
        通过日期查询需要的动态，默认查询当天
        :param time_limit:
        :param page_size:
        :param page_number:
        :return:
        """
        now_ts = int(time.time())
        base_conditions = [
            Lotdata.status == 0,
            Lotdata.business_type == 1,
            Lotdata.lottery_time >= now_ts
        ]

        if time_limit:
            target_ts = now_ts + time_limit
            base_conditions.append(Lotdata.lottery_time <= target_ts)
        stmt = select(Lotdata).options(joinedload(Lotdata.bilidyndetail)).where(and_(*base_conditions)).order_by(
            Lotdata.lottery_time.asc())
        # 如果提供了分页参数，则应用分页
        if page_number and page_size:
            stmt = stmt.limit(page_size).offset((page_number - 1) * page_size)
        async with self._session() as session:
            result = await session.execute(stmt)
            records = result.scalars().all()
            # 计算总数
            count_stmt = select(func.count()).select_from(Lotdata).where(and_(*base_conditions))
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            return records, total_count

    @lock_wrapper
    async def query_charge_lottery_by_timelimit_page_offset(
            self,
            time_limit: int = 24 * 3600,
            page_number: int = 0,
            page_size: int = 0,
    ) -> tuple[Sequence[Lotdata], int]:
        """
        通过日期查询需要的动态，默认查询当天
        :param page_number:
        :param time_limit:
        :param page_size:
        :return:
        """
        now_ts = int(time.time())
        base_conditions = [
            Lotdata.status == 0,
            Lotdata.business_type == 12,
            Lotdata.lottery_time >= now_ts
        ]

        if time_limit:
            target_ts = now_ts + time_limit
            base_conditions.append(Lotdata.lottery_time <= target_ts)
        stmt = select(Lotdata).options(joinedload(Lotdata.bilidyndetail)).where(and_(*base_conditions)).order_by(
            Lotdata.lottery_time.asc())
        # 如果提供了分页参数，则应用分页
        if page_number > 0 and page_size > 0:
            stmt = stmt.limit(page_size).offset((page_number - 1) * page_size)
        async with self._session() as session:
            result = await session.execute(stmt)
            records = result.scalars().all()

            # 计算总数
            count_stmt = select(func.count()).select_from(Lotdata).where(and_(*base_conditions))
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            return records, total_count

    # endregion

    # region 更新和新增内容

    @lock_wrapper
    async def upsert_DynDetail(self, doc_id: str | int, dynamic_id: str | int, dynData: dict|None, lot_id: str | int | None,
                               dynamic_created_time: str|None):
        if dynData:
            parsed_dyn_data = json.dumps(dynData, ensure_ascii=False)
        else:
            parsed_dyn_data = None
        async with self._session() as session:
            stmt = insert(Bilidyndetail).values(
                rid=doc_id,
                dynamic_id=dynamic_id,
                dynData=parsed_dyn_data,
                lot_id=lot_id,
                dynamic_created_time=dynamic_created_time
            ).on_duplicate_key_update(
                dynamic_id=dynamic_id,
                dynData=parsed_dyn_data,
                lot_id=lot_id,
                dynamic_created_time=dynamic_created_time
            )

            await session.execute(stmt)
            await session.commit()

    @lock_wrapper
    async def upsert_lot_detail(self, lot_data_dict: dict):
        '''

        :param lot_data_dict: lottery_notice的响应的data
        :return:更新 返回{'mode':'update'}
                插入 返回{'mode':'insert'}
                失败 返回{'mode': 'error'}
        '''
        async with (self._session() as session):
            lottery_id = lot_data_dict.get('lottery_id')
            if lottery_id is None:
                return {'mode': 'error'}
            existing_record = await session.execute(
                select(Lotdata).where(Lotdata.lottery_id == lottery_id)
            )
            exists = existing_record.scalars().first() is not None
            # 获取Lotdata的所有列名
            columns = Lotdata.__table__.columns.keys()

            # 分离出不在Lotdata模型中的键值对
            custom_extra = {k: lot_data_dict.pop(k) for k in list(lot_data_dict.keys()) if
                            k not in columns and k != 'lottery_id'}
            if custom_extra:
                lot_data_dict['custom_extra_key'] = json.dumps(custom_extra)
            else:
                lot_data_dict['custom_extra_key'] = None
            self._process_2_save_data(
                [
                    lot_data_dict
                ]
            )

            await session.merge(Lotdata(**lot_data_dict))

            # 判断是插入还是更新
            mode = 'insert' if exists == 1 else 'update'
            await session.commit()
            return {'mode': mode}

    # endregion
    @lock_wrapper
    async def get_all_lot_not_drawn(self) -> Sequence[Lotdata]:
        async with self._session() as session:
            stmt = select(Lotdata).where(
                and_(
                    Lotdata.lottery_result.is_(None),
                    Lotdata.status != -1
                )
            ).order_by(Lotdata.lottery_id)

            result = await session.execute(stmt)
            return result.scalars().all()

    @lock_wrapper
    async def get_all_lottery_result_rank(self, business_type: Literal[1, 10, 12],
                                          rank_type: BiliLotStatisticRankTypeEnum) -> list[
        tuple[int, int]]:
        async with self._session() as session:
            if rank_type == BiliLotStatisticRankTypeEnum.total:
                query = text("""
                        SELECT uid, COUNT(*) AS total_count 
                        FROM (
                            SELECT JSON_UNQUOTE(JSON_EXTRACT(JSON_UNQUOTE(JSON_EXTRACT(lotData.lottery_result, '$.first_prize_result')), CONCAT('$[', seq.seq, '].uid'))) AS uid
                            FROM lotData, 
                            (SELECT 0 AS seq UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS seq
                            WHERE lotData.business_type = :business_type AND JSON_VALID(lotData.lottery_result)
                            AND seq.seq < JSON_LENGTH(JSON_EXTRACT(lotData.lottery_result, '$.first_prize_result'))

                            UNION ALL

                            SELECT JSON_UNQUOTE(JSON_EXTRACT(JSON_UNQUOTE(JSON_EXTRACT(lotData.lottery_result, '$.second_prize_result')), CONCAT('$[', seq.seq, '].uid'))) AS uid
                            FROM lotData, 
                            (SELECT 0 AS seq UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS seq
                            WHERE lotData.business_type = :business_type AND JSON_VALID(lotData.lottery_result)
                            AND seq.seq < JSON_LENGTH(JSON_EXTRACT(lotData.lottery_result, '$.second_prize_result'))

                            UNION ALL

                            SELECT JSON_UNQUOTE(JSON_EXTRACT(JSON_UNQUOTE(JSON_EXTRACT(lotData.lottery_result, '$.third_prize_result')), CONCAT('$[', seq.seq, '].uid'))) AS uid
                            FROM lotData, 
                            (SELECT 0 AS seq UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS seq
                            WHERE lotData.business_type = :business_type AND JSON_VALID(lotData.lottery_result)
                            AND seq.seq < JSON_LENGTH(JSON_EXTRACT(lotData.lottery_result, '$.third_prize_result'))
                        ) AS combined_results
                        WHERE uid IS NOT NULL
                        GROUP BY uid
                        ORDER BY total_count DESC;
                    """)
                result = await session.execute(query, {"business_type": business_type})
                return [(row.uid, row.total_count) for row in result]
            else:
                prize_key = f"{rank_type.value}_prize_result"
                query = text(f"""
                        SELECT JSON_UNQUOTE(JSON_EXTRACT(JSON_UNQUOTE(JSON_EXTRACT(lotData.lottery_result, '$.{prize_key}')), CONCAT('$[', seq.seq, '].uid'))) AS uid, COUNT(*) AS count 
                        FROM lotData, 
                        (SELECT 0 AS seq UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) AS seq
                        WHERE lotData.business_type = :business_type AND JSON_VALID(lotData.lottery_result)
                        AND seq.seq < JSON_LENGTH(JSON_EXTRACT(lotData.lottery_result, '$.{prize_key}'))
                        AND JSON_UNQUOTE(JSON_EXTRACT(JSON_UNQUOTE(JSON_EXTRACT(lotData.lottery_result, '$.{prize_key}')), CONCAT('$[', seq.seq, '].uid'))) IS NOT NULL
                        GROUP BY uid
                        ORDER BY count DESC, uid DESC;
                    """)
                result = await session.execute(query, {"business_type": business_type})

                return [(row.uid, row.count) for row in result]


grpc_sql_helper = SQLHelper()

if __name__ == "__main__":


    async def _test():
        sql_log.debug(1)
        result = await grpc_sql_helper.get_all_lottery_result_rank(
                                                     )

        sql_log.debug(result)


    asyncio.run(_test())
