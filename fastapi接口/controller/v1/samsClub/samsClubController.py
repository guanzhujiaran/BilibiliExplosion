from typing import Literal

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.background_service.background_service_model import ProgressStatusResp
from fastapi接口.service.samsclub.Sql.SdlHelper import graphql_app
from fastapi接口.service.samsclub.main import sams_club_crawler
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


@router.post(
    '/crawler_op',
    description='操作爬虫',
    response_model=CommonResponseModel[bool],
)
async def samsclub_crawler_op(cmd: Literal['run', 'start', 'pause']):
    match cmd:
        case 'start':
            await sams_club_crawler.start()
        case 'pause':
            await sams_club_crawler.pause()
        case 'run':
            await sams_club_crawler.main()
    return CommonResponseModel(data=True)


@router.get('crawler_status',
            response_model=CommonResponseModel[ProgressStatusResp],
            )
async def crawler_status():
    return CommonResponseModel(data=await sams_club_crawler.get_status())


router.include_router(graphql_app, prefix='/graphql')
