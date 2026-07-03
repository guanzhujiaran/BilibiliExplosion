from log.base_log import reserve_lot_logger, official_lot_logger
from scripts.database.clean_backup_outdated_dynamic import cleaner
from Service.BaseCrawler.launcher.scheduler_launcher import (
    GenericCrawlerScheduler,
    BaseScheduler,
)
from Service.GrpcModule.GrpcSrc.获取取关对象.GetRmFollowingListV2 import gmflv2
from Service.opus新版官方抽奖.bili_lottery_api.scrapyLotteryDataFromBapi import (
    LotteryApiRobot,
)
from Service.samsclub.main import sams_club_crawler, sams_club_SPU_detail_crawler
from Utils.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy
from Service.opus新版官方抽奖.bili_lottery_api.refresh_bili_lot_database import (
    refresh_bili_lot_database_crawler,
)
from Service.BackgroundService.DailyReportCrawler import crawler_stuck_checker
from Models.v1.background_service.background_service_model import BackgroundServiceName


class BackgroundService:
    STUCK_CHECK_SCHEDULER: BaseScheduler | None = None
    DYN_DETAIL_DATABASE_CLEANER: BaseScheduler | None = None
    GET_PROXY_METHODS_SCHEDULER: GenericCrawlerScheduler | None = None
    SAMSCCLUB_SCHEDULER: GenericCrawlerScheduler | None = None
    SAMSCCLUB_SPU_DETAIL_SCHEDULER: GenericCrawlerScheduler | None = None
    GET_RESERVE_INFO: GenericCrawlerScheduler | None = None
    GET_DYN: GenericCrawlerScheduler | None = None
    GET_TOPIC: GenericCrawlerScheduler | None = None
    REFRESH_BILI_LOTDATA_DATABASE: GenericCrawlerScheduler | None = None
    LOTTERY_API_ROBOT_DYN_SCHEDULER: GenericCrawlerScheduler | None = None
    LOTTERY_API_ROBOT_RESERVE_SCHEDULER: GenericCrawlerScheduler | None = None
    GMFLV2_SCHEDULER: GenericCrawlerScheduler | None = None

    def __init__(self):
        self.STUCK_CHECK_SCHEDULER = BaseScheduler(
            func=crawler_stuck_checker.check_and_report_stuck,
            cron_expr="*/10 * * * *",  # 每10分钟检查一次爬虫是否卡住
            default_interval_seconds=600,  # 10分钟间隔
            crawler_name=BackgroundServiceName.STUCK_CHECK_SCHEDULER.value
        )
        self.DYN_DETAIL_DATABASE_CLEANER = BaseScheduler(
            func=cleaner.do_clean,
            cron_expr="0 0 * * *",
            crawler_name=BackgroundServiceName.DYN_DETAIL_DATABASE_CLEANER.value,
            default_interval_seconds=2 * 3600,
        )
        self.GET_PROXY_METHODS_SCHEDULER = GenericCrawlerScheduler(
            crawler=get_proxy_methods,
            cron_expr="0 */5 * * *",
            default_interval_seconds=12 * 3600,
        )
        self.SAMSCCLUB_SCHEDULER = GenericCrawlerScheduler(
            crawler=sams_club_crawler,
            cron_expr="0 3 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.SAMSCCLUB_SPU_DETAIL_SCHEDULER = GenericCrawlerScheduler(
            crawler=sams_club_SPU_detail_crawler,
            cron_expr="0 4 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.GET_RESERVE_INFO = GenericCrawlerScheduler(
            crawler=reserve_robot,
            cron_expr="0 1 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.GET_DYN = GenericCrawlerScheduler(
            crawler=dyn_detail_scrapy,
            cron_expr="0 2 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.GET_TOPIC = GenericCrawlerScheduler(
            crawler=topic_robot,
            cron_expr="0 3 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.REFRESH_BILI_LOTDATA_DATABASE = GenericCrawlerScheduler(
            crawler=refresh_bili_lot_database_crawler,
            cron_expr="0 4 * * *",
            default_interval_seconds=15 * 3600,
        )
        self.LOTTERY_API_ROBOT_DYN_SCHEDULER = GenericCrawlerScheduler(
            crawler=LotteryApiRobot(
                log=official_lot_logger, business_type=2, sem_num=2
            ),
            cron_expr="0 5 * * *",
            default_interval_seconds=15 * 3600,
            crawler_name=BackgroundServiceName.LOTTERY_API_ROBOT_DYN_SCHEDULER.value,
        )
        self.LOTTERY_API_ROBOT_RESERVE_SCHEDULER = GenericCrawlerScheduler(
            crawler=LotteryApiRobot(
                log=reserve_lot_logger, business_type=10, sem_num=2
            ),
            cron_expr="0 6 * * *",
            default_interval_seconds=15 * 3600,
            crawler_name=BackgroundServiceName.LOTTERY_API_ROBOT_RESERVE_SCHEDULER.value,
        )
        self.GMFLV2_SCHEDULER = GenericCrawlerScheduler(
            crawler=gmflv2,
            cron_expr="0 7 * * *",
            default_interval_seconds=1,
            crawler_name=BackgroundServiceName.GMFLV2_SCHEDULER.value,
        )


background_service = BackgroundService()

__all__ = ["background_service", "BackgroundService"]
