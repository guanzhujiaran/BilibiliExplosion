from typing import Literal

from Models.common import CommonResponseModel
from Models.v1.background_service.background_service_model import ProgressStatusResp
from Service.samsclub.Sql.SdlHelper import graphql_app
from Service.samsclub.main import sams_club_crawler
from .base import new_router

router = new_router()

@router.post(
    '/set_new_auth_token',
    description='更新samsclub爬虫的auth_token',
    response_model=CommonResponseModel[str],
)
async def set_new_auth_token(auth_token: str):
    await sams_club_crawler.api.update_auth_token(auth_token)
    return CommonResponseModel(data="更新成功！")

router.include_router(graphql_app, prefix='/graphql')
