from typing import List

from pydantic import BaseModel


class GeetestDetectPicReq(BaseModel):
    """
    请求内容
    """
    pic_url: str
    ts: int


class GeetestDetectPicRes(BaseModel):
    """
    ai回复内容
    """
    target_position: List[List[int]]
    ts: int
