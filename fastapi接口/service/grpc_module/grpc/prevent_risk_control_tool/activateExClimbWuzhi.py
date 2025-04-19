import hashlib
import hmac
import base64
import io
import json
import string
import struct
from dataclasses import dataclass
from typing import Optional, Literal
from urllib.parse import quote
import CONFIG
from fastapi接口.log.base_log import activeExclimbWuzhi_logger
from utl.加密 import utils
import random
import time
from utl.代理.SealedRequests import my_async_httpx as MyAsyncReq
from utl.加密.utils import get_time_milli

MOD = 1 << 64


def rotate_left(x: int, k: int) -> int:
    bin_str = bin(x)[2:].rjust(64, "0")
    return int(bin_str[k:] + bin_str[:k], base=2)


def fmix64(k: int) -> int:
    C1 = 0xFF51_AFD7_ED55_8CCD
    C2 = 0xC4CE_B9FE_1A85_EC53
    R = 33
    tmp = k
    tmp ^= tmp >> R
    tmp = tmp * C1 % MOD
    tmp ^= tmp >> R
    tmp = tmp * C2 % MOD
    tmp ^= tmp >> R
    return tmp


class UuidInfoc:
    '''
    生成UUID
    '''

    @staticmethod
    def gen() -> str:
        t = get_time_milli() % 100000
        mp = list("123456789ABCDEF") + ["10"]
        pck = [8, 4, 4, 4, 12]
        gen_part = lambda x: "".join([random.choice(mp) for _ in range(x)])
        return "-".join([gen_part(l) for l in pck]) + str(t).ljust(5, "0") + "infoc"


@dataclass
class resolution:
    w: int = random.randint(680, 3840)
    h: int = random.randint(480, 2160)
    window_w: int = random.randint(680, 3840)
    window_h: int = random.randint(680, 3840)
    avail_w: int = random.randint(680, 3840)
    avail_h: int = random.randint(680, 3840)


@dataclass
class APIExClimbWuzhi:
    _spi: str = "https://api.bilibili.com/x/frontend/finger/spi"
    _giaGateWayExClimbWuzhi: str = "https://api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi"
    _GenWebTicket = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
    browser_resolution: resolution = resolution()
    request_url = "https://www.bilibili.com/"
    ua: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    cookie: str = ""
    Buvid: str = ""
    bili_ticket: str = ""
    bili_ticket_expires: str | int = ""
    deviceMemory: int = 8
    CPUCoreNum: int = 4
    _uuid: str = UuidInfoc.gen()
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    timezoneOffset: int = -480
    renderer_id: str = ''
    renderer: str = ''

    @property
    def GenWebTicket(self):
        return self._GenWebTicket

    @property
    def giaGateWayExClimbWuzhi(self):
        return self._giaGateWayExClimbWuzhi

    @property
    def spi(self):
        """
        https://api.bilibili.com/x/frontend/finger/spi
        :return:
        """
        return self._spi

    @property
    def uuid(self):
        return self._uuid


class BuvidFp:
    @staticmethod
    def gen(payload_key: str, seed: int = 31) -> Optional[str]:
        source = io.BytesIO(bytes(payload_key, "ascii"))
        m = murmur3_x64_128(source, seed)
        return "{}{}".format(hex(m & (MOD - 1))[2:], hex(m >> 64)[2:])
        # key = BuvidFp._gen_key_from_compoonents(BuvidFp.get_payload(apiExClimbWuzhi))
        # m = murmur3_x64_128(io.BytesIO(key.encode()), seed)
        # if m is not None:
        #     return format("{:016x}{:016x}".format(m & ((1 << 64) - 1), m >> 64))
        # return None

    @staticmethod
    def _gen_key_from_compoonents(compoonents: list[dict]) -> str:
        def change_str_to_js_string(string: str) -> str:
            return string.replace('False', 'false').replace('True', 'true').replace('None', 'null')

        if type(compoonents) is not list:
            return ""
        ret_str = ""
        for cp in compoonents:
            v = cp.get('value')
            if type(v) is list:
                ret_str += ','.join([str(x) for x in v])
            elif type(v) is bool:
                ret_str += change_str_to_js_string(str(v))
            else:
                ret_str += str(v)
        return ret_str

    @staticmethod
    def gen_payload(my_cfg: APIExClimbWuzhi = APIExClimbWuzhi()) -> str:
        content = {
            "3064": 1,  # ptype, mobile => 2, others => 1
            "5062": str(get_time_milli()),  # timestamp
            "03bf": quote(my_cfg.request_url, safe=''),  # url accessed
            "39c8": "333.1007.fp.risk",  # spm_id,
            "34f1": "",  # target_url, default empty now
            "d402": "",  # screenx, default empty
            "654a": "",  # screeny, default empty
            "6e7c": f"{my_cfg.browser_resolution.w}x{my_cfg.browser_resolution.h}",
            # browser_resolution, window.innerWidth || document.body && document.body.clientWidth + "x" + window.innerHeight || document.body && document.body.clientHeight
            "3c43": {  # 3c43 => msg
                "2673": 1,
                # hasLiedResolution, window.screen.width < window.screen.availWidth || window.screen.height < window.screen.availHeight
                "5766": 24,  # colorDepth, window.screen.colorDepth
                "6527": 0,  # addBehavior, !!window.HTMLElement.prototype.addBehavior, html5 api
                "7003": 1,  # indexedDb, !!window.indexedDB, html5 api
                "807e": 1,  # cookieEnabled, navigator.cookieEnabled
                "b8ce": my_cfg.ua,
                # ua
                "641c": 0,  # webdriver, navigator.webdriver, like Selenium
                "07a4": my_cfg.language,  # language
                "1c57": my_cfg.deviceMemory,  # deviceMemory in GB, navigator.deviceMemory
                "0bd0": my_cfg.CPUCoreNum,  # hardwareConcurrency, navigator.hardwareConcurrency
                "748e": [
                    my_cfg.browser_resolution.window_w,  # window.screen.width
                    my_cfg.browser_resolution.window_h  # window.screen.height
                ],  # screenResolution
                "d61f": [
                    my_cfg.browser_resolution.avail_w,  # window.screen.availWidth
                    my_cfg.browser_resolution.avail_h  # window.screen.availHeight
                ],  # availableScreenResolution
                "fc9d": my_cfg.timezoneOffset,  # timezoneOffset, (new Date).getTimezoneOffset()
                "6aa9": my_cfg.timezone,  # timezone, (new window.Intl.DateTimeFormat).resolvedOptions().timeZone
                "75b8": 1,  # sessionStorage, window.sessionStorage, html5 api
                "3b21": 1,  # localStorage, window.localStorage, html5 api
                "8a1c": 0,  # openDatabase, window.openDatabase, html5 api
                "d52f": "not available",  # cpuClass, navigator.cpuClass
                "adca": "Win32" if "Linux" not in my_cfg.ua else "Linux",  # platform, navigator.platform
                "80c9": [
                    [
                        "PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Chrome PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Chromium PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Microsoft Edge PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "WebKit built-in PDF",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ]
                ],  # plugins
                "13ab": base64.b64encode(hex(int(time.time() * random.random()))[2:].encode('ascii')).decode('utf-8'),
                # canvas fingerprint
                "bfe9": ''.join([random.choice(string.ascii_letters + '1234567890') for x in range(50)]),  # webgl_str
                "a3c1": [
                    "extensions:ANGLE_instanced_arrays;EXT_blend_minmax;EXT_color_buffer_half_float;EXT_disjoint_timer_query;EXT_float_blend;EXT_frag_depth;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;EXT_sRGB;KHR_parallel_shader_compile;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBGL_multi_draw",
                    "webgl aliased line width range:[1, 1]",
                    "webgl aliased point size range:[1, 1024]",
                    "webgl alpha bits:8",
                    "webgl antialiasing:yes",
                    "webgl blue bits:8",
                    "webgl depth bits:24",
                    "webgl green bits:8",
                    "webgl max anisotropy:16",
                    "webgl max combined texture image units:32",
                    "webgl max cube map texture size:16384",
                    "webgl max fragment uniform vectors:1024",
                    "webgl max render buffer size:16384",
                    "webgl max texture image units:16",
                    "webgl max texture size:16384",
                    "webgl max varying vectors:30",
                    "webgl max vertex attribs:16",
                    "webgl max vertex texture image units:16",
                    "webgl max vertex uniform vectors:4095",
                    "webgl max viewport dims:[32767, 32767]",
                    "webgl red bits:8",
                    "webgl renderer:WebKit WebGL",
                    "webgl shading language version:WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                    "webgl stencil bits:0",
                    "webgl vendor:WebKit",
                    "webgl version:WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    "webgl unmasked vendor:Google Inc. (NVIDIA) #X3fQVPgERx",
                    f"webgl unmasked renderer:{my_cfg.renderer}",
                    "webgl vertex shader high float precision:23",
                    "webgl vertex shader high float precision rangeMin:127",
                    "webgl vertex shader high float precision rangeMax:127",
                    "webgl vertex shader medium float precision:23",
                    "webgl vertex shader medium float precision rangeMin:127",
                    "webgl vertex shader medium float precision rangeMax:127",
                    "webgl vertex shader low float precision:23",
                    "webgl vertex shader low float precision rangeMin:127",
                    "webgl vertex shader low float precision rangeMax:127",
                    "webgl fragment shader high float precision:23",
                    "webgl fragment shader high float precision rangeMin:127",
                    "webgl fragment shader high float precision rangeMax:127",
                    "webgl fragment shader medium float precision:23",
                    "webgl fragment shader medium float precision rangeMin:127",
                    "webgl fragment shader medium float precision rangeMax:127",
                    "webgl fragment shader low float precision:23",
                    "webgl fragment shader low float precision rangeMin:127",
                    "webgl fragment shader low float precision rangeMax:127",
                    "webgl vertex shader high int precision:0",
                    "webgl vertex shader high int precision rangeMin:31",
                    "webgl vertex shader high int precision rangeMax:30",
                    "webgl vertex shader medium int precision:0",
                    "webgl vertex shader medium int precision rangeMin:31",
                    "webgl vertex shader medium int precision rangeMax:30",
                    "webgl vertex shader low int precision:0",
                    "webgl vertex shader low int precision rangeMin:31",
                    "webgl vertex shader low int precision rangeMax:30",
                    "webgl fragment shader high int precision:0",
                    "webgl fragment shader high int precision rangeMin:31",
                    "webgl fragment shader high int precision rangeMax:30",
                    "webgl fragment shader medium int precision:0",
                    "webgl fragment shader medium int precision rangeMin:31",
                    "webgl fragment shader medium int precision rangeMax:30",
                    "webgl fragment shader low int precision:0",
                    "webgl fragment shader low int precision rangeMin:31",
                    "webgl fragment shader low int precision rangeMax:30"
                ],  # webgl_params, cab be set to [] if webgl is not supported
                "6bc5": f"Google Inc. (NVIDIA) {my_cfg.renderer_id}~{my_cfg.renderer}",
                # webglVendorAndRenderer
                "ed31": 0,  # hasLiedLanguages
                "72bd": 0,  # hasLiedOs
                "097b": 0,  # hasLiedBrowser
                "52cd": [
                    0,
                    # void 0 !== navigator.maxTouchPoints ? t = navigator.maxTouchPoints : void 0 !== navigator.msMaxTouchPoints && (t = navigator.msMaxTouchPoints);
                    0,  # document.createEvent("TouchEvent"), if succeed 1 else 0
                    0  # "ontouchstart" in window ? 1 : 0
                ],  # touch support
                "a658": [
                    "Arial",
                    "Arial Black",
                    "Arial Narrow",
                    "Calibri",
                    "Cambria",
                    "Cambria Math",
                    "Comic Sans MS",
                    "Consolas",
                    "Courier",
                    "Courier New",
                    "Georgia",
                    "Helvetica",
                    "Impact",
                    "Lucida Console",
                    "Lucida Sans Unicode",
                    "Microsoft Sans Serif",
                    "MS Gothic",
                    "MS PGothic",
                    "MS Sans Serif",
                    "MS Serif",
                    "Palatino Linotype",
                    "Segoe Print",
                    "Segoe Script",
                    "Segoe UI",
                    "Segoe UI Light",
                    "Segoe UI Semibold",
                    "Segoe UI Symbol",
                    "Tahoma",
                    "Times",
                    "Times New Roman",
                    "Trebuchet MS",
                    "Verdana",
                    "Wingdings"
                ],  # font details. see https:#github.com/fingerprintjs/fingerprintjs for implementation details
                "d02f": "124.04347527516074"  # str(124 + random.random())
                # audio fingerprint. see https:#github.com/fingerprintjs/fingerprintjs for implementation details
            },
            "54ef": '{"in_new_ab":true,"ab_version":{"remove_back_version":"REMOVE","login_dialog_version":"V_PLAYER_PLAY_TOAST","open_recommend_blank":"SELF","storage_back_btn":"HIDE","call_pc_app":"FORBID","clean_version_old":"GO_NEW","optimize_fmp_version":"LOADED_METADATA","for_ai_home_version":"V_OTHER","bmg_fallback_version":"DEFAULT","ai_summary_version":"SHOW","weixin_popup_block":"ENABLE","rcmd_tab_version":"DISABLE","in_new_ab":true},"ab_split_num":{"remove_back_version":11,"login_dialog_version":43,"open_recommend_blank":90,"storage_back_btn":87,"call_pc_app":47,"clean_version_old":46,"optimize_fmp_version":28,"for_ai_home_version":38,"bmg_fallback_version":86,"ai_summary_version":466,"weixin_popup_block":45,"rcmd_tab_version":90,"in_new_ab":0},"pageVersion":"new_video","videoGoOldVersion":-1}',
            # abtest info, embedded in html
            "8b94": "",  # refer_url, document.referrer ? encodeURIComponent(document.referrer).substr(0, 1e3) : ""
            "df35": my_cfg._uuid,
            # _uuid, set from cookie, generated by client side(algorithm remains unknown)
            "07a4": "zh-CN",  # language
            "5f45": None,  # laboratory, set from cookie, null if empty, source remains unknown
            "db46": 0  # is_selfdef, default 0
        }
        return json.dumps(
            {"payload": json.dumps(content, separators=(",", ":"))},
            separators=(",", ":"),
        )


def murmur3_x64_128(source: io.IOBase, seed: int) -> Optional[int]:
    C1 = 0x87C3_7B91_1142_53D5
    C2 = 0x4CF5_AD43_2745_937F
    C3 = 0x52DC_E729
    C4 = 0x3849_5AB5
    R1, R2, R3, M = 27, 31, 33, 5
    h1, h2 = seed, seed
    processed = 0
    while 1:
        read = source.read(16)
        processed += len(read)
        if len(read) == 16:
            k1 = struct.unpack("<q", read[:8])[0]
            k2 = struct.unpack("<q", read[8:])[0]
            h1 ^= rotate_left(k1 * C1 % MOD, R2) * C2 % MOD
            h1 = ((rotate_left(h1, R1) + h2) * M + C3) % MOD
            h2 ^= rotate_left(k2 * C2 % MOD, R3) * C1 % MOD
            h2 = ((rotate_left(h2, R2) + h1) * M + C4) % MOD
        elif len(read) == 0:
            h1 ^= processed
            h2 ^= processed
            h1 = (h1 + h2) % MOD
            h2 = (h2 + h1) % MOD
            h1 = fmix64(h1)
            h2 = fmix64(h2)
            h1 = (h1 + h2) % MOD
            h2 = (h2 + h1) % MOD
            return (h2 << 64) | h1
        else:
            k1 = 0
            k2 = 0
            if len(read) >= 15:
                k2 ^= int(read[14]) << 48
            if len(read) >= 14:
                k2 ^= int(read[13]) << 40
            if len(read) >= 13:
                k2 ^= int(read[12]) << 32
            if len(read) >= 12:
                k2 ^= int(read[11]) << 24
            if len(read) >= 11:
                k2 ^= int(read[10]) << 16
            if len(read) >= 10:
                k2 ^= int(read[9]) << 8
            if len(read) >= 9:
                k2 ^= int(read[8])
                k2 = rotate_left(k2 * C2 % MOD, R3) * C1 % MOD
                h2 ^= k2
            if len(read) >= 8:
                k1 ^= int(read[7]) << 56
            if len(read) >= 7:
                k1 ^= int(read[6]) << 48
            if len(read) >= 6:
                k1 ^= int(read[5]) << 40
            if len(read) >= 5:
                k1 ^= int(read[4]) << 32
            if len(read) >= 4:
                k1 ^= int(read[3]) << 24
            if len(read) >= 3:
                k1 ^= int(read[2]) << 16
            if len(read) >= 2:
                k1 ^= int(read[1]) << 8
            if len(read) >= 1:
                k1 ^= int(read[0])
            k1 = rotate_left(k1 * C1 % MOD, R2) * C2 % MOD
            h1 ^= k1


def hmac_sha256(key, message):
    """
    使用HMAC-SHA256算法对给定的消息进行加密
    :param key: 密钥
    :param message: 要加密的消息
    :return: 加密后的哈希值
    """
    # 将密钥和消息转换为字节串
    key = key.encode('utf-8')
    message = message.encode('utf-8')

    # 创建HMAC对象，使用SHA256哈希算法
    hmac_obj = hmac.new(key, message, hashlib.sha256)

    # 计算哈希值
    hash_value = hmac_obj.digest()

    # 将哈希值转换为十六进制字符串
    hash_hex = hash_value.hex()

    return hash_hex


class ExClimbWuzhi:
    proxy_ip = CONFIG.CONFIG.my_ipv6_addr

    # proxy_ip = None
    @staticmethod
    async def _get_b3_b4_buvidfp_ticket_Cookie(payload: str, apiExClimbWuzhi: APIExClimbWuzhi = APIExClimbWuzhi(),
                                               useProxy=True,
                                               _from: Literal["web", "h5"] = 'web'):
        '''
        获取带有b3和b4的cookie
        :return:
        '''
        fingerprint = BuvidFp.gen(payload, 31)
        if _from == "web":
            cookie = [
                f'buvid_fp={fingerprint}',
                f'fingerprint={fingerprint}',
            ]
        else:
            cookie = [
                f'Buvid={apiExClimbWuzhi.Buvid}',
                f'buvid_fp={fingerprint}',
            ]
        cookie.append("=".join(['b_lsid', utils.lsid()]))
        cookie.append("=".join(['_uuid', apiExClimbWuzhi.uuid]))
        cookie.append("=".join(['b_nut', str(int(time.time()))]))
        try:
            response = await MyAsyncReq.request(method="get",
                                                 url=apiExClimbWuzhi.spi,
                                                 headers={
                                                     "referer": 'https://www.bilibili.com/',
                                                     "user-agent": apiExClimbWuzhi.ua,
                                                     "cookie": "; ".join(cookie),
                                                 })
            response_dict = response.json()
            cookie.append("=".join(['buvid3', quote(response_dict['data']['b_3'], safe='')]))
            cookie.append("=".join(['buvid4', quote(response_dict['data']['b_4'], safe='')]))
        except Exception as e:
            activeExclimbWuzhi_logger.exception(f"获取buvid3和buvid4失败: {e}")
            ExClimbWuzhi.proxy_ip = None
        apiExClimbWuzhi.cookie = "; ".join(cookie)
        try:
            if apiExClimbWuzhi.bili_ticket and apiExClimbWuzhi.bili_ticket_expires:
                cookie.append("=".join(['bili_ticket', apiExClimbWuzhi.bili_ticket]))
                cookie.append("=".join(['bili_ticket_expires', str(apiExClimbWuzhi.bili_ticket_expires)]))
            else:
                bili_ticket = await ExClimbWuzhi._get_bili_ticket_web(apiExClimbWuzhi)
                for k, v in bili_ticket.items():
                    cookie.append("=".join([k, str(v)]))
        except Exception as e:
            activeExclimbWuzhi_logger.error(f"获取bili_ticket失败:{e}")
        apiExClimbWuzhi.cookie = "; ".join(cookie)
        return "; ".join(cookie)

    @staticmethod
    async def _get_bili_ticket_web(apiExClimbWuzhi: APIExClimbWuzhi = APIExClimbWuzhi()):
        o = hmac_sha256("XgwSnGZ1p", f"ts{int(time.time())}")
        params = {
            "key_id": "ec02",
            "hexsign": o,
            "context[ts]": f"{int(time.time())}",
            "csrf": ''
        }
        headers = {
            'user-agent': apiExClimbWuzhi.ua,
            'cookie': apiExClimbWuzhi.cookie
        }
        resp = await MyAsyncReq.request(url=apiExClimbWuzhi.GenWebTicket,
                                        method='post',
                                        params=params,
                                        headers=headers,
                                        )
        resp_json = resp.json()
        return {
            "bili_ticket": resp_json['data']['ticket'],
            'bili_ticket_expires': resp_json['data']['created_at']
        }

    @staticmethod
    async def verifyExClimbWuzhi(url: str = "https://www.bilibili.com/",
                                 my_cfg: APIExClimbWuzhi = APIExClimbWuzhi(),
                                 use_proxy: bool = None,
                                 _from: Literal["web", "h5"] = "web",
                                 ) -> str:
        if type(my_cfg) != APIExClimbWuzhi:
            raise Exception(f"MYCFG type is not an APIExClimbWuzi!\n{my_cfg}")
        if not my_cfg.ua:
            my_cfg = APIExClimbWuzhi()
        my_cfg.renderer_id = f"#X{''.join([random.choice(string.ascii_letters + '123456789') for x in range(9)])}" if not my_cfg.renderer_id else my_cfg.renderer_id
        my_cfg.renderer = f"ANGLE (NVIDIA, NVIDIA GeForce RTX {random.choice('12345')}0{random.choice('56789')}0 Laptop GPU (0x00002560) Direct3D11 vs_5_0 ps_5_0, D3D11) {my_cfg.renderer_id}" if not my_cfg.renderer else my_cfg.renderer
        payload = BuvidFp.gen_payload(my_cfg)

        if not my_cfg.cookie:
            cookie = await ExClimbWuzhi._get_b3_b4_buvidfp_ticket_Cookie(payload, my_cfg, useProxy=use_proxy,
                                                                         _from=_from)
            my_cfg.cookie = cookie
        else:
            cookie = my_cfg.cookie
        headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json;charset=UTF-8",
            "dnt": "1",
            "origin": "https://www.bilibili.com",
            "referer": "https://www.bilibili.com/",
            "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "cookie": cookie,
            "user-agent": APIExClimbWuzhi.ua
        }
        if _from == 'h5':
            headers = {
                'user-agent': my_cfg.ua,
                'content-type': 'application/json',
                'accept': '*/*',
                'origin': 'https://www.bilibili.com',
                'x-requested-with': 'tv.danmaku.bili',
                'sec-fetch-site': 'same-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://www.bilibili.com/',
                'accept-encoding': 'gzip, deflate',
                'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            headers = tuple(headers.items())
            for i in cookie.split(';'):
                headers += (('cookie', i.strip(),),)
        try:
            resp = await MyAsyncReq.request(url=my_cfg.giaGateWayExClimbWuzhi,
                                                 method='post',
                                                 data=payload,
                                                 headers=headers
                                                 )
            resp_dict = resp.json()
            activeExclimbWuzhi_logger.debug(f'ExClimbWuzhi提交响应：{resp_dict}')
            if resp_dict.get('code') != 0:
                activeExclimbWuzhi_logger.error(f'{resp_dict} ExClimbWuzhi提交失败！参数：\n{payload}')
        except Exception as e:
            activeExclimbWuzhi_logger.exception(f'ExClimbWuzhi提交失败！参数：\n{payload}\n错误信息：{type(e)}{e}')
        return cookie


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(ExClimbWuzhi.verifyExClimbWuzhi()))
