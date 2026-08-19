"""抽奖 RPC 请求参数模型（兼容转发层）。

实际定义已迁移至 `bili_common.rpc.lottery`（按系统分模块组织），
本文件仅作为兼容入口 re-export，保证存量引用零改动。
"""

from bili_common.rpc.lottery import (
    BaseLotteryRpcParams,
    GetAllLotteryRpcParams,
    GetChargeLotteryRpcParams,
    GetOfficialLotteryRpcParams,
    GetOthersLotDynListRpcParams,
    GetReserveLotteryRpcParams,
    GetTopicLotteryRpcParams,
    RPC_METHOD_PARAMS_FIELD_MAP,
    RPC_METHOD_PARAMS_MODEL_MAP,
)

__all__ = [
    "BaseLotteryRpcParams",
    "GetReserveLotteryRpcParams",
    "GetOfficialLotteryRpcParams",
    "GetChargeLotteryRpcParams",
    "GetTopicLotteryRpcParams",
    "GetAllLotteryRpcParams",
    "GetOthersLotDynListRpcParams",
    "RPC_METHOD_PARAMS_MODEL_MAP",
    "RPC_METHOD_PARAMS_FIELD_MAP",
]
