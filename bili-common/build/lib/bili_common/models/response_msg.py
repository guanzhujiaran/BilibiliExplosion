"""
Response Message 模块 - 响应消息字符串枚举（单一来源）
"""

from enum import StrEnum


class ResponseMsg(StrEnum):
    """响应消息字符串枚举"""

    exception_browser_notify_conf_not_found = "浏览器通知配置不存在"

    exception_browser_id_is_none = "浏览器ID不能为空~"
    exception_browser_id_not_belone_to_user = (
        "浏览器ID {browser_id} 不属于当前用户或不存在"
    )

    exception_not_logged_in = "未登录，请提供有效的x-bili-mid请求头"
    exception_invalid_uid = "无效的用户ID，请重新登录"
    exception_invalid_mid_format = "Invalid mid format in x-bili-mid header"

    exception_plugin_id_is_none = "插件ID不能为空"
    exception_plugin_id_not_belong_to_user = "插件ID {plugin_id} 不属于当前用户或不存在"

    exception_browser_not_started = "浏览器未启动或已停止"
    exception_browser_page_index_error = "页面索引 {page_index} 无效"
    exception_video_stream_init_failed = "视频流初始化失败: {error}"

    exception_get_browser_session_failed = "获取浏览器会话失败: {error}"
    exception_get_browser_info_failed = "获取浏览器信息失败: {error}"

    exception_webrtc_stream_not_active = "WebRTC 流未激活"

    exception_bilibili_login_failed = "B站登录失败"

    exception_browser_fingerprint_not_found = "浏览器指纹不存在"

    exception_fingerprint_limit_exceeded = "已达到最大指纹数量限制，当前等级最多可创建 {max} 个指纹"


__all__ = ["ResponseMsg"]
