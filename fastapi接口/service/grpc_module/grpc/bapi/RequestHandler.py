from CONFIG import CONFIG
from fastapi接口.models.AntiRisk.Bili.WebCookie import BiliWebCookie
from fastapi接口.service.grpc_module.Utils.UserAgentParser import UserAgentParser
from fastapi接口.service.grpc_module.grpc.bapi.BiliCookie import get_bili_cookie, CookieWrapper
from utl.代理.mdoel.RequestConf import RequestConf


async def prepare_request_data(
        request_conf: RequestConf,
        /,
        extra_headers: dict | None = None,
        cookie_include_list: list[BiliWebCookie.__pydantic_fields_set__] | None = None
) -> tuple[CookieWrapper | None, dict]:
    """
    准备请求所需的 Cookie 和 Headers
    """
    cookie_data = None
    ua = None
    headers = extra_headers or {}

    if request_conf.is_use_cookie:
        cookie_data = await get_bili_cookie()
        ua = cookie_data.ck.gen_web_cookie_params.ua
        headers.update({'cookie': cookie_data.ck.to_str(include_keys=cookie_include_list)})

    ua = ua or CONFIG.rand_ua
    ua_parser = UserAgentParser(ua, is_mobile=False)
    base_headers = ua_parser.get_headers_dict(extra_headers_dict=headers)

    return cookie_data, base_headers
