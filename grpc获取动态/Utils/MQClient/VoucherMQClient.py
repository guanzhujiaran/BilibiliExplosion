import time
from grpc获取动态.Models.RabbitmqModel import VoucherInfo
from grpc获取动态.Utils.MQServer.BasicMQ import BasicMQServer
from grpc获取动态.Utils.极验.极验点击验证码 import GeetestV3Breaker
import pickle
import json
class VoucherMQClient(BasicMQServer):
    """
    rabbitmq 客户端
    不能用单例模式，不然无法并发了
    """

    def __init__(self):
        super().__init__()
        self.GeetestV3Breaker = GeetestV3Breaker()
        self.queue_name = self.CONFIG.RabbitMQConfig.QueueName.bili_352_voucher.value


    def start_voucher_break_consumer(self):
        def voucher_break_callback(ch, method, properties, body):
            ct = json.loads(pickle.loads(body))

            voucher_info: VoucherInfo = VoucherInfo(
                **ct
            )
            if int(time.time()) - voucher_info.generate_ts > 10:
                return
            print(f"Received: {ct}")
            self.GeetestV3Breaker.main(voucher_info.voucher, voucher_info.ua)

        self._queue_consumer(voucher_break_callback, self.queue_name)

if __name__ == '__main__':
    __ = VoucherMQClient()
    __.start_voucher_break_consumer()
