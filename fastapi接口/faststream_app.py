import asyncio
import sys
import io
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))  # 将CONFIG导入
current_dir = os.path.dirname(__file__)
grpc_dir = os.path.join(current_dir, 'service/grpc_module/grpc/grpc_proto')
sys.path.append(grpc_dir)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.platform.startswith('windows'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # 祖传代码不可删，windows必须替换掉selector，不然跑一半就停了
else:
    import uvloop

    uvloop.install()
from fastapi接口.utils.argParse import parse

args = parse()
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

    uvicorn.run(app, host="0.0.0.0", port=23334, loop="uvloop")
