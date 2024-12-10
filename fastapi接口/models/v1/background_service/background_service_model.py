from pydantic import BaseModel, computed_field, Field


class DynScrapyStatusResp(BaseModel):
    first_dyn_id: str | int = 0
    succ_count: int = 0
    cur_stop_num: int = 0
    latest_rid: int = 0
    latest_succ_dyn_id: int = 0
    start_ts: int = 0
    freq: int | float = Field(default=0, description='爬取成功的频率，单位为（条/秒）')

    @computed_field
    @property
    def latest_succ_dyn_id_str(self) -> str:
        return str(self.latest_succ_dyn_id)

    @computed_field
    @property
    def first_dyn_id_str(self) -> str:
        return str(self.first_dyn_id)
