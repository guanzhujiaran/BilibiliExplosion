import os
import uuid
from enum import Enum
from loguru import logger
from loguru._logger import Logger
from CONFIG import CONFIG


class UserMap(Enum):
    samsclub_logger = "samsclub_logger"
    httpx = "httpx"
    background_task = 'background_task'
    live_monitor_logger = "live_monitor_logger"
    request_with_proxy_logger = "request_with_proxy_logger"
    pushme_logger = "pushme"
    reserve_lot_logger = "预约抽奖"
    official_lot_logger = "官方抽奖"
    topic_lot_logger = "话题抽奖"

    Voucher352_logger = "Voucher352_logger"
    get_rm_following_list_logger = "获取取关对象列表日志"
    space_monitor_logger = "space_monitor"
    bapi_log = "BAPI日志"
    fastapi = "fastapi"
    MQ_logger = "MQ_logger"
    redis_logger = "redis_logger"
    get_others_lot_logger = "get_others_lot_logger"
    MysqlProxy = "MysqlProxy"

    BiliGrpcClient_logger = "BiliGrpcClient_logger"
    BiliGrpcUtils_logger = "BiliGrpcUtils_logger"
    BiliGrpcApi_logger = "BiliGrpcApi_logger"

    zhihu_api_logger = "zhihu_api_logger"
    toutiao_api_logger = "toutiao_api_logger"
    ipv6_monitor_logger = "ipv6_monitor_logger"
    activeExclimbWuzhi_logger = "激活cookie日志"

    milvus_db_logger = "milvus_db_logger"


def create_logger(user: UserMap) -> Logger:
    user_uq_value = uuid.uuid4().hex + user.value
    _user_logger = logger.bind(user=user_uq_value)
    _user_logger.add(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"../scripts/log/error_{user.value}_log.log"),
        level="WARNING",
        encoding="utf-8",
        enqueue=True,
        rotation="500MB",
        compression="zip",
        retention="15 days",
        filter=lambda record: record["extra"].get('user') == user_uq_value,

    )
    return _user_logger


sql_log = create_logger(UserMap.MysqlProxy)
myfastapi_logger = create_logger(UserMap.fastapi)
MQ_logger = create_logger(UserMap.MQ_logger)
redis_logger = create_logger(UserMap.redis_logger)
get_others_lot_logger = create_logger(UserMap.get_others_lot_logger)

BiliGrpcClient_logger = create_logger(UserMap.BiliGrpcClient_logger)
BiliGrpcApi_logger = create_logger(UserMap.BiliGrpcApi_logger)
BiliGrpcUtils_logger = create_logger(UserMap.BiliGrpcUtils_logger)

zhihu_api_logger = create_logger(UserMap.zhihu_api_logger)
toutiao_api_logger = create_logger(UserMap.toutiao_api_logger)
ipv6_monitor_logger = create_logger(UserMap.ipv6_monitor_logger)
live_monitor_logger = create_logger(UserMap.live_monitor_logger)
bapi_log = create_logger(UserMap.bapi_log)
activeExclimbWuzhi_logger = create_logger(UserMap.activeExclimbWuzhi_logger)
space_monitor_logger = create_logger(UserMap.space_monitor_logger)
get_rm_following_list_logger = create_logger(UserMap.get_rm_following_list_logger)
Voucher352_logger = create_logger(UserMap.Voucher352_logger)

topic_lot_logger = create_logger(UserMap.topic_lot_logger)
official_lot_logger = create_logger(UserMap.official_lot_logger)
reserve_lot_logger = create_logger(UserMap.reserve_lot_logger)
milvus_db_logger = create_logger(UserMap.milvus_db_logger)
sams_club_logger = create_logger(UserMap.samsclub_logger)

pushme_logger = create_logger(UserMap.pushme_logger)
request_with_proxy_logger = create_logger(UserMap.request_with_proxy_logger)
background_task_logger = create_logger(UserMap.background_task)

httpx_logger = create_logger(UserMap.httpx)
