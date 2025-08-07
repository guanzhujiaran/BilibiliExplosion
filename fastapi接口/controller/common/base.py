from fastapi import APIRouter

def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ['乱七八糟的路由']
    router.prefix = ''
    if dependencies:
        router.dependencies = dependencies
    return router
