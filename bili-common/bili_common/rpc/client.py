"""RabbitMQ RPC 通用客户端（基于 FastStream 框架）。

供各系统（RPA-Browser / be-gateway 等）经 RabbitMQ 同步调用 be-message-service /
be-bilibili-crawler 等 RPC 服务端方法，不依赖具体服务的 settings：
`amqp_url` 由调用方在构造时传入。

FastStream 使用 Direct Reply-To 特性，客户端无需手动管理回调队列，
直接调用 broker.request() 即可同步等待响应。

RPC 流程（FastStream Blocking Request）：
1. connect() 调用 broker.start() 建立 RabbitMQ 连接并声明 reply 队列
2. call(routing_key, payload) 调用 broker.request() 发送消息并等待响应
3. FastStream 自动处理 correlation_id 和 reply_to
4. 解析响应消息体为 dict 返回

消息协议简化：请求端直接发送强类型参数模型的 JSON dict，
服务端由 FastStream 自动 validate 为对应 Pydantic 模型，
handler 直接返回 StandardResponse，客户端解析为 dict。

注意：必须使用 broker.start() 而非 broker.connect()：
- start() 会设置 broker.running=True 并声明 RABBIT_REPLY 队列（Direct Reply-To 所需）
- connect() 仅建立底层连接，running 仍为 False，会导致 connected 检查失效
- 关闭时必须使用 broker.stop()（connect() 的逆操作），broker 无 close() 方法
"""

import asyncio
import json
from typing import Any

from faststream.rabbit import RabbitBroker
from loguru import logger


class RpcClient:
    """RabbitMQ RPC 客户端（amqp_url 由调用方注入）。

    生命周期由使用方管理：
    - startup 时调用 connect()
    - shutdown 时调用 close()
    - 执行期间通过 call(routing_key, payload) 发送 RPC 请求
    """

    def __init__(self, amqp_url: str) -> None:
        self._amqp_url = amqp_url
        self._broker = RabbitBroker(amqp_url)

    @property
    def connected(self) -> bool:
        return self._broker.running

    async def connect(self) -> None:
        """建立 RabbitMQ 连接。

        使用 broker.start() 而非 broker.connect()：
        start() 会设置 running=True 并声明 RABBIT_REPLY 队列（Direct Reply-To 所需）。
        """
        if self.connected:
            return
        logger.info("[RpcClient] 正在连接 RabbitMQ...")
        await self._broker.start()
        logger.info("[RpcClient] 已连接 RabbitMQ")

    async def close(self) -> None:
        """关闭连接"""
        if self.connected:
            await self._broker.stop()
            logger.info("[RpcClient] 已断开连接")

    async def call(
        self,
        routing_key: str,
        payload: dict[str, Any],
        timeout: float = 180.0,
    ) -> dict[str, Any]:
        """发送 RPC 请求并等待响应（FastStream Blocking Request）

        利用 FastStream 的 Direct Reply-To 特性，无需手动创建回调队列。

        Args:
            routing_key: RPC routing_key（= 队列名，如 FastapiApp.rpc.get_reserve_lottery）
            payload: RPC 请求参数 dict（强类型参数模型 model_dump 后的 JSON dict）
            timeout: 超时时间（秒），通过 asyncio.wait_for 控制

        Returns:
            RPC 响应 dict（StandardResponse 序列化后的 JSON dict，含 code / msg / data）

        Raises:
            TimeoutError: 请求超时
            ConnectionError: 客户端未连接
        """
        if not self.connected:
            raise ConnectionError("RPC 客户端未连接，请先调用 connect()")

        logger.info(f"[RpcClient] 发送 RPC 请求: routing_key={routing_key}")

        # FastStream broker.request() 使用 Direct Reply-To，自动处理 correlation_id 和 reply_to
        # 通过 asyncio.wait_for 控制超时（FastStream request 的 timeout 参数是发布确认超时，非 RPC 等待超时）
        try:
            msg = await asyncio.wait_for(
                self._broker.request(payload, queue=routing_key),
                timeout=timeout,
            )
        except TimeoutError:
            raise TimeoutError(
                f"RPC 请求超时（{timeout}s）: routing_key={routing_key}"
            )

        # 解析响应消息体（StandardResponse 序列化后的 JSON）
        body = msg.body.decode()
        try:
            raw = json.loads(body)
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"RPC 响应解析失败: {e}")

        logger.info(
            f"[RpcClient] 收到 RPC 响应: routing_key={routing_key} "
            f"code={raw.get('code', '-')} msg={raw.get('msg', '-')}"
        )
        return raw


__all__ = ["RpcClient"]
