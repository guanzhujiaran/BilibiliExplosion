import datetime
import inspect
import time
from typing import Any, Optional

import numpy as np

from fastapi接口.service.BaseCrawler.base.core import ParamsType, BaseCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerModel, WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.base import CrawlerPlugin
from fastapi接口.utils.Tool import ts_2_DateTime


class StatsPlugin(CrawlerPlugin[ParamsType]):
    """
    一个用于收集和提供爬虫运行统计信息的插件。
    """

    def __init__(self, crawler: Optional[BaseCrawler[ParamsType]] = None):
        super().__init__(crawler)
        self._init_params: Optional[ParamsType] = None
        self._end_params: Optional[ParamsType] = None
        self._end_success_params: Optional[ParamsType] = None
        self._is_running: bool = False
        self._start_time: float = time.time()  # Stores the monotonic start time
        self._last_update_time: float = 0.0  # Stores the wall clock time of last worker finish
        self._processed_items_count: int = 0  # Fundamental counter
        self._null_count: int = 0
        self._succ_count: int = 0

    async def on_run_start(self, init_params: ParamsType):
        """
        在爬虫的 run 方法开始执行时触发，记录初始参数并重置统计数据。
        """
        self.log.info(f"StatsPlugin: Crawler run started. Init params: {init_params}")
        self._init_params = init_params
        self._is_running = True
        self._start_time = time.time()
        self._last_update_time = time.time()  # Initial update time
        self._processed_items_count = 0
        self._null_count = 0
        self._succ_count = 0
        await super().on_run_start(init_params)

    async def on_worker_end(self, worker_model: WorkerModel):
        """
        在单条任务（worker）完成处理后触发，更新已处理项数量和最后更新时间。
        速度的计算现在放在 property 中。
        """
        self._processed_items_count += 1
        self._last_update_time = time.time()  # Update wall clock time
        if worker_model.fetchStatus in (WorkerStatus.complete, WorkerStatus.nullData):
            self._succ_count += 1
            if worker_model.fetchStatus == WorkerStatus.complete:
                self._end_success_params = worker_model.params
            if worker_model.fetchStatus == WorkerStatus.nullData:
                self._null_count += 1
        self._end_params = worker_model.params
        # Log current speed by calling the property, which calculates it on demand
        self.log.debug(
            f"StatsPlugin: params:{worker_model.params} Worker finished. Total processed: {self._processed_items_count}, "
            f"Current Speed: {self.crawling_speed:.2f} items/s")
        await super().on_worker_end(worker_model)

    async def on_run_end(self, end_param: ParamsType):
        """
        在爬虫的 run 方法完全结束时触发，记录最终参数。
        总时长和速度的计算现在放在 property 中。
        """
        self.log.info(f"StatsPlugin: Crawler run ended. End params: {end_param}")
        self._end_params = end_param
        self._is_running = False
        # No need to calculate _total_run_duration or _current_speed here,
        # the properties will return the final values when accessed.

        self.log.info(f"StatsPlugin Summary:")
        self.log.info(f"  Initial Params: {self._init_params}")
        self.log.info(f"  Final Params: {self._end_params}")
        self.log.info(f"  Is Running: {self._is_running}")
        self.log.info(f"  Processed Items: {self._processed_items_count}")
        # Call properties to get the final calculated values
        self.log.info(f"  Total Duration: {self.total_run_duration:.2f} seconds")
        self.log.info(f"  Average Speed: {self.crawling_speed:.2f} items/second")
        self.log.info(
            f"  Last Update Time: {time.ctime(self.last_update_time)}")  # Convert timestamp to readable string
        self.log.info(f"  Success Count: {self.succ_count}")
        await super().on_run_end(end_param)

    # --- Public properties to access statistics ---

    @property
    def init_params(self) -> Optional[ParamsType]:
        """最开始的参数"""
        return self._init_params

    @property
    def end_params(self) -> Optional[ParamsType]:
        """最后的参数"""
        return self._end_params

    @property
    def end_success_params(self):
        return self._end_success_params

    @property
    def is_running(self) -> bool:
        """爬虫是否正在运行"""
        return self._is_running

    @property
    def last_update_time(self) -> float:
        """最后一次任务完成的时间戳 (Unix timestamp)"""
        return self._last_update_time

    @property
    def last_update_time_str(self) -> datetime.datetime:
        return ts_2_DateTime(self.last_update_time)

    @property
    def processed_items_count(self) -> int:
        """已处理的任务数量"""
        return self._processed_items_count

    @property
    def start_time(self) -> float:
        """爬虫的启动时间 (Unix timestamp)"""
        return self._start_time

    @property
    def start_time_str(self) -> datetime.datetime:
        return ts_2_DateTime(self.start_time)

    @property
    def total_run_duration(self) -> float:
        """
        总运行时长 (秒)。
        无论爬虫是否仍在运行，此属性都将返回从启动到当前时间点或结束的总时长。
        """
        if self.start_time == 0.0:
            return 0.0
        return self.last_update_time - self.start_time

    @property
    def crawling_speed(self) -> float:
        """
        当前的爬取速度 (项/秒)。
        此属性在每次访问时根据当前已处理项数量和总运行时长重新计算。
        """
        current_duration = self.total_run_duration  # Use the calculated property
        if current_duration > 0:
            return self._processed_items_count / current_duration
        return 0.0

    @property
    def null_count(self) -> int:
        """返回 null 数据的数量"""
        return self._null_count

    @property
    def succ_count(self) -> int:
        """成功处理的任务数量"""
        return self._succ_count

    def get_all_status(self) -> dict:
        """
            使用反射自动收集所有 @property 属性的当前值。
        """
        result = {}

        # 获取当前实例的类类型
        cls = type(self)

        # 遍历类的所有成员，找出是 property 的属性
        for name, prop in inspect.getmembers(cls, predicate=lambda x: isinstance(x, property)):
            try:
                # 通过 getattr 动态获取属性值
                value = getattr(self, name)
                result[name] = value
            except Exception as e:
                result[name] = f"<Error: {str(e)}>"

        return result


