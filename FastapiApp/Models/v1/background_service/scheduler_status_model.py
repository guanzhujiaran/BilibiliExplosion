import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, computed_field, Field


class SchedulerInfoModel(BaseModel):
    """调度器基本信息"""
    running: bool = False
    timezone: str = ""
    executor_count: int = 0
    job_count: int = 0


class JobInfoModel(BaseModel):
    """单个任务信息"""
    id: str
    name: str
    func_ref: str
    trigger: str
    next_run_time: Optional[float] = None
    pending_jobs_count: int = 0
    
    @computed_field
    def next_run_time_formatted(self) -> str:
        if self.next_run_time:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.next_run_time))
        return "N/A"


class ExecutionInfoModel(BaseModel):
    """任务执行信息"""
    crawler_name: str
    default_interval_seconds: int
    last_exec_time: Optional[float] = None
    
    @computed_field
    def last_exec_time_formatted(self) -> str:
        if self.last_exec_time:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_exec_time))
        return "N/A"


class SchedulerJobDetailModel(BaseModel):
    """调度器中任务的详细信息"""
    job_info: JobInfoModel
    execution_info: Optional[ExecutionInfoModel] = None


class GlobalSchedulerStatusModel(BaseModel):
    """全局调度器完整状态"""
    scheduler_info: SchedulerInfoModel
    jobs: List[SchedulerJobDetailModel] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    
    @computed_field
    def timestamp_formatted(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))