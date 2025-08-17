from datetime import datetime, timedelta
from enum import StrEnum
from typing import Optional, Dict
from pydantic import Field
from pydantic import computed_field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class LotdataResp(CustomBaseModel):
    @computed_field
    @property
    def business_id_str(self) -> str:
        return str(self.business_id)

    @computed_field
    @property
    def sender_uid_str(self) -> str:
        return str(self.sender_uid)

    lottery_id: int | None
    business_id: int | None
    status: int | None
    lottery_time: int | None
    lottery_at_num: int | None
    lottery_feed_limit: int | None
    first_prize: int | None
    second_prize: int | None
    third_prize: int | None
    lottery_result: str | None
    first_prize_cmt: str | None
    second_prize_cmt: str | None
    third_prize_cmt: str | None
    first_prize_pic: str | None
    second_prize_pic: str | None
    third_prize_pic: str | None
    need_post: int | None
    business_type: int | None
    sender_uid: int | None
    prize_type_first: str | None
    prize_type_second: str | None
    prize_type_third: str | None
    pay_status: int | None
    ts: int | None
    _gt_: int | None
    has_charge_right: str | None
    lottery_detail_url: str | None
    participants: int | None
    participated: str | None
    vip_batch_sign: str | None
    exclusive_level: str | None
    followed: int | None
    reposted: int | None
    custom_extra_key: str | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class reserveInfo(CustomBaseModel):
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在


class TUpReserveRelationInfoResp(CustomBaseModel):
    @computed_field
    @property
    def upmid_str(self) -> str:
        if self.upmid:
            return str(self.upmid)
        return '0'

    @computed_field
    @property
    def oid_str(self) -> str:
        if self.oid:
            return str(self.oid)
        return '0'

    @computed_field
    @property
    def dynamicId_str(self) -> str:
        if self.dynamicId:
            return str(self.dynamicId)
        return '0'

    ids: int | None  # 主键
    code: int | None
    message: str | None
    ttl: int | None
    sid: int | None
    name: str | None
    total: int | None
    stime: int | None
    etime: int | None
    isFollow: int | None
    state: int | None
    oid: str | None
    type: int | None
    upmid: int | None
    reserveRecordCtime: int | None
    livePlanStartTime: int | None
    upActVisible: int | None
    lotteryType: int | None
    text: str | None
    jumpUrl: str | None
    dynamicId: str | None
    reserveTotalShowLimit: int | None
    desc: str | None
    start_show_time: int | None
    BaseJumpUrl: str | None  # 可能为空，设置为 Optional 并提供默认值
    OidView: int | None  # 可能为空，设置为 Optional 并提供默认值
    hide: str | None  # 可能为空，设置为 Optional 并提供默认值
    ext: str | None  # 可能为空，设置为 Optional 并提供默认值
    subType: str | None  # 可能为空，设置为 Optional 并提供默认值
    productIdPrice: str | Dict | None  # JSON 字段，可能为空
    reserve_products: str | Dict | None  # JSON 字段，可能为空
    raw_JSON: str | Dict | None  # JSON 字段，可能为空
    reserve_round_id: int | None
    new_field: str | Dict | None  # 是否有新的字段，默认为 None

    class Config:
        from_attributes = True


class ReserveInfoResp(reserveInfo):
    app_sche: str
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在
    raw: TUpReserveRelationInfoResp


class CommonLotteryResp(CustomBaseModel):
    dynId: str
    dynamicUrl: str
    authorName: str
    up_uid: int
    pubTime: datetime
    dynContent: str
    commentCount: Optional[int] = 0
    repostCount: Optional[int] = 0
    highlightWords: str
    officialLotType: str
    officialLotId: str
    isOfficialAccount: int
    isManualReply: str
    isFollowed: int
    isLot: int
    hashTag: str


class OfficialLotteryResp(CustomBaseModel):
    jump_url: str
    app_sche: str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int
    raw: LotdataResp


