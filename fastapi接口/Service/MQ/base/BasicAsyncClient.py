import asyncio
import functools
import traceback
from pika.adapters.asyncio_connection import AsyncioConnection
from typing import Dict, Coroutine, Callable, Any
import msgpack
import pika
from pika.exchange_type import ExchangeType
from CONFIG import CONFIG
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.BaseMQModel import QueueName, ExchangeName, RoutingKey
from utl.pushme.pushme import pushme


def _mq_retry_wrapper(max_retries: int = 5, delay: int = 10):
    """
    异步重试装饰器：在函数执行异常时进行重试
    :param max_retries: 最大重试次数，默认为 5 次
    :param delay: 每次重试的延迟时间，单位秒，默认为 10 秒
    """

    def inner_wrap(func: Callable[[Any], Coroutine[None, None, Any]]):
        async def wrap(*args, **kwargs):
            retries = 0
            while 1:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    MQ_logger.exception(
                        f"MQ {func.__name__} 执行异常,参数：{args, kwargs}, 重试次数: {retries}/{max_retries}: {e}")
                    if max_retries <= 0 or retries < max_retries:
                        pass
                    else:
                        MQ_logger.exception(
                            f"【MQ发布消息】执行{func.__name__}失败第{retries}次，彻底失败！！参数：{args, kwargs}")
                        pushme(f'【MQ发布消息】执行{func.__name__}失败第{retries}次，彻底失败！！{e}',
                               f'参数：{args, kwargs}\n{traceback.format_exc()}')
                        break
                    await asyncio.sleep(delay)  # 等待后再重试
            return None  # 如果超出了最大重试次数，返回 None 或者可以根据需求自定义错误返回值

        return wrap

    return inner_wrap


