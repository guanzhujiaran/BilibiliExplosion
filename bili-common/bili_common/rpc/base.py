"""RPC 方法契约基础（公共库）。

集中定义 RPC 方法名枚举、各系统路由键前缀、路由键生成函数与白名单，
供 be-bilibili-crawler（RPC 服务端）、RPA-Browser（RPC 客户端）、
be-message-service（RPC 服务端）与 be-gateway（RPC 客户端）统一复用，
确保两端调用契约完全一致。

路由键前缀约定：
- `FastapiApp.rpc.*`      —— 抽奖 RPC（be-bilibili-crawler 服务端 ↔ RPA-Browser 客户端）
- `message.pptr.rpc.*`    —— pptr 用户 RPC（be-message 服务端 ↔ be-gateway 客户端）
- `message.push.rpc.*`    —— 站外推送 RPC（be-message 服务端 ↔ 其它系统客户端）
- `message.rpa.rpc.*`     —— RPA 资源 RPC（RPA-Browser 服务端 ↔ be-message 客户端，2.18.0）

源定义（两端逐字重复，已合并到此处）：
- be-bilibili-crawler/Models/rpc_models.py
- RPA-Browser/app/models/execution/system_services.py
"""

from enum import StrEnum

from pydantic import BaseModel, Field

# RPC 路由键前缀（两端必须保持一致）
ROUTING_KEY_PREFIX = "FastapiApp.rpc"

# pptr 用户相关 RPC 路由键前缀（be-message 为服务端，be-gateway 为客户端）。
# 与 FastapiApp.rpc.* 隔离，避免与 be-bilibili-crawler 的抽奖 RPC 冲突。
PPTR_RPC_ROUTING_KEY_PREFIX = "message.pptr.rpc"

# 站外推送 RPC 路由键前缀（be-message 为服务端，其它系统为客户端）。
# 与 message.pptr.rpc / FastapiApp.rpc 隔离，互不冲突。
PUSH_RPC_ROUTING_KEY_PREFIX = "message.push.rpc"

# RPA 资源 RPC 路由键前缀（RPA-Browser 为服务端，be-message 为客户端，2.18.0）。
# 与 message.pptr.rpc / message.push.rpc / FastapiApp.rpc 隔离，互不冲突。
RPA_RPC_ROUTING_KEY_PREFIX = "message.rpa.rpc"


class RpcMethodName(StrEnum):
    """RPC 业务方法名枚举

    枚举值即 method_name（snake_case），routing_key 自动生成为
    `FastapiApp.rpc.<method_name>`。必须与 controller/v1/mq/lottery_data.py
    中 @rpc_subscriber 装饰的方法名一一对应。

    NONE 表示"不使用 RPC"（走 HTTP 模式），供前端下拉框作为空值选项。
    """

    NONE = ""
    GET_RESERVE_LOTTERY = "get_reserve_lottery"
    GET_OFFICIAL_LOTTERY = "get_official_lottery"
    GET_CHARGE_LOTTERY = "get_charge_lottery"
    GET_TOPIC_LOTTERY = "get_topic_lottery"
    GET_ALL_LOTTERY = "get_all_lottery"
    GET_OTHERS_LOT_DYN_LIST = "get_others_lot_dyn_list"
    # 内部校验（be-message 客户端调用，不进入 ALLOWED_RPC_METHODS 前端白名单）
    CHECK_LOTTERY_EXIST = "check_lottery_exist"

    # pptr 用户相关（be-message 服务端 / be-gateway 客户端）
    GET_USER_INFO = "get_user_info"
    GET_USER_CARD = "get_user_card"
    CREATE_USER = "create_user"
    UPDATE_USER_INFO = "update_user_info"
    GET_USER_LEVEL = "get_user_level"
    SET_USER_LEVEL = "set_user_level"
    SET_USER_DETAIL = "set_user_detail"
    SET_USER_ROLE = "set_user_role"
    SEARCH_USERS = "search_users"
    ADD_EXP = "add_exp"
    ADD_DAILY_LOGIN_EXP = "add_daily_login_exp"
    ADD_USERNAME_RECORD = "add_username_record"
    GET_USER_NAV = "get_user_nav"

    # RPA 资源相关（RPA-Browser 服务端 / be-message 客户端，2.18.0）
    GET_RESOURCE_DETAIL = "get_resource_detail"


