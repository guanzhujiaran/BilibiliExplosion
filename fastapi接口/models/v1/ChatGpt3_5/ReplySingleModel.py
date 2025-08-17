from datetime import datetime
from typing import Any, Optional

from pydantic import computed_field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class ReplyReq(CustomBaseModel):
    """
    请求内容
    """
    question: str
    ts: int


class ReplyRes(CustomBaseModel):
    """
    ai回复内容
    """
    answer: str
    ts: int


class OpenAiClientModel(CustomBaseModel):
    OpenAiclient: Optional[Any] = None  # langchain用的v1的pydantic 和fastapi的v2版本不兼容，所以直接设置成Any，不校验
    base_url: str = ""
    useNum: int = 0
    isAvailable: bool = True
    latestUseDate: datetime = datetime.now()


class LLMShowInfo(CustomBaseModel):
    available_num: int
    total_num: int

    _llm_list: list[OpenAiClientModel] = []

    @computed_field
    @property
    def llm_list(self) -> list[OpenAiClientModel]:
        return self._llm_list

    @llm_list.setter
    def llm_list(self, value: list[OpenAiClientModel]):
        self._llm_list = [OpenAiClientModel(
            base_url=x.base_url,
            useNum=x.useNum,
            isAvailable=x.isAvailable,
            latestUseDate=x.latestUseDate
        ) for x in value]
