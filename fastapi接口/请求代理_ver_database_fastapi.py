# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import io
import os
import sys
import tracemalloc

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
print(f'运行 args:{args}')
if not args.logger:
    print('关闭日志输出')
    logger.remove()
    logger.add(sink=sys.stdout, level="ERROR", colorize=True)
import asyncio
from fastapi接口.log.base_log import myfastapi_logger
from fastapi接口.dao.redisConn import r
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi接口.controller.damo import DamoML
from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.controller.v1.lotttery_database.bili import LotteryData
from fastapi接口.controller.v1.lotttery_database.bili.lottery_statistic import LotteryStatistic
from fastapi接口.controller.v1.GeetestDet import GetV3ClickTarget
from fastapi接口.controller.v1.ip_info import get_ip_info
from fastapi接口.controller.v1.background_service import BackgroundService, MQController
from fastapi接口.models.lottery_database.bili.LotteryDataModels import reserveInfo
from src.monitor import BiliLiveLotRedisManager
from starlette.requests import Request
from starlette.responses import Response
import json
import traceback
from typing import Union
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from github.my_operator.get_others_lot.new_main import get_others_lot_dyn
from grpc获取动态.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from grpc获取动态.src.获取取关对象.GetRmFollowingList import GetRmFollowingListV1
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy
from 获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import lotScrapy
from src.FastApiReturns.SpaceFeedLotService.ToutiaoSpaceFeedLot import ToutiaoSpaceFeedLotService
from utl.pushme.pushme import pushme
import fastapi_cdn_host

# 创建自定义线程池
get_rm_following_list = GetRmFollowingListV1()
zhihu_lotScrapy = lotScrapy()
toutiaoSpaceFeedLotService = ToutiaoSpaceFeedLotService()
req = request_with_proxy()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tracemalloc.start()

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    myfastapi_logger.critical("开启其他服务")  # 提前开启，不导入其他无关的包，减少内存占用
    show_log = False
    back_ground_tasks = BackgroundService.start_background_service(show_log=show_log)
    yield
    # 获取快照并打印内存使用情况
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    myfastapi_logger.critical("[ Top 100 ]")
    for stat in top_stats[:100]:
        myfastapi_logger.critical(stat)
    # 停止 tracemalloc 并取消其他服务
    tracemalloc.stop()
    myfastapi_logger.critical("正在取消其他服务")
    [
        x.cancel() for x in back_ground_tasks
    ]
    await asyncio.gather(*back_ground_tasks)
    myfastapi_logger.critical("其他服务已取消")


app = FastAPI(lifespan=lifespan)
fastapi_cdn_host.patch_docs(app)


@app.get('/v1/get/snapshot', tags=['v1', 'debug'])
def get_snapshot(limit: int = Query(default=10, gt=0, lt=100)):
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    for stat in top_stats[:100]:
        myfastapi_logger.critical(stat)
    return top_stats[:limit]


@app.get('/v1/get/live_lots', description='获取redis中的所有直播相关抽奖信息', )
def v1_get_live_lots(
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

    return _()


# region 测试类

@app.get('/test')
async def app_avaliable_api():
    await asyncio.sleep(1)
    return 'Service is running!'


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

# region 获取抽奖内容接口
@app.post('/lot/upsert_lot_detail')
async def upsert_lot_detail(request_body: dict):
    result = await grpc_sql_helper.upsert_lot_detail(request_body)
    return result


@app.get('/get_others_lot_dyn')
async def api_get_others_lot_dyn():
    myfastapi_logger.error('get_others_lot_dyn 开始获取B站其他用户的动态抽奖！')
    result = await get_others_lot_dyn.get_new_dyn()
    return result


@app.get('/get_others_official_lot_dyn')
async def api_get_others_official_lot_dyn():
    def _():
        myfastapi_logger.error('get_others_lot_dyn 开始获取别人的官方动态抽奖！')
        result = get_others_lot_dyn.get_official_lot_dyn()
        return result

    return await asyncio.to_thread(_)


@app.get('/get_others_big_lot')
async def api_get_others_big_lot():
    myfastapi_logger.error('get_others_lot_dyn 开始获取别人的大奖！')
    result = await asyncio.to_thread(get_others_lot_dyn.get_unignore_Big_lot_dyn)
    return result


@app.get('/get_others_big_reserve')
async def api_get_others_big_reserve() -> list[reserveInfo]:
    myfastapi_logger.error('get_others_lot_dyn 开始获取重要的预约抽奖！')
    result = await get_others_lot_dyn.get_unignore_reserve_lot_space()
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
    result = result if result else []
    pushme(f'获取到头条抽奖{len(result)}条', '\n'.join(result))
    return result


# endregion
app.include_router(DamoML.router)
app.include_router(ReplySingle.router)
app.include_router(LotteryData.router)
app.include_router(LotteryStatistic.router)
app.include_router(GetV3ClickTarget.router)
app.include_router(get_ip_info.router)
app.include_router(BackgroundService.router)
app.include_router(MQController.router)


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
        myfastapi_logger.error(e)
        myfastapi_logger.exception(e)
        pushme(f'fastapi请求异常！{request.url}{str(e)}', traceback.format_exc())
        raise HTTPException(
            status_code=500,
            # detail 可以传递任何可以转换成JSON格式的数据
            detail=str(e),
            # 自定义新的response header
        )


if __name__ == '__main__':
    try:
        uvicorn.run(
            # '请求代理_ver_database_fastapi:app',
            app,
            # host="",
            # If host is an empty string or None, all interfaces are assumed and a list of multiple sockets will be returned (most likely one for IPv4 and another one for IPv6).
            host="0.0.0.0",
            port=23333,
        )
    except Exception as e:
        myfastapi_logger.exception(e)
        pushme(f'fastapi请求异常！{str(e)}', traceback.format_exc())
        raise e
