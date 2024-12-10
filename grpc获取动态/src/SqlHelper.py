# -*- coding: utf-8 -*-
import datetime
from typing import Generator
from fastapi接口.log.base_log import myfastapi_logger
from grpc获取动态.src.DynObjectClass import *  # 导入自定义对象
import time
import ast
import sqlite_utils
import threading
from CONFIG import CONFIG

op_db_lock = threading.Lock()
sql_log = myfastapi_logger


@sql_log.catch
def lock_wrapper(func: callable) -> callable:
    def wrapper(*args, **kwargs):
        while 1:
            with op_db_lock:
                try:
                    res = func(*args, **kwargs)
                    return res
                except Exception as e:
                    sql_log.exception(e)
                    time.sleep(10)

    return wrapper


def parse_dict(d: dict, dump_key: str = ''):
    '''
    将多重dict转换为pandas to_sql的样式
    :param d:
    :param dump_key:
    :return:
    '''
    ret_dict = {}
    for k, v in d.items():
        if dump_key:
            k = dump_key + '.' + k
        if type(v) is dict:
            for _k, _v in parse_dict(v, k).items():
                ret_dict[_k] = _v
        else:
            ret_dict[k] = v
    return ret_dict


class SQLHelper:

    def __init__(self, db_path: str = CONFIG.database.dynDetail,
                 main_table_name: str = 'biliDynDetail'):
        self.main_table_name = main_table_name
        self.lot_table_name = 'lotData'
        self._underscore_spe_time = 8 * 3600 * 3 * 2  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600 * 2  # 0分以上但是"-412"风控的代理休眠时间
        self.db_path = db_path
        self.op_db = sqlite_utils.Database(self.db_path)
        self.op_db_table = self.op_db[self.main_table_name]
        self.op_lot_table = self.op_db[self.lot_table_name]

    # region 返回和提交内容预处理

    def __preprocess_list_dict(self, orig_list_dict: list[dict]) -> list[dict]:
        '''
        对存入数据预处理，将dict转化为str(dict)
        :param orig_list_dict:
        :return:
        '''
        for _dic in orig_list_dict:
            for k, v in _dic.items():
                if type(v) == dict:
                    _dic[k] = str(v)
        return orig_list_dict

    def __preprocess_ret_list_dict(self, ret_dict: dict) -> dict:
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
    def get_lost_lots(self) -> [dict]:
        """
        获取主表中lot_id存在，但抽奖信息表中不存在数据的lot_id和rid信息
        :return:
        """
        ret_row = []
        for row in self.op_db.query(
                """
SELECT b.*
FROM (select * from biliDynDetail limit 300000) AS b
left JOIN lotData AS l ON b.lot_id = l.lottery_id
WHERE b.lot_id IS NOT NULL AND TRIM(b.lot_id) != '' AND l.lottery_id IS NULL
ORDER BY b.rid DESC
LIMIT 300000;
    """
        ):
            ret_row.append(row)
        return ret_row

    @lock_wrapper
    def get_discountious_rids(self) -> list:
        """
        获取最大值和最小值之间不连续的rid，也就是那些可能获取失败了rid（rid最近的30万条数据）
        :return:
        """
        ret_row = []
        for row in self.op_db.query(
                """SELECT DISTINCT (t1.rid + 1) AS x
FROM (SELECT * FROM biliDynDetail ORDER BY rid DESC LIMIT 300000) t1
WHERE NOT EXISTS (
    SELECT 1 FROM biliDynDetail t2 WHERE t2.rid = t1.rid + 1
) and x>0 and Length(x)<18
ORDER BY x
"""
        ):
            ret_row.append(row.get('x'))
        return ret_row

    @lock_wrapper
    def get_all_dynamic_detail_by_dynamic_id(self, dynamic_id: str) -> dynAllDetail.__dict__:
        '''
        根据动态id获取特定动态详情
        :param dynamic_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        '''
        where = "dynamic_id=:dynamic_id"
        where_args = {
            'dynamic_id': dynamic_id,
        }
        ret_list_dict = [row for row in
                         self.op_db_table.rows_where(
                             where=where, where_args=where_args)]
        if ret_list_dict:
            return dynAllDetail(**self.__preprocess_ret_list_dict(ret_list_dict[0])).__dict__
        else:
            return dynAllDetail().__dict__

    @lock_wrapper
    def get_all_dynamic_detail_by_rid(self, rid: str) -> dynAllDetail.__dict__:
        '''
        根据动态id获取特定动态详情
        :param rid: 动态rid
        :return:[{...}, {...}] dynAllDetail dict
        '''
        where = "rid=:rid"
        where_args = {
            'rid': rid,
        }
        ret_list_dict = [row for row in
                         self.op_db_table.rows_where(
                             where=where, where_args=where_args)]
        if ret_list_dict:
            return dynAllDetail(**self.__preprocess_ret_list_dict(ret_list_dict[0])).__dict__
        else:
            return dynAllDetail().__dict__

    @lock_wrapper
    def get_lotDetail_by_lot_id(self, lot_id: int) -> lotDetail.__dict__:
        '''
        根据动态id获取所有详情
        :param lot_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        '''
        where = "lottery_id=:lottery_id"
        where_args = {
            'lottery_id': lot_id,
        }
        ret_list_dict = [row for row in
                         self.op_lot_table.rows_where(
                             where=where, where_args=where_args)]
        if ret_list_dict:
            return lotDetail(
                self.__preprocess_ret_list_dict(ret_list_dict[0])
            ).__dict__
        else:
            return lotDetail({}).__dict__

    @lock_wrapper
    def get_latest_rid(self) -> int | None:
        # where = "dynamic_id is not null and dynamic_id is not ''"
        # select = 'max(rid)'
        sql = """WITH TopRIDs AS (
    SELECT rid
    FROM biliDynDetail
    WHERE LENGTH(rid) < 18
    ORDER BY rid DESC
    LIMIT 1000
)
SELECT MAX(t1.rid) AS max_consecutive_id
FROM TopRIDs t1
INNER JOIN biliDynDetail t2 ON t1.rid = t2.rid + 1;"""
        # res = self.op_db_table.rows_where(where=where, select=select)
        res = self.op_db.query(sql)
        try:
            # max_rid = next(res).get('max(rid)')
            max_rid = next(res).get('max_consecutive_id')
        except:
            max_rid = None
        return max_rid

    @lock_wrapper
    def query_dynData_by_key_word(self, key_word_list: [str], between_ts: list = []) -> Generator:
        """
        通过like查询需要的动态
        :param between_ts:
        :param RegExp:
        :return:
        """
        where = ""
        for key_word in key_word_list:
            if key_word == key_word_list[-1]:
                where += f"dynData like '%{key_word}%' "
            else:
                where += f"dynData like '%{key_word}%' or "
        where_args = {
            'order_by': 'dynamic_created_time desc',
        }
        if len(between_ts) == 2:
            between_ts.sort()
            where += "and dynamic_created_time between datetime(:start_ts,'unixepoch','localtime') and datetime(:end_ts,'unixepoch','localtime')"
            where_args.update(
                {'start_ts': between_ts[0],
                 'end_ts': between_ts[1]}
            )
        return self.op_db_table.rows_where(
            where=where, where_args=where_args)

    @lock_wrapper
    def query_dynData_by_date(self, between_ts: list = None) -> Generator:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        if between_ts is None:
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            yesterday_end_time = int(time.mktime(time.strptime(str(today), '%Y-%m-%d'))) - 1
            today_start_time = yesterday_end_time + 1
            today_end_time = int(time.mktime(time.strptime(str(tomorrow), '%Y-%m-%d'))) - 1
            between_ts = [today_start_time, today_end_time]
        if len(between_ts) != 2:
            raise ValueError('错误的日期间隔')
        where = ""
        where_args = {
            'order_by': 'dynamic_created_time desc',
        }
        if len(between_ts) == 2:
            where += "dynamic_created_time between datetime(:start_ts,'unixepoch','localtime') and datetime(:end_ts,'unixepoch','localtime')"
            where_args.update(
                {'start_ts': between_ts[0],
                 'end_ts': between_ts[1]}
            )
        return self.op_db_table.rows_where(
            where=where, where_args=where_args)

    @lock_wrapper
    def query_lot_data_by_business_id(self, business_id: int | str):
        where = "business_id=:business_id limit 1"
        if ret := list(self.op_lot_table.rows_where(
                where=where, where_args={
                    "business_id": business_id,
                })):
            return ret[0]
        else:
            return None

    @lock_wrapper
    def query_official_lottery_by_timelimit(self, time_limit: int = 24 * 3600) -> Generator:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        now_ts = int(time.time())
        target_ts = now_ts + time_limit
        where = "status=0 and business_type=1 and lottery_time>=:now_ts and lottery_time<=:target_ts order by lottery_time desc"
        return self.op_lot_table.rows_where(
            where=where, where_args={
                "now_ts": now_ts,
                "target_ts": target_ts
            })

    @lock_wrapper
    def query_official_lottery_by_timelimit_page_offset(self, time_limit: int = 24 * 3600, page_number: int = 0,
                                                        page_size: int = 0) -> tuple[Generator[dict, None, None], int]:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        now_ts = int(time.time())
        base_where = 'status=0 and business_type=1 and lottery_time>=:now_ts'
        if not time_limit:
            where = base_where + " order by lottery_time asc"
            where_args = {
                "now_ts": now_ts,
            }
        else:
            target_ts = now_ts + time_limit
            where = base_where + " and lottery_time<=:target_ts order by lottery_time asc"
            where_args = {
                "now_ts": now_ts,
                "target_ts": target_ts
            }
        if page_number and page_size:
            offset_value = (page_number - 1) * page_size
            where += " limit :page_size offset :offset_value"
            where_args.update({
                "page_size": page_size,
                "offset_value": offset_value
            })
        return (
            self.op_lot_table.rows_where(where=where, where_args=where_args),
            self.op_lot_table.count_where(base_where, where_args)
        )

    @lock_wrapper
    def query_charge_lottery_by_timelimit_page_offset(self, time_limit: int = 24 * 3600, page_number: int = 0,
                                                      page_size: int = 0) -> tuple[Generator[dict, None, None], int]:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        now_ts = int(time.time())
        base_where = 'status=0 and business_type=12 and lottery_time>=:now_ts'
        if not time_limit:
            where = base_where + " order by lottery_time asc"
            where_args = {
                "now_ts": now_ts,
            }
        else:
            target_ts = now_ts + time_limit
            where = base_where + " and lottery_time<=:target_ts order by lottery_time asc"
            where_args = {
                "now_ts": now_ts,
                "target_ts": target_ts
            }
        if page_number and page_size:
            offset_value = (page_number - 1) * page_size
            where += " limit :page_size offset :offset_value"
            where_args.update({
                "page_size": page_size,
                "offset_value": offset_value
            })
        return (
            self.op_lot_table.rows_where(where=where, where_args=where_args),
            self.op_lot_table.count_where(base_where, where_args)
        )

    # endregion

    # region 更新和新增内容

    @lock_wrapper
    def upsert_doc_2_dynamic_id(self, doc_id: str, dynamic_id: str):
        if len(list(self.op_db_table.rows_where(where='rid=:doc_id', where_args={'doc_id': doc_id}))) >= 1:
            return self.op_db_table.update(pk_values=doc_id, updates={
                'dynamic_id': dynamic_id
            }
                                           )
        else:
            return self.op_db_table.insert({
                'rid': doc_id,
                'dynamic_id': dynamic_id
            },
                pk='rid', )

    @lock_wrapper
    def upsert_DynDetail(self, doc_id: str, dynamic_id: str, dynData: str, lot_id: int, dynamic_created_time: str):
        if len(list(self.op_db_table.rows_where(where='rid=:doc_id', where_args={'doc_id': doc_id}))) >= 1:
            return self.op_db_table.update(
                pk_values=doc_id,
                updates={
                    'dynamic_id': dynamic_id,
                    'dynData': dynData,
                    'lot_id': lot_id,
                    'dynamic_created_time': dynamic_created_time
                }
            )
        else:
            return self.op_db_table.insert({
                'rid': doc_id,
                'dynamic_id': dynamic_id,
                'dynData': dynData,
                'lot_id': lot_id,
                'dynamic_created_time': dynamic_created_time
            }, pk='rid',
            )

    @lock_wrapper
    def upsert_lot_detail(self, lot_data_dict: dict):
        '''

        :param lot_data_dict: lottery_notice的响应的data
        :return:更新 返回{'mode':'update'}
                插入 返回{'mode':'insert'}
                失败 返回{'mode': 'error'}
        '''
        if lot_data_dict.get('lottery_id') is None:
            return {'mode': 'error'}
        lot_id = lot_data_dict['lottery_id']
        if len(list(self.op_lot_table.rows_where(where='lottery_id=:lot_id', where_args={'lot_id': lot_id}))) >= 1:
            self.op_lot_table.update(pk_values=lot_id, updates=lot_data_dict)
            return {'mode': 'update'}
        else:
            self.op_lot_table.insert(record=lot_data_dict)
            return {'mode': 'insert'}
    # endregion


grpc_sql_helper = SQLHelper()

if __name__ == '__main__':
    result = grpc_sql_helper.get_latest_rid()
    print(result)
