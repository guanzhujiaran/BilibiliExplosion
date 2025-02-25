from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.ip_info.ip_model import IpInfoResp
from fastapi接口.service.ipinfo.get_ipv6 import get_ipv6_from_redis
from .base import new_router

router = new_router()


@router.get('/get', summary='获取ipv6地址信息',
            response_model=CommonResponseModel[IpInfoResp])
async def get_ip_info():
    ipv6_redis = await get_ipv6_from_redis()
    return CommonResponseModel(
        data=IpInfoResp(ipv6=ipv6_redis if ipv6_redis else "")
    )
