from pydantic import BaseModel


class IpInfoResp(BaseModel):
    ipv6: str
