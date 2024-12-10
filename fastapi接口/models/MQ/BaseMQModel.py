from enum import Enum
from pydantic import BaseModel


class QueueName(str, Enum):
    bili_data = "bili_data"
    OfficialReserveChargeLotMQ = "OfficialReserveChargeLotQueue"
    UpsertOfficialReserveChargeLotMQ = "UpsertOfficialReserveChargeLotQueue"
    UpsertLotDataByDynamicIdMQ = "UpsertLotDataByDynamicIdQueue"


class ExchangeName(str, Enum):
    bili_data = "bili_data"


class RoutingKey(str, Enum):
    OfficialReserveChargeLotMQ = "BiliData.OfficialReserveChargeLotMQ"
    UpsertOfficialReserveChargeLotMQ = "BiliData.UpsertOfficialReserveChargeLotMQ"
    UpsertLotDataByDynamicIdMQ = "BiliData.UpsertLotDataByDynamicIdMQ"


class RabbitMQConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    protocol: str
