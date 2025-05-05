import time
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.GeetestDet.GetV3ClickTarget import GeetestDetectPicReq, GeetestDetectPicRes
from fastapi接口.service.geetest_captcha.jy_click_captcha import a_jy_click
from fastapi接口.service.grpc_module.Utils.极验.极验点击验证码 import GeetestV3Breaker
from .base import new_router

router = new_router()
gb = GeetestV3Breaker()


@router.post('/GetTextSelectPos', summary='获取极验点击中心（JYClick）',
             response_model=CommonResponseModel[GeetestDetectPicRes])
async def GetV3ClickTarget(geetest_det_req: GeetestDetectPicReq):
    """
    获取极验点击中心
    :param geetest_det_req:
    :return:
    """
    result = await a_jy_click(geetest_det_req.pic_url)
    reply_res = GeetestDetectPicRes(
        target_position=result.target_centers,
        ts=int(time.time())
    )
    return CommonResponseModel(data=reply_res)
