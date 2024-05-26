import json
import time
from dataclasses import asdict

from loguru import logger

from grpc获取动态.Models.RabbitmqModel import VoucherInfo
from grpc获取动态.Utils.MQServer.BasicMQ import BasicMQServer


class VoucherRabbitMQ(BasicMQServer):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__()
        self.q_name = self.CONFIG.RabbitMQConfig.QueueName.bili_352_voucher.value
        self.log = logger.bind(user='VoucherRabbitMQServer')
    def push_voucher_info(self, voucher:str,ua:str):
        try:
            voucher_info:VoucherInfo = VoucherInfo(voucher=voucher,ua=ua,generate_ts=int(time.time()))
            voucher_info_dict = asdict(voucher_info)
            self.log .info(f"voucher_info_dict: {voucher_info_dict}")
            self._queue_push(json.dumps(voucher_info_dict), self.q_name)
        except Exception as e:
            self.log.error(f"推送352数据至MQ失败: {e}")
            self.log.exception(e)
