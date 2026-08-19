"""「站外推送」RPC 契约（兼容转发层）。

实际定义已迁移至 `bili_common.rpc.push`（按系统分模块组织），
路由键前缀 / 生成函数见 `bili_common.rpc.base`，
本文件仅作为兼容入口 re-export，保证存量引用零改动。
"""

from bili_common.rpc.base import (
    PUSH_RPC_ROUTING_KEY_PREFIX,
    push_rpc_routing_key_for,
)
from bili_common.rpc.push import (
    PUSH_RPC_CONTRACT,
    PushRpcMethodName,
    PushRpcSendNowParams,
    PushRpcSendNowResult,
    PushRpcSendParams,
    PushRpcSendResult,
)

__all__ = [
    "PUSH_RPC_ROUTING_KEY_PREFIX",
    "PushRpcMethodName",
    "push_rpc_routing_key_for",
    "PushRpcSendParams",
    "PushRpcSendNowParams",
    "PushRpcSendResult",
    "PushRpcSendNowResult",
    "PUSH_RPC_CONTRACT",
]
