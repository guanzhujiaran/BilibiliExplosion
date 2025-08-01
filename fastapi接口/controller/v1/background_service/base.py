from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['BackgroundService']
    router.prefix = '/api/v1/background_service'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router
