"""「站外推送」消息队列公共发布函数（fire-and-forget，不需要管返回）。

任何系统（RPA-Browser / be-gateway / be-bilibili-crawler 等）需要向
be-message-service 投递「站外推送」请求时，直接调用 `publish_push_message()`：

- 把 `PushMessagePayload` 发布到 `message_exchange`（TOPIC / durable）的
  `message.push` 路由，即返回；
- **不等待** be-message 消费与第三方渠道（PushMe / PushPlus 等）发送结果，
  属于 fire-and-forget 的消息队列推送方式；
- 队列绑定由 be-message-service 维护，本模块**只发布不声明队列**，
  避免重复绑定把 `message_queue` 截获成 `message.#` 而吃掉 pptr RPC 请求。

与 RPC 方式（`bili_common.rpc.push` 的 `message.push.rpc.*`）互补：
RPC 同步等待返回；本函数只负责推送、不需要管返回。

约定：
- `amqp_url` 由调用方传入（不依赖任何服务的 settings）；缺省从环境变量
  `RABBITMQ_URL` 读取，仍无则回退 `amqp://guest:guest@localhost:5672/`。
- 发布失败**不静默**：记录日志并上抛异常，与「不静默、不吞错」的约定一致。
- 依赖 faststream，为**按需子模块**（不进入 `core/__init__.py` 顶层导出），
  调用方环境需具备 faststream（RPA-Browser / be-message-service 均已具备）。
"""

import os

from typing import Optional, Union

from bili_common.models.push import PushChannelConfig, PushMessagePayload
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange
from loguru import logger

# be-message-service 消费 `message_queue`（routing_key=message.push）的固定路由键
PUSH_ROUTING_KEY = "message.push"

# 交换机定义与 be-message-service/app/core/broker.py 保持一致（TOPIC / durable）
push_exchange = RabbitExchange(
    "message_exchange",
    type=ExchangeType.TOPIC,
    durable=True,
    auto_delete=False,
)

# 按 amqp_url 缓存的 broker 实例：懒连接，首次发布时建立，之后复用
_brokers: dict[str, RabbitBroker] = {}


def _get_broker(amqp_url: str | None = None) -> RabbitBroker:
    """获取（并按需创建）指定 amqp_url 的 broker 实例。"""
    url = amqp_url or os.getenv("RABBITMQ_URL") or "amqp://guest:guest@localhost:5672/"
    broker = _brokers.get(url)
    if broker is None:
        broker = RabbitBroker(url)
        _brokers[url] = broker
    return broker


def _normalize_config(config: Optional[Union[PushChannelConfig, dict]]) -> PushChannelConfig | None:
    """config 兼容 PushChannelConfig / dict / None，统一转成 PushChannelConfig。"""
    if config is None:
        return None
    if isinstance(config, PushChannelConfig):
        return config
    return PushChannelConfig(**config)


async def publish_push_message(
    title: str,
    content: str,
    push_type: Optional[str] = "text",
    config: Optional[Union[PushChannelConfig, dict]] = None,
    amqp_url: Optional[str] = None,
) -> None:
    """发布一条「站外推送」请求到 be-message 的 `message.push` 队列。

    Args:
        title: 推送标题
        content: 推送正文
        push_type: pushme/pushplus 的模板类型，如 text/markdown/html/json 等
        config: 渠道配置，优先传 PushChannelConfig（SQLModel）；若调用方只有 dict
            （例如 NotificationConfig.model_dump()），则就地构造为 PushChannelConfig
        amqp_url: RabbitMQ 连接串；缺省从环境变量 RABBITMQ_URL 读取，再缺省回退本地

    Raises:
        Exception: 发布失败时上抛（不静默吞错），调用方可按需 catch
    """
    payload = PushMessagePayload(
        title=title,
        content=content,
        push_type=push_type,
        config=_normalize_config(config),
    )
    broker = _get_broker(amqp_url)
    # 懒连接：首次发布时建立连接，之后复用
    if not getattr(broker, "_connection", None):
        await broker.start()
    await broker.publish(
        message=payload,
        exchange=push_exchange,
        routing_key=PUSH_ROUTING_KEY,
    )
    logger.debug(f"已发布推送消息到 message 队列: {title}")


__all__ = ["PUSH_ROUTING_KEY", "push_exchange", "publish_push_message"]
