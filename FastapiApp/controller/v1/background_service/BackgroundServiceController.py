import asyncio
import inspect
from datetime import datetime
from typing import Union, Any
from Models.common import CommonResponseModel
from Models.v1.background_service.background_service_model import (
    AllLotScrapyStatusResp,
    BackgroundServiceName,
    ProgressStatusResp,
    ProxyStatusResp,
)
from Models.v1.background_service.scheduler_status_model import (
    GlobalSchedulerStatusModel,
    SchedulerInfoModel,
    JobInfoModel,
    SchedulerJobDetailModel,
    ExecutionInfoModel,
)
from Service.BackgroundService.CrawlerScheduler import background_service

from Service.BackgroundServiceStatus.GetScrapyStaus import get_scrapy_status
from Service.BaseCrawler.launcher.scheduler_launcher import (
    BaseScheduler,
    GenericCrawlerScheduler,
)
from Service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from Service.GrpcModule.GrpcSrc.监控up动态.bili_dynamic_monitor import (
    bili_space_monitor,
)
from Utils.通用.Common import GLOBAL_SCHEDULER
from Utils.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper
from ApiRoutes import RouterPaths, RouterNames
from .base import new_router

router = new_router()


def start_monitor_tasks(show_log: bool):
    back_ground_tasks = [
        asyncio.create_task(bili_space_monitor.main(show_log=show_log))
    ]
    return back_ground_tasks


@router.get(
    RouterPaths.GET_DYNAMIC_SCRAPY_STATUS,
    name=RouterNames.GET_DYNAMIC_SCRAPY_STATUS,
    description="获取动态爬虫状态",
    response_model=CommonResponseModel[Union[Any, None]],
    response_model_exclude_none=True,
)
def get_dynamic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status("dyn"))


@router.get(
    RouterPaths.GET_TOPIC_SCRAPY_STATUS,
    name=RouterNames.GET_TOPIC_SCRAPY_STATUS,
    description="获取话题爬虫状态",
    response_model=CommonResponseModel[Union[Any, None]],
    response_model_exclude_none=True,
)
def get_topic_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status("topic"))


@router.get(
    RouterPaths.GET_RESERVE_SCRAPY_STATUS,
    name=RouterNames.GET_RESERVE_SCRAPY_STATUS,
    description="获取预约爬虫状态",
    response_model=CommonResponseModel[Union[Any, None]],
    response_model_exclude_none=True,
)
def get_reserve_scrapy_status():
    return CommonResponseModel(data=get_scrapy_status("reserve"))


@router.get(
    RouterPaths.GET_ALL_SCRAPY_STATUS,
    name=RouterNames.GET_ALL_SCRAPY_STATUS,
    description="获取所有爬虫状态",
    response_model=CommonResponseModel[Union[AllLotScrapyStatusResp, None]],
    response_model_exclude_none=True,
)
def get_all_scrapy_status():
    return CommonResponseModel(
        data=AllLotScrapyStatusResp(
            dyn_scrapy_status=get_scrapy_status("dyn"),
            topic_scrapy_status=get_scrapy_status("topic"),
            reserve_scrapy_status=get_scrapy_status("reserve"),
        )
    )


@router.get(
    RouterPaths.GET_OTHERS_LOT_SPACE_STATUS,
    name=RouterNames.GET_OTHERS_LOT_SPACE_STATUS,
    description="获取其他人空间爬虫的状态",
    response_model=CommonResponseModel[Union[ProgressStatusResp, None]],
)
def get_others_lot_space_status():
    return CommonResponseModel(data=get_scrapy_status("other_space"))


@router.get(
    RouterPaths.GET_OTHERS_LOT_DYN_STATUS,
    name=RouterNames.GET_OTHERS_LOT_DYN_STATUS,
    description="获取其他人动态爬虫的状态",
    response_model=CommonResponseModel[Union[ProgressStatusResp, None]],
)
def get_others_lot_dyn_status():
    return CommonResponseModel(data=get_scrapy_status("other_dyn"))


