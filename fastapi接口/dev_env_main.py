"""
开发环境
测试并开发api用！
"""
import json
from contextlib import asynccontextmanager
from fastapi_cache.backends.inmemory import InMemoryBackend
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi接口.controller.v1.lotttery_database.bili import GetLotteryData
from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.controller.v1.GeetestDet import GetV3ClickTarget
import fastapi_cdn_host
from fastapi接口.models.common import CommonResponseModel
from starlette.requests import Request
from pydantic import BaseModel as PydanticBaseModel
from fastapi.responses import JSONResponse
from loguru import logger

log = logger.bind(name='fastapi')


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
@asynccontextmanager
async def lifespan(_app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield

app = FastAPI(lifespan=lifespan)
fastapi_cdn_host.patch_docs(app)

app.include_router(ReplySingle.router)
app.include_router(GetLotteryData.router)
app.include_router(GetV3ClickTarget.router)
# @app.middleware("http")
# async def some_middleware(request: Request, call_next):
#     try:
#         request_ip = request.client.host
#         response = await call_next(request)
#         response_body = b""
#         async for chunk in response.body_iterator:
#             response_body += chunk
#         return Response(content=response_body, status_code=response.status_code,
#                         headers=dict(response.headers), media_type=response.media_type)
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             # detail 可以传递任何可以转换成JSON格式的数据
#             detail=str(e),
#             # 自定义新的response header
#         )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, e: Exception):
    return JSONResponse(CommonResponseModel(
        code=500,
        data=str(e),
        msg="服务器错误，请联系管理员"
    ).dict())


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, e: RequestValidationError):
    return JSONResponse(CommonResponseModel(
        code=400,
        data=json.dumps(e.errors()),
        msg='参数错误'
    ).dict())






if __name__ == '__main__':
    uvicorn.run(app='dev_env_main:app', host='127.0.0.1', port=3090)
