# -*- coding: utf-8 -*-
import base64

import grpc
import httpx

from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.app.dynamic.v2.dynamic_pb2 import DynSpaceReq, DynDetailReq
from bilibili.api.ticket.v1.ticket_pb2 import GetTicketRequest , GetTicketResponse
from bilibili.metadata.locale.locale_pb2 import Locale
from bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq
from bilibili.rpc.status_grpc import
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


grpc_msg_encoded = "CglhbmRyb2lkNjQSBHByb2QaCGRhMWNjYjIz"
from google.protobuf import text_format

grpc_msg = b64decode(grpc_msg_encoded)
print(grpc_msg)
msg = FawkesReq()
msg.ParseFromString(grpc_msg)

print(msg)
