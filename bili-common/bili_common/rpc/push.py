"""「站外推送」RPC 契约（公共库）。

be-message-service 作为 RPC 服务端，其它系统（be-gateway / RPA-Browser /
be-bilibili-crawler 等）经 RabbitMQ 按 `message.push.rpc.<method>` 同步调用本契约，
完成「站外提醒」类推送，不再依赖 HTTP 网关转发与请求头注入的 `x-bili-*` 用户信息。

路由键前缀 `message.push.rpc` 见 `bili_common.rpc.base`。

与既有 `message.pptr.rpc.*` 模式对齐：
- 客户端发布到 topic exchange `message_exchange`，用 direct reply-to
  （`amq.rabbitmq.reply-to`）收取响应；
- 服务端返回 `StandardResponse{code, msg, data}`，异常在 RPC 边界翻译成
  `error_response` 回包；
- 请求 / 响应模型统一用 SQLModel，保证两端契约一致。

HTTP `/api/v1/message/push` 与 RPC 并存：HTTP 面向终端用户 / 浏览器侧，
RPC 面向服务端系统，二者都落到同一套 `PushMessageService` 执行体。
"""

from bili_common.models import StrEnumAutoDoc

from sqlmodel import SQLModel, Field

from bili_common.models.push import PushChannelConfig


class PushRpcMethodName(StrEnumAutoDoc):
    """站外推送 RPC 业务方法名枚举。

    枚举值即 method_name，routing_key 自动生成为 `message.push.rpc.<method_name>`。
    """

    PUSH_MESSAGE = "push_message"
    SEND_PUSH_NOW = "send_push_now"


# ---------------------------------------------------------------------------
# 请求参数
# ---------------------------------------------------------------------------


class PushRpcSendParams(SQLModel):
    """投递推送消息到队列（push_message，异步）。

    等价 HTTP `POST /api/v1/message/push`。服务端收到后把消息投递到
    `message.push` 队列，由消费者异步分发到各渠道（不阻塞调用方）。
    """

    title: str = Field(description="推送标题")
    content: str = Field(description="推送正文")
    # pushme/pushplus 的模板类型，例如 text/markdown/html/json 等
    push_type: str | None = Field(default="text", description="推送模板类型")
    # 渠道配置；为空时回落到 message-service 的全局环境变量配置
    config: PushChannelConfig | None = Field(default=None, description="推送渠道配置（可选）")
    # 来源标签，可选；非空时服务端拼进标题前缀，便于区分推送来源
    user_label: str | None = Field(default=None, description="来源用户标签（拼进标题前缀）")


class PushRpcSendNowParams(SQLModel):
    """立即发送推送（send_push_now，同步）。

    等价 HTTP `POST /api/v1/message/push/test`。服务端同步执行渠道降级分发，
    调用方需等待渠道返回结果；适合测试 / 低频即时提醒场景。
    """

    title: str = Field(description="推送标题")
    content: str = Field(description="推送正文")
    # pushme/pushplus 的模板类型，例如 text/markdown/html/json 等
    push_type: str | None = Field(default="text", description="推送模板类型")
    # 渠道配置；为空时使用 message-service 的全局环境变量配置
    config: PushChannelConfig | None = Field(default=None, description="推送渠道配置（可选）")
    # 来源标签，可选；非空时服务端拼进标题前缀，便于区分推送来源
    user_label: str | None = Field(default=None, description="来源用户标签（拼进标题前缀）")


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


class PushRpcSendResult(SQLModel):
    """push_message 返回结果（已投递到队列）。"""

    title: str = Field(description="实际推送标题（含来源标签前缀）")
    queued: bool = Field(default=True, description="true=已投递到 message.push 队列")


class PushRpcSendNowResult(SQLModel):
    """send_push_now 返回结果（同步发送结果）。"""

    success: bool = Field(description="true=至少一个渠道推送成功")
    message: str = Field(default="", description="结果说明（成功 / 无可用渠道 / 失败原因）")
    # 本次成功推送所经过的渠道（由 message-service 统一分发）
    sent_channels: list[str] = Field(default_factory=list, description="成功推送的渠道列表")


# 方法名 -> 请求模型 -> 响应模型 的契约映射（仅供文档 / 校验参考）
PUSH_RPC_CONTRACT: dict[str, tuple[type[SQLModel], type[SQLModel]]] = {
    PushRpcMethodName.PUSH_MESSAGE: (PushRpcSendParams, PushRpcSendResult),
    PushRpcMethodName.SEND_PUSH_NOW: (PushRpcSendNowParams, PushRpcSendNowResult),
}


__all__ = [
    "PushRpcMethodName",
    "PushRpcSendParams",
    "PushRpcSendNowParams",
    "PushRpcSendResult",
    "PushRpcSendNowResult",
    "PUSH_RPC_CONTRACT",
]
