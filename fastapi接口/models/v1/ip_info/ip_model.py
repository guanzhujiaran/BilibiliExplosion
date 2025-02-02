from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class IpInfoResp(CustomBaseModel):
    ipv6: str
