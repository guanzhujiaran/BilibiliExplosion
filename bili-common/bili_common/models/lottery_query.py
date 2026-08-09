"""
抽奖通用查询模型与枚举（公共库）

集中定义抽奖业务相关的共享枚举、分页参数与高级查询参数模型，
供 be-bilibili-crawler（HTTP 路由 + RPC 服务端）与 RPA-Browser（RPC 客户端）
统一复用，避免两端重复定义导致字段/取值不一致。

- 枚举：LotteryDataSortEnum / SortOrderEnum / OthersLotDynSortEnum /
  OthersLotDynSortOrderEnum / TimePresetEnum / LotteryStatusEnum
- 分页：LotteryPaginationParams / LotterySearchPaginationParams
- 查询：LotteryAdvancedQueryParams / OthersLotDynListFilterMetadata
"""

from enum import StrEnum


from pydantic import ConfigDict, Field
from sqlmodel import SQLModel

from bili_common.models.pagination import RequestPaginationParams


# ============ 共享枚举 ============


class LotteryDataSortEnum(StrEnum):
    """抽奖数据排序字段枚举（用于预约/官方/充电/话题抽奖）"""

    lottery_time = "lottery_time"  # 开奖时间
    participants = "participants"  # 参与人数
    first_prize = "first_prize"  # 一等奖份数
    created_at = "created_at"  # 收录时间


class SortOrderEnum(StrEnum):
    """通用排序方向枚举"""

    asc = "asc"
    desc = "desc"


class OthersLotDynSortEnum(StrEnum):
    """第三方抽奖动态排序字段枚举"""

    pub_time = "pubTime"
    created_at = "created_at"


class OthersLotDynSortOrderEnum(StrEnum):
    """第三方抽奖动态排序方向枚举"""

    asc = "asc"
    desc = "desc"


class TimePresetEnum(StrEnum):
    """时间快捷筛选枚举（值如 '1d'/'3d' 等，handler 会转为时间戳）"""

    last_1_day = "1d"
    last_3_days = "3d"
    last_5_days = "5d"
    last_7_days = "7d"
    last_14_days = "14d"
    last_30_days = "30d"
    last_60_days = "60d"
    last_90_days = "90d"
    last_180_days = "180d"
    last_365_days = "365d"


class LotteryStatusEnum(StrEnum):
    """抽奖状态枚举（字符串值与 FastapiApp _parse_status 的 key 一致）"""

    unfinished = "unfinished"
    finished = "finished"
    canceled = "canceled"
    deleted = "deleted"
    unknown = "unknown"


# 时间快捷筛选的共享枚举值列表（前端显示中文 label）
_TIME_PRESET_ENUM_VALUES = [
    {"label": "最近1天", "value": "1d"},
    {"label": "最近3天", "value": "3d"},
    {"label": "最近5天", "value": "5d"},
    {"label": "最近7天", "value": "7d"},
    {"label": "最近14天", "value": "14d"},
    {"label": "最近30天", "value": "30d"},
    {"label": "最近60天", "value": "60d"},
    {"label": "最近90天", "value": "90d"},
    {"label": "最近180天", "value": "180d"},
    {"label": "最近365天", "value": "365d"},
]
_TIME_PRESET_JSON_EXTRA = {
    "filter_widget": "select",
    "filter_enum_values": _TIME_PRESET_ENUM_VALUES,
}


# ============ 分页与查询参数 ============


class LotteryPaginationParams(RequestPaginationParams):
    """抽奖分页参数，继承自通用页码分页参数"""

    model_config = ConfigDict(extra="allow")


class LotterySearchPaginationParams(LotteryPaginationParams):
    """抽奖搜索分页参数，包含 keyword"""

    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")


