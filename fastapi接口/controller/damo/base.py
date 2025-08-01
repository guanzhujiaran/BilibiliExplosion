from fastapi import APIRouter

def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['modelscope达摩机器学习']
    router.prefix = '/damo'
    # 将认证依赖项应用于所有路由
    if dependencies:
        router.dependencies = dependencies
    return router
