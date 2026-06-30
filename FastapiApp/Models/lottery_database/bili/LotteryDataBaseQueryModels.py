from Models.base.custom_pydantic import CustomBaseModel
from pydantic import Field, computed_field
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
    is_grand_prize: bool | None = Field(default=None, description="是否大奖筛选: True-是, False-否, None-不过滤")

    @computed_field
    @property
    def offset(self) -> int:
        """分页 offset: (page_num - 1) * page_size，page_num 从 1 开始

        当 page_num=0 或 page_size=0 时返回 0（由 SQL 层的 if guard 跳过分页）。
        max(0, ...) 防止 page_num=0 时返回负数。
        """
        return max(0, (self.page_num - 1) * self.page_size)
