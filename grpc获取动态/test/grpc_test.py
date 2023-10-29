# -*- coding: utf-8 -*-
import base64
import httpx

from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from grpc获取动态.grpc.makeMetaData import make_metadata
from utl.代理.request_with_proxy import request_with_proxy

uid = 2

data_dict = {
    'host_uid': int(uid),
    'history_offset': '',
    'local_time': 8,
    'page': 99999,
    'from': 'space'
}

msg = dynamic_pb2.DynSpaceReq(**data_dict)
proto = msg.SerializeToString()
data = b"\0" + len(proto).to_bytes(4, "big") + proto
headers = {
    # "User-Agent": "Dalvik/2.1.0 (Linux; Android) os/android",
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/grpc",
    # "x-bili-device-bin": ""
}
headers.update(dict(make_metadata("")))
for k, v in list(headers.items()):
    if k == 'user-agent':
        headers.pop(k)
    if k.endswith('-bin'):
        if type(v) == bytes:
            headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
resp = httpx.post("https://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace", data=data,
                  headers=headers,
                  verify=False,
                  )
resp.raise_for_status()
print(resp.headers)
gresp = dynamic_pb2.DynSpaceRsp()
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
