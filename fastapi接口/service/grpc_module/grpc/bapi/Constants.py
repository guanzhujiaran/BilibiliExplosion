# constants.py

# 异常代码，需要重试的
BLACK_CODE_LIST = [-412, -352]

# Cookie相关常量
BASE_COOKIE_KEYS = [
    "buvid3",
    "b_nut",
    "b_lsid",
    "_uuid",
    "hit-dyn-v2"
]
EXCLIMB_WUZHI_COOKIE_KEYS = [
    'buvid3',
    'b_nut',
    'buvid4',
    'b_lsid',
    'buvid_fp',
    '_uuid',
    'enable_web_push',
    'home_feed_column',
    'browser_resolution',
    'bili_ticket',
    'bili_ticket_expires'
]
COMMON_COOKIE_KEYS = [
    'buvid3',
    'b_nut',
    'b_lsid',
    '_uuid',
    'enable_web_push',
    'home_feed_column',
    'browser_resolution',
    'buvid4',
    'bili_ticket',
    'bili_ticket_expires',
    'buvid_fp'
]

# APP签名密钥
APP_KEY = "1d8b6e7d45233436"
APP_SEC = "560c52ccd288fed045859ed18bffd973"

# API URLs
URL_GET_WEB_AREA_LIST = "https://api.live.bilibili.com/xlive/web-interface/v1/index/getWebAreaList?source_id=2"
URL_ABTEST_ABSERVER = "https://app.bilibili.com/x/resource/abtest/abserver"
URL_VALIDATE_GEETEST = "https://api.bilibili.com/x/gaia-vgate/v1/validate"
URL_REGISTER_GEETEST = "https://api.bilibili.com/x/gaia-vgate/v1/register"
URL_DYNAMIC_DETAIL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail"
URL_GAIA_GET_AXE = "https://api.bilibili.com/x/internal/gaia-gateway/ExGetAxe?web_location=333.1007"
URL_GAIA_EXCLIMB_WUZHI = "https://api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi"
URL_GEN_WEB_TICKET = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
URL_FRONTEND_FINGER_SPI = "https://api.bilibili.com/x/frontend/finger/spi"
URL_BILI_MAIN_PAGE = "https://www.bilibili.com/"
URL_SPACE_DYNAMIC = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
URL_RESERVE_RELATION_INFO = "https://api.bilibili.com/x/activity/up/reserve/relation/info"
URL_LOTTERY_NOTICE = "https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice"
URL_GET_WEB_TOPIC = "https://app.bilibili.com/x/topic/web/details/top"
URL_REPLY_MAIN = "https://api.bilibili.com/x/v2/reply/main"
URL_LATEST_VERSION = "https://app.bilibili.com/x/v2/version"