class LotteryAdvancedQueryParams(LotteryPaginationParams):
    """抽奖高级查询参数，包含分页、筛选、排序

    移除了意义不明的 limit_time 参数，改用更直观的 start_ts/end_ts 时间范围筛选，
    新增 sort_by/sort_order 排序控制，与主流查询体验一致。

    字段上的 json_schema_extra 同时作为前端筛选 UI 的元数据来源，
    与 api_GetLotteryFilterParams 响应的 FilterParamMeta 一一对应。
    """

    # 时间范围筛选（开奖时间）
    start_ts: int | None = Field(
        default=None, ge=0, description="开奖时间起始（Unix秒时间戳）",
        json_schema_extra={
            "filter_display_name": "开奖起始时间",
            "filter_widget": "datetime",
            "filter_description": "开奖起始 Unix 时间戳（秒）",
            "filter_placeholder": "选择起始时间",
        },
    )
    end_ts: int | None = Field(
        default=None, ge=0, description="开奖时间结束（Unix秒时间戳）",
        json_schema_extra={
            "filter_display_name": "开奖结束时间",
            "filter_widget": "datetime",
            "filter_description": "开奖结束 Unix 时间戳（秒）",
            "filter_placeholder": "选择结束时间",
        },
    )

    # UP主筛选
    sender_uid: int | None = Field(
        default=None, ge=0, description="UP主UID",
        json_schema_extra={
            "filter_display_name": "UP主UID",
            "filter_widget": "number",
            "filter_description": "按UP主UID筛选",
            "filter_placeholder": "输入UP主UID",
        },
    )

    # 参与人数筛选
    min_participants: int | None = Field(
        default=None, ge=0, description="最小参与人数",
        json_schema_extra={
            "filter_display_name": "最小参与人数",
            "filter_widget": "number",
            "filter_description": "最少参与人数",
            "filter_placeholder": "输入最小参与人数",
        },
    )
    max_participants: int | None = Field(
        default=None, ge=0, description="最大参与人数",
        json_schema_extra={
            "filter_display_name": "最大参与人数",
            "filter_widget": "number",
            "filter_description": "最多参与人数",
            "filter_placeholder": "输入最大参与人数",
        },
    )

    # 状态筛选
    status: str | None = Field(
        default=None, description="抽奖状态: unfinished/finished/canceled",
        json_schema_extra={
            "filter_display_name": "抽奖状态",
            "filter_widget": "select",
            "filter_param_type": "enum",
            "filter_enum_values": [
                {"label": "未开奖", "value": "unfinished"},
                {"label": "已开奖", "value": "finished"},
                {"label": "已取消", "value": "canceled"},
                {"label": "已删除", "value": "deleted"},
            ],
            "filter_description": "按抽奖状态筛选",
            "filter_default": "unfinished",
        },
    )

    # 是否大奖筛选
    is_grand_prize: bool | None = Field(
        default=None, description="是否大奖: True-是, False-否, None-不过滤",
        json_schema_extra={
            "filter_display_name": "是否大奖",
            "filter_widget": "select",
            "filter_param_type": "enum",
            "filter_enum_values": [
                {"label": "是", "value": "true"},
                {"label": "否", "value": "false"},
            ],
            "filter_description": "SVM判断是否为大奖",
        },
    )

    # 关键词
    keyword: str | None = Field(
        default=None, max_length=100, description="关键词搜索",
        json_schema_extra={
            "filter_display_name": "关键词",
            "filter_widget": "input",
            "filter_description": "按关键词搜索",
            "filter_placeholder": "输入关键词",
        },
    )

    # 排序
    sort_by: LotteryDataSortEnum | None = Field(
        default=None, description="排序字段: lottery_time/participants/first_prize/created_at",
        json_schema_extra={
            "filter_display_name": "排序字段",
            "filter_widget": "select",
            "filter_enum_values": [
                {"label": "开奖时间", "value": "lottery_time"},
                {"label": "参与人数", "value": "participants"},
                {"label": "一等奖份数", "value": "first_prize"},
                {"label": "收录时间", "value": "created_at"},
            ],
            "filter_description": "排序字段",
            "filter_default": "lottery_time",
        },
    )
    sort_order: SortOrderEnum | None = Field(
        default=None, description="排序方向: asc/desc",
        json_schema_extra={
            "filter_display_name": "排序方向",
            "filter_widget": "select",
            "filter_enum_values": [
                {"label": "降序", "value": "desc"},
                {"label": "升序", "value": "asc"},
            ],
            "filter_description": "排序方向",
            "filter_default": "asc",
        },
    )

    # 时间快捷筛选
    created_at_preset: TimePresetEnum | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "收录时间快捷",
            "filter_description": "按收录时间快捷筛选，优先级高于单独设置的收录起始/结束时间",
            **_TIME_PRESET_JSON_EXTRA,
        },
    )
    pub_time_preset: TimePresetEnum | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "发布时间快捷",
            "filter_description": "按发布时间快捷筛选，优先级高于单独设置的发布起始/结束时间",
            **_TIME_PRESET_JSON_EXTRA,
        },
    )


