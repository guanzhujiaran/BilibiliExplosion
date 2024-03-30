# -*- coding: utf-8 -*-
import json

import traceback

import requests
from requests import Response

from CONFIG import CONFIG


def pushme(title: str, content: str, __type='text')->Response:
    try:
        url = CONFIG.pushnotify.pushme.url
        token = CONFIG.pushnotify.pushme.token
        data = {
            "push_key": token,
            "title": title,
            "content": content,
            'type': __type
        }
        return requests.post(url=url, data=data, verify=False)
    except:
        print(f'推送失败！\n{traceback.format_exc()}')
        print(f'开始尝试微信pushpush推送！')
        return _pushpush(title, content, __type)


def _pushpush(title: str, content: str, __type='txt'):
    if __type == 'text':
        __type = 'txt'
    elif __type=='data':
        __type = 'json'
    elif __type=='markdata':
        __type='markdown'
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
        url = CONFIG.pushnotify.pushplus.url

        data = {
            "token": CONFIG.pushnotify.pushplus.token,
            "title": title,
            "content": content,
            "template": __type
        }
        req = requests.post(url=url, data=json.dumps(data), headers={
            "Content-Type": "application/json"
        })
        if req.json().get('code') != 200:
            raise SyntaxError(f'推送请求失败！{req.text}')
        return req
    except:
        print(f'推送失败！\n{traceback.format_exc()}')


if __name__ == '__main__':
    pushme('测试标题', '测试内容')
