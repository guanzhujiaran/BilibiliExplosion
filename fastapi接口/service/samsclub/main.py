import asyncio
import datetime
import os
import time
from pathlib import Path
from typing import Any

import aiofiles
import pandas as pd

from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.models.v1.background_service.background_service_model import ProgressStatusResp
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus, ParamsType
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from fastapi接口.service.samsclub.Sql.SqlHelper import sql_helper
from fastapi接口.service.samsclub.api.samsclub_api import sams_club_api
from fastapi接口.service.samsclub.exceptions.error import StopError
from fastapi接口.utils.SleepTimeGen import SleepTimeGenerator


class SamsClubCrawler(UnlimitedCrawler[tuple[int, int]]):
    async def is_stop(self) -> bool:
        return False

    async def key_params_gen(self, params):
        for grouping_info in self.task_params_list:
            yield grouping_info.parentGroupingId, grouping_info.groupingIdInt
            await asyncio.sleep(next(self.delay_gen))

    async def handle_fetch(self, params) -> WorkerStatus | Any:
        first_category, second_category = params
        if {'firstCategoryId': first_category, 'secondCategoryId': second_category} in self.unfinished_tasks:
            self.log.debug('已经爬取完成的')
            return WorkerStatus.complete
        await self.grouping_list_downloader(first_category, second_category)
        return WorkerStatus.complete

    def __init__(self):
        self.api = sams_club_api
        # 设置配置
        self.concurrent_num = 1
        self.sleep_time_gen = SleepTimeGenerator()
        self.delay_gen = self.sleep_time_gen.continuous_generator()
        self._stop_flag = False
        self.sql_helper = sql_helper
        self.fetch_grouping_id_ts = 0
        self.api.headers_gen.version_str = "5.0.123"
        self.stats_plugin = StatsPlugin(self)
        super().__init__(
            [self.stats_plugin],
            max_sem=self.concurrent_num,
            _logger=sams_club_logger
        )
        self.task_params_list = []
        self.unfinished_tasks = []
        self.main_lock = asyncio.Lock()

    class FilePath:
        fetch_grouping_id_ts = os.path.join(os.path.dirname(__file__), 'fetch_grouping_id_ts.txt')
        fetch_spu_info_ts = os.path.join(os.path.dirname(__file__), 'fetch_spu_info_ts.txt')
        grouping_data_list = lambda first_cate, second_cate, pn: os.path.join(os.path.dirname(__file__), f'csv/'
                                                                                                         f'{datetime.datetime.now().year}/'
                                                                                                         f'{datetime.datetime.now().month}/'
                                                                                                         f'{datetime.datetime.now().day}/{first_cate}_{second_cate}_{pn}.csv')

    @property
    def stop_flag(self):
        return self._stop_flag

    @stop_flag.setter
    def stop_flag(self, value):
        self._stop_flag = value

    def check_stop(self):
        if self.stop_flag:
            raise StopError("触发停止条件")

    async def grouping_id_downloader(self):
        if not self.fetch_grouping_id_ts:
            if os.path.exists(self.FilePath.fetch_grouping_id_ts):
                async with aiofiles.open(self.FilePath.fetch_grouping_id_ts, 'r') as f:
                    if content := await f.read():
                        try:
                            self.fetch_grouping_id_ts = int(content)
                        except Exception as e:
                            self.log.error(f"读取文件{self.FilePath.fetch_grouping_id_ts}内容失败，{e}")
                            self.fetch_grouping_id_ts = 0
                    else:
                        self.fetch_grouping_id_ts = 0
        if int(time.time()) - self.fetch_grouping_id_ts < 3 * 24 * 60 * 60:
            self.log.info(f'grouping_id_downloader 未到更新时间')
            return
        all_grouping_ids_level_1 = await self.api.grouping_query_navigation()
        dataList = all_grouping_ids_level_1.json().get('data', {}).get('dataList', [])  # level 1的分类不需要动
        await self.sql_helper.bulk_upsert_grouping_info(dataList)
        for grouping_id_level_1 in dataList:
            grouping_id = grouping_id_level_1.get('groupingId')
            navigationId = grouping_id_level_1.get('navigationId')
            grouping_id_level_2 = await self.api.grouping_query_children(grouping_id, navigationId)
            level_2_data_list = grouping_id_level_2.json().get('data', {})
            [x.update({"parentGroupingId": grouping_id}) for x in level_2_data_list]
            await self.sql_helper.bulk_upsert_grouping_info(level_2_data_list)
            for item in level_2_data_list:
                children = item.get('children')
                [x.update({"parentGroupingId": item.get('groupingId')}) for x in children]
                await self.sql_helper.bulk_upsert_grouping_info(children)

        self.log.info(f'grouping_id_downloader 完成')
        with open(self.FilePath.fetch_grouping_id_ts, 'w') as f:
            f.write(str(int(time.time())))

    async def grouping_list_downloader(self, firstCategoryId, secondCategoryId, pageSize: int = 20):
        """
            直接按照二级分类底下的`全部`分类去爬取
        :param secondCategoryId: 一级大分类
        :param firstCategoryId: 二级中分类
        :param pageSize:
        :return:
        """
        task_progress = await self.sql_helper.get_or_create_task_progress(firstCategoryId, secondCategoryId)
        start_page_num = task_progress.last_page_num
        frontCategoryIds = await self.sql_helper.get_front_category_ids(firstCategoryId, secondCategoryId)
        hasNextPage = True
        while hasNextPage:
            resp = await self.api.grouping_list(firstCategoryId, secondCategoryId, frontCategoryIds,
                                                start_page_num, pageSize)
            dataList = resp.json().get('data', {}).get('dataList', [])
            await self.sql_helper.bulk_upsert_spu_info(dataList)
            file_p = self.FilePath.grouping_data_list(firstCategoryId, secondCategoryId, start_page_num)
            await asyncio.to_thread(
                Path(file_p).parent.mkdir,
                parents=True, exist_ok=True
            )
            df = pd.DataFrame(dataList)
            await asyncio.to_thread(
                df.to_csv,
                file_p,
                index=False,
                header=True
            )
            hasNextPage = resp.json().get('data', {}).get('hasNextPage', False)
            start_page_num += 1
            await self.sql_helper.update_task_progress(
                first_category_id=firstCategoryId,
                second_category_id=secondCategoryId,
                new_page_num=start_page_num,
                is_finished=False
            )
            await asyncio.sleep(next(self.delay_gen))
        await self.sql_helper.update_task_progress(
            first_category_id=firstCategoryId,
            second_category_id=secondCategoryId,
            new_page_num=start_page_num,
            is_finished=True
        )

    async def on_run_end(self, end_param: ParamsType):
        async with aiofiles.open(self.FilePath.fetch_spu_info_ts, 'w') as f:
            await f.write(str(int(time.time())))

    async def check_latest_run_time(self) -> bool:
        fetch_spu_info_ts = 0
        if os.path.exists(self.FilePath.fetch_spu_info_ts):
            async with aiofiles.open(self.FilePath.fetch_spu_info_ts, 'r') as f:
                if content := await f.read():
                    try:
                        fetch_spu_info_ts = int(content)
                    except Exception as e:
                        self.log.error(f"读取文件{self.FilePath.fetch_grouping_id_ts}内容失败，{e}")
        return int(time.time()) - fetch_spu_info_ts > 15 * 60 * 60

    async def main(self):
        async with self.main_lock:
            if await self.check_latest_run_time():
                self.log.info(f'已超过15小时，开始更新数据')
                try:
                    await self.api.init_headers_info()  # 先更新一下版本信息之类的
                    await self.grouping_id_downloader()
                    self.unfinished_tasks = await sql_helper.get_unfinished_tasks()
                    for task in self.unfinished_tasks:
                        await self.grouping_list_downloader(**task)  # 继续抓取逻辑

                    self.task_params_list = await self.sql_helper.get_grouping_infos_by_level(
                        2)  # 只有2级分类的children可以对里面的内容访问，目前没有发现3级分类有children
                    await self.run((0, 0))
                except Exception as e:
                    self.log.opt(exception=True).critical(f"发生异常：{e}")

    async def get_status(self) -> ProgressStatusResp:
        return ProgressStatusResp(
            succ_count=self.stats_plugin.succ_count,
            start_ts=int(self.stats_plugin.start_time),
            total_num=len(self.task_params_list),
            progress=0 if not self.task_params_list else self.stats_plugin.processed_items_count / len(
                self.task_params_list),
            is_running=self.stats_plugin.is_running,
            update_ts=int(self.stats_plugin.last_update_time)  # 最后更新时间
        )


sams_club_crawler = SamsClubCrawler()  # 直接单例模式运行

if __name__ == "__main__":
    print(sams_club_crawler.__class__.__name__)
