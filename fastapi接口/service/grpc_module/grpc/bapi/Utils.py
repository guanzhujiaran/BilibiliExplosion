import hashlib
import time
import urllib.parse
import uuid
import asyncio
from typing import Callable
from fastapi接口.log.base_log import bapi_log
from fastapi接口.service.grpc_module.Models.CustomRequestErrorModel import RequestKnownError
from fastapi接口.service.grpc_module.grpc.bapi.Constants import APP_KEY, APP_SEC

def appsign(params: dict, appkey=APP_KEY, appsec=APP_SEC) -> dict:
    """
    为请求参数进行 APP 签名
    """
    params.update({"appkey": appkey})
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode(params)
    sign = hashlib.md5((query + appsec).encode()).hexdigest()
    params.update({"sign": sign})
    return params

def gen_trace_id() -> str:
    """
    生成 Bilibili 请求追踪 ID
    """
    trace_id_uid = str(uuid.uuid4()).replace("-", "")[0:26].lower()
    trace_id_hex = hex(int(round(time.time()) / 256)).lower().replace("0x", "")
    return f"{trace_id_uid}{trace_id_hex}:{trace_id_uid[-10:]}{trace_id_hex}:0:0"

def request_wrapper(func: Callable):
    """
    一个通用的请求重试装饰器
    """
    async def wrapper(*args, **kwargs):
        while True:
            try:
                resp_dict = await func(*args, **kwargs)
                return resp_dict
            except RequestKnownError:
                # 已知可忽略的错误，直接重试
                continue
            except Exception as e:
                bapi_log.error(f"方法：【{func.__name__}】 请求失败！\n{e}")
                await asyncio.sleep(10)
    return wrapper