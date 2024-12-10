import json
import time
from dataclasses import asdict

from fastapi接口.log.base_log import MQ_logger
from grpc获取动态.Models.RabbitmqModel import VoucherInfo
from fastapi接口.service.MQ.base.BasicMQ import BasicMQServer
from utl.designMode.singleton import Singleton


@Singleton
class VoucherRabbitMQ(BasicMQServer):

    def __init__(self):
        super().__init__()
        self.q_name = self.CONFIG.RabbitMQConfig.QueueName.bili_352_voucher.value
        self.log = MQ_logger

    def push_voucher_info(self, voucher: str, ua: str, ck: str, origin: str, referer: str, ticket: str, version: str):
        try:
            assert type(voucher) is str and type(ua) is str, "voucher和ua必须为字符串"
            assert voucher and ua, "voucher和ua不能为空"
            assert type(ticket) is str, "ticket必须为字符串"
            # 推送数据至MQ
            voucher_info: VoucherInfo = VoucherInfo(voucher=voucher, ua=ua, generate_ts=int(time.time()), ck=ck,
                                                    origin=origin, referer=referer, ticket=ticket, version=version,
                                                    session_id="")
            voucher_info_dict = asdict(voucher_info)
            self.log.info(f"推送voucher_info_dict数据至MQ: {voucher_info_dict}")
            self._queue_push(json.dumps(voucher_info_dict), self.q_name)
        except Exception as e:
            self.log.error(f"推送352数据至MQ失败: {e}")
            self.log.exception(e)
