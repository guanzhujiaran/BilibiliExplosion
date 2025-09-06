from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from Service.CaptchaGen.captcha_service import CaptchaService
from .base import new_router

router = new_router()
captcha_service = CaptchaService()


@router.get("/generate")
async def generate_captcha():
    captcha_id, captcha_image = captcha_service.generate_captcha()
    # 将验证码图片转换为字节流
    image_bytes = BytesIO()
    captcha_image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    # 返回验证码图片和随机 ID
    return {
        "captcha_id": captcha_id,
        "image": StreamingResponse(image_bytes, media_type="image/png")
    }


@router.post("/validate")
async def validate_captcha(captcha_id: str, input_text: str):
    if not captcha_service.validate_captcha(input_text, captcha_text):
        raise HTTPException(status_code=400, detail="Invalid captcha")
    return {"message": "Captcha validated successfully"}
