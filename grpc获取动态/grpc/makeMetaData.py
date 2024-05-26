# -*- coding: utf-8 -*-
import copy

import string

import grpc
import hmac

import base64
import hashlib
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from google.protobuf.json_format import MessageToDict
from grpc import aio
from loguru import logger
from utl.代理.SealedRequests import MYASYNCHTTPX
myreq=MYASYNCHTTPX()
from bilibili.api.ticket.v1 import ticket_pb2_grpc, ticket_pb2
from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq
from bilibili.metadata.locale.locale_pb2 import Locale, LocaleIds
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.metadata.network.network_pb2 import Network, NetworkType
from bilibili.metadata.parabox.parabox_pb2 import Exps
from bilibili.metadata.restriction.restriction_pb2 import Restriction
from datacenter.hakase.protobuf import android_device_info_pb2


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


class gen_x_bili_ticket:
    def __init__(self, device_info: bytes, fingerprint: bytes, exbadbasket: bytes = b''):
        """
        :param device_info: # context, generated with `com.bapis.bilibili.metadata.device.Device`
        :param fingerprint:        /// x-fingerprint, generated with `datacenter.hakase.protobuf.AndroidDeviceInfo`
        :param exbadbasket:        /// x-exbadbasket, can leave it empty but should with it
        """
        self.device_info: bytes = device_info
        self.fingerprint: bytes = fingerprint
        self.exbadbasket: bytes = exbadbasket
        self.App_key = b"Ezlc3tgtl"

    def gen(self) -> bytes:
        mac = hmac.new(self.App_key, digestmod=hashlib.sha256)
        mac.update(self.device_info)
        mac.update(b"x-exbadbasket")
        mac.update(self.exbadbasket)
        mac.update(b"x-fingerprint")
        mac.update(self.fingerprint)
        return mac.digest()


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


def make_base_metadata(
        access_key,
        brand='Xiaomi',
        Dalvik="Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1)",
        version_name="7.63.0",
        build=7630200,
        channel='bili',
        proxy=None
) -> dict:
    """
    不带bili-ticket的基础metadata
    :param access_key:
    :param brand:
    :param Dalvik:
    :param version_name:
    :param build:
    :param channel:
    :param proxy:
    :return:
    """
    mid = 0
    metaDataNeedInfo = MetaDataNeedInfo()
    metaDataNeedInfo.generate_ua_from_Dalvik_appVer(Dalvik, version_name, build, channel, brand)
    BUVID = fake_buvid()
    device_model = metaDataNeedInfo.device_model
    fp_generator = Fp(BUVID, device_model, "")
    gen_ts = int(time.time() - random.randint(0, 15 * 3600 * 24))
    fp = fp_generator.gen(gen_ts)
    device_params = {
        "app_id": 1,
        "build": metaDataNeedInfo.build,
        "buvid": BUVID,
        "mobi_app": "android",
        "platform": "android",
        "channel": metaDataNeedInfo.channel,
        "brand": metaDataNeedInfo.brand,
        "model": device_model,
        "device": "phone",
        "osver": metaDataNeedInfo.osver,
        "fp_local": fp_generator.gen(gen_ts + random.randint(10, 60)),
        "fp_remote": fp,
        "version_name": metaDataNeedInfo.version_name,
        "fp": fp,
        "fts": gen_ts
    }

    device_info_bytes = Device(**device_params).SerializeToString()
    metadata_params = {
        "mobi_app": "android",
        "build": metaDataNeedInfo.build,
        "channel": metaDataNeedInfo.channel,
        "buvid": BUVID,
        "platform": "android"
    }
    metadata = {
        "accept-encoding": "identity",
        "grpc-accept-encoding": "identity, gzip",
        "env": "prod",
        "app-key": "android64",
        "env": "prod",
        "app-key": "android64",
        'user-agent': metaDataNeedInfo.ua,
        "x-bili-trace-id": gen_trace_id(),
        "x-bili-aurora-eid": "",
        "x-bili-mid": str(mid) if mid else "",
        "x-bili-aurora-zone": "",
        "x-bili-gaia-vtoken": "",
        'x-bili-ticket': '',
        "x-bili-metadata-bin": Metadata(**metadata_params).SerializeToString(),
        "x-bili-device-bin": device_info_bytes,
        "x-bili-network-bin": Network(type=NetworkType.WIFI, oid=random.choice(['46000',
                                                                                '46001',
                                                                                '46002',
                                                                                '46003',
                                                                                '46601',
                                                                                '46606',
                                                                                '46668',
                                                                                '46688'
                                                                                ])).SerializeToString(),
        "x-bili-restriction-bin": Restriction(
            # teenagers_mode=False, lessons_mode=False, mode=ModeType.NORMAL, review=True, disable_rcmd=False
        ).SerializeToString(),
        "x-bili-local-bin": Locale(
            c_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
            s_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
        ).SerializeToString(),
        "x-bili-exps-bin": Exps().SerializeToString(),
        "buvid": BUVID,
        "x-bili-fawkes-request-bin": FawkesReq(
            appkey="android64", env="prod", session_id=random_id()
        ).SerializeToString(),
        'content-type': "application/grpc"
        # "x-bili-ticket":gen_random_x_bili_ticket(BUVID), # ticket没有搞明白怎么获取，应该是发一个请求，然后将这个请求的string作为参数，不变
    }

    if access_key:
        metadata["authorization"] = f"identify_v1 {access_key}"
        metadata["x-bili-aurora-eid"] = gen_aurora_eid(mid)
    return metadata


