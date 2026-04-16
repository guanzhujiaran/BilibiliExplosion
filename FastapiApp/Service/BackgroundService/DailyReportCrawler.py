from datetime import datetime
from typing import List, Dict, Any
import httpx
from log.base_log import pushme_logger
from Utils.PushMe import a_pushme
from CONFIG import CONFIG


class DailyReportGenerator:
    """每日报告生成器，用于收集后台服务状态并发送到PushMe"""
    
    def __init__(self):
        self.api_base_url = f"http://localhost:{getattr(CONFIG, 'port', 23333)}"
    
    async def fetch_all_background_service_status(self) -> List[Dict[str, Any]]:
        """获取所有后台服务的状态信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/api/v1/background_service/BackgroundService/AllStat",
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('code') == 0:
                    return result.get('data', [])
                else:
                    pushme_logger.error(f"获取后台服务状态失败: {result.get('msg', '未知错误')}")
                    return []
        except Exception as e:
            pushme_logger.exception(f"调用BackgroundService/AllStat API时出错: {e}")
            return []
    
    def generate_summary_report(self, service_statuses: List[Dict[str, Any]]) -> str:
        """根据服务状态生成摘要报告"""
        if not service_statuses:
            return "⚠️ 无法获取后台服务状态信息"
        
        report_lines = [
            f"📊 B站抽奖系统每日报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            ""
        ]
        
        total_services = len(service_statuses)
        active_services = 0
        
        for service_status in service_statuses:
            for service_name, status_data in service_status.items():
                report_lines.append(f"🔧 服务名称: {service_name}")
                
                # 提取统计插件信息
                stats_plugin_info = status_data.get('StatsPlugin', {})
                exec_info = status_data.get('exec_info', {})
                
                if stats_plugin_info:
                    succ_count = stats_plugin_info.get('succ_count', 0)
                    fail_count = stats_plugin_info.get('fail_count', 0)
                    total_requests = stats_plugin_info.get('total_requests', 0)
                    success_rate = (succ_count / total_requests * 100) if total_requests > 0 else 0
                    
                    report_lines.extend([
                        f"   ✅ 成功次数: {succ_count}",
                        f"   ❌ 失败次数: {fail_count}",
                        f"   📈 总请求数: {total_requests}",
                        f"   🎯 成功率: {success_rate:.2f}%"
                    ])
                    
                    # 如果成功率较高，则标记为活跃服务
                    if success_rate > 80:
                        active_services += 1
                
                if exec_info:
                    last_exec_time = exec_info.get('last_exec_time')
                    if last_exec_time:
                        # 将时间戳转换为可读格式
                        try:
                            dt = datetime.fromtimestamp(last_exec_time)
                            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                            report_lines.append(f"   ⏰ 最后执行时间: {formatted_time}")
                        except:
                            report_lines.append(f"   ⏰ 最后执行时间: {last_exec_time}")
                
                report_lines.append("")  # 空行分隔不同服务
        
        # 添加总结信息
        report_lines.extend([
            "=" * 50,
            f"📋 总计服务数: {total_services}",
            f"✅ 活跃服务数: {active_services}",
            f"📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ])
        
        return "\n".join(report_lines)
    
    async def send_daily_report(self):
        """发送每日报告到PushMe"""
        try:
            # 获取所有后台服务状态
            service_statuses = await self.fetch_all_background_service_status()
            
            # 生成摘要报告
            summary_report = self.generate_summary_report(service_statuses)
            
            # 发送到PushMe
            title = f"B站抽奖系统每日报告 - {datetime.now().strftime('%Y-%m-%d')}"
            await a_pushme(title=title, content=summary_report, push_type='markdown')
            
            pushme_logger.info("每日报告已成功发送到PushMe")
            
        except Exception as e:
            error_msg = f"发送每日报告时出错: {str(e)}"
            pushme_logger.exception(error_msg)
            await a_pushme(
                title="B站抽奖系统每日报告 - 发送失败",
                content=f"❌ {error_msg}\n\n请检查系统日志以获取更多信息。",
                push_type='text'
            )


# 创建全局实例
daily_report_generator = DailyReportGenerator()
