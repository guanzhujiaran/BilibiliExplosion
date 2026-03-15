from abc import ABC
from typing import Optional, Generic, Any
from Service.BaseCrawler.base.core import BaseCrawler
from Service.BaseCrawler.model.base import WorkerModel, ParamsType
from loguru._logger import Logger
from log.base_log import myfastapi_logger


class CrawlerPlugin(ABC, Generic[ParamsType]):
    """
    爬虫插件的基类。
    插件可以在爬虫的各个生命周期事件中注入自定义逻辑。
    """

    # 提供默认 logger，避免 on_plugin_register 调用前访问未初始化属性
    log: Logger = myfastapi_logger

    def __init__(self, crawler: BaseCrawler[ParamsType]):
        self.crawler = crawler  # 插件可以访问到宿主爬虫实例

    async def on_run_start(self, init_worker_model: WorkerModel):
        """
        在爬虫的 run 方法开始执行时触发。
        """
        pass

    async def on_worker_start(self, worker_model: WorkerModel) -> Any:
        """
        在 worker 开始 handle_fetch 之前触发。
        可以用于修改 fetch_params。
        返回修改后的 fetch_params。
        """
        return None

    async def on_worker_end(self, worker_model: WorkerModel) -> Any:
        """
        在 worker 完成 handle_fetch 之后，on_worker_end 之前触发。
        可以用于处理 fetch_result。
        返回修改后的 fetch_result。
        """
        return None

    async def should_stop_check(self) -> bool:
        """
        在每次生成新的 key_param 之前，检查是否应该停止。
        如果任何一个插件返回 True，或 UnlimitedCrawler 自身的 is_stop 返回 True，则爬虫停止。
        """
        return False

    async def on_run_end(self, end_param: WorkerModel):
        """
        在爬虫的 run 方法完全结束时（包括等待所有任务完成）触发。
        """
        pass

    def on_plugin_register(self):
        """
        当插件被注册到爬虫实例时触发。
        """
        # 🔴 修复：crawler 可能为 None，注册前必须校验
        if self.crawler is None:
            raise RuntimeError(
                f"Plugin {self.__class__.__name__} must be bound to a crawler before registration."
            )
        self.log = self.crawler.log
        # self.log.debug(f"Plugin {self.__class__.__name__} registered.")
