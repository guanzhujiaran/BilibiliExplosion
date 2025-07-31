# -*- coding: utf-8 -*-
import asyncio
import base64
import gzip
import hashlib
import hmac
import json
import random
import re
import string
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from CONFIG import CONFIG
from fastapi接口.log.base_log import BiliGrpcApi_logger
from fastapi接口.service.grpc_module.Models.GrpcApiBaseModel import MetaDataBasicInfo
from fastapi接口.service.grpc_module.Utils.CONST import MemSizes, CPUFreqs, ProductDevices, Languages, Countries, \
    NetworkTypes, UsbStates, \
    CPUAbiLists, CPUHardwares, ANDROID_VERSIONS, BatteryStates, ANDROID_KERNELS, ScreenDPIs
from fastapi接口.service.grpc_module.grpc.bapi.Utils import appsign
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.api.ticket.v1.ticket_pb2 import GetTicketResponse, \
    GetTicketRequest
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.device.device_pb2 import Device
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.locale.locale_pb2 import Locale, LocaleIds
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.metadata_pb2 import Metadata
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.network.network_pb2 import Network, NetworkType
from fastapi接口.service.grpc_module.grpc.grpc_proto.bilibili.metadata.restriction.restriction_pb2 import Restriction
from fastapi接口.service.grpc_module.grpc.grpc_proto.datacenter.hakase.protobuf.android_device_info_pb2 import \
    AndroidDeviceInfo
from utl.代理.SealedRequests import my_async_httpx as myreq


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
    trace_id_uid = str(uuid.uuid4()).replace("-", "")[0:26].lower()
    trace_id_hex = hex(int(round(time.time()) / 256)).lower().replace("0x", "")
    trace_id = trace_id_uid + trace_id_hex + ":" + trace_id_uid[-10:] + trace_id_hex + ":0:0"
    return trace_id


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
            BiliGrpcApi_logger.error('解析Dalvik失败！')
            BiliGrpcApi_logger.error(f'{Dalvik}\n{build, device_model, osver, version_name, brand, channel}')
        self.ua = (f'grpc-c++/1.66.2 {Dalvik} '
                   f'{self.version_name} '
                   f'os/android '
                   f'model/{self.device_model} '
                   f'mobi_app/android '
                   f'build/{self.build} '
                   f'channel/{self.channel} '
                   f'innerVer/{self.build} '
                   f'osVer/{self.osver} '
                   f'network/2 '
                   f'grpc-java-ignet/1.36.1 '
                   f'grpc-c/43.0.0 '
                   f'(android; ignet_http)')

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
            BiliGrpcApi_logger.error('解析ua失败！')
            BiliGrpcApi_logger.error(f'{build, device_model, osver, version_name, brand, channel}')


