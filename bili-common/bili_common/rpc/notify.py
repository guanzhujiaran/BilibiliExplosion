"""「系统通知」RPC 契约（公共库）。

be-message-service 作为 RPC 服务端，其它系统（be-gateway / RPA-Browser /
be-bilibili-crawler 等）经 RabbitMQ 按 `message.notify.rpc.<method>` 同步调用
本契约，发布站内系统通知（写入 `msg_notify`），不再依赖 HTTP 网关转发与请求头
注入的 `x-bili-*` 用户信息。

路由键前缀 `message.notify.rpc` 见 `bili_common.rpc.base`。

与既有 `message.push.rpc.*` / `message.pptr.rpc.*` 模式对齐：
- 客户端发布到 topic exchange `message_exchange`，用 direct reply-to
  （`amq.rabbitmq.reply-to`）收取响应；
- 服务端返回 `StandardResponse{code, msg, data}`，异常在 RPC 边界由 `rpc_safe`
  翻译成 `error_response` 回包（不静默、不吞错）；
- 请求 / 响应模型统一用 SQLModel，保证两端契约一致。

管理端 HTTP `POST /api/v1/message/notify/admin/create` 与 RPC 并存：
HTTP 面向管理员浏览器侧，RPC 面向服务端系统，二者落到同一套 `NotifyService`
执行体（`NotifyService.create` / `create_idempotent`）。

客户端调用示例（FastStream Direct Reply-To）：:

    from bili_common.rpc.client import RpcClient
    from bili_common.rpc import (
        NotifyRpcMethodName,
        PublishNotifyParams,
        notify_rpc_routing_key_for,
    )

    client = RpcClient(amqp_url)
    await client.connect()
    resp = await client.call(
        notify_rpc_routing_key_for(NotifyRpcMethodName.PUBLISH_NOTIFY),
        PublishNotifyParams(title="...", content="...", target_value="12345").model_dump(),
    )
"""

from sqlmodel import Field, SQLModel

from bili_common.models import StrEnumAutoDoc
from bili_common.models.notify import NotifyLevelEnum, NotifyTargetTypeEnum


class NotifyRpcMethodName(StrEnumAutoDoc):
    """系统通知 RPC 业务方法名枚举。

    枚举值即 method_name，routing_key 自动生成为 `message.notify.rpc.<method_name>`。
    """

    PUBLISH_NOTIFY = "publish_notify"


# ---------------------------------------------------------------------------
# 请求参数
# ---------------------------------------------------------------------------


class PublishNotifyParams(SQLModel):
    """发布系统通知（publish_notify，同步写库）。

    等价管理端 HTTP `POST /api/v1/message/notify/admin/create`：服务端写入
    `msg_notify` 一行，随后由既有 `notify_push` 链路异步投递到用户会话。

    **幂等**：对 `CUSTOM` + 单个 mid 的定向通知，服务端按
    `(target_value, title)` 判重，重复调用返回同一条 `notify_id`
    （`duplicated=True`），不会重复通知用户；面向全体 / 角色 / 等级 / VIP 的通知
    每条本就独立，不判重。
    """

    title: str = Field(description="通知标题")
    content: str = Field(description="通知正文")
    target_type: NotifyTargetTypeEnum = Field(
        default=NotifyTargetTypeEnum.CUSTOM, description="目标用户类型"
    )
    target_value: str | None = Field(
        default=None,
        description="目标值：custom 填 mid（可逗号分隔多个）、role 填 root/normal、level 填最低等级",
    )
    level: NotifyLevelEnum = Field(
        default=NotifyLevelEnum.NORMAL, description="通知重要级别"
    )
    jump_url: str | None = Field(default=None, description="跳转链接")
    publish_now: bool = Field(default=True, description="是否立即发布（False 存为草稿）")
    creator_mid: int = Field(default=0, description="发布者 mid，0 表示系统自动发布")


# ---------------------------------------------------------------------------
# 响应
# ---------------------------------------------------------------------------


class PublishNotifyResult(SQLModel):
    """publish_notify 返回结果。"""

    notify_id: int = Field(description="通知 id（幂等命中时为既有通知 id）")
    duplicated: bool = Field(default=False, description="true=幂等命中，未重复写入")


# 方法名 -> 请求模型 -> 响应模型 的契约映射（仅供文档 / 校验参考）
NOTIFY_RPC_CONTRACT: dict[str, tuple[type[SQLModel], type[SQLModel]]] = {
    NotifyRpcMethodName.PUBLISH_NOTIFY: (PublishNotifyParams, PublishNotifyResult),
}


__all__ = [
    "NOTIFY_RPC_CONTRACT",
    "NotifyRpcMethodName",
    "PublishNotifyParams",
    "PublishNotifyResult",
]
