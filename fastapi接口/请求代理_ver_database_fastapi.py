# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import asyncio

import fastapi
import uvicorn
from fastapi import Query
from loguru import logger

from utl.代理.请求代理_ver_database import request_with_proxy
from grpc获取动态.src.SqlHelper import SQLHelper
from github.my_operator.bili_upload.get_bili_upload import GET_OTHERS_LOT_DYN
from 获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import lotScrapy
from utl.机器学习.情感分析.情感分析 import judge_semantic_cls

zhihu_lotScrapy = lotScrapy()
get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
grpc_sql_helper = SQLHelper()
app = fastapi.FastAPI()
req = request_with_proxy()


@app.get('/test/')
def app_avaliable_api():
    return 'Service is running!'


# region 魔搭社区的各种ai模型
@app.get('/damo/semantic/')
def semantic(data=Query(default=None)):
    try:
        if data:
            return judge_semantic_cls(data)
        else:
            return False
    except Exception as e:
        logger.error(e)
        return False


# endregion


# region 代理类方法的请求接口
@app.post('/request_with_proxy/')
async def request_with_proxy_api(request: fastapi.Request):
    request_body = await request.json()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, req.request_with_proxy, request_body)
    return result


@app.get('/get_one_rand_proxy/')
def get_one_rand_proxy():
    proxy = req.get_one_rand_proxy()
    return proxy


@app.get('/grpc/get_one_rand_grpc_proxy/')
def get_one_rand_grpc_proxy():
    proxy = req.get_one_rand_grpc_proxy()
    return proxy


@app.post('/grpc/upsert_grpc_proxy_status/')
async def upsert_grpc_proxy_status(request: fastapi.Request):
    request_body = await request.json()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, req.upsert_grpc_proxy_status, request_body)
    return result


# endregion

@app.post('/lot/upsert_lot_detail/')
async def upsert_grpc_proxy_status(request: fastapi.Request):
    request_body = await request.json()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, grpc_sql_helper.upsert_lot_detail, request_body)
    return result


@app.get('/get_others_lot_dyn/')
def app_avaliable_api():
    return get_OTHERS_LOT_DYN.get_new_dyn()


@app.get('/zhihu/get_others_lot_pins/')
def zhuhu_avaliable_api():
    return zhihu_lotScrapy.api_get_all_pins()


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=23333)  # worker就是多进程，没意思，不用
