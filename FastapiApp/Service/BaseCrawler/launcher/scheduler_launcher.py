# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, AsyncGenerator, Any
from apscheduler.triggers.cron import CronTrigger
from loguru import logger as default_logger
from Models.base.custom_pydantic import CustomBaseModelHashable, CustomBaseModel
from Service.BaseCrawler.CrawlerType import UnlimitedCrawler
from Service.BaseCrawler.model.base import ParamsType, WorkerStatus
from Utils.通用.Common import GLOBAL_SCHEDULER
from Utils.推送.PushMe import async_pushme_try_catch_decorator, a_pushme
import asyncio
from typing import Callable
from dao.commStorageRedisObj import comm_storage_redis_obj


class CrawlerExecutionInfoModel(CustomBaseModel):
    crawler_name: str
    default_interval_seconds: int
    last_exec_time: datetime | None = None


class CrawlerExecutionInfo:
    info: CrawlerExecutionInfoModel

    def __init__(
        self,
        crawler_name: str,
        default_interval_seconds: int = 2 * 3600,
        logger=default_logger,
    ):
        self.logger = logger
        self.info = CrawlerExecutionInfoModel(
            crawler_name=crawler_name,
            default_interval_seconds=default_interval_seconds,
        )
        self._exec_info_redis_key = f"{self.info.crawler_name}_last_exec_time.txt"

    async def load_last_exec_time(self):
        if self.info.last_exec_time is None:
            ts_str = await comm_storage_redis_obj.get_val(self._exec_info_redis_key)
            if ts_str:
                self.info.last_exec_time = datetime.fromtimestamp(float(ts_str))
                self.logger.info(
                    f"[{self.info.crawler_name}] 加载上次执行时间：{self.info.last_exec_time}"
                )
            else:
                self.logger.info(
                    f"[{self.info.crawler_name}] 未找到上次执行时间，使用默认值。"
                )
                self.info.last_exec_time = datetime.fromtimestamp(
                    86400
                )  # 默认时间点：1970-01-02 00:00:00

    async def save_last_exec_time(self):
        now = datetime.now()
        self.info.last_exec_time = now
        await comm_storage_redis_obj.set_val(
            self._exec_info_redis_key, str(now.timestamp())
        )

    async def is_need_to_execute(self) -> bool:
        """判断是否需要执行爬虫"""
        await self.load_last_exec_time()
        if self.info.last_exec_time is None:
            self.logger.info(
                f"[{self.info.crawler_name}] 上次执行时间为空，将执行一次。"
            )
            return True
        now = datetime.now()
        delta = (now - self.info.last_exec_time).total_seconds()
        if delta >= self.info.default_interval_seconds:
            self.logger.info(f"[{self.info.crawler_name}] 满足执行条件，delta={delta}s")
            return True
        else:
            self.logger.info(
                f"[{self.info.crawler_name}] 不满足执行条件，delta={delta}s"
            )
            return False


