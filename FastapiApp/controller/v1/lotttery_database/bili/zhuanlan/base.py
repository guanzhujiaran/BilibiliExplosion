from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.V1_BILI]
    router.prefix = RouterPrefix.BILI_ZHUANLAN
    if dependencies:
        router.dependencies = dependencies
    return router


