from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.ip_info.ip_model import IpInfoResp
from fastapi接口.service.ipinfo.get_ipv6 import get_ipv6
from .base import new_router

router = new_router()


@router.get('/get', summary='获取ipv6地址信息',
            response_model=CommonResponseModel[IpInfoResp])
async def get_ip_info():
    return CommonResponseModel(
        data=IpInfoResp(ipv6=await get_ipv6())
    )
