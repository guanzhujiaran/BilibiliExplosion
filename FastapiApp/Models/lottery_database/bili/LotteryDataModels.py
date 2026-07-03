from datetime import datetime, timedelta
from enum import StrEnum, Enum, IntEnum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic import computed_field

from Models.base.custom_pydantic import CustomBaseModel


class LotdataResp(CustomBaseModel):
    @computed_field
    @property
    def business_id_str(self) -> str:
        return str(self.business_id)

    @computed_field
    @property
    def sender_uid_str(self) -> str:
        return str(self.sender_uid)

    lottery_id: int | None
    business_id: int | None
    status: int | None
    lottery_time: int | None
    lottery_at_num: int | None
    lottery_feed_limit: int | None
    first_prize: int | None
    second_prize: int | None
    third_prize: int | None
    lottery_result: str | None
    first_prize_cmt: str | None
    second_prize_cmt: str | None
    third_prize_cmt: str | None
    first_prize_pic: str | None
    second_prize_pic: str | None
    third_prize_pic: str | None
    need_post: int | None
    business_type: int | None
    sender_uid: int | None
    prize_type_first: str | None
    prize_type_second: str | None
    prize_type_third: str | None
    pay_status: int | None
    ts: int | None
    _gt_: int | None
    has_charge_right: str | None
    lottery_detail_url: str | None
    participants: int | None
    participated: str | None
    vip_batch_sign: str | None
    exclusive_level: str | None
    followed: int | None
    reposted: int | None
    custom_extra_key: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class reserveInfo(CustomBaseModel):
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在


class TUpReserveRelationInfoResp(CustomBaseModel):
    @computed_field
    @property
    def upmid_str(self) -> str:
        if self.upmid:
            return str(self.upmid)
        return "0"

    @computed_field
    @property
    def oid_str(self) -> str:
        if self.oid:
            return str(self.oid)
        return "0"

    @computed_field
    @property
    def dynamicId_str(self) -> str:
        if self.dynamicId:
            return str(self.dynamicId)
        return "0"

    ids: int | None  # 主键
    code: int | None
    message: str | None
    ttl: int | None
    sid: int | None
    name: str | None
    total: int | None
    stime: int | None
    etime: int | None
    isFollow: int | None
    state: int | None
    oid: str | None
    type: int | None
    upmid: int | None
    reserveRecordCtime: int | None
    livePlanStartTime: int | None
    upActVisible: int | None
    lotteryType: int | None
    text: str | None
    jumpUrl: str | None
    dynamicId: str | None
    reserveTotalShowLimit: int | None
    desc: str | None
    start_show_time: int | None
    BaseJumpUrl: str | None  # 可能为空，设置为 Optional 并提供默认值
    OidView: int | None  # 可能为空，设置为 Optional 并提供默认值
    hide: str | None  # 可能为空，设置为 Optional 并提供默认值
    ext: str | None  # 可能为空，设置为 Optional 并提供默认值
    subType: str | None  # 可能为空，设置为 Optional 并提供默认值
    productIdPrice: str | Dict | None  # JSON 字段，可能为空
    reserve_products: str | Dict | None  # JSON 字段，可能为空
    raw_JSON: str | Dict | None  # JSON 字段，可能为空
    reserve_round_id: int | None
    new_field: str | Dict | None  # 是否有新的字段，默认为 None

    model_config = ConfigDict(from_attributes=True)


class ReserveInfoResp(reserveInfo):
    app_sche: str
    reserve_url: str  # 空间动态链接 like https://space.bilibili.com/1927279531
    lottery_prize_info: str  # 奖品名称
    etime: int  # 结束时间(秒)
    jump_url: str  # 单独抽奖的跳转链接，like https://www.bilibili.com/h5/lottery/result?business_id=3640758&business_type=10
    reserve_sid: int  # 直播预约sid
    available: bool  # 预约是否正常存在
    raw: TUpReserveRelationInfoResp | None
    dynamic_id: int | None
    total: int | None

    @computed_field
    @property
    def dynamic_id_str(self) -> str | None:
        return str(self.dynamic_id) if self.dynamic_id else None


class OfficialLotType(StrEnum):
    """官方抽奖类型枚举"""
    reserve_lot = '预约抽奖'
    charge_lot = '充电抽奖'
    official_lot = '官方抽奖'
    lot_dyn_origin_dyn = '抽奖动态的源动态'


