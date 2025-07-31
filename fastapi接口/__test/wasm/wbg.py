# wbg.py

import random
from typing import Any,  Optional

# 模拟 handle 系统（类似 JS 的 JSValue 的 handle）
HANDLE_MAP = {}
HANDLE_COUNTER = 1048576

def e(obj: Any) -> int:
    """将对象注册为句柄"""
    global HANDLE_COUNTER
    HANDLE_COUNTER += 1
    HANDLE_MAP[HANDLE_COUNTER] = obj
    return HANDLE_COUNTER

def n(handle: int) -> Any:
    """根据句柄获取对象"""
    return HANDLE_MAP.get(handle)

def F(ptr: int, length: int) -> str:
    """从 WASM 内存读取 UTF-8 字符串"""
    if not MEMORY:
        raise RuntimeError("Memory not set")
    buffer = MEMORY.read(STORE, ptr, length)
    return bytes(buffer).decode("utf-8")

def r(string: str, malloc, realloc=None) -> int:
    """将字符串写入 WASM 内存，返回指针"""
    encoded = string.encode("utf-8")
    ptr = malloc(len(encoded), 1)
    if not MEMORY:
        raise RuntimeError("Memory not set")
    # 直接写入字节，效率极高
    MEMORY.write(STORE, ptr, encoded)
    # 返回写入的字节数和指针，这在 JS 胶水代码中很常见
    return ptr, len(encoded)

# =============================
# 以下是完整的 31 个 __wbg_* 函数
# =============================

def __wbg_buffer_609cc3eee51ed158(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'buffer', None))

def __wbg_call_672a4d21634d4a24(func_handle: int, this_handle: int) -> int:
    func = n(func_handle)
    this = n(this_handle)
    result = func(this)
    return e(result)

def __wbg_call_7cccdd69e0791ae2(func_handle: int, this_handle: int, arg_handle: int) -> int:
    func = n(func_handle)
    this = n(this_handle)
    arg = n(arg_handle)
    result = func(this, arg)
    return e(result)

def __wbg_crypto_574e78ad8b13b65f(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'crypto', None))

def __wbg_getRandomValues_b8f5dbd5f3995a9e(array_handle: int):
    array = n(array_handle)
    if isinstance(array, bytearray):
        for i in range(len(array)):
            array[i] = random.getrandbits(8)

def __wbg_msCrypto_a61aeb35a24c1329(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'msCrypto', None))

def __wbg_new_a12002a7f91c75be(handle: int) -> int:
    array = n(handle)
    return e(bytearray(array))

def __wbg_newnoargs_105ed471475aaf50(ptr: int, length: int) -> int:
    code = F(ptr, length)
    return e(eval(code))  # ⚠️ eval 有安全风险，仅用于演示

def __wbg_newwithbyteoffsetandlength_d97e637ebe145a9a(handle: int, offset: int, length: int) -> int:
    array = n(handle)
    return e(array[offset:offset+length])

def __wbg_newwithlength_a381634e90c276d4(length: int) -> int:
    return e(bytearray(length))

def __wbg_node_905d3e251edff8a2(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'node', None))

def __wbg_process_dc0fbacc7c1c06f7(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'process', None))

def __wbg_randomFillSync_ac0988aba3254290(handle: int, array_handle: int):
    obj = n(handle)
    array = n(array_handle)
    if hasattr(obj, 'randomFillSync'):
        obj.randomFillSync(array)

def __wbg_require_60cc747a6bc5215a():
    raise NotImplementedError("require not supported in Python")

def __wbg_set_65595bdd868b3009(dest_handle: int, src_handle: int, offset: int):
    dest = n(dest_handle)
    src = n(src_handle)
    dest[offset:offset + len(src)] = src

def __wbg_static_accessor_GLOBAL_88a902d13a557d07() -> int:
    return e(globals())

def __wbg_static_accessor_GLOBAL_THIS_56578be7e9f832b0() -> int:
    return e(globals())

def __wbg_static_accessor_SELF_37c5d418e4bf5819() -> int:
    return e(globals())

def __wbg_static_accessor_WINDOW_5de37043a91a9c40() -> int:
    return 0  # null

def __wbg_subarray_aa9065fa9dc5df96(handle: int, start: int, end: int) -> int:
    array = n(handle)
    return e(array[start:end])

def __wbg_versions_c01dfd4722a88165(handle: int) -> int:
    obj = n(handle)
    return e(getattr(obj, 'versions', {"python": "3.11"}))


def __wbindgen_debug_string(ptr: int, handle: int, wasm_malloc):
    """
    将对象的字符串表示写入内存。
    :param ptr: Wasm 提供的用于写回结果的地址。
    :param handle: 要调试的对象的句柄。
    :param wasm_malloc: Wasm 导出的分配器函数。
    """
    obj = n(handle)
    s = str(obj)
    # 使用 Wasm 自己的分配器来获取内存
    s_encoded = s.encode('utf-8')
    s_len = len(s_encoded)
    s_ptr = wasm_malloc(s_len, 1)
    # 将字符串内容写入新分配的内存
    MEMORY.write(STORE, s_ptr, s_encoded)
    # 将字符串的（指针，长度）写回到 Wasm 指定的返回地址 ptr
    MEMORY.write(STORE, ptr, s_ptr.to_bytes(4, 'little', signed=False))
    MEMORY.write(STORE, ptr + 4, s_len.to_bytes(4, 'little', signed=False))
def __wbindgen_is_function(handle: int) -> bool:
    obj = n(handle)
    return callable(obj)

def __wbindgen_is_object(handle: int) -> bool:
    obj = n(handle)
    return isinstance(obj, dict)

def __wbindgen_is_string(handle: int) -> bool:
    obj = n(handle)
    return isinstance(obj, str)

def __wbindgen_is_undefined(handle: int) -> bool:
    obj = n(handle)
    return obj is None

def __wbindgen_memory() -> int:
    if not MEMORY:
        raise RuntimeError("Memory not set")
    return e(MEMORY)

def __wbindgen_object_clone_ref(handle: int) -> int:
    obj = n(handle)
    return e(obj)

def __wbindgen_object_drop_ref(handle: int):
    obj = n(handle)
    # Python 自动管理内存，无需手动 drop

def __wbindgen_string_new(ptr: int, length: int) -> int:
    return e(F(ptr, length))

def __wbindgen_throw(ptr: int, length: int):
    raise Exception(F(ptr, length))