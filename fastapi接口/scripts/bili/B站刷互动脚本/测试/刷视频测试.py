# -*- coding:utf- 8 -*-
import copy
import json
import random
import re
import threading
import time
import requests
import numpy
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods as my_methonds

url = 'https://api.live.bilibili.com/room/v1/Room/get_info?room_id=24127369&from=room'
req = requests.get(url=url)
print(req.text)
