from log.base_log import reserve_lot_logger, official_lot_logger
from scripts.database.clean_backup_outdated_dynamic import cleaner
from Service.BaseCrawler.launcher.scheduler_launcher import GenericCrawlerScheduler, BaseScheduler
from Service.GrpcModule.GrpcSrc.获取取关对象.GetRmFollowingListV2 import gmflv2
from Service.opus新版官方抽奖.bili_lottery_api.scrapyLotteryDataFromBapi import LotteryApiRobot
from Service.samsclub.main import sams_club_crawler, sams_club_SPU_detail_crawler
from Utils.代理.redisProxyRequest.GetProxyFromNet import get_proxy_methods
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy
from Service.opus新版官方抽奖.bili_lottery_api.refresh_bili_lot_database import \
    refresh_bili_lot_database_crawler


class BackgroundService:
    dyn_detail_database_cleaner = BaseScheduler(
        func=cleaner.do_clean,
        cron_expr="0 0 * * *",
        crawler_name="dyn_detail_database_cleaner",
        default_interval_seconds=2 * 3600,
    )
    get_proxy_methods_scheduler = GenericCrawlerScheduler(
        crawler=get_proxy_methods,
        cron_expr="0 */5 * * *",
        default_interval_seconds=12 * 3600,
    )
    samsclub_scheduler = GenericCrawlerScheduler(
        crawler=sams_club_crawler,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    samsclub_spu_detail_scheduler = GenericCrawlerScheduler(
        crawler=sams_club_SPU_detail_crawler,
        cron_expr="0 4 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_reserve_lot = GenericCrawlerScheduler(
        crawler=reserve_robot,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_dyn = GenericCrawlerScheduler(
        crawler=dyn_detail_scrapy,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    get_topic = GenericCrawlerScheduler(
        crawler=topic_robot,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    refresh_bili_lotdata_database = GenericCrawlerScheduler(
        crawler=refresh_bili_lot_database_crawler,
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
    )
    lottery_api_robot_dyn_scheduler = GenericCrawlerScheduler(
        crawler= LotteryApiRobot(log=official_lot_logger, business_type=2, sem_num=2),
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
        crawler_name='lottery_api_robot_dyn'
    )
    lottery_api_robot_reserve_scheduler = GenericCrawlerScheduler(
        crawler=LotteryApiRobot(log=reserve_lot_logger, business_type=10, sem_num=2),
        cron_expr="0 0 * * *",
        default_interval_seconds=15 * 3600,
        crawler_name='lottery_api_robot_reserve'
    )
    gmflv2_scheduler = GenericCrawlerScheduler(
        crawler=gmflv2,
        cron_expr="0 0 * * *",
        default_interval_seconds=1,
        crawler_name='gmflv2'
    )
