import json

from wasmtime import Store, Module, Engine, Linker


class WasmModule:
    def __init__(self, wasm_file):
        self.store = Store()
        self.engine = Engine()
        self.linker = Linker(self.engine)
        self.module = Module.from_file(self.engine, wasm_file)
        self.instance = self.linker.instantiate(self.store, self.module)
        self.exports = self.instance.exports(self.store)

        # 获取 WASM 内存
        self.memory = self.exports["memory"]

        # 获取 WASM 函数
        self.encrypt_data_func = self.exports["encrypt_data"]
        self.__wbindgen_export_1 = self.exports["__wbindgen_export_1"]  # alloc
        self.__wbindgen_export_2 = self.exports["__wbindgen_export_2"]  # realloc
        self.__wbindgen_export_3 = self.exports["__wbindgen_export_3"]  # dealloc
        self.__wbindgen_add_to_stack_pointer = self.exports["__wbindgen_add_to_stack_pointer"]

        # 全局变量 R
        self.R = 0

    def h(self):
        """获取内存缓冲区"""
        return self.memory.data_ptr(self.store)

    def L(self):
        """获取内存的 DataView"""
        return self.memory

    def F(self, A, I):
        """从内存读取 UTF-8 字符串"""
        A &= 0xFFFFFFFF  # 模拟 >>>= 0
        data = self.h()[A:A + I]
        return bytes(data).decode("utf-8")

    def r(self, A, I, g=None):
        """
        将字符串写入 WASM 内存，返回指针
        :param A: str or bytes
        :param I: alloc 函数
        :param g: realloc 函数 (可选)
        :return: ptr
        """
        if g is None:
            return self._r_fast_ascii(A, I)
        else:
            return self._r_utf8(A, I, g)

    def _r_fast_ascii(self, A, I):
        """尝试快速写入 ASCII 字符串"""
        if isinstance(A, bytes):
            A = A.decode("utf-8")
        elif not isinstance(A, str):
            raise TypeError("Expected str or bytes")

        B = len(A)
        Q = I(self.store, B, 1) >> 0
        C = self.h()

        E = 0
        while E < B:
            char_code = ord(A[E])
            if char_code > 127:
                break
            C[Q + E] = char_code
            E += 1

        if E == B:
            self.R = E
            return Q

        # 有非 ASCII 字符，切换到 UTF-8 写入
        return self._r_utf8(A, I, self.__wbindgen_export_2)

    def _r_utf8(self, A, I, g):
        """写入 UTF-8 编码字符串"""
        if isinstance(A, bytes):
            A = A.decode("utf-8")

        A = A[self.R:]  # 剩余部分
        B = self.R + 3 * len(A)  # 预估大小
        Q = g(self.store, self.R, B, 1) >> 0
        target = self.h()[Q + self.R: Q + B]

        written = 0
        for ch in A:
            code = ord(ch)
            if code < 0x80:
                target[written] = code
                written += 1
            elif code < 0x800:
                target[written] = 0xC0 | (code >> 6)
                target[written + 1] = 0x80 | (code & 0x3F)
                written += 2
            elif code < 0xD800 or code >= 0xE000:
                target[written] = 0xE0 | (code >> 12)
                target[written + 1] = 0x80 | ((code >> 6) & 0x3F)
                target[written + 2] = 0x80 | (code & 0x3F)
                written += 3
            elif code < 0xDC00:
                # Surrogate pair
                next_code = ord(A[A.index(ch) + 1]) if A.index(ch) + 1 < len(A) else 0
                if 0xDC00 <= next_code < 0xE000:
                    code = 0x10000 + ((code - 0xD800) << 10) + (next_code - 0xDC00)
                    target[written] = 0xF0 | (code >> 18)
                    target[written + 1] = 0x80 | ((code >> 12) & 0x3F)
                    target[written + 2] = 0x80 | ((code >> 6) & 0x3F)
                    target[written + 3] = 0x80 | (code & 0x3F)
                    written += 4
        self.R += written

        Q = g(self.store, Q, B, self.R, 1) >> 0
        return Q

    def encrypt_data(self, *args):
        """调用 WASM 中的 encrypt_data 函数"""
        o = self.__wbindgen_add_to_stack_pointer(self.store, -16)
        Q = C = 0

        try:
            D = self.r(args[0], self.__wbindgen_export_1, self.__wbindgen_export_2)
            w = self.R
            a = self.r(args[1], self.__wbindgen_export_1, self.__wbindgen_export_2)
            s = self.R
            M = self.r(args[2], self.__wbindgen_export_1, self.__wbindgen_export_2)
            c = self.R
            e = self.r(args[3], self.__wbindgen_export_1, self.__wbindgen_export_2)
            N = self.R

            self.encrypt_data_func(self.store, o, D, w, a, s, M, c, e, N)

            E = self.L().read(self.store, o)
            i = self.L().read(self.store, o + 4)
            Q, C = E, i
            return self.F(E, i)
        finally:
            self.__wbindgen_add_to_stack_pointer(self.store, 16)
            self.__wbindgen_export_3(self.store, Q, C, 1)


