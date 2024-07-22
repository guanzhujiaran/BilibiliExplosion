# -*- coding: utf-8 -*-
# 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
import os
import string
from dataclasses import dataclass
import asyncio
import base64
import copy
import datetime
import random
import time
import traceback
from typing import Union
import grpc
from grpc import aio
import json
from bilibili.app.dynamic.v2.dynamic_pb2 import Config, AdParam
from bilibili.app.archive.middleware.v1.preload_pb2 import PlayerArgs
from google.protobuf.json_format import MessageToDict
from bilibili.app.dynamic.v2 import dynamic_pb2_grpc, dynamic_pb2
from grpc获取动态.Utils.MQServer.VoucherMQServer import VoucherRabbitMQ
from grpc获取动态.grpc.makeMetaData import make_metadata, is_useable_Dalvik, gen_trace_id
from grpc获取动态.grpc.prevent_risk_control_tool.activateExClimbWuzhi import ExClimbWuzhi, APIExClimbWuzhi
from utl.代理.request_with_proxy import request_with_proxy
from CONFIG import CONFIG
from grpc获取动态.Utils.GrpcProxyUtils import GrpcProxyTools
from utl.代理.SealedRequests import MYASYNCHTTPX
from loguru import logger


# grpc_err_log.add(
#     CONFIG.root_dir + 'grpc获取动态/src/' + "log/grpc_err.log",
#     encoding="utf-8",
#     enqueue=True,
#     rotation="500MB",
#     compression="zip",
#     retention="15 days",
#     filter=lambda record: record["extra"].get('user') == "grpc_err"
# )

# Handle gRPC errors
def grpc_error(err):
    status = grpc.StatusCode.UNKNOWN
    details = str(err)
    if isinstance(err, grpc.RpcError):
        status = err.code()
        if err.details():
            details = err.details()
    return status, details


@dataclass
class MetaDataWrapper:
    md: tuple
    expire_ts: int
    able: bool = True


class RequestInterceptor(grpc.UnaryUnaryClientInterceptor):
    '''
    grpc请求拦截器
    '''

    def intercept_unary_unary(self, continuation, client_call_details, request):
        print("Method:", client_call_details.method)
        print("Request:", request)
        print("MetaData:", client_call_details.metadata)

        # 调用原始的 continuation，继续处理请求
        response = continuation(client_call_details, request)

        return response


