import asyncio
import hashlib
import json
import random
import time
import urllib.parse
import uuid
from typing import Callable

import curl_cffi.requests.models
from curl_cffi import requests
from curl_cffi.requests import BrowserType

from CONFIG import CONFIG
from fastapi接口.log.base_log import bapi_log
from fastapi接口.service.grpc_module.Models.CustomRequestErrorModel import RequestKnownError
from fastapi接口.service.grpc_module.Utils.UserAgentParser import UserAgentParser
from fastapi接口.service.grpc_module.Utils.response.check_resp import check_reserve_relation_info
from fastapi接口.service.grpc_module.Utils.极验.models.captcha_models import GeetestRegInfo
from fastapi接口.service.grpc_module.grpc.bapi.models import LatestVersionBuild
from utl.pushme.pushme import a_pushme
from utl.代理.mdoel.RequestConf import RequestConf
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
from utl.加密.utils import hmac_sha256
from utl.加密.wbi加密 import gen_dm_args, get_wbi_params

_custom_proxy = CONFIG.custom_proxy
black_code_list = [-412, -352]  # 异常代码，需要重试的


def _request_wrapper(func: Callable):
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                resp_dict = await func(*args, **kwargs)
                return resp_dict
            except RequestKnownError:
                continue
            except Exception as e:
                bapi_log.error(f"方法：【{func.__name__}】 请求失败！{e}")
                await asyncio.sleep(10)

    return wrapper


def gen_trace_id() -> str:
    trace_id_uid = str(uuid.uuid4()).replace("-", "")[0:26].lower()
    trace_id_hex = hex(int(round(time.time()) / 256)).lower().replace("0x", "")
    trace_id = trace_id_uid + trace_id_hex + ":" + trace_id_uid[-10:] + trace_id_hex + ":0:0"
    return trace_id


def _gen_headers(*extra_headers: dict) -> dict:
    ua = CONFIG.rand_ua
    ua_parser = UserAgentParser(ua, is_mobile=False)
    return ua_parser.get_headers_dict(*extra_headers)


def appsign(params, appkey="1d8b6e7d45233436", appsec="560c52ccd288fed045859ed18bffd973") -> dict:
    """
    为请求参数进行 APP 签名
    :param params:
    :param appkey:
    :param appsec:

    """
    params.update({"appkey": appkey})
    params = dict(sorted(params.items()))  # 按照 key 重排参数
    query = urllib.parse.urlencode(params)  # 序列化参数
    sign = hashlib.md5((query + appsec).encode()).hexdigest()  # 计算 api 签名
    params.update({"sign": sign})
    return params


def get_latest_version_builds() -> list[LatestVersionBuild]:
    url = "https://app.bilibili.com/x/v2/version"
    resp = requests.get(url, impersonate=random.choice(list(BrowserType)).value)
    resp_dict = resp.json()
    return [LatestVersionBuild(**item) for item in resp_dict["data"]]


