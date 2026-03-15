from enum import Enum
from typing import TypeVar, Generic
from datetime import datetime
from pydantic import Field
from Models.base.custom_pydantic import CustomGenericModel, CustomBaseModelHashable

ParamsType = TypeVar("ParamsType", bound=CustomBaseModelHashable)


class WorkerStatus(Enum):
    # region 成功的代码
    complete = 1
    nullData = 2
    # endregion

    pending = 3
    fail = 4
    timeoutError=5

class WorkerModel(CustomGenericModel, Generic[ParamsType]):
    params: ParamsType | None = None
    seqId: int = Field(..., description="任务序号（自增）从0开始")
    fetchStatus: WorkerStatus = Field(WorkerStatus.pending)
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    retry_count: int = Field(0, description="重试次数")

    @property
    def fetchStatusStr(self) -> str:
        """将 WorkerStatus 枚举转换为字符串"""
        for i in WorkerStatus:
            if i.value == self.fetchStatus:
                return str(i)
        return "unknown"

    def __hash__(self) -> int:
        return hash((self.seqId or 0, str(self.params)))

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != "updated_at" and name in self.__class__.model_fields:
            super().__setattr__("updated_at", datetime.now())
