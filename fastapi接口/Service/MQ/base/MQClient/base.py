from faststream.rabbit import RabbitExchange, ExchangeType
from faststream.rabbit.fastapi import RabbitRouter
from CONFIG import CONFIG

from fastapi接口.models.MQ.BaseMQModel import ExchangeName, MQPropBase, QueueName, RoutingKey


class BaseFastStreamMQ:
    def __init__(self, mq_props: MQPropBase):
        self.mq_props = mq_props

    async def consume(self, *args, **kwargs):
        raise NotImplementedError("子类必须实现此方法")


router = RabbitRouter(
    CONFIG.RabbitMQConfig.broker_url,
    include_in_schema=True,
    logger=None,
    max_consumers=500,  # 对于rabbitmq来说就是 prefetch_count
    channel_number=10
)


def get_broker():
    return router.broker


exch = RabbitExchange(ExchangeName.bili_data.value, auto_delete=False, type=ExchangeType.TOPIC, durable=True)
official_reserve_charge_lot_mq_prop = MQPropBase(
    queue_name=QueueName.OfficialReserveChargeLotMQ,
    routing_key_name=RoutingKey.OfficialReserveChargeLotMQ,
    exchange=exch
)
upsert_official_reserve_charge_lot_mq_prop = MQPropBase(
    queue_name=QueueName.UpsertOfficialReserveChargeLotMQ,
    routing_key_name=RoutingKey.UpsertOfficialReserveChargeLotMQ,
    exchange=exch
)
upsert_lot_data_by_dynamic_id_prop = MQPropBase(
    queue_name=QueueName.UpsertLotDataByDynamicIdMQ,
    routing_key_name=RoutingKey.UpsertLotDataByDynamicIdMQ,
    exchange=exch
)
upsert_topic_lot_prop = MQPropBase(
    queue_name=QueueName.UpsertTopicLotMQ,
    routing_key_name=RoutingKey.UpsertTopicLotMQ,
    exchange=exch
)
upsert_milvus_bili_lot_data_prop = MQPropBase(
    queue_name=QueueName.UpsertMilvusBiliLotDataMQ,
    routing_key_name=RoutingKey.UpsertMilvusBiliLotDataMQ,
    exchange=exch
)
bili_voucher_prop = MQPropBase(
    queue_name=QueueName.BiliVoucherMQ,
    routing_key_name=RoutingKey.BiliVoucherMQ,
    exchange=exch
)