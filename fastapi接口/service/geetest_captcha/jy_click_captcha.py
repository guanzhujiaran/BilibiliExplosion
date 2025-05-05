import asyncio
import numpy as np
from curl_cffi import requests
from fastapi接口.service.geetest_captcha.textselect.src.method.jy_click import JYClick
from fastapi接口.service.grpc_module.Utils.极验.models.captcha_models import CaptchaResultInfo

cap = JYClick()


def _get_geetest_pic(geetest_pic_url) -> bytes:
    pic_resp = requests.get(geetest_pic_url, impersonate='chrome120')
    return pic_resp.content


async def a_jy_click(pic_url) -> CaptchaResultInfo:
    return await asyncio.to_thread(jy_click, pic_url)


def jy_click(pic_url) -> CaptchaResultInfo:
    img_bytes = _get_geetest_pic(pic_url)
    raw_result = cap.run(img_bytes)
    result_list = [[int((x1 + x2) / 2), int((y1 + y2) / 2)] for x1, y1, x2, y2 in raw_result]
    captcha_result_info = CaptchaResultInfo(
        target_centers=result_list,
        img_name=pic_url.replace("/", '').replace('/', '').replace(':', ''),
        origin_img=np.frombuffer(img_bytes, dtype=np.uint8),
        bboxes=result_list
    )
    return captcha_result_info
