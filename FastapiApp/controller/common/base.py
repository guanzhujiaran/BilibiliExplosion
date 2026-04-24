from fastapi import APIRouter
from ApiRoutes import RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.COMMON]
    router.prefix = ''
    if dependencies:
        router.dependencies = dependencies
    return router