async def make_metadata(
        access_key,
        brand='Xiaomi',
        Dalvik="Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1)",
        version_name="7.63.0",
        build=7630200,
        channel='bili',
        proxy=None
) -> tuple:
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
    gen_ts = int(time.time() - random.randint(0, 15 * 3600 * 24))
    fp = fp_generator.gen(gen_ts)
    device_params = {
        "app_id": 1,
        "build": metaDataNeedInfo.build,
        "buvid": BUVID,
        "mobi_app": "android",
        "platform": "android",
        "channel": metaDataNeedInfo.channel,
        "brand": metaDataNeedInfo.brand,
        "model": device_model,
        "device": "phone",
        "osver": metaDataNeedInfo.osver,
        "fp_local": fp_generator.gen(gen_ts + random.randint(10, 60)),
        "fp_remote": fp,
        "version_name": metaDataNeedInfo.version_name,
        "fp": fp,
        "fts": gen_ts
    }

    device_info_bytes = Device(**device_params).SerializeToString()
    metadata_params = {
        "mobi_app": "android",
        "build": metaDataNeedInfo.build,
        "channel": metaDataNeedInfo.channel,
        "buvid": BUVID,
        "platform": "android"
    }
    metadata = {
        "accept-encoding": "identity",
        "grpc-accept-encoding": "identity, gzip",
        "env": "prod",
        "app-key": "android64",
        "env": "prod",
        "app-key": "android64",
        'user-agent': metaDataNeedInfo.ua,
        "x-bili-trace-id": gen_trace_id(),
        "x-bili-aurora-eid": "",
        "x-bili-mid": str(mid) if mid else "",
        "x-bili-aurora-zone": "",
        "x-bili-gaia-vtoken": "",
        'x-bili-ticket': '',
        "x-bili-metadata-bin": Metadata(**metadata_params).SerializeToString(),
        "x-bili-device-bin": device_info_bytes,
        "x-bili-network-bin": Network(type=NetworkType.WIFI, oid=random.choice(['46000',
                                                                                '46001',
                                                                                '46002',
                                                                                '46003',
                                                                                '46601',
                                                                                '46606',
                                                                                '46668',
                                                                                '46688'
                                                                                ])).SerializeToString(),
        "x-bili-restriction-bin": Restriction(
            # teenagers_mode=False, lessons_mode=False, mode=ModeType.NORMAL, review=True, disable_rcmd=False
        ).SerializeToString(),
        "x-bili-local-bin": Locale(
            c_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
            s_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
        ).SerializeToString(),
        "x-bili-exps-bin": Exps().SerializeToString(),
        "buvid": BUVID,
        "x-bili-fawkes-request-bin": FawkesReq(
            appkey="android64", env="prod", session_id=random_id()
        ).SerializeToString(),
        'content-type': "application/grpc"
        # "x-bili-ticket":gen_random_x_bili_ticket(BUVID), # ticket没有搞明白怎么获取，应该是发一个请求，然后将这个请求的string作为参数，不变
    }
    bili_ticket = await get_bili_ticket(
        device_info=device_info_bytes,
        app_version=metaDataNeedInfo.version_name,
        app_version_code=str(metaDataNeedInfo.build),
        chid=metaDataNeedInfo.channel,
        osver=metaDataNeedInfo.osver,
        model=metaDataNeedInfo.device_model,
        brand=metaDataNeedInfo.brand,
        md=tuple(metadata.items()),
        proxy=proxy
    )
    if bili_ticket:
        metadata['x-bili-ticket'] = bili_ticket
    if access_key:
        metadata["authorization"] = f"identify_v1 {access_key}"
        metadata["x-bili-aurora-eid"] = gen_aurora_eid(mid)
    return tuple(metadata.items())


