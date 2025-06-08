import asyncio
import time

from fastapi接口.service.samsclub.Sql.SqlHelper import sql_helper
from fastapi接口.service.samsclub.api.samsclub_api import sams_club_api
from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.service.samsclub.exceptions.error import StopError
from fastapi接口.utils.SleepTimeGen import SleepTimeGenerator
import os


class SamsClubCrawler:
    class FilePath:
        fetch_grouping_id_ts = os.path.join(os.path.dirname(__file__), 'fetch_grouping_id_ts.txt')

    def __init__(self):
        self.api = sams_club_api
        self.log = sams_club_logger

        # 设置配置
        self.concurrent_num = 10
        self.sleep_time_gen = SleepTimeGenerator()
        self.delay_gen = self.sleep_time_gen.continuous_generator()
        self._stop_flag = False
        self._sem = asyncio.Semaphore(self.concurrent_num)
        self.sql_helper = sql_helper
        self.fetch_grouping_id_ts = 0

    @property
    def stop_flag(self):
        return self._stop_flag

    @stop_flag.setter
    def stop_flag(self, value):
        if value:
            self._stop_flag = value

    def check_stop(self):
        if self.stop_flag:
            raise StopError("触发停止条件")

    async def grouping_id_downloader(self):
        if not self.fetch_grouping_id_ts:
            if os.path.exists(self.FilePath.fetch_grouping_id_ts):
                with open(self.FilePath.fetch_grouping_id_ts, 'r') as f:
                    if content := f.read():
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

    async def grouping_list_downloader_params_gen(self):
        grouping_infos_level2 = await self.sql_helper.get_grouping_infos_by_level(
            2)  # 只有2级分类的children可以对里面的内容访问，目前没有发现3级分类有children
        for grouping_info in grouping_infos_level2:
            yield grouping_info.parentGroupingId, grouping_info.groupingIdInt
            await asyncio.sleep(next(self.delay_gen))

    async def scraping_spu_info_by_grouping_id(self, unfinished_tasks: list[dict] = None):
        if unfinished_tasks is None:
            unfinished_tasks = []
        async for first_category, second_category in self.grouping_list_downloader_params_gen():
            if {'firstCategoryId': first_category, 'secondCategoryId': second_category} in unfinished_tasks:
                self.log.debug('已经爬取完成的')
                continue
            await self.grouping_list_downloader(first_category, second_category)

    async def main(self):
        try:
            await self.grouping_id_downloader()
            unfinished_tasks = await sql_helper.get_unfinished_tasks()
            for task in unfinished_tasks:
                await self.grouping_list_downloader(**task)  # 继续抓取逻辑
            await self.scraping_spu_info_by_grouping_id(unfinished_tasks)
        except Exception as e:
            self.log.opt(exception=True).critical(f"发生异常：{e}")


if __name__ == "__main__":
    sams_club_crawler = SamsClubCrawler()
    res = asyncio.run(sams_club_crawler.main())
    print(res)
