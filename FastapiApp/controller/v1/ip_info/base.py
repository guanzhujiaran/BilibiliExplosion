from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.V1_IP]
    router.prefix = RouterPrefix.IP_INFO
    if dependencies:
        router.dependencies = dependencies
    return router


