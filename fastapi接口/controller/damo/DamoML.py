from fastapi import Body, Query

from fastapi接口.controller.damo.base import new_router
from fastapi接口.service.damo.semantic import damo_semantic

router = new_router()


@router.get('/semantic', summary='情感分析', response_model=bool)
@router.post("/semantic", summary='情感分析', response_model=bool)
async def semantic_analysis(data: str | None = Body('', embed=True), query: str | None = Query('')):
    return await damo_semantic.semantic(data or query)