@_request_wrapper
async def get_reply_main(
        dynamic_id,
        rid,
        pn,
        _type,
        mode,
        request_conf: RequestConf = RequestConf(
            use_custom_proxy=True,
            is_use_available_proxy=False
        ),
):
    """
           mode 3是热评，2是最新，大概
           :param dynamic_id:
           :param rid:
           :param pn:
           :param _type:
           :param mode:
           :param request_conf:
           :return:
           """
    if mode:
        mode = mode[0]
    else:
        mode = 2
    ctype = 17
    if str(_type) == "8":
        ctype = 1
    elif str(_type) == "4" or str(_type) == "1":
        ctype = 17
    elif str(_type) == "2":
        ctype = 11
    elif str(_type) == "64":
        ctype = 12
    if len(str(rid)) == len(str(dynamic_id)):
        oid = dynamic_id
    else:
        oid = rid
    headers = _gen_headers()
    pinglunurl = "https://api.bilibili.com/x/v2/reply/main?next=" + str(pn) + "&type=" + str(ctype) + "&oid=" + str(
        oid) + "&mode=" + str(mode) + "&plat=1&_=" + str(int(time.time()))
    pinglundata = {
        "jsonp": "jsonp",
        "next": pn,
        "type": ctype,
        "oid": oid,
        "mode": mode,
        "plat": 1,
        "_": time.time()
    }
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=pinglunurl,
        params=pinglundata,
        headers=headers,
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def get_web_topic(
        topic_id: int,
        request_conf: RequestConf = RequestConf(
            use_custom_proxy=True,
            is_use_available_proxy=False
        ),
):
    url = "https://app.bilibili.com/x/topic/web/details/top"
    params = {
        "topic_id": topic_id,
        "source": "Web"
    }
    headers = _gen_headers()

    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        params=params,
        headers=headers,
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def get_lot_notice(
        business_type: str | int,
        business_id: str | int,
        origin_dynamic_id: str | int | None = None,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False
        )
):
    """
    获取抽奖notice
    :param origin_dynamic_id:
    :param business_type: 抽奖类型  12:充电 1：转发抽奖 10：预约抽奖
    :param business_id:
    :param request_conf:
    :return:
    """
    while 1:
        url = "https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice"
        params = {
            "business_type": business_type,
            "business_id": business_id,
        }
        headers = _gen_headers()
        resp = await request_with_proxy_internal.request_with_proxy(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            request_conf=request_conf
        )
        if resp.get("code") != 0:
            if resp.get("code") == -9999:
                return resp  # 只允许code为-9999的或者是0的响应返回！其余的都是有可能代理服务器的响应而非b站自己的响应
            bapi_log.critical(f"get_lot_notice响应代码错误:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
            await a_pushme("get_lot_notice响应代码错误！",
                           f"https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type="
                           f"{business_type}&business_id={business_id}\nget_lot_notice Error:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
            await asyncio.sleep(100)
            continue
        # resp_business_id = resp.get("data", {}).get("business_id")
        # resp_business_type = resp.get("data", {}).get("business_type")
        # if str(business_type) != "2" and str(business_id) != str(resp_business_id):  # 非图片动态响应才使用business_id判断
        #     bapi_log.error(f"get_lot_notice响应内容错误:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
        #     await asyncio.to_thread(
        #         pushme,
        #         f"get_lot_notice响应内容错误，business_type{business_type}！",
        #         f"https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type="
        #         f"{business_type}&business_id={business_id}\nget_lot_notice Error:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
        #     await asyncio.sleep(10)
        #     continue
        # 用的是自己的代理就不需要检查返回的是不是正确的响应了
        # if str(business_type) == "2" and origin_dynamic_id and str(origin_dynamic_id) != str(resp_business_id):
        #     bapi_log.error(f"get_lot_notice响应内容错误:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
        #     await asyncio.to_thread(
        #         pushme,
        #         f"get_lot_notice响应内容错误，business_type{business_type}！",
        #         f"https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type="
        #         f"{business_type}&business_id={business_id}\nget_lot_notice Error:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}")
        #     await asyncio.sleep(100)
        #     continue
        return resp


@_request_wrapper
async def reserve_relation_info(
        ids: int | str,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False
        )
) -> dict:
    url = "https://api.bilibili.com/x/activity/up/reserve/relation/info?ids=" + str(ids)
    headers = _gen_headers()
    req_dict = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf
    )
    check_reserve_relation_info(req_dict, ids=ids)
    return req_dict


@_request_wrapper
async def get_space_dynamic_req_with_proxy(
        hostuid: int | str,
        offset: str,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=False,
            is_use_available_proxy=False,
            is_use_cookie=True
        )
):
    """
    offset不能为0，需要为0的时候传入空字符串即可
    :param hostuid:
    :param offset:
    :param request_conf:
    :return:
    """
    offset = offset if offset else ""
    url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    headers = _gen_headers({
        "origin": "https://space.bilibili.com",
        "referer": f"https://space.bilibili.com/{hostuid}/dynamic",
    })
    dongtaidata = {
        "offset": offset,
        "host_mid": hostuid,
        "timezone_offset": -480,
        "platform": "web",
        "features": "itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,ugcDelete,onlyfansQaCard",
        "web_location": "333.1387",
    }
    dongtaidata = gen_dm_args(dongtaidata)  # 先加dm参数
    dongtaidata.update({
        "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(",", ":")),
        "x-bili-web-req-json": json.dumps({"spm_id": "333.1387"}, separators=(",", ":"))
    })
    wbi_sign = await get_wbi_params(dongtaidata)
    dongtaidata.update({
        "w_rid": wbi_sign["w_rid"]
    })
    dongtaidata.update({
        "wts": wbi_sign["wts"]
    })
    url_params = url + "?" + urllib.parse.urlencode(dongtaidata, safe="[],:")
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url_params,
        headers=headers,
        request_conf=request_conf,
    )
    return resp


