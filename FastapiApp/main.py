# -*- coding: utf-8 -*-
import time
import asyncio
import uvloop
import sys

if not sys.platform.startswith("win"):
    uvloop.install()
elif sys.platform.startswith("windows"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import os
import traceback
import fastapi_cdn_host
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from loguru import logger
from starlette.requests import Request
from starlette.responses import Response

current_dir = os.path.dirname(__file__)
grpc_dir = os.path.join(current_dir, "Service/GrpcModule/Grpc/GrpcProto")
sys.path.append(grpc_dir)
from CONFIG import settings

logger.info(f"运行 settings:{settings}")
if not settings.SHOW_LOG:
    logger.info("关闭日志输出")
    logger.remove()
    logger.add(sink=sys.stdout, level="ERROR", colorize=True)

from log.base_log import myfastapi_logger
from Utils.推送.PushMe import a_pushme
from Utils.FastAPI.FastapiLifespan import life_span
from controller.v1.lotttery_database.bili import LotteryData
from controller.v1.lotttery_database.bili.lottery_statistic import LotteryStatistic
from controller.v1.ip_info import get_ip_info
from controller.v1.background_service import BackgroundServiceController
from controller.common import CommonRouter
from controller.v1.mq import mq_controller as MQController
from controller.v1.mq.rpc_info_controller import router as RpcInfoRouter
from controller.v1.samsClub import samsClubController
from controller.v1.captcha import captchaController
from Models.common import CommonResponseModel
from controller.v1.lotttery_database.bili.zhuanlan import zhuanlanController

app = FastAPI(lifespan=life_span)
fastapi_cdn_host.patch_docs(app)
app.include_router(LotteryData.router)
app.include_router(LotteryStatistic.router)
app.include_router(get_ip_info.router)
app.include_router(BackgroundServiceController.router)
app.include_router(CommonRouter.router)
app.include_router(MQController.router)
app.include_router(RpcInfoRouter)
app.include_router(captchaController.router)
app.include_router(samsClubController.router)
app.include_router(zhuanlanController.router)
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


@app.middleware("http")
async def global_middleware(request: Request, call_next):
    request_ip = request.client.host if request.client else "unknown"
    start_ts = time.time()
    try:
        response = await call_next(request)
        # 可选：仅在调试模式下返回错误堆栈
        if hasattr(app, "debug"):
            end_ts = time.time()
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            myfastapi_logger.info(
                f"请求耗时: {end_ts - start_ts:.4f}秒\n"
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
                media_type=response.media_type,
            )
        else:
            # 在非调试模式下，直接返回原始响应
            return response

    except Exception as err:
        error_detail = {
            "error": str(err),
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request_ip,
        }
        myfastapi_logger.exception(f"FastAPI请求异常: {error_detail}")
        err_title = str(err).replace("\n", "")
        await a_pushme(
            f"FastAPI请求异常！URL: {request.url}\n错误详情: {err_title}",
            traceback.format_exc(),
            None,
        )

        raise HTTPException(
            status_code=400,
            detail=CommonResponseModel(code=400, msg=str(err)),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=23333)
