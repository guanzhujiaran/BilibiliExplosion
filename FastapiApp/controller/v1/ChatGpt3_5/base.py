from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.V1_CHATGPT]
    router.prefix = RouterPrefix.CHATGPT
    if dependencies:
        router.dependencies = dependencies
    return router
