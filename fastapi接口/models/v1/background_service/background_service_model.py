import time

from pydantic import computed_field, Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class ProgressStatusResp(CustomBaseModel):
    succ_count: int = 0
    start_ts: int = 0
    total_num: int = 0
    progress: float | int = Field(default=0, description='当前进度')
    is_running: bool = False
    update_ts: int = 0  # 最后更新时间


class BaseScrapyStatusResp(CustomBaseModel):
    succ_count: int = 0
    cur_stop_num: int = 0
    start_ts: int = 0
    freq: int | float = Field(default=0, description='爬取成功的频率，单位为（条/秒）')
    is_running: bool = False
    update_ts: int = 0  # 最后更新时间


class DynScrapyStatusResp(BaseScrapyStatusResp):
    latest_rid: int = 0
    latest_succ_dyn_id: int = 0
    first_dyn_id: str | int = 0

    @computed_field
    @property
    def latest_succ_dyn_id_str(self) -> str:
        return str(self.latest_succ_dyn_id)

    @computed_field
    @property
    def first_dyn_id_str(self) -> str:
        return str(self.first_dyn_id)


class TopicScrapyStatusResp(BaseScrapyStatusResp):
    latest_succ_topic_id: int = 0
    first_topic_id: str | int = 0
    latest_topic_id: int = 0  # 最后获取的话题id，不管是否成功

    @computed_field
    @property
    def latest_succ_first_topic_id_str(self) -> str:
        return str(self.latest_succ_topic_id)

    @computed_field
    @property
    def first_topic_id_str(self) -> str:
        return str(self.first_topic_id)


class ReserveScrapyStatusResp(BaseScrapyStatusResp):
    latest_succ_reserve_id: int = 0
    first_reserve_id: str | int = 0
    latest_reserve_id: int = 0  # 最后获取的话题id，不管是否成功


class ProxyStatusResp(CustomBaseModel):
    proxy_total_count: int = 0
    proxy_black_count: int = 0
    proxy_unknown_count: int = 0
    proxy_usable_count: int = 0
    mysql_sync_redis_ts: int = 0
    free_proxy_fetch_ts: int = 0
    sync_ts: int = 0  # 同步到redis的时间
    sem_value: int = 0

    def is_need_sync(self) -> bool:
        return not (bool(self.sync_ts) and self.sync_ts > int(time.time()) - 600)


class AllLotScrapyStatusResp(CustomBaseModel):
    dyn_scrapy_status: DynScrapyStatusResp = DynScrapyStatusResp()
    topic_scrapy_status: TopicScrapyStatusResp = TopicScrapyStatusResp()
    reserve_scrapy_status: ReserveScrapyStatusResp = ReserveScrapyStatusResp()
