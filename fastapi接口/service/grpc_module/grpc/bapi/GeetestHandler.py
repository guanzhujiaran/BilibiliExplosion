import json
import time
from fastapi接口.log.base_log import bapi_log
from fastapi接口.service.grpc_module.Utils.response.check_resp import check_reserve_relation_info
from fastapi接口.service.grpc_module.grpc.bapi.models import LatestVersionBuild
from utl.代理.mdoel.RequestConf import RequestConf
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
from fastapi接口.service.grpc_module.grpc.bapi.Utils import appsign, gen_trace_id, request_wrapper
from fastapi接口.service.grpc_module.grpc.bapi.Constants import URL_REGISTER_GEETEST, URL_VALIDATE_GEETEST
from fastapi接口.service.grpc_module.Utils.极验.models.captcha_models import GeetestRegInfo


@request_wrapper
async def get_geetest_reg_info(v_voucher: str,
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
        )) -> GeetestRegInfo | bool:
    url = URL_REGISTER_GEETEST
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


@request_wrapper
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
                           )) -> str:
    """
    :param h5_ua
    :param challenge:
    :param token:
    :param validate:
    :return:
    """
    url = URL_VALIDATE_GEETEST
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