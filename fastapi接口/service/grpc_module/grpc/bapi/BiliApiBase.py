import time

import curl_cffi

from fastapi接口.models.AntiRisk.Bili.WebCookie import BiliWebCookie
from fastapi接口.service.grpc_module.Models.ApiResponseModel import FrontendFingerSpiResp, BiliBaseResp
from fastapi接口.service.grpc_module.Utils.UserAgentParser import UserAgentParser
from fastapi接口.service.grpc_module.grpc.bapi.Constants import URL_FRONTEND_FINGER_SPI, URL_BILI_MAIN_PAGE, \
    URL_GEN_WEB_TICKET, URL_GAIA_EXCLIMB_WUZHI
from fastapi接口.service.grpc_module.grpc.bapi.Utils import request_wrapper
from utl.代理.mdoel.RequestConf import RequestConf
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
from utl.加密.utils import hmac_sha256


def _gen_headers_base(bili_web_cookie: BiliWebCookie, exheaders: dict = None):
    ua_parser = UserAgentParser(user_agent=bili_web_cookie.gen_web_cookie_params.ua, is_mobile=False)
    base_headers = ua_parser.get_headers_dict(extra_headers_dict=exheaders)
    return base_headers


@request_wrapper
async def get_frontend_finger_spi(cookie_str: str, bili_web_cookie: BiliWebCookie,
                                  request_conf=RequestConf(
                                      is_use_custom_proxy=True,
                                      is_use_available_proxy=False,
                                      is_use_cookie=False,
                                      is_return_raw_response=False
                                  )
                                  ) -> BiliBaseResp[FrontendFingerSpiResp] | curl_cffi.Response:
    url = URL_FRONTEND_FINGER_SPI
    headers = _gen_headers_base(
        bili_web_cookie=bili_web_cookie,
        exheaders={
            "origin": "https://www.bilibili.com",
            "referer": URL_BILI_MAIN_PAGE,
            "cookie": cookie_str,
        }
    )
    cookie_data = None
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    if request_conf.is_return_raw_response:
        return resp
    return BiliBaseResp[FrontendFingerSpiResp].model_validate(resp)


@request_wrapper
async def gen_web_ticket(cookie_str: str, bili_web_cookie: BiliWebCookie,
                         request_conf=RequestConf(
                             is_use_custom_proxy=True,
                             is_use_available_proxy=False,
                             is_use_cookie=False,
                             is_return_raw_response=False
                         )
                         ):
    url = URL_GEN_WEB_TICKET
    headers = _gen_headers_base(
        bili_web_cookie=bili_web_cookie,
        exheaders={
            "origin": "https://www.bilibili.com",
            "referer": URL_BILI_MAIN_PAGE,
            "cookie": cookie_str,
        }
    )
    cookie_data = None
    o = hmac_sha256("XgwSnGZ1p", f"ts{int(time.time())}")
    params = {
        "key_id": "ec02",
        "hexsign": o,
        "context[ts]": f"{int(time.time())}",
        "csrf": ''
    }
    resp = await request_with_proxy_internal.request_with_proxy(
        method="POST",
        url=url,
        params=params,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    return resp


@request_wrapper
async def get_bili_main_page_raw_resp(bili_web_cookie: BiliWebCookie, request_conf=RequestConf(
    is_use_custom_proxy=True,
    is_use_available_proxy=False,
    is_use_cookie=False,
    is_return_raw_response=True
)) -> curl_cffi.requests.models.Response:
    url = URL_BILI_MAIN_PAGE
    headers = _gen_headers_base(
        bili_web_cookie=bili_web_cookie,
        exheaders={
            "origin": "https://www.bilibili.com",
            "referer": URL_BILI_MAIN_PAGE,
        }
    )
    cookie_data = None
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    return resp


@request_wrapper
async def gaia_gateway_ExClimbWuzhi(
        cookie_str: str,
        bili_web_cookie: BiliWebCookie,
        payload: str,
        request_conf=RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False,
            is_use_cookie=False,
            is_return_raw_response=False
        )
):
    url = URL_GAIA_EXCLIMB_WUZHI
    headers = _gen_headers_base(
        bili_web_cookie=bili_web_cookie,
        exheaders={
            "origin": "https://www.bilibili.com",
            "referer": URL_BILI_MAIN_PAGE,
            "cookie": cookie_str,
        }
    )
    cookie_data = None
    resp = await request_with_proxy_internal.request_with_proxy(
        url=url,
        method='post',
        data=payload,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )

    return resp


@request_wrapper
async def gaia_gateway_ExClimbCongling():
    ...
    # Todo: 需要破解wasm加密
