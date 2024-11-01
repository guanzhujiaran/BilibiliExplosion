# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import io
import os
import sys
from threading import Thread

sys.path.append(os.path.dirname(os.path.join(__file__, '../../')))  # 将CONFIG导入
from CONFIG import CONFIG

sys.path.extend([
    x.value for x in CONFIG.project_path
])
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from loguru import logger
import argparse

parser = argparse.ArgumentParser(
    prog='lot_fastapi',  # 程序名
    description='lottery info fastapi backend',  # 描述
)
parser.add_argument('-l', '--logger', type=int, default=1, choices=[0, 1])
args = parser.parse_args()
print(f'args:{args}')
if not args.logger:
    logger.remove()
    logger.add(level="ERROR",sink=print)
myfastapi_logger = logger.bind(user='fastapi')
myfastapi_logger.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_fastapi_log.log"),
                     level="WARNING",
                     encoding="utf-8",
                     enqueue=True,
                     rotation="500MB",
                     compression="zip",
                     retention="15 days",
                     filter=lambda record: record["extra"].get('user') == 'fastapi',
                     )
# logger.add(sys.stderr, level="ERROR", filter=lambda record: record["extra"].get('user') =="MYREQ")
from fastapi接口.dao.redisConn import r, r1
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.controller.v1.lotttery_database.bili import GetLotteryData
from fastapi接口.controller.v1.GeetestDet import GetV3ClickTarget
from fastapi接口.controller.v1.ip_info import get_ip_info
from fastapi接口.models.lottery_database.bili.LotteryDataModels import reserveInfo
from src.monitor import BiliLiveLotRedisManager
from starlette.requests import Request
from starlette.responses import Response
import asyncio
import json
import time
import traceback
from typing import Union
import uvicorn
from fastapi import Query, Body, FastAPI, HTTPException
from pydantic import BaseModel
from github.my_operator.get_others_lot.new_main import GET_OTHERS_LOT_DYN
from grpc获取动态.grpc.grpc_api import BiliGrpc
from grpc获取动态.src.SqlHelper import SQLHelper
from grpc获取动态.src.获取取关对象.GetRmFollowingList import GetRmFollowingListV1
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy
from 获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import lotScrapy
from src.FastApiReturns.SpaceFeedLotService.ToutiaoSpaceFeedLot import ToutiaoSpaceFeedLotService
from utl.pushme.pushme import pushme
import fastapi_cdn_host

# 创建自定义线程池
get_rm_following_list = GetRmFollowingListV1()
zhihu_lotScrapy = lotScrapy()
grpc_sql_helper = SQLHelper()
grpc_api = BiliGrpc()
toutiaoSpaceFeedLotService = ToutiaoSpaceFeedLotService()
req = request_with_proxy()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    # from apscheduler.schedulers.background import BackgroundScheduler
    # scheduler = BackgroundScheduler()
    # from fastapi接口.scripts.start_other_service import start_scripts
    myfastapi_logger.info("开启其他服务")  # 提前开启，不导入其他无关的包，减少内存占用
    # __t = Thread(target=start_scripts, daemon=False)
    # __t.start()
    # scheduler.add_job(func=start_scripts, )
    # scheduler.start()
    # myfastapi_logger.info("其他服务已启动")

    ### 异步
    show_log = False
    back_ground_tasks = []

    from grpc获取动态.src.监控up动态.bili_dynamic_monitor import monitor
    _ = monitor()
    back_ground_tasks.append(asyncio.create_task(_.main(show_log=show_log)))

    from opus新版官方抽奖.转发抽奖.定时获取所有动态以及发布充电和官方抽奖专栏 import \
        async_schedule_get_official_lot_main
    back_ground_tasks.append(asyncio.create_task(async_schedule_get_official_lot_main(show_log=show_log)))

    from opus新版官方抽奖.预约抽奖.etc.schedule_get_reserve_lot import async_schedule_get_reserve_lot_main
    back_ground_tasks.append(asyncio.create_task(async_schedule_get_reserve_lot_main(show_log=show_log)))

    from opus新版官方抽奖.活动抽奖.定时获取话题抽奖 import async_schedule_get_topic_lot_main
    back_ground_tasks.append(asyncio.create_task(async_schedule_get_topic_lot_main(show_log=show_log)))

    from fastapi接口.scripts.光猫ip.监控本地ip地址变化 import async_monitor_ipv6_address_changes
    back_ground_tasks.append(asyncio.create_task(async_monitor_ipv6_address_changes()))

    from src.monitor import AsyncMonitor
    m = AsyncMonitor()
    back_ground_tasks.append(asyncio.create_task(m.async_main(ShowLog=show_log)))

    from grpc获取动态.Utils.MQClient.VoucherMQClient import VoucherMQClient
    back_ground_tasks.extend([
        asyncio.create_task(asyncio.to_thread(VoucherMQClient().start_voucher_break_consumer)) for _ in range(5)
    ])

    yield

    await asyncio.gather(*back_ground_tasks)


app = FastAPI(lifespan=lifespan)
fastapi_cdn_host.patch_docs(app)


