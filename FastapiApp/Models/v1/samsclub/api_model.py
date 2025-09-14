from typing import TypeVar, Generic, Optional

from pydantic import TypeAdapter

from Models.base.custom_pydantic import CustomBaseModel

T = TypeVar('T')


class ApiResponse(CustomBaseModel, Generic[T]):
    code: str
    data: Optional[T] = None
    errorMsg: str = ""
    msg: str = ""
    requestId: str
    rt: int
    success: bool
    traceId: str


class UserProfile(CustomBaseModel):
    autoRenew: bool
    blackFlag: bool
    cardStatus: int
    cardType: int
    countryCode: str
    headUrl: str
    idType: int
    isExperienceCard: int
    isMember: int
    language: str
    mobile: str
    nickname: str
    realName: str
    recommendStatus: int
    sex: int
    uid: str
    userName: str


RespUserProfile = TypeAdapter(ApiResponse[UserProfile])

__slot__ = [
    'RespUserProfile',
    'ApiResponse',
    'UserProfile'
]
