from copy import deepcopy

import base64

import json

from enum import Enum

import random
from typing import Literal, Dict

import requests
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from hashlib import md5
from utl.redisTool.RedisManager import RedisManagerBase

HEADERS = {
    "authority": "api.bilibili.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # "Referer": "https://www.bilibili.com/video/{bvid}".format(bvid=self.bvid),
}

mixinKeyEncTab = [
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
]


@dataclass
class WbiKeys:
    img_key: str = ''
    sub_key: str = ''


class My_dm_img_Redis(RedisManagerBase):

    def __init__(self):
        super().__init__()
        self.dm_dict = {
            "get_ts": 0,
            "WbiKeys": WbiKeys()
        }

    class RedisMap(str, Enum):
        WbiKeys = "WbiKeys"

    async def get_wbiKeys(self) -> WbiKeys:
        get_datetime = datetime.fromtimestamp(self.dm_dict["get_ts"])
        if (datetime.now() - get_datetime).days >= 1:
            redis_raw = await self._get(self.RedisMap.WbiKeys.value)
            if redis_raw:
                redis_da = json.loads(redis_raw)
                if (datetime.now() - datetime.fromtimestamp(redis_da.get('get_ts'))).days >= 1:
                    img_key, sub_key = getWbiKeys()
                else:
                    img_key = redis_da.get('img_key')
                    sub_key = redis_da.get('sub_key')
            else:
                img_key, sub_key = getWbiKeys()
            self.dm_dict["WbiKeys"] = WbiKeys(
                img_key, sub_key
            )
            self.dm_dict["get_ts"] = int(datetime.now().timestamp())
            await self._setex(self.RedisMap.WbiKeys.value,
                              json.dumps({
                                  'get_ts': self.dm_dict["get_ts"],
                                  'img_key': img_key, 'sub_key': sub_key
                              }), 24 * 3600
                              )

        return self.dm_dict["WbiKeys"]


my_dm_img_Redis = My_dm_img_Redis()


def base64_encode(encoded_str, encode='utf-8'):
    """
    Base64解密函数
    :param encoded_str: Base64编码的字符串
    :return: 原始的二进制数据
    """
    encoded_str = encoded_str.encode(encode)
    encoded_str = base64.b64encode(encoded_str)
    encoded_str = encoded_str.decode()
    return encoded_str.strip('=')


def getMixinKey(orig: str):
    "对 imgKey 和 subKey 进行字符顺序打乱编码"
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, "")[:32]


def encWbi(params: dict, img_key: str, sub_key: str) -> dict:
    "为请求参数进行 wbi 签名"
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params["wts"] = curr_time  # 添加 wts 字段
    params = dict(sorted(params.items()))  # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k: "".join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v in params.items()
    }
    query = urllib.parse.urlencode(params)  # 序列化参数
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()  # 计算 w_rid
    params["w_rid"] = wbi_sign
    return {
        "w_rid": wbi_sign,
        "wts": str(curr_time)
    }


def getWbiKeys() -> tuple[str, str]:
    "获取最新的 img_key 和 sub_key"
    resp = requests.get("https://api.bilibili.com/x/web-interface/nav", headers=HEADERS)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content["data"]["wbi_img"]["img_url"]
    sub_url: str = json_content["data"]["wbi_img"]["sub_url"]
    img_key = img_url.rsplit("/", 1)[1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
    return img_key, sub_key


async def get_wbi_params(params: dict) -> Dict[Literal["w_rid", "wts"], str]:
    wbiKeys = await my_dm_img_Redis.get_wbiKeys()
    img_key, sub_key = wbiKeys.img_key, wbiKeys.sub_key
    new_pm = deepcopy(params)
    return encWbi(new_pm, img_key, sub_key)


def gen_dm_args(params: dict):
    """reference: https://github.com/SocialSisterYi/bilibili-API-collect/issues/868"""

    def get_dm_cover_img_str(num=650):
        num = random.randrange(350, 651)
        sss = f'ANGLE (Intel Inc., Intel(R) Iris(TM) Plus Graphics {num}, OpenGL 4.1)Google Inc. (Intel Inc.)'
        _dm_cover_img_str = base64_encode(sss)
        return _dm_cover_img_str

    dm_rand = 'ABCDEFGHIJK'
    dm_img_list = json.dumps([], separators=(',', ':'))
    dm_img_str = ''.join(random.sample(dm_rand, 2))  # 'V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ'
    dm_cover_img_str = ''.join(random.sample(dm_rand,
                                             2))  # "QU5HTEUgKEludGVsLCBJbnRlbChSKSBIRCBHcmFwaGljcyA2MzAgKDB4MDAwMDU5MUIpIERpcmVjdDNEMTEgdnNfNV8wIHBzXzVfMCwgRDNEMTEpR29vZ2xlIEluYy4gKEludGVsKQ"
    dm_img_inter = '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}'

    params.update(
        {
            "dm_img_list": dm_img_list,
            "dm_img_str": dm_img_str,
            "dm_cover_img_str": dm_cover_img_str,
            "dm_img_inter": dm_img_inter,
        }
    )

    return params
