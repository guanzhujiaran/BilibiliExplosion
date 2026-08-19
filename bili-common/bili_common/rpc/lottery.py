"""抽奖系统 RPC 契约（公共库）。

be-bilibili-crawler（RPC 服务端）与 RPA-Browser（RPC 客户端）统一复用，
确保两端调用契约完全一致。路由键前缀 `FastapiApp.rpc`（见 `bili_common.rpc.base`）。

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


# ============ 内部校验契约（be-message 客户端 → be-bilibili-crawler，2.20.0）============
# 该契约供 be-message 的 LotteryRpcClient 调用，校验 lottery 资源存在性；
# 不进入 RPC_METHOD_PARAMS_MODEL_MAP / FIELD_MAP（那两张表仅供 RPA-Browser 前端下拉使用）。


class CheckLotteryExistRpcParams(SQLModel):
    """check_lottery_exist 方法请求参数。

    `lottery_ids` 优先（批量查询）；为空时回退到单个 `lottery_id`。
    """

    lottery_id: int | None = Field(default=None, description="lottery 主键（Lotdata.lottery_id），单查用")
    lottery_ids: list[int] = Field(default_factory=list, description="lottery_id 批量列表（批量查，优先于 lottery_id）")


class LotteryDetailItem(SQLModel):
    """lottery 单个资源详情（批量响应元素）。"""

    lottery_id: int = Field(description="lottery 主键")
    exists: bool = Field(default=False, description="lottery 是否存在")
    title: str | None = Field(default=None, description="抽奖标题（Lotdata.first_prize_cmt）")
    cover: str | None = Field(default=None, description="封面图链接（Lotdata.first_prize_pic，无则空）")
    jumpUrl: str | None = Field(default=None, description="跳转链接（Lotdata.lottery_detail_url，缺省降级为空）")


class CheckLotteryExistRpcResult(SQLModel):
    """check_lottery_exist 方法响应数据。

    除存在性外，顺带返回 lottery 基础详情（title/cover/jumpUrl），
    供 be-message 读取动态时对 RESOURCE=lottery 节点实时填充 attach 卡片信息
    （不依赖数据库快照，2.20.1 起）。
    批量请求时走 ``items``；单查时仍填充 ``exists``/``lottery_id`` 等单条字段。
    """

    exists: bool = Field(default=False, description="lottery 是否存在（单查）")
    lottery_id: int | None = Field(default=None, description="校验的 lottery_id（回显，单查）")
    title: str | None = Field(default=None, description="抽奖标题（Lotdata.first_prize_cmt）")
    cover: str | None = Field(default=None, description="封面图链接（Lotdata.first_prize_pic，无则空）")
    jumpUrl: str | None = Field(default=None, description="跳转链接（Lotdata.lottery_detail_url，缺省降级为空）")
    items: list[LotteryDetailItem] = Field(default_factory=list, description="批量查询结果（lottery_ids 时返回）")


__all__ = [
    "BaseLotteryRpcParams",
    "GetReserveLotteryRpcParams",
    "GetOfficialLotteryRpcParams",
    "GetChargeLotteryRpcParams",
    "GetTopicLotteryRpcParams",
    "GetAllLotteryRpcParams",
    "GetOthersLotDynListRpcParams",
    "CheckLotteryExistRpcParams",
    "CheckLotteryExistRpcResult",
    "LotteryDetailItem",
    "RPC_METHOD_PARAMS_MODEL_MAP",
    "RPC_METHOD_PARAMS_FIELD_MAP",
]
