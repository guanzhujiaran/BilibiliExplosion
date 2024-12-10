import asyncio
import hashlib
import json
import random
import time
import urllib.parse
import uuid
from curl_cffi import requests
from curl_cffi.requests import BrowserType
from CONFIG import CONFIG
from fastapi接口.log.base_log import bapi_log
from grpc获取动态.Utils.UserAgentParser import UserAgentParser
from grpc获取动态.Utils.极验.models.captcha_models import GeetestRegInfo
from grpc获取动态.grpc.bapi.models import LatestVersionBuild
from utl.代理.SealedRequests import MYASYNCHTTPX
from utl.代理.request_with_proxy import request_with_proxy
from utl.加密.wbi加密 import gen_dm_args, get_wbi_params
from utl.pushme.pushme import pushme

proxy_req = request_with_proxy()
_my_sealed_req = MYASYNCHTTPX()
_custom_proxy = {'http': CONFIG.my_ipv6_addr, 'https': CONFIG.my_ipv6_addr}
black_code_list = [-412, -352]  # 异常代码，需要重试的


def _request_wrapper(func):
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                resp_dict = await func(*args, **kwargs)
                if resp_dict.get('code') is None or resp_dict.get('code') in black_code_list:
                    if kwargs.get('use_custom_proxy') is True:
                        kwargs.update({'use_custom_proxy': False})
                    raise ValueError(f'请求失败！检查响应：{resp_dict}')
                return resp_dict
            except Exception as e:
                bapi_log.exception(f'请求失败！{e}')
                await asyncio.sleep(10)

    return wrapper


def gen_trace_id() -> str:
    trace_id_uid = str(uuid.uuid4()).replace("-", "")[0:26].lower()
    trace_id_hex = hex(int(round(time.time()) / 256)).lower().replace("0x", "")
    trace_id = trace_id_uid + trace_id_hex + ":" + trace_id_uid[-10:] + trace_id_hex + ":0:0"
    return trace_id


def get_request_func(use_custom_proxy=False) -> callable:
    if use_custom_proxy:
        return _my_sealed_req.request  # 自己的ipv6发起请求
    else:
        return proxy_req.request_with_proxy  # 代理池里面的ip发起请求


def _gen_headers(*extra_headers) -> dict:
    ua = CONFIG.rand_ua
    ua_parser = UserAgentParser(ua, is_mobile=False, fetch_dest='empty', fetch_mode='cors',
                                fetch_site='same-site')
    return ua_parser.get_headers_dict(*extra_headers)


def appsign(params, appkey='1d8b6e7d45233436', appsec='560c52ccd288fed045859ed18bffd973') -> dict:
    """
    为请求参数进行 APP 签名
    :param params:
    :param appkey:
    :param appsec:

    """
    params.update({'appkey': appkey})
    params = dict(sorted(params.items()))  # 按照 key 重排参数
    query = urllib.parse.urlencode(params)  # 序列化参数
    sign = hashlib.md5((query + appsec).encode()).hexdigest()  # 计算 api 签名
    params.update({'sign': sign})
    return params


def get_latest_version_builds() -> [LatestVersionBuild]:
    url = "https://app.bilibili.com/x/v2/version"
    resp = requests.get(url, impersonate=random.choice(list(BrowserType)).value)
    resp_dict = resp.json()
    return [LatestVersionBuild(**item) for item in resp_dict['data']]


@_request_wrapper
async def get_lot_notice(business_type: int, business_id: str, origin_dynamic_id: str | int | None = None,
                         use_custom_proxy=False):
    """
    获取抽奖notice
    :param origin_dynamic_id:
    :param use_custom_proxy:
    :param business_type: 抽奖类型  12:充电 1：转发抽奖 10：预约抽奖
    :param business_id:
    :return:
    """
    while 1:
        url = 'https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice'
        params = {
            'business_type': business_type,
            'business_id': business_id,
        }
        if use_custom_proxy:
            resp = await get_request_func(use_custom_proxy=use_custom_proxy)(url=url, method='get', params=params,
                                                                             headers=_gen_headers(),
                                                                             hybrid='1',
                                                                             proxies=_custom_proxy
                                                                             )
            resp = await resp.json()
        else:
            resp = await get_request_func(use_custom_proxy=use_custom_proxy)(url=url, method='get', params=params,
                                                                             headers=_gen_headers(),
                                                                             hybrid='1',
                                                                             )
        if resp.get('code') != 0:
            pushme('get_lot_notice',
                   f'https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type={business_type}&business_id={business_id}\nget_lot_notice Error:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}')
            bapi_log.error(f'get_lot_notice Error:\t{resp}\t{params}\torigin_dynamic_id:{origin_dynamic_id}')
            if resp.get('code') == -9999:
                return resp  # 只允许code为-9999的或者是0的响应返回！其余的都是有可能代理服务器的响应而非b站自己的响应
            await asyncio.sleep(10)
            continue
        return resp


