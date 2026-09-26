"""各微服务共享的「推送 / 服务标识」配置片段。

历史问题：`PushChannelConfig` 与「全局推送渠道配置 + 服务标识」这几项在
`RPA-Browser/app/config.py`、`be-bilibili-crawler/CONFIG.py` 各复制了一份，
字段增删极易漂移（渠道配置副本还是 `BaseModel`，与 bili_common 的 `SQLModel`
版本并存）。这里把**共用部分**收敛到一处：

- 渠道配置模型统一用 :class:`bili_common.models.push.PushChannelConfig`（单一来源）；
- 共用设置项以 :class:`PushNotifySettingsMixin` 提供给各服务 `Settings` 混入。

用法（**mixin 必须排在 `BaseSettings` 之前**，pydantic 才会把基类注解收成字段；
环境变量 / ``env_file`` 的覆盖行为与直接写在 `Settings` 里完全一致）::

    from pydantic_settings import BaseSettings
    from bili_common.core.push_settings import PushNotifySettingsMixin

    class Settings(PushNotifySettingsMixin, BaseSettings):
        # 服务各自的差异默认值在自己的类体里覆盖
        SERVER_NAME: str = "rpa-browser"
        rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/?heartbeat=180"

    settings = Settings()
"""

import socket

from pydantic import BaseModel

from bili_common.models.push import PushChannelConfig

# 服务名的最后兜底：环境变量把 SERVER_NAME 置空（配置模板里常见 ``SERVER_NAME=``）
# 且当前 Settings 也没有声明服务名时使用。
_UNKNOWN_SERVER_NAME = "unknown-service"


class PushNotifySettingsMixin(BaseModel):
    """推送 / 服务标识相关的共用配置片段（供 pydantic-settings 的 `Settings` 混入）。

    字段全部可用同名环境变量覆盖（pydantic-settings 大小写不敏感）。
    """

    # 全局推送渠道配置：单个 JSON 环境变量 MESSAGE_CONFIG，与 be-message-service /
    # RPA-Browser / be-bilibili-crawler 共用同一份，作为无 per-user 配置时的兜底；
    # 由 pydantic-settings 自动解析 JSON，无需 Json() 包装。
    message_config: PushChannelConfig = PushChannelConfig()

    # 本服务标识（写入推送告警标题 ``[服务名@地址]``，便于定位「哪台服务器的哪个服务」报错）。
    # 名称由各服务在自己的 Settings 里给出默认值；地址缺省自动取本机 hostname。
    SERVER_NAME: str = ""
    SERVER_ADDRESS: str = ""

    # 一言（随机句子）接口，供推送内容点缀使用。
    hitokoto_api_url: str = "https://v1.hitokoto.cn"

    # pushme / pushplus 渠道默认端点：渠道配置未显式给出 URL 时使用。
    pushme_url: str = "https://push.i-i.me"
    pushplus_url: str = "http://www.pushplus.plus/send"

    # RabbitMQ 连接串（单一 URL 形式的服务使用，默认值即 docker-compose 内部服务名）。
    # heartbeat=180：与服务端保持一致，避免 handler 执行时间较长时 heartbeat 超时导致连接关闭。
    # 按 host/port/user/password 自行拼连接串的服务（be-bilibili-crawler）保留自己的字段，
    # 不读取本项。
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/?heartbeat=180"


def build_server_label(settings: PushNotifySettingsMixin) -> str:
    """返回推送标题用的服务标识前缀，例如 ``[rpa-browser@10.0.0.5]``。

    所有推送标题都会带上它，便于在告警中区分「是哪台服务器的哪个服务」报错。
    历史实现把同一段逻辑抄在每个服务的推送模块里（只有服务名兜底不同），现统一到本函数：

    - 服务名取 ``settings.SERVER_NAME``；被环境变量覆盖成空串时，回落该类**字段声明的
      默认值**（即各服务 ``Settings`` 里写的服务名，如 ``"rpa-browser"``），最后才用
      ``unknown-service`` 兜底；
    - 地址取 ``settings.SERVER_ADDRESS``，缺省自动取本机 hostname。

    各服务只需保留一个零参包装（沿用原有函数名，历史调用点零改动）调用本函数即可。
    """
    declared_name = type(settings).model_fields["SERVER_NAME"].default or ""
    name = settings.SERVER_NAME or declared_name or _UNKNOWN_SERVER_NAME
    addr = settings.SERVER_ADDRESS or socket.gethostname()
    return f"[{name}@{addr}]"


__all__ = ["PushNotifySettingsMixin", "build_server_label"]