@router.get(
    RouterPaths.GET_REFRESH_BILI_OFFICIAL_STATUS,
    name=RouterNames.GET_REFRESH_BILI_OFFICIAL_STATUS,
    description="获取刷新B站官方和充电抽奖结果状态",
    response_model=CommonResponseModel[Union[ProgressStatusResp, None]],
)
def get_refresh_bili_official_status():
    return CommonResponseModel(data=get_scrapy_status("refresh_bili_official"))


@router.get(
    RouterPaths.GET_REFRESH_BILI_RESERVE_STATUS,
    name=RouterNames.GET_REFRESH_BILI_RESERVE_STATUS,
    description="获取刷新B站预约抽奖结果状态",
    response_model=CommonResponseModel[Union[ProgressStatusResp, None]],
)
def get_refresh_bili_reserve_status():
    return CommonResponseModel(data=get_scrapy_status("refresh_bili_reserve"))


@router.get(
    RouterPaths.GET_PROXY_STATUS,
    name=RouterNames.GET_PROXY_STATUS,
    description="获取代理状态",
    response_model=CommonResponseModel[Union[ProxyStatusResp, None]],
)
async def get_proxy_status():
    return CommonResponseModel(data=await SQLHelper.get_proxy_database_redis())


@router.get(
    RouterPaths.GET_GLOBAL_JOBS,
    name=RouterNames.GET_GLOBAL_JOBS,
    description="全局定时任务",
    response_model=CommonResponseModel[Any],
)
def global_schedule():
    ret = []
    for job in GLOBAL_SCHEDULER.get_jobs():
        ret.append(str(job))
    return CommonResponseModel(data=ret)


@router.get(
    RouterPaths.GET_ALL_STAT,
    name=RouterNames.GET_ALL_STAT,
    description="后台服务状态",
    response_model=CommonResponseModel[Any],
    response_model_exclude_none=True,
)
def background_service_status():
    ret_list = []
    members = inspect.getmembers(background_service)
    for name, value in members:
        if isinstance(value, GenericCrawlerScheduler):
            for plugin in value.crawler.plugins:
                if isinstance(plugin, StatsPlugin):
                    ret_list.append(
                        {
                            f"{name}": {
                                StatsPlugin.__name__: plugin.get_all_status(),
                                "exec_info": value.exec_info.info,
                            }
                        }
                    )
    return CommonResponseModel(data=ret_list)


