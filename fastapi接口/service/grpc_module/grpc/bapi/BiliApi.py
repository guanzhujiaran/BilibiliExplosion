import asyncio
import json
import random
import time
import urllib.parse

from curl_cffi import requests
from curl_cffi.requests import BrowserType

from fastapi接口.log.base_log import bapi_log
from fastapi接口.service.grpc_module.Utils.response.check_resp import check_reserve_relation_info
from fastapi接口.service.grpc_module.grpc.bapi.Constants import URL_GAIA_GET_AXE, URL_BILI_MAIN_PAGE, \
    URL_ABTEST_ABSERVER, URL_GET_WEB_AREA_LIST, \
    URL_DYNAMIC_DETAIL, URL_SPACE_DYNAMIC, URL_RESERVE_RELATION_INFO, URL_LOTTERY_NOTICE, URL_GET_WEB_TOPIC, \
    URL_REPLY_MAIN
from fastapi接口.service.grpc_module.grpc.bapi.RequestHandler import prepare_request_data
from fastapi接口.service.grpc_module.grpc.bapi.Utils import request_wrapper, appsign, gen_trace_id
from fastapi接口.service.grpc_module.grpc.bapi.models import LatestVersionBuild
from utl.pushme.pushme import a_pushme
from utl.代理.mdoel.RequestConf import RequestConf
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
from utl.加密.wbi加密 import gen_dm_args, get_wbi_params


def get_latest_version_builds() -> list[LatestVersionBuild]:
    url = "https://app.bilibili.com/x/v2/version"
    resp = requests.get(url, impersonate=random.choice(list(BrowserType)).value)
    resp_dict = resp.json()
    return [LatestVersionBuild(**item) for item in resp_dict["data"]]


@request_wrapper
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
    cookie_data, headers = await prepare_request_data(request_conf)
    pinglunurl = URL_REPLY_MAIN
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
        request_conf=request_conf,
    )
    return resp


@request_wrapper
async def get_web_topic(
        topic_id: int,
        request_conf: RequestConf = RequestConf(
            use_custom_proxy=True,
            is_use_available_proxy=False
        ),
):
    url = URL_GET_WEB_TOPIC
    params = {
        "topic_id": topic_id,
        "source": "Web"
    }
    cookie_data, headers = await prepare_request_data(request_conf)

    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        params=params,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    return resp


@request_wrapper
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
        url = URL_LOTTERY_NOTICE
        params = {
            "business_type": business_type,
            "business_id": business_id,
        }
        cookie_data, headers = await prepare_request_data(request_conf)
        resp = await request_with_proxy_internal.request_with_proxy(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            request_conf=request_conf,
            cookie_data=cookie_data,
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


@request_wrapper
async def reserve_relation_info(
        ids: int | str,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=True,
            is_use_available_proxy=False
        )
) -> dict:
    url = URL_RESERVE_RELATION_INFO
    params = {
        "ids": ids
    }
    cookie_data, headers = await prepare_request_data(request_conf)
    req_dict = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        params=params,
        url=url,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    check_reserve_relation_info(req_dict, ids=ids)
    return req_dict


@request_wrapper
async def get_space_dynamic_req_with_proxy(
        hostuid: int | str,
        offset: str,
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=False,
            is_use_available_proxy=True,
            is_use_cookie=True,
            is_return_raw_response=False
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
    url = URL_SPACE_DYNAMIC
    cookie_data, headers = await prepare_request_data(
        request_conf,
        extra_headers={
            "origin": "https://space.bilibili.com",
            "referer": f"https://space.bilibili.com/{hostuid}/dynamic",
        },
        cookie_include_list=[
            'buvid3',
            'b_nut',
            '__at_once',
            'bili_ticket',
            'bili_ticket_expires',
            'buvid4',
            'buvid_fp',
            'b_lsid'
        ]
    )
    dongtaidata = {
        "offset": offset,
        "host_mid": hostuid,
        "timezone_offset": -480,
        "platform": "web",
        "features": "itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,ugcDelete,onlyfansQaCard",
        "web_location": "333.1387",
    }
    dongtaidata = gen_dm_args(dongtaidata, gen_bili_web_cookie_params=cookie_data.ck.gen_web_cookie_params)  # 先加dm参数
    dongtaidata.update({
        "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(",", ":")),
        "x-bili-web-req-json": json.dumps({"spm_id": "333.1387"}, separators=(",", ":"))
    })
    wbi_sign = await get_wbi_params(dongtaidata)
    dongtaidata.update({
        "w_rid": wbi_sign["w_rid"],
        "wts": wbi_sign["wts"]
    })

    url_params = url + "?" + urllib.parse.urlencode(dongtaidata, safe="[],:")
    resp = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url_params,
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    return resp


@request_wrapper
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
    url = URL_GAIA_GET_AXE
    cookie_data, headers = await prepare_request_data(request_conf, {
        "origin": "https://www.bilibili.com",
        "referer": URL_BILI_MAIN_PAGE,
        "cookie": cookie_str,
        "user-agent": ua
    })
    resp = await request_with_proxy_internal.request_with_proxy(
        url=url,
        method='GET',
        headers=headers,
        request_conf=request_conf,
        cookie_data=cookie_data,
    )

    return resp


@request_wrapper
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
    url = URL_DYNAMIC_DETAIL
    cookie_data, headers = await prepare_request_data(
        request_conf,
        {
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
        request_conf=request_conf,
        cookie_data=cookie_data,
    )
    return resp


@request_wrapper
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
    url = URL_ABTEST_ABSERVER
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


@request_wrapper
async def xlive_web_interface_v1_index_getWebAreaList(
        request_conf: RequestConf = RequestConf(
            is_use_custom_proxy=False,
            is_use_available_proxy=False
        )
):
    url = URL_GET_WEB_AREA_LIST
    cookie_data, headers = await prepare_request_data(
        request_conf,
        {
            "origin": "https://live.bilibili.com",
            "referer": "https://live.bilibili.com/"
        })
    resp_json = await request_with_proxy_internal.request_with_proxy(
        method="GET",
        url=url,
        headers=headers,
        request_conf=request_conf,
        cookies=cookie_data
    )
    return resp_json


if __name__ == "__main__":
    async def _test_space():
        resp = await get_space_dynamic_req_with_proxy(
            hostuid=4237378,
            offset='',
            request_conf=RequestConf(
                is_use_custom_proxy=True,
                is_use_available_proxy=False,
                is_use_cookie=True
            )
        )
        print(resp)


    asyncio.run(_test_space())
