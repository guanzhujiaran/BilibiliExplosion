import copy
from dataclasses import dataclass
from enum import Enum

from fake_useragent import UserAgent


@dataclass
class DBINFO:
    DB_path: str
    DB_URI: str


@dataclass
class REDISINFO:
    host: str = '127.0.0.1'
    port: int = 11451
    db: int = 15


@dataclass
class ChatGptSettings:
    baseurl: str = "https://api.chatanywhere.tech/v1"
    open_ai_api_key: str = 'sk-mZDs5CvKYABSjV2QSOEHy8m5tSZh00uUEjXozezF8dNQHDpS'


@dataclass
class MYSQL:
    proxy_db_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/proxy_db?charset=utf8mb4&autocommit=true'
    bili_db_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/bilidb?charset=utf8mb4&autocommit=true'
    bili_reserve_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/bili_reserve?charset=utf8mb4&autocommit=true'
    get_other_lot_URI: str = 'mysql+aiomysql://root:114514@127.0.0.1:3306/BiliOpusDb?charset=utf8mb4&autocommit=true'


# region 基本配置
class pushme:
    _url = "https://push.i-i.me"
    _token = "T1cBRRgooZyhfIJMYPjR"

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
        push_template.set_token('044b3325295b47228409452e0e7aeef7')
        self._pushplus = copy.deepcopy(push_template)

    @property
    def pushme(self):
        return self._pushme

    @property
    def pushplus(self):
        return self._pushplus


class zhihu_CONFIG:
    root_dir = 'K:/zhihu/'


class database:
    dynDetail = "H:/database/dynDetail.db"
    proxy_db = "K:/sqlite_database/proxy_database/proxy_db.db"
    proxy_db_URI = 'sqlite+aiosqlite:///K:/sqlite_database/proxy_database/proxy_db.db?check_same_thread=False'
    followingup_db_RUI = 'sqlite+aiosqlite:///G:/database/Following_Usr.db?check_same_thread=False'  # 取关up数据库地址
    bili_live_monitor_db_URI = fr'sqlite:///H:\liveLotMonitorDB\Bili_live_database.db''?check_same_thread=False'  # b站直播数据库
    MYSQL = MYSQL()
    proxyRedis = REDISINFO()


class RabbitMQConfig:
    class QueueName(Enum):
        bili_352_voucher = 'bili_352_voucher'
        ipv6_change = 'ipv6_change'

    host = '127.0.0.1'
    port = 5672
    user = 'Xingtong'
    pwd = '114514'
    queue_name_list = [x.value for x in QueueName]
    broker_url = f"amqp://{user}:{pwd}@{host}:{port}/"


class ProjectPath(str, Enum):
    bili_live_monitor = "K:/Bili_live_monitor"
    toutiao = "K:/toutiao/pyProject"
    bili_lottery = 'K:/python test'
    py_test = 'K:/python测试专用'
    zhihu = 'K:/zhihu'
    grpc_api_proto = "K:/python test/grpc获取动态/grpc/grpc_proto"


class _SeleniumConfig:
    edge_path = 'C:/WebDriver/bin/msedgedriver.exe'


# endregion


class _CONFIG:
    root_dir = 'K:/python test/'  # b站代码的根目录
    V2ray_proxy = 'http://127.0.0.1:10809'  # socks端口+1
    project_path = ProjectPath
    pushnotify = pushnotify()  # 推送设置
    zhihu_CONFIG = zhihu_CONFIG()  # 知乎设置
    database = database()
    chat_gpt_configs = [
        ChatGptSettings(
            baseurl="https://api.chatanywhere.tech/v1",
            open_ai_api_key='sk-mZDs5CvKYABSjV2QSOEHy8m5tSZh00uUEjXozezF8dNQHDpS'
        ),
        ChatGptSettings(
            baseurl="https://api.chatanywhere.tech/v1",
            open_ai_api_key='sk-15uefwaxlC3ik3Rzc6olDUUJ9pzDl8fFiesHJvTEXdz66Gba'
        ),
        ChatGptSettings(
            baseurl='https://happyapi.org/v1',
            open_ai_api_key='sk-B0JwJwpkzqhlwh3qC2638d73De5042C3Aa02951313Bd1e39'
        ),
        ChatGptSettings(
            baseurl='https://happyapi.org/v1',
            open_ai_api_key='sk-rooVNOUA9Xs2AqtpE9445cC879F3467b9f6a97B6De2219C1'
        ),
        ChatGptSettings(
            baseurl='https://api.openai-hk.com/v1',
            open_ai_api_key='hk-reurs910000380223c324e435ac8ef84f5d0a75f22a4e6c0'
        ),
        ChatGptSettings(
            baseurl='https://api.openai-hk.com/v1',
            open_ai_api_key='hk-wb59m7100003926553e7b82535bb9ea57b67d97626838c25'
        ),
    ]
    my_ipv6_addr = 'http://192.168.1.201:3128'
    # my_ipv6_addr = 'http://127.0.0.1:1919'
    # my_ipv6_addr=None
    RabbitMQConfig = RabbitMQConfig()
    selenium_config = _SeleniumConfig()

    _pc_ua = UserAgent(platforms=["pc", "tablet"])
    _mobile_ua = UserAgent(platforms=["mobile"])

    @property
    def rand_ua(self):
        return CONFIG._pc_ua.random

    @property
    def rand_ua_mobile(self):
        return self._mobile_ua.random


CONFIG = _CONFIG()