if __name__ == "__main__":
    wasm_modeul = WasmModule("enc.wasm")
    result = wasm_modeul.encrypt_data_func(
            json.dumps({
                "buvid_fp": "fa3d9dc1b9ce79b6fc4e62dd29fc5068",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "webdriver": 0,
                "language": "zh-CN",
                "colorDepth": 24,
                "deviceMemory": 8,
                "hardwareConcurrency": 12,
                "screenResolution": [
                    2560,
                    1440
                ],
                "availableScreenResolution": [
                    2560,
                    1392
                ],
                "timezoneOffset": -480,
                "timezone": "Asia/Shanghai",
                "sessionStorage": 1,
                "localStorage": 1,
                "indexedDb": 1,
                "addBehavior": 0,
                "openDatabase": 0,
                "cpuClass": "not available",
                "platform": "Win32",
                "plugins": [
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
                ],
                "canvas": "DF7EAAAAAElFTkSuQmCC",
                "webgl_str": "1kBCiQjQIAKxurGSgK2Ffg/4oKBbVXSVNmAAAAAElFTkSuQmCC",
                "webgl_params": [
                    "extensions:ANGLE_instanced_arrays;EXT_blend_minmax;EXT_clip_control;EXT_color_buffer_half_float;EXT_depth_clamp;EXT_float_blend;EXT_frag_depth;EXT_polygon_offset_clamp;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;EXT_texture_mirror_clamp_to_edge;EXT_sRGB;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_astc;WEBGL_compressed_texture_etc;WEBGL_compressed_texture_etc1;WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBGL_multi_draw;WEBGL_polygon_mode",
                    "webgl aliased line width range:[1, 1]",
                    "webgl aliased point size range:[1, 1023]",
                    "webgl alpha bits:8",
                    "webgl antialiasing:yes",
                    "webgl blue bits:8",
                    "webgl depth bits:24",
                    "webgl green bits:8",
                    "webgl max anisotropy:16",
                    "webgl max combined texture image units:64",
                    "webgl max cube map texture size:16384",
                    "webgl max fragment uniform vectors:4096",
                    "webgl max render buffer size:8192",
                    "webgl max texture image units:32",
                    "webgl max texture size:8192",
                    "webgl max varying vectors:31",
                    "webgl max vertex attribs:16",
                    "webgl max vertex texture image units:32",
                    "webgl max vertex uniform vectors:4096",
                    "webgl max viewport dims:[8192, 8192]",
                    "webgl red bits:8",
                    "webgl renderer:WebKit WebGL",
                    "webgl shading language version:WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                    "webgl stencil bits:0",
                    "webgl vendor:WebKit",
                    "webgl version:WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    "webgl unmasked vendor:Google Inc. (Google)",
                    "webgl unmasked renderer:ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)",
                    "webgl vertex shader high float precision:23",
                    "webgl vertex shader high float precision rangeMin:127",
                    "webgl vertex shader high float precision rangeMax:127",
                    "webgl vertex shader medium float precision:10",
                    "webgl vertex shader medium float precision rangeMin:15",
                    "webgl vertex shader medium float precision rangeMax:15",
                    "webgl vertex shader low float precision:10",
                    "webgl vertex shader low float precision rangeMin:15",
                    "webgl vertex shader low float precision rangeMax:15",
                    "webgl fragment shader high float precision:23",
                    "webgl fragment shader high float precision rangeMin:127",
                    "webgl fragment shader high float precision rangeMax:127",
                    "webgl fragment shader medium float precision:10",
                    "webgl fragment shader medium float precision rangeMin:15",
                    "webgl fragment shader medium float precision rangeMax:15",
                    "webgl fragment shader low float precision:10",
                    "webgl fragment shader low float precision rangeMin:15",
                    "webgl fragment shader low float precision rangeMax:15",
                    "webgl vertex shader high int precision:0",
                    "webgl vertex shader high int precision rangeMin:31",
                    "webgl vertex shader high int precision rangeMax:30",
                    "webgl vertex shader medium int precision:0",
                    "webgl vertex shader medium int precision rangeMin:15",
                    "webgl vertex shader medium int precision rangeMax:14",
                    "webgl vertex shader low int precision:0",
                    "webgl vertex shader low int precision rangeMin:15",
                    "webgl vertex shader low int precision rangeMax:14",
                    "webgl fragment shader high int precision:0",
                    "webgl fragment shader high int precision rangeMin:31",
                    "webgl fragment shader high int precision rangeMax:30",
                    "webgl fragment shader medium int precision:0",
                    "webgl fragment shader medium int precision rangeMin:15",
                    "webgl fragment shader medium int precision rangeMax:14",
                    "webgl fragment shader low int precision:0",
                    "webgl fragment shader low int precision rangeMin:15",
                    "webgl fragment shader low int precision rangeMax:14"
                ],
                "webglVendorAndRenderer": "Google Inc. (Google)|ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)|WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                "hasLiedLanguages": 0,
                "hasLiedResolution": 0,
                "hasLiedOs": 0,
                "hasLiedBrowser": 0,
                "touchSupport": [
                    10,
                    0,
                    0
                ],
                "fonts": [
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
                ],
                "audio": "124.04347527516074",
                "os_source": "pc",
                "nav_languages": [
                    "zh-CN"
                ],
                "nav_productsub": "20030107",
                "eval_length": 33,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "screen_size_info": "1440x2560x24x24x1.75",
                "window_size_info": "252x752x2560x1392",
                "local_time": 1753371795858,
                "os_platform": "Win32",
                "accept": "application/json; charset=utf-8; */*;",
                "accept_encoding": "gzip, deflate, br, zstd",
                "accept_language": "zh-CN,zh;q=0.8,en;q=0.7",
                "cookieEnabled": 1,
                "browser_build_version": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "notify_message_api": "default",
                "spmid": "333.1007",
                "path": "https://www.bilibili.com/",
                "lsid": "95171A82_1983D1A4EC0",
                "b_nut_h": 1753369200,
                "collect_api": "spontaneous",
                "buvid": "B00659C6-6026-9F85-0611-308708B3E6F590581infoc",
                "mid": "",
                "sdk_version": "0.1.7"
            }, separators=(',', ':')),

            json.dumps({
    "version": "v1",
    "public_key": "-----BEGIN rsa public key-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA1SomDTbicibEZdRNTFIf\nG0MZI9Vm+VLvXvoS6YGtHkMexd+O8ImALMxiMkydZ0h5XPPfiUXGiyfWawVW1Q6Q\nL8E9HV8tXgI82zMc/2ZnAyAp5dACWfcsqF1lH4hh63W424c9EJ/Ryqk4ZFss+vDr\nn33+FN1LOyJtg8nPqCt9DN9PFaRvJTEXT0Bt2ZQTiSznHPIpalgHUNsg1OPV3ou9\n5ahf5CpRl89QeIptrbObEqsmRqC0rDwsMUhY1NnvPKGYnCqOWl006q6OBP77qHa9\nHRLZS0EuCEuLUnKRQq2vbbpqKrgIQln+HjMy4oIjV7Bdv9e6SJSxwausegaCQ+pt\nIzy6O41iIQSISCRf+2iywvKGxvi3Jhhc39GxvhBPl9W3QF4knJmWHHbqAb94mDNE\nT0GzjbU6c3j7FJcC2JjK7PeC44+VSyiY7N+9Dc0ulw7OIoigPl+R6zyWEPCdKems\n9Cd8vn/njM+o7BRaBzyqJSYSOjQQiQHJYzcMRhhue/2W1wSx2S9Ry/zNvpP/Qapw\n4Z6IlDt+wL9omIwcFMndUruAaRKQEDgDRKZHspUIRkXhCiaV4MwUH1rF6EFq8BRc\nIsoS5O0o8ew5mzW81q2I1Mkvx2wDRyX9+zlVBMkKAvv3xMzU5l7sUM1eP3tw3mhg\n6D6utwZfuFFb7Zj1oGJq4VMCAwEAAQ==\n-----END rsa public key-----",
    "deadline": 2524608000
},separators=(',',':')
            ),
            'B00659C6-6026-9F85-0611-308708B3E6F590581infoc',
            '000001000000001011111'
        )
    print(result)
