from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['V1Ip']
    router.prefix = '/api/v1/ip_info'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router


