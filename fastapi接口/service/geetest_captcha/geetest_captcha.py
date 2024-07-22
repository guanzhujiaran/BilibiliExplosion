import asyncio
from typing import List

from grpc获取动态.Utils.极验.极验点击验证码 import GeetestV3Breaker

gb = GeetestV3Breaker()


async def get_captcha_target_center(pic_url: str) -> List[List[float]]:
    if gb.captcha_detector is None:
        gb.init_det()
    captcha_result_info = await asyncio.to_thread(gb.captcha_detector.detect, pic_url)
    return captcha_result_info.target_centers
