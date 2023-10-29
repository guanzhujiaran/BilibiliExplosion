# -*- coding: utf-8 -*-
import base64
import hashlib
import random
import time

from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq
from bilibili.metadata.locale.locale_pb2 import Locale
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.metadata.network.network_pb2 import Network, NetworkType
from bilibili.metadata.parabox.parabox_pb2 import Exps
from bilibili.metadata.restriction.restriction_pb2 import Restriction


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


def make_metadata(access_key):
    mid = 0
    BUVID = fake_buvid()
    device_params = {
        "mobi_app": "android",
        "device": "phone",
        "build": 7380300,
        "channel": "master",
        "buvid": BUVID,
        "platform": "android",
    }
    metadata_params = device_params.copy()

    metadata = {
        "x-bili-device-bin": Device(**device_params).SerializeToString(),
        "x-bili-local-bin": Locale().SerializeToString(),
        "x-bili-metadata-bin": Metadata(**metadata_params).SerializeToString(),
        "x-bili-network-bin": Network(type=NetworkType.WIFI).SerializeToString(),
        "x-bili-fawkes-request-bin": FawkesReq(
            appkey="android64", env="prod", session_id=random_id()
        ).SerializeToString(),
        "x-bili-restriction-bin": Restriction(
            # teenagers_mode=False, lessons_mode=False, mode=ModeType.NORMAL, review=True, disable_rcmd=False
        ).SerializeToString(),
        "x-bili-exps-bin": Exps().SerializeToString(),
        "x-bili-aurora-zone": "",
        "x-bili-mid": str(mid) if mid else "",
        "x-bili-trace-id": gen_trace_id(),
        "buvid": BUVID,
        'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 13; KB2003 '
                      'Build/RKQ1.211119.001) 7.38.0 os/android model/KB2003 '
                      'mobi_app/android build/7380300 channel/master innerVer/7380300 '
                      'osVer/13 network/2',
    }
    if access_key:
        metadata["authorization"] = f"identify_v1 {access_key}"
        metadata["x-bili-aurora-eid"] = gen_aurora_eid(mid)
    return tuple(metadata.items())