@_request_wrapper
async def reserve_relation_info(ids: int | str, use_custom_proxy=False) -> dict:
    url = 'http://api.bilibili.com/x/activity/up/reserve/relation/info?ids=' + str(ids)
    # ua = random.choice(BAPI.User_Agent_List)
    headers = {
        'accept': 'text/html,application/json',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'sec-ch-ua': "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': "\"Windows\"",
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': CONFIG.rand_ua,
        'cookie': '1'
        # 'X-Forwarded-For': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
        #                                         random.choice(range(0, 255)), random.choice(range(0, 255))),
        # 'X-Real-IP': '{}.{}.{}.{}'.format(random.choice(range(0, 255)), random.choice(range(0, 255)),
        #                                   random.choice(range(0, 255)), random.choice(range(0, 255))),
        # 'From': 'bingbot(at)microsoft.com',
    }
    if use_custom_proxy:
        req_dict = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET', url=url,
                                                                             headers=headers, hybrid='1',
                                                                             proxies=_custom_proxy
                                                                             )
    else:
        req_dict = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET', url=url,
                                                                             headers=headers, hybrid='1',
                                                                             )
    return req_dict


@_request_wrapper
async def get_space_dynamic_req_with_proxy(hostuid: int | str, offset: str, use_custom_proxy=False):
    while 1:
        url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
        headers = _gen_headers({
            "origin": "https://space.bilibili.com",
            'referer': f"https://space.bilibili.com/{hostuid}/dynamic",
            'cookie': '1'
        })
        dongtaidata = {
            'offset': offset,
            'host_mid': hostuid,
            'timezone_offset': -480,
            'platform': 'web',
            'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,decorationCard,forwardListHidden,ugcDelete,onlyfansQaCard',
            'web_location': "333.999",
        }
        dongtaidata = gen_dm_args(dongtaidata)  # 先加dm参数
        dongtaidata.update({
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.999"}, separators=(',', ':'))
        })
        wbi_sign = await get_wbi_params(dongtaidata)
        dongtaidata.update({
            'w_rid': wbi_sign['w_rid']
        })
        dongtaidata.update({
            "wts": wbi_sign['wts']
        })
        url_params = url + '?' + urllib.parse.urlencode(dongtaidata, safe='[],:')
        if use_custom_proxy:
            req = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET',
                                                                            url=url_params,
                                                                            headers=headers,
                                                                            mode='rand',
                                                                            hybrid='1',
                                                                            proxies=_custom_proxy
                                                                            )
        else:
            req = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET',
                                                                            url=url_params,
                                                                            headers=headers,
                                                                            mode='rand',
                                                                            hybrid='1',
                                                                            )
        return req


@_request_wrapper
async def get_polymer_web_dynamic_detail(dynamic_id: str | int | None = None, rid: str | int | None = None,
                                         dynamic_type: str | int | None = None, use_custom_proxy=False):
    url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail'
    headers = _gen_headers({
        "origin": "https://t.bilibili.com",
        'referer': f"https://t.bilibili.com/{dynamic_id}" if dynamic_id else f"https://t.bilibili.com/{rid}?type={dynamic_type}",
        'te': 'trailers',
        'cookie': '1'
    })
    if dynamic_id:
        data = {
            'timezone_offset': -480,
            'platform': 'web',
            'gaia_source': 'main_web',
            'id': dynamic_id,
            'features': 'itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,commentsNewVersion',
            'web_location': '333.1368',
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(',', ':'))
        }
    else:
        data = {
            'timezone_offset': -480,
            'platform': 'web',
            'gaia_source': 'main_web',
            'rid': rid,
            'type': dynamic_type,
            'features': 'itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,commentsNewVersion',
            'web_location': '333.1368',
            "x-bili-device-req-json": json.dumps({"platform": "web", "device": "pc"}, separators=(',', ':')),
            "x-bili-web-req-json": json.dumps({"spm_id": "333.1368"}, separators=(',', ':'))
        }
    wbi_sign = await get_wbi_params(data)
    data.update({
        'w_rid': wbi_sign['w_rid'],
        "wts": wbi_sign['wts']
    })
    url_with_params = url + '?' + urllib.parse.urlencode(data, safe='[],:')
    if use_custom_proxy:
        dynamic_req = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET', url=url_with_params,
                                                                                headers=headers,
                                                                                mode='single', hybrid='1',
                                                                                proxies=_custom_proxy
                                                                                )
    else:
        dynamic_req = await get_request_func(use_custom_proxy=use_custom_proxy)(method='GET', url=url_with_params,
                                                                                headers=headers,
                                                                                mode='single', hybrid='1',
                                                                                )
    return dynamic_req


