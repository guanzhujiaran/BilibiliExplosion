# -*- coding: utf-8 -*-
# 自己本地的fastapi封装接口服务 这是一个sqlite3数据库的接口，使用proxy相关操作
import io
import os
import sys
import objgraph
import asyncio
from loguru import logger
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
import fastapi_cdn_host
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import Response
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))  # 将CONFIG导入
current_dir = os.path.dirname(__file__)
grpc_dir = os.path.join(current_dir, 'service/grpc_module/grpc/grpc_proto')
sys.path.append(grpc_dir)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from fastapi接口.utils.argParse import parse

args = parse()
print(f'运行 args:{args}')
if not args.logger:
    print('关闭日志输出')
    logger.remove()
    logger.add(sink=sys.stdout, level="ERROR", colorize=True)
if sys.platform.startswith('windows'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # 祖传代码不可删，windows必须替换掉selector，不然跑一半就停了
else:
    import uvloop

    print('使用uvloop')
    uvloop.install()
from fastapi接口.log.base_log import myfastapi_logger
from utl.pushme.pushme import pushme
from fastapi接口.utils.Common import GLOBAL_SCHEDULER
from fastapi接口.controller.damo import DamoML
from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.controller.v1.lotttery_database.bili import LotteryData
from fastapi接口.controller.v1.lotttery_database.bili.lottery_statistic import LotteryStatistic
from fastapi接口.controller.v1.ip_info import get_ip_info
from fastapi接口.controller.v1.background_service import BackgroundService
from fastapi接口.controller.common import CommonRouter


@asynccontextmanager
async def lifespan(_app: FastAPI):
    myfastapi_logger.critical("开启其他服务")  # 提前开启，不导入其他无关的包，减少内存占用
    GLOBAL_SCHEDULER.start()
    show_log = False
    back_ground_tasks = BackgroundService.start_background_service(show_log=show_log)
    yield
    myfastapi_logger.critical("正在取消其他服务")
    [
        x.cancel() for x in back_ground_tasks
    ]
    await asyncio.gather(*back_ground_tasks, return_exceptions=True)
    myfastapi_logger.critical("其他服务已取消")


app = FastAPI(lifespan=lifespan, debug=True)
fastapi_cdn_host.patch_docs(app)
app.include_router(DamoML.router)
app.include_router(ReplySingle.router)
app.include_router(LotteryData.router)
app.include_router(LotteryStatistic.router)
app.include_router(get_ip_info.router)
app.include_router(BackgroundService.router)
app.include_router(CommonRouter.router)
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


@app.get('/memory_objgraph', )
async def memory_objgraph(limit: int = 50):
    common_types = await asyncio.to_thread(objgraph.most_common_types, limit=limit)
    return [{"type": item[0], "count": item[1]} for item in common_types]


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
        myfastapi_logger.exception(f"FastAPI请求异常: {error_detail}")
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
    )
