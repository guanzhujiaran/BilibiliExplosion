from typing import TypeVar, Generic
from fastapi接口.models.base.custom_pydantic import CustomBaseModel
T = TypeVar('T')  # 泛型类型 T
class CommonResponseModel(CustomBaseModel, Generic[T]):
    code: int = 0
    msg: str = 'success'
    data: T = None


class ResponsePaginationItems(CustomBaseModel, Generic[T]):
    items: list[T]
    total: int

if __name__ == '__main__':
    class __t(CustomBaseModel):
        a: int
        b: str

    a = ResponsePaginationItems[__t](
        items=[__t(a=1, b='a'), __t(a=2, b='b')],
        total=114514
    )
    print(a)