from Models.common import CommonResponseModel
from Service.samsclub.Sql.SdlHelper import graphql_app
from Service.samsclub.api.samsclub_api import SamsClubApiStatus
from Service.samsclub.main import sams_club_crawler
from ApiRoutes import RouterPaths, RouterNames
from .base import new_router

router = new_router()


@router.post(
    RouterPaths.SET_NEW_AUTH_TOKEN,
    name=RouterNames.SET_NEW_AUTH_TOKEN,
    description='更新samsclub爬虫的auth_token',
    response_model=CommonResponseModel[str],
)
async def set_new_auth_token(auth_token: str):
    await sams_club_crawler.api.update_auth_token(auth_token)
    return CommonResponseModel(data="更新成功！")


router.include_router(graphql_app, prefix='/graphql')


@router.get(RouterPaths.SAMSCLUB_API_STATUS, name=RouterNames.SAMSCLUB_API_STATUS, response_model=CommonResponseModel[SamsClubApiStatus])
def samsclub_api_status():
    return CommonResponseModel(data=sams_club_crawler.api.status)
