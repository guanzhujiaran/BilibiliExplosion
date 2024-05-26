"""
单轮回复
"""
import time
from fastapi接口.models.v1.ChatGpt3_5.ReplySingleModel import ReplyReq, ReplyRes
from fastapi接口.service.handleLLMReplySingle import ChatGpt3_5
from starlette.requests import Request
from .base import new_router

chatgpt = ChatGpt3_5()

router = new_router()


@router.post('/ReplySingle', summary='回复单轮消息', response_model=ReplyRes)
async def reply_single(reply_req: ReplyReq):
    """

    :param reply_req:
    :return:
    """
    reply_res = ReplyRes(
        answer=await chatgpt.SingleReply(reply_req.question),
        ts=int(time.time())
    )
    return reply_res

@router.get('/helloWorld')
async def hello_world(request: Request):
    if request.query_params.get('mode')==1:
        return {'msg':"服务运行中"}
    elif request.query_params.get('mode')==2:
        return '服务运行中'
    else:
        raise "服务运行中"