@_request_wrapper
async def get_bili_main_page_raw_resp(request_conf=RequestConf(
    is_use_custom_proxy=True,
    is_use_available_proxy=False,
    is_use_cookie=False,
    is_return_raw_response=True
)) -> curl_cffi.requests.models.Response:
    url = "https://www.bilibili.com/"
    headers = _gen_headers({
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
    })
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def get_frontend_finger_spi(cookie_str: str, ua: str,
                                  request_conf=RequestConf(
                                      is_use_custom_proxy=True,
                                      is_use_available_proxy=False,
                                      is_use_cookie=False,
                                      is_return_raw_response=False
                                  )
                                  ):
    url = "https://api.bilibili.com/x/frontend/finger/spi"
    headers = _gen_headers({
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "cookie": cookie_str,
        "user-agent": ua
    })
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def gen_web_ticket(cookie_str: str, ua: str,
                         request_conf=RequestConf(
                             is_use_custom_proxy=True,
                             is_use_available_proxy=False,
                             is_use_cookie=False,
                             is_return_raw_response=False
                         )
                         ):
    url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
    headers = _gen_headers({
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "cookie": cookie_str,
        "user-agent": ua
    })
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
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def gaia_gateway_ExClimbWuzhi(
        cookie_str: str,
        ua: str,
        payload: str,
        request_conf=RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False,
            is_use_cookie=False,
            is_return_raw_response=False
        )
):
    url = "https://api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi"

    headers = _gen_headers({
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "cookie": cookie_str,
        "user-agent": ua
    })
    resp = await request_with_proxy_internal.request_with_proxy(
        url=url,
        method='post',
        data=payload,
        headers=headers,
        request_conf=request_conf
    )

    return resp


@_request_wrapper
async def gaia_gateway_ExGetAxe(
        cookie_str: str,
        ua: str,
        request_conf=RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False,
            is_use_cookie=False,
            is_return_raw_response=False
        )
):
    url = "https://api.bilibili.com/x/internal/gaia-gateway/ExGetAxe?web_location=333.1007"
    headers = _gen_headers({
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "cookie": cookie_str,
        "user-agent": ua
    })
    resp = await request_with_proxy_internal.request_with_proxy(
        url=url,
        method='GET',
        headers=headers,
        request_conf=request_conf
    )

    return resp


@_request_wrapper
async def get_polymer_web_dynamic_detail(
        dynamic_id: str | int | None = None,
        rid: str | int | None = None,
        dynamic_type: str | int | None = None,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=False,
            is_use_available_proxy=False,
            is_use_cookie=True
        )
):
    url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail"
    headers = _gen_headers({
        "origin": "https://t.bilibili.com",
        "referer": f"https://t.bilibili.com/{dynamic_id}" if dynamic_id else f"https://t.bilibili.com/{rid}?type={dynamic_type}",
    })
    if dynamic_id:
        data = {
            "timezone_offset": -480,
            "platform": "web",
            "gaia_source": "main_web",
            "id": dynamic_id,
            "features": "itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,editable,opusPrivateVisible,avatarAutoTheme",
            "web_location": "333.1368",
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(",", ":")),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(",", ":"))
        }
    else:
        data = {
            "timezone_offset": -480,
            "platform": "web",
            "gaia_source": "main_web",
            "rid": rid,
            "type": dynamic_type,
            "features": "itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,editable,opusPrivateVisible,avatarAutoTheme",
            "web_location": "333.1368",
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(",", ":")),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(",", ":"))
        }
    wbi_sign = await get_wbi_params(data)
    data.update({
        "w_rid": wbi_sign["w_rid"],
        "wts": wbi_sign["wts"]
    })
    url_with_params = url + "?" + urllib.parse.urlencode(data, safe="[],:")
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url_with_params,
        headers=headers,
        request_conf=request_conf
    )
    return resp


