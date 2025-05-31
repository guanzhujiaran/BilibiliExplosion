"""
开发环境
测试并开发api用！
"""
import asyncio
from contextlib import asynccontextmanager
import objgraph
from fastapi_cache.backends.inmemory import InMemoryBackend
import uvicorn
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi接口.controller.v1.lotttery_database.bili import LotteryData
import fastapi_cdn_host
from fastapi接口.models.common import CommonResponseModel
from pydantic import BaseModel as PydanticBaseModel
from loguru import logger
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import  JSONResponse
log = logger.bind(name='fastapi')


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
@asynccontextmanager
async def lifespan(_app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield

app = FastAPI(
    lifespan=lifespan,

              )
fastapi_cdn_host.patch_docs(app)

app.include_router(LotteryData.router)
@app.get('/memory_objgraph',)
async def memory_objgraph(limit:int=50):
    common_types = await asyncio.to_thread(objgraph.most_common_types, limit=limit)
    return [{"type": item[0], "count": item[1]} for item in common_types]

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
