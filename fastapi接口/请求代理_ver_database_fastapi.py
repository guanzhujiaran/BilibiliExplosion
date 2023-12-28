# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import asyncio
import json
import traceback
from typing import Union

import fastapi
import redis
import uvicorn
from fastapi import Query, HTTPException
from loguru import logger
from pydantic import BaseModel

from utl.代理.请求代理_ver_database import request_with_proxy
from grpc获取动态.src.SqlHelper import SQLHelper
from github.my_operator.bili_upload.get_bili_upload import GET_OTHERS_LOT_DYN
from 获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import lotScrapy
from utl.机器学习.情感分析.情感分析 import judge_semantic_cls
from grpc获取动态.grpc.grpc_api import BiliGrpc
from grpc获取动态.src.获取取关对象.GetRmFollowingList import GetRmFollowingListV1

get_rm_following_list = GetRmFollowingListV1()
zhihu_lotScrapy = lotScrapy()
get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
grpc_sql_helper = SQLHelper()
grpc_api = BiliGrpc()
app = fastapi.FastAPI()
req = request_with_proxy()
r = redis.Redis(host='localhost', port=11451, db=0)


@app.get('/v1/get/live_lots/',description='获取redis中的所有直播相关抽奖信息')
def v1_get_live_lots():
    ret_list = []
    for k in r.keys():
        res = r.get(k)
        if res:
            ret_list.append(json.loads(res))
    return ret_list


# region 测试类
@app.get('/test/')
def app_avaliable_api():
    return 'Service is running!'


# endregion

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
        return True


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


# region GRPC_API请求方法


@app.post('/grpc/grpc_api_get_DynDetails/')
async def grpc_api_get_DynDetails(request: fastapi.Request):
    request_body = await request.json()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, grpc_api.grpc_api_get_DynDetails, request_body)
    return result


@app.post('/grpc/grpc_get_dynamic_detail_by_type_and_rid/')
async def grpc_get_dynamic_detail_by_type_and_rid(request: fastapi.Request):
    request_body = await request.json()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, grpc_api.grpc_get_dynamic_detail_by_type_and_rid, request_body)
    return result


class grpcGetSpaceDynByUid(BaseModel):
    uid: Union[str, int]
    history_offset: str = ''
    page: int = 1


@app.post('/grpc/grpc_get_space_dyn_by_uid/')
def grpc_get_space_dyn_by_uid(request: grpcGetSpaceDynByUid):
    result = grpc_api.grpc_get_space_dyn_by_uid(request.uid, request.history_offset, request.page)
    return result


# endregion

# region 基于Grpc api的功能实现
@app.post('/v1/post/RmFollowingList/')
def v1_post_rm_following_list(data: list[Union[int, str]]):
    """
    取关接口
    :param data: list[int] 关注列表 直接传列表即可
    :return:
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  # 使用新的协程，防止阻塞
        result = loop.run_until_complete(get_rm_following_list.main(data))
        return result
    except:
        traceback.print_exc()
        raise HTTPException(status_code=114514,detail=traceback.format_exc())


# endregion


# endregion


# region 获取抽奖内容接口
@app.post('/lot/upsert_lot_detail/')
async def upsert_lot_detail(request: fastapi.Request):
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


# endregion


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=23333)  # worker就是多进程，没意思，不用
