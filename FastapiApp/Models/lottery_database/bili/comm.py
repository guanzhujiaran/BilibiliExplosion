from enum import Enum

from pydantic import Field

from Models.common import RequestPaginationParams


class LotteryBusinessType(Enum):
    Official = 1
    Reserve = 10
    Charge = 12

class BiliLotDataStatusEnum(Enum):
    CANCELED = -1
    DELETED = -2
    UNFINISHED = 0
    FINISHED = 2
    UNKNOWN = 404


class LotteryPaginationParams(RequestPaginationParams):
    """抽奖分页参数，继承自通用页码分页参数"""

    # 不设置最大值限制，符合项目规范
    page_size: int = Field(
        default=10, ge=0, le=100, description="每页数量，最小值为 0,最大为 100"
    )


class LotteryWithLimitTimePaginationParams(LotteryPaginationParams):
    """带 limit_time 参数的抽奖分页参数"""

    limit_time: int = Field(default=0, ge=0, le=2**128, description="时间限制（秒）")


class LotterySearchPaginationParams(LotteryPaginationParams):
    """抽奖搜索分页参数，包含 keyword"""

    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
