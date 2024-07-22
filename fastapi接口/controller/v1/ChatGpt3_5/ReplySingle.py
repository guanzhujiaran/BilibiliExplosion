"""
单轮回复
"""
import os
import time
from fastapi import Query
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.ChatGpt3_5.ReplySingleModel import ReplyReq, ReplyRes
from fastapi接口.service.handleLLMReplySingle import ChatGpt3_5
from loguru import logger
from .base import new_router
myfastapi_logger = logger.bind(user='fastapi')

chatgpt = ChatGpt3_5()
router = new_router()
_current_dir = os.path.dirname(os.path.abspath(__file__))


@router.post('/ReplySingle', summary='回复单轮消息', response_model=CommonResponseModel[ReplyRes])
async def reply_single(reply_req: ReplyReq):
    """

    :param reply_req:
    :return:
    """
    reply_res = ReplyRes(
        answer=await chatgpt.SingleReply(reply_req.question),
        ts=int(time.time())
    )
    try:
        log_path = os.path.join(_current_dir, '../../../log/chatgpt_single.log')
        write_mode = 'a+'
        if not os.path.exists(log_path):
            write_mode = 'w'
        with open(log_path, write_mode, encoding='utf-8') as f:
            f.write(f'|{reply_req.question}|\n|{reply_res.answer}|\n-----')
    except Exception as e:
        myfastapi_logger.exception(f'写入日志失败\n{e} ')
    return CommonResponseModel(data=reply_res)


@router.get('/helloWorld', response_model=CommonResponseModel)
async def hello_world(mode: int = Query(..., le=2, title='模式，1为json，2为str，其他形式则报错')):
    if mode == 1:
        return CommonResponseModel(code=0, msg='服务运行中', data={'msg': '服务运行中'})
    elif mode == 2:
        return CommonResponseModel(code=0, msg='服务运行中', data='服务运行中')
    else:
        raise SyntaxError("服务运行中")
