"""RPA 浏览器操作日志的「生产端」发布函数（生产 / 消费拆分，fire-and-forget）。

RPA-Browser 执行浏览器操作会产生操作日志。为把「日志落库」与「业务执行」解耦，
日志不再在业务线程里同步写库，而是投递到 RabbitMQ，由同进程内的消费者
（RPA-Browser/app/services/execution/action_log_consumer.py）异步落库：

- 发布到独立交换机 `rpa_log_exchange`（TOPIC / durable）的 `rpa.action.log` 路由即返回，
  **不等待**消费与落库结果，属于 fire-and-forget；
- ⚠️ 刻意使用**独立交换机**，不复用 `message_exchange`：见
  `bili_common.core.message_pub` 的说明——复用会把 be-message 的 `message_queue`
  绑定截获成 `message.#`，吃掉 pptr RPC 请求；
- 队列 `rpa_action_log_queue` 的声明与绑定由**消费端**维护，本模块只发布不声明队列。

约定：
- `amqp_url` 由调用方传入；缺省从环境变量 `RABBITMQ_URL` 读取，仍无则回退本地；
- 复用 `bili_common.core.message_pub` 的 broker 单例（同进程内共享连接）；
- 发布失败**不静默**：上抛异常，由调用方（action_logger）回落为同步直写；
- 发布带 `persist=True`（持久化消息），配合消费端 durable 队列，
  RabbitMQ 重启不丢日志；幂等由消费端 `log_id` 唯一键保证。
- 依赖 faststream，为**按需子模块**（不进入 `core/__init__.py` 顶层导出），
  调用方环境需具备 faststream（RPA-Browser 已具备）。
"""

from __future__ import annotations

from typing import Any, Optional

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange
from loguru import logger
from sqlmodel import Field, SQLModel

from bili_common.core.message_pub import _get_broker

# 消息结构版本号：消费端据此做兼容处理（未来字段变更时递增）
ACTION_LOG_SCHEMA_VERSION = 1

# 独立交换机 / 队列 / 路由键（须与消费端 action_log_consumer.py 保持一致）
ACTION_LOG_EXCHANGE_NAME = "rpa_log_exchange"
ACTION_LOG_QUEUE_NAME = "rpa_action_log_queue"
ACTION_LOG_ROUTING_KEY = "rpa.action.log"

# 交换机定义（TOPIC / durable，与消费端声明保持一致）
action_log_exchange = RabbitExchange(
    ACTION_LOG_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True,
    auto_delete=False,
)


class ActionLogMessage(SQLModel):
    """操作日志队列消息体。

    `record` 为 ActionLogRecord 的 JSON 快照（`model_dump(mode="json")` 结果），
    与 RPA-Browser 的投递端 / 消费端共用本模型以保证契约一致。
    """

    model_config = {"extra": "ignore"}  # type: ignore[assignment]

    schema_version: int = Field(default=ACTION_LOG_SCHEMA_VERSION)
    record: dict[str, Any] = Field(default_factory=dict)


async def publish_action_log(
    payload: ActionLogMessage | dict[str, Any],
    amqp_url: Optional[str] = None,
) -> None:
    """发布一条操作日志到 `rpa.action.log`（fire-and-forget）。

    Args:
        payload: ActionLogMessage（推荐）或等价 dict
        amqp_url: RabbitMQ 连接串；缺省从环境变量 `RABBITMQ_URL` 读取

    Raises:
        Exception: 发布失败时上抛（不静默吞错），调用方回落为同步直写
    """
    message = (
        payload
        if isinstance(payload, ActionLogMessage)
        else ActionLogMessage.model_validate(payload)
    )
    broker: RabbitBroker = _get_broker(amqp_url)
    # 懒连接：首次发布时建立连接，之后复用
    if not getattr(broker, "_connection", None):
        await broker.start()
    await broker.publish(
        message=message,
        exchange=action_log_exchange,
        routing_key=ACTION_LOG_ROUTING_KEY,
        # 持久化消息：配合消费端 durable 队列，RabbitMQ 重启不丢日志
        persist=True,
    )
    logger.debug(
        f"已发布操作日志到 rpa.action.log: log_id={message.record.get('log_id')}"
    )


__all__ = [
    "ACTION_LOG_SCHEMA_VERSION",
    "ACTION_LOG_EXCHANGE_NAME",
    "ACTION_LOG_QUEUE_NAME",
    "ACTION_LOG_ROUTING_KEY",
    "ActionLogMessage",
    "action_log_exchange",
    "publish_action_log",
]