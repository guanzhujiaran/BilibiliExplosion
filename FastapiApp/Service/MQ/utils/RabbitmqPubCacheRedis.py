from enum import StrEnum
from typing import List
from CONFIG import CONFIG
from Models.MQ.BaseMQModel import ExchangeName
from Models.MQ.MQRouterModels import MQ_PARAMS_JOINED_TYPE
from Models.base.custom_pydantic import CustomBaseModel
from Utils.redisTool.RedisManager import RedisManagerBase


class CachedMessage(CustomBaseModel):
    """缓存消息模型"""
    id: str  # 消息唯一标识
    msg: MQ_PARAMS_JOINED_TYPE  # 消息内容
    queue_name: str  # MQ属性配置
    routing_key: str  # 路由键
    extra_routing_key: str  # 额外的路由键
    exchange_name: ExchangeName
    timestamp: float  # 时间戳


class RedisObj(RedisManagerBase):
    class RedisMap(StrEnum):
        pending_messages = 'rabbitmq_pub_cache:pending_messages'  # 待发送消息列表 hashtable

    def __init__(self):
        super().__init__(
            host=CONFIG.database.rabbitmqCacheRedis.host,
            port=CONFIG.database.rabbitmqCacheRedis.port,
            db=CONFIG.database.rabbitmqCacheRedis.db)

    async def add_pending_message(self, cached_message: CachedMessage):
        """添加待发送消息到缓存"""
        await self._hset(
            self.RedisMap.pending_messages, cached_message.id,
            cached_message.model_dump_json(
                exclude_defaults=True,
                exclude_none=True,
                exclude_computed_fields=True
            )
        )

    async def remove_pending_message(self, message_id: str):
        """从缓存中删除待发送消息"""
        await self._hdel(self.RedisMap.pending_messages, message_id)

    async def get_pending_messages(self) -> List[CachedMessage]:
        """获取所有待发送消息"""
        messages = await self._hgetall(self.RedisMap.pending_messages)
        return [CachedMessage.model_validate_json(message) for message in messages.values()]


redis_obj = RedisObj()

__all__ = [
    "CachedMessage",
    "RedisObj",
    "redis_obj"
]