@_request_wrapper
async def get_geetest_reg_info(
        v_voucher: str,
        h5_ua: str = "Mozilla/5.0 (Linux; Android 9; PCRT00 Build/PQ3A.190605.05081124; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 os/android model/PCRT00 build/8130300 osVer/9 sdkInt/28 network/2 BiliApp/8130300 mobi_app/android channel/master Buvid/XYC415CC0C4C410574E19A3772711795B96A8 sessionID/34420383 innerVer/8130300 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 themeId/1 sh/24 8.13.0 os/android model/PCRT00 mobi_app/android build/8130300 channel/master innerVer/8130300 osVer/9 network/2",
        buvid: str = "",
        ori: str = "",
        ref: str = "",
        ticket: str = "",
        version: str = "8.9.0",
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False,
            is_use_cookie=False
        )
) -> GeetestRegInfo | bool:
    url = "https://api.bilibili.com/x/gaia-vgate/v1/register"
    data = {
        "disable_rcmd": 0,
        "mobi_app": "android",
        "platform": "android",
        "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                 separators=(",", ":")),
        "ts": int(time.time()),
        "v_voucher": v_voucher,
    }
    data = appsign(data)
    headers_raw = [
        ("native_api_from", "h5"),
        ("cookie", f"Buvid={buvid}" if buvid else ""),
        ("buvid", buvid if buvid else ""),
        ("accept", "application/json, text/plain, */*"),
        ("referer", "https://www.bilibili.com/h5/risk-captcha"),
        ("env", "prod"),
        ("app-key", "android"),
        ("env", "prod"),
        ("app-key", "android"),
        ("user-agent", h5_ua),
        ("x-bili-trace-id", gen_trace_id()),
        ("x-bili-aurora-eid", ""),
        ("x-bili-mid", ""),
        ("x-bili-aurora-zone", ""),
        ("x-bili-gaia-vtoken", ""),
        ("x-bili-ticket", ticket),
        ("content-type", "application/x-www-form-urlencoded; charset=utf-8"),
        # ("content-length", str(len(json.dumps(data).encode("utf-8")))),
        ("accept-encoding", "gzip")
    ]
    # data = urllib.parse.urlencode(data)
    resp_json = await request_with_proxy_internal.request_with_proxy(
        method="POST",
        url=url,
        headers=dict(headers_raw),
        request_conf=request_conf,
    )
    if resp_json.get("code") == 0:  # gt=ac597a4506fee079629df5d8b66dd4fe 这个是web端的，目标是获取到app端的gt
        if resp_json.get("data").get("geetest") is None:
            bapi_log.warning(
                f"\n该风控无法通过 captcha 解除！！！获取极验信息失败: {data}\n{resp_json}\n请求头：{headers_raw}")
            return False
        bapi_log.debug(f"\n成功获取极验challenge：{resp_json}")
        return GeetestRegInfo(
            type=resp_json.get("data").get("type"),
            token=resp_json.get("data").get("token"),
            geetest_challenge=resp_json.get("data").get("geetest").get("challenge"),
            geetest_gt=resp_json.get("data").get("geetest").get("gt")
        )
    else:
        bapi_log.error(f"\n获取极验信息失败: {resp_json}")
        return False


