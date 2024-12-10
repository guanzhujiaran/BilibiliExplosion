import json

from fastapi接口.log.base_log import MQ_logger
from fastapi接口.service.MQ.base.BasicMQ import BasicMQServer
from utl.designMode.singleton import Singleton


@Singleton
class Ipv6ChangeRabbitMQ(BasicMQServer):

    def __init__(self):
        super().__init__()
        self.q_name = self.CONFIG.RabbitMQConfig.QueueName.ipv6_change.value
        self.log = MQ_logger

    def push_ipv6_change(self, origin_ipv6: str, now_ipv6: str):
        try:
            assert type(origin_ipv6) is str and type(now_ipv6) is str, "origin_ipv6和now_ipv6必须为字符串"
            assert origin_ipv6 and now_ipv6, "origin_ipv6和now_ipv6不能为空"
            # 推送数据至MQ
            ipv6_dict: dict = {
                "origin_ipv6": origin_ipv6,
                "now_ipv6": now_ipv6
            }
            self.log.info(f"推送ipv6_change数据至MQ: {ipv6_dict}")
            self._queue_push(json.dumps(ipv6_dict), self.q_name)
        except Exception as e:
            self.log.error(f"推送ipv6_change数据至MQ失败: {e}")
            self.log.exception(e)


if __name__ == '__main__':
    ipv6_change_mq = Ipv6ChangeRabbitMQ.Instance()
