from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.DAMO]
    router.prefix = RouterPrefix.DAMO
    if dependencies:
        router.dependencies = dependencies
    return router
