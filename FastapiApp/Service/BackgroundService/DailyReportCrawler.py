import inspect
from datetime import datetime
from Service.BaseCrawler.launcher.scheduler_launcher import GenericCrawlerScheduler
from Service.BaseCrawler.plugin.statusPlugin import StatsPlugin, CrawlerHealthStatus
from Utils.推送.PushMe import a_pushme
from log.base_log import pushme_logger


# 需要监控卡住状态的爬虫调度器名称（官方抽奖 + 第三方爬虫）
_MONITORED_CRAWLER_NAMES = {
    "GET_RESERVE_INFO",        # 预约抽奖
    "GET_DYN",                 # 动态抽奖
    "GET_TOPIC",               # 话题抽奖
    "REFRESH_BILI_LOTDATA_DATABASE",  # 刷新B站抽奖数据库
    "LOTTERY_API_ROBOT_DYN_SCHEDULER",    # 官方动态抽奖API
    "LOTTERY_API_ROBOT_RESERVE_SCHEDULER",  # 官方预约抽奖API
    "SAMSCCLUB_SCHEDULER",     # 山姆会员店（第三方）
    "SAMSCCLUB_SPU_DETAIL_SCHEDULER",  # 山姆SPU详情（第三方）
}

# 记录上次推送时各爬虫的卡住状态，避免重复推送
_last_stuck_state: dict[str, bool] = {}


class CrawlerStuckChecker:
    """爬虫卡住检测器，仅在目标爬虫卡住时推送通知"""

    def _get_monitored_crawlers(self) -> dict[str, GenericCrawlerScheduler]:
        """获取所有需要监控的爬虫调度器（惰性导入避免循环引用）"""
        from Service.BackgroundService.CrawlerScheduler import background_service

        result: dict[str, GenericCrawlerScheduler] = {}
        members = inspect.getmembers(background_service)
        for name, value in members:
            if name in _MONITORED_CRAWLER_NAMES and isinstance(value, GenericCrawlerScheduler):
                result[name] = value
        return result

    def _get_stats_plugin(self, scheduler: GenericCrawlerScheduler) -> StatsPlugin | None:
        """从调度器中获取 StatsPlugin"""
        for plugin in scheduler.crawler.plugins:
            if isinstance(plugin, StatsPlugin):
                return plugin
        return None

    async def check_and_report_stuck(self):
        """检查所有目标爬虫的健康状态，仅在卡住时推送"""
        try:
            crawlers = self._get_monitored_crawlers()
            stuck_list: list[str] = []
            normal_list: list[str] = []

            for name, scheduler in crawlers.items():
                stats = self._get_stats_plugin(scheduler)
                if stats is None:
                    continue

                health = stats.health_status
                if health == CrawlerHealthStatus.STUCK:
                    stuck_list.append(name)
                else:
                    normal_list.append(name)

            # 更新状态并仅在状态变化时推送
            new_stuck_names = set(stuck_list)
            for name in _MONITORED_CRAWLER_NAMES:
                was_stuck = _last_stuck_state.get(name, False)
                is_stuck = name in new_stuck_names
                if is_stuck and not was_stuck:
                    # 新卡住的爬虫，推送通知
                    _last_stuck_state[name] = True
                    await self._push_stuck_notification([name])
                elif not is_stuck and was_stuck:
                    # 之前卡住现在恢复了
                    _last_stuck_state[name] = False
                    await a_pushme(
                        title=f"爬虫恢复通知",
                        content=f"✅ 爬虫 **{name}** 已恢复正常运行\n\n恢复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        push_type='markdown',
                    )

            pushme_logger.debug(
                f"爬虫卡住检测完成: 卡住={stuck_list}, 正常={normal_list}"
            )

        except Exception as e:
            pushme_logger.exception(f"爬虫卡住检测出错: {e}")

    async def _push_stuck_notification(self, stuck_names: list[str]):
        """推送爬虫卡住通知"""
        names_str = "、".join(stuck_names)
        content = (
            f"⚠️ 以下爬虫可能已卡住，请及时检查：\n\n"
            f"**卡住爬虫**: {names_str}\n\n"
            f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"可能原因：\n"
            f"- 爬虫进程无响应超过10分钟\n"
            f"- 运行中的任务超过1天未更新"
        )
        await a_pushme(
            title=f"爬虫卡住告警 - {names_str}",
            content=content,
            push_type='markdown',
        )


crawler_stuck_checker = CrawlerStuckChecker()