"""
单轮回复
"""
import os
import time
from typing import Union, Literal

import aiofiles
from fastapi import Query, Body
from fastapi接口.log.base_log import myfastapi_logger
from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.ChatGpt3_5.ReplySingleModel import ReplyReq, ReplyRes, LLMShowInfo
from fastapi接口.service.LLM.handleLLMReplySingle import ChatGpt3_5
from .base import new_router

chatgpt = ChatGpt3_5()
router = new_router()
_current_dir = os.path.dirname(os.path.abspath(__file__))


@router.post('/ReplySingle', summary='回复单轮消息', response_model=CommonResponseModel[Union[ReplyRes, None]])
async def reply_single(reply_req: ReplyReq):
    """

    :param reply_req:
    :return:
    """
    try:
        answer = await chatgpt.SingleReply(reply_req.question)
        reply_res = ReplyRes(
            answer=answer,
            ts=int(time.time())
        )
        try:
            log_path = os.path.join(_current_dir, '../../../log/chatgpt_single.log')
            write_mode:Literal['a+','w'] = 'a+'
            if not os.path.exists(log_path):
                write_mode = 'w'
            async with aiofiles.open(file=log_path, mode=write_mode, encoding='utf-8') as f:
                await f.write(f'|{reply_req.question}|\n|{reply_res.answer}|\n-----\n')
        except Exception as e:
            myfastapi_logger.error(f'写入日志失败！{e} ')
        return CommonResponseModel(data=reply_res)
    except Exception as e:
        myfastapi_logger.error(f'AI回复失败！{e} ')
        return CommonResponseModel(code=500, data=None, msg=f'AI回复失败！\n{e}')


@router.get('/LLMStatus', response_model=CommonResponseModel[LLMShowInfo], response_model_exclude_none=True)
async def get_llm_status():
    resp = chatgpt.show_openai_client()
    return CommonResponseModel(code=0, data=resp)


@router.post('ResetLLMStatus', response_model=CommonResponseModel)
async def reset_llm_status(base_url: str | None = Body(...)):
    return CommonResponseModel(msg=chatgpt.reset_llm_status(base_url))


@router.get('/helloWorld', response_model=CommonResponseModel)
async def hello_world(mode: int = Query(..., le=2, title='模式，1为json，2为str，其他形式则报错')):
    if mode == 1:
        return CommonResponseModel(code=0, msg='服务运行中', data={'msg': '服务运行中'})
    elif mode == 2:
        return CommonResponseModel(code=0, msg='服务运行中', data='服务运行中')
    else:
        raise SyntaxError("服务运行中")
