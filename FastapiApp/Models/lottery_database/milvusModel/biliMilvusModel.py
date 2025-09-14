from Models.base.custom_pydantic import CustomBaseModel


class BiliLotData(CustomBaseModel):
    pk: int
    lottery_id: int
    prize_vec: list[float] | None
    prize_cmt: str
    lottery_time: int  # 开奖时间