@_request_wrapper
async def validate_geetest(challenge, token, validate,
                           h5_ua: str = "Mozilla/5.0 (Linux; Android 9; PCRT00 Build/PQ3A.190605.05081124; wv)"
                                        " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile "
                                        "Safari/537.36 os/android model/PCRT00 build/8130300 osVer/9 sdkInt/28 network/2 "
                                        "BiliApp/8130300 mobi_app/android channel/master "
                                        "Buvid/XYC415CC0C4C410574E19A3772711795B96A8 sessionID/34420383 "
                                        "innerVer/8130300 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 themeId/1 "
                                        "sh/24 8.13.0 os/android model/PCRT00 mobi_app/android build/8130300 "
                                        "channel/master innerVer/8130300 osVer/9 network/2",
                           buvid: str = "",
                           ori: str = "",
                           ref: str = "",
                           ticket: str = "",
                           version: str = "8.9.0",
                           request_conf: RequestConf = RequestConf(
                               is_use_custom_proxy=True,
                               is_use_available_proxy=False,
                               is_use_cookie=False
                           )
                           ) -> str:
    """
    :param h5_ua
    :param challenge:
    :param token:
    :param validate:
    :return:
    """
    url = "https://api.bilibili.com/x/gaia-vgate/v1/validate"
    data = {
        "challenge": challenge,
        "disable_rcmd": 0,
        "mobi_app": "android",
        "platform": "android",
        "seccode": validate + "|jordan",
        "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                 separators=(",", ":")),
        "token": token,
        "ts": int(time.time()),
        "validate": validate
    }
    data = appsign(data)
    headers_raw = [
        ("native_api_from", "h5"),
        ("cookie", f"Buvid={buvid}" if buvid else ""),
        ("buvid", buvid if buvid else ""),
        ("accept", "application/json, text/plain, */*"),
        ("referer", "https://www.bilibili.com/h5/risk-captcha"),
        ("env", "prod"),
        ("app-key", "android"),
        ("env", "prod"),
        ("app-key", "android"),
        ("user-agent", h5_ua),
        ("x-bili-trace-id", gen_trace_id()),
        ("x-bili-aurora-eid", ""),
        ("x-bili-mid", ""),
        ("x-bili-aurora-zone", ""),
        ("x-bili-gaia-vtoken", ""),
        ("x-bili-ticket", ticket),
        ("content-type", "application/x-www-form-urlencoded; charset=utf-8"),
        # ("content-length", str(len(urllib.parse.urlencode(data).encode("utf-8")))),
        ("accept-encoding", "gzip")
    ]
    # data = urllib.parse.urlencode(data)
    resp_json = await request_with_proxy_internal.request_with_proxy(
        method="POST",
        url=url,
        headers=dict(headers_raw),
        request_conf=request_conf
    )
    if resp_json.get("code") != 0:
        bapi_log.error(
            f"\n发请求 {url} 验证validate极验失败:{challenge, token, validate}\n {resp_json}\n{data}\n{headers_raw}")
        return ""
    bapi_log.debug(f"\n发请求 {url} 验证validate极验成功：{resp_json}")
    return token


@_request_wrapper
async def resource_abtest_abserver(
        buvid,
        fp_local,
        fp_remote,
        session_id,
        guestid,
        app_version_name,
        model,
        app_build,
        channel,
        osver,
        ticket,
        brand,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False,
            is_use_cookie=False
        )
):
    url = "https://app.bilibili.com/x/resource/abtest/abserver"
    ua = f"Mozilla/5.0 BiliDroid/{app_version_name} (bbcallen@gmail.com) os/android model/{model} mobi_app/android build/{app_build} channel/{channel} innerVer/{app_build} osVer/{osver} network/2"
    headers_raw = [
        ("buvid", buvid),
        ("fp_local", fp_local),
        ("fp_remote", fp_remote),
        ("session_id", session_id),
        ("guestid", str(guestid)),
        ("user-agent", ua),
        ("x-bili-trace-id", gen_trace_id()),
        ("x-bili-aurora-eid", ""),
        ("x-bili-mid", ""),
        ("x-bili-aurora-zone", ""),
        ("x-bili-gaia-vtoken", ""),
        ("x-bili-ticket", ticket),
        ("accept-encoding", "gzip"),
    ]
    params = {
        "brand": brand,
        "build": app_build,
        "buvid": buvid,
        "c_locale": "zh_CN",
        "channel": channel,
        "device": "phone",
        "disable_rcmd": 0,
        "mobi_app": "android",
        "model": model,
        "osver": osver,
        "platform": "android",
        "s_locale": "zh_CN",
        "statistics": json.dumps({"appId": 1, "platform": 3, "version": app_version_name, "abtest": ""},
                                 separators=(",", ":")),
        "ts": int(time.time()),
    }
    signed_params = appsign(params)
    resp_json = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        params=signed_params,
        headers=dict(headers_raw),
        request_conf=request_conf
    )
    bapi_log.debug(f"\n{url}\t发请求验证成功：{resp_json}")
    return resp_json


@_request_wrapper
async def xlive_web_interface_v1_index_getWebAreaList(
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=False,
            is_use_available_proxy=False
        )
):
    url = "https://api.live.bilibili.com/xlive/web-interface/v1/index/getWebAreaList?source_id=2"
    headers = _gen_headers({
        "origin": "https://live.bilibili.com",
        "referer": "https://live.bilibili.com/"
    })
    resp_json = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf
    )
    return resp_json


if __name__ == "__main__":
    # _custom_proxy = {"http": "http://127.0.0.1:48978", "https": "http://127.0.0.1:48978"}
    print(asyncio.run(get_polymer_web_dynamic_detail(962043520082771991, use_custom_proxy=True)))
