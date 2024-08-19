import os
import time
import traceback
from threading import Thread

from CONFIG import CONFIG
from grpc获取动态.Models.RabbitmqModel import VoucherInfo
from grpc获取动态.Utils.MQServer.BasicMQ import BasicMQServer
from grpc获取动态.Utils.极验.极验点击验证码 import GeetestV3Breaker
import pickle
import json
from loguru import logger
from utl.pushme.pushme import pushme_try_catch_decorator, pushme

log = logger.bind(user='-352Voucher')
log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_352VoucherClient_lot_log.log"),
        level="WARNING",
        encoding="utf-8",
        enqueue=True,
        rotation="500MB",
        compression="zip",
        retention="15 days",
        filter=lambda record: record["extra"].get('user') == "-352Voucher",
        )


class VoucherMQClient(BasicMQServer):

    def __init__(self):
        super().__init__()
        self.GeetestV3Breaker = GeetestV3Breaker()
        self.queue_name = self.CONFIG.RabbitMQConfig.QueueName.bili_352_voucher.value

    def start_voucher_break_consumer(self):
        def voucher_break_callback(ch, method, properties, body):
            try:
                ct = json.loads(pickle.loads(body))
                voucher_info: VoucherInfo = VoucherInfo(**ct)
                if int(time.time()) - voucher_info.generate_ts > 10:
                    return
                log.info(f"Received: {ct}")
                self.GeetestV3Breaker.validate_form_voucher_ua(voucher_info.voucher, voucher_info.ua,voucher_info.ck,voucher_info.origin,voucher_info.referer, True)
            except Exception as e:
                pushme('-352Voucher出错', traceback.format_exc())
                log.exception(f'-352Voucher出错\n{e}')

        self._queue_consumer(voucher_break_callback, self.queue_name)


if __name__ == '__main__':
    threads = set()
    for i in range(3):
        __ = VoucherMQClient()
        thread = Thread(target=__.start_voucher_break_consumer)
        thread.start()
        threads.add(thread)

    for i in threads:
        i.join()