@router.post(RouterPaths.START_SERVICE, name=RouterNames.START_SERVICE, description="启动特定的后台爬虫服务")
def start_background_service(background_service_name: BackgroundServiceName):
    """
    启动指定的后台爬虫服务
    :param background_service_name: 服务名称枚举，必须是 BackgroundServiceName 枚举值
    :return: 操作结果
    """
    members = inspect.getmembers(background_service)
    scheduler = None
    for name, value in members:
        if name == background_service_name.value and isinstance(value, BaseScheduler):
            scheduler = value
            break

    if scheduler is None:
        return CommonResponseModel(
            code=404, msg=f"未找到名为 {background_service_name.value} 的后台服务"
        )

    try:
        if GLOBAL_SCHEDULER.get_job(scheduler.job_id) is not None:
            return CommonResponseModel(
                code=400, msg=f"服务 {background_service_name.value} 已经在运行中"
            )

        GLOBAL_SCHEDULER.add_job(
            scheduler.run,
            name=scheduler.job_id,
            trigger=scheduler.trigger,
            id=scheduler.job_id,
            next_run_time=datetime.now(),
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        return CommonResponseModel(
            code=0, msg=f"成功启动服务 {background_service_name.value}"
        )
    except Exception as e:
        return CommonResponseModel(code=500, msg=f"启动服务失败: {str(e)}")


@router.post(RouterPaths.STOP_SERVICE, name=RouterNames.STOP_SERVICE, description="停止特定的后台爬虫服务")
def stop_background_service(background_service_name: BackgroundServiceName):
    """
    停止指定的后台爬虫服务
    :param background_service_name: 服务名称枚举，必须是 BackgroundServiceName 枚举值
    :return: 操作结果
    """
    members = inspect.getmembers(background_service)
    scheduler = None
    for name, value in members:
        if name == background_service_name.value and isinstance(value, BaseScheduler):
            scheduler = value
            break

    if scheduler is None:
        return CommonResponseModel(
            code=404, msg=f"未找到名为 {background_service_name.value} 的后台服务"
        )

    try:
        if GLOBAL_SCHEDULER.get_job(scheduler.job_id) is None:
            return CommonResponseModel(
                code=400, msg=f"服务 {background_service_name.value} 未在运行"
            )

        scheduler.remove()
        return CommonResponseModel(
            code=0, msg=f"成功停止服务 {background_service_name.value}"
        )
    except Exception as e:
        return CommonResponseModel(code=500, msg=f"停止服务失败: {str(e)}")


@router.post(RouterPaths.RESTART_SERVICE, name=RouterNames.RESTART_SERVICE, description="重启特定的后台爬虫服务")
def restart_background_service(background_service_name: BackgroundServiceName):
    """
    重启指定的后台爬虫服务
    :param background_service_name: 服务名称枚举，必须是 BackgroundServiceName 枚举值
    :return: 操作结果
    """
    members = inspect.getmembers(background_service)
    scheduler = None
    for name, value in members:
        if name == background_service_name.value and isinstance(value, BaseScheduler):
            scheduler = value
            break

    if scheduler is None:
        return CommonResponseModel(
            code=404, msg=f"未找到名为 {background_service_name.value} 的后台服务"
        )

    try:
        # 先停止（移除任务）
        if GLOBAL_SCHEDULER.get_job(scheduler.job_id) is not None:
            scheduler.remove()

        # 再启动（添加任务）
        GLOBAL_SCHEDULER.add_job(
            scheduler.run,
            name=scheduler.job_id,
            trigger=scheduler.trigger,
            id=scheduler.job_id,
            next_run_time=datetime.now(),
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        return CommonResponseModel(
            code=0, msg=f"成功重启服务 {background_service_name.value}"
        )
    except Exception as e:
        return CommonResponseModel(code=500, msg=f"重启服务失败: {str(e)}")


@router.get(
    RouterPaths.GET_GLOBAL_SCHEDULER_STATUS,
    name=RouterNames.GET_GLOBAL_SCHEDULER_STATUS,
    description="全局定时任务详细状态",
    response_model=CommonResponseModel[GlobalSchedulerStatusModel],
    response_model_exclude_none=True,
)
def global_scheduler_status():
    """
    获取全局调度器的详细状态信息
    包括调度器自身状态和所有任务的详细信息
    """
    # 获取调度器基本信息
    scheduler_info = SchedulerInfoModel(
        running=GLOBAL_SCHEDULER.running,
        timezone=str(GLOBAL_SCHEDULER.timezone),
        executor_count=(
            len(GLOBAL_SCHEDULER._executors)
            if hasattr(GLOBAL_SCHEDULER, "_executors")
            else 0
        ),
        job_count=len(GLOBAL_SCHEDULER.get_jobs()),
    )

    # 收集所有任务信息
    jobs_details = []
    for job in GLOBAL_SCHEDULER.get_jobs():
        # 基本任务信息
        job_info = JobInfoModel(
            id=job.id,
            name=job.name,
            func_ref=str(job.func_ref),
            trigger=str(job.trigger),
            next_run_time=job.next_run_time.timestamp() if job.next_run_time else None,
        )

        # 尝试获取任务关联的执行信息（如果是爬虫任务）
        execution_info = None
        # 检查是否可以通过BackgroundService访问到更详细的执行信息
        members = inspect.getmembers(background_service)
        for name, value in members:
            if isinstance(value, GenericCrawlerScheduler) and value.job_id == job.id:
                # 从CrawlerExecutionInfoModel转换为ExecutionInfoModel
                crawler_info = value.exec_info.info
                last_exec_time = crawler_info.last_exec_time
                execution_info = ExecutionInfoModel(
                    crawler_name=crawler_info.crawler_name,
                    default_interval_seconds=crawler_info.default_interval_seconds,
                    last_exec_time=(
                        last_exec_time.timestamp() if last_exec_time else None
                    ),
                )
                break

        jobs_details.append(
            SchedulerJobDetailModel(job_info=job_info, execution_info=execution_info)
        )

    # 构造完整状态模型
    result = GlobalSchedulerStatusModel(
        scheduler_info=scheduler_info, jobs=jobs_details
    )

    return CommonResponseModel(data=result)
