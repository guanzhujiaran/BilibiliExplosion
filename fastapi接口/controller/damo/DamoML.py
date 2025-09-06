from fastapi import Body, Query

from fastapi接口.controller.damo.base import new_router
from fastapi接口.Service.LLM.handleLLMReplySingle import chatgpt

router = new_router()


@router.get('/semantic', summary='情感分析', response_model=bool)
@router.post("/semantic", summary='情感分析', response_model=bool)
async def semantic_analysis(data: str | None = Body('', embed=True), query: str | None = Query('')):
    return await chatgpt.analyze_sentiment(data or query)
