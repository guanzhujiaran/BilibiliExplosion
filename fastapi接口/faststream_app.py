import asyncio
import io
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
sys.path.append(os.path.dirname(os.path.join(__file__, '../../')))  # 将CONFIG导入
current_dir = os.path.dirname(__file__)
grpc_dir = os.path.join(current_dir, 'service/grpc_module/grpc/grpc_proto')
sys.path.append(grpc_dir)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from loguru import logger
import argparse
parser = argparse.ArgumentParser(
    prog='lot_fastapi',  # 程序名
    description='lottery info fastapi backend',  # 描述
)
parser.add_argument('-l', '--logger', type=int, default=0, choices=[0, 1])
args = parser.parse_args()
print(f'运行 args:{args}')
if not args.logger:
    print('关闭日志输出')
    logger.remove()
    logger.add(sink=sys.stdout, level="ERROR", colorize=True)
from fastapi接口.controller.v1.background_service.MQController import router
import fastapi
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
app = fastapi.FastAPI(lifespan=lifespan)
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
app.include_router(router)



if __name__ == "__main__":
    import uvicorn
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run(app, host="0.0.0.0", port=23334)
