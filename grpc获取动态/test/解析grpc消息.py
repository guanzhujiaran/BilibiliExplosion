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
"CAEQvL/QAxolWFkyQzJEQjI3QjFBRjFGNDlDOTM1NzFGODc0MkE5RkQ4QjE1RCIHYW5kcm9pZCoHYW5kcm9pZDIFcGhvbmU6BGJpbGlCBlhpYW9taUoJMjIwODEyMTJDUgIxNFpAZmZiZWMyMWNlYjczZTg3OWEyM2MxYTAxOTU3ZjI0NmEyMDI0MDExNDIzNDcwNDYxYmFkNjE1NjhmMDRiZWU1M2JAZmZiZWMyMWNlYjczZTg3OWEyM2MxYTAxOTU3ZjI0NmEyMDI0MDExNDIzNDcwNDYxYmFkNjE1NjhmMDRiZWU1M2oGNy42MS4wckBmZmJlYzIxY2ViNzNlODc5YTIzYzFhMDE5NTdmMjQ2YTIwMjQwMTE0MjM0NzA0NjFiYWQ2MTU2OGYwNGJlZTUzePiDkK0G"

grpc_msg = b64decode(grpc_msg_encoded)

device_msg = Device()
device_msg.ParseFromString(grpc_msg)
print(device_msg)