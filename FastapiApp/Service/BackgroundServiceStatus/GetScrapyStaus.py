from typing import Literal, Any
from Models.v1.background_service.background_service_model import ProgressStatusResp
from Service.opus新版官方抽奖.bili_lottery_api.refresh_bili_lot_database import (
    refresh_bili_lot_database_crawler,
)
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Service.opus新版官方抽奖.预约抽奖.etc.scrapyReserveJsonData import reserve_robot
from Service.GetOthersLotDyn import (
    get_others_lot_dyn as other_lot_class,
)
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy


def get_scrapy_status(
    scrapy_type: Literal[
        "dyn",
        "topic",
        "reserve",
        "other_space",
        "other_dyn",
        "refresh_bili_official",
        "refresh_bili_reserve",
    ],
) -> Any | dict | ProgressStatusResp | None:
    match scrapy_type:
        case "dyn":
            if dyn_detail_scrapy is not None:
                return dyn_detail_scrapy.status_plugin.get_all_status()
            else:
                return dict()
        case "topic":
            if topic_robot is not None:
                return topic_robot.stats_plugin.get_all_status()
            else:
                return dict()
        case "reserve":
            if reserve_robot is not None:
                return reserve_robot.stats_plugin.get_all_status()
            else:
                return dict()
        case "other_space":
            if other_lot_class and other_lot_class.robot:
                return ProgressStatusResp(
                    succ_count=other_lot_class.robot.space_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.space_succ_counter.start_ts,
                    total_num=other_lot_class.robot.space_succ_counter.total_num,
                    progress=other_lot_class.robot.space_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.space_succ_counter.is_running,
                    update_ts=other_lot_class.robot.space_succ_counter.update_ts,
                    running_params=other_lot_class.robot.space_succ_counter.running_params,
                )
            else:
                return ProgressStatusResp()
        case "other_dyn":
            if other_lot_class and other_lot_class.robot:
                return ProgressStatusResp(
                    succ_count=other_lot_class.robot.dyn_succ_counter.succ_count,
                    start_ts=other_lot_class.robot.dyn_succ_counter.start_ts,
                    total_num=other_lot_class.robot.dyn_succ_counter.total_num,
                    progress=other_lot_class.robot.dyn_succ_counter.show_pace(),
                    is_running=other_lot_class.robot.dyn_succ_counter.is_running,
                    update_ts=other_lot_class.robot.dyn_succ_counter.update_ts,
                    running_params=other_lot_class.robot.dyn_succ_counter.running_params,
                )
            else:
                return ProgressStatusResp()
        case "refresh_bili_official":
            if (
                refresh_bili_lot_database_crawler.extract_official_lottery
                and refresh_bili_lot_database_crawler.extract_official_lottery.refresh_official_lot_progress
            ):
                _progress = (
                    refresh_bili_lot_database_crawler.extract_official_lottery.refresh_official_lot_progress
                )
                return ProgressStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts,
                )
            else:
                return ProgressStatusResp()
        case "refresh_bili_reserve":
            if (
                refresh_bili_lot_database_crawler.reserve_robot
                and refresh_bili_lot_database_crawler.reserve_robot.refresh_progress_counter
            ):
                _progress = (
                    refresh_bili_lot_database_crawler.reserve_robot.refresh_progress_counter
                )
                return ProgressStatusResp(
                    succ_count=_progress.succ_count,
                    start_ts=_progress.start_ts,
                    total_num=_progress.total_num,
                    progress=_progress.show_pace(),
                    is_running=_progress.is_running,
                    update_ts=_progress.update_ts,
                )
            else:
                return ProgressStatusResp()
