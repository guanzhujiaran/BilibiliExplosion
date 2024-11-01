from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class reserveInfo(BaseModel):
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在

class ReserveInfoResp(reserveInfo):
    app_sche:str
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在

class CommonLotteryResp(BaseModel):
    dynId: str
    dynamicUrl: str
    authorName: str
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


class OfficialLotteryResp(BaseModel):
    jump_url:str
    app_sche:str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int


class ChargeLotteryResp(BaseModel):
    jump_url: str
    app_sche: str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int
    upower_level_str:str

class TopicLotteryResp(BaseModel):
    jump_url: str
    app_sche:str
    title: str
    end_date_str: str
    lot_type_text: str
    lottery_pool_text: str
    lottery_sid:Optional[str]

class LiveLotteryResp(BaseModel):
    live_room_url: str
    app_schema: str
    award_name: str
    type: str
    end_time:int
    total_price: int
    danmu:str
    anchor_uid: int
    room_id:int
    lot_id: int
    require_type:int


class AllLotteryResp(BaseModel):
    common_lottery: list[CommonLotteryResp] = Field(..., description="一般抽奖")
    must_join_common_lottery: list[CommonLotteryResp] = Field(..., description="必抽的一般抽奖")
    reserve_lottery: list[reserveInfo]= Field(..., description="必抽的预约抽奖")
    official_lottery: list[OfficialLotteryResp]= Field(..., description="必抽的官方抽奖")

