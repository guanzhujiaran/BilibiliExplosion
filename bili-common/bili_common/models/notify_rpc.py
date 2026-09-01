"""「系统通知」RPC 契约（兼容转发层）。

实际定义已迁移至 `bili_common.rpc.notify`（按系统分模块组织），
路由键前缀 / 生成函数见 `bili_common.rpc.base`，
本文件仅作为兼容入口 re-export，保证存量引用零改动。
"""

from bili_common.models.notify import NotifyLevelEnum, NotifyTargetTypeEnum
from bili_common.rpc.base import (
    NOTIFY_RPC_ROUTING_KEY_PREFIX,
    notify_rpc_routing_key_for,
)
from bili_common.rpc.notify import (
    NOTIFY_RPC_CONTRACT,
    NotifyRpcMethodName,
    PublishNotifyParams,
    PublishNotifyResult,
)

__all__ = [
    "NOTIFY_RPC_CONTRACT",
    "NOTIFY_RPC_ROUTING_KEY_PREFIX",
    "NotifyLevelEnum",
    "NotifyRpcMethodName",
    "NotifyTargetTypeEnum",
    "PublishNotifyParams",
    "PublishNotifyResult",
    "notify_rpc_routing_key_for",
]