class CommonLotteryResp(CustomBaseModel):
    @computed_field
    @property
    def up_uid_str(self) -> str:
        return str(self.up_uid)

    dynId: str
    dynamicUrl: str
    authorName: str
    up_uid: int
    pubTime: datetime
    dynContent: str
    commentCount: Optional[int] = 0
    repostCount: Optional[int] = 0
    likeCount: Optional[int] = 0
    officialLotType: OfficialLotType | None
    officialLotId: str = ""
    isOfficialAccount: int
    isManualReply: bool = Field(default=False, description="是否需要人工评论")
    isLot: int
    hashTag: str
    isBigLot: int = Field(default=0, description="SVM 大奖判断结果: 1-大奖, 0-非大奖")

    @field_validator("officialLotType", mode="before")
    @classmethod
    def _empty_str_to_none_official_lot_type(cls, v):
        # 数据库中可能存储了空字符串，需转换为 None 以通过枚举校验
        if v == "" or v is None:
            return None
        return v

    @field_validator("officialLotId", "dynamicUrl", "authorName", "dynContent", "hashTag", mode="before")
    @classmethod
    def _str_none_to_empty(cls, v):
        # 数据库中这些文本字段可能为 None，转为空字符串
        if v is None:
            return ""
        return v

    @field_validator("isManualReply", mode="before")
    @classmethod
    def _to_bool(cls, v):
        # 兼容旧数据：'人工判断'/1/True -> True，''/0/None/False -> False
        if isinstance(v, str):
            return v == '人工判断'
        return bool(v)

    @field_validator("isOfficialAccount", "isLot", "up_uid", mode="before")
    @classmethod
    def _int_none_to_zero(cls, v):
        # 数据库中这些整数字段可能为 None，转为 0
        if v is None:
            return 0
        return v

    @field_validator("pubTime", mode="before")
    @classmethod
    def _pubtime_none_to_epoch(cls, v):
        # 数据库中 pubTime 可能为 None，转为 Unix epoch
        if v is None:
            return datetime.fromtimestamp(0)
        return v


class LotExtraInfoResp(CustomBaseModel):
    """抽奖附加信息 — 对应数据库 t_lot_extra_info 表，方便后续扩展"""
    is_grand_prize: bool = Field(default=False, description="大奖标志: true-大奖, false-非大奖")
    need_comment: bool = Field(default=False, description="是否需要评论")
    need_repost: bool = Field(default=False, description="是否需要转发")


class OfficialLotteryResp(CustomBaseModel):
    @computed_field
    @property
    def lottery_id_str(self) -> str:
        return str(self.lottery_id)

    jump_url: str
    app_sche: str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int
    extra_info: LotExtraInfoResp | None = Field(default=None, description="抽奖附加信息")
    raw: LotdataResp


class ChargeLotteryResp(CustomBaseModel):
    @computed_field
    @property
    def lottery_id_str(self) -> str:
        return str(self.lottery_id)

    jump_url: str
    app_sche: str
    lottery_text: str
    lottery_time: int
    dynId: str
    sender_uid: str
    lottery_id: int
    upower_level_str: str
    extra_info: LotExtraInfoResp | None = Field(default=None, description="抽奖附加信息")
    raw: LotdataResp


class TopicLotteryResp(CustomBaseModel):
    jump_url: str
    app_sche: str
    title: str
    end_date_str: str
    lot_type_text: str
    lottery_pool_text: str
    lottery_sid: Optional[str]


class LiveLotteryResp(CustomBaseModel):
    @computed_field
    @property
    def anchor_uid_str(self) -> str:
        return str(self.anchor_uid)

    @computed_field
    @property
    def room_id_str(self) -> str:
        return str(self.room_id)

    @computed_field
    @property
    def lot_id_str(self) -> str:
        return str(self.lot_id)

    live_room_url: str
    app_schema: str
    award_name: str
    type: str
    end_time: int
    total_price: int
    danmu: str
    anchor_uid: int
    room_id: int
    lot_id: int
    require_type: int


class AllLotteryResp(CustomBaseModel):
    common_lottery: list[CommonLotteryResp] = Field(..., description="一般抽奖（分页后）")
    common_lottery_total: int = Field(
        default=0, description="一般抽奖总数（分页前），用于前端计算总页数"
    )
    must_join_common_lottery: list[CommonLotteryResp] = Field(
        ..., description="必抽的一般抽奖（来自当前页）"
    )
    reserve_lottery: list[ReserveInfoResp] = Field(..., description="必抽的预约抽奖")
    official_lottery: list[OfficialLotteryResp] = Field(
        ..., description="必抽的官方抽奖"
    )


