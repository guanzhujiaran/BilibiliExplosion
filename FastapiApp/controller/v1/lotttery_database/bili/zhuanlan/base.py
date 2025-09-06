from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['V1Bili']
    router.prefix = '/api/v1/lottery_database/bili/zhuanlan'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router


