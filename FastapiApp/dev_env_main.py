"""
开发环境
测试并开发api用！
"""
from contextlib import asynccontextmanager

import fastapi_cdn_host
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from loguru import logger
from pydantic import BaseModel as PydanticBaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from controller.v1.samsClub import samsClubController
# from controller.v1.lotttery_database.bili.zhuanlan import zhuanlanController
# from controller.damo import DamoML
from models.common import CommonResponseModel

log = logger.bind(name='fastapi')


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    # back_ground_tasks = BackgroundService.start_background_service(show_log=True)
    # yield
    # [
    #     x.cancel() for x in back_ground_tasks
    # ]
    # await asyncio_gather(*back_ground_tasks)
    yield


app = FastAPI(
    lifespan=lifespan,

)

fastapi_cdn_host.patch_docs(app)
# app.include_router(zhuanlanController.router)
# app.include_router(DamoML.router)
app.include_router(samsClubController.router)


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
    uvicorn.run(app='dev_env_main:app', host='127.0.0.1', port=3090, loop='uvloop')
