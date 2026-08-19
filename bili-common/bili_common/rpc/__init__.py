"""bili-common RPC 公共设施（按系统/模块分文件夹组织）。

集中收编各微服务的 RPC「通用设施 + 契约」：

| 模块 | 内容 | 原位置 |
| --- | --- | --- |
| `base` | RpcMethodName 枚举、路由键前缀、白名单 | `bili_common/models/rpc.py` + `push_rpc.py` |
| `safe` | `rpc_safe` 服务端异常转回包装饰器 | `be-message-service/app/mq/rpc_safe.py` |
| `client` | `RpcClient` 通用客户端（FastStream Direct Reply-To） | `RPA-Browser/app/services/mq/rpc_client.py` |
| `lottery` | 抽奖 RPC 契约（be-bilibili-crawler 服务端 ↔ RPA-Browser 客户端） | `bili_common/models/rpc_params.py` |
| `pptr_user` | pptr 用户 RPC 契约（be-message 服务端 ↔ be-gateway 客户端） | `bili_common/models/pptr_user_rpc.py` 等 |
| `push` | 站外推送 RPC 契约（be-message 服务端 ↔ 其它系统客户端） | `bili_common/models/push_rpc.py` |

约定：
- 服务端返回统一 `StandardResponse{code, msg, data}`；异常在 RPC 边界由 `rpc_safe` 翻译成
  `error_response` 回包（不静默、不吞错）。
- 客户端使用 FastStream Direct Reply-To（`amq.rabbitmq.reply-to`）同步等待响应。
- 路由键前缀：`FastapiApp.rpc`（抽奖）/ `message.pptr.rpc`（pptr 用户）/ `message.push.rpc`（推送）。

注意（依赖边界）：
- 本包顶层**只导出纯 SQLModel / Pydantic 契约**（`base` / `lottery` / `pptr_user` / `push`），
  保证任意只依赖 bili-common 的消费方（含 be-bilibili-crawler 等）无需安装额外依赖即可导入。
- `safe`（依赖 loguru）与 `client`（依赖 faststream）为**按需子模块**，由对应微服务显式
  `from bili_common.rpc.safe import rpc_safe` / `from bili_common.rpc.client import RpcClient`
  导入；消费方各自环境已具备这些依赖。
"""

from bili_common.rpc.base import (
    ALLOWED_RPC_METHODS,
    PPTR_RPC_ROUTING_KEY_PREFIX,
    PUSH_RPC_ROUTING_KEY_PREFIX,
    ROUTING_KEY_PREFIX,
    RpcMethodInfo,
    RpcMethodInfoResponse,
    RpcMethodName,
    build_method_responses,
    get_allowed_method_names,
    pptr_routing_key_for,
    push_rpc_routing_key_for,
    routing_key_for,
    validate_rpc_method,
)
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
from bili_common.rpc.pptr_user import (
    PPTR_USER_RPC_CONTRACT,
    PptrAddDailyLoginExpParams,
    PptrAddDailyLoginExpResult,
    PptrAddExpParams,
    PptrAddExpResult,
    PptrAddUsernameRecordParams,
    PptrAddUsernameRecordResult,
    PptrCreateUserParams,
    PptrCreateUserResult,
    PptrGetUserCardParams,
    PptrGetUserInfoParams,
    PptrGetUserLevelParams,
    PptrGetUserNavParams,
    PptrSetResult,
    PptrSetUserDetailParams,
    PptrSetUserLevelParams,
    PptrSetUserRoleParams,
    PptrUpdateUserInfoParams,
    PptrUpdateUserInfoResult,
    PptrUserCard,
    PptrUserLevelInfo,
    PptrUserProfile,
    PptrUserSearchResult,
    UserSearchParams,
)
from bili_common.rpc.push import (
    PUSH_RPC_CONTRACT,
    PushRpcMethodName,
    PushRpcSendNowParams,
    PushRpcSendNowResult,
    PushRpcSendParams,
    PushRpcSendResult,
)
from bili_common.rpc.rpa import (
    GetResourceDetailParams,
    GetResourceDetailResult,
    ResourceDetail,
    RPA_RPC_CONTRACT,
    RpaRpcMethodName,
)

__all__ = [
    # base
    "RpcMethodName",
    "ROUTING_KEY_PREFIX",
    "PPTR_RPC_ROUTING_KEY_PREFIX",
    "PUSH_RPC_ROUTING_KEY_PREFIX",
    "routing_key_for",
    "pptr_routing_key_for",
    "push_rpc_routing_key_for",
    "RpcMethodInfo",
    "RpcMethodInfoResponse",
    "ALLOWED_RPC_METHODS",
    "get_allowed_method_names",
    "build_method_responses",
    "validate_rpc_method",
    # lottery
    "BaseLotteryRpcParams",
    "GetReserveLotteryRpcParams",
    "GetOfficialLotteryRpcParams",
    "GetChargeLotteryRpcParams",
    "GetTopicLotteryRpcParams",
    "GetAllLotteryRpcParams",
    "GetOthersLotDynListRpcParams",
    "RPC_METHOD_PARAMS_MODEL_MAP",
    "RPC_METHOD_PARAMS_FIELD_MAP",
    # pptr_user
    "PptrGetUserInfoParams",
    "PptrGetUserCardParams",
    "PptrCreateUserParams",
    "PptrUpdateUserInfoParams",
    "PptrUserCard",
    "PptrUserProfile",
    "PptrCreateUserResult",
    "PptrUpdateUserInfoResult",
    "PptrGetUserLevelParams",
    "PptrUserLevelInfo",
    "PptrSetUserLevelParams",
    "PptrSetUserDetailParams",
    "PptrSetUserRoleParams",
    "PptrSetResult",
    "PptrAddExpParams",
    "PptrAddExpResult",
    "PptrAddDailyLoginExpParams",
    "PptrAddDailyLoginExpResult",
    "PptrAddUsernameRecordParams",
    "PptrAddUsernameRecordResult",
    "PptrGetUserNavParams",
    "PPTR_USER_RPC_CONTRACT",
    "UserSearchParams",
    "PptrUserSearchResult",
    # push
    "PushRpcMethodName",
    "PushRpcSendParams",
    "PushRpcSendNowParams",
    "PushRpcSendResult",
    "PushRpcSendNowResult",
    "PUSH_RPC_CONTRACT",
    # rpa
    "RpaRpcMethodName",
    "GetResourceDetailParams",
    "GetResourceDetailResult",
    "ResourceDetail",
    "RPA_RPC_CONTRACT",
]
