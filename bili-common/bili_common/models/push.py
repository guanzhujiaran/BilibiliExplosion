"""「推送」消息队列载体（公共定义，供 RPA-Browser 与 be-message-service 复用）。

RPA-Browser 通过 RabbitMQ 投递「站外推送」消息时，使用本模型构造 payload，
be-message-service 的消费者 `consume_message` 也用本模型反序列化，保证两端契约一致。

统一使用 SQLModel；所有字段均为字符串/可空对象，不涉及 JS 精度问题。
"""



from sqlmodel import SQLModel, Field


class PushChannelConfig(SQLModel):
    """推送渠道配置模型（消息系统「推送」模块的渠道配置）。

    字段与 RPA-Browser / FastapiApp 的 PushChannelConfig 保持一致，以便直接接收
    它们序列化后的 per-user 配置。未知字段一律忽略。
    """

    model_config = {"extra": "ignore"}

    # 一言（随机句子）
    hitokoto: bool = True

    # Bark
    bark_push: str = ""
    bark_archive: str = ""
    bark_group: str = ""
    bark_sound: str = ""
    bark_icon: str = ""
    bark_level: str = ""
    bark_url: str = ""

    # 钉钉机器人
    dd_bot_secret: str = ""
    dd_bot_token: str = ""

    # 飞书机器人
    fskey: str = ""

    # go-cqhttp
    gobot_url: str = ""
    gobot_qq: str = ""
    gobot_token: str = ""

    # Gotify
    gotify_url: str = ""
    gotify_token: str = ""
    gotify_priority: int = 0

    # iGot
    igot_push_key: str = ""

    # Server 酱
    push_key: str = ""

    # PushDeer
    deer_key: str = ""
    deer_url: str = ""

    # Synology Chat
    chat_url: str = ""
    chat_token: str = ""

    # PushPlus
    push_plus_token: str = ""
    push_plus_url: str = ""
    push_plus_user: str = ""
    push_plus_template: str = "html"
    push_plus_channel: str = "wechat"
    push_plus_webhook: str = ""
    push_plus_callbackurl: str = ""
    push_plus_to: str = ""

    # 微加机器人
    we_plus_bot_token: str = ""
    we_plus_bot_receiver: str = ""
    we_plus_bot_version: str = "pro"

    # Qmsg 酱
    qmsg_key: str = ""
    qmsg_type: str = ""

    # 企业微信
    qywx_origin: str = ""
    qywx_am: str = ""
    qywx_key: str = ""

    # Telegram
    tg_bot_token: str = ""
    tg_user_id: str = ""
    tg_api_host: str = ""
    tg_proxy_auth: str = ""
    tg_proxy_host: str = ""
    tg_proxy_port: str = ""

    # 智能微秘书
    aibotk_key: str = ""
    aibotk_type: str = ""
    aibotk_name: str = ""

    # SMTP 邮件
    smtp_server: str = ""
    smtp_ssl: str = "false"
    smtp_email: str = ""
    smtp_password: str = ""
    smtp_name: str = ""

    # PushMe
    pushme_key: str = ""
    pushme_url: str = ""

    # Chronocat
    chronocat_qq: str = ""
    chronocat_token: str = ""
    chronocat_url: str = ""

    # 自定义 Webhook
    webhook_url: str = ""
    webhook_body: str = ""
    webhook_headers: str = ""
    webhook_method: str = ""
    webhook_content_type: str = ""

    # Ntfy
    ntfy_url: str = ""
    ntfy_topic: str = ""
    ntfy_priority: str = "3"
    ntfy_token: str = ""
    ntfy_username: str = ""
    ntfy_password: str = ""
    ntfy_actions: str = ""

    # WxPusher
    wxpusher_app_token: str = ""
    wxpusher_topic_ids: str = ""
    wxpusher_uids: str = ""


class PushMessagePayload(SQLModel):
    """消息队列（RabbitMQ）中「推送」消息的专用载体。

    RPA-Browser 投递与 be-message-service 消费共用本模型，保证契约一致。
    """

    title: str
    content: str
    # pushme/pushplus 的模板类型，例如 text/markdown/html/json 等
    push_type: str | None = "text"
    # 渠道配置；为空时回落到 message-service 的全局环境变量配置
    config: PushChannelConfig | None = None


__all__ = ["PushChannelConfig", "PushMessagePayload"]
