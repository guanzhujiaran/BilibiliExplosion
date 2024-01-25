# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq
from bilibili.metadata.locale.locale_pb2 import Locale
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.metadata.network.network_pb2 import Network, NetworkType
from bilibili.metadata.parabox.parabox_pb2 import Exps
from bilibili.metadata.restriction.restriction_pb2 import Restriction


class Fp:
    def __init__(self, buvid_auth, device_model, device_radio_ver):
        self.buvid_auth = buvid_auth
        self.device_model = device_model
        self.device_radio_ver = device_radio_ver

    def gen(self, timestamp):
        device_fp = f"{self.buvid_auth}{self.device_model}{self.device_radio_ver}"
        device_fp_md5 = hashlib.md5(device_fp.encode()).hexdigest()

        fp_raw = device_fp_md5
        fp_raw += datetime.fromtimestamp(timestamp).strftime("%Y%m%d%H%M%S")
        fp_raw += self.gen_random_string(16)

        veri_code_str = format(
            "%02x" % (sum(int(fp_raw[i:i + 2], 16) for i in range(0, min(len(fp_raw), 62), 2)) % 256))

        fp_raw += veri_code_str

        return fp_raw

    @staticmethod
    def gen_random_string(length):
        charset = "0123456789abcdef"
        return ''.join(random.choice(charset) for _ in range(length))


def gen_random_access_key() -> str:
    charset = "abcdefghijklmnopqrstuvwxyz0123456789"
    shift_charset = "ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join([random.choice(charset) for _ in range(32)]) + \
        ''.join([random.choice(shift_charset) for _ in range(34)]) + \
        '_' + \
        ''.join([random.choice(shift_charset) for _ in range(14)]) + \
        '-' + \
        ''.join([random.choice(shift_charset) for _ in range(25)])


def random_id():
    return "".join(random.sample("0123456789abcdefghijklmnopqrstuvwxyz", 8))


def gen_aurora_eid(uid: int) -> str:
    if uid == 0:
        raise ValueError("uid must not be 0")
    result_byte = bytearray()
    mid_byte = bytearray(str(uid), "utf-8")
    key = bytearray(b"ad1va46a7lza")
    for i, v in enumerate(mid_byte):
        result_byte.append(v ^ key[i % len(key)])
    return base64.b64encode(result_byte).decode("utf-8").rstrip("=")


def fake_buvid():
    mac_list = []
    for _ in range(1, 7):
        rand_str = "".join(random.sample("0123456789abcdef", 2))
        mac_list.append(rand_str)
    rand_mac = ":".join(mac_list)
    md5 = hashlib.md5()
    md5.update(rand_mac.encode())
    md5_mac_str = md5.hexdigest()
    md5_mac = list(md5_mac_str)
    return f"XY{md5_mac[2]}{md5_mac[12]}{md5_mac[22]}{md5_mac_str}".upper()


