import random
from urllib.parse import quote

from CONFIG import CONFIG
from fastapi接口.models.AntiRisk.Bili.WebCookie import BiliWebCookie
from fastapi接口.service.grpc_module.grpc.bapi import biliapi
from utl.加密.utils import lsid, GenWebCookieParams

BaseCookieList = [
    "buvid3",
    "b_nut",
    "b_lsid",
    "_uuid",
    "hit-dyn-v2"
]
CommonCookieList = [
    'buvid3',
    'b_nut',
    'b_lsid',
    '_uuid',
    'enable_web_push',
    'home_feed_column',
    'browser_resolution',
    'buvid4',
    'bili_ticket',
    'bili_ticket_expires',
    'buvid_fp'
]


async def _gen_buvid4(cookie: BiliWebCookie) -> None:
    cookie_str = cookie.to_str(include_keys=BaseCookieList)
    ua = cookie.gen_web_cookie_params.ua
    spi_resp_dict = await biliapi.get_frontend_finger_spi(
        cookie_str=cookie_str,
        ua=ua
    )
    cookie.buvid4 = quote(spi_resp_dict['data']['b_4'], safe='')


async def _gen_web_ticket(cookie: BiliWebCookie) -> None:
    cookie_str = cookie.to_str(include_keys=BaseCookieList)
    ua = cookie.gen_web_cookie_params.ua
    spi_resp_dict = await biliapi.gen_web_ticket(
        cookie_str=cookie_str,
        ua=ua
    )
    cookie.buvid4 = quote(spi_resp_dict['data']['b_4'], safe='')


def _gen_lsid_hit_dyn_v2(cookie: BiliWebCookie) -> None:
    """
    生成uuid
    """
    cookie.b_lsid = lsid()
    cookie.hit_dyn_v2 = '1'


async def _get_buvid3(cookie: BiliWebCookie) -> None:
    """
    这个是一直需要使用的buvid3,就是用这个buvid3激活各种东西,然后中途不能替换
    这一步设置了buvid3和b_nut
    """
    result = await biliapi.get_bili_main_page_raw_resp()  # 直接用它的ssr获取buvid3 自己生成的肯定有问题
    if ua := result.request.headers.get('user-agent'):
        cookie.gen_web_cookie_params.ua = ua
    for k, v in result.cookies.items():
        setattr(cookie, k, v)


async def _active_exclimb_wuzhi(cookie: BiliWebCookie):
    await biliapi.gaia_gateway_ExClimbWuzhi(
        cookie_str=cookie.to_str(include_keys=BaseCookieList),
        ua=cookie.gen_web_cookie_params.ua
    )

async def _active_exclimb_congling(cookie:BiliWebCookie):
    await biliapi.gaia_gateway_ExClimbCongling(
        cookie_str=cookie.to_str(include_keys=BaseCookieList),
        ua=cookie.gen_web_cookie_params.ua
    )

async def bili_web_cookie_gen() -> BiliWebCookie:
    while 1:
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
        await asyncio.gather(
            _gen_buvid4(cookie),
            _gen_web_ticket(cookie)
        )
        await _active_exclimb_wuzhi(cookie)

        yield cookie


if __name__ == '__main__':
    import asyncio

    asyncio.run(_get_buvid3(BiliWebCookie(ua='')))
