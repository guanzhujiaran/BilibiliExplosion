import asyncio
import time

from curl_cffi import requests

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.GeetestDet.GetV3ClickTarget import GeetestDetectPicReq, GeetestDetectPicRes
from fastapi接口.service.geetest_captcha.geetest_captcha import get_captcha_target_center
from fastapi接口.service.geetest_captcha.textselect.src.method.jy_click import JYClick
from grpc获取动态.Utils.极验.极验点击验证码 import GeetestV3Breaker
from .base import new_router

router = new_router()
gb = GeetestV3Breaker()
cap = JYClick()


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


def _get_geetest_pic(geetest_pic_url) -> bytes:
    pic_resp = requests.get(geetest_pic_url, impersonate='chrome120')
    return pic_resp.content


@router.post('/GetTextSelectPos', summary='获取极验点击中心（YOLO）',
             response_model=CommonResponseModel[GeetestDetectPicRes])
async def GetV3ClickTarget(geetest_det_req: GeetestDetectPicReq):
    """
    获取极验点击中心
    :param geetest_det_req:
    :return:
    """
    img_bytes = _get_geetest_pic(geetest_det_req.pic_url)
    result = await asyncio.to_thread(cap.run, img_bytes)
    result = [[int((x1 + x2) / 2), int((y1 + y2) / 2)] for x1, y1, x2, y2 in result]
    reply_res = GeetestDetectPicRes(
        target_position=result,
        ts=int(time.time())
    )
    return CommonResponseModel(data=reply_res)
