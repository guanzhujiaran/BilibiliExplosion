import time
from enum import Enum
from typing import Any

from pydantic import computed_field, Field

from Models.base.custom_pydantic import CustomBaseModel


class BackgroundServiceName(str, Enum):
    """后台服务名称枚举"""
    DYN_DETAIL_DATABASE_CLEANER = "DYN_DETAIL_DATABASE_CLEANER"
    GET_PROXY_METHODS_SCHEDULER = "GET_PROXY_METHODS_SCHEDULER"
    SAMSCCLUB_SCHEDULER = "SAMSCCLUB_SCHEDULER"
    SAMSCCLUB_SPU_DETAIL_SCHEDULER = "SAMSCCLUB_SPU_DETAIL_SCHEDULER"
    GET_RESERVE_INFO = "GET_RESERVE_INFO"
    GET_DYN = "GET_DYN"
    GET_TOPIC = "GET_TOPIC"
    REFRESH_BILI_LOTDATA_DATABASE = "REFRESH_BILI_LOTDATA_DATABASE"
    LOTTERY_API_ROBOT_DYN_SCHEDULER = "LOTTERY_API_ROBOT_DYN_SCHEDULER"
    LOTTERY_API_ROBOT_RESERVE_SCHEDULER = "LOTTERY_API_ROBOT_RESERVE_SCHEDULER"
    GMFLV2_SCHEDULER = "GMFLV2_SCHEDULER"


class ProgressStatusResp(CustomBaseModel):
    succ_count: int = 0
    start_ts: int = 0
    total_num: int = 0
    progress: float | int = Field(default=0, description='当前进度')
    is_running: bool = False
    update_ts: int = 0  # 最后更新时间
    running_params: set = Field(default_factory=set, description='运行中的参数')

    @computed_field
    def update_time(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.update_ts))
    @computed_field
    def start_time(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_ts))

class BaseScrapyStatusResp(CustomBaseModel):
    succ_count: int = 0
    cur_stop_num: int = 0
    start_ts: int = 0
    freq: int | float = Field(default=0, description='爬取成功的频率，单位为（条/秒）')
    is_running: bool = False
    update_ts: int = 0  # 最后更新时间

class ProxyStatusResp(CustomBaseModel):
    proxy_total_count: int = 0
    proxy_black_count: int = 0
    proxy_unknown_count: int = 0
    proxy_usable_count: int = 0
    mysql_sync_redis_ts: int = 0
    free_proxy_fetch_ts: int = 0
    sync_ts: int = 0  # 同步到redis的时间

    def is_need_sync(self) -> bool:
        return not (bool(self.sync_ts) and self.sync_ts > int(time.time()) - 600)


class AllLotScrapyStatusResp(CustomBaseModel):
    dyn_scrapy_status: Any
    topic_scrapy_status: Any
    reserve_scrapy_status: Any
