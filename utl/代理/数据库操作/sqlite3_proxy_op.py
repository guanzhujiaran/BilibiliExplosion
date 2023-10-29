# -*- coding: utf-8 -*-
import ast
import sqlite_utils
import threading
import time
from copy import deepcopy
from loguru import logger
from CONFIG import CONFIG
logger.bind(user='sqlite3')
op_db_lock = threading.Lock()

logger.add(CONFIG.root_dir+"utl/代理/log/sqlite3.log",
            encoding="utf-8",
            enqueue=True,
            rotation="500MB",
            compression="zip",
            retention="15 days",
            filter=lambda record: record["extra"].get('user') == "sqlite3")

def lock_wrapper(func: callable) -> callable:
    def wrapper(*args, **kwargs):
        with op_db_lock:
            res = func(*args, **kwargs)
            return res

    return wrapper


class SQLHelper:

    def __init__(self, db_path: str, table_name: str):
        self.table_name = table_name
        self._underscore_spe_time = 8 * 3600  # 0分以下的无响应代理休眠时间
        self._412_sep_time = 2 * 3600  # 0分以上但是"-412"风控的代理休眠时间
        self.db_path = db_path
        self.op_db = sqlite_utils.Database(self.db_path)
        self.op_db_table = self.op_db[self.table_name]
        self.grpc_tb_name = 'SD_grpc_stat'
        self.op_db_grpc_table = self.op_db[self.grpc_tb_name]

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
        for k, v in ret_dict.items():
            if type(v) == str:
                ret_dict[k] = ast.literal_eval(v)
        return ret_dict

    def select_score_top_proxy(self) -> dict:
        ret_list_dict = [row for row in
                         self.op_db_table.rows_where(order_by='score desc , update_ts desc', limit=1)]
        return self.__preprocess_ret_list_dict(ret_list_dict[0])

    @logger.catch
    def select_one_proxy(self, mode='single', channel='bili') -> dict:
        '''
        选择一个可用的代理
        :param channel:
        :param mode:
        :return:[{...}, {...}] proxy_dict
        '''
        where = "(status=:available_status and score>=:available_score) or (" \
                "status=:_412_status and score>=:available_score and strftime(" \
                "'%s','now')-update_ts >=:_412_sep_time) or (score<:available_score and strftime(" \
                "'%s','now')-update_ts >=:_underscore_spe_time)"
        where_args = {
            'available_status': 0,
            'available_score': 0,
            '_412_status': '-412',
            '_412_sep_time': self._412_sep_time,
            '_underscore_spe_time': self._underscore_spe_time
        }
        if channel == 'zhihu':
            where = "zhihu_status=:available_status and score>=:available_score and success_times>0"
            where_args = {
                'available_status': 0,
                'available_score': 0,
            }
        if mode == 'single':
            ret_list_dict = [row for row in
                             self.op_db_table.rows_where(
                                 where=where, where_args=where_args, order_by='score desc , update_ts desc', limit=1)]
        else:
            ret_list_dict = [row for row in
                             self.op_db_table.rows_where(
                                 where=where, where_args=where_args, order_by='random()', limit=1)]
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict[0])
        else:
            return {}

    def select_rand_proxy(self) -> dict:
        ret_list_dict = [row for row in
                         self.op_db_table.rows_where(
                             order_by='random()', limit=1)]
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict[0])
        else:
            return {}

    @logger.catch
    def is_exist_proxy_by_proxy(self, proxy: dict) -> int:
        '''
        查询是否存在这个代理
        :param proxy:{'http':xxxx, 'https':xxxx}
        :return:int
        '''
        exist_num = self.op_db_table.count_where(where="proxy=:proxy", where_args={'proxy': (str(proxy))})
        return exist_num

    @logger.catch
    @lock_wrapper
    def remove_list_dict_data_by_proxy(self) -> bool:
        '''
        根据proxy列对数据库table去重
        :return:
        '''
        self.op_db_table.delete_where(
            where=f'proxy_id NOT IN(SELECT MAX(proxy_id) from {self.table_name} GROUP BY proxy)')
        return True

    @logger.catch
    @lock_wrapper
    def refresh_412_proxy(self) -> int:
        '''
        更新412和负分的代理，返回更新的数量
        :return:
        '''
        avaliable_score = 0
        available_status = 0
        now = int(time.time())
        unavaliable_status = -412
        res1 = self.op_db.execute(
            f"update proxy_tab set status=:available_status,update_ts=:now where status= :unavaliable_status and strftime('%s','now')-update_ts >= :_412_sep_time and score>=:avaliable_score",
            {
                'available_status': available_status,
                'now': now,
                'unavaliable_status': unavaliable_status,
                '_412_sep_time': self._412_sep_time,
                'avaliable_score': avaliable_score
            }
        ).rowcount  # 刷新超过两小时的412风控代理 不改变分数，只改变status
        # res2 = self.op_db.execute(
        #     f"update proxy_tab set status=:available_status, update_ts=:now, score=50 where score<:avaliable_score and strftime('%s','now')-update_ts >=:_underscore_spe_time",
        #     {
        #         'available_status': available_status,
        #         'now': now,
        #         'unavaliable_status': unavaliable_status,
        #         '_underscore_spe_time': self._underscore_spe_time,
        #         'avaliable_score': avaliable_score
        #     }).rowcount  # 刷新超过12小时的无效代理，改变status和score
        res2 = self.op_db.execute(
            f"delete from proxy_tab where score<:avaliable_score and success_times <-5",
            {
                'avaliable_score': avaliable_score
            }).rowcount  # 刷新超过12小时的无效代理，改变status和score 删除可能把一些好用的也删了？不清楚，反正先不删除了
        self.op_db.conn.commit()
        return res1

    @logger.catch
    @lock_wrapper
    def update_to_proxy_list(self, proxy_dict: dict, score_plus_Flag=False, score_minus_Flag=False,
                             change_score_num=10) -> bool:
        '''
        更新数据 update 最好只用update，upsert会导致主键增长异常
        :param score_plus_Flag:
        :param change_score_num: 修改的分数
        :param score_minus_Flag:
        :param proxy_dict:
        :return:
        '''
        proxy_dict = deepcopy(proxy_dict)
        if score_plus_Flag:
            self.op_db.execute(
                f'update {self.table_name} set status=:status,score=score+{change_score_num},success_times'
                f'=success_times+1,update_ts=:update_ts,add_ts=:add_ts where proxy=:proxy',
                self.__preprocess_list_dict([proxy_dict])[0])
        elif score_minus_Flag:
            self.op_db.execute(
                f'update {self.table_name} set status=:status,score=score-{change_score_num},success_times'
                f'=success_times-1,update_ts=:update_ts,add_ts=:add_ts where proxy=:proxy',
                self.__preprocess_list_dict([proxy_dict])[0])
        else:
            self.op_db.execute(
                f'update {self.table_name} set status=:status,score=:score,update_ts=:update_ts,add_ts=:add_ts where proxy=:proxy',
                self.__preprocess_list_dict([proxy_dict])[0])
        self.op_db.conn.commit()
        return True

    @logger.catch
    @lock_wrapper
    def add_to_proxy_list(self, proxy_dict: dict) -> bool:
        '''
        添加数据
        :param proxy_dict:
        :return:
        '''
        proxy_dict = deepcopy(proxy_dict)
        res = self.op_db_table.insert(self.__preprocess_list_dict([proxy_dict])[0])
        res.db.conn.commit()
        return True

    # @logger.catch
    # def insert_all_proxy(self, info_dict_list: list[dict]) -> bool:
    #     '''
    #     增加
    #     :param info_dict_list: # [{'http': 'http://120.196.186.248:9091', 'https': 'http://120.196.186.248:9091'}...]
    #     :return:
    #     '''
    #     self.op_db_table.insert_all(self.__preprocess_list_dict(info_dict_list))
    #     return True

    @logger.catch
    @lock_wrapper
    def remove_proxy(self, proxy: dict):
        '''
        删除
        :param proxy:
        :return:
        '''
        self.op_db_table.delete_where(where='proxy=:proxy', where_args={'proxy': str(proxy)})

    @logger.catch
    def get_412_proxy_num(self) -> int:
        res = self.op_db_table.count_where(where='status=-412')
        return res

    @logger.catch
    def get_latest_add_ts(self) -> int:
        res = self.op_db_table.rows_where(order_by='add_ts desc', limit=1)
        max_status_ts = next(res)
        return max_status_ts['add_ts']

    @logger.catch
    def get_all_proxy_nums(self):
        return self.op_db_table.count

    @logger.catch
    def get_available_proxy_nums(self):
        return self.op_db_table.count_where(where='score>=0 and status!=-412')

    # region grpc_proxy
    @logger.catch
    def get_one_rand_grpc_proxy(self):
        def fresh_grpc_proxy():
            avaliable_score = 0
            available_status = 0
            now = int(time.time())
            unavaliable_status = -412
            res1 = self.op_db.execute(
                f"update SD_grpc_stat set status=:available_status,update_ts=:now where status= :unavaliable_status and strftime('%s','now')-update_ts >= :_412_sep_time and score>=:avaliable_score",
                {
                    'available_status': available_status,
                    'now': now,
                    'unavaliable_status': unavaliable_status,
                    '_412_sep_time': self._412_sep_time,
                    'avaliable_score': avaliable_score
                }
            ).rowcount  # 刷新超过两小时的412风控代理 不改变分数，只改变status
            res2 = self.op_db.execute(
                f"update proxy_tab set status=:available_status, update_ts=:now, score=50 where score<:avaliable_score and strftime('%s','now')-update_ts >=:_underscore_spe_time",
                {
                    'available_status': available_status,
                    'now': now,
                    'unavaliable_status': unavaliable_status,
                    '_underscore_spe_time': self._underscore_spe_time,
                    'avaliable_score': avaliable_score
                }).rowcount  # 刷新超过12小时的无效代理，改变status和score
        if self.op_db_grpc_table.count_where(where='score>=0 and status!=-412') == 0:
            fresh_grpc_proxy()
        available_status = 0
        available_score = 0
        _412_status = -412
        _412_sep_time = self._412_sep_time
        _underscore_spe_time = self._underscore_spe_time
        sql_str = f"""
select * from(select proxy_tab.proxy_id,proxy_tab.proxy,
 ifnull(SD_grpc_stat.status,0) as status,
SD_grpc_stat.update_ts as update_ts,ifnull(SD_grpc_stat.success_times,0) as success_times,
ifnull(SD_grpc_stat.score,50) as score
from proxy_tab 
left join SD_grpc_stat on proxy_tab.proxy_id=SD_grpc_stat.proxy_id)
where (status={available_status} and score>={available_score}) 
or (status={_412_status} and score>={available_status} and strftime('%s','now')-update_ts >={_412_sep_time})
or (score<0 and strftime('%s','now')-update_ts >={_underscore_spe_time})
order by random()
limit 1
"""
        ret_list_dict = [row for row in
                         self.op_db.query(
                             sql_str
                         )]
        if ret_list_dict:
            return self.__preprocess_ret_list_dict(ret_list_dict[0])
        else:
            return {}

    @logger.catch
    @lock_wrapper
    def upsert_grpc_proxy_status(self, proxy_id: int, status: int, score_change: int = 0):
        '''

        :param proxy_id:
        :param status:
        :param score_change:修改的分数值，+10，-10，或者不变
        :return:
        '''
        grpc_proxy_detail = list(
            self.op_db_grpc_table.rows_where(where='proxy_id=:proxy_id', where_args={'proxy_id': proxy_id}))
        if len(grpc_proxy_detail) >= 1:  # 存在
            success_times = grpc_proxy_detail[0]['success_times']
            if score_change > 0:
                success_times += 1
            else:
                success_times-=1
            if grpc_proxy_detail[0]['score'] > 100:
                score_change = 100 - grpc_proxy_detail[0]['score']
            elif grpc_proxy_detail[0]['score'] < -50:
                score_change = -50 - grpc_proxy_detail[0]['score']
            self.op_db_grpc_table.update(pk_values=proxy_id, updates={
                'status': status,
                'score': grpc_proxy_detail[0]['score'] + score_change,
                'success_times': success_times,
                'update_ts': int(time.time()),
            })
        else:
            self.op_db_grpc_table.insert(
                {
                    'proxy_id': proxy_id,
                    'status': status,
                    'score': score_change,
                    'success_times': 1 if score_change >= 0 else 0,
                    'update_ts': int(time.time()),
                }
            )

    # endregion

    def test(self):
        res = self.select_score_top_proxy()
        print(res)


if __name__ == '__main__':
    sq = SQLHelper(CONFIG.database.proxy_db, 'proxy_tab')
    sq.test()
