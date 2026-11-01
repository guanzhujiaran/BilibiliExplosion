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
        default=1,
        ge=1,
        description="页码，从 1 开始，最小值为 1",
        json_schema_extra={
            "filter_display_name": "页码",
            "filter_widget": "number",
            "filter_description": "分页页码，从 1 开始",
            "filter_placeholder": "输入页码",
        },
    )
    page_size: int = Field(
        default=1000,
        ge=1,
        le=3000,
        description="每页数量，默认 1000，最大 3000，最小值为 1",
        json_schema_extra={
            "filter_display_name": "每页条数",
            "filter_widget": "number",
            "filter_description": "每页返回数量",
            "filter_placeholder": "输入每页条数",
        },
    )


class GetReserveLotteryRpcParams(BaseLotteryRpcParams):
    """get_reserve_lottery 方法请求参数 - 获取预约抽奖数据

    ``only_available``：预约是否已取消 / 已失效不体现在 ``lotdata.status`` 上，
    由预约关系表 ``t_up_reserve_relation_info`` 的 ``state / code / etime`` 决定
    （见 crawler ``_reserve_available``）。默认 ``True``，与只读 HTTP 端点
    ``GetReserveLottery`` 的默认行为一致：只返回仍可参与的预约（未取消 / 未失效 /
    未开奖 / 未过期），避免把已取消的抽奖推给 RPA 去参与。
    显式传 ``False`` 才会返回全部 unfinished 预约（排查用）。
    """

    only_available: bool = Field(
        default=True,
        description="仅返回预约仍有效（未取消/未失效/未过期）的记录；仅在 status=unfinished 时生效",
        json_schema_extra={
            "filter_display_name": "仅看有效预约",
            "filter_widget": "switch",
            "filter_description": "过滤掉已取消/已失效的预约抽奖",
            "filter_default": True,
        },
    )


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
        default=1000,
        ge=1,
        le=3000,
        description="每页数量，默认 1000，最大 3000，最小值为 1",
    )
    created_at_preset: TimePresetEnum | None = Field(
        default=None,
        description="收录时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认不筛选",
    )
    created_at_start: int | None = Field(
        default=None,
        ge=0,
        description="收录起始时间（Unix 秒），preset 优先级高于此字段",
    )
    created_at_end: int | None = Field(
        default=None, ge=0, description="收录结束时间（Unix 秒）"
    )
    pub_time_preset: TimePresetEnum | None = Field(
        default=None,
        description="发布时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认不筛选",
    )
    pub_time_start: int | None = Field(
        default=None,
        ge=0,
        description="发布起始时间（Unix 秒），preset 优先级高于此字段",
    )
    pub_time_end: int | None = Field(
        default=None, ge=0, description="发布结束时间（Unix 秒）"
    )


class GetOthersLotDynListRpcParams(SQLModel):
    """get_others_lot_dyn_list 方法请求参数 - 获取第三方抽奖动态列表"""

    page_num: int = Field(default=1, ge=1, description="页码，从 1 开始，最小值为 1")
    page_size: int = Field(
        default=1000, ge=1, le=3000, description="每页数量，最大 3000，最小值为 1"
    )

    sort_by: OthersLotDynSortEnum = Field(
        default=OthersLotDynSortEnum.created_at,
        description="排序字段: pubTime(发布时间)/created_at(收录时间)",
    )
    sort_order: OthersLotDynSortOrderEnum = Field(
        default=OthersLotDynSortOrderEnum.desc, description="排序方向: asc/desc"
    )

    is_lot: bool = Field(default=True, description="是否筛选为抽奖的动态")

    is_grand_prize: bool | None = Field(
        default=None,
        description="大奖筛选: True-只看大奖 / False-排除大奖 / None-不过滤。"
        "大奖判定来自 t_lot_extra_info（lot_type=common）的 is_grand_prize",
        json_schema_extra={
            "filter_display_name": "只看大奖",
            "filter_widget": "switch",
            "filter_description": "只返回 LLM 判定为大奖的抽奖动态",
        },
    )

    created_at_preset: TimePresetEnum | None = Field(
        default=TimePresetEnum.last_30_days,
        description="收录时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认 30d",
    )
    pub_time_preset: TimePresetEnum | None = Field(
        default=TimePresetEnum.last_7_days,
        description="发布时间快捷筛选: 1d/3d/5d/7d/14d/30d/60d/90d/180d/365d，默认 7d。"
        "第三方抽奖以发布时间近似判断开奖状态：发布时间超过 7 天的动态大概率已开奖，默认排除，"
        "需要看更早的数据请显式放宽该参数",
    )

    pub_time_start: int | None = Field(
        default=None, ge=0, description="发布起始时间（Unix 秒）"
    )
    pub_time_end: int | None = Field(
        default=None, ge=0, description="发布结束时间（Unix 秒）"
    )
    created_at_start: int | None = Field(
        default=None, ge=0, description="收录起始时间（Unix 秒）"
    )
    created_at_end: int | None = Field(
        default=None, ge=0, description="收录结束时间（Unix 秒）"
    )


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

    lottery_id: int | None = Field(
        default=None, description="lottery 主键（Lotdata.lottery_id），单查用"
    )
    lottery_ids: list[int] = Field(
        default_factory=list,
        description="lottery_id 批量列表（批量查，优先于 lottery_id）",
    )


