import asyncio
import time
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.GeetestDet.GetV3ClickTarget import GeetestDetectPicReq, GeetestDetectPicRes
from fastapi接口.service.geetest_captcha.geetest_captcha import get_captcha_target_center
from fastapi接口.service.geetest_captcha.jy_click_captcha import _get_geetest_pic, a_jy_click
from grpc获取动态.Utils.极验.极验点击验证码 import GeetestV3Breaker
from .base import new_router

router = new_router()
gb = GeetestV3Breaker()


@router.post('/GetV3ClickTarget', summary='获取极验点击中心（CLIP）',
             response_model=CommonResponseModel[GeetestDetectPicRes])
async def GetV3ClickTarget(geetest_det_req: GeetestDetectPicReq):
    """
    获取极验点击中心
    :param geetest_det_req:
    :return:
    """
    result = await get_captcha_target_center(geetest_det_req.pic_url)
    reply_res = GeetestDetectPicRes(
        target_position=[[int(y) for y in x] for x in result],
        ts=int(time.time())
    )
    return CommonResponseModel(data=reply_res)


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
