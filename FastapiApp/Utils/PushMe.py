import datetime
import json
import traceback
from collections import deque
from functools import wraps
from typing import Literal, Optional
import requests
from requests import Response
from CONFIG import CONFIG
from Utils.代理.SealedRequests import my_async_httpx
from log.base_log import pushme_logger

push_msg_d = deque(maxlen=50)


def __preprocess_content(content: str) -> str:
    content += f'\n{datetime.datetime.now()}'
    return content


async def _pushme(title: str, content: str, push_type: Literal[
                                                           "text",
                                                           "data",
                                                           "markdata",
                                                           "html",
                                                           "txt",
                                                           "json",
                                                           "markdown",
                                                           "cloudMonitor",
                                                           "jenkins",
                                                           "route",
                                                           "pay"
                                                       ] | None = 'text') -> Response:
    resp = Response()
    if content in push_msg_d:
        return Response()
    push_msg_d.append(content)
    try:
        url = CONFIG.pushnotify.pushme.url
        token = CONFIG.pushnotify.pushme.token
        push_content = __preprocess_content(content)
        data = {
            "push_key": token,
            "title": title[0:100],
            "content": push_content[0:500],
            'type': push_type
        }
        resp = await my_async_httpx.post(url=url, data=data, proxies={
            "http": CONFIG.V2ray_proxy,
            "https": CONFIG.V2ray_proxy
        }, timeout=10)
        return resp
    except Exception as e:
        pushme_logger.info(f'推送pushme失败！{e}\n开始尝试微信pushpush推送！')
        resp = await _pushpush(title, content, push_type)
        return resp
    finally:
        try:
            pushme_logger.debug(f'请求响应：{resp.text}\n{title}\n{content}')
        except Exception as e:
            pushme_logger.exception(f'推送失败！{e}')


async def _pushpush(title: str, content: str, push_type: str = 'txt') -> Response:
    resp = Response()
    if push_type == 'text':
        push_type = 'txt'
    elif push_type == 'data':
        push_type = 'json'
    elif push_type == 'markdata':
        push_type = 'markdown'
    elif push_type == 'html':
        pass
    elif push_type == 'txt':
        pass
    elif push_type == 'json':
        pass
    elif push_type == 'markdown':
        pass
    elif push_type == 'cloudMonitor':
        pass
    elif push_type == 'jenkins':
        pass
    elif push_type == 'route':
        pass
    elif push_type == 'pay':
        pass
    else:
        push_type = 'txt'
    try:
        push_content = __preprocess_content(content)
        url = CONFIG.pushnotify.pushplus.url
        data = {
            "token": CONFIG.pushnotify.pushplus.token,
            "title": title[0:100],
            "content": push_content[0:500],
            "template": push_type
        }
        resp = await my_async_httpx.post(url=url, data=json.dumps(data), headers={
            "Content-Type": "application/json"
        })

        if resp.json().get('code') != 200:
            raise SyntaxError(f'推送请求失败！{resp.text}')
        return resp
    except Exception as e:
        pushme_logger.exception(f'推送失败！\n{e}')
        return resp


def async_pushme_try_catch_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            await a_pushme(f'服务：【{func.__class__.__name__} {func.__name__}】报错！',
                           f'错误堆栈：\n{traceback.format_exc()}')
            pushme_logger.exception(e)
            raise e

    return wrapper


async def a_pushme(title: str, content: str, push_type: Optional[Literal[
    'text', 'data', "markdata", "html", "txt", "json", "markdown", "cloudMonitor", "jenkins", "route", "pay"]] = 'text') -> Response:
    return await _pushme(title, content, push_type)
