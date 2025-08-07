# -*- coding: utf-8 -*-
import asyncio.tasks
import base64
import random

import httpx
from bilibili.app.dynamic.v2.dynamic_pb2 import AdParam
from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2
from fastapi接口.service.grpc_module.Utils.metadata.makeMetaData import make_metadata

event_loop = asyncio.get_event_loop()
uid = 2
url = "https://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynDetail"
data_dict = {
    'uid': random.randint(1, 9223372036854775807),
    'dyn_type': 2,
    'rid': 326834723,
    "ad_param": AdParam(
        ad_extra=''
        # ''.join(random.choices(string.ascii_uppercase + string.digits,
        #                                 k=random.choice([x for x in range(1300, 1350)])))
    ),
    'player_args': PlayerArgs(qn=32, fnval=272, voice_balance=1),
    'share_id': 'dt.dt-detail.0.0.pv',
    'share_mode': 3,
    'local_time': 8,
    'config': Config()
}

grpc_req_message = dynamic_pb2.DynDetailReq(**data_dict)
grpc_resp_msg = dynamic_pb2.DynDetailReply()
msg = grpc_req_message
proto = msg.SerializeToString()
data = b"\0" + len(proto).to_bytes(4, "big") + proto
headers = {
    "content-type": "application/grpc",
    # 'Connection': 'close',
    # "user-agent": ua,
    # 'user-agent': random.choice(CONFIG.UA_LIST),
}
headers.update(dict(
    event_loop.run_until_complete(make_metadata(""))[0]
))
for k, v in list(headers.items()):
    if k == 'user-agent':
        headers.pop(k)
    if k.endswith('-bin'):
        if isinstance(v, bytes):
            headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
resp = httpx.post(url,
                  data=data,
                  headers=headers,
                  proxies={
                      'https://': "socks5://194.195.122.51:1080",
                      'http://': "socks5://194.195.122.51:1080"
                  }
                  )
print(headers)
print(resp)
print(resp.content)
print(resp.headers)
gresp = grpc_resp_msg
gresp.ParseFromString(resp.content[5:])
resp_dict = MessageToDict(gresp)

print(resp_dict)


# te = dynamic_pb2.DynSpaceRsp(resp_dict)
# print(te)


def parse_newdict_from_dict(orig_dict: dict) -> dict:
    def _parse_newlist_form_list(orig_list: list) -> list:
        new_list = []
        for i in orig_list:
            new_list.append(parse_newdict_from_dict(i))
        return new_list

    new_dict = {}
    for k, v in orig_dict.items():
        new_k = k[0]
        new_v = v
        if type(v) == str:
            if v.isdigit():
                new_v = int(v)
        for alpha in k[1:]:
            if alpha.isupper():
                new_k += '_' + alpha.lower()
            else:
                new_k += alpha
        if type(v) is dict:
            new_dict.update({new_k: parse_newdict_from_dict(new_v)})
        elif type(v) is list:
            new_dict.update({new_k: _parse_newlist_form_list(new_v)})
        else:
            new_dict.update({new_k: new_v})

    return new_dict
