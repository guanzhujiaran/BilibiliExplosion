from dataclasses import dataclass
from enum import StrEnum

from faststream.rabbit import RabbitQueue, RabbitExchange


class QueueName(StrEnum):
    OfficialReserveChargeLotMQ = "OfficialReserveChargeLotQueue"
    UpsertOfficialReserveChargeLotMQ = "UpsertOfficialReserveChargeLotQueue"
    UpsertLotDataByDynamicIdMQ = "UpsertLotDataByDynamicIdQueue"
    UpsertTopicLotMQ = "UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ = "UpsertMilvusBiliLotDataMQ"
    BiliVoucherMQ = "bili_352_voucher"


class ExchangeName(StrEnum):
    bili_data = "bili_data"


# 定义一个名为RoutingKey的类，继承自str和Enum
class RoutingKey(StrEnum):
    # 定义一个名为OfficialReserveChargeLotMQ的枚举值，值为"BiliData.OfficialReserveChargeLotMQ"
    OfficialReserveChargeLotMQ = "BiliData.OfficialReserveChargeLotMQ"
    # 定义一个名为UpsertOfficialReserveChargeLotMQ的枚举值，值为"BiliData.UpsertOfficialReserveChargeLotMQ"
    UpsertOfficialReserveChargeLotMQ = "BiliData.UpsertOfficialReserveChargeLotMQ"
    # 定义一个名为UpsertLotDataByDynamicIdMQ的枚举值，值为"BiliData.UpsertLotDataByDynamicIdMQ"
    UpsertLotDataByDynamicIdMQ = "BiliData.UpsertLotDataByDynamicIdMQ"
    # 定义一个名为UpsertTopicLotMQ的枚举值，值为"BiliData.UpsertTopicLotMQ"
    UpsertTopicLotMQ = "BiliData.UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ = "Milvus.BiliLotDataMQ"
    BiliVoucherMQ = "BiliData.bili_352_voucher"


@dataclass
class MQPropBase:
    queue_name: QueueName
    routing_key_name: RoutingKey
    exchange: RabbitExchange
    _rabbit_queue: RabbitQueue | None = None

    def __post_init__(self):
        self._rabbit_queue = RabbitQueue(
            name=self.queue_name,
            routing_key=self.routing_key_name + '.#')

    @property
    def rabbit_queue(self) -> RabbitQueue:
        return self._rabbit_queue
