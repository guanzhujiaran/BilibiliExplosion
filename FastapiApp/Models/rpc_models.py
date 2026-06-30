"""
RPC 方法名枚举与方法元数据

定义 RPA-Browser ↔ FastapiApp 之间的 RPC 方法注册表。
独立模块以避免 rpc_server 与 handler 之间的循环导入。

- RpcMethodName：RPC 方法名 StrEnum（与 @rpc_subscriber 装饰器一一对应）
- ALLOWED_RPC_METHODS：预设的 RPC 方法元数据白名单（供通用接口返回）

RPC 消息协议已简化：请求端直接发送强类型参数模型的 JSON，
服务端由 FastStream 自动 validate 为对应 Pydantic 模型，handler 直接返回 CommonResponseModel。
不再使用 RpcRequest / RpcResponse 包装类。
"""

from enum import StrEnum

from pydantic import BaseModel, Field


# routing_key 前缀（与 RPA-Browser 侧 system_services.py 保持一致）
ROUTING_KEY_PREFIX = "FastapiApp.rpc"


class RpcMethodName(StrEnum):
    """RPC 业务方法名枚举

    枚举值即 method_name（snake_case），routing_key 自动生成为
    `FastapiApp.rpc.<method_name>`。必须与 controller/v1/mq/lottery_data.py
    中 @rpc_subscriber 装饰的方法名一一对应。
    """

    GET_RESERVE_LOTTERY = "get_reserve_lottery"
    GET_OFFICIAL_LOTTERY = "get_official_lottery"
    GET_CHARGE_LOTTERY = "get_charge_lottery"
    GET_TOPIC_LOTTERY = "get_topic_lottery"
    GET_ALL_LOTTERY = "get_all_lottery"
    GET_OTHERS_LOT_DYN_LIST = "get_others_lot_dyn_list"


def routing_key_for(method_name: str) -> str:
    """根据方法名生成 routing_key

    Args:
        method_name: 方法名（snake_case，如 get_reserve_lottery）

    Returns:
        routing_key（如 FastapiApp.rpc.get_reserve_lottery）
    """
    return f"{ROUTING_KEY_PREFIX}.{method_name}"


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
        description="获取必抽的充电抽奖数据，支持高级筛选",
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
