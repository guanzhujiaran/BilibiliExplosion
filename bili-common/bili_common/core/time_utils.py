"""时间工具 - 统一对外输出秒级 int32 时间戳。

约定（全项目）：
- 后端响应体中**所有** date / datetime 一律序列化为 **int32 秒级时间戳**（int），
  不再输出 ISO 字符串 / 时区偏移字符串，由前端自行按本地时区渲染。
- naive（无时区）datetime 按业务时区 `Asia/Shanghai` 解释；
  aware datetime 直接按其真实时区换算。
- 请求方向保持不变：仍接受 ISO 字符串 / 业务既有格式，由后端解析。
"""

from datetime import date, datetime, time, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer

__all__ = [
    "BUSINESS_TZ",
    "to_unix_timestamp",
    "unix_timestamp_serializer",
    "UnixTime",
    "OptionalUnixTime",
]

# 业务统一时区：项目调度器、数据库默认值（1970-01-01 00:00:00+08）均以此为准
BUSINESS_TZ = ZoneInfo("Asia/Shanghai")


def _normalize(value: datetime | date) -> datetime:
    """把 date / datetime 归一为带时区的 datetime。"""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            # naive：按业务时区解释，避免被当成 UTC 造成偏移
            return value.replace(tzinfo=BUSINESS_TZ)
        return value
    # date：当天 00:00:00（业务时区）
    return datetime.combine(value, time.min, tzinfo=BUSINESS_TZ)


def to_unix_timestamp(value: datetime | date | None) -> int | None:
    """把 date / datetime 转成秒级时间戳；`None` 与非法值返回 `None`。

    Args:
        value: 待转换的时间值。

    Returns:
        int | None: 秒级 Unix 时间戳（int32 范围内），无值时返回 None。
    """
    if value is None:
        return None
    try:
        normalized = _normalize(value)
    except (TypeError, ValueError):
        return None
    return int(normalized.timestamp())


def unix_timestamp_serializer(value: datetime | date | None) -> int | None:
    """pydantic 字段序列化器：datetime -> 秒级 int 时间戳。"""
    return to_unix_timestamp(value)


# 响应模型中的时间字段统一使用这两个别名声明
UnixTime = Annotated[
    datetime,
    PlainSerializer(unix_timestamp_serializer, return_type=int, when_used="always"),
]
OptionalUnixTime = Annotated[
    datetime | None,
    PlainSerializer(unix_timestamp_serializer, return_type=int | None, when_used="always"),
]