def sync(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        while 1:
            try:
                loop = asyncio.new_event_loop()
                return loop.create_task(f(*args, **kwargs))
            except Exception as e:
                MQ_logger.exception(f"MQ {f.__name__} 执行异常,参数：{args, kwargs}, 错误信息：{e}")

    return wrapper


class BasicMessageReceiver:
    EXCHANGE = 'message'
    EXCHANGE_TYPE = ExchangeType.topic
    PUBLISH_INTERVAL = 1
    QUEUE = 'text'
    ROUTING_KEY = 'example.text'

    def __init__(self,
                 EXCHANGE: ExchangeName,
                 EXCHANGE_TYPE: ExchangeType,
                 QUEUE: QueueName,
                 ROUTING_KEY: RoutingKey,
                 rabbit_mq_config=CONFIG.RabbitMQConfig):
        self._stopping = None
        self.EXCHANGE = EXCHANGE or self.EXCHANGE
        self.EXCHANGE_TYPE = EXCHANGE_TYPE or self.EXCHANGE_TYPE
        self.QUEUE = QUEUE or self.QUEUE
        if EXCHANGE_TYPE == ExchangeType.topic:  # 如果是topic模式，就直接用通配符就完事儿了，剩下自己加在发布者的routing key后面
            self.ROUTING_KEY = (ROUTING_KEY + '.#') or (self.ROUTING_KEY + '.#')
        else:
            self.ROUTING_KEY = ROUTING_KEY or self.ROUTING_KEY
        self.should_reconnect = False
        self.was_consuming = False
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = rabbit_mq_config.broker_url
        self._consuming = False
        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 20  # -- 设置一个最大数字，保证所有请求全部消费掉？最大65535，因为网络接口只有这么多。。。
        # 但是数字太大会导致报错file descriptor溢出，只能改成一个合理的数字了

    def encode_message(self, body: Dict, encoding_type: str = "bytes"):
        if encoding_type == "bytes":
            return msgpack.packb(body)
        else:
            raise NotImplementedError

    def decode_message(self, body):
        if type(body) == bytes:
            return msgpack.unpackb(body)
        else:
            raise NotImplementedError

    def connect(self):
        MQ_logger.info(f'Connecting to {self._url}')
        return AsyncioConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
            custom_ioloop=asyncio.get_event_loop(),
        )

    def close_connection(self):
        self._consuming = False
        if self._connection.is_closing or self._connection.is_closed:
            MQ_logger.info('Connection is closing or already closed')
        else:
            MQ_logger.info('Closing connection')
            self._connection.close()

    def on_connection_open(self, _unused_connection):
        MQ_logger.info('Connection opened')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        MQ_logger.error(f'Connection open failed: {err}', )
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        self._channel = None
        # if self._closing:
        #     self._connection.ioloop.stop()
        # else:
        MQ_logger.critical(f'Connection closed, reconnect necessary: {reason}')
        self.reconnect()

    def reconnect(self):
        self.should_reconnect = True
        self.stop()

    def open_channel(self):
        MQ_logger.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        MQ_logger.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        MQ_logger.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        MQ_logger.warning(f'Channel {channel} was closed: {channel, reason}', )
        self.close_connection()

    def setup_exchange(self, exchange_name):
        MQ_logger.info(f'Declaring exchange: {exchange_name}', )
        cb = functools.partial(
            self.on_exchange_declareok, userdata=exchange_name)
        self._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=self.EXCHANGE_TYPE,
            callback=cb,
            passive=False,
            durable=True,
            auto_delete=False
        )

    def on_exchange_declareok(self, _unused_frame, userdata):
        MQ_logger.info(f'Exchange declared: {userdata}', )
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        MQ_logger.info(f'Declaring queue {queue_name}')
        cb = functools.partial(self.on_queue_declareok, userdata=queue_name)
        self._channel.queue_declare(queue=queue_name, callback=cb)

    def on_queue_declareok(self, _unused_frame, userdata):
        queue_name = userdata
        MQ_logger.info(f'Binding {self.EXCHANGE} to {queue_name} with {self.ROUTING_KEY}')
        cb = functools.partial(self.on_bindok, userdata=queue_name)
        self._channel.queue_bind(
            queue_name,
            self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            callback=cb
        )

    def on_bindok(self, _unused_frame, userdata):
        MQ_logger.info(f'Queue bound: {userdata}')
        self.set_qos()

    def set_qos(self):
        self._channel.basic_qos(
            prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        MQ_logger.info(f'QOS set to: {self._prefetch_count}')
        self.start_consuming()

    def start_consuming(self):
        MQ_logger.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(
            self.QUEUE,
            self.on_message,
            auto_ack=False
        )
        self.was_consuming = True
        self._consuming = True

    def add_on_cancel_callback(self):
        MQ_logger.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        MQ_logger.critical(f'Consumer was cancelled remotely, shutting down: {method_frame}', )
        if self._channel:
            self._channel.close()

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        MQ_logger.info(f'Received message # {basic_deliver.delivery_tag} from {properties.app_id}: {body}')

        return asyncio.create_task(self.consume(basic_deliver, properties, body))

    async def consume(self, basic_deliver, properties, body):
        raise NotImplementedError('未实现消费者函数！')

    def acknowledge_message(self, delivery_tag):
        if self._channel is None or self._channel.is_closed or self._channel.is_closing:
            MQ_logger.error("Channel is invalid, cannot acknowledge message")
            return
        MQ_logger.info(f'Acknowledging message {delivery_tag}')
        self._channel.basic_ack(delivery_tag)

    def nacknowledge_message(self, delivery_tag):
        if self._channel is None or self._channel.is_closed or self._channel.is_closing:
            MQ_logger.error("Channel is invalid, cannot nacknowledge message")
            return
        MQ_logger.info(f'Not Acknowledging message {delivery_tag}')
        self._channel.basic_nack(delivery_tag, requeue=True)

    def stop_consuming(self):
        if self._channel:
            MQ_logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                self.on_cancelok, userdata=self._consumer_tag)
            self._channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)

        """
        self._consuming = False
        MQ_logger.info(
            f'RabbitMQ acknowledged the cancellation of the consumer: {userdata}',
        )
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        MQ_logger.info('Closing the channel')
        self._channel.close()

    async def run(self):
        while not self._stopping:
            try:
                self._connection = self.connect()
                await asyncio.Future()  # Run forever until stopped
            except Exception as e:
                MQ_logger.exception(f"RabbitMQ run Exception occurred: {e}")
                await asyncio.sleep(5)  # 等待一段时间再重试

    def stop(self):
        if not self._closing:
            self._closing = True
            MQ_logger.critical('Stopping')
            if self._consuming:
                self.stop_consuming()
            MQ_logger.critical('Stopped')

        self._stopping = True


class BasicMessageSender:
    EXCHANGE = 'message'
    EXCHANGE_TYPE = ExchangeType.topic
    PUBLISH_INTERVAL = 1
    QUEUE = 'text'
    ROUTING_KEY = 'example.text'

    def __init__(self,
                 EXCHANGE: ExchangeName,
                 EXCHANGE_TYPE: ExchangeType,
                 QUEUE: QueueName,
                 ROUTING_KEY: RoutingKey,
                 rabbit_mq_config=CONFIG.RabbitMQConfig):
        self._channel = None
        self.EXCHANGE = EXCHANGE or self.EXCHANGE
        self.EXCHANGE_TYPE = EXCHANGE_TYPE or self.EXCHANGE_TYPE
        self.QUEUE = QUEUE or self.QUEUE
        self.ROUTING_KEY = ROUTING_KEY or self.ROUTING_KEY
        self._url = rabbit_mq_config.broker_url
        self._connection = None

    def connection(self):
        self._connection = pika.BlockingConnection(pika.URLParameters(self._url))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
            passive=False,
            durable=True,
            auto_delete=False
        )

    def send_message(
            self,
            body: Dict,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        self.connection()
        if extra_routing_key and type(extra_routing_key) is str:
            routing_key = self.ROUTING_KEY + "." + extra_routing_key
        else:
            MQ_logger.critical(
                f'Invalid routing key {extra_routing_key}!!!use original routing key 【{self.ROUTING_KEY}】 instead')
            routing_key = self.ROUTING_KEY
        self._channel.basic_publish(
            exchange=self.EXCHANGE, routing_key=routing_key,
            body=self.encode_message(body)
        )
        MQ_logger.info(f'Published message # {body}')
        self._connection.close()

    def encode_message(self, body: Dict, encoding_type: str = "bytes"):
        if encoding_type == "bytes":
            return msgpack.packb(body)
        else:
            raise NotImplementedError
