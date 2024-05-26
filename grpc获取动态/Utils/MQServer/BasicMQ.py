import pickle
from typing import Callable

import pika

from CONFIG import CONFIG


class BasicMQServer:

    def __init__(self):
        self.CONFIG = CONFIG
        credentials = pika.PlainCredentials(self.CONFIG.RabbitMQConfig.user, self.CONFIG.RabbitMQConfig.pwd)  # mq用户名和密码
        pika_params = pika.ConnectionParameters(host=self.CONFIG.RabbitMQConfig.host,
                                                port=self.CONFIG.RabbitMQConfig.port,
                                                virtual_host='/',
                                                credentials=credentials,
                                                heartbeat=0
                                                )
        connection = pika.BlockingConnection(pika_params)

        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        for q_name in self.CONFIG.RabbitMQConfig.queue_name_list:
            channel.queue_declare(queue=q_name)
        channel.confirm_delivery()
        self.channel = channel

    def _queue_push(self, message: str, queue_name: str):
        """

        :param message:
        :param queue_name: 队列名称
        :return:
        """
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   body=pickle.dumps(message))

    def _queue_consumer(self, callback: Callable, queue_name: str):
        """

        :param callback:
        :param queue_name: 队列名称
        :return:
        """
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True, )
        self.channel.start_consuming()
