from typing import TypeVar, Generic

from fastapi接口.models.base.custom_pydantic import CustomBaseModel

T = TypeVar('T')


class BiliBaseResp(CustomBaseModel, Generic[T]):
    code: int
    data: T
    message: str


class FrontendFingerSpiResp(CustomBaseModel):
    b_3: str
    b_4: str
