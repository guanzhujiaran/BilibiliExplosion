import json

import wasmtime
import os
import logging
from typing import List, Any, Tuple

# 设置日志记录，方便调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WasmEnvironment:
    """
    一个用于模拟 wasm-bindgen 生成的 JavaScript 粘合代码环境的 Python 类。
    它使用 wasmtime 库加载并与 WASM 模块进行交互。
    """

    def __init__(self, wasm_file_path: str):
        """
        初始化环境，加载 WASM 模块并链接导入函数。
        """
        logging.info(f"正在初始化 WasmEnvironment，使用文件: {wasm_file_path}")

        # 1. 初始化 wasmtime
        self.engine = wasmtime.Engine()
        self.store = wasmtime.Store(self.engine)
        self.module = wasmtime.Module.from_file(self.engine, wasm_file_path)
        self.linker = wasmtime.Linker(self.engine)

        # 2. 模拟 JS 句柄表 (`s` 数组)
        # s[0-131] 是预留的
        self.s_table: List[Any] = [None] * 132
        # 模拟 `c` 变量，用于实现一个简单的 freelist 来回收句柄索引
        self.next_free_idx = 132

        # 3. 定义 WASM 所需的所有导入函数
        self._define_imports()

        # 4. 实例化模块
        self.instance = self.linker.instantiate(self.store, self.module)
        logging.info("WASM 模块实例化成功。")

        # 5. 获取对 WASM 内存和导出函数的引用
        exports = self.instance.exports(self.store)
        self.memory = exports["memory"]

        # 这些是 wasm-bindgen 用于内存管理的标准导出函数
        self.wasm_alloc = exports["__wbindgen_export_1"]
        self.wasm_realloc = exports["__wbindgen_export_2"]
        self.wasm_free = exports["__wbindgen_export_3"]
        self.wasm_stack_alloc = exports["__wbindgen_add_to_stack_pointer"]

        # 核心业务逻辑函数
        self.core_encrypt_data = exports["encrypt_data"]
        logging.info("环境设置完毕。")

    def _add_to_table(self, obj: Any) -> int:
        """
        模拟 JS 中的 `e` 函数，将一个 Python 对象添加到句柄表中并返回其索引。
        """
        if self.next_free_idx == len(self.s_table):
            self.s_table.append(None)

        idx = self.next_free_idx
        self.next_free_idx = self.s_table[idx] if self.s_table[idx] is not None else len(self.s_table)

        self.s_table[idx] = obj
        return idx

    def _get_from_table(self, idx: int) -> Any:
        """
        模拟 JS 中的 `M` 函数，根据索引从句柄表中获取 Python 对象。
        """
        if idx >= len(self.s_table):
            raise IndexError(f"句柄索引 {idx} 超出范围。")
        return self.s_table[idx]

    def _remove_from_table(self, idx: int) -> Any:
        """
        模拟 JS 中的 `n` 函数，从句柄表中移除一个对象并回收其索引。
        """
        if idx < 132:
            return None  # 预留值不能被移除

        obj = self.s_table[idx]
        self.s_table[idx] = self.next_free_idx
        self.next_free_idx = idx
        return obj

    def _read_string_from_wasm(self, ptr: int, length: int) -> str:
        """
        从 WASM 内存中读取 UTF-8 编码的字符串。
        """
        memory_data = self.memory.read(self.store, ptr, length)
        return memory_data.decode('utf-8')

    def _write_string_to_wasm(self, s: str) -> Tuple[int, int]:
        """
        将 Python 字符串写入 WASM 内存。
        这模拟了 JS 粘合代码中的 `r` 函数。
        1. 编码字符串为 UTF-8。
        2. 调用 WASM 的分配器获取内存空间。
        3. 将编码后的字节写入分配的内存。
        返回 (指针, 长度) 元组。
        """
        encoded_s = s.encode('utf-8')
        length = len(encoded_s)

        # 调用 wasm 内部的分配器来获取内存地址
        ptr = self.wasm_alloc(self.store, length, 1)
        if not isinstance(ptr, int): ptr = ptr[0]  # wasmtime v10+

        # 将数据写入内存
        self.memory.write(self.store, encoded_s, ptr)

        logging.debug(f"将字符串 '{s[:20]}...' 写入到内存地址 {ptr}，长度 {length}")
        return ptr, length

    def _define_imports(self):
        """
        在此处定义所有 wasm-bindgen 需要的导入函数。

        此版本添加了对 Node.js `require` 和 `crypto.randomFillSync` 的模拟。
        """
        ns = "wbg"

        # --- 模拟 Node.js 环境所需的对象 ---
        self.mock_process = {"versions": {"node": "18.0.0"}}
        self.mock_global = {"process": self.mock_process, "crypto": {"__is_crypto": True}}

        # --- 核心辅助函数 ---
        def __wbindgen_string_new(ptr: int, length: int) -> int:
            return self._add_to_table(self._read_string_from_wasm(ptr, length))

        self.linker.define_func(ns, "__wbindgen_string_new",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()],
                                                  [wasmtime.ValType.i32()]), __wbindgen_string_new)

        def __wbindgen_object_drop_ref(idx: int):
            self._remove_from_table(idx)

        self.linker.define_func(ns, "__wbindgen_object_drop_ref", wasmtime.FuncType([wasmtime.ValType.i32()], []),
                                __wbindgen_object_drop_ref)

        def __wbindgen_is_string(idx: int) -> int:
            return 1 if isinstance(self._get_from_table(idx), str) else 0

        self.linker.define_func(ns, "__wbindgen_is_string",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_string)

        def __wbindgen_is_object(idx: int) -> int:
            return 1 if isinstance(self._get_from_table(idx), (dict, list, bytearray)) else 0

        self.linker.define_func(ns, "__wbindgen_is_object",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_object)

        def __wbindgen_is_undefined(idx: int) -> int:
            return 1 if self._get_from_table(idx) is None else 0

        self.linker.define_func(ns, "__wbindgen_is_undefined",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_undefined)

        def __wbindgen_throw(ptr: int, length: int):
            raise RuntimeError(f"WASM Error: {self._read_string_from_wasm(ptr, length)}")

        self.linker.define_func(ns, "__wbindgen_throw",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbindgen_throw)

        # --- 环境探测 (Node.js & Browser) ---
        def __wbg_globalThis_56578be7e9f832b0() -> int:
            return self._add_to_table(self.mock_global)

        self.linker.define_func(ns, "__wbg_globalThis_56578be7e9f832b0",
                                wasmtime.FuncType([], [wasmtime.ValType.i32()]), __wbg_globalThis_56578be7e9f832b0)

        def __wbg_process_dc0fbacc7c1c06f7(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("process"))

        self.linker.define_func(ns, "__wbg_process_dc0fbacc7c1c06f7",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_process_dc0fbacc7c1c06f7)

        def __wbg_versions_c01dfd4722a88165(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("versions"))

        self.linker.define_func(ns, "__wbg_versions_c01dfd4722a88165",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_versions_c01dfd4722a88165)

        def __wbg_node_905d3e251edff8a2(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("node"))

        self.linker.define_func(ns, "__wbg_node_905d3e251edff8a2",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_node_905d3e251edff8a2)

        # --- Node.js `require` 模拟 ---
        def __wbg_require_60cc747a6bc5215a() -> int:
            return self._add_to_table(self._mock_require)

        self.linker.define_func(ns, "__wbg_require_60cc747a6bc5215a", wasmtime.FuncType([], [wasmtime.ValType.i32()]),
                                __wbg_require_60cc747a6bc5215a)

        # --- 加密/随机数 (Browser & Node.js) ---
        def __wbg_crypto_574e78ad8b13b65f(_) -> int:
            return self._add_to_table({"__is_crypto": True})

        self.linker.define_func(ns, "__wbg_crypto_574e78ad8b13b65f",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_crypto_574e78ad8b13b65f)

        def __wbg_getRandomValues_b8f5dbd5f3995a9e(_, h: int):
            buf = self._get_from_table(h)
            if isinstance(buf, bytearray): buf[:] = os.urandom(len(buf))

        self.linker.define_func(ns, "__wbg_getRandomValues_b8f5dbd5f3995a9e",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbg_getRandomValues_b8f5dbd5f3995a9e)

        def __wbg_randomFillSync_ac0988aba3254290(_, h: int):
            buf = self._get_from_table(h)
            if isinstance(buf, bytearray): buf[:] = os.urandom(len(buf))

        self.linker.define_func(ns, "__wbg_randomFillSync_ac0988aba3254290",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbg_randomFillSync_ac0988aba3254290)

        # --- Uint8Array/Buffer 操作 ---
        def __wbg_newwithlength_a381634e90c276d4(l: int) -> int:
            return self._add_to_table(bytearray(l))

        self.linker.define_func(ns, "__wbg_newwithlength_a381634e90c276d4",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_newwithlength_a381634e90c276d4)

        # --- 动态调用函数 (Function.prototype.call) ---
        def __wbg_call_7cccdd69e0791ae2(func_h: int, this_h: int, arg1_h: int) -> int:
            try:
                func = self._get_from_table(func_h)
                if not callable(func): raise TypeError("Attempted to call a non-callable object.")
                # 我们的 _mock_require 需要句柄，而不是解包后的值
                result = func(arg1_h)
                return self._add_to_table(result)
            except Exception as e:
                logging.error(f"Error during __wbg_call_...: {e}")
                # 抛出一个 WASM 能理解的异常
                error_msg_handle, error_msg_len = self._write_string_to_wasm(str(e))
                __wbindgen_throw(error_msg_handle, error_msg_len)
                return 0  # 不会到达这里，但需要一个返回值

        self.linker.define_func(ns, "__wbg_call_7cccdd69e0791ae2", wasmtime.FuncType(
            [wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_call_7cccdd69e0791ae2)

        # 存根：以防万一它调用了无参数的 call
        def __wbg_call_672a4d21634d4a24(func_h: int, this_h: int) -> int:
            logging.warning(f"调用了存根函数 __wbg_call_672a4d21634d4a24")
            return 0

        self.linker.define_func(ns, "__wbg_call_672a4d21634d4a24",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()],
                                                  [wasmtime.ValType.i32()]), __wbg_call_672a4d21634d4a24)

    def _define_imports(self):
        """
        在此处定义所有 wasm-bindgen 需要的导入函数。

        此版本添加了对旧版 IE `msCrypto` 的模拟。
        """
        ns = "wbg"

        # --- 模拟 Node.js 环境所需的对象 ---
        self.mock_process = {"versions": {"node": "18.0.0"}}
        self.mock_global = {"process": self.mock_process, "crypto": {"__is_crypto": True}}

        # --- 核心辅助函数 ---
        def __wbindgen_string_new(ptr: int, length: int) -> int:
            return self._add_to_table(self._read_string_from_wasm(ptr, length))

        self.linker.define_func(ns, "__wbindgen_string_new",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()],
                                                  [wasmtime.ValType.i32()]), __wbindgen_string_new)

        def __wbindgen_object_drop_ref(idx: int):
            self._remove_from_table(idx)

        self.linker.define_func(ns, "__wbindgen_object_drop_ref", wasmtime.FuncType([wasmtime.ValType.i32()], []),
                                __wbindgen_object_drop_ref)

        def __wbindgen_is_string(idx: int) -> int:
            return 1 if isinstance(self._get_from_table(idx), str) else 0

        self.linker.define_func(ns, "__wbindgen_is_string",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_string)

        def __wbindgen_is_object(idx: int) -> int:
            return 1 if isinstance(self._get_from_table(idx), (dict, list, bytearray)) else 0

        self.linker.define_func(ns, "__wbindgen_is_object",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_object)

        def __wbindgen_is_undefined(idx: int) -> int:
            return 1 if self._get_from_table(idx) is None else 0

        self.linker.define_func(ns, "__wbindgen_is_undefined",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbindgen_is_undefined)

        def __wbindgen_throw(ptr: int, length: int):
            raise RuntimeError(f"WASM Error: {self._read_string_from_wasm(ptr, length)}")

        self.linker.define_func(ns, "__wbindgen_throw",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbindgen_throw)

        # --- 环境探测 (Node.js & Browser) ---
        def __wbg_globalThis_56578be7e9f832b0() -> int:
            return self._add_to_table(self.mock_global)

        self.linker.define_func(ns, "__wbg_globalThis_56578be7e9f832b0",
                                wasmtime.FuncType([], [wasmtime.ValType.i32()]), __wbg_globalThis_56578be7e9f832b0)

        def __wbg_process_dc0fbacc7c1c06f7(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("process"))

        self.linker.define_func(ns, "__wbg_process_dc0fbacc7c1c06f7",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_process_dc0fbacc7c1c06f7)

        def __wbg_versions_c01dfd4722a88165(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("versions"))

        self.linker.define_func(ns, "__wbg_versions_c01dfd4722a88165",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_versions_c01dfd4722a88165)

        def __wbg_node_905d3e251edff8a2(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get("node"))

        self.linker.define_func(ns, "__wbg_node_905d3e251edff8a2",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_node_905d3e251edff8a2)

        def __wbg_require_60cc747a6bc5215a() -> int:
            return self._add_to_table(self._mock_require)

        self.linker.define_func(ns, "__wbg_require_60cc747a6bc5215a", wasmtime.FuncType([], [wasmtime.ValType.i32()]),
                                __wbg_require_60cc747a6bc5215a)

        # --- 加密/随机数 (Browser & Node.js) ---
        def __wbg_crypto_574e78ad8b13b65f(h: int) -> int:
            return self._add_to_table(self._get_from_table(h).get('crypto'))

        self.linker.define_func(ns, "__wbg_crypto_574e78ad8b13b65f",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_crypto_574e78ad8b13b65f)

        # 新增的函数！
        def __wbg_msCrypto_a61aeb35a24c1329(h: int) -> int:
            # 模拟在全局对象上找不到 msCrypto 的情况
            global_obj = self._get_from_table(h)
            ms_crypto_obj = global_obj.get('msCrypto', None)  # .get with default returns None
            return self._add_to_table(ms_crypto_obj)  # Add None (== undefined) to table

        self.linker.define_func(ns, "__wbg_msCrypto_a61aeb35a24c1329",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_msCrypto_a61aeb35a24c1329)

        def __wbg_getRandomValues_b8f5dbd5f3995a9e(_, h: int):
            buf = self._get_from_table(h)
            if isinstance(buf, bytearray): buf[:] = os.urandom(len(buf))

        self.linker.define_func(ns, "__wbg_getRandomValues_b8f5dbd5f3995a9e",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbg_getRandomValues_b8f5dbd5f3995a9e)

        def __wbg_randomFillSync_ac0988aba3254290(_, h: int):
            buf = self._get_from_table(h)
            if isinstance(buf, bytearray): buf[:] = os.urandom(len(buf))

        self.linker.define_func(ns, "__wbg_randomFillSync_ac0988aba3254290",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []),
                                __wbg_randomFillSync_ac0988aba3254290)

        # --- Uint8Array/Buffer 操作 ---
        def __wbg_newwithlength_a381634e90c276d4(l: int) -> int:
            return self._add_to_table(bytearray(l))

        self.linker.define_func(ns, "__wbg_newwithlength_a381634e90c276d4",
                                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_newwithlength_a381634e90c276d4)

        # --- 动态调用函数 (Function.prototype.call) ---
        def __wbg_call_7cccdd69e0791ae2(func_h: int, this_h: int, arg1_h: int) -> int:
            try:
                func = self._get_from_table(func_h)
                if not callable(func): raise TypeError(f"Attempted to call a non-callable object: {type(func)}")
                result = func(arg1_h)
                return self._add_to_table(result)
            except Exception as e:
                logging.error(f"Error during __wbg_call_...: {e}")
                error_msg_handle, error_msg_len = self._write_string_to_wasm(str(e))
                __wbindgen_throw(error_msg_handle, error_msg_len)
                return 0

        self.linker.define_func(ns, "__wbg_call_7cccdd69e0791ae2", wasmtime.FuncType(
            [wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                                __wbg_call_7cccdd69e0791ae2)

        def __wbg_call_672a4d21634d4a24(func_h: int, this_h: int) -> int:
            logging.warning(f"调用了存根函数 __wbg_call_672a4d24")
            return 0

        self.linker.define_func(ns, "__wbg_call_672a4d24",
                                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()],
                                                  [wasmtime.ValType.i32()]), __wbg_call_672a4d21634d4a24)


