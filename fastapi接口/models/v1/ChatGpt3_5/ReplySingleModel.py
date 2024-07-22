from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReplyReq(BaseModel):
    """
    请求内容
    """
    question: str
    ts: int


class ReplyRes(BaseModel):
    """
    ai回复内容
    """
    answer: str
    ts: int


class OpenAiClientModel(BaseModel):
    OpenAiclient: Any  # langchain用的v1的pydantic 和fastapi的v2版本不兼容，所以直接设置成Any，不校验
    useNum: int = 0
    isAvailable: bool = True
    latestUseDate: datetime = datetime.now()
