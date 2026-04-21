from Models.base.custom_pydantic import CustomBaseModel
from pydantic import Field
from enum import Enum

from Models.lottery_database.bili.comm import BiliLotDataStatusEnum, LotteryBusinessType


class BiliLotDataQueryModel(CustomBaseModel):
    business_type: LotteryBusinessType = Field(...)
    status: BiliLotDataStatusEnum = Field(BiliLotDataStatusEnum.UNFINISHED)
    page_num: int = Field(..., ge=0)
    page_size: int = Field(..., ge=0)
    start_ts: int | None = Field(..., ge=0)
    end_ts: int | None = Field(..., ge=0)
    sender_uid: int | None = Field(...,ge=0)
    min_participants: int | None = Field(...,ge=0)
    max_participants: int | None = Field(...,ge=0)
