from enum import Enum

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class QueueName(str, Enum):
    OfficialReserveChargeLotMQ = "OfficialReserveChargeLotQueue"
    UpsertOfficialReserveChargeLotMQ = "UpsertOfficialReserveChargeLotQueue"
    UpsertLotDataByDynamicIdMQ = "UpsertLotDataByDynamicIdQueue"
    UpsertTopicLotMQ = "UpsertTopicLotMQ"

class ExchangeName(str, Enum):
    bili_data = "bili_data"


class RoutingKey(str, Enum):
    OfficialReserveChargeLotMQ = "BiliData.OfficialReserveChargeLotMQ"
    UpsertOfficialReserveChargeLotMQ = "BiliData.UpsertOfficialReserveChargeLotMQ"
    UpsertLotDataByDynamicIdMQ = "BiliData.UpsertLotDataByDynamicIdMQ"
    UpsertTopicLotMQ = "BiliData.UpsertTopicLotMQ"


class RabbitMQConfig(CustomBaseModel):
    host: str
    port: int
    username: str
    password: str
    protocol: str