def is_useable_Dalvik(Dalvik: str):
    '''
    检查Dalvik是否可用
    :param Dalvik:
    :return:
    '''
    device_model = ''.join(re.findall('Android.*?\d+; (.*?) (?:Build|MIUI)', Dalvik))
    osver = ''.join(re.findall('Android (.*?[\w]);', Dalvik))
    if device_model and osver:
        return True
    else:
        return False


async def get_bili_ticket(device_info: bytes,
                          app_version: str,
                          app_version_code: str,
                          chid: str,
                          osver: str,
                          model: str,
                          brand: str,
                          md,
                          proxy=None
                          ):
    x_fingerprint = android_device_info_pb2.AndroidDeviceInfo(
        sdkver='0.2.4',
        app_id='1',
        app_version=app_version,
        app_version_code=app_version_code,
        chid=chid,
        fts=1712822061,
        # buvid_local='b2cdb0059fb390966b4431ff9f90433d2024041115542486b4448a7cffdabe3b',
        proc='tv.danmaku.bili',
        osver=osver,
        t=int(time.time() * 1000),
        cpu_count=8,
        model=model,
        brand=brand,
        screen='1440,3200,480',
        boot=4740001,
        emu='000',
        oid='46007',
        network='WIFI',
        mem=random.randint(10 ** 10, 10 ** 12),
        sensor='[]',
        cpu_freq=random.randint(10 ** 6, 10 ** 8),
        cpu_vendor='Qualcomm',
        sim='1',
        brightness=102,
        props={
            'net.hostname': '',
            'ro.boot.hardware': 'qcom',
            'gsm.sim.state': 'LOADED',
            'ro.build.date.utc': f'{int(time.time())}',
            'ro.product.device': 'star2qltechn',
            'persist.sys.language': 'en',
            'ro.debuggable': '1',
            'net.gprs.local-ip': '',
            'ro.build.tags': 'release-keys',
            'http.proxy': '',
            'ro.serialno': '00536fe6',
            'persist.sys.country': 'JP',
            'ro.boot.serialno': '00536fe6',
            'gsm.network.type': "LTE",
            'net.eth0.gw': '',
            'net.dns1': '192.168.0.1',
            'sys.usb.state': '',
            'http.agent': ''
        },
        sys={
            'product': model,
            'cpu_model_name': 'Qualcomm Technologies, Inc MSM8998',
            'display': 'PQ3B.190801.03191204 release-keys',
            'cpu_abi_list': 'arm64-v8a,armeabi-v7a',
            'cpu_abi_libc': 'ARM',
            'manufacturer': 'Xiaomi',
            'cpu_hardware': 'Qualcomm Technologies, Inc MSM8998',
            'cpu_processor': 'AArch64 Processor rev 256 (aarch64)',
            'cpu_abi_libc64': 'ARM64-V8A',
            'cpu_abi': 'arm64-v8a',
            'serial': 'unknown',
            'cpu_features': 'fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics',
            'fingerprint': 'samsung/star2qltezh/star2qltechn:9/PQ3B.190801.03191204/G9650ZHU2ARC6:user/release-keys',
            'device': 'star2qltechn',
            'hardware': 'qcom'
        },
        adid=hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
        os='android',
        total_space=random.randint(10 ** 8, 10 ** 10),
        axposed='false',
        files='/data/user/0/tv.danmaku.bili/files',
        virtual='0',
        virtualproc='[]',
        apps='[]',
        uid=str(random.randint(10 ** 3, 10 ** 5)),
        androidapp20='[]',
        androidsysapp20='[]',
        battery=100,
        battery_state='BATTERY_STATUS_CHARGING',
        build_id='PQ3B.190801.03191204 release-keys',
        country_iso='JP',
        free_memory=random.randint(10 ** 8, 10 ** 10),
        fstorage=f'{random.randint(10 ** 8, 10 ** 10)}',
        kernel_version='4.4.146',
        languages='en',
        systemvolume=5,
        memory=random.randint(10 ** 8, 10 ** 10),
        str_battery='100',
        str_brightness='102',
        str_app_id='1',
        light_intensity='301.514',
        gps_sensor=1,
        speed_sensor=1,
        linear_speed_sensor=1,
        gyroscope_sensor=1,
        biometric=1,
        biometrics=['touchid'],
        ui_version='pq3b.190801.03191204 release-keys',
        sensors_info=[],
        battery_present=1,
        battery_technology='Li-ion',
        battery_temperature=322,
        battery_voltage=random.choice(
            [3000, 3150, 3250, 3450, 3550, 3650, 3750, 3850, 3950, 4050, 4150, 4250, 4350, 4450, 4650, 4550, 4660,
             5000]),
        battery_plugged=1,
        battery_health=2,
    )

    sign = gen_x_bili_ticket(
        device_info=device_info,
        fingerprint=x_fingerprint.SerializeToString(),
        exbadbasket=b''
    ).gen()
    reqdata = ticket_pb2.GetTicketRequest(
        context={
            'x-fingerprint': x_fingerprint.SerializeToString(),
            'x-exbadbasket': b''
        },
        key_id='ec01',
        sign=sign,
    )
    headers = {
        "Content-Type": "application/grpc",
        # 'Connection': 'close',
        # "User-Agent": ua,
        # 'User-Agent': random.choice(CONFIG.UA_LIST),
    }
    headers.update(md)
    headers_copy = copy.deepcopy(headers)
    for k, v in list(headers_copy.items()):
        if k.endswith('-bin'):
            if isinstance(v, bytes):
                headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
    proto = reqdata.SerializeToString()
    data = b"\0" + len(proto).to_bytes(4, "big") + proto
    try:
        resp = await myreq.post(url='https://app.bilibili.com/bilibili.api.ticket.v1.Ticket/GetTicket',data=data, headers=headers, proxies = {
            'http': proxy['proxy']['http'],
            'https': proxy['proxy']['https']}if proxy else None, verify=False
                   )
        gresp = ticket_pb2.GetTicketResponse()
        gresp.ParseFromString(resp.content[5:])
        return gresp.ticket
    except Exception as e:
        logger.error(f'使用代理 {proxy} 获取bili_ticket失败！\t{e}')
