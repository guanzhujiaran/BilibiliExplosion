# -*- coding: utf-8 -*-
import base64

import grpc
import httpx
from bilibili.metadata.restriction.restriction_pb2 import Restriction
from bilibili.app.dynamic.v2.dynamic_pb2 import Config
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.metadata.device.device_pb2 import Device
from bilibili.metadata.metadata_pb2 import Metadata
from bilibili.app.dynamic.v2.dynamic_pb2 import DynSpaceReq, DynDetailReq
from bilibili.api.ticket.v1.ticket_pb2 import GetTicketRequest, GetTicketResponse
from bilibili.metadata.locale.locale_pb2 import Locale
from bilibili.metadata.fawkes.fawkes_pb2 import FawkesReq


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


grpc_msg_encoded = "CAEQ/J3wAxolWFlDMTIwNkM4NEI1MkNFNEUxNjk3MDI3RTQ3MjM0RjEyQjlGRCIHYW5kcm9pZCoHYW5kcm9pZDoGbWFzdGVyQgRTb255SghTTS1HNjEwTFIFOC4xLjBaQDNjNDYwMGE5ZmQwMzhiZWY1ZTAzY2E0YzY0ZDc0NGU2MjAyNDA5MTQxNTI0MTQ5OTQzNDBjNjRkOWQ3YzBkODRiQDNjNDYwMGE5ZmQwMzhiZWY1ZTAzY2E0YzY0ZDc0NGU2MjAyNDA5MTQxNTIzMjdjYmNhMzExNzRmODllMmVmYzdqBjguMTMuMHJAM2M0NjAwYTlmZDAzOGJlZjVlMDNjYTRjNjRkNzQ0ZTYyMDI0MDkxNDE1MjMyN2NiY2EzMTE3NGY4OWUyZWZjN3jv85S3Bg"





from google.protobuf import text_format

grpc_msg = b64decode(grpc_msg_encoded)
print(grpc_msg)
msg = Device()
msg.ParseFromString(grpc_msg)

print(msg)

my_msg = Device(
)
print(my_msg.SerializeToString())
