import base64
import hashlib
import hmac
import io
import json
import random
import string
import struct
import time
from typing import Optional, Literal, Any

from pydantic import Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from fastapi接口.utils.Constants import GPU_DATABASE

config = {
    'bilibili': {
        'dmImgList': '[{"img_url": "https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png"}, {"sub_url": "https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png"}]'
    }
}


def get_time_milli() -> int:
    return int(time.time() * 1000)


def lsid():
    ret = ""
    for _ in range(8):
        ret += hex(random.randint(0, 15))[2:].upper()
    ret = f"{ret}_{hex(get_time_milli())[2:].upper()}"
    return ret


MOD = 1 << 64


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


class uuidInfoc:
    """
    生成UUID
    """

    @staticmethod
    def gen() -> str:
        t = get_time_milli() % 100000
        mp = list("123456789ABCDEF") + ["10"]
        pck = [8, 4, 4, 4, 12]
        gen_part = lambda x: "".join([random.choice(mp) for _ in range(x)])
        return "-".join([gen_part(a) for a in pck]) + str(t).ljust(5, "0") + "infoc"


class GenWebCookieParams(CustomBaseModel):
    ua: str
    window_h: int
    window_w: int
    avail_w: int
    avail_h: int
    uuid: str = Field(default_factory=lambda: uuidInfoc.gen())
    language: Literal['zh-CN', 'zh-TW', 'en-US', 'en-GB', 'ja-JP', 'ko-KR'] = 'zh-CN'
    timezone: str = "Asia/Shanghai"
    timezoneOffset: int = -480

    payload_str: str = Field('')
    buvid_fp: str = Field('')
    deviceMemory: int = Field(default_factory=lambda: random.choice(range(4, 33, 4)))
    CPUCoreNum: int = Field(default_factory=lambda: random.choice(range(4, 25, 4)))

    renderer_id: str = Field('')
    renderer: str = Field('')
    webgl_renderer: str = Field(
        '',
        description='''类似
`ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001638) Direct3D11 vs_5_0 ps_5_0, D3D11)Google Inc. (AMD`
''')

    def model_post_init(self, context: Any):
        """
                在模型初始化后，自动生成并填充随机的 renderer 和 webgl 信息。
                - webgl_renderer 格式为: ANGLE (...) Google Inc. (厂商)
                - renderer 格式为: ANGLE (...) #X...随机ID...
                """
        # 1. 随机选择一个 GPU 配置
        selected_gpu = random.choice(GPU_DATABASE)
        manufacturer = selected_gpu['manufacturer']
        gpu_name = selected_gpu['name']
        gpu_id = selected_gpu['id']

        # 2. 生成 renderer ID，它将被用在 renderer 字符串中
        self.renderer_id = f"#X{''.join(random.choices(string.ascii_letters + string.digits, k=9))}"

        # 3. 定义不变的 ANGLE 核心信息部分，方便复用
        angle_core_info = f"ANGLE ({manufacturer}, {gpu_name} ({gpu_id}) Direct3D11 vs_5_0 ps_5_0, D3D11)"

        # 4. 生成 webgl_renderer (格式: ... Google Inc. (厂商))
        self.webgl_renderer = f"{angle_core_info} Google Inc. ({manufacturer})"
        # 5. 生成 renderer (格式: ... #X...ID...)
        self.renderer = f"{angle_core_info} {self.renderer_id}"

        self.payload_str = BuvidFp.gen_payload(buvid_payload_params=self)
        self.buvid_fp = BuvidFp.gen(self.payload_str, 31)


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
    def gen_payload(buvid_payload_params: GenWebCookieParams) -> str:
        content = {
            "39c8": "333.1007.fp.risk",  # spm_id,
            "3c43": {  # 3c43 => msg
                "2673": 0,
                # hasLiedResolution, window.screen.width < window.screen.availWidth || window.screen.height < window.screen.availHeight
                "5766": 24,  # colorDepth, window.screen.colorDepth
                "6527": 0,  # addBehavior, !!window.HTMLElement.prototype.addBehavior, html5 api
                "7003": 1,  # indexedDb, !!window.indexedDB, html5 api
                "807e": 1,  # cookieEnabled, navigator.cookieEnabled
                "b8ce": buvid_payload_params.ua,
                # ua
                "641c": 0,  # webdriver, navigator.webdriver, like Selenium
                "07a4": buvid_payload_params.language,  # language
                "1c57": buvid_payload_params.deviceMemory,  # deviceMemory in GB, navigator.deviceMemory
                "0bd0": buvid_payload_params.CPUCoreNum,  # hardwareConcurrency, navigator.hardwareConcurrency
                "748e": [
                    buvid_payload_params.window_w,  # window.screen.width
                    buvid_payload_params.window_h  # window.screen.height
                ],  # screenResolution
                "d61f": [
                    buvid_payload_params.avail_w,  # window.screen.availWidth
                    buvid_payload_params.avail_h  # window.screen.availHeight
                ],  # availableScreenResolution
                "fc9d": buvid_payload_params.timezoneOffset,  # timezoneOffset, (new Date).getTimezoneOffset()
                "6aa9": buvid_payload_params.timezone,
                # timezone, (new window.Intl.DateTimeFormat).resolvedOptions().timeZone
                "75b8": 1,  # sessionStorage, window.sessionStorage, html5 api
                "3b21": 1,  # localStorage, window.localStorage, html5 api
                "8a1c": 0,  # openDatabase, window.openDatabase, html5 api
                "d52f": "not available",  # cpuClass, navigator.cpuClass
                "adca": "Win32" if "Linux" not in buvid_payload_params.ua else "Linux",  # platform, navigator.platform
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
                    f"webgl unmasked renderer:{buvid_payload_params.renderer}",
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
                "6bc5": f"Google Inc. (NVIDIA) {buvid_payload_params.renderer_id}~{buvid_payload_params.renderer}",
                # webglVendorAndRenderer
                "ed31": 0,  # hasLiedLanguages
                "72bd": 0,  # hasLiedOs
                "097b": 0,  # hasLiedBrowser
                "52cd": [
                    10,
                    0,
                    0
                ],
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
        }
        return json.dumps(
            {"payload": json.dumps(content, separators=(",", ":"))},
            separators=(",", ":"),
        )
