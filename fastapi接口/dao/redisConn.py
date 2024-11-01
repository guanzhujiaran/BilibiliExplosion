import redis
from CONFIG import CONFIG

__reids_port = CONFIG.database.proxyRedis.port
__reids_host = CONFIG.database.proxyRedis.host
r = redis.Redis(host=__reids_host, port=__reids_port, db=0)  # 直播抽奖数据
r1 = redis.Redis(host=__reids_host, port=__reids_port, db=1)  # 情感分析数据