async def get_geetest_reg_info(v_voucher: str,
                               h5_ua: str = "Mozilla/5.0 (Linux; Android 9; PCRT00 Build/PQ3A.190605.05081124; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 os/android model/PCRT00 build/8130300 osVer/9 sdkInt/28 network/2 BiliApp/8130300 mobi_app/android channel/master Buvid/XYC415CC0C4C410574E19A3772711795B96A8 sessionID/34420383 innerVer/8130300 c_locale/zh_CN s_locale/zh_CN disable_rcmd/0 themeId/1 sh/24 8.13.0 os/android model/PCRT00 mobi_app/android build/8130300 channel/master innerVer/8130300 osVer/9 network/2",
                               buvid: str = "",
                               ori: str = "",
                               ref: str = "",
                               ticket: str = "",
                               version: str = "8.9.0"
                               ) -> GeetestRegInfo | bool:
    url = 'https://api.bilibili.com/x/gaia-vgate/v1/register'
    data = {
        "disable_rcmd": 0,
        "mobi_app": "android",
        "platform": "android",
        "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                 separators=(',', ':')),
        "ts": int(time.time()),
        "v_voucher": v_voucher,
    }
    data = appsign(data)
    headers_raw = [
        ('native_api_from', 'h5'),
        ("cookie", f'Buvid={buvid}' if buvid else ''),
        ('buvid', buvid if buvid else ''),
        ('accept', 'application/json, text/plain, */*'),
        ("referer", "https://www.bilibili.com/h5/risk-captcha"),
        ('env', 'prod'),
        ('app-key', 'android'),
        ('env', 'prod'),
        ('app-key', 'android'),
        ("user-agent", h5_ua),
        ('x-bili-trace-id', gen_trace_id()),
        ("x-bili-aurora-eid", ''),
        ('x-bili-mid', ''),
        ('x-bili-aurora-zone', ''),
        ('x-bili-gaia-vtoken', ''),
        ('x-bili-ticket', ticket),
        ('content-type', "application/x-www-form-urlencoded; charset=utf-8"),
        # ('content-length', str(len(json.dumps(data).encode('utf-8')))),
        ('accept-encoding', 'gzip')
    ]
    # data = urllib.parse.urlencode(data)
    response = await get_request_func(use_custom_proxy=True)(
        method='POST',
        url=url,
        data=data,
        headers=headers_raw,
        proxies=_custom_proxy
    )
    resp_json = response.json()
    if resp_json.get('code') == 0:  # gt=ac597a4506fee079629df5d8b66dd4fe 这个是web端的，目标是获取到app端的gt
        if resp_json.get('data').get('geetest') is None:
            bapi_log.error(
                f"\n该风控无法通过 captcha 解除！！！获取极验信息失败: {data}\n{resp_json}\n请求头：{headers_raw}\n响应头：{response.headers}")
            return False
        bapi_log.debug(f"\n成功获取极验challenge：{resp_json}")
        return GeetestRegInfo(
            type=resp_json.get('data').get('type'),
            token=resp_json.get('data').get('token'),
            geetest_challenge=resp_json.get('data').get('geetest').get('challenge'),
            geetest_gt=resp_json.get('data').get('geetest').get('gt')
        )
    else:
        bapi_log.error(f"\n获取极验信息失败: {resp_json}")
        return False


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
                           version: str = "8.9.0"
                           ) -> str:
    """
    :param challenge:
    :param token:
    :param validate:
    :param ua:
    :return:
    """
    url = 'https://api.bilibili.com/x/gaia-vgate/v1/validate'
    data = {
        "challenge": challenge,
        "disable_rcmd": 0,
        "mobi_app": "android",
        "platform": "android",
        "seccode": validate + "|jordan",
        "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                 separators=(',', ':')),
        "token": token,
        "ts": int(time.time()),
        "validate": validate
    }
    data = appsign(data)
    headers_raw = [
        ('native_api_from', 'h5'),
        ("cookie", f'Buvid={buvid}' if buvid else ''),
        ('buvid', buvid if buvid else ''),
        ('accept', 'application/json, text/plain, */*'),
        ("referer", "https://www.bilibili.com/h5/risk-captcha"),
        ('env', 'prod'),
        ('app-key', 'android'),
        ('env', 'prod'),
        ('app-key', 'android'),
        ("user-agent", h5_ua),
        ('x-bili-trace-id', gen_trace_id()),
        ("x-bili-aurora-eid", ''),
        ('x-bili-mid', ''),
        ('x-bili-aurora-zone', ''),
        ('x-bili-gaia-vtoken', ''),
        ('x-bili-ticket', ticket),
        ('content-type', "application/x-www-form-urlencoded; charset=utf-8"),
        # ('content-length', str(len(urllib.parse.urlencode(data).encode('utf-8')))),
        ('accept-encoding', 'gzip')
    ]
    # data = urllib.parse.urlencode(data)
    response = await get_request_func(use_custom_proxy=True)(
        method='POST',
        url=url,
        data=data,
        headers=headers_raw,
        proxies=_custom_proxy
    )
    resp_json = response.json()
    if resp_json.get('code') != 0:
        bapi_log.error(
            f"\n发请求 {url} 验证validate极验失败:{challenge, token, validate}\n {resp_json}\n{data}\n{headers_raw}")
        return ''
    bapi_log.debug(f'\n发请求 {url} 验证validate极验成功：{resp_json}')
    return token


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
        brand
):
    url = 'https://app.bilibili.com/x/resource/abtest/abserver'
    ua = f'Mozilla/5.0 BiliDroid/{app_version_name} (bbcallen@gmail.com) os/android model/{model} mobi_app/android build/{app_build} channel/{channel} innerVer/{app_build} osVer/{osver} network/2'
    headers_raw = [
        ('buvid', buvid),
        ("fp_local", fp_local),
        ('fp_remote', fp_remote),
        ('session_id', session_id),
        ("guestid", str(guestid)),
        ('user-agent', ua),
        ('x-bili-trace-id', gen_trace_id()),
        ('x-bili-aurora-eid', ''),
        ('x-bili-mid', ''),
        ("x-bili-aurora-zone", ''),
        ('x-bili-gaia-vtoken', ''),
        ("x-bili-ticket", ticket),
        ('accept-encoding', 'gzip'),
    ]
    params = {
        'brand': brand,
        'build': app_build,
        'buvid': buvid,
        'c_locale': 'zh_CN',
        "channel": channel,
        'device': 'phone',
        'disable_rcmd': 0,
        'mobi_app': 'android',
        'model': model,
        'osver': osver,
        'platform': 'android',
        's_locale': 'zh_CN',
        'statistics': json.dumps({"appId": 1, "platform": 3, "version": app_version_name, "abtest": ""},
                                 separators=(',', ':')),
        'ts': int(time.time()),
    }
    signed_params = appsign(params)
    response = await get_request_func(use_custom_proxy=True)(url=url, method='get', params=signed_params,
                                                             headers=headers_raw)
    bapi_log.debug(f'\n{url}\t发请求验证成功：{response.json()}')
    return response


