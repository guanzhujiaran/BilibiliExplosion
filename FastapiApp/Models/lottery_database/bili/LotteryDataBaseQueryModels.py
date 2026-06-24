from Models.base.custom_pydantic import CustomBaseModel
from pydantic import Field
from enum import Enum

from Models.lottery_database.bili.comm import BiliLotDataStatusEnum, LotteryBusinessType
from Models.lottery_database.bili.LotteryDataModels import (
    LotteryDataSortEnum,
    SortOrderEnum,
    TimePresetEnum,
)


class BiliLotDataQueryModel(CustomBaseModel):
    business_type: LotteryBusinessType = Field(...)
    status: BiliLotDataStatusEnum | None = Field(default=None, description="不传则不过滤状态")
    page_num: int = Field(..., ge=0)
    page_size: int = Field(..., ge=0)
    start_ts: int | None = Field(default=None, ge=0)
    end_ts: int | None = Field(default=None, ge=0)
    sender_uid: int | None = Field(default=None, ge=0)
    min_participants: int | None = Field(default=None, ge=0)
    max_participants: int | None = Field(default=None, ge=0)
    keyword: str | None = Field(default=None, description="关键词，对抽奖结果描述做 LIKE 过滤")
    created_at_preset: TimePresetEnum | None = Field(default=None, description="收录时间快捷筛选")
    pub_time_preset: TimePresetEnum | None = Field(default=None, description="发布时间快捷筛选")
    sort_by: LotteryDataSortEnum | None = Field(default=None, description="排序字段")
    sort_order: SortOrderEnum | None = Field(default=None, description="排序方向")
