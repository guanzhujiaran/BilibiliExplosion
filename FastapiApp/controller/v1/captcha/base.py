from fastapi import APIRouter
from ApiRoutes import RouterPrefix, RouterTags


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = [RouterTags.CAPTCHA]
    router.prefix = RouterPrefix.CAPTCHA
    if dependencies:
        router.dependencies = dependencies
    return router