def gen_trace_id() -> str:
    random_id = "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=32))
    random_trace_id = random_id[:24]
    b_arr = [0] * 3
    ts = int(time.time())
    for i in reversed(range(3)):
        ts >>= 8
        b_arr[i] = ts % 256 if (ts // 128) % 2 == 0 else ts % 256 - 256
    for i in range(3):
        random_trace_id += "{:02x}".format(b_arr[i] & 0xFF)
    random_trace_id += random_id[-2:]
    return f"{random_trace_id}:{random_trace_id[16:]}:0:0"


def gen_random_x_bili_ticket(buvid: str):
    suffix1 = {
        "alg": "HS256", "kid": "s03", "typ": "JWT"
    }
    now_ts = int(time.time())
    suffix2 = {
        "exp": now_ts + 29100, "iat": now_ts, "buvid": buvid
    }
    suffix = json.dumps(suffix1) + json.dumps(suffix2)
    return suffix.encode(
        "utf-8") + b':\xa8E\xb4\xab\xa4\x97\x90z]\x97\xa2B\xe5\x8b)mN\x0b\xa3\xd4e0\xd2\xe0\xa9)\x88I\xa4\xac'


@dataclass
class MetaDataNeedInfo:
    '''
    根据不同ua制作MetaData需要的不同的信息
    '''
    build: int = 7630200  # 版本号
    device_model: str = '22081212C'  # 机型
    osver: str = "13"  # 系统版本
    version_name: str = "7.63.0"  # app版本名称
    brand: str = 'Xiaomi'
    channel: str = "bili"  # 安装包渠道信息
    ua: str = 'Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 os/android model/22081212C mobi_app/android build/7630200 channel/bili innerVer/7630200 osVer/13 network/2'

    def generate_ua_from_Dalvik_appVer(self, Dalvik: str, version_name: str = "7.63.0", build: int = 7630200,
                                       channel: str = "bili", brand: str = 'Xiaomi'):

        device_model = ''.join(re.findall('Android.*?\d+; (.*?) (?:Build|MIUI)', Dalvik))
        osver = ''.join(re.findall('Android (.*?[\w]);', Dalvik))

        if device_model and osver and version_name and build and channel and brand:
            self.device_model = device_model
            self.osver = osver
            self.build = build
            self.version_name = version_name
            self.channel = channel
            self.brand = brand
        else:
            logger.error('解析Dalvik失败！')
            logger.error(f'{Dalvik}\n{build, device_model, osver, version_name, brand, channel}')
        self.ua = f'{Dalvik} {self.version_name} os/android model/{self.device_model} mobi_app/android build/{self.build} channel/{self.channel} innerVer/{self.build} osVer/{self.osver} network/2'

    def init_from_ua(self, ua: str, brand: str):
        self.ua = ua
        build = ''.join(re.findall('build/(\d+)', ua))
        if build and str.isdigit(build):
            build = int(build)
        else:
            build = 7630200
        device_model = ''.join(re.findall('Android.*?\d+; (.*?) (?:Build|MIUI)', ua))
        osver = ''.join(re.findall('Android (.*?[\w]);', ua))
        version_name = ''.join(re.findall('\(.*?\) (.*?) ', ua))
        channel = ''.join(re.findall('channel/(\w+)', ua))
        if build and device_model and osver and version_name and brand and channel:
            self.build, self.device_model, self.osver, self.version_name, self.brand, self.channel = build, device_model, osver, version_name, brand, channel
        else:
            logger.error('解析ua失败！')
            logger.error(f'{build, device_model, osver, version_name, brand, channel}')


def make_metadata(access_key, ua="Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 "
                                 "os/android model/22081212C mobi_app/android build/7630200 channel/master "
                                 "innerVer/7630200 osVer/13 network/2",
                  brand='Xiaomi',
                  Dalvik="Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1)",
                  version_name="7.63.0",
                  build=7630200,
                  channel='bili') -> tuple:
    '''
    根据ua自动生成包含ua信息的MetaData
    :param brand:
    :param Dalvik:
    :param version_name:
    :param build:
    :param channel:
    :param access_key:
    :param ua:
    :return:
    '''
    mid = 0
    metaDataNeedInfo = MetaDataNeedInfo()
    metaDataNeedInfo.generate_ua_from_Dalvik_appVer(Dalvik, version_name, build, channel, brand)
    BUVID = fake_buvid()
    device_model = metaDataNeedInfo.device_model
    fp_generator = Fp(BUVID, device_model, "")
    gen_ts = int(time.time())
    fp = fp_generator.gen(gen_ts)
    device_params = {
        "app_id": 1,
        "mobi_app": "android",
        "device": "phone",
        "build": metaDataNeedInfo.build,
        "channel": metaDataNeedInfo.channel,
        "buvid": BUVID,
        "platform": "android",
        "brand": metaDataNeedInfo.brand,
        "model": device_model,
        "osver": metaDataNeedInfo.osver,
        "fp_local": fp,
        "fp_remote": fp,
        "version_name": metaDataNeedInfo.version_name,
        "fp": fp,
        "fts": gen_ts
    }

    metadata_params = {
        "mobi_app": "android",
        "build": metaDataNeedInfo.build,
        "channel": metaDataNeedInfo.channel,
        "buvid": BUVID,
        "platform": "android"
    }
    metadata = {
        "env": "prod",
        "app-key": "android",
        "x-bili-device-bin": Device(**device_params).SerializeToString(),
        "x-bili-local-bin": Locale().SerializeToString(),
        "x-bili-metadata-bin": Metadata(**metadata_params).SerializeToString(),
        "x-bili-network-bin": Network(type=NetworkType.WIFI).SerializeToString(),
        "x-bili-fawkes-request-bin": FawkesReq(
            appkey="android", env="prod", session_id=random_id()
        ).SerializeToString(),
        "x-bili-restriction-bin": Restriction(
            # teenagers_mode=False, lessons_mode=False, mode=ModeType.NORMAL, review=True, disable_rcmd=False
        ).SerializeToString(),
        "x-bili-exps-bin": Exps().SerializeToString(),
        "x-bili-aurora-zone": "",
        "x-bili-gaia-vtoken": "",
        # "x-bili-ticket":gen_random_x_bili_ticket(BUVID), # ticket没有搞明白怎么获取，应该是发一个请求，然后将这个请求的string作为参数，不变
        "x-bili-mid": str(mid) if mid else "",
        "x-bili-trace-id": gen_trace_id(),
        "buvid": BUVID,
        'user-agent': metaDataNeedInfo.ua,
    }
    if access_key:
        metadata["authorization"] = f"identify_v1 {access_key}"
        metadata["x-bili-aurora-eid"] = gen_aurora_eid(mid)
    return tuple(metadata.items())
