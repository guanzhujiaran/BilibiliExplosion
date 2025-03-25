from fastapi import APIRouter

def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['乱七八糟的路由']
    router.prefix = ''
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router