async def make_metadata(
        access_key,
        brand='Xiaomi',
        Dalvik="Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1)",
        version_name="8.12.0",
        build=81200100,
        channel='bili',
        proxy=None,
        mid=0
) -> tuple[tuple, GetTicketResponse | None, MetaDataBasicInfo]:
    '''
    根据ua自动生成包含ua信息的MetaData
    :param mid:
    :param brand:
    :param Dalvik:
    :param version_name:
    :param build:
    :param channel:
    :param access_key:
    :param proxy:
    :return:
    '''
    proxy = {'proxy':
        {
            'http': CONFIG.my_ipv6_addr,
            'https': CONFIG.my_ipv6_addr
        }
    }
    metaDataNeedInfo = MetaDataNeedInfo()
    metaDataNeedInfo.generate_ua_from_Dalvik_appVer(Dalvik, version_name, build, channel, brand)
    BUVID = fake_buvid()
    device_model = metaDataNeedInfo.device_model
    fp_generator = Fp(BUVID, device_model, "")
    gen_ts = int(time.time()) - random.randint(600, 60000)
    fp_remote = fp_generator.gen(gen_ts)
    fp_local = fp_generator.gen(gen_ts - random.randint(1000, 60000))
    device_params = {
        "app_id": 1,
        "build": metaDataNeedInfo.build,
        "buvid": BUVID,
        "mobi_app": "android",
        "platform": "android",
        "channel": metaDataNeedInfo.channel,
        "brand": metaDataNeedInfo.brand,
        "model": device_model,
        "osver": metaDataNeedInfo.osver,
        "fp_local": fp_remote,  # 三个保持一致
        "fp_remote": fp_remote,
        "version_name": metaDataNeedInfo.version_name,
        "fp": fp_remote,
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
    metadata: tuple = (
        ("accept", "*/*"),
        ("accept-encoding", "gzip, deflate, br"),
        ("bili-http-engine", "ignet"),
        ("buvid", BUVID),
        ("content-type", "application/grpc"),
        ("grpc-accept-encoding", "identity, deflate, gzip"),
        ("grpc-encoding", "gzip"),
        ("grpc-timeout", "18S"),
        ("ignet_grpc_annotation_id", f"{random.choice(range(1, 200))}"),
        ("te", "trailers"),
        ("user-agent", metaDataNeedInfo.ua),
        ('x-bili-aurora-eid', ''),
        ("x-bili-device-bin", device_info_bytes),
        ("x-bili-fawkes-req-bin", FawkesReq(
            appkey="android64", env="prod", session_id=random_id()
        ).SerializeToString()),
        ("x-bili-locale-bin", Locale(
            c_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
            s_locale=LocaleIds(
                language='zh',
                region='CN'
            ),
        ).SerializeToString()),
        ("x-bili-metadata-bin", Metadata(**metadata_params).SerializeToString()),
        ("x-bili-metadata-ip-region", "CN"),
        ("x-bili-metadata-legal-region", "CN"),
        ("x-bili-network-bin", Network(type=NetworkType.WIFI, oid=random.choice(['46000',
                                                                                 '46002',
                                                                                 '46007',
                                                                                 '46008'
                                                                                 ])).SerializeToString()),
        ("x-bili-restriction-bin", Restriction(unknown1=16).SerializeToString()),
        ('x-bili-ticket', ""),
        ("x-bili-trace-id", gen_trace_id())
    )
    try:
        await active_buvid(
            brand=brand,
            build=16180799,
            buvid=BUVID,
            channel=channel,
            app_version_build=metaDataNeedInfo.build,
            app_version_name=metaDataNeedInfo.version_name,
            model=metaDataNeedInfo.device_model,
            ua=metaDataNeedInfo.ua,
            proxy=proxy
        )
    except Exception as e:
        pass
    finally:
        pass
    bili_ticket_resp = await get_bili_ticket(
        device_info=device_info_bytes,
        app_version=metaDataNeedInfo.version_name,
        app_version_code=str(metaDataNeedInfo.build),
        chid=metaDataNeedInfo.channel,
        osver=metaDataNeedInfo.osver,
        model=metaDataNeedInfo.device_model,
        brand=metaDataNeedInfo.brand,
        fp_local=fp_local,
        md=metadata,
    )
    if bili_ticket_resp:
        new_metadata = []
        for k, v in metadata:
            if k == 'x-bili-ticket':
                new_metadata.append((k, bili_ticket_resp.ticket))
                continue
            new_metadata.append((k, v))
        metadata = tuple(new_metadata)
    if access_key:
        metadata.__add__(("authorization", f"identify_v1 {access_key}"))

    metadata_basic_info = MetaDataBasicInfo(
        buvid=BUVID,
        fp_local=fp_local,
        fp_remote=fp_remote,
        guestid=random.randint(1000000000000, 9999999999999),
        app_version_name=version_name,
        model=device_model,
        app_build=build,
        channel=channel,
        osver=metaDataNeedInfo.osver,
        ticket=bili_ticket_resp.ticket if bili_ticket_resp else "",
        brand=brand
    )
    return metadata, bili_ticket_resp, metadata_basic_info


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


def generate_app_info(android_version: str, is_sys_app: bool = True, app_ver_name: str = '8.15.0') -> str:
    sdk_ver = ANDROID_VERSIONS.get(android_version, )
    if is_sys_app:
        apps = ["com.android.settings", "com.android.phone", "com.android.contacts", "com.android.messaging",
                "com.android.documentsui", "com.android.dreams.phototable", "com.android.calendar",
                "com.android.browser",
                "com.android.gallery", "com.android.music", "com.android.launcher", "com.android.camera"]
        data_list = []
    else:
        apps = [
            "com.android.chrome",
            "com.android.contacts",
            "com.android.dialer",
            "com.android.gallery",
            "com.android.messaging",
            "com.android.settings",
            "com.android.calendar",
            "com.android.calculator2",
            "com.android.music",
            "com.facebook.katana",
            "com.instagram.android",
            "com.snapchat.android",
            "com.twitter.android",
            "com.linkedin.android",
            "com.tinder",
            "com.spotify.music",
            "com.netflix.mediaclient",
            "com.hulu.plus",
            "com.amazon.mShop.android.shopping",
            "com.ebay.mobile",
            "com.walmart.android",
            "com.target",
            "com.kroger.mobile",
            "com.alibaba.aliexpresshd",
            "com.booking",
            "com.airbnb",
            "com.expedia",
            "com.tripadvisor",
            "com.yelp.android",
            "com.zomato",
            "com.ubereats",
            "com.doordash",
            "com.postmates",
            "com.swiggy",
            "com.dunzo",
            "com.fitbit.FitbitMobile",
            "com.strava",
            "com.myfitnesspal.android",
            "com.headspace",
            "com.calm.android",
            "com.duolingo",
            "com.memrise",
            "com.babbel.mobile",
            "com.khanacademy.android",
            "com.coursera",
            "com.edx.mobile",
            "com.udemy",
            "com.quora",
            "com.reddit",
            "com.stackoverflow",
            "com.discord",
            "com.zoom.us",
            "com.microsoft.teams",
            "com.skype",
            "com.googleclassroom",
            "com.schoology",
            "com.blackboard",
            "com.canva",
            "com.adobe.psmobile",
            "com.pinterest",
            "com.etsy.android",
            "com.zillow",
            "com.trulia",
            "com.realtor.com",
            "com.indeed.android.jobsearch",
            "com.linkedin.jobs",
            "com.glassdoor",
            "com.monster.android",
            "com.simplyhired",
            "com.trello",
            "com.asana",
            "com.jira.mobile",
            "com.evernote",
            "com.microsoft.onenote",
            "com.dropbox.android",
            "com.box.android",
            "com.google.docs",
            "com.google.sheets",
            "com.google.slides",
            "com.microsoft.word",
            "com.microsoft.excel",
            "com.microsoft.powerpoint",
            "com.adobe.acrobat.reader",
            "com.kindle",
            "com.nook.android",
            "com.scribd",
            "com.pandora.android",
            "com.spotify.music",
            "com.apple.music",
            "com.tidal",
            "com.deezer",
            "com.soundcloud",
            "com.shazam",
            "com.spotify.tuner",
            "com.netflix.mediaclient",
            "com.hulu.plus",
            "com.amazon.avod.thirdpartyclient",
            "com.hbo.max",
            "com.disneyplus",
            "com.paramountplus",
            "com.peacocktv",
            "com.appletv.app",
            "com.fandango",
            "com.movietickets",
            "com.atomtickets",
            "com.stubhub",
            "com.eventbrite",
            "com.meetup",
            "com.ticketmaster",
            "com.lyft",
            "com.taxify",
            "com.ola.cabs",
            "com.uber",
            "com.didi",
            "com.grab",
            "com.gojek",
            "com.bolt",
            "com.inshorts",
            "com.flipboard.android",
            "com.pulse",
            "com.news360",
            "com.feedly",
            "com.smule",
            "com.yokee",
            "com.singplay",
            "com.soundhound",
            "com.shazam.en",
            "com.spotify.tuner.en",
            "com.netflix.mediaclient.en",
            "com.hulu.plus.en",
            "com.amazon.avod.thirdpartyclient.en",
            "com.hbo.max.en",
            "com.disneyplus.en",
            "com.paramountplus.en",
            "com.peacocktv.en",
            "com.appletv.app.en",
            "com.fandango.en",
            "com.movietickets.en",
            "com.atomtickets.en",
            "com.stubhub.en",
            "com.eventbrite.en",
            "com.meetup.en",
            "com.ticketmaster.en"
        ]
        random_time_delta = random.randint(1000000000, 5000000000)
        timestamp = int(time.time() * 1000) - random_time_delta
        data_list = [
            f"{timestamp},tv.danmaku.bili,{1 if is_sys_app else app_ver_name},{android_version},{sdk_ver},{timestamp}"]

    max_data_len = 20 if is_sys_app else random.choice(
        [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
    while len(data_list) < max_data_len:
        random_app = random.choice(apps)
        existing_data_with_app = [data for data in data_list if random_app in data]
        if existing_data_with_app:
            generated_data = existing_data_with_app[0]
        else:
            # 生成几个月或者几年前的时间戳
            random_time_delta = random.randint(1000000000, 5000000000)
            timestamp = int(time.time() * 1000) - random_time_delta
            generated_data = f"{timestamp},{random_app},{1 if is_sys_app else app_ver_name},{android_version},{sdk_ver},{timestamp}"
        data_list.append(generated_data)
    return json.dumps(data_list, separators=(',', ' '))


async def get_bili_ticket(device_info: bytes,
                          app_version: str,
                          app_version_code: str,
                          chid: str,
                          osver: str,
                          model: str,
                          brand: str,
                          fp_local: str,
                          md,
                          proxy=None
                          ) -> GetTicketResponse | None:
    android_build_id_moc = f"{''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))}.{(datetime.now() - timedelta(days=random.randint(365, 365 * 5))).strftime('%y%m%d')}.{str(random.randint(10000000, 99999999))}"
    rand_memory = MemSizes[random.choice(list(MemSizes.keys()))]
    rand_boot_id = random.randint(100000, 948576)
    rand_cpu_freq = CPUFreqs[random.choice(list(CPUFreqs.keys()))]
    rand_brightness = random.randint(30, 255)
    rand_ro_build_date_utc = int((datetime.now() - timedelta(days=random.randint(int(0.3 * 365), 5 * 365))).timestamp())
    rand_ro_product_device = random.choice(ProductDevices)
    rand_persist_sys_language = random.choice(Languages)
    rand_serial_no = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    rand_country = random.choice(Countries)
    rand_network_type = random.choice(NetworkTypes)
    rand_usb_state = random.choice(UsbStates)
    rand_cpu_abi_list = random.choice(CPUAbiLists)
    rand_cpu_headrware = random.choice(CPUHardwares)
    sys_apps = generate_app_info(osver, is_sys_app=True)
    android_apps = generate_app_info(osver, is_sys_app=False, app_ver_name=app_version)
    rand_battery_state = random.choice(BatteryStates)
    rand_kernel = random.choice(ANDROID_KERNELS.get(
        random.choice(list(ANDROID_KERNELS.keys())),
        ["4.4.146"]
    ))
    rand_battery = random.randint(30, 100)
    rand_screen = random.choice(ScreenDPIs)
    rand_light_intensity = str(round(random.uniform(50.0, 600.0), 3))
    x_fingerprint = AndroidDeviceInfo()
    x_fingerprint.sdkver = '0.2.4'
    x_fingerprint.app_id = '1'
    x_fingerprint.app_version = app_version
    x_fingerprint.app_version_code = app_version_code
    x_fingerprint.chid = chid
    x_fingerprint.fts = 1712822061
    x_fingerprint.buvid_local = fp_local
    x_fingerprint.proc = 'tv.danmaku.bili'
    x_fingerprint.osver = osver
    x_fingerprint.t = int(time.time() * 1000)
    x_fingerprint.cpu_count = random.choice([4, 6, 8, 10, 12])
    x_fingerprint.model = model
    x_fingerprint.brand = brand
    x_fingerprint.screen = rand_screen
    x_fingerprint.boot = rand_boot_id
    x_fingerprint.emu = random.choice(['000', '001', '010', '011', '100', '101', '110', '111'])
    x_fingerprint.oid = random.choice(['46000',
                                       '46002',
                                       '46007',
                                       '46008'
                                       ])
    x_fingerprint.network = 'WIFI'
    x_fingerprint.mem = rand_memory
    x_fingerprint.sensor = '["LSM330 Accelerometer,STMicroelectronics", "Linear Acceleration,QTI", "Magnetometer,AKM", "Orientation,Yamaha", "Gravity,QTI", "Gyroscope,STMicroelectronics", "Proximity sensor,AMS TAOS", "Light sensor,AMS TAOS", "Game Rotation Vector Sensor,AOSP", "GeoMag Rotation Vector Sensor,AOSP", "Rotation Vector Sensor,AOSP", "Orientation Sensor,AOSP"]'
    x_fingerprint.cpu_freq = rand_cpu_freq
    x_fingerprint.cpu_vendor = 'ARM'
    x_fingerprint.brightness = rand_brightness
    x_fingerprint.props.update({
        'net.hostname': '',
        'ro.boot.hardware': 'qcom',
        'gsm.sim.state': 'LOADED',
        'ro.build.date.utc': f'{rand_ro_build_date_utc}',
        'ro.product.device': rand_ro_product_device,
        'persist.sys.language': rand_persist_sys_language,
        'ro.debuggable': '1',
        'net.gprs.local-ip': '',
        'ro.build.tags': 'release-keys',
        'http.proxy': '',
        'ro.serialno': rand_serial_no,
        'persist.sys.country': rand_country,
        'ro.boot.serialno': rand_serial_no,
        'gsm.network.type': rand_network_type,
        'net.eth0.gw': '',
        'net.dns1': f'192.168.{random.randint(0, 255)}.{random.randint(0, 255)}',
        'sys.usb.state': rand_usb_state,
        'http.agent': '',
        'product': model,
        'cpu_model_name': '',
        'display': f'{android_build_id_moc} release-keys',
        'cpu_abi_list': rand_cpu_abi_list,
        'cpu_abi_libc': 'X86_64',
        'manufacturer': brand,
        'cpu_hardware': rand_cpu_headrware,
        'cpu_processor': 'AArch64 Processor rev 12 (aarch64)',
        'cpu_abi_libc64': 'arm64-v8a',
        'cpu_abi': 'arm64-v8a',
        'serial': 'unknown',
        'cpu_features': 'fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp',
        'fingerprint': f'{brand}/{model}/{rand_ro_product_device}:{osver}/{android_build_id_moc}/{random.randint(100000, 9999999999)}:user/release-keys',
        'cpu_abi2': '',
        'device': rand_ro_product_device,
        'hardware': 'qcom'
    })
    x_fingerprint.adid = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
    x_fingerprint.os = 'android'
    x_fingerprint.total_space = random.randint(10 ** 8, 10 ** 10)
    x_fingerprint.axposed = 'false'
    x_fingerprint.files = '/data/user/0/tv.danmaku.bili/files'
    x_fingerprint.virtual = '0'
    x_fingerprint.virtualproc = '[]'
    x_fingerprint.apps = sys_apps
    x_fingerprint.guid = str(uuid.uuid4())
    x_fingerprint.uid = str(random.randint(10000, 10053))
    x_fingerprint.root = 0
    x_fingerprint.androidapp20 = android_apps
    x_fingerprint.androidappcnt = random.randint(20, 70)
    x_fingerprint.androidsysapp20 = sys_apps
    x_fingerprint.battery = rand_battery  # 63
    x_fingerprint.battery_state = rand_battery_state  # 64
    x_fingerprint.build_id = f'{android_build_id_moc} release-keys'  # 67
    x_fingerprint.country_iso = rand_country  # 68
    x_fingerprint.free_memory = random.randint(10 ** 8, 10 ** 10)  # 70
    x_fingerprint.fstorage = f'{random.randint(10 ** 8, 10 ** 10)}'  # 71
    x_fingerprint.kernel_version = rand_kernel  # 74
    x_fingerprint.languages = rand_persist_sys_language  # 75
    x_fingerprint.systemvolume = random.choice([0, 1, 2, 3, 4, 5, 6, 7])  # 80
    x_fingerprint.memory = rand_memory  # 82
    x_fingerprint.str_battery = str(rand_battery)  # 83
    x_fingerprint.is_root = False  # 84
    x_fingerprint.str_brightness = str(rand_brightness)  # 85
    x_fingerprint.str_app_id = '1'  # 86
    x_fingerprint.light_intensity = rand_light_intensity  # 89
    x_fingerprint.device_angle.extend([round(random.uniform(-180.0, 180.0), 3) for _ in range(3)])  # 90
    x_fingerprint.gps_sensor = 1  # 91
    x_fingerprint.speed_sensor = 1  # 92
    x_fingerprint.linear_speed_sensor = 1  # 93
    x_fingerprint.gyroscope_sensor = 1  # 94
    x_fingerprint.biometric = 1  # 95
    x_fingerprint.biometrics.extend(['touchid']),  # 96
    x_fingerprint.last_dump_ts = int(time.time() * 1000) - random.randint(3 * 3600 * 1000, 5000000000)  #
    x_fingerprint.ui_version = f'{android_build_id_moc} release-keys'  # 108
    x_fingerprint.sensors_info.extend([])  # 110
    x_fingerprint.battery_present = True  # 112
    x_fingerprint.battery_technology = 'Li-ion'  # 113
    x_fingerprint.battery_temperature = random.choice([322, 323, 324, 325, 326, 327, 328, 329, 330])  # 114
    x_fingerprint.battery_voltage = random.choice(
        [3000, 3150, 3250, 3450, 3550, 3650, 3750, 3850, 3950, 4050, 4150, 4250, 4350, 4450, 4650, 4550, 4660,
         5000])  # 115
    x_fingerprint.battery_plugged = 1  # 116
    x_fingerprint.battery_health = 2  # 117
    x_fingerprint.adb_info = json.dumps({
        "ro.product.model": model,
        "ro.bootmode": "unknown",
        "qemu.sf.lcd_density": "",
        "qemu.hw.mainkeys": "",
        "init.svc.qemu-props": "",
        "ro.hardware": "qcom",
        "ro.product.device": rand_ro_product_device,
        "init.svc.qemud": "",
        "ro.kernel.android.qemud": "",
        "ro.kernel.qemu.gles": "",
        "ro.serialno": rand_serial_no,
        "ro.kernel.qemu": "",
        "ro.product.name": model,
        "qemu.sf.fake_camera": "",
        "ro.bootloader": "unknown"
    })

    sign = gen_x_bili_ticket(
        device_info=device_info,
        fingerprint=x_fingerprint.SerializeToString(),
        exbadbasket=b''
    ).gen()
    reqdata = GetTicketRequest(
        context={
            'x-fingerprint': x_fingerprint.SerializeToString(),
            'x-exbadbasket': b''
        },
        key_id='ec01',
        sign=sign,
    )
    new_headers = []
    for k, v in md:
        if isinstance(v, bytes):
            new_headers.append((k, base64.b64encode(v).decode('utf-8').strip('=')))
            continue
        if k == 'x-bili-trace-id':
            new_headers.append((k, gen_trace_id()))
            continue
        new_headers.append((k, v))
    proto_bytes = reqdata.SerializeToString()
    compressed_proto_bytes = gzip.compress(proto_bytes, compresslevel=6)
    data = b"\01" + len(compressed_proto_bytes).to_bytes(4, "big") + compressed_proto_bytes
    proxy = CONFIG.custom_proxy
    while 1:
        try:
            resp = await myreq.request(
                url='https://app.bilibili.com/bilibili.api.ticket.v1.Ticket/GetTicket',
                method='POST',
                data=data,
                headers=tuple(new_headers),
                proxies=proxy,
                verify=False
            )
            gresp = GetTicketResponse()
            if 'gzip' in dict(new_headers).get('grpc-encoding'):
                gresp.ParseFromString(gzip.decompress(resp.content[5:]))
            else:
                gresp.ParseFromString(resp.content[5:])
            if not gresp.ticket:
                BiliGrpcApi_logger.error(f'获取ticket失败！\n{resp.content}\n{resp.headers}')
            return gresp
        except Exception as e:
            BiliGrpcApi_logger.error(f'获取bili_ticket失败！\n{type(e)}\t{e}')
            if not proxy:
                proxy = CONFIG.custom_proxy
            else:
                proxy = None


async def active_buvid(brand, build, buvid, channel, app_version_build, app_version_name, model, ua, proxy):
    """
    激活buvid???? 顺序在 get_bili_ticket 之前
    :return:
    """
    url = 'https://app.bilibili.com/x/polymer/buvid/get'
    data = {
        "androidId": ''.join([random.choice(string.ascii_lowercase + string.digits) for x in range(16)]),
        "brand": brand,
        "build": build,
        "buvid": buvid,
        "channel": channel,
        "drmId": "",
        "fawkesAppKey": "android",
        "first": 1,
        "firstStart": 1,
        "imei": "",
        "internalVersionCode": app_version_build,
        "mac": ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)]),
        "model": model,
        "neuronAppId": 1,
        "neuronPlatformId": 3,
        "oaid": "",
        "versionCode": app_version_build,
        "versionName": app_version_name
    }
    signed_data = appsign(data)
    headers = (
        ('env', 'prod'),
        ('app-key', 'android'),
        ('env', 'prod'),
        ('app-key', 'android'),
        ('user-agent', ua),
        ('x-bili-trace-id', gen_trace_id()),
        ('x-bili-aurora-eid', ''),
        ('x-bili-mid', ''),
        ('x-bili-aurora-zone', ''),
        ('x-bili-gaia-vtoken', ''),
        ('x-bili-ticket', ''),
        ('content-type', 'application/x-www-form-urlencoded; charset=utf-8'),
    )

    req = await myreq.request(url=url, method='post', data=signed_data, headers=headers, proxies={
        'http': proxy['proxy']['http'],
        'https': proxy['proxy']['https']} if proxy else CONFIG.custom_proxy, verify=False)
    BiliGrpcApi_logger.debug(f' {url} 激活buvid：{req.text}')


if __name__ == '__main__':
    __ = asyncio.run(make_metadata(""))
    print(__)
