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
    req = requests.post(url=url, data=data)
