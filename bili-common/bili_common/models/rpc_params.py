"""
RPC 方法请求参数模型（公共库）

为每个 RpcMethodName 提供独立的、强类型的请求参数模型，
直接由 FastStream 从消息体 validate 出来，无需 RpcRequest 包装。

字段定义与两端（be-bilibili-crawler / RPA-Browser）保持一致，
确保通过 JSON 传递的参数能被正确解析。高级查询类参数统一继承自
公共的 LotteryAdvancedQueryParams，消除两端之前的重复定义。

源定义（两端逐字重复，已合并到此处）：
- be-bilibili-crawler/Models/rpc_params.py
- RPA-Browser/app/models/execution/rpc_method_params.py
"""



from pydantic import Field
from sqlmodel import SQLModel

from bili_common.models.lottery_query import (
    LotteryAdvancedQueryParams,
    OthersLotDynSortEnum,
    OthersLotDynSortOrderEnum,
    TimePresetEnum,
)


class BaseLotteryRpcParams(LotteryAdvancedQueryParams):
    """抽奖 RPC 请求参数基类（继承高级查询参数）

    覆盖分页默认值：RPC 场景默认每页 1000 条，最大 3000。
    """

    page_num: int = Field(
        default=1, ge=1, description="页码，从 1 开始，最小值为 1",
        json_schema_extra={
            "filter_display_name": "页码",
            "filter_widget": "number",
            "filter_description": "分页页码，从 1 开始",
            "filter_placeholder": "输入页码",
        },
    )
    page_size: int = Field(
        default=1000, ge=1, le=3000,
        description="每页数量，默认 1000，最大 3000，最小值为 1",
        json_schema_extra={
            "filter_display_name": "每页条数",
            "filter_widget": "number",
            "filter_description": "每页返回数量",
            "filter_placeholder": "输入每页条数",
        },
    )


class GetReserveLotteryRpcParams(BaseLotteryRpcParams):
    """get_reserve_lottery 方法请求参数 - 获取预约抽奖数据"""
    pass


class GetOfficialLotteryRpcParams(BaseLotteryRpcParams):
    """get_official_lottery 方法请求参数 - 获取官方抽奖数据"""
    pass


class GetChargeLotteryRpcParams(BaseLotteryRpcParams):
    """get_charge_lottery 方法请求参数 - 获取充电抽奖数据"""
    pass


class GetTopicLotteryRpcParams(BaseLotteryRpcParams):
    """get_topic_lottery 方法请求参数 - 获取话题抽奖数据"""
    pass


class GetAllLotteryRpcParams(SQLModel):
    """get_all_lottery 方法请求参数 - 按收录时间和发布时间获取全部抽奖信息"""
    page_num: int = Field(default=1, ge=1, description="页码，从 1 开始，最小值为 1")
    page_size: int = Field(
        default=1000, ge=1, le=3000,
        description="每页数量，默认 1000，最大 3000，最小值为 1",
    )
    created_at_preset: TimePresetEnum | None = Field(
        default=None,
        description="收录时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认不筛选",
    )
    created_at_start: int | None = Field(
        default=None, ge=0, description="收录起始时间（Unix 秒），preset 优先级高于此字段"
    )
    created_at_end: int | None = Field(
        default=None, ge=0, description="收录结束时间（Unix 秒）"
    )
    pub_time_preset: TimePresetEnum | None = Field(
        default=None,
        description="发布时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认不筛选",
    )
    pub_time_start: int | None = Field(
        default=None, ge=0, description="发布起始时间（Unix 秒），preset 优先级高于此字段"
    )
    pub_time_end: int | None = Field(
        default=None, ge=0, description="发布结束时间（Unix 秒）"
    )


class GetOthersLotDynListRpcParams(SQLModel):
    """get_others_lot_dyn_list 方法请求参数 - 获取第三方抽奖动态列表"""
    page_num: int = Field(default=1, ge=1, description="页码，从 1 开始，最小值为 1")
    page_size: int = Field(default=1000, ge=1, le=3000, description="每页数量，最大 3000，最小值为 1")

    sort_by: OthersLotDynSortEnum = Field(
        default=OthersLotDynSortEnum.created_at,
        description="排序字段: pubTime(发布时间)/created_at(收录时间)")
    sort_order: OthersLotDynSortOrderEnum = Field(
        default=OthersLotDynSortOrderEnum.desc,
        description="排序方向: asc/desc")

    is_lot: bool = Field(default=True, description="是否筛选为抽奖的动态")

    created_at_preset: TimePresetEnum | None = Field(
        default=TimePresetEnum.last_30_days, description="收录时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认 30d")
    pub_time_preset: TimePresetEnum | None = Field(
        default=TimePresetEnum.last_30_days, description="发布时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认 30d")

    pub_time_start: int | None = Field(default=None, ge=0, description="发布起始时间（Unix 秒）")
    pub_time_end: int | None = Field(default=None, ge=0, description="发布结束时间（Unix 秒）")
    created_at_start: int | None = Field(default=None, ge=0, description="收录起始时间（Unix 秒）")
    created_at_end: int | None = Field(default=None, ge=0, description="收录结束时间（Unix 秒）")


# ============ 方法名 → 参数模型/字段名映射 ============
# 供 RPA-Browser 端根据 method_name 获取参数模型类型与对应字段名

RPC_METHOD_PARAMS_MODEL_MAP: dict[str, type[SQLModel]] = {
    "get_reserve_lottery": GetReserveLotteryRpcParams,
    "get_official_lottery": GetOfficialLotteryRpcParams,
    "get_charge_lottery": GetChargeLotteryRpcParams,
    "get_topic_lottery": GetTopicLotteryRpcParams,
    "get_all_lottery": GetAllLotteryRpcParams,
    "get_others_lot_dyn_list": GetOthersLotDynListRpcParams,
}

RPC_METHOD_PARAMS_FIELD_MAP: dict[str, str] = {
    "get_reserve_lottery": "get_reserve_lottery_params",
    "get_official_lottery": "get_official_lottery_params",
    "get_charge_lottery": "get_charge_lottery_params",
    "get_topic_lottery": "get_topic_lottery_params",
    "get_all_lottery": "get_all_lottery_params",
    "get_others_lot_dyn_list": "get_others_lot_dyn_list_params",
}


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
