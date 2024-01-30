# -*- coding: utf-8 -*-
import base64

import grpc
import httpx

from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.app.dynamic.v2.dynamic_pb2 import DynSpaceReq
def b64decode(encoded_str):
    # 计算需要添加的等号个数
    padding = len(encoded_str) % 4
    if padding != 0:
        padding = 4 - padding

    # 在字符串末尾添加等号
    padded_str = encoded_str + '=' * padding

    # 解码Base64
    decoded_bytes = base64.b64decode(padded_str)

    return decoded_bytes

grpc_msg_encoded=\
""

# grpc_msg = b64decode(grpc_msg_encoded)
grpc_msg=b'\x11\x08\x94\xe4\xd4\xcc\x06 \x08(\x012\x05space'
device_msg = DynSpaceReq()
device_msg.ParseFromString(grpc_msg)
print(device_msg)