"""
Response Code 模块 - 统一响应码定义（单一来源）
"""

from bili_common.core.enums import IntEnumAutoDoc


class ResponseCode(IntEnumAutoDoc):
    """
    统一响应码枚举类
    """
    # 成功
    SUCCESS = 0

    # 未登录：采用 B 站官方约定业务码 -101。
    # 契约：业务状态一律由 body 的 `code` 表达；HTTP 状态码只表达 HTTP 层语义。
    # -101 由 http_status_for_code() 映射为 401，前端同时也按 `code == -101` 判定，
    # 两者互为兜底。完整设计见 docs/response-code-design.md。
    NOT_LOGGED_IN = -101

    # 通用错误码
    BAD_REQUEST = 400
    INVALID_PARAM = 400  # 请求参数非法（与 BAD_REQUEST 同值，语义区分）
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    TOO_MANY_REQUESTS = 429

    # 服务器错误
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

    # 自定义业务错误码
    BUSINESS_ERROR = 1000
    VALIDATION_ERROR = 1001
    DATABASE_ERROR = 1002
    NETWORK_ERROR = 1003
    MID_NOT_FOUND = 1004
    BROWSER_ID_NOT_FOUND = 1005
    SESSION_NOT_FOUND = 1006
    BROWSER_NOT_STARTED = 1007
    USER_NOT_FOUND = 1008  # 目标用户不存在（空间资料等单用户读接口返回，替代空列表/0/404 兜底）

    # 资源冲突 / 缺失（RPA-Browser：名称冲突、通知配置、被引用的动作）
    # 注意：这些是「业务语义」而非 HTTP 语义，一律映射 HTTP 200，业务由 body.code 表达，
    # 以便前端读到 msg 做精准提示（详见 docs/response-code-design.md）。
    NAME_ALREADY_EXISTS = 1009  # 同名资源冲突（工作流 / 插件 / 动作重名，需引导改名）
    BROWSER_NOTIFY_CONF_NOT_FOUND = 1010  # 浏览器通知配置不存在（命令类删除场景）
    ACTION_NOT_FOUND = 1011  # 引用的自定义操作不存在

    # WebRTC 相关错误码
    WEBRTC_OFFER_FAILED = 2001
    WEBRTC_ANSWER_FAILED = 2002
    WEBRTC_ICE_CANDIDATE_FAILED = 2003
    WEBRTC_CLOSE_FAILED = 2004
    WEBRTC_CONNECTION_FAILED = 2005
    WEBRTC_STATUS_FAILED = 2006
    WEBRTC_STREAM_NOT_ACTIVE = 2009

    # 页面状态错误码
    # 注意：PAGE_CLOSED 与 SCREENSHOT_FAILED 曾共用 2007（两义歧义），现已拆分：
    # PAGE_CLOSED 保留 2007（前置状态不满足），截图失败归入下方浏览器/页面操作失败族。
    PAGE_CLOSED = 2007

    # 指纹数量限制错误码
    FINGERPRINT_LIMIT_EXCEEDED = 2008

    # 浏览器/页面相关错误码
    GET_BROWSER_INFO_FAILED = 2010
    PAGE_NAVIGATION_FAILED = 2011
    SCREENSHOT_FAILED = 2012  # 截图失败（操作失败；原与 PAGE_CLOSED 共用 2007）

    # 浏览器启动内存准入 / 排队（RPA-Browser：内存不足时按 VIP / 普通双队列排队）
    BROWSER_LAUNCH_MEMORY_INSUFFICIENT = 2013  # 内存不足，启动请求已进入排队
    BROWSER_LAUNCH_QUEUE_TIMEOUT = 2014  # 排队等待超时（内存长时间未释放）
    BROWSER_LAUNCH_QUEUE_CANCELLED = 2015  # 排队被取消（用户关闭 / 主动取消）

    # 执行期互斥（RPA-Browser：工作流运行中禁止调试类接口，直播不受影响，见计划书 §5.17）
    BROWSER_WORKFLOW_RUNNING = 2016  # 浏览器正在执行工作流，调试类接口暂不可用

    # Casdoor OAuth 相关错误码
    CASDOOR_OAUTH_ERROR = 3001       # Casdoor 返回错误（如 code 过期、invalid_grant）
    CASDOOR_ENDPOINT_NOT_CONFIGURED = 3002  # Casdoor endpoint 未配置
    CASDOOR_TOKEN_PARSE_FAILED = 3003  # JWT 解析失败
    CASDOOR_USER_NOT_FOUND = 3004     # Casdoor 用户不存在
    CASDOOR_CREATE_USER_FAILED = 3005  # 创建本地用户失败

    # 消息（私信）发送限制错误码（2.57.0，be-message 私信发送拦截）
    DM_SEND_DAILY_LIMIT = 4001        # 单用户当天发送私信达到每日上限（dm_daily_send_limit）
    DM_SEND_STRANGER_LIMIT = 4002     # 对方未关注且未回过消息时，陌生人单条额度已用尽

    # 内容发布每日上限错误码（2.58.0，评论 / 动态 / 话题创建拦截）
    COMMENT_DAILY_CREATE_LIMIT = 4101  # 单用户当天评论创建达到每日上限（comment_daily_create_limit）
    MOMENT_DAILY_CREATE_LIMIT = 4102   # 单用户当天动态(WORD)创建达到每日上限（moment_daily_create_limit）
    TOPIC_DAILY_CREATE_LIMIT = 4103    # 单用户当天话题创建达到每日上限（topic_daily_create_limit）


__all__ = ["ResponseCode"]