class LotteryDetailItem(SQLModel):
    """lottery 单个资源详情（批量响应元素）。"""

    lottery_id: int = Field(description="lottery 主键")
    exists: bool = Field(default=False, description="lottery 是否存在")
    title: str | None = Field(
        default=None, description="抽奖标题（Lotdata.first_prize_cmt）"
    )
    cover: str | None = Field(
        default=None, description="封面图链接（Lotdata.first_prize_pic，无则空）"
    )
    jumpUrl: str | None = Field(
        default=None, description="跳转链接（Lotdata.lottery_detail_url，缺省降级为空）"
    )


class CheckLotteryExistRpcResult(SQLModel):
    """check_lottery_exist 方法响应数据。

    除存在性外，顺带返回 lottery 基础详情（title/cover/jumpUrl），
    供 be-message 读取动态时对 RESOURCE=lottery 节点实时填充 attach 卡片信息
    （不依赖数据库快照，2.20.1 起）。
    批量请求时走 ``items``；单查时仍填充 ``exists``/``lottery_id`` 等单条字段。
    """

    exists: bool = Field(default=False, description="lottery 是否存在（单查）")
    lottery_id: int | None = Field(
        default=None, description="校验的 lottery_id（回显，单查）"
    )
    title: str | None = Field(
        default=None, description="抽奖标题（Lotdata.first_prize_cmt）"
    )
    cover: str | None = Field(
        default=None, description="封面图链接（Lotdata.first_prize_pic，无则空）"
    )
    jumpUrl: str | None = Field(
        default=None, description="跳转链接（Lotdata.lottery_detail_url，缺省降级为空）"
    )
    items: list[LotteryDetailItem] = Field(
        default_factory=list, description="批量查询结果（lottery_ids 时返回）"
    )


class CheckOthersLotDynExistRpcParams(SQLModel):
    """check_others_lot_dyn_exist 方法请求参数（2.61.0）。

    `dyn_ids` 优先（批量查询）；为空时回退到单个 `dyn_id`。
    """

    dyn_id: int | None = Field(
        default=None, description="第三方抽奖动态 dynId（t_lotdyninfo.dynId），单查用"
    )
    dyn_ids: list[int] = Field(
        default_factory=list, description="dynId 批量列表（批量查，优先于 dyn_id）"
    )


class OthersLotDynDetailItem(SQLModel):
    """第三方抽奖动态单个资源详情（批量响应元素）。"""

    dyn_id: int = Field(description="第三方抽奖动态 dynId")
    exists: bool = Field(default=False, description="该 dynId 是否存在于 t_lotdyninfo")
    title: str | None = Field(
        default=None,
        description="卡片标题（作者名 + 「的抽奖动态」，无作者名时为 null）",
    )
    cover: str | None = Field(
        default=None, description="封面图链接（第三方动态无封面，恒 null）"
    )
    jumpUrl: str | None = Field(
        default=None, description="跳转链接（t_lotdyninfo.dynamicUrl，缺省为 null）"
    )
    authorMid: int | None = Field(
        default=None, description="动态作者 mid（t_lotdyninfo.up_uid）"
    )
    authorName: str | None = Field(
        default=None, description="动态作者昵称（t_lotdyninfo.authorName）"
    )


class CheckOthersLotDynExistRpcResult(SQLModel):
    """check_others_lot_dyn_exist 方法响应数据（2.61.0）。

    批量请求走 ``items``；单查仍填充 ``exists`` / ``dyn_id`` 等单条字段。
    """

    exists: bool = Field(default=False, description="dynId 是否存在（单查）")
    dyn_id: int | None = Field(default=None, description="校验的 dynId（回显，单查）")
    title: str | None = Field(default=None, description="卡片标题")
    cover: str | None = Field(default=None, description="封面图链接")
    jumpUrl: str | None = Field(default=None, description="跳转链接")
    authorMid: int | None = Field(default=None, description="动态作者 mid")
    authorName: str | None = Field(default=None, description="动态作者昵称")
    items: list[OthersLotDynDetailItem] = Field(
        default_factory=list, description="批量查询结果（dyn_ids 时返回）"
    )


