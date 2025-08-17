from typing import Optional

from fastapi接口.models.base.custom_pydantic import CustomBaseModel

class TopicLotData(CustomBaseModel):
    topic_id:int|str

class LotDataReq(CustomBaseModel):
    business_type: int | str
    business_id: int | str
    origin_dynamic_id: Optional[int | str] = None


class LotDataDynamicReq(CustomBaseModel):
    dynamic_id: int | str


if __name__ == "__main__":
    def _test(
            business_type: int | str,
            business_id: int | str,
            *args,
            **kwargs):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        print(args)
        print(kwargs)
        _ = LotDataReq(
            business_type=business_type, business_id=business_id, **kwargs
        )
        print(_)
        print(_.model_dump())


    _test(1, 2, 1, 2, 3)
