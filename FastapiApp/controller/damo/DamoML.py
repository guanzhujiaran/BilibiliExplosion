from fastapi import Body, Query

from controller.damo.base import new_router
from Service.LLM.handleLLMReplySingle import chatgpt

router = new_router()


@router.get('/semantic', summary='情感分析', response_model=bool)
@router.post("/semantic", summary='情感分析', response_model=bool)
async def semantic_analysis(data: str | None = Body('', embed=True), query: str | None = Query('')):
    return await chatgpt.analyze_sentiment(data or query)
