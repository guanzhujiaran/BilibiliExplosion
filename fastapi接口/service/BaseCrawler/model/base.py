from enum import Enum
from typing import TypeVar, Any

from pydantic import Field

from fastapi接口.models.base.custom_pydantic import CustomBaseModel

ParamsType = TypeVar("ParamsType", bound=Any)


class WorkerStatus(Enum):
    # region 成功的代码
    complete = 1
    nullData = 2
    # endregion

    pending = 3
    fail = 4


class WorkerModel(CustomBaseModel):
    params: ParamsType
    seqId: int = Field(..., description="任务序号（自增）从0开始")
    fetchStatus: WorkerStatus = Field(WorkerStatus.pending)