class SequentialNullStopPlugin(CrawlerPlugin[ParamsType]):
    """
    一个用于在连续多个任务（按原始生成顺序）返回 null 结果时触发停止的插件。
    """

    def __init__(self,
                 crawler: Optional["BaseCrawler[ParamsType]"] = None,
                 max_consecutive_nulls: int = 5):
        super().__init__(crawler)
        self._max_consecutive_nulls: int = max_consecutive_nulls
        # --- 核心状态变量 ---
        # 向量化存储所有任务的状态。使用 WorkerStatus Enum。
        self._status_vector = np.array([])
        self._sequential_null_count: int = 0

    async def on_run_start(self, init_params: ParamsType):
        """
               在爬虫运行开始时重置所有状态变量。
               """
        self.log.info(f"插件启动，连续 {self._max_consecutive_nulls} 个 null 将触发停止。")
        self._status_vector = np.array([])
        self._sequential_null_count = 0
        await super().on_run_start(init_params)

    async def on_worker_end(self, worker_model: WorkerModel) -> Any:
        task_id = worker_model.seqId
        status = worker_model.fetchStatus

        # 如果任务ID超出了当前向量的范围，就用 pending 状态扩展它
        current_len = len(self._status_vector)
        if task_id >= current_len:
            needed_extension = task_id - current_len + 1
            self._status_vector = np.append(self._status_vector, [WorkerStatus.pending] * needed_extension)
        # 直接在相应位置记录状态
        self._status_vector[task_id] = status

        return await super().on_worker_end(worker_model)

    def _calculate_max_streak(self) -> int:
        """
        使用差分法高效计算 _status_vector 中最长的连续 null 区块的长度。
        """
        # 如果向量为空，则不可能有 streak
        if self._status_vector.size == 0:
            return 0

        # 1. 将 Python list 临时转换为 NumPy 数组进行计算
        #    并提取枚举的整数值
        all_values = np.array([s.value for s in self._status_vector], dtype=np.int8)

        # 2. 直接创建 0/1 的整数数组
        binary_arr = np.where(all_values == WorkerStatus.nullData.value, 1, 0)

        # 3. 在数组两端用整数 0 进行填充
        padded_arr = np.concatenate(([0], binary_arr, [0]))

        # 4. 直接在整数数组上计算差分
        diffs = np.diff(padded_arr)

        # 5. 找到所有开始的索引
        starts = np.where(diffs == 1)[0]
        if starts.size == 0:
            return 0  # 如果从未出现过 null，返回 0

        ends = np.where(diffs == -1)[0]

        # 6. 计算所有连续区块的长度并返回最大值
        return int(np.max(ends - starts))

    async def should_stop_check(self) -> bool:
        """
       高效地检查是否应停止爬虫。
       1. 计算全局最长的 null 序列。
       2. 将其赋值给 self._sequential_null_count。
       3. 判断是否满足停止条件。
       """
        # 步骤 1: 调用辅助函数，计算当前全局的最大连续 null 计数
        self._sequential_null_count = self._calculate_max_streak()
        # (可选) 日志记录，便于调试
        self.log.debug(f"全局最长连续 null 计数已更新为: {self._sequential_null_count}")

        # 步骤 3: 使用新赋值的变量来判断是否停止
        if self._sequential_null_count >= self._max_consecutive_nulls:
            self.log.warning(f"连续 null 计数已达到最大值 {self._max_consecutive_nulls}，将停止运行。")
            return True

        return False

    async def on_run_end(self, end_param: ParamsType) -> None:
        """
        在爬虫运行完全结束时调用。
        """
        self._sequential_null_count = self._calculate_max_streak()
        self.log.info(
            f"插件结束。最终已处理的连续 null 计数: {self._sequential_null_count}。"
        )
        await super().on_run_end(end_param)

    # --- 公开属性以访问统计信息 ---
    @property
    def sequential_null_count(self) -> int:
        """获取当前基于已处理任务的连续 null 结果数量。"""
        return self._sequential_null_count
