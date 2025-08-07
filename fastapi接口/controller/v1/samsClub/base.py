from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['SamsClub']
    router.prefix = '/api/v1/samsClub'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router
