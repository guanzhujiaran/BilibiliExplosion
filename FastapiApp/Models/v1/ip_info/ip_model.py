from Models.base.custom_pydantic import CustomBaseModel


class IpInfoResp(CustomBaseModel):
    ipv6: str
