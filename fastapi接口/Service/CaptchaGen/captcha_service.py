import asyncio

from captcha.image import ImageCaptcha
import random
import string
import uuid

from fastapi接口.Service.CaptchaGen.captcha_redis_store import RedisHelper


class CaptchaService:
    def __init__(self, captcha_timeout: int = 600):
        self.image = ImageCaptcha()
        self.store = RedisHelper()
        self.captcha_timeout = captcha_timeout

    async def generate_captcha(self):
        # 生成随机验证码文本（4位数字组合）
        captcha_text = ''.join(random.choices(string.digits, k=4))
        # 生成验证码图片
        captcha_image = await asyncio.to_thread(
            self.image.generate, captcha_text
        )
        # 生成随机 ID 并存储验证码内容
        captcha_id = uuid.uuid4().hex
        await self.store.set_id(captcha_id, captcha_text, self.captcha_timeout)
        return captcha_id, captcha_image

    async def validate_captcha(self, captcha_id, input_text):
        captcha_text = self.captcha_store.get(captcha_id)
        if not captcha_text:
            return False
        return input_text.lower() == captcha_text.lower()
