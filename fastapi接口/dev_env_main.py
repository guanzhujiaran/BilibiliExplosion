"""
开发环境
测试并开发api用！
"""
from contextlib import asynccontextmanager
from fastapi_cache.backends.inmemory import InMemoryBackend
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache

from fastapi接口.controller.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.controller.v1.background_service import MQController
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
# app.include_router(LotteryData.router)
# app.include_router(GetV3ClickTarget.router)
# app.include_router(MQController.router)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, e: Exception):
    return JSONResponse(CommonResponseModel(
        code=500,
        data=str(e),
        msg="服务器错误，请联系管理员"
    ).model_dump())


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, e: RequestValidationError):
    return JSONResponse(CommonResponseModel(
        code=400,
        data=str(e),
        msg='参数错误'
    ).model_dump())






if __name__ == '__main__':
    uvicorn.run(app='dev_env_main:app', host='127.0.0.1', port=3090)
