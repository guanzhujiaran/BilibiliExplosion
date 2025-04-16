from enum import Enum

from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class QueueName(str, Enum):
    OfficialReserveChargeLotMQ = "OfficialReserveChargeLotQueue"
    UpsertOfficialReserveChargeLotMQ = "UpsertOfficialReserveChargeLotQueue"
    UpsertLotDataByDynamicIdMQ = "UpsertLotDataByDynamicIdQueue"
    UpsertTopicLotMQ = "UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ="UpsertMilvusBiliLotDataMQ"
    UpsertProxyInfoMQ="UpsertProxyInfoMQ"

class ExchangeName(str, Enum):
    bili_data = "bili_data"
    proxy='proxy'


# 定义一个名为RoutingKey的类，继承自str和Enum
class RoutingKey(str, Enum):
    # 定义一个名为OfficialReserveChargeLotMQ的枚举值，值为"BiliData.OfficialReserveChargeLotMQ"
    OfficialReserveChargeLotMQ = "BiliData.OfficialReserveChargeLotMQ"
    # 定义一个名为UpsertOfficialReserveChargeLotMQ的枚举值，值为"BiliData.UpsertOfficialReserveChargeLotMQ"
    UpsertOfficialReserveChargeLotMQ = "BiliData.UpsertOfficialReserveChargeLotMQ"
    # 定义一个名为UpsertLotDataByDynamicIdMQ的枚举值，值为"BiliData.UpsertLotDataByDynamicIdMQ"
    UpsertLotDataByDynamicIdMQ = "BiliData.UpsertLotDataByDynamicIdMQ"
    # 定义一个名为UpsertTopicLotMQ的枚举值，值为"BiliData.UpsertTopicLotMQ"
    UpsertTopicLotMQ = "BiliData.UpsertTopicLotMQ"
    UpsertMilvusBiliLotDataMQ="Milvus.BiliLotDataMQ"
    UpsertProxyInfoMQ="Proxy.UpsertProxyInfoMQ"

class RabbitMQConfig(CustomBaseModel):
    host: str
    port: int
    username: str
    password: str
    protocol: str
