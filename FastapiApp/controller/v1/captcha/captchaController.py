from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from Models.common import CommonResponseModel
from Models.v1.CaptchaGen.model import CaptchaGenResp, CaptchaVerifyReq
from Service.CaptchaGen.captcha_service import CaptchaService
from ApiRoutes import RouterPaths, RouterNames
from .base import new_router

router = new_router()
captcha_service = CaptchaService()


@router.get(RouterPaths.GEN_CAPTCHA, name=RouterNames.GEN_CAPTCHA, description="生成验证码", response_model=CommonResponseModel[CaptchaGenResp])
async def generate_captcha():
    captcha_id, captcha_image_base64 = await captcha_service.generate_captcha()
    return CommonResponseModel(
        data=CaptchaGenResp(
            captcha_id=captcha_id,
            image=captcha_image_base64
        )
    )


@router.post(RouterPaths.VERIFY_CAPTCHA, name=RouterNames.VERIFY_CAPTCHA, response_model=CommonResponseModel[str])
async def validate_captcha(body: CaptchaVerifyReq):
    res = await captcha_service.validate_captcha(body.captcha_id, body.input_text)
    return CommonResponseModel(
        code=res.code,
        data=res.message,
    )