if __name__ == "__main__":
    wasm_env = WasmEnvironment("exclimb_congling.wasm")
    result = wasm_env.encrypt_data(
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
        }, separators=(',', ':')),
        'B00659C6-6026-9F85-0611-308708B3E6F590581infoc',
        '000001000000001011111'
    )
    print(result)
    assert result == '{"data":"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","key":"wXo1pUG2egNxYO5d5xcs7uh6iPSkEcjUHP+Lu4Gejw/D50wCkNZSH6DxVcjWwKkAcSLy+Le1w0HKUavSnJ+m2MS8BsD7JYqwCrD+iy6D3U0EEMnsAYlRrQzvHBR0M3I7uQj/h/hvuVRgPfpC08wp4j41U55wbECTkHwJtrWEj676hvLKIP0w1hFJERer8KIYYr+vu/5BaGbW508mNpNxZGs3ETqc6HJYOthBNLV9STRU6o8EosVdI2sqIxQnIIGJbalYgoX1rnAUPvQK36gb19X58Iod0qE394perL+BneX3mRsbrYwjEztSIyhb62N83jJlIHsM9dkpRTVNb6Gdoy/sjl/YWSsNxm3CEHgnGv9tjT9LF3u0qCK3N/bvoGhl0KdaTE9OFcQFSJK77CUUFPRO9GdwgjkRaS3ezm5czU88egBxX4fmFmsQrO3Y1D9SzBPfufLjrcckanWlNpitlVYocVPPdcXz9NjOSfkagAIt5h8GPiklFNSAOsFNRXjEEoV+B7R9323yMtzAZ2ahyMQOxAsds/kPtURH3lavvoaFaOkCzXzLhBYZBc4y3wzEX+qar6DuanATs/MrdwGlqCIqZvY9a77Gype2YjqgXQtdo3bxHQdpgnIGeXNA/h0BZBolo8velZkliNlKHJahjSOxaAGRjRVFnGlEgriTNKo="}', '加密出错'