class ChargeLotteryResp(CustomBaseModel):
    jump_url: str
    app_sche: str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int
    upower_level_str: str
    raw: LotdataResp


class TopicLotteryResp(CustomBaseModel):
    jump_url: str
    app_sche: str
    title: str
    end_date_str: str
    lot_type_text: str
    lottery_pool_text: str
    lottery_sid: Optional[str]


class LiveLotteryResp(CustomBaseModel):
    live_room_url: str
    app_schema: str
    award_name: str
    type: str
    end_time: int
    total_price: int
    danmu: str
    anchor_uid: int
    room_id: int
    lot_id: int
    require_type: int


class AllLotteryResp(CustomBaseModel):
    common_lottery: list[CommonLotteryResp] = Field(..., description="一般抽奖")
    must_join_common_lottery: list[CommonLotteryResp] = Field(..., description="必抽的一般抽奖")
    reserve_lottery: list[reserveInfo] = Field(..., description="必抽的预约抽奖")
    official_lottery: list[OfficialLotteryResp] = Field(..., description="必抽的官方抽奖")


class AddDynamicLotteryReq(CustomBaseModel):
    dynamic_id_or_url: str


class BulkAddDynamicLotteryReq(CustomBaseModel):
    dynamic_id_or_urls: list[str]


class BulkAddDynamicLotteryRespItem(CustomBaseModel):
    dynamic_id: str
    msg: str
    is_succ: bool


class BiliUserInfoSimple(CustomBaseModel):
    uid: str
    name: str
    face: str


class AddTopicLotteryReq(CustomBaseModel):
    topic_id: int | str


# region Description：抽奖信息统计模型
class WinnerInfo(CustomBaseModel):
    user: BiliUserInfoSimple
    count: int
    rank: int


class BiliLotStatisticInfoResp(CustomBaseModel):
    sync_ts: int
    winners: list[WinnerInfo]
    total: int


class BiliLotStatisticLotteryResultResp(CustomBaseModel):
    user: BiliUserInfoSimple
    prize_result: list[dict]
    total: int


class BiliLotStatisticLotTypeEnum(StrEnum):
    official = "official"
    reserve = "reserve"
    charge = "charge"
    total = "total"

    @classmethod
    def lot_type_2_business_type(cls, lot_type: 'BiliLotStatisticLotTypeEnum') -> int:
        mapping = {
            cls.official: 1,
            cls.reserve: 10,
            cls.charge: 12,
        }
        return mapping.get(lot_type, 0)


class BiliLotStatisticRankTypeEnum(StrEnum):
    first = "first"
    second = "second"
    third = "third"
    total = "total"


class BiliLotStatisticRankDateTypeEnum(StrEnum):
    month = "month"  # 当月
    pre_month = "pre_month"  # 上月
    year = 'year'
    pre_year = 'pre_year'
    total = "total"  # 总计

    def get_start_end_ts(self) -> tuple[int, int]:
        now = datetime.now()
        if self.value == 'total':
            return 0, 0
        elif self.value == 'month':
            start_ts = datetime(now.year, now.month, 1)  # 本月1号
            end_ts = now
        elif self.value == 'pre_month':
            start_ts = datetime(now.year, now.month - 1, 1)  # 上月1号
            end_ts = datetime(now.year, now.month, 1) - timedelta(seconds=1)  # 上月最后一天
        elif self.value == 'year':
            start_ts = datetime(now.year, 1, 1)  # 本年1号
            end_ts = now
        elif self.value == 'pre_year':
            start_ts = datetime(now.year - 1, 1, 1)  # 上年1号
            end_ts = datetime(now.year, 1, 1) - timedelta(seconds=1)  # 上年最后一天
        else:
            raise ValueError(f"Invalid rank date type: {self.value}")
        return int(start_ts.timestamp()), int(end_ts.timestamp())


# endregion


if __name__ == '__main__':
    print(BiliLotStatisticRankDateTypeEnum.pre_month.get_start_end_ts())
