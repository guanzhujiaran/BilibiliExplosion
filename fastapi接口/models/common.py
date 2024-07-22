from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')  # 泛型类型 T


class CommonResponseModel(BaseModel, Generic[T]):
    code: int = 0
    msg: str = 'success'
    data: T = None