class BaseAddLotteryResp(CustomBaseModel):
    """添加抽奖响应基类"""

    msg: str = Field(..., description="操作消息")
    is_succ: bool = Field(..., description="是否成功")
    is_new: bool = Field(..., description="是否是新的内容")


class AddDynamicLotteryResp(BaseAddLotteryResp):
    """添加动态抽奖响应"""

    dynamic_id_or_url: str = Field(..., description="提交的动态ID或URL")


class AddDynamicLotteryReq(CustomBaseModel):
    dynamic_id_or_url: str


class BulkAddDynamicLotteryReq(CustomBaseModel):
    dynamic_id_or_urls: list[str]


class BiliUserInfoSimple(CustomBaseModel):
    uid: str
    name: str
    face: str


class AddTopicLotteryReq(CustomBaseModel):
    topic_id: int | str


class BulkAddTopicLotteryReq(CustomBaseModel):
    topic_ids: list[int | str]


class BulkAddOthersLotDynReq(CustomBaseModel):
    dynamic_id_or_urls: list[str]


class SubmitFeedbackReq(CustomBaseModel):
    """提交反馈请求模型"""

    message: str = Field(..., description="反馈内容")


class AddTopicLotteryResp(BaseAddLotteryResp):
    """添加话题抽奖响应"""

    topic_id: str | int = Field(..., description="提交的话题 ID")


# region Description：抽奖信息统计模型
class WinnerInfo(CustomBaseModel):
    user: BiliUserInfoSimple
    count: int
    rank: int


class BiliLotStatisticInfoResp(CustomBaseModel):
    sync_ts: int
    winners: list[WinnerInfo]
    total: int


class AtariLotRankEnum(IntEnum):
    first_prize = 1
    second_prize = 2
    third_prize = 3


class BiliLotStatisticLotteryResultResp(CustomBaseModel):
    user: BiliUserInfoSimple
    prize_result: list[dict]
    total: int


class BiliLotteryStatusEnum(IntEnum):
    not_drawn = 0
    end = 2
    canceled = -1


class BiliBusinessTypeEnum(IntEnum):
    official = 1
    reserve = 10
    charge = 12


class BiliLotStatisticLotTypeEnum(StrEnum):
    official = "official"
    reserve = "reserve"
    charge = "charge"
    total = "total"

    @property
    def business_type(self) -> AtariLotRankEnum | None:
        mapping = {
            self.official: BiliBusinessTypeEnum.official,
            self.reserve: BiliBusinessTypeEnum.reserve,
            self.charge: BiliBusinessTypeEnum.charge,
        }
        return mapping.get(self)


class BiliLotStatisticRankTypeEnum(StrEnum):
    first = "first"
    second = "second"
    third = "third"
    total = "total"

    @property
    def rank_enum(self) -> AtariLotRankEnum | None:
        mapping = {
            self.first: AtariLotRankEnum.first_prize,
            self.second: AtariLotRankEnum.second_prize,
            self.third: AtariLotRankEnum.third_prize,
        }
        return mapping.get(self)


