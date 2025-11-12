from dataclasses import dataclass
from enum import StrEnum

from faststream.rabbit import RabbitQueue, RabbitExchange


class QueueName(StrEnum):
    TestMQ = "test"
    OfficialReserveChargeLotMQ = "OfficialReserveChargeLotQueue"
    UpsertOfficialReserveChargeLotMQ = "UpsertOfficialReserveChargeLotQueue"
    UpsertLotDataByDynamicIdMQ = "UpsertLotDataByDynamicIdQueue"
    UpsertTopicLotMQ = "UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ = "UpsertMilvusBiliLotDataMQ"
    UpsertBiliAtariMQ = "UpsertBiliAtariMQ"
    BiliVoucherMQ = "bili_352_voucher"


class ExchangeName(StrEnum):
    bili_data = "bili_data"


# 定义一个名为RoutingKey的类，继承自str和Enum
class RoutingKey(StrEnum):
    TestMQ = "testRouter"
    OfficialReserveChargeLotMQ = "BiliData.OfficialReserveChargeLotMQ"
    UpsertOfficialReserveChargeLotMQ = "BiliData.UpsertOfficialReserveChargeLotMQ"
    UpsertLotDataByDynamicIdMQ = "BiliData.UpsertLotDataByDynamicIdMQ"
    UpsertTopicLotMQ = "BiliData.UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ = "Milvus.BiliLotDataMQ"
    UpsertBiliAtariMQ = "BiliData.UpsertBiliAtariMQ"
    BiliVoucherMQ = "BiliData.bili_352_voucher"


@dataclass
class MQPropBase:
    queue_name: QueueName
    routing_key_name: RoutingKey
    exchange: RabbitExchange
    _exchange_name: ExchangeName | str | None = None
    _rabbit_queue: RabbitQueue | None = None

    def __post_init__(self):
        self._rabbit_queue = RabbitQueue(
            name=self.queue_name,
            routing_key=self.routing_key_name + '.#')
        self._exchange_name = self.exchange.name

    @property
    def rabbit_queue(self) -> RabbitQueue:
        return self._rabbit_queue

    @property
    def exchange_name(self) -> ExchangeName:
        return self._exchange_name
