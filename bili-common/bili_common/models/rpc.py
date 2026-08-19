"""RPC 方法契约（兼容转发层）。

实际定义已迁移至 `bili_common.rpc.base`（按系统分模块组织），
本文件仅作为兼容入口 re-export，保证存量引用零改动。
"""

from bili_common.rpc.base import (
    ALLOWED_RPC_METHODS,
    PPTR_RPC_ROUTING_KEY_PREFIX,
    PUSH_RPC_ROUTING_KEY_PREFIX,
    RPA_RPC_ROUTING_KEY_PREFIX,
    ROUTING_KEY_PREFIX,
    RpcMethodInfo,
    RpcMethodInfoResponse,
    RpcMethodName,
    build_method_responses,
    get_allowed_method_names,
    pptr_routing_key_for,
    push_rpc_routing_key_for,
    routing_key_for,
    rpa_rpc_routing_key_for,
    validate_rpc_method,
)

__all__ = [
    "RpcMethodName",
    "ROUTING_KEY_PREFIX",
    "PPTR_RPC_ROUTING_KEY_PREFIX",
    "PUSH_RPC_ROUTING_KEY_PREFIX",
    "RPA_RPC_ROUTING_KEY_PREFIX",
    "routing_key_for",
    "pptr_routing_key_for",
    "push_rpc_routing_key_for",
    "rpa_rpc_routing_key_for",
    "RpcMethodInfo",
    "RpcMethodInfoResponse",
    "ALLOWED_RPC_METHODS",
    "get_allowed_method_names",
    "build_method_responses",
    "validate_rpc_method",
]
