import asyncio
import random
import time
from typing import AsyncGenerator
from urllib.parse import quote

from CONFIG import CONFIG
from fastapi接口.log.base_log import bapi_log
from fastapi接口.models.AntiRisk.Bili.WebCookie import BiliWebCookie, CookieWrapper
from fastapi接口.service.grpc_module.grpc.bapi.BiliApiBase import get_frontend_finger_spi, gen_web_ticket, \
    get_bili_main_page_raw_resp, gaia_gateway_ExClimbWuzhi, gaia_gateway_ExClimbCongling
from fastapi接口.service.grpc_module.grpc.bapi.Constants import BASE_COOKIE_KEYS, EXCLIMB_WUZHI_COOKIE_KEYS
from fastapi接口.utils.Common import asyncio_gather
from utl.加密.utils import GenWebCookieParams
from utl.加密.utils import lsid

# --- Cookie池状态变量 ---
_cookie_lock = asyncio.Lock()
_fake_cookie_list: list[CookieWrapper] = []
_cookie_queue_num = 0


async def _gen_buvid4(cookie: BiliWebCookie) -> None:
    cookie_str = cookie.to_str(include_keys=BASE_COOKIE_KEYS)
    spi_resp_dict = await get_frontend_finger_spi(cookie_str=cookie_str, bili_web_cookie=cookie)
    cookie.buvid4 = quote(spi_resp_dict.data.b_4, safe='')


async def _gen_web_ticket(cookie: BiliWebCookie) -> None:
    cookie_str = cookie.to_str(include_keys=BASE_COOKIE_KEYS)
    spi_resp_dict = await gen_web_ticket(cookie_str=cookie_str, bili_web_cookie=cookie)
    cookie.bili_ticket = spi_resp_dict['data']['ticket']
    cookie.bili_ticket_expires = spi_resp_dict['data']['created_at'] + spi_resp_dict['data']['ttl']


def _gen_lsid_hit_dyn_v2(cookie: BiliWebCookie) -> None:
    cookie.b_lsid = lsid()
    cookie.hit_dyn_v2 = '1'


async def _get_buvid3(cookie: BiliWebCookie) -> None:
    result = await get_bili_main_page_raw_resp(bili_web_cookie=cookie)
    if ua := result.request.headers.get('user-agent'):
        cookie.gen_web_cookie_params.ua = ua
    for k, v in result.cookies.items():
        setattr(cookie, k, v)


async def _active_exclimb_wuzhi(cookie: BiliWebCookie):
    await gaia_gateway_ExClimbWuzhi(
        cookie_str=cookie.to_str(include_keys=EXCLIMB_WUZHI_COOKIE_KEYS),
        payload=cookie.gen_web_cookie_params.payload_str,
        bili_web_cookie=cookie
    )


async def _active_exclimb_congling():
    await gaia_gateway_ExClimbCongling()


async def _bili_web_cookie_gen_once() -> BiliWebCookie:
    """生成单个 BiliWebCookie 实例"""
    rand_ua = CONFIG.rand_ua
    cookie = BiliWebCookie(
        gen_web_cookie_params=GenWebCookieParams(
            ua=rand_ua,
            window_h=random.randint(1080, 1440),
            window_w=random.randint(1920, 2560),
            avail_w=random.randint(1920, 2560),
            avail_h=random.randint(1080, 1440),
        )
    )
    await _get_buvid3(cookie)
    _gen_lsid_hit_dyn_v2(cookie)
    await asyncio_gather(
        _gen_buvid4(cookie),
        _gen_web_ticket(cookie),
        log=bapi_log
    )
    await _active_exclimb_wuzhi(cookie)
    cookie._is_used = False
    return cookie


async def _bili_web_cookie_generator() -> AsyncGenerator[BiliWebCookie, None]:
    """一个异步生成器，持续生成新的 Cookie"""
    while True:
        yield await _bili_web_cookie_gen_once()


# 初始化全局Cookie生成器
async_bili_cookie_iter = _bili_web_cookie_generator()


async def get_bili_cookie() -> CookieWrapper:
    """
    从池中获取一个可用的 Bilibili Cookie。如果池中 Cookie 不足，则生成新的。
    """
    global _cookie_queue_num

    async with _cookie_lock:
        # 尝试从现有列表中获取有效cookie
        if _fake_cookie_list:
            random.shuffle(_fake_cookie_list)
            for i, cw in enumerate(_fake_cookie_list):
                if cw.expire_ts > time.time() and cw.able:
                    return cw
                else:
                    # 移除过期或无效的cookie
                    _fake_cookie_list.pop(i)
                    _cookie_queue_num -= 1

        # 如果池中无可用cookie或池容量未满，则生成新的
        if len(_fake_cookie_list) < 50:  # 假设池最大容量为50
            _cookie_queue_num += 1
            bapi_log.debug(
                f'当前cookie池数量：{len(_fake_cookie_list)}，总共{_cookie_queue_num}个cookie，前往获取新的cookie'
            )
            new_ck = await anext(async_bili_cookie_iter)
            cookie_data = CookieWrapper(
                ck=new_ck,
                ua=new_ck.gen_web_cookie_params.ua,
                expire_ts=int(time.time() + 8 * 3600)  # 8小时有效期
            )
            _fake_cookie_list.append(cookie_data)
            return cookie_data

        # 如果池已满但没有可用的，等待并重试
        await asyncio.sleep(1)
        return await get_bili_cookie()


if __name__ == '__main__':
    asyncio.run(get_bili_cookie())
