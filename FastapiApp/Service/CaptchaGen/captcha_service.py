import asyncio
from io import BytesIO
import base64

from captcha.image import ImageCaptcha
import random
import string
import uuid

from Models.v1.CaptchaGen.model import CaptchaVerifyStatus, CaptchaVerifyStatusEnum
from Service.CaptchaGen.captcha_redis_store import RedisHelper


class CaptchaService:
    def __init__(self, captcha_timeout: int = 600):
        self.image = ImageCaptcha(
            width=64,
            height=32
        )
        self.store = RedisHelper()
        self.captcha_timeout = captcha_timeout

    async def generate_captcha(self, validate_timeout: int | None = None) -> tuple[str, str]:
        if validate_timeout is None:
            validate_timeout = self.captcha_timeout
        if validate_timeout <= 0:
            raise ValueError('validate_timeout must be greater than 0')
        # 生成随机验证码文本（4位数字组合）
        captcha_text = ''.join(random.choices(string.digits + string.ascii_letters, k=4))
        # 生成验证码图片
        captcha_image_bytes_io: BytesIO = await asyncio.to_thread(
            self.image.generate, captcha_text
        )
        # 转换为 Base64 格式
        captcha_image_base64 = base64.b64encode(captcha_image_bytes_io.getvalue()).decode('utf-8')
        # 生成随机 ID 并存储验证码内容
        captcha_id = uuid.uuid4().hex
        await self.store.set_id(captcha_id, captcha_text, validate_timeout)
        return captcha_id, captcha_image_base64

    async def validate_captcha(self, captcha_id, input_text) -> CaptchaVerifyStatus:
        """
        只要内容一致就行了，空格什么的无所谓
        """
        captcha_text = await self.store.get_captcha(captcha_id)
        trim_input_text = input_text.replace(' ', '')
        if not captcha_text:
            return CaptchaVerifyStatus(value=CaptchaVerifyStatusEnum.EXPIRED)
        if trim_input_text.lower() == captcha_text.lower():
            return CaptchaVerifyStatus(value=CaptchaVerifyStatusEnum.VALID)
        return CaptchaVerifyStatus(value=CaptchaVerifyStatusEnum.INVALID)


if __name__ == '__main__':
    captcha = CaptchaService()
    print(asyncio.run(captcha.generate_captcha()))
