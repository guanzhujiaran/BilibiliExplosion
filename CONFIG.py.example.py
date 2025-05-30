import copy
from dataclasses import dataclass
from enum import Enum
from fake_useragent import UserAgent
from sqlalchemy import AsyncAdaptedQueuePool


@dataclass
class DBINFO:
    DB_path: str
    DB_URI: str


@dataclass
class ChatGptSettings:
    baseurl: str = "https://api.chatanywhere.tech/v1"
    open_ai_api_key: str = 'sk-xxx'


# region 基本配置
class pushme:
    _url = "https://push.i-i.me"
    _token = "xxx"

    @property
    def url(self):
        return self._url

    @property
    def token(self):
        return self._token

    def set_url(self, url):
        self._url = url

    def set_token(self, token):
        self._token = token


class pushnotify:
    def __init__(self):
        push_template = pushme()
        self._pushme = copy.deepcopy(push_template)
        push_template.set_url('http://www.pushplus.plus/send')
        push_template.set_token('xxx')
        self._pushplus = copy.deepcopy(push_template)

    @property
    def pushme(self):
        return self._pushme

    @property
    def pushplus(self):
        return self._pushplus

class database:
    @dataclass
    class _MYSQL:
        proxy_db_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/proxy_db?charset=utf8mb4&autocommit=true'
        bili_db_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/bilidb?charset=utf8mb4&autocommit=true'  # 话题抽奖
        bili_reserve_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/bili_reserve?charset=utf8mb4&autocommit=true'
        get_other_lot_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/BiliOpusDb?charset=utf8mb4&autocommit=true'
        dyn_detail: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/dynDetail?charset=utf8mb4&autocommit=true'
        sams_club_URI:str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/samsClub?charset=utf8mb4&autocommit=true'

    @dataclass
    class _REDISINFO:
        def __init__(self, db: int = 15):
            self.host: str = '127.0.0.1'
            self.port: int = 11451
            self.db: int = db

    dynDetail = "H:/database/dynDetail.db"
    proxy_db = "K:/sqlite_database/proxy_database/proxy_db.db"
    proxy_db_URI = 'sqlite+aiosqlite:///K:/sqlite_database/proxy_database/proxy_db.db?check_same_thread=False'
    followingup_db_RUI = 'sqlite+aiosqlite:///G:/database/Following_Usr.db?check_same_thread=False'  # 取关up数据库地址
    bili_live_monitor_db_URI = fr'sqlite:///H:\liveLotMonitorDB\Bili_live_database.db''?check_same_thread=False'  # b站直播数据库
    aiobili_live_monitor_db_URI = fr'sqlite+aiosqlite:///H:\liveLotMonitorDB\Bili_live_database.db''?check_same_thread=False'
    MYSQL = _MYSQL()
    proxyRedis = _REDISINFO(15)
    proxySubRedis = _REDISINFO(6)
    lotDataRedisObj = _REDISINFO(2)
    ipInfoRedisObj = _REDISINFO(2)
    getOtherLotRedis = _REDISINFO(15)


class SqlAlchemyConfig:
    engine_config = dict(
        echo=False,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=500,  # 默认是5
        max_overflow=100,
        pool_recycle=True,
        pool_timeout=30,
        future=True,
        pool_pre_ping=True,
    )
    session_config = dict(
        expire_on_commit=False,
    )


class RabbitMQConfig:
    class QueueName(Enum):
        bili_352_voucher = 'bili_352_voucher'
        ipv6_change = 'ipv6_change'

    host = '127.0.0.1'
    port = 5672
    user = 'Xingtong'
    pwd = '114514'
    protocol = 'amqp'
    queue_name_list = [x.value for x in QueueName]
    broker_url = f"{protocol}://{user}:{pwd}@{host}:{port}/"


class _SeleniumConfig:
    edge_path = 'C:/WebDriver/bin/msedgedriver.exe'


# endregion


class _CONFIG:
    root_dir = 'K:/python test/'  # b站代码的根目录
    V2ray_proxy = 'http://127.0.0.1:10809'  # socks端口+1
    pushnotify = pushnotify()  # 推送设置
    database = database()
    chat_gpt_configs = [
        ChatGptSettings(
            baseurl="https://api.chatanywhere.tech/v1",
            open_ai_api_key='sk-xxx'
        )
    ]
    my_ipv6_addr = 'http://192.168.1.201:3128'
    # my_ipv6_addr = 'http://127.0.0.1:8080'
    unidbg_addr = "http://127.0.0.1:23335"
    RabbitMQConfig = RabbitMQConfig()
    selenium_config = _SeleniumConfig()
    sql_alchemy_config = SqlAlchemyConfig()

    _pc_ua = UserAgent(platforms=["pc", "tablet"])
    _mobile_ua = UserAgent(platforms=["mobile"])

    @property
    def rand_ua(self):
        return CONFIG._pc_ua.random

    @property
    def rand_ua_mobile(self):
        return self._mobile_ua.random

    @property
    def custom_proxy(self):
        return {'http': self.my_ipv6_addr, 'https': self.my_ipv6_addr}

    @property
    def custom_v2ray_proxy(self):
        return {'http': self.V2ray_proxy, 'https': self.V2ray_proxy}


CONFIG = _CONFIG()

if __name__ == "__main__":
    print(CONFIG.rand_ua)