class BaseScheduler:
    """
    定时任务调度器
    """

    def __init__(
        self,
        func: Callable,
        cron_expr: str,
        default_interval_seconds: int = 2 * 3600,
        crawler_name: str = "",
        logger=default_logger,
    ):
        self.func = func
        self.crawler_asyncio_task = None
        self.cron_expr = cron_expr
        self.job_id = f"crawler_job_{crawler_name}"
        self.logger = logger
        # 初始化执行信息管理器
        self.exec_info = CrawlerExecutionInfo(
            crawler_name=crawler_name,
            default_interval_seconds=default_interval_seconds,
            logger=self.logger,
        )

        # 构建cron trigger
        minute, hour, day, month, day_of_week = cron_expr.split()
        self.trigger = CronTrigger(
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
        )
        # 添加或更新任务
        self._add_or_update_job()

    def _add_or_update_job(self):
        job = GLOBAL_SCHEDULER.get_job(self.job_id)
        if job:
            GLOBAL_SCHEDULER.reschedule_job(
                job_id=self.job_id,
                trigger=self.trigger,
            )
        else:
            # 强制首次任务立即执行
            GLOBAL_SCHEDULER.add_job(
                self.run,
                name=self.job_id,
                trigger=self.trigger,
                id=self.job_id,
                next_run_time=datetime.now(),  # 立即执行第一次
                coalesce=True,  # 错过的任务合并为一次
                max_instances=1,  # 同时最多允许一个实例
                misfire_grace_time=24 * 3600,  # 允许延迟最多 1 天
            )
            self.logger.debug(
                f"[{self.exec_info.info.crawler_name}] 已添加新任务，首次运行时间已设为现在，将立即尝试执行"
            )

    @async_pushme_try_catch_decorator
    async def run(self):
        self.logger.debug(
            f"[{self.exec_info.info.crawler_name}] 定时任务被触发，正在检查是否需要执行..."
        )

        if await self.exec_info.is_need_to_execute():
            try:
                self.logger.debug(
                    f"[{self.exec_info.info.crawler_name}] 开始执行爬虫任务..."
                )
                # 调用异步 main 函数
                self.crawler_asyncio_task = asyncio.create_task(
                    self.func()
                )  # 获取异步包装的Task实例
                await self.crawler_asyncio_task  # 等待异步任务完成
                await self.exec_info.save_last_exec_time()
            except asyncio.CancelledError as e:
                self.logger.error(
                    f"[{self.exec_info.info.crawler_name}] 爬虫主动终止：{e}"
                )
            except Exception as e:
                self.logger.exception(
                    f"[{self.exec_info.info.crawler_name}] 爬虫执行出错：{e}"
                )
                await a_pushme(
                    title=f"{self.exec_info.info.crawler_name} 执行异常",
                    content=f"错误详情：{str(e)}",
                )
        else:
            self.logger.info(
                f"[{self.exec_info.info.crawler_name}] 当前不满足执行条件，跳过本次任务。"
            )

    def terminate(self):
        """
        终止当前正在执行的任务
        """
        if self.crawler_asyncio_task:
            self.crawler_asyncio_task.cancel()
            return True
        return False

    def start(self):
        if not GLOBAL_SCHEDULER.running:
            self.logger.critical("调度器未运行，请确保已启动 GLOBAL_SCHEDULER。")
        GLOBAL_SCHEDULER.resume_job(self.job_id)

    def pause(self):
        """
        暂停任务计划，对当前正在执行任务无影响
        """
        GLOBAL_SCHEDULER.pause_job(self.job_id)

    def remove(self):
        """
        移除将来的任务计划，对当前正在执行的任务无影响
        """
        GLOBAL_SCHEDULER.remove_job(self.job_id)

    def add_job(self):
        """
        添加任务到调度器
        """
        job = GLOBAL_SCHEDULER.get_job(self.job_id)
        if job is None:
            GLOBAL_SCHEDULER.add_job(
                self.run,
                name=self.job_id,
                trigger=self.trigger,
                id=self.job_id,
                next_run_time=datetime.now(),
                coalesce=True,
                max_instances=1,
                misfire_grace_time=3600,
            )
            self.logger.info(
                f"[{self.exec_info.info.crawler_name}] 任务已重新添加到调度器"
            )


class GenericCrawlerScheduler(BaseScheduler):
    """
    通用爬虫调度器，用于调度任意爬虫类
    """

    def __init__(
        self,
        crawler: UnlimitedCrawler,
        cron_expr: str,
        default_interval_seconds: int = 2 * 3600,
        crawler_name: Optional[str] = None,
    ):
        self.crawler = crawler
        super().__init__(
            func=self.crawler.main,
            cron_expr=cron_expr,
            default_interval_seconds=default_interval_seconds,
            crawler_name=crawler_name or self.crawler.__class__.__name__,
            logger=self.crawler.log,
        )


if __name__ == "__main__":

    class MockParams(CustomBaseModelHashable):
        a: int

        def __hash__(self):
            return hash(self.a)

    class MockCrawler(UnlimitedCrawler[MockParams]):
        """模拟的爬虫类，仅用于测试"""

        async def handle_fetch(self, params: ParamsType) -> WorkerStatus | Any:
            self.log.info(f"[MockCrawler] 模拟爬虫正在执行 handle_fetch...{params}")
            await asyncio.sleep(1)

        async def key_params_gen(
            self, params: ParamsType
        ) -> AsyncGenerator[MockParams, None]:
            for i in range(10):
                yield MockParams(a=i)

        async def is_stop(self) -> bool: ...

        async def main(self):
            self.log.info("[MockCrawler] 开始执行 main 方法...")
            await self.run()
            self.log.info("[MockCrawler] main 方法执行完成")

    async def _test_scheduler():
        # 启动全局调度器（如果尚未启动）
        if not GLOBAL_SCHEDULER.running:
            GLOBAL_SCHEDULER.start()
        # 创建爬虫和调度器
        crawler = MockCrawler(max_sem=1)
        scheduler = GenericCrawlerScheduler(
            crawler=crawler,
            cron_expr="*/1 * * * *",  # 每分钟执行一次
            default_interval_seconds=60,  # 至少间隔 60 秒才能再次执行
        )

        default_logger.info("调度器已启动，等待任务触发...")

        try:
            # 让主函数持续运行一段时间以便观察定时任务
            await asyncio.sleep(300)  # 5分钟
        except KeyboardInterrupt:
            default_logger.info("收到退出信号，正在关闭调度器...")
        finally:
            scheduler.remove()
            GLOBAL_SCHEDULER.shutdown()

    asyncio.run(_test_scheduler())
