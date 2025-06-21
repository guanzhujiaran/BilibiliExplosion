import time
from typing import AsyncGenerator, Any

from fastapi接口.dao.biliLotteryStatisticRedisObj import lottery_data_statistic_redis
from fastapi接口.log.base_log import background_task_logger
from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from fastapi接口.models.lottery_database.bili.LotteryDataModels import BiliLotStatisticLotTypeEnum, \
    BiliLotStatisticRankTypeEnum, BiliLotStatisticRankDateTypeEnum
from fastapi接口.scripts.database.同步向量数据库.sync_bili_lottery_data import sync_bili_lottery_data, \
    del_outdated_bili_lottery_data
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import \
    grpc_sql_helper
from fastapi接口.service.opus新版官方抽奖.转发抽奖.提交专栏信息 import ExtractOfficialLottery
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from fastapi接口.utils.Common import asyncio_gather


class RBDParamsType(CustomBaseModel):
    BiliLotStatisticRankDateType: BiliLotStatisticRankDateTypeEnum
    BiliLotStatisticLotType: BiliLotStatisticLotTypeEnum
    BiliLotStatisticRankType: BiliLotStatisticRankTypeEnum


class RefreshBiliLotDatabaseCrawler(UnlimitedCrawler[None]):
    def __init__(self):
        max_sem = 10
        self.status_plugin = StatsPlugin(self)
        super().__init__(
            max_sem=max_sem,
            _logger=background_task_logger,
            plugins=[self.status_plugin]
        )
        self.reserve_robot = reserve_robot
        self.extract_official_lottery = ExtractOfficialLottery()

    async def is_stop(self) -> bool:
        ...

    async def key_params_gen(self, params: None) -> AsyncGenerator[RBDParamsType, None]:
        for _lot_type in BiliLotStatisticLotTypeEnum:
            for j in BiliLotStatisticRankTypeEnum:
                for k in BiliLotStatisticRankDateTypeEnum:
                    yield RBDParamsType(
                        BiliLotStatisticRankDateType=k,
                        BiliLotStatisticLotType=_lot_type,
                        BiliLotStatisticRankType=j
                    )

    async def handle_fetch(self, params: RBDParamsType) -> WorkerStatus | Any:
        k = params.BiliLotStatisticRankDateType
        _lot_type = params.BiliLotStatisticLotType
        j = params.BiliLotStatisticRankType
        start_ts, end_ts = k.get_start_end_ts()
        await lottery_data_statistic_redis.set_lot_prize_count(
            date=k,
            lot_type=_lot_type,
            rank_type=j,
            uid_atari_count_dict=dict(
                await grpc_sql_helper.get_all_lottery_result_rank(
                    start_ts=start_ts,
                    end_ts=end_ts,
                    business_type=BiliLotStatisticLotTypeEnum.lot_type_2_business_type(_lot_type),
                    rank_type=j
                )
            )
        )

    async def sync_bili_user_info_simple(self):
        res = await grpc_sql_helper.get_all_bili_user_info()
        await lottery_data_statistic_redis.set_bili_user_info_bulk(res)

    async def main(self, is_api_update=True, *args, **kwargs):
        """
        运行的主函数
        """
        await self.run(None)
        await self.sync_bili_user_info_simple()
        if is_api_update:
            await asyncio_gather(self.reserve_robot.refresh_not_drawn_lottery(),
                                 self.extract_official_lottery.get_all_lots(is_api_update=True), log=self.log)
            await self.run(None)  # 第二遍同步
            await asyncio_gather(
                *[lottery_data_statistic_redis.set_sync_ts(lot_type=_lot_type, ts=int(time.time())) for _lot_type in
                  BiliLotStatisticLotTypeEnum], log=self.log
            )
            await self.sync_bili_user_info_simple()
        await sync_bili_lottery_data()
        await del_outdated_bili_lottery_data()


refresh_bili_lot_database_crawler = RefreshBiliLotDatabaseCrawler()
