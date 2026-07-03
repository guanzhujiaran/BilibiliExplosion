"""
RabbitMQ RPC 服务端（基于 FastStream 框架）

使用 @rpc_subscriber 装饰器注册 RPC 函数，handler 直接接收强类型参数模型，
直接返回 CommonResponseModel，全程由 FastStream + Pydantic 做参数校验和序列化。

router 实例直接复用 Service/MQ/base/MQClient/base.py 中的 RabbitRouter，
由 FastAPI 通过 app.include_router(MqController.router) 自动管理连接和关闭。

RPC handler 注册方式：在 mq_controller.py 末尾导入 lottery_data 模块，
触发 @rpc_subscriber 装饰器执行，将 subscriber 注册到 router 上。

消息处理流程：
1. FastStream 接收 RabbitMQ 消息，自动将 body JSON validate 为 params_model
2. handler 处理后返回 CommonResponseModel，FastStream 自动序列化并发送到 reply_to

超时控制：
- 默认超时时间 DEFAULT_RPC_TIMEOUT 秒，超时后服务器主动取消内部 Task（CancelledError）
  释放数据库连接、HTTP 客户端等资源，避免长尾请求堆积导致负载升高
- 使用 asyncio.wait_for 而非 asyncio.timeout：wait_for 在独立的内部 Task 上运行 handler，
  超时只取消内部 Task，不影响 FastStream subscriber task，避免后续 _publish 步骤被误取消
- 装饰器可通过 timeout 参数覆盖默认值（None 表示不限制）
- 超时返回 code=504 的错误响应

消息确认策略：
- 使用 AckPolicy.ACK_FIRST：消息在 handler 执行前就被 ack
- 避免 _publish 失败后 FastStream 尝试 reject → ChannelInvalidStateError → 消息未 ack →
  RabbitMQ 重新投递 → 无限重试循环
- RPC 模式下客户端有自己的超时机制，服务端不需要重试

连接保活：
- broker_url 中配置 heartbeat=180 秒，避免 handler 执行时间较长时
  RabbitMQ heartbeat 超时导致连接关闭、channel 失效

使用方式：
    from controller.v1.mq.rpc_server import rpc_subscriber
    from Models.rpc_models import RpcMethodName
    from Models.rpc_params import GetReserveLotteryRpcParams

    @rpc_subscriber(RpcMethodName.GET_RESERVE_LOTTERY, GetReserveLotteryRpcParams)
    async def handle_get_reserve_lottery(params: GetReserveLotteryRpcParams) -> CommonResponseModel:
        ...
"""
import asyncio
from faststream import AckPolicy
from pydantic import BaseModel
from Service.MQ.base.MQClient.base import router
from log.base_log import MQ_logger as logger
from Models.rpc_models import RpcMethodName, ROUTING_KEY_PREFIX
from Models.common import CommonResponseModel

# RPC 默认超时时间（秒）：超时后服务器主动取消任务以释放资源
DEFAULT_RPC_TIMEOUT: float = 60.0


def rpc_subscriber(
    method_name: RpcMethodName | str,
    params_model: type[BaseModel],
    timeout: float | None = DEFAULT_RPC_TIMEOUT,
):
    """RPC subscriber 装饰器

    基于 @router.subscriber，FastStream 自动将消息体 JSON validate 为 params_model，
    handler 直接接收强类型参数，返回 CommonResponseModel 即可。

    超时机制：使用 asyncio.wait_for 在独立内部 Task 上运行 handler，超时取消该内部 Task，
    CancelledError 会中断 handler 内部所有 await 中的协程（DB 查询、HTTP 请求等），及时释放资源。
    不使用 asyncio.timeout 是因为它会取消当前 FastStream subscriber task，导致后续 _publish
    步骤被误取消，引发 ChannelInvalidStateError。

    Args:
        method_name: RPC 方法名（推荐使用 RpcMethodName 枚举，也可传 str）
                    routing_key 自动生成为 `FastapiApp.rpc.<method_name>`
        params_model: 该方法的请求参数 Pydantic 模型类，FastStream 自动从消息体 validate
        timeout: 超时时间（秒），默认 DEFAULT_RPC_TIMEOUT；
                 None 表示不限制（不推荐，可能堆积长尾请求）

    用法：
        @rpc_subscriber(RpcMethodName.GET_RESERVE_LOTTERY, GetReserveLotteryRpcParams)
        async def handle_get_reserve_lottery(params: GetReserveLotteryRpcParams) -> CommonResponseModel:
            ...

        # 为慢方法单独设置更长超时
        @rpc_subscriber(RpcMethodName.GET_RESERVE_LOTTERY, GetReserveLotteryRpcParams, timeout=120)
        async def handle_get_reserve_lottery(params: GetReserveLotteryRpcParams) -> CommonResponseModel:
            ...
    """
    method_name_str = method_name.value if isinstance(method_name, RpcMethodName) else str(method_name)
    routing_key = f"{ROUTING_KEY_PREFIX}.{method_name_str}"

    def decorator(func):
        # ACK_FIRST：消息在 handler 执行前就被 ack，避免 _publish 失败后
        # FastStream 尝试 reject → ChannelInvalidStateError → 消息未 ack →
        # RabbitMQ 重新投递 → 无限重试循环。
        # RPC 模式下客户端有自己的超时机制，服务端不需要重试。
        @router.subscriber(routing_key, ack_policy=AckPolicy.ACK_FIRST)
        async def wrapper(params: params_model) -> CommonResponseModel:
            try:
                # 安全日志：避免直接 {params} 触发 __str__/__repr__，
                # CustomBaseModel 的 @computed_field 在某些场景下会触发
                # __getattr__ 访问 __private_attributes__ 失败
                try:
                    params_repr = params.model_dump_json(indent=2)
                except Exception:
                    params_repr = f"<{type(params).__name__} (序列化失败)>"
                logger.info(
                    f"[RpcServer] 收到 RPC 请求: {routing_key}\n{params_repr}"
                )
                # asyncio.wait_for 在独立的内部 Task 上运行 handler，
                # 超时只取消内部 Task（CancelledError 中断 handler 内所有 await，
                # 释放 DB 连接、HTTP 客户端等资源），不影响当前 FastStream subscriber task，
                # 避免后续 _publish 步骤被误取消导致 ChannelInvalidStateError
                result = await asyncio.wait_for(func(params), timeout=timeout)
                return result
            except TimeoutError:
                logger.exception(
                    f"[RpcServer] handler 执行超时: {routing_key} (timeout={timeout}s)"
                )
                return CommonResponseModel(
                    code=504, msg=f"RPC 请求超时（{timeout}s）: {routing_key}"
                )
            except KeyError as e:
                logger.exception(f"[RpcServer] handler 参数缺失: {routing_key} - {e}")
                return CommonResponseModel(code=400, msg=f"参数缺失: {e}")
            except ValueError as e:
                logger.exception(f"[RpcServer] handler 参数格式错误: {routing_key} - {e}")
                return CommonResponseModel(code=400, msg=f"参数格式错误: {e}")
            except Exception as e:
                logger.exception(f"[RpcServer] handler 执行异常: {routing_key} - {e}")
                return CommonResponseModel(code=500, msg=f"handler 执行异常: {e}")
            
        return wrapper

    return decorator