@app.get('/v1/get/live_lots', description='获取redis中的所有直播相关抽奖信息', )
async def v1_get_live_lots(
        get_all: bool = False
):
    def _():
        ret_list = []
        if get_all:
            return json.loads(r.get(BiliLiveLotRedisManager.RedisMap.all_live_lot.value))
        for k in r.keys():
            if k == BiliLiveLotRedisManager.RedisMap.all_live_lot.value.encode('utf-8'):
                continue
            if b'Lock' in k:
                continue
            res = r.get(k)
            myfastapi_logger.info(f'获取到直播抽奖信息：【{k}:{res}】')
            if res:
                ret_list.append(json.loads(res))
        return ret_list

    return await asyncio.to_thread(_)


# region 测试类

@app.get('/test')
async def app_avaliable_api():
    await asyncio.sleep(1)
    return 'Service is running!'


# endregion

# region 魔搭社区的各种ai模型
@app.get('/damo/semantic')
async def semantic(data=Query(default=None)):
    def _():
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

    return await asyncio.to_thread(_)


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
        myfastapi_logger.exception(e)


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
    取关接口 调用的是b站appp端的grpc协议接口，没那么容易被风控
    :param data: list[int] 关注列表 直接传列表即可
    :return:
    """
    result = await get_rm_following_list.main(data)
    return result


# endregion


# endregion


# region 获取抽奖内容接口
@app.post('/lot/upsert_lot_detail')
async def upsert_lot_detail(request_body: dict):
    result = await asyncio.to_thread(grpc_sql_helper.upsert_lot_detail, request_body)
    return result


@app.get('/get_others_lot_dyn')
async def api_get_others_lot_dyn():
    myfastapi_logger.error('get_others_lot_dyn 开始获取B站其他用户的动态抽奖！')
    get_other_lot_dyn = GET_OTHERS_LOT_DYN()
    result = await get_other_lot_dyn.get_new_dyn()
    return result


@app.get('/get_others_official_lot_dyn')
async def api_get_others_official_lot_dyn():
    def _():
        myfastapi_logger.error('get_others_lot_dyn 开始获取别人的官方动态抽奖！')
        get_other_lot_dyn = GET_OTHERS_LOT_DYN()
        result = get_other_lot_dyn.get_official_lot_dyn()
        return result

    return await asyncio.to_thread(_)


@app.get('/get_others_big_lot')
async def api_get_others_big_lot():
    myfastapi_logger.error('get_others_lot_dyn 开始获取别人的大奖！')
    get_other_lot_dyn = GET_OTHERS_LOT_DYN()
    result = await asyncio.to_thread(get_other_lot_dyn.get_unignore_Big_lot_dyn)
    return result


@app.get('/get_others_big_reserve')
async def api_get_others_big_reserve() -> list[reserveInfo]:
    myfastapi_logger.error('get_others_lot_dyn 开始获取重要的预约抽奖！')
    get_other_lot_dyn = GET_OTHERS_LOT_DYN()
    result = await get_other_lot_dyn.get_unignore_reserve_lot_space()
    reserveInfos = []
    for i in result:  # 对df的每一行数据访问
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
    myfastapi_logger.info('开始获取zhihu抽奖内容')
    resp = await zhihu_lotScrapy.api_get_all_pins()
    pushme(f'获取到知乎抽奖{len(resp)}条', '\n'.join(resp))
    return resp


@app.get('/toutiao/get_others_lot_ids')
async def toutiao_get_others_lot_ids():
    myfastapi_logger.info('开始获取toutiao抽奖内容')
    result = await toutiaoSpaceFeedLotService.main()
    pushme(f'获取到头条抽奖{len(result)}条', '\n'.join(result))
    return result


# endregion

app.include_router(ReplySingle.router)
app.include_router(GetLotteryData.router)
app.include_router(GetV3ClickTarget.router)
app.include_router(get_ip_info.router)


@app.middleware("http")
async def some_middleware(request: Request, call_next):
    try:
        request_ip = request.client.host
        response = await call_next(request)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        myfastapi_logger.info(f"请求ip：{request_ip}\n{response_body.decode()}")
        return Response(content=response_body, status_code=response.status_code,
                        headers=dict(response.headers), media_type=response.media_type)
    except Exception as e:
        myfastapi_logger.exception(e)
        if e.__str__() != 'No OpenAiClient is available' and e.__str__() != "Error code: 429 - {'error': {'message': '免费API限制每日200次请求，请00:00后再试，如有更多需求，请访问 https://buyca.shop 购买付费API。The free account is limited to 200 requests per day. Please try again after 00:00 the next day. If you have additional requirements, please visit https://buyca.shop to purchase a premium key.', 'type': 'chatanywhere_error', 'param': None, 'code': '429 TOO_MANY_REQUESTS'}}":
            pushme(f'fastapi请求异常！{str(e)}', traceback.format_exc())
        raise HTTPException(
            status_code=500,
            # detail 可以传递任何可以转换成JSON格式的数据
            detail=str(e),
            # 自定义新的response header
        )


if __name__ == '__main__':
    uvicorn.run(
        # '请求代理_ver_database_fastapi:app',
        app,
        host="",
        # If host is an empty string or None, all interfaces are assumed and a list of multiple sockets will be returned (most likely one for IPv4 and another one for IPv6).
        port=23333,
    )
