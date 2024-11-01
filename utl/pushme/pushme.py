# -*- coding: utf-8 -*-
import datetime
import json
import os
import traceback
from functools import wraps
from loguru import logger
import requests
from requests import Response

from CONFIG import CONFIG

pushme_log = logger.bind(user='pushme')
pushme_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_pushme_log.log"),
               level="WARNING",
               encoding="utf-8",
               enqueue=True,
               rotation="500MB",
               compression="zip",
               retention="15 days",
               filter=lambda record: record["extra"].get('user') == "pushme",
               )


def __preprocess_content(content: str) -> str:
    try:
        ipv4 = requests.get('https://4.ipw.cn/').text
    except:
        ipv4 = ""
    ipv4 = f'http://{ipv4}:23333/docs'
    try:
        ipv6 = requests.get('https://6.ipw.cn/').text
        ipv6 = f'http://[{ipv6}]:23333/docs'
        content += f'\n{datetime.datetime.now()}当前服务器ip信息：\n{ipv4}\n{ipv6}'
    except Exception as e:
        pushme_log.exception(e)
    return content


def pushme(title: str, content: str, __type='text') -> Response:
    resp = Response()
    try:
        url = CONFIG.pushnotify.pushme.url
        token = CONFIG.pushnotify.pushme.token
        push_content = __preprocess_content(content)
        data = {
            "push_key": token,
            "title": title,
            "content": push_content,
            'type': __type
        }
        resp = requests.post(url=url, data=data, proxies={
            "http": CONFIG.V2ray_proxy,
            "https": CONFIG.V2ray_proxy
        }, timeout=10)
        return resp
    except Exception as e:
        pushme_log.info(f'推送pushme失败！{e}\n开始尝试微信pushpush推送！')
        resp = _pushpush(title, content, __type)
        return resp
    finally:
        try:
            pushme_log.error(f'请求响应：{resp.text}\n{title}\n{content}')
        except Exception as e:
            pushme_log.exception(f'推送失败！{e}')


def _pushpush(title: str, content: str, __type='txt') -> Response:
    resp = Response()
    if __type == 'text':
        __type = 'txt'
    elif __type == 'data':
        __type = 'json'
    elif __type == 'markdata':
        __type = 'markdown'
    elif __type == 'html':
        pass
    elif __type == 'txt':
        pass
    elif __type == 'json':
        pass
    elif __type == 'markdown':
        pass
    elif __type == 'cloudMonitor':
        pass
    elif __type == 'jenkins':
        pass
    elif __type == 'route':
        pass
    elif __type == 'pay':
        pass
    else:
        __type = 'txt'
    try:
        push_content = __preprocess_content(content)
        url = CONFIG.pushnotify.pushplus.url
        data = {
            "token": CONFIG.pushnotify.pushplus.token,
            "title": title[0:100],
            "content": push_content,
            "template": __type
        }
        resp = requests.post(url=url, data=json.dumps(data), headers={
            "Content-Type": "application/json"
        })

        if resp.json().get('code') != 200:
            raise SyntaxError(f'推送请求失败！{resp.text}')
        return resp
    except Exception as e:
        pushme_log.exception(f'推送失败！\n{e}')
        return resp


def pushme_try_catch_decorator(func: callable) -> callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            pushme(f'服务：【{func.__class__.__name__} {func.__name__}】报错！', f'错误堆栈：\n{traceback.format_exc()}')
            pushme_log.exception(e)
            raise e
    return wrapper


def async_pushme_try_catch_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            pushme(f'服务：【{func.__class__.__name__} {func.__name__}】报错！', f'错误堆栈：\n{traceback.format_exc()}')
            pushme_log.exception(e)
            raise e

    return wrapper


if __name__ == '__main__':
    _pushpush('测试3', 'test3')