class BiliLotStatisticRankDateTypeEnum(StrEnum):
    month = "month"  # 当月
    pre_month = "pre_month"  # 上月
    year = "year"
    pre_year = "pre_year"
    total = "total"  # 总计

    def get_start_end_ts(self) -> tuple[int, int]:
        now = datetime.now()
        if self.value == "total":
            return 0, 0
        elif self.value == "month":
            start_ts = datetime(now.year, now.month, 1)  # 本月1号
            end_ts = now
        elif self.value == "pre_month":
            start_ts = datetime(now.year, now.month - 1, 1)  # 上月1号
            end_ts = datetime(now.year, now.month, 1) - timedelta(
                seconds=1
            )  # 上月最后一天
        elif self.value == "year":
            start_ts = datetime(now.year, 1, 1)  # 本年1号
            end_ts = now
        elif self.value == "pre_year":
            start_ts = datetime(now.year - 1, 1, 1)  # 上年1号
            end_ts = datetime(now.year, 1, 1) - timedelta(seconds=1)  # 上年最后一天
        else:
            raise ValueError(f"Invalid rank date type: {self.value}")
        return int(start_ts.timestamp()), int(end_ts.timestamp())

    def get_start_end_datetime(self) -> tuple[datetime | None, datetime | None]:
        now = datetime.now()
        if self.value == "total":
            return None, None
        elif self.value == "month":
            start_ts = datetime(now.year, now.month, 1)  # 本月1号
            end_ts = now
        elif self.value == "pre_month":
            start_ts = datetime(now.year, now.month - 1, 1)  # 上月1号
            end_ts = datetime(now.year, now.month, 1) - timedelta(
                seconds=1
            )  # 上月最后一天
        elif self.value == "year":
            start_ts = datetime(now.year, 1, 1)  # 本年1号
            end_ts = now
        elif self.value == "pre_year":
            start_ts = datetime(now.year - 1, 1, 1)  # 上年1号
            end_ts = datetime(now.year, 1, 1) - timedelta(seconds=1)  # 上年最后一天
        else:
            raise ValueError(f"Invalid rank date type: {self.value}")
        return start_ts, end_ts


# endregion


# region 第三方抽奖动态列表模型
class OthersLotDynSortEnum(StrEnum):
    """排序字段枚举"""
    pub_time = "pubTime"
    created_at = "created_at"


class OthersLotDynSortOrderEnum(StrEnum):
    """排序方向枚举"""
    asc = "asc"
    desc = "desc"


class LotteryDataSortEnum(StrEnum):
    """抽奖数据排序字段枚举（用于预约/官方/充电抽奖）"""
    lottery_time = "lottery_time"  # 开奖时间
    participants = "participants"  # 参与人数
    first_prize = "first_prize"  # 一等奖份数
    created_at = "created_at"  # 收录时间


class SortOrderEnum(StrEnum):
    """通用排序方向枚举"""
    asc = "asc"
    desc = "desc"


class TimePresetEnum(StrEnum):
    """时间快捷筛选"""
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


class OthersLotPrizeInfo(BaseModel):
    """第三方抽奖动态的提取信息（UIE 提取）"""
    model_config = ConfigDict(extra="forbid")
    prize_names: list[str] = Field(
        default_factory=list, description="提取到的奖品名称列表")
    lottery_time: str | None = Field(
        default=None, description="提取到的开奖时间字符串")


