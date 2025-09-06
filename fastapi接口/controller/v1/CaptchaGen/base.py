from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['CaptchaGen']
    router.prefix = '/api/v1/CaptchaGen'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router
