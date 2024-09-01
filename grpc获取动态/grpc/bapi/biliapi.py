import asyncio
import hashlib
import random
import urllib.parse
from curl_cffi import requests
from curl_cffi.requests import BrowserType
from grpc获取动态.grpc.bapi.base_log import bapi_log
from grpc获取动态.grpc.bapi.models import LatestVersionBuild
from utl.代理.request_with_proxy import request_with_proxy

proxy_req = request_with_proxy()
comm_headers = {
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json;charset=UTF-8",
    "dnt": "1",
    "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0",
}


def appsign(params, appkey='1d8b6e7d45233436', appsec='560c52ccd288fed045859ed18bffd973'):
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
    url = "https://app.bilibili.com/x/v2/version?mobi_app=android"
    resp = requests.get(url, impersonate=random.choice(list(BrowserType)).value)
    resp_dict = resp.json()
    return [LatestVersionBuild(**item) for item in resp_dict['data']]


async def get_lot_notice(bussiness_type: int, business_id: str):
    """
    获取抽奖notice
    :param bussiness_type: 抽奖类型  12:充电 1：转发抽奖 10：预约抽奖
    :param business_id:
    :return:
    """
    while 1:
        url = 'http://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice'
        params = {
            'business_type': bussiness_type,
            'business_id': business_id,
        }
        resp = await proxy_req.request_with_proxy(url=url, method='get', params=params,
                                                       headers=comm_headers,
                                                       hybrid='1'
                                                       )
        if resp.get('code') != 0:
            bapi_log.error(f'get_lot_notice Error:\t{resp}\t{bussiness_type, business_id}')
            await asyncio.sleep(10)
            if resp.get('code') == -9999:
                return resp  # 只允许code为-9999的或者是0的响应返回！其余的都是有可能代理服务器的响应而非b站自己的响应
            continue
        return resp


if __name__ == "__main__":
    print([LatestVersionBuild(**x) for x in [
        {
            "build": 8000200,
            "version": "8.0.0"
        },
        {
            "build": 7810200,
            "version": "7.81.0"
        },
        {
            "build": 7800300,
            "version": "7.80.0"
        },
        {
            "build": 7790400,
            "version": "7.79.0"
        },
        {
            "build": 7780300,
            "version": "7.78.0"
        },
        {
            "build": 7770300,
            "version": "7.77.0"
        },
        {
            "build": 7760700,
            "version": "7.76.0"
        },
        {
            "build": 7750300,
            "version": "7.75.0"
        },
        {
            "build": 7740200,
            "version": "7.74.0"
        },
        {
            "build": 7730300,
            "version": "7.73.0"
        },
        {
            "build": 7720200,
            "version": "7.72.0"
        },
        {
            "build": 7710300,
            "version": "7.71.0"
        }
    ]][:10])
