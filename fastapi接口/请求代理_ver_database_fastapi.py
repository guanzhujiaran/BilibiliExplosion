# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import io
import os
import sys

import objgraph

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
from starlette.requests import Request
from starlette.responses import Response
import traceback
from fastapi接口.log.base_log import myfastapi_logger
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import fastapi_cdn_host
from fastapi import FastAPI, HTTPException
from utl.pushme.pushme import pushme

@asynccontextmanager
async def lifespan(_app: FastAPI):
    from fastapi接口.controller.damo import DamoML
    from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
    from fastapi接口.controller.v1.lotttery_database.bili import LotteryData
    from fastapi接口.controller.v1.lotttery_database.bili.lottery_statistic import LotteryStatistic
    from fastapi接口.controller.v1.GeetestDet import GetV3ClickTarget
    from fastapi接口.controller.v1.ip_info import get_ip_info
    from fastapi接口.controller.v1.background_service import BackgroundService, MQController
    from fastapi接口.controller.common import CommonRouter

    _app.include_router(DamoML.router)
    _app.include_router(ReplySingle.router)
    _app.include_router(LotteryData.router)
    _app.include_router(LotteryStatistic.router)
    _app.include_router(GetV3ClickTarget.router)
    _app.include_router(get_ip_info.router)
    _app.include_router(BackgroundService.router)
    _app.include_router(MQController.router)
    _app.include_router(CommonRouter.router)

    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    myfastapi_logger.critical("开启其他服务")  # 提前开启，不导入其他无关的包，减少内存占用
    show_log = False
    back_ground_tasks = BackgroundService.start_background_service(show_log=show_log)
    yield
    myfastapi_logger.critical("正在取消其他服务")
    [
        x.cancel() for x in back_ground_tasks
    ]
    await asyncio.gather(*back_ground_tasks)
    myfastapi_logger.critical("其他服务已取消")


app = FastAPI(lifespan=lifespan)
fastapi_cdn_host.patch_docs(app)

@app.get('/memory_objgraph',)
async def memory_objgraph(limit=50):
    return await asyncio.to_thread(objgraph.show_most_common_types, limit=limit)

@app.middleware("http")
async def global_middleware(request: Request, call_next):
    request_ip = request.client.host if request.client else "unknown"
    try:
        response = await call_next(request)
        # 可选：仅在调试模式下记录响应体
        if app.debug:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            myfastapi_logger.info(
                f"请求IP: {request_ip}\n"
                f"请求方法: {request.method}\n"
                f"请求路径: {request.url.path}\n"
                f"响应状态码: {response.status_code}\n"
                f"响应体: {response_body.decode(errors='replace')}"
            )
            # 构造新的响应对象，使用原始的响应体迭代器
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        else:
            # 在非调试模式下，直接返回原始响应
            return response

    except Exception as err:
        error_detail = {
            "error": str(err),
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request_ip
        }
        myfastapi_logger.error(f"FastAPI请求异常: {error_detail}")
        myfastapi_logger.exception(err)
        err_title = str(err).replace("\n", "")
        await asyncio.to_thread(
            pushme,
            f'FastAPI请求异常！URL: {request.url}\n错误详情: {err_title}',
            traceback.format_exc(),
            None
        )

        raise HTTPException(
            status_code=500,
            detail=str(err),
        )


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        # host="",
        # If host is an empty string or None, all interfaces are assumed and a list of multiple sockets will be returned (most likely one for IPv4 and another one for IPv6).
        host="0.0.0.0",
        port=23333,
        loop='asyncio'
    )
