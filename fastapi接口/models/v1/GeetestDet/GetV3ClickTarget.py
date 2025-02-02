from typing import List
from fastapi接口.models.base.custom_pydantic import CustomBaseModel

class GeetestDetectPicReq(CustomBaseModel):
    """
    请求内容
    """
    pic_url: str
    ts: int


class GeetestDetectPicRes(CustomBaseModel):
    """
    ai回复内容
    """
    target_position: List[List[int]]
    ts: int