# async def get_guest_id():
#     """
#     获取metadata生成时的guest_id，一直会使用下去
#     :return:
#     """
#     url = 'https://passport.bilibili.com/x/passport-user/guest/reg'
#     ua = f'Mozilla/5.0 BiliDroid/{app_version_name} (bbcallen@gmail.com) os/android model/{model} mobi_app/android build/{app_build} channel/{channel} innerVer/{app_build} osVer/{osver} network/2'
#     headers_raw = [
#         ('fp_local', fp_local),
#         ("fp_remote", fp_remote),
#         ('session_id', session_id),
#         ('buvid', buvid),
#         ("env", 'prod'),
#         ('app-key', 'android'),
#         ('env', 'prod'),
#         ('app-key', 'android'),
#         ('user-agent', ua),
#         ("x-bili-trace-id", gen_trace_id()),
#         ('x-bili-aurora-eid', ''),
#         ("x-bili-mid", ''),
#         ('x-bili-aurora-zone', ''),
#         ("x-bili-gaia-vtoken", ""),
#         ("x-bili-ticket", ticket),
#         ('content-type', 'application/x-www-form-urlencoded; charset=utf-8'),
#         ('accept-encoding', 'gzip')
#     ]
#     params = {
#         'build': brand,
#         'buvid': app_build,
#         'buvid': buvid,
#         'c_locale': 'zh_CN',
#         "channel": channel,
#         'device_info': 'phone',
#         'disable_rcmd': 0,
#         'dt': '',
#         'local_id': buvid,
#         'mobi_app': 'android',
#         'platform': 'android',
#         's_locale': 'zh_CN',
#         'statistics': json.dumps({"appId": 1, "platform": 3, "version": app_version_name, "abtest": ""},
#                                  separators=(',', ':')),
#         'ts': int(time.time()),
#     }
#     signed_params = appsign(params)
#     response = await get_request_func(use_custom_proxy=True)(url=url, method='get', params=signed_params, )
#     bapi_log.debug(f'\n{url}\t发请求验证成功：{response.json()}')
#     return response


if __name__ == "__main__":
    # _custom_proxy = {'http': 'http://127.0.0.1:48978', 'https': 'http://127.0.0.1:48978'}
    _____x = asyncio.run(get_lot_notice(1, '1002115152638640195', True))
    print(_____x)