# ============ 抽奖卡片批量详情（2.67.0）============
# 热门抽奖榜由 be-message 聚合「热度 id」，卡片内容经 crawler 只读查询服务的
# `GetLotteryDetailList` 一次批量回捞（HTTP）；响应形态与 GetLotteryDetail 的 data
# 完全一致（raw + extra_info），前端可直接 normalizeLotteryData 渲染。
# 这些模型只用于**解析该 HTTP 响应的 data**（不承载 RPC 语义）。


class LotteryCardRaw(SQLModel):
    """抽奖卡片原始字段（与 crawler ``LotdataResp`` 同名字段对齐）。

    仅下发前端 ``normalizeLotteryData`` 渲染卡片所需字段，避免整表字段跨服务搬运；
    时间统一为 Unix 秒，ID 另带 ``*_str`` 字符串副本（前端 JS 无法安全表示大整数）。
    """

    lottery_id: int = Field(description="lottery 主键（对外互动资源 bizId）")
    business_id: int | None = Field(default=None, description="业务 id（动态 id / 预约 sid）")
    business_id_str: str = Field(default="", description="business_id 的字符串副本")
    business_type: int | None = Field(
        default=None, description="抽奖业务类型（1=动态转发 / 10=预约 / 12=充电）"
    )
    status: int | None = Field(
        default=None, description="抽奖状态（-1=取消 / 0=未开奖 / 1、2=已开奖）"
    )
    lottery_time: int | None = Field(default=None, description="开奖时间（Unix 秒）")
    created_at: str | None = Field(
        default=None,
        description="收录时间（ISO 字符串，与 crawler lotdata 响应的 created_at 原样一致）",
    )
    participants: int | None = Field(default=None, description="参与人数")
    sender_uid: int | None = Field(default=None, description="发起人 UID")
    sender_uid_str: str = Field(default="", description="sender_uid 的字符串副本")
    first_prize: int | None = Field(default=None, description="一等奖数量")
    first_prize_cmt: str | None = Field(default=None, description="一等奖文案（卡片标题）")
    first_prize_pic: str | None = Field(default=None, description="一等奖图片")
    second_prize: int | None = Field(default=None, description="二等奖数量")
    second_prize_cmt: str | None = Field(default=None, description="二等奖文案")
    second_prize_pic: str | None = Field(default=None, description="二等奖图片")
    third_prize: int | None = Field(default=None, description="三等奖数量")
    third_prize_cmt: str | None = Field(default=None, description="三等奖文案")
    third_prize_pic: str | None = Field(default=None, description="三等奖图片")
    need_post: int | None = Field(default=None, description="是否需要发帖")
    vip_batch_sign: str | None = Field(default=None, description="大会员批次标记")
    exclusive_level: str | None = Field(
        default=None, description="充电专属等级 JSON（前端解析充电要求）"
    )
    lottery_result: str | None = Field(default=None, description="开奖结果")
    lottery_detail_url: str | None = Field(default=None, description="抽奖详情链接")


class LotteryCardExtraInfo(SQLModel):
    """抽奖卡片附加信息（与 crawler ``OfficialLotExtraInfoResp`` 同口径）。

    ``is_lot`` / ``need_comment`` / ``need_repost`` 由 ``lottery_type`` 派生
    （仅 ``is_grand_prize`` 落库），口径与 crawler 侧 computed_field 完全一致。
    """

    lottery_type: int | None = Field(
        default=None, description="抽奖类型（= business_type，前端卡片展示用）"
    )
    is_grand_prize: bool | None = Field(
        default=None, description="是否大奖（None=未判断）"
    )
    is_lot: bool | None = Field(default=None, description="是否为抽奖（恒 True）")
    need_comment: bool | None = Field(
        default=None, description="是否要求评论（官方抽奖恒 False）"
    )
    need_repost: bool | None = Field(
        default=None, description="是否要求转发（仅 business_type=1 为 True）"
    )


class LotteryCard(SQLModel):
    """单个抽奖卡片（形态与 ``GetLotteryDetail`` 的 data 完全一致）。"""

    raw: LotteryCardRaw = Field(description="抽奖原始字段")
    extra_info: LotteryCardExtraInfo | None = Field(
        default=None, description="附加信息（无记录时为 None）"
    )


class LotteryCardList(SQLModel):
    """crawler ``GetLotteryDetailList`` 的响应 data。"""

    items: list[LotteryCard] = Field(
        default_factory=list, description="卡片列表（与请求顺序一致，未命中的不放入）"
    )
    missing_ids: list[int] = Field(
        default_factory=list, description="lotdata 中不存在的 lottery_id"
    )


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
    "CheckOthersLotDynExistRpcParams",
    "CheckOthersLotDynExistRpcResult",
    "OthersLotDynDetailItem",
    "LotteryCard",
    "LotteryCardList",
    "LotteryCardRaw",
    "LotteryCardExtraInfo",
    "RPC_METHOD_PARAMS_MODEL_MAP",
    "RPC_METHOD_PARAMS_FIELD_MAP",
]