class OthersLotDynListFilterMetadata(LotteryPaginationParams):
    """第三方抽奖动态列表筛选参数元数据

    仅用于 api_GetLotteryFilterParams 自动生成前端筛选 UI 元数据，
    不作为 api_GetOthersLotDynList 的 FastAPI 依赖注入模型。
    """

    sort_by: OthersLotDynSortEnum = Field(
        default=OthersLotDynSortEnum.created_at,
        json_schema_extra={
            "filter_display_name": "排序字段",
            "filter_widget": "select",
            "filter_enum_values": [
                {"label": "发布时间", "value": "pubTime"},
                {"label": "收录时间", "value": "created_at"},
            ],
            "filter_description": "排序字段",
        },
    )

    sort_order: OthersLotDynSortOrderEnum = Field(
        default=OthersLotDynSortOrderEnum.desc,
        json_schema_extra={
            "filter_display_name": "排序方向",
            "filter_widget": "select",
            "filter_enum_values": [
                {"label": "降序", "value": "desc"},
                {"label": "升序", "value": "asc"},
            ],
            "filter_description": "排序方向",
        },
    )

    is_lot: bool | None = Field(
        default=True,
        json_schema_extra={
            "filter_display_name": "是否抽奖",
            "filter_widget": "select",
            "filter_param_type": "enum",
            "filter_enum_values": [
                {"label": "是", "value": "true"},
                {"label": "否", "value": "false"},
            ],
            "filter_description": "筛选是否为抽奖动态",
            "filter_default": "true",
        },
    )

    created_at_preset: TimePresetEnum | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "收录时间快捷",
            "filter_description": "按收录时间快捷筛选，优先级高于单独设置的收录起始/结束时间",
            **_TIME_PRESET_JSON_EXTRA,
        },
    )

    pub_time_preset: TimePresetEnum | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "发布时间快捷",
            "filter_description": "按发布时间快捷筛选，优先级高于单独设置的发布起始/结束时间",
            **_TIME_PRESET_JSON_EXTRA,
        },
    )

    pub_time_start: int | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "发布起始时间",
            "filter_widget": "datetime",
            "filter_description": "发布起始Unix时间戳",
            "filter_placeholder": "选择发布时间",
        },
    )

    pub_time_end: int | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "发布结束时间",
            "filter_widget": "datetime",
            "filter_description": "发布结束Unix时间戳",
            "filter_placeholder": "选择发布时间",
        },
    )

    created_at_start: int | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "收录起始时间",
            "filter_widget": "datetime",
            "filter_description": "数据库收录起始时间戳",
            "filter_placeholder": "选择收录时间",
        },
    )

    created_at_end: int | None = Field(
        default=None,
        json_schema_extra={
            "filter_display_name": "收录结束时间",
            "filter_widget": "datetime",
            "filter_description": "数据库收录结束时间戳",
            "filter_placeholder": "选择收录时间",
        },
    )


__all__ = [
    "LotteryDataSortEnum",
    "SortOrderEnum",
    "OthersLotDynSortEnum",
    "OthersLotDynSortOrderEnum",
    "TimePresetEnum",
    "LotteryStatusEnum",
    "LotteryPaginationParams",
    "LotterySearchPaginationParams",
    "LotteryAdvancedQueryParams",
    "OthersLotDynListFilterMetadata",
]
