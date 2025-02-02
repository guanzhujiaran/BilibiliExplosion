from pydantic import computed_field, Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class BaseScrapyStatusResp(CustomBaseModel):
    succ_count: int = 0
    cur_stop_num: int = 0
    start_ts: int = 0
    freq: int | float = Field(default=0, description='爬取成功的频率，单位为（条/秒）')
    is_running: bool = False


class DynScrapyStatusResp(BaseScrapyStatusResp):
    latest_rid: int = 0
    latest_succ_dyn_id: int = 0
    first_dyn_id: str | int = 0
    update_ts: int = 0  # 最后更新时间

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
    update_ts: int = 0  # 最后更新时间

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
    update_ts: int = 0  # 最后更新时间


class AllLotScrapyStatusResp(CustomBaseModel):
    dyn_scrapy_status: DynScrapyStatusResp = DynScrapyStatusResp()
    topic_scrapy_status: TopicScrapyStatusResp = TopicScrapyStatusResp()
    reserve_scrapy_status: ReserveScrapyStatusResp = ReserveScrapyStatusResp()
