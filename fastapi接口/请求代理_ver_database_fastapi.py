# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import pydantic.main
import sys

import asyncio
import json
import time
import traceback
from typing import Union
import redis
import uvicorn
from fastapi import Query, Body, FastAPI
from loguru import logger
from pydantic import BaseModel
from github.my_operator.get_others_lot.new_main import GET_OTHERS_LOT_DYN
from grpc获取动态.grpc.grpc_api import BiliGrpc
from grpc获取动态.src.SqlHelper import SQLHelper
from grpc获取动态.src.获取取关对象.GetRmFollowingList import GetRmFollowingListV1
from utl.代理.请求代理_ver_database import request_with_proxy
from 获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import lotScrapy
from src.FastApiReturns.SpaceFeedLotService.ToutiaoSpaceFeedLot import ToutiaoSpaceFeedLotService

# 创建自定义线程池
get_rm_following_list = GetRmFollowingListV1()
zhihu_lotScrapy = lotScrapy()
grpc_sql_helper = SQLHelper()
grpc_api = BiliGrpc()
toutiaoSpaceFeedLotService = ToutiaoSpaceFeedLotService()
req = request_with_proxy()
r = redis.Redis(host='localhost', port=11451, db=0)  # 直播抽奖数据
r1 = redis.Redis(host='localhost', port=11451, db=1)  # 情感分析数据
app = FastAPI()
# logger.remove()

myfastapi_logger = logger.bind(user=__name__ + 'fastapi')
myfastapi_logger.add(sys.stderr, level="INFO",
                     filter=lambda record: record["extra"].get('user') == __name__ + "fastapi")


@app.get('/v1/get/live_lots', description='获取redis中的所有直播相关抽奖信息')
def v1_get_live_lots():
    ret_list = []
    for k in r.keys():
        res = r.get(k)
        if res:
            ret_list.append(json.loads(res))
    return ret_list


# region 测试类

@app.get('/test')
async def app_avaliable_api():
    await asyncio.sleep(1)
    return 'Service is running!'


# endregion

# region 魔搭社区的各种ai模型
@app.get('/damo/semantic')
def semantic(data=Query(default=None)):
    timeout = 0
    while 1:
        if timeout > 11:
            return True
        if data:
            res = json.loads(r1.get(data)).get(data, None) if r1.get(data) else None
            if res != None:
                return res
            else:
                r1.setex(data, 180, json.dumps({data: None}))
        else:
            return False
        time.sleep(1)
        timeout += 1


# endregion

# region 代理类方法的请求接口
@app.post('/request_with_proxy')
async def request_with_proxy_api(  # 改为了并发模式
        # request: fastapi.Request
        request: dict
):
    try:
        result = await req.request_with_proxy(request)
        return result
    except Exception as e:
        myfastapi_logger.error(traceback.format_exc())
        myfastapi_logger.error(request)


# region grpc代理数据库的操作方法
@app.get('/get_one_rand_proxy')
async def get_one_rand_proxy():
    proxy = await req.get_one_rand_proxy()
    return proxy


@app.get('/grpc/get_one_rand_grpc_proxy')
async def get_one_rand_grpc_proxy():
    proxy = await req.get_one_rand_grpc_proxy()
    return proxy


@app.post('/grpc/upsert_grpc_proxy_status')
async def upsert_grpc_proxy_status(request_body: dict):
    await req.upsert_grpc_proxy_status(request_body)
    return True


@app.get('/grpc/get_grpc_proxy_by_ip')  # 通过ip获取grpc的代理
async def grpc_get_grpc_proxy_by_ip(ip: str):
    result = await req.get_grpc_proxy_by_ip(ip)
    return result


# endregion


# region GRPC_API请求方法


@app.post('/grpc/grpc_api_get_DynDetails')
async def grpc_api_get_DynDetails(request_body: list[int]):
    result = await grpc_api.grpc_api_get_DynDetails(request_body)
    return result


@app.post('/grpc/grpc_get_dynamic_detail_by_type_and_rid')
async def grpc_get_dynamic_detail_by_type_and_rid(rid: Union[int, str] = Body(..., title='动态rid', embed=True),
                                                  dynamic_type: int = Body(2, title='动态类型', embed=True), ):
    result = await grpc_api.grpc_get_dynamic_detail_by_type_and_rid(rid, dynamic_type)
    return result


class grpcGetSpaceDynByUid(BaseModel):
    uid: Union[str, int]
    history_offset: str = ''
    page: int = 1


@app.post('/grpc/grpc_get_space_dyn_by_uid')
async def grpc_get_space_dyn_by_uid(request: grpcGetSpaceDynByUid):
    result = await grpc_api.grpc_get_space_dyn_by_uid(request.uid, request.history_offset, request.page)
    return result


# endregion

# region 基于Grpc api的功能实现
@app.post('/v1/post/RmFollowingList')
async def v1_post_rm_following_list(data: list[Union[int, str]]):
    """
    取关接口
    :param data: list[int] 关注列表 直接传列表即可
    :return:
    """
    result = await get_rm_following_list.main(data)
    return result


# endregion


# endregion


# region 获取抽奖内容接口
@app.post('/lot/upsert_lot_detail')
def upsert_lot_detail(request_body: dict):
    result = grpc_sql_helper.upsert_lot_detail(request_body)
    return result


@app.get('/get_others_lot_dyn')
async def api_get_others_lot_dyn():
    myfastapi_logger.debug('get_others_lot_dyn 开始获取别人的动态抽奖！')
    get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
    result = await get_OTHERS_LOT_DYN.get_new_dyn()
    return result


@app.get('/get_others_official_lot_dyn')
def api_get_others_official_lot_dyn():
    myfastapi_logger.debug('get_others_lot_dyn 开始获取别人的官方动态抽奖！')
    get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
    result = get_OTHERS_LOT_DYN.get_official_lot_dyn()
    return result


@app.get('/get_others_big_lot')
def api_get_others_big_lot():
    myfastapi_logger.debug('get_others_lot_dyn 开始获取别人的大奖！')
    get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
    result = get_OTHERS_LOT_DYN.get_unignore_Big_lot_dyn()
    return result


class reserveInfo(pydantic.BaseModel):
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    etime: int  # 结束时间(秒)
    lottery_prize_info: str  # 奖品名称
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在


@app.get('/get_others_big_reserve')
async def api_get_others_big_reserve() -> list[reserveInfo]:
    myfastapi_logger.debug('get_others_lot_dyn 开始获取重要的预约抽奖！')
    get_OTHERS_LOT_DYN = GET_OTHERS_LOT_DYN()
    result =await get_OTHERS_LOT_DYN.get_unignore_reserve_lot_space()
    reserveInfos = []
    for i in result:# 对df的每一行数据访问
        reserve_info = reserveInfo(
            reserve_url=f'https://space.bilibili.com/{str(i.upmid)}/dynamic',
            etime=i.etime,
            lottery_prize_info=i.text,
            jump_url=i.jumpUrl,
            reserve_sid=i.sid,
            available=True
        )
        reserveInfos.append(reserve_info)
    return reserveInfos


@app.get('/zhihu/get_others_lot_pins')
async def zhuhu_avaliable_api():
    resp = await zhihu_lotScrapy.api_get_all_pins()
    return resp


@app.get('/toutiao/get_others_lot_ids')
async def toutiao_get_others_lot_ids():
    return await toutiaoSpaceFeedLotService.main()


# endregion

if __name__ == '__main__':
    uvicorn.run(
        # '请求代理_ver_database_fastapi:app',
        app,
        host="0.0.0.0",
        port=23333,
    )
