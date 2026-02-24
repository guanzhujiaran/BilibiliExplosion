from enum import Enum
from typing import TypeVar
import time
from datetime import datetime
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
    created_at: datetime = Field(
        default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="更新时间")

    def __hash__(self) -> int:
        return hash((self.seqId or 0) + int(time.time()))

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != 'updated_at' and name in self.__class__.model_fields:
            super().__setattr__('updated_at', datetime.now())


