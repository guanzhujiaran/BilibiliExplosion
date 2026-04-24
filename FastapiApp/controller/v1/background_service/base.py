from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.BACKGROUND_SERVICE]
    router.prefix = RouterPrefix.BACKGROUND_SERVICE
    if dependencies:
        router.dependencies = dependencies
    return router