class OthersLotDynItem(CustomBaseModel):
    """第三方抽奖动态条目"""

    @computed_field
    @property
    def dynId_str(self) -> str:
        return str(self.dynId)

    @computed_field
    @property
    def up_uid_str(self) -> str | None:
        return str(self.up_uid) if self.up_uid else None

    dynId: int
    dynamicUrl: str | None
    authorName: str | None
    up_uid: int | None
    pubTime: datetime | None
    dynContent: str | None
    commentCount: int | None
    repostCount: int | None
    likeCount: int | None
    officialLotType: OfficialLotType | None
    isOfficialAccount: int | None
    isManualReply: bool | None = Field(default=None, description="是否需要人工评论")
    isLot: int | None
    hashTag: str | None
    created_at: datetime | None  # 数据库创建时间
    prize_info: OthersLotPrizeInfo | None = Field(
        default=None, description="UIE 提取的奖品信息，首次提取后缓存")
    extra_info: LotExtraInfoResp | None = Field(
        default=None, description="抽奖附加信息")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("officialLotType", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        # 数据库中可能存储了空字符串，需转换为 None 以通过枚举校验
        if v == "" or v is None:
            return None
        return v

    @field_validator("isManualReply", mode="before")
    @classmethod
    def _to_bool(cls, v):
        # 兼容旧数据：'人工判断'/1/True -> True，''/0/None/False -> False
        if v is None:
            return None
        if isinstance(v, str):
            return v == '人工判断'
        return bool(v)


class FilterParamTypeEnum(StrEnum):
    """筛选参数类型枚举"""
    INT = "int"
    STR = "str"
    ENUM = "enum"
    BOOL = "bool"
    DATETIME_RANGE = "datetime_range"


class FilterEnumValue(CustomBaseModel):
    """枚举选项值"""
    label: str = Field(..., description="显示名称")
    value: str = Field(..., description="实际值")


class FilterParamMeta(CustomBaseModel):
    """单个筛选参数元数据"""
    param_name: str = Field(..., description="API 参数名")
    display_name: str = Field(..., description="中文显示名称")
    param_type: str = Field(...,
                            description="后端接收的参数类型: int/str/enum/bool")
    widget: str = Field(default="input",
                        description="前端UI组件类型: input/number/datetime/select/switch")
    enum_values: Optional[list[FilterEnumValue]] = Field(
        default=None, description="枚举选项（仅枚举类型）")
    default_value: Optional[Any] = Field(default=None, description="默认值")
    description: str = Field(default="", description="参数说明")
    required: bool = Field(default=False, description="是否必填")
    placeholder: Optional[str] = Field(default=None, description="输入框占位提示")


class EndpointFilterMeta(CustomBaseModel):
    """端点筛选参数元数据"""
    endpoint_path: str = Field(..., description="API 端点路径")
    display_name: str = Field(..., description="端点中文名称")
    params: list[FilterParamMeta] = Field(
        default_factory=list, description="筛选参数列表")


class LotteryFilterParamsResp(CustomBaseModel):
    """抽奖查询筛选参数响应"""
    endpoints: list[EndpointFilterMeta] = Field(
        default_factory=list, description="各端点筛选参数列表")


# region 筛选参数元数据 — 自动生成工具


class FilterWidgetType(StrEnum):
    """前端控件类型"""
    INPUT = "input"
    NUMBER = "number"
    DATETIME = "datetime"
    SELECT = "select"
    SWITCH = "switch"


def _infer_param_type(annotation: Any) -> str:
    """从 Python 类型注解推断 param_type

    注意：bool 是 int 的子类，StrEnum 是 str 的子类，
    检查顺序必须为 bool → (StrEnum/Enum) → int → str。
    """
    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", ())
    # 解 Optional / Union with None
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            annotation = non_none[0]
    if isinstance(annotation, type):
        if issubclass(annotation, bool):
            return "bool"
        if issubclass(annotation, (StrEnum, Enum)):
            return "enum"
        if issubclass(annotation, int):
            return "int"
        if issubclass(annotation, str):
            return "str"
    return "str"


def _extract_enum_values(annotation: Any) -> list[FilterEnumValue] | None:
    """从 StrEnum 类型提取枚举值列表"""
    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", ())
    # 解 Optional
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            annotation = non_none[0]
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return [FilterEnumValue(label=member.value, value=member.value) for member in annotation]
    return None


def _get_field_default(field_info) -> Any:
    """安全获取 Pydantic 字段默认值"""
    from pydantic.fields import PydanticUndefined
    default = field_info.default
    if default is PydanticUndefined:
        return None
    # 如果是 default_factory，尝试调用
    if field_info.default_factory and field_info.default_factory is not None:
        try:
            return field_info.default_factory()
        except Exception:
            return None
    return default


def pydantic_model_to_filter_params(model_cls: type[CustomBaseModel]) -> list[FilterParamMeta]:
    """将 Pydantic 模型字段自省为 FilterParamMeta 列表

    模型字段上的 json_schema_extra 中包含 filter_* 键的会被提取用于前端元数据。
    不包含 filter_display_name 的字段将自动推导名称与类型。
    """
    params: list[FilterParamMeta] = []
    for field_name, field_info in model_cls.model_fields.items():
        extra = (field_info.json_schema_extra or {}) if field_info.json_schema_extra else {}

        display_name = extra.get("filter_display_name", field_name)
        param_type = extra.get("filter_param_type") or _infer_param_type(field_info.annotation)
        widget = extra.get("filter_widget", "input")
        description = extra.get("filter_description", field_info.description or "")
        placeholder = extra.get("filter_placeholder")
        required = extra.get("filter_required", field_info.is_required())
        default_value = extra.get("filter_default") if "filter_default" in extra else _get_field_default(field_info)

        # 枚举值：优先用 json_schema_extra 中声明的，否则从 StrEnum 注解自动提取
        enum_values = extra.get("filter_enum_values")
        if enum_values is None and param_type == "enum":
            enum_values = _extract_enum_values(field_info.annotation)

        params.append(FilterParamMeta(
            param_name=field_name,
            display_name=display_name,
            param_type=param_type,
            widget=widget,
            enum_values=enum_values,
            default_value=default_value,
            description=description,
            required=required,
            placeholder=placeholder,
        ))
    return params


# endregion


if __name__ == "__main__":
    print(BiliLotStatisticLotTypeEnum.charge.business_type)
