"""
Response Message 模块 - 响应消息字符串枚举（单一来源）

i18n 约定：枚举值存「原文」（中文），对外返回时需调用 `.t()` 做延迟翻译
（gettext 依赖请求级 ContextVar，不能在类定义期翻译）。
动态占位符：`.t(browser_id=...)` 会用 `.format()` 填充。
"""

from bili_common.models import StrEnumAutoDoc

from bili_common.i18n import _


class ResponseMsg(StrEnumAutoDoc):
    """响应消息字符串枚举（值=原文，调用 `.t()` 取翻译）"""

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

    def t(self, **kwargs) -> str:
        """返回当前语言下的翻译（含占位符格式化）。

        在请求上下文中调用（视图 / 异常处理器执行期）。
        """
        translated = _(self.value)
        if kwargs:
            try:
                translated = translated.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return translated


# Babel 抽取标记：下列 `_("...")` 仅用于让 pybabel extract 收集枚举原文 msgid，
# 运行时 `.t()` 会按 self.value 翻译。模块加载期调用 `_()` 安全（无请求时返回原文）。
_I18N_EXTRACT_MARKERS = [
    _("浏览器通知配置不存在"),
    _("浏览器ID不能为空~"),
    _("浏览器ID {browser_id} 不属于当前用户或不存在"),
    _("未登录，请提供有效的x-bili-mid请求头"),
    _("无效的用户ID，请重新登录"),
    _("Invalid mid format in x-bili-mid header"),
    _("插件ID不能为空"),
    _("插件ID {plugin_id} 不属于当前用户或不存在"),
    _("浏览器未启动或已停止"),
    _("页面索引 {page_index} 无效"),
    _("视频流初始化失败: {error}"),
    _("获取浏览器会话失败: {error}"),
    _("获取浏览器信息失败: {error}"),
    _("WebRTC 流未激活"),
    _("B站登录失败"),
    _("浏览器指纹不存在"),
    _("已达到最大指纹数量限制，当前等级最多可创建 {max} 个指纹"),
]


__all__ = ["ResponseMsg"]
