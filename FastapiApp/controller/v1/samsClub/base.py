from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.SAMS_CLUB]
    router.prefix = RouterPrefix.SAMS_CLUB
    if dependencies:
        router.dependencies = dependencies
    return router
