# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import Optional, AsyncGenerator, Any

import aiofiles
from apscheduler.triggers.cron import CronTrigger
from loguru import logger as default_logger  # 统一别名为 default_logger

from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import ParamsType, WorkerStatus
from fastapi接口.utils.Common import GLOBAL_SCHEDULER
from utl.pushme.pushme import async_pushme_try_catch_decorator


class CrawlerExecutionInfo:
    def __init__(
            self,
            crawler_name: str,
            default_interval_seconds: int = 2 * 3600,
            logger=default_logger
    ):
        self.crawler_name = crawler_name
        self.default_interval_seconds = default_interval_seconds
        self.logger = logger
        self.last_exec_time: Optional[datetime] = None
        self._load_last_exec_time()

    def _get_last_exec_file_path(self) -> str:
        cur_file_dir = os.path.dirname(__file__)
        RUNTIME_DIR = os.path.join(cur_file_dir, "runtime_data")
        filename = f'{self.crawler_name}_last_exec_time.txt'
        if not os.path.exists(RUNTIME_DIR):
            os.makedirs(RUNTIME_DIR)
        return os.path.join(RUNTIME_DIR, filename)

    def _load_last_exec_time(self):
        file_path = self._get_last_exec_file_path()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    ts_str = f.read().strip()
                    self.last_exec_time = datetime.fromtimestamp(int(ts_str))
                    self.logger.info(f"[{self.crawler_name}] 上次执行时间为：{self.last_exec_time}")
        except Exception as e:
            self.logger.exception(f"[{self.crawler_name}] 加载上次执行时间失败，使用默认值。")
            self.last_exec_time = datetime.fromtimestamp(86400)  # 默认时间点：1970-01-02 00:00:00

    async def save_last_exec_time(self):
        now = datetime.now()
        self.last_exec_time = now
        file_path = self._get_last_exec_file_path()
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(str(int(now.timestamp())))
        except Exception as e:
            self.logger.exception(f"[{self.crawler_name}] 写入上次执行时间失败：{e}")

    def is_need_to_execute(self) -> bool:
        """判断是否需要执行爬虫"""
        if self.last_exec_time is None:
            self.logger.critical(f"[{self.crawler_name}] 上次执行时间为空，将执行一次。")
            return True
        now = datetime.now()
        delta = (now - self.last_exec_time).total_seconds()
        if delta >= self.default_interval_seconds:
            self.logger.critical(f"[{self.crawler_name}] 满足执行条件，delta={delta}s")
            return True
        else:
            self.logger.critical(f"[{self.crawler_name}] 不满足执行条件，delta={delta}s")
            return False


class GenericCrawlerScheduler:
    def __init__(
            self,
            crawler: UnlimitedCrawler,
            cron_expr: str,
            default_interval_seconds: int = 2 * 3600,
            crawler_name: Optional[str] = None
    ):
        self.crawler = crawler
        self.crawler_name = crawler_name if crawler_name else crawler.__class__.__name__
        self.cron_expr = cron_expr
        self.default_interval_seconds = default_interval_seconds
        self.job_id = f"crawler_job_{self.crawler_name}"
        self.logger = self.crawler.log

        # 初始化执行信息管理器
        self.exec_info = CrawlerExecutionInfo(
            crawler_name=self.crawler_name,
            default_interval_seconds=default_interval_seconds,
            logger=self.logger
        )

        # 构建cron trigger
        minute, hour, day, month, day_of_week = cron_expr.split()
        self.trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
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
                max_instances=1,  # 同时只运行一个实例
                misfire_grace_time=3600  # 允许延迟最多 3600 秒
            )
            self.logger.info(f"[{self.crawler_name}] 已添加新任务，首次运行时间已设为现在，将立即尝试执行")

    @async_pushme_try_catch_decorator
    async def run(self):
        self.logger.info(f"[{self.crawler_name}] 定时任务被触发，正在检查是否需要执行...")

        if self.exec_info.is_need_to_execute():
            try:
                self.logger.info(f"[{self.crawler_name}] 开始执行爬虫任务...")
                await self.crawler.main()  # 调用异步 main 函数
                await self.exec_info.save_last_exec_time()
            except Exception as e:
                self.logger.exception(f"[{self.crawler_name}] 爬虫执行出错：{e}")
        else:
            self.logger.info(f"[{self.crawler_name}] 当前不满足执行条件，跳过本次任务。")

    def start(self):
        if not GLOBAL_SCHEDULER.running:
            self.logger.critical("调度器未运行，请确保已启动 GLOBAL_SCHEDULER。")
        GLOBAL_SCHEDULER.resume_job(self.job_id)

    def pause(self):
        GLOBAL_SCHEDULER.pause_job(self.job_id)

    def remove(self):
        GLOBAL_SCHEDULER.remove_job(self.job_id)


if __name__ == '__main__':
    import asyncio


    class MockCrawler(UnlimitedCrawler):
        """模拟的爬虫类，仅用于测试"""

        async def handle_fetch(self, params: ParamsType) -> WorkerStatus | Any:
            pass

        async def key_params_gen(self, params: ParamsType) -> AsyncGenerator[ParamsType, None]:
            pass

        async def is_stop(self) -> bool:
            pass

        async def main(self):
            self.log.info("[MockCrawler] 开始执行 main 方法...")
            self.log.info("[MockCrawler] main 方法执行完成")


    async def _test_scheduler():
        # 启动全局调度器（如果尚未启动）
        if not GLOBAL_SCHEDULER.running:
            GLOBAL_SCHEDULER.start()
        # 创建爬虫和调度器
        crawler = MockCrawler()
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
