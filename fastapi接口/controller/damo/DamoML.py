from fastapi import Query

from fastapi接口.service.damo.semantic import semantic
from fastapi接口.controller.damo.base import new_router

router = new_router()


@router.get("/semantic", summary='情感分析', response_model=bool)
async def semantic_analysis(data: str = Query()):
    return await semantic(data)