class BiliGrpc:
    def __init__(self):
        self.metadata_list = []  # 设备ip列表
        self.queue_num = 0
        self.my_proxy_addr = CONFIG.my_ipv6_addr
        self.grpc_api_Info_log = logger.bind(user=__name__ + "Info")
        # self.grpc_api_Info_log_handler = logger.add(sys.stderr, level="INFO", filter=lambda record: record["extra"].get(
        #     'user') == __name__ + "Info")
        self.grpc_api_any_log = logger.bind(user=__name__ + "AnyElse")
        self.grpc_api_any_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_grpc_api_log.log"),
                                  level="ERROR",
                                  encoding="utf-8",
                                  enqueue=True,
                                  rotation="500MB",
                                  compression="zip",
                                  retention="15 days",
                                  filter=lambda record: record["extra"].get('user') == __name__ + "AnyElse",
                                  )
        # self.grpc_api_any_log_handler = logger.add(sys.stderr, level="INFO", filter=lambda record: record["extra"].get(
        #     'user') == __name__ + "AnyElse")
        # logger.remove(self.grpc_api_any_log_handler)  # 移除非Info信息
        self.s = MYASYNCHTTPX()
        self.GrpcProxyTools = GrpcProxyTools()  # 实例化
        # 版本号根据 ```https://app.bilibili.com/x/v2/version?mobi_app=android```这个api获取
        self.version_name_build_list = [
            {
                "build": 8000200,
                "version_name": "8.0.0"
            },
            {
                "build": 7810200,
                "version_name": "7.81.0"
            },
            {
                "build": 7800300,
                "version_name": "7.80.0"
            },
            {
                "build": 7790400,
                "version_name": "7.79.0"
            },
            {
                "build": 7780300,
                "version_name": "7.78.0"
            },
            {
                "build": 7770300,
                "version_name": "7.77.0"
            },
            {
                "build": 7760700,
                "version_name": "7.76.0"
            },
            {
                "build": 7750300,
                "version_name": "7.75.0"
            },
            {
                "build": 7740200,
                "version_name": "7.74.0"
            },
            {
                "build": 7730300,
                "version_name": "7.73.0"
            },
            {
                "build": 7720200,
                "version_name": "7.72.0"
            },
            {
                "build": 7710300,
                "version_name": "7.71.0"
            },
            {
                "build": 7700200,
                "version_name": "7.70.0"
            },
            {
                "build": 7690300,
                "version_name": "7.69.0"
            },
            {
                "build": 7640300,
                "version_name": "7.64.0"
            },
            {
                "build": 7630200,
                "version_name": "7.63.0"
            },
            {
                "build": 7620400,
                "version_name": "7.62.0"
            },
            {
                "build": 7610300,
                "version_name": "7.61.0"
            },
            {
                "build": 7600200,
                "version_name": "7.60.0"
            },
            {
                "build": 7590200,
                "version_name": "7.59.0"
            },
            {
                "build": 7580300,
                "version_name": "7.58.0"
            },
            {
                "build": 7571100,
                "version_name": "7.57.1"
            },
            {
                "build": 7560400,
                "version_name": "7.56.0"
            },
            {
                "build": 7550300,
                "version_name": "7.55.0"
            },
            {
                "build": 7540300,
                "version_name": "7.54.0"
            },
            {
                "build": 7530400,
                "version_name": "7.53.0"
            },
            {
                "build": 7510200,
                "version_name": "7.51.0"
            },
            {
                "build": 7500300,
                "version_name": "7.50.0"
            },
            {
                "build": 7520200,
                "version_name": "7.52.0"
            },
            {
                "build": 7490200,
                "version_name": "7.49.0"
            },
            {
                "build": 7480200,
                "version_name": "7.48.0"
            },
            {
                "build": 7470300,
                "version_name": "7.47.0"
            },
            {
                "build": 7460300,
                "version_name": "7.46.0"
            },
            {
                "build": 7440300,
                "version_name": "7.44.0"
            },
            {
                "build": 7430300,
                "version_name": "7.43.0"
            },
            {
                "build": 7410300,
                "version_name": "7.41.0"
            },
            {
                "build": 7400300,
                "version_name": "7.40.0"
            },
            {
                "build": 7390300,
                "version_name": "7.39.0"
            },
            {
                "build": 7380300,
                "version_name": "7.38.0"
            },
            {
                "build": 7370300,
                "version_name": "7.37.0"
            },
            {
                "build": 7360300,
                "version_name": "7.36.0"
            },
            {
                "build": 7350200,
                "version_name": "7.35.0"
            },
            {
                "build": 7340200,
                "version_name": "7.34.0"
            },
            {
                "build": 7330300,
                "version_name": "7.33.0"
            },
            {
                "build": 7320400,
                "version_name": "7.32.0"
            },
            {
                "build": 7310300,
                "version_name": "7.31.0"
            },
            {
                "build": 7300400,
                "version_name": "7.30.0"
            },
            {
                "build": 7300400,
                "version_name": "7.30.0"
            },
            {
                "build": 7290300,
                "version_name": "7.29.0"
            },
            {
                "build": 7280300,
                "version_name": "7.28.0"
            },
            {
                "build": 7270300,
                "version_name": "7.27.0"
            },
            {
                "build": 7260200,
                "version_name": "7.26.0"
            },
            {
                "build": 7250200,
                "version_name": "7.25.0"
            },
            {
                "build": 7240200,
                "version_name": "7.24.0"
            },
            {
                "build": 7230200,
                "version_name": "7.23.0"
            },
            {
                "build": 7220300,
                "version_name": "7.22.0"
            },
            {
                "build": 7210300,
                "version_name": "7.21.0"
            },
            {
                "build": 7200300,
                "version_name": "7.20.0"
            },
            {
                "build": 7190300,
                "version_name": "7.19.0"
            },
            {
                "build": 7180300,
                "version_name": "7.18.0"
            },
            {
                "build": 7170400,
                "version_name": "7.17.0"
            },
            {
                "build": 7160300,
                "version_name": "7.16.0"
            },
            {
                "build": 7150200,
                "version_name": "7.15.0"
            },
            {
                "build": 7141100,
                "version_name": "7.14.1"
            },
            {
                "build": 7140300,
                "version_name": "7.14.0"
            },
            {
                "build": 7130400,
                "version_name": "7.13.0"
            },
            {
                "build": 7120200,
                "version_name": "7.12.0"
            },
            {
                "build": 7110300,
                "version_name": "7.11.0"
            },
            {
                "build": 7100500,
                "version_name": "7.10.0"
            },
            {
                "build": 7090300,
                "version_name": "7.9.0"
            },
            {
                "build": 7081200,
                "version_name": "7.8.1"
            },
            {
                "build": 7080200,
                "version_name": "7.8.0"
            },
            {
                "build": 7070300,
                "version_name": "7.7.0"
            },
            {
                "build": 7060200,
                "version_name": "7.6.0"
            },
            {
                "build": 7051100,
                "version_name": "7.5.1"
            },
            {
                "build": 7050300,
                "version_name": "7.5.0"
            },
            {
                "build": 7040300,
                "version_name": "7.4.0"
            },
            {
                "build": 7030300,
                "version_name": "7.3.0"
            },
            {
                "build": 7020300,
                "version_name": "7.2.0"
            },
            {
                "build": 7012100,
                "version_name": "7.1.2"
            },
            {
                "build": 7011100,
                "version_name": "7.1.1"
            },
            {
                "build": 7010500,
                "version_name": "7.1.0"
            },
            {
                "build": 7000400,
                "version_name": "7.0.0"
            },
            {
                "build": 6880300,
                "version_name": "6.88.0"
            },
            {
                "build": 6870300,
                "version_name": "6.87.0"
            },
            {
                "build": 6860300,
                "version_name": "6.86.0"
            },
            {
                "build": 6850300,
                "version_name": "6.85.0"
            },
            {
                "build": 6840300,
                "version_name": "6.84.0"
            },
            {
                "build": 6840300,
                "version_name": "6.84.0"
            },
            {
                "build": 6830300,
                "version_name": "6.83.0"
            },
            {
                "build": 6820300,
                "version_name": "6.82.0"
            },
            {
                "build": 6810300,
                "version_name": "6.81.0"
            },
            {
                "build": 6800300,
                "version_name": "6.80.0"
            },
            {
                "build": 6790300,
                "version_name": "6.79.0"
            },
            {
                "build": 6780300,
                "version_name": "6.78.0"
            },
            {
                "build": 6770300,
                "version_name": "6.77.0"
            },
            {
                "build": 6760200,
                "version_name": "6.76.0"
            },
            {
                "build": 6720300,
                "version_name": "6.72.0"
            },
            {
                "build": 6710300,
                "version_name": "6.71.0"
            },
            {
                "build": 6700300,
                "version_name": "6.70.0"
            },
            {
                "build": 6690300,
                "version_name": "6.69.0"
            },
            {
                "build": 6680400,
                "version_name": "6.68.0"
            },
            {
                "build": 6670300,
                "version_name": "6.67.0"
            },
            {
                "build": 6660400,
                "version_name": "6.66.0"
            },
            {
                "build": 6650300,
                "version_name": "6.65.0"
            },
            {
                "build": 6640400,
                "version_name": "6.64.0"
            },
            {
                "build": 6630300,
                "version_name": "6.63.0"
            },
            {
                "build": 6620300,
                "version_name": "6.62.0"
            },
            {
                "build": 6610300,
                "version_name": "6.61.0"
            },
            {
                "build": 6600300,
                "version_name": "6.60.0"
            },
            {
                "build": 6590300,
                "version_name": "6.59.0"
            },
            {
                "build": 6580300,
                "version_name": "6.58.0"
            },
            {
                "build": 6570500,
                "version_name": "6.57.0"
            },
            {
                "build": 6560300,
                "version_name": "6.56.0"
            },
            {
                "build": 6550400,
                "version_name": "6.55.0"
            },
            {
                "build": 6540300,
                "version_name": "6.54.0"
            },
            {
                "build": 6530500,
                "version_name": "6.53.0"
            },
            {
                "build": 6512000,
                "version_name": "6.51.2"
            },
            {
                "build": 6510400,
                "version_name": "6.51.0"
            },
            {
                "build": 6500300,
                "version_name": "6.50.0"
            },
            {
                "build": 6491000,
                "version_name": "6.49.1"
            },
            {
                "build": 6490300,
                "version_name": "6.49.0"
            },
            {
                "build": 6480300,
                "version_name": "6.48.0"
            },
            {
                "build": 6470500,
                "version_name": "6.47.0"
            },
            {
                "build": 6460400,
                "version_name": "6.46.0"
            },
            {
                "build": 6450400,
                "version_name": "6.45.0"
            },
            {
                "build": 6440300,
                "version_name": "6.44.0"
            },
            {
                "build": 6430500,
                "version_name": "6.43.0"
            },
            {
                "build": 6421100,
                "version_name": "6.42.1"
            },
            {
                "build": 6420300,
                "version_name": "6.42.0"
            },
            {
                "build": 6410400,
                "version_name": "6.41.0"
            },
            {
                "build": 6400300,
                "version_name": "6.40.0"
            },
            {
                "build": 6390300,
                "version_name": "6.39.0"
            },
            {
                "build": 6380500,
                "version_name": "6.38.0"
            },
            {
                "build": 6371100,
                "version_name": "6.37.1"
            },
            {
                "build": 6370300,
                "version_name": "6.37.0"
            },
            {
                "build": 6360400,
                "version_name": "6.36.0"
            },
            {
                "build": 6350300,
                "version_name": "6.35.0"
            },
            {
                "build": 6340400,
                "version_name": "6.34.0"
            },
            {
                "build": 6330300,
                "version_name": "6.33.0"
            },
            {
                "build": 6320200,
                "version_name": "6.32.0"
            },
            {
                "build": 6310200,
                "version_name": "6.31.0"
            },
            {
                "build": 6300400,
                "version_name": "6.30.0"
            },
            {
                "build": 6290300,
                "version_name": "6.29.0"
            },
            {
                "build": 6280300,
                "version_name": "6.28.0"
            },
            {
                "build": 6270200,
                "version_name": "6.27.0"
            },
            {
                "build": 6262000,
                "version_name": "6.26.2"
            },
            {
                "build": 6260300,
                "version_name": "6.26.0"
            },
            {
                "build": 6250300,
                "version_name": "6.25.0"
            },
            {
                "build": 6240300,
                "version_name": "6.24.0"
            },
            {
                "build": 6235200,
                "version_name": "6.23.5"
            },
            {
                "build": 6230400,
                "version_name": "6.23.0"
            },
            {
                "build": 6225300,
                "version_name": "6.22.5"
            },
            {
                "build": 6220300,
                "version_name": "6.22.0"
            },
            {
                "build": 6216000,
                "version_name": "6.21.6"
            },
            {
                "build": 6215200,
                "version_name": "6.21.5"
            },
            {
                "build": 6210600,
                "version_name": "6.21.0"
            },
            {
                "build": 6205500,
                "version_name": "6.20.5"
            },
            {
                "build": 6200400,
                "version_name": "6.20.0"
            },
            {
                "build": 6190400,
                "version_name": "6.19.0"
            },
            {
                "build": 6182200,
                "version_name": "6.18.2"
            },
            {
                "build": 6181000,
                "version_name": "6.18.1"
            },
            {
                "build": 6180500,
                "version_name": "6.18.0"
            },
            {
                "build": 6171000,
                "version_name": "6.17.1"
            },
            {
                "build": 6170500,
                "version_name": "6.17.0"
            },
            {
                "build": 6160500,
                "version_name": "6.16.0"
            },
            {
                "build": 6151000,
                "version_name": "6.15.1"
            },
            {
                "build": 6150400,
                "version_name": "6.15.0"
            },
            {
                "build": 6140500,
                "version_name": "6.14.0"
            },
            {
                "build": 6130400,
                "version_name": "6.13.0"
            },
            {
                "build": 6120400,
                "version_name": "6.12.0"
            },
            {
                "build": 6110500,
                "version_name": "6.11.0"
            },
            {
                "build": 6100500,
                "version_name": "6.10.0"
            },
            {
                "build": 6090600,
                "version_name": "6.9.0"
            },
            {
                "build": 6082000,
                "version_name": "6.8.2"
            },
            {
                "build": 6081300,
                "version_name": "6.8.1"
            },
            {
                "build": 6080500,
                "version_name": "6.8.0"
            },
            {
                "build": 6071200,
                "version_name": "6.7.1"
            },
            {
                "build": 6070600,
                "version_name": "6.7.0"
            },
            {
                "build": 6060600,
                "version_name": "6.6.0"
            },
            {
                "build": 6050500,
                "version_name": "6.5.0"
            },
            {
                "build": 6042000,
                "version_name": "6.4.2"
            },
            {
                "build": 6040500,
                "version_name": "6.4.0"
            },
            {
                "build": 6030600,
                "version_name": "6.3.0"
            },
            {
                "build": 6020500,
                "version_name": "6.2.0"
            },
            {
                "build": 6010600,
                "version_name": "6.1.0"
            },
            {
                "build": 6000500,
                "version_name": "6.0.0"
            },
            {
                "build": 5580400,
                "version_name": "5.58.0"
            },
            {
                "build": 5572000,
                "version_name": "5.57.2"
            },
            {
                "build": 5570300,
                "version_name": "5.57.0"
            },
            {
                "build": 5561000,
                "version_name": "5.56.1"
            },
            {
                "build": 5560400,
                "version_name": "5.56.0"
            },
            {
                "build": 5551100,
                "version_name": "5.55.1"
            },
            {
                "build": 5550400,
                "version_name": "5.55.0"
            },
            {
                "build": 5540500,
                "version_name": "5.54.0"
            },
            {
                "build": 5531000,
                "version_name": "5.53.1"
            },
            {
                "build": 5530500,
                "version_name": "5.53.0"
            },
            {
                "build": 5521100,
                "version_name": "5.52.1"
            },
            {
                "build": 5520400,
                "version_name": "5.52.0"
            },
            {
                "build": 5511400,
                "version_name": "5.51.1"
            },
            {
                "build": 5510300,
                "version_name": "5.51.0"
            },
            {
                "build": 5500300,
                "version_name": "5.50.0"
            },
            {
                "build": 5490400,
                "version_name": "5.49.0"
            },
            {
                "build": 5483100,
                "version_name": "5.48.3"
            },
            {
                "build": 5482000,
                "version_name": "5.48.2"
            },
            {
                "build": 5480400,
                "version_name": "5.48.0"
            },
            {
                "build": 5470400,
                "version_name": "5.47.0"
            },
            {
                "build": 5460500,
                "version_name": "5.46.0"
            },
            {
                "build": 5452100,
                "version_name": "5.45.2"
            },
            {
                "build": 5451000,
                "version_name": "5.45.1"
            },
            {
                "build": 5450300,
                "version_name": "5.45.0"
            },
            {
                "build": 5442100,
                "version_name": "5.44.2"
            },
            {
                "build": 5440900,
                "version_name": "5.44.0"
            },
            {
                "build": 5431000,
                "version_name": "5.43.1"
            },
            {
                "build": 5423000,
                "version_name": "5.42.3"
            },
            {
                "build": 5420000,
                "version_name": "5.42.0"
            },
            {
                "build": 5410002,
                "version_name": "5.41.1"
            },
            {
                "build": 5410000,
                "version_name": "5.41.0"
            },
            {
                "build": 5400000,
                "version_name": "5.40.0"
            },
            {
                "build": 5391000,
                "version_name": "5.39.1"
            },
            {
                "build": 5390000,
                "version_name": "5.39.0"
            },
            {
                "build": 5380000,
                "version_name": "5.38.0"
            },
            {
                "build": 5370000,
                "version_name": "5.37.0"
            },
            {
                "build": 5360000,
                "version_name": "5.36.0"
            },
            {
                "build": 5350000,
                "version_name": "5.35.0"
            },
            {
                "build": 5341000,
                "version_name": "5.34.1"
            },
            {
                "build": 5340000,
                "version_name": "5.34.0"
            },
            {
                "build": 5332000,
                "version_name": "5.33.2"
            },
            {
                "build": 5330000,
                "version_name": "5.33.0"
            },
            {
                "build": 5330001,
                "version_name": "5.33.1"
            },
            {
                "build": 5322000,
                "version_name": "5.32.2"
            },
            {
                "build": 5320000,
                "version_name": "5.32.0"
            },
            {
                "build": 5310300,
                "version_name": "5.31.3"
            },
            {
                "build": 5310000,
                "version_name": "5.31.0"
            },
            {
                "build": 5300000,
                "version_name": "5.30.0"
            },
            {
                "build": 5291001,
                "version_name": "5.29.1"
            },
            {
                "build": 5290000,
                "version_name": "5.29.0"
            },
            {
                "build": 5280000,
                "version_name": "5.28.0"
            },
            {
                "build": 5271000,
                "version_name": "5.27.1"
            },
            {
                "build": 5270000,
                "version_name": "5.27.0"
            },
            {
                "build": 5260003,
                "version_name": "5.26.3"
            },
            {
                "build": 5260002,
                "version_name": "5.26.2"
            },
            {
                "build": 5250000,
                "version_name": "5.25.0"
            },
            {
                "build": 5240000,
                "version_name": "5.24.0"
            },
            {
                "build": 5220001,
                "version_name": "5.22.1"
            },
            {
                "build": 5220000,
                "version_name": "5.22.0"
            },
            {
                "build": 5210002,
                "version_name": "5.21.2"
            },
            {
                "build": 5210000,
                "version_name": "5.21.0"
            },
            {
                "build": 520001,
                "version_name": "5.20.1"
            },
            {
                "build": 520000,
                "version_name": "5.20.0"
            },
            {
                "build": 519000,
                "version_name": "5.19.0"
            },
            {
                "build": 518000,
                "version_name": "5.18.0"
            },
            {
                "build": 517000,
                "version_name": "5.17.0"
            },
            {
                "build": 516001,
                "version_name": "5.16.1"
            },
            {
                "build": 515000,
                "version_name": "5.15"
            },
            {
                "build": 514000,
                "version_name": "5.14"
            },
            {
                "build": 513000,
                "version_name": "5.13.0"
            },
            {
                "build": 512000,
                "version_name": "5.12.0"
            },
            {
                "build": 511000,
                "version_name": "5.11.0"
            },
            {
                "build": 511000,
                "version_name": "5.11"
            },
            {
                "build": 510000,
                "version_name": "5.10.0"
            },
            {
                "build": 509001,
                "version_name": "5.9.1"
            },
            {
                "build": 509000,
                "version_name": "5.9"
            },
            {
                "build": 508000,
                "version_name": "5.8"
            },
            {
                "build": 507000,
                "version_name": "5.7"
            },
            {
                "build": 506000,
                "version_name": "5.6"
            },
            {
                "build": 505000,
                "version_name": "5.5"
            },
            {
                "build": 504001,
                "version_name": "5.4.1"
            },
            {
                "build": 503000,
                "version_name": "5.3"
            },
            {
                "build": 503000,
                "version_name": "5.3"
            },
            {
                "build": 502000,
                "version_name": "5.2.0"
            },
            {
                "build": 501020,
                "version_name": "5.1.2"
            },
            {
                "build": 501002,
                "version_name": "5.1.1"
            },
            {
                "build": 501000,
                "version_name": "5.1"
            },
            {
                "build": 500001,
                "version_name": "5.0.1"
            },
            {
                "build": 500000,
                "version_name": "5.0"
            },
            {
                "build": 435001,
                "version_name": "4.35.1"
            },
            {
                "build": 435000,
                "version_name": "4.35.0"
            },
            {
                "build": 434000,
                "version_name": "4.34.0"
            },
            {
                "build": 433003,
                "version_name": "4.33.3"
            },
            {
                "build": 433000,
                "version_name": "4.33.0"
            },
            {
                "build": 432000,
                "version_name": "4.32.0"
            },
            {
                "build": 431001,
                "version_name": "4.31.1"
            },
            {
                "build": 431000,
                "version_name": "4.31.0"
            },
            {
                "build": 430000,
                "version_name": "4.30.0"
            },
            {
                "build": 429002,
                "version_name": "4.29.2"
            },
            {
                "build": 429001,
                "version_name": "4.29.1"
            },
            {
                "build": 429000,
                "version_name": "4.29.0"
            },
            {
                "build": 428003,
                "version_name": "4.28.3"
            },
            {
                "build": 428001,
                "version_name": "4.28.1"
            },
            {
                "build": 427001,
                "version_name": "4.27.1"
            },
            {
                "build": 427000,
                "version_name": "4.27.0"
            },
            {
                "build": 426003,
                "version_name": "4.26.3"
            },
            {
                "build": 426002,
                "version_name": "4.26.2"
            },
            {
                "build": 425000,
                "version_name": "4.25.0"
            },
            {
                "build": 424000,
                "version_name": "4.24.0"
            },
            {
                "build": 423001,
                "version_name": "4.23.1"
            },
            {
                "build": 423000,
                "version_name": "4.23.0"
            },
            {
                "build": 423000,
                "version_name": "4.23.0"
            },
            {
                "build": 422000,
                "version_name": "4.22.0"
            },
            {
                "build": 421000,
                "version_name": "4.21.0"
            },
            {
                "build": 420000,
                "version_name": "4.20.0"
            },
            {
                "build": 419000,
                "version_name": "4.19.0"
            },
            {
                "build": 418000,
                "version_name": "4.18.0"
            },
            {
                "build": 417000,
                "version_name": "4.17.0"
            },
            {
                "build": 416000,
                "version_name": "4.16.0"
            },
            {
                "build": 415000,
                "version_name": "4.15.0"
            },
            {
                "build": 414000,
                "version_name": "4.14.0"
            },
            {
                "build": 413001,
                "version_name": "4.13.1"
            },
            {
                "build": 413000,
                "version_name": "4.13.0"
            },
            {
                "build": 412001,
                "version_name": "4.12.1"
            },
            {
                "build": 412000,
                "version_name": "4.12.0"
            },
            {
                "build": 411007,
                "version_name": "4.11.7"
            },
            {
                "build": 411005,
                "version_name": "4.11.5"
            },
            {
                "build": 411000,
                "version_name": "4.11.0"
            },
            {
                "build": 410005,
                "version_name": "4.10.5"
            },
            {
                "build": 410000,
                "version_name": "4.10.0"
            }
        ]
        self.ua = ("Dalvik/2.1.0 (Linux; U; Android 13; 22081212C Build/TQ2A.230505.002.A1) 7.63.0 os/android "
                   "model/22081212C mobi_app/android build/7630200 channel/bili innerVer/7630200 osVer/13 network/2")
        self.channel_list = ['bili', 'master', 'yyb', '360', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google']  # 渠道包列表
        with open(CONFIG.root_dir + 'grpc获取动态/Utils/user-agents_dalvik_application_2-1.json', 'r',
                  encoding='utf-8') as f:
            self.Dalvik_list = json.loads(f.read())
            self.Dalvik_list = list(filter(lambda x: 'Dalvik/2.1.0' in x
                                                     and '[ip:' not in x
                                                     and 'AppleWebKit' not in x
                                           , self.Dalvik_list))
        self.brand_list = ['Xiaomi', 'Huawei', 'Samsung', 'Vivo', 'Oppo', 'Oneplus', 'Meizu', 'Nubia', 'Sony', 'Zte',
                           'Honor', 'Lenovo', 'Lg', 'Blu', 'Asus', 'Panasonic', 'Htc', 'Nokia', 'Motorola', 'Realme',
                           'Alcatel', 'BlackBerry']
        self.__req = request_with_proxy()
        self.channel = None
        self.proxy = None
        self.timeout = 10
        self.cookies = None
        self.cookies_ts = 0
        self.metadata_lock = asyncio.Lock()
        self._352MQServer = VoucherRabbitMQ.Instance()

    async def _prepare_ck_proxy(self):
        proxy = self.proxy
        channel = self.channel
        cookies = await self.__set_available_cookies(self.cookies)
        if not channel:
            proxy, channel = await self.__get_random_channel()

        return proxy, channel, cookies

    async def __set_available_cookies(self, cookies, useProxy=False):
        if not cookies:
            while int(time.time()) - self.cookies_ts < 3 * 60:
                self.grpc_api_any_log.warning(
                    f'上次获取cookie时间：{datetime.datetime.fromtimestamp(self.cookies_ts)} 时间过短！')
                if self.cookies:
                    return self.cookies
                await asyncio.sleep(10)
            self.cookies_ts = int(time.time())
            self.grpc_api_any_log.warning(f"COOKIE:{self.cookies}失效！正在尝试获取新的认证过的cookie！")
            cookies = await self.__get_available_cookies(useProxy)
        self.cookies = cookies
        return cookies

    async def __get_available_cookies(self, useProxy=False) -> str:
        try:
            return await ExClimbWuzhi.verifyExClimbWuzhi(
                MYCFG=APIExClimbWuzhi(
                    ua=self.ua
                ),
                useProxy=useProxy
            )
        except:
            traceback.print_exc()
            await asyncio.sleep(2 * 3600)
            return await self.__get_available_cookies()

    async def __set_available_channel(self, proxy, channel):
        self.proxy = proxy
        self.channel = channel

    async def __get_random_channel(self):
        while 1:
            avaliable_ip_status = await self.GrpcProxyTools.get_rand_avaliable_ip_status()
            proxy = {}
            if avaliable_ip_status:
                proxy = await self.__req.get_grpc_proxy_by_ip(avaliable_ip_status.ip)
            if not proxy:
                proxy = await self.__req.get_one_rand_grpc_proxy()
            if proxy:
                options = [
                    ("grpc.http_proxy", proxy['proxy']['http']),
                ]
                channel = aio.secure_channel('grpc.biliapi.net:443', grpc.ssl_channel_credentials(),
                                             options=options,
                                             compression=grpc.Compression.NoCompression
                                             )  # Connect to the gRPC server
                return proxy, channel
            else:
                logger.critical('无可用代理状态！')
                await asyncio.sleep(3)

    async def metadata_productor(self, proxy) -> MetaDataWrapper:
        """
        metadata生产者
        :param proxy:
        :return:
        """
        await self.metadata_lock.acquire()
        if self.queue_num < 20:
            self.queue_num += 1
            metadata: Union[MetaDataWrapper, None] = None
        else:
            while 1:
                if len(self.metadata_list) > 0:
                    metadata = random.choice(self.metadata_list)
                    if metadata.expire_ts < time.time() or metadata.able == False:
                        self.queue_num -= 1
                        self.metadata_list.remove(metadata)
                        continue
                    break
                if len(self.metadata_list) == 0 and self.queue_num == 0:
                    self.queue_num += 1
                    metadata = None
                    break
                await asyncio.sleep(1)
        self.metadata_lock.release()
        if not metadata:
            while 1:
                brand = random.choice(self.brand_list)
                Dalvik = random.choice(self.Dalvik_list)
                while not is_useable_Dalvik(Dalvik):
                    Dalvik = random.choice(self.Dalvik_list)
                version_name_build = random.choice(self.version_name_build_list)
                version_name = version_name_build['version_name']
                build = version_name_build['build']
                channel = random.choice(self.channel_list)
                logger.debug(
                    f'当前metadata池数量：{len(self.metadata_list)}，总共{self.queue_num}个meta信息，前往获取新的metadata')
                md = await make_metadata("",
                                         brand=brand,
                                         Dalvik=Dalvik,
                                         version_name=version_name,
                                         build=build,
                                         channel=channel,
                                         proxy=proxy
                                         )
                if not dict(md).get('x-bili-ticket'):
                    logger.error(f'bili-ticket获取失败！{md}')
                    await asyncio.sleep(30)
                    continue
                else:
                    break
            metadata = MetaDataWrapper(md=md, expire_ts=int(time.time() + 0.5 * 3600))  # TODO 时间长一点应该没问题吧
            self.metadata_list.append(metadata)
        logger.debug(f'当前metadata池数量：{len(self.metadata_list)}')

        return metadata

    async def handle_grpc_request(self, url: str, grpc_req_message, grpc_resp_msg, cookie_flag: bool,
                                  func_name: str = ""):
        """
        处理grpc请求
        :param url:
        :param grpc_req_message: dynamic_pb2.DynDetailReq(**data_dict)
        :param grpc_resp_msg: dynamic_pb2.DynDetailReply()
        :param cookie_flag:
        :return:
        """
        proxy = {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}}
        channel = None
        ipv6_proxy_weights = 5
        real_proxy_weights = 5
        while 1:
            proxy_flag = random.choices([True, False], weights=[real_proxy_weights, ipv6_proxy_weights], k=1)[0]

            ip_status = None
            cookies = None
            if proxy_flag:
                proxy, channel = await self.__get_random_channel()
                if cookie_flag:
                    cookies = await self.__set_available_cookies(self.cookies)
                if not await self.GrpcProxyTools.check_ip_status(proxy['proxy']['http']):
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=10)
                ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
            else:
                proxy = {'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}}
                if cookie_flag:
                    self.cookies = await ExClimbWuzhi.verifyExClimbWuzhi(useProxy=False, MYCFG=APIExClimbWuzhi(
                        ua=self.ua
                    ))
                    cookies = self.cookies
            msg = grpc_req_message
            proto = msg.SerializeToString()
            data = b"\0" + len(proto).to_bytes(4, "big") + proto
            headers = {
                "Content-Type": "application/grpc",
                'Connection': 'close',
                # "User-Agent": ua,
                # 'User-Agent': random.choice(CONFIG.UA_LIST),
            }
            if cookie_flag and cookies:
                headers.update({
                    "Cookie": cookies
                })
            md = await self.metadata_productor({'proxy': {'http': self.my_proxy_addr, 'https': self.my_proxy_addr}})

            try:
                ret_dict = dict(md.md)
                ret_dict['x-bili-trace-id'] = gen_trace_id()
                headers.update(ret_dict)
                headers_copy = copy.deepcopy(headers)
                for k, v in list(headers_copy.items()):
                    if k.endswith('-bin'):
                        if isinstance(v, bytes):
                            headers.update({k: base64.b64encode(v).decode('utf-8').strip('=')})
                if not headers.get('x-bili-ticket'):
                    raise ValueError('headers中没有有效的x-bili-ticket！')
                resp = await self.s.request(method="post",
                                            url=url,
                                            data=data,
                                            headers=headers, timeout=self.timeout, proxies={
                        'http': proxy['proxy']['http'],
                        'https': proxy['proxy']['https']} if proxy_flag else proxy.get('proxy'), verify=False)
                resp.raise_for_status()
                if type(resp.headers.get('grpc-status')) is not str and type(
                        resp.headers.get('grpc-status')) is not bytes:
                    raise MY_Error(resp.text.replace('\n', ''))
                if '-352' in str(resp.headers.get('bili-status-code')) or \
                        '-352' in str(resp.headers.get('grpc-Message')) or \
                        '-412' in str(resp.headers.get('bili-status-code')) or \
                        '-412' in str(resp.headers.get('grpc-Message')):  # -352的话尝试把这个metadata丢弃
                    self.grpc_api_any_log.warning(
                        f'{func_name}\t{url} -352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{str(data)}')
                    self._352MQServer.push_voucher_info(voucher=resp.headers.get('x-bili-gaia-vvoucher'),
                                                        ua=headers.get('user-agent'))
                    raise MY_Error(
                        f'{func_name}\t-352报错-{proxy}\n{str(resp.headers)}\n{str(headers)}\n{proxy}\n{str(data)}\n{grpc_req_message}')
                gresp = grpc_resp_msg
                gresp.ParseFromString(resp.content[5:])
                resp_dict = MessageToDict(gresp)
                if proxy_flag:
                    if proxy != self.proxy:
                        await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    await self.__set_available_channel(proxy, channel)  # 能用的代理就设置为可用的，下一个获取的代理的就直接接着用了
                if ip_status:
                    origin_available = ip_status.available
                    ip_status.available = True
                    if origin_available != ip_status.available:
                        await self.GrpcProxyTools.set_ip_status(ip_status)
                self.grpc_api_Info_log.info(
                    f'{func_name}\t{url} 获取grpc动态请求成功代理：{proxy.get("proxy")} {grpc_req_message}\n{headers}'
                    f'\n当前可用代理数量：{self.GrpcProxyTools.avalibleNum}/{self.GrpcProxyTools.allNum}')  # 成功代理：\{'http': 'http://(?!.*(192)) 查找非192本地代理
                return resp_dict
            except Exception as err:
                if str(err) == 'Error parsing message':
                    self.grpc_api_any_log.error(f'{func_name}\t解析grpc消息失败！\n{resp.text}\n{resp.content.hex()}')
                    return {}
                origin_available = False
                if ip_status:
                    origin_available = ip_status.available
                    ip_status.available = False
                score_change = -10
                self.grpc_api_any_log.warning(
                    f"{func_name}\t{url} grpc_get_dynamic_detail_by_type_and_rid\n BiliGRPC error: {err}\n"
                    f"{proxy['proxy'] if proxy_flag else proxy.get('proxy')}\n{err}\n{type(err)}")
                if proxy_flag:
                    if proxy == self.proxy:
                        await self.__set_available_channel(None, None)
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                              score_change=score_change)
                    ipv6_proxy_weights += 1
                else:
                    real_proxy_weights += 1
                if '352' in str(err) or '412' in str(err):
                    score_change = 10
                    ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                    self.grpc_api_any_log.warning(f"{ip_status.ip} ip获取次数到达{ip_status.counter}次，出现-352现象，舍弃当前metadata！")
                    if cookie_flag:
                        if ip_status and ip_status.counter > 10:
                            pass
                        else:
                            if cookies == self.cookies:
                                self.cookies = None
                                await self.__set_available_cookies(None, useProxy=True)
                    md.able = False # -352报错就舍弃当前metadata
                    if proxy['proxy']['http'] != self.my_proxy_addr:
                        if not ip_status:
                            ip_status = await self.GrpcProxyTools.get_ip_status_by_ip(proxy['proxy']['http'])
                        ip_status.max_counter_ts = int(time.time())
                        ip_status.code = -352
                        ip_status.available = False
                        if origin_available != ip_status.available:
                            await self.GrpcProxyTools.set_ip_status(ip_status)
                    else:

                        await asyncio.sleep(2)  # 本地ipv6状态-352的情况下，等待一段时间，破解验证码之后再执行

    # region 第三方grpc库发起的请求
    async def grpc_api_get_DynDetails(self, dyn_ids: [int]) -> dict:
        """
        通过grpc客户端请求的，不太好一起统一处理
        通过动态id的列表批量获取动态详情，但是需要有所有的动态id，不能用，很难受
        :param dyn_ids:
        :return:
        """
        if type(dyn_ids) is not list:
            raise TypeError(f'dyn_ids must be a list!{dyn_ids}')
        if len(dyn_ids) == 0:
            return {}
        dyn_ids = [int(x) for x in dyn_ids]
        # proxy_server_address = sqlhelper.select_rand_proxy()['proxy']['https']
        # intercept_channel = grpc.intercept_channel(
        #     channel,
        #     # RequestInterceptor()
        # )

        while 1:
            proxy, channel, cookies = await self._prepare_ck_proxy()
            dyn_details_req = dynamic_pb2.DynDetailsReq(
                dynamic_ids=json.dumps({'dyn_ids': dyn_ids}),
            )
            try:
                dynamic_client = dynamic_pb2_grpc.DynamicStub(channel)
                # print(dyn_details_req.SerializeToString())
                # ack = gen_random_access_key()
                ack = ''
                md = await make_metadata(ack, proxy=proxy)

                dyn_all_resp = await dynamic_client.DynDetails(dyn_details_req,
                                                               metadata=md,
                                                               timeout=self.timeout)
                ret_dict = MessageToDict(dyn_all_resp)
                if proxy != self.proxy:
                    await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=0, score_change=10)
                    await self.__set_available_channel(proxy, channel)
                return ret_dict
            except grpc.RpcError as e:
                stat, det = grpc_error(e)
                self.grpc_api_any_log.warning(f"\nBiliGRPC error: {stat} - {proxy['proxy']}")
                if proxy == self.proxy:
                    await self.__set_available_channel(None, None)
                score_change = -10
                if 'HTTP proxy returned response code 400' in det or 'OPENSSL_internal' in det:  # 400状态码表示代理可能是http1.1协议，不支持grpc的http2.0
                    score_change = -10
                # 已知的不重要的错误
                if det == 'Deadline Exceeded':
                    pass
                elif 'failed to connect to all addresses' in det:
                    pass
                elif 'OPENSSL_internal:TLSV1_ALERT_NO_APPLICATION_PROTOCOL.' in det:
                    pass
                elif 'OPENSSL_internal:WRONG_VERSION_NUMBER.' in det:
                    pass
                else:
                    self.grpc_api_any_log.warning(
                        f"{dyn_ids} grpc_api_get_DynDetails\n BiliGRPC error: {stat} - {det}\n{dyn_details_req}\n{type(e)}")  # 重大错误！
                await self.__req.upsert_grpc_proxy_status(proxy_id=proxy['proxy_id'], status=-412,
                                                          score_change=score_change)

    # endregion

    # region grpc请求接口
    async def grpc_get_dynamic_detail_by_type_and_rid(self, rid: Union[int, str], dynamic_type: int = 2,
                                                      proxy_flag=False, cookie_flag=False) -> dict:
        """
        通过rid和动态类型特定获取一个动态详情
        :param cookie_flag: 是否使用cookie
        :param proxy_flag:
        :param dynamic_type:动态类型
        :param rid:动态rid
        :return:
        """
        if type(rid) is str and str.isdigit(rid):
            rid = int(rid)
        if type(rid) is not int:
            raise TypeError(f'rid must be number! rid:{rid}')
        url = "http://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynDetail"
        data_dict = {
            'uid': random.randint(1, 9223372036854775807),
            'dyn_type': dynamic_type,
            'rid': rid,
            "ad_param": AdParam(
                ad_extra=''.join(random.choices(string.ascii_uppercase + string.digits,
                                                k=random.choice([x for x in range(1300, 1350)])))
            ),
            'player_args': PlayerArgs(qn=32, fnval=272, voice_balance=1),
            'share_id': 'dt.dt-detail.0.0.pv',
            'share_mode': 3,
            'local_time': 8,
            'config': Config()
        }
        msg = dynamic_pb2.DynDetailReq(**data_dict)
        gresp = dynamic_pb2.DynDetailReply()
        return await self.handle_grpc_request(url, msg, gresp, cookie_flag)

    async def grpc_get_space_dyn_by_uid(self, uid: Union[str, int], history_offset: str = '', page: int = 1,
                                        proxy_flag: bool = False) -> dict:
        """
         获取up空间
        :param uid:
        :param history_offset:
        :param page:
        :return:
        """
        if type(uid) is str and str.isdigit(uid):
            uid = int(uid)
        if type(uid) is not int or type(history_offset) is not str:
            raise TypeError(
                f'uid must be a number and history_offset must be str! uid:{uid} history_offset:{history_offset}')
        url = "http://app.bilibili.com/bilibili.app.dynamic.v2.Dynamic/DynSpace"
        data_dict = {
            'host_uid': int(uid),
            'history_offset': history_offset,
            'local_time': 8,
            'page': page,
            'from': 'space'
        }
        msg = dynamic_pb2.DynSpaceReq(**data_dict)
        gresp = dynamic_pb2.DynSpaceRsp()
        return await self.handle_grpc_request(url, msg, gresp, False, 'grpc_get_space_dyn_by_uid')

    # endregion


class MY_Error(ValueError):
    pass


async def _test():
    t = BiliGrpc()
    resp = await t.grpc_get_dynamic_detail_by_type_and_rid(313189161, 2, False)  # 没有ticket的情况下一个ip大概50次就会出现-352
    print(resp)


if __name__ == '__main__':
    asyncio.run(_test())