def routing_key_for(method_name: str) -> str:
    """根据方法名生成抽奖 RPC 的 routing_key

    Args:
        method_name: 方法名（snake_case，如 get_reserve_lottery）

    Returns:
        routing_key（如 FastapiApp.rpc.get_reserve_lottery）
    """
    return f"{ROUTING_KEY_PREFIX}.{method_name}"


def pptr_routing_key_for(method_name: str) -> str:
    """根据 pptr 用户方法名生成 routing_key（前缀 message.pptr.rpc）"""
    return f"{PPTR_RPC_ROUTING_KEY_PREFIX}.{method_name}"


def push_rpc_routing_key_for(method_name: str) -> str:
    """根据推送 RPC 方法名生成 routing_key（前缀 message.push.rpc）"""
    return f"{PUSH_RPC_ROUTING_KEY_PREFIX}.{method_name}"


def rpa_rpc_routing_key_for(method_name: str) -> str:
    """根据 RPA 资源 RPC 方法名生成 routing_key（前缀 message.rpa.rpc，2.18.0）"""
    return f"{RPA_RPC_ROUTING_KEY_PREFIX}.{method_name}"


class RpcMethodInfo(BaseModel):
    """RPC 业务方法描述"""

    method_name: str = Field(description="方法名（snake_case，用于生成 routing_key）")
    display_name: str = Field(description="前端显示名称")
    description: str = Field(default="", description="方法用途说明")


class RpcMethodInfoResponse(RpcMethodInfo):
    """RPC 业务方法响应（供前端展示）"""

    routing_key: str = Field(description="routing_key（供前端调试/展示用）")


# 预设的 RPC 业务方法白名单（写死，不允许前端随意调用其他方法）
# method_name 必须与 controller/v1/mq/lottery_data.py 的 @rpc_subscriber 保持一致
ALLOWED_RPC_METHODS: list[RpcMethodInfo] = [
    RpcMethodInfo(
        method_name=RpcMethodName.GET_RESERVE_LOTTERY,
        display_name="获取预约抽奖数据",
        description="获取必抽的预约抽奖数据，支持高级筛选",
    ),
    RpcMethodInfo(
        method_name=RpcMethodName.GET_OFFICIAL_LOTTERY,
        display_name="获取官方抽奖数据",
        description="获取必抽的官方抽奖数据，支持高级筛选",
    ),
    RpcMethodInfo(
        method_name=RpcMethodName.GET_CHARGE_LOTTERY,
        display_name="获取充电抽奖数据",
        description="获取必充的充电抽奖数据，支持高级筛选",
    ),
    RpcMethodInfo(
        method_name=RpcMethodName.GET_TOPIC_LOTTERY,
        display_name="获取话题抽奖数据",
        description="获取所有话题抽奖数据（分页+筛选）",
    ),
    RpcMethodInfo(
        method_name=RpcMethodName.GET_ALL_LOTTERY,
        display_name="获取一轮全部抽奖",
        description="获取指定轮次的所有抽奖信息",
    ),
    RpcMethodInfo(
        method_name=RpcMethodName.GET_OTHERS_LOT_DYN_LIST,
        display_name="获取第三方抽奖动态列表",
        description="获取第三方抽奖动态列表（分页+排序+时间筛选）",
    ),
]


def get_allowed_method_names() -> list[str]:
    """获取所有允许的方法名列表"""
    return [m.method_name for m in ALLOWED_RPC_METHODS]


def build_method_responses() -> list[RpcMethodInfoResponse]:
    """构建供前端展示的方法响应列表"""
    return [
        RpcMethodInfoResponse(
            method_name=m.method_name,
            display_name=m.display_name,
            description=m.description,
            routing_key=routing_key_for(m.method_name),
        )
        for m in ALLOWED_RPC_METHODS
    ]


def validate_rpc_method(method_name: str) -> tuple[bool, str]:
    """校验方法名是否属于允许的 RPC 业务方法

    Args:
        method_name: 方法名（如 get_reserve_lottery）

    Returns:
        (是否通过, 失败原因)
    """
    if not method_name:
        return False, "方法名不能为空"

    allowed = get_allowed_method_names()
    if method_name in allowed:
        return True, ""

    return False, (
        f"仅允许调用预设的 RPC 业务方法，"
        f"当前方法名 '{method_name}' 不在允许列表中。"
        f"允许的方法: {', '.join(allowed)}"
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
