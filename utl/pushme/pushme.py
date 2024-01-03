# -*- coding: utf-8 -*-
import requests

from CONFIG import CONFIG


def pushme(title,content,__type='text'):
    url = CONFIG.pushnotify.pushme.url
    token = CONFIG.pushnotify.pushme.token
    data = {
        "push_key": token,
        "title": title,
        "content": content,
        'type': __type
    }
    req = requests.post(url=url, data=data,verify=False)

if __name__ == '__main__':
    pushme('测试标题', '测试内容')
