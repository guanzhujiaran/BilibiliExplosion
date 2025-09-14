from enum import Enum
from typing import TypeVar

from pydantic import Field

from Models.base.custom_pydantic import CustomBaseModel, CustomBaseModelHashable

ParamsType = TypeVar("ParamsType", bound=CustomBaseModelHashable)


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
