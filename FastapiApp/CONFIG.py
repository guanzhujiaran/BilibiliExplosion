import copy
import os
from dataclasses import dataclass
from enum import Enum, StrEnum
from fake_useragent import UserAgent
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import AsyncAdaptedQueuePool


class Settings(BaseSettings):
    MYSQL_HOST: str
    MYSQL_PORT: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PWD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    PUSHME_TOKEN: str
    PUSHPLUS_TOKEN: str
    UNIDBG_HOST: str
    UNIDBG_PORT: str
    V2RAY_HOST: str
    V2RAY_PORT: str
    LMSTUDIO_HOST: str  # lm studio 开个网络服务
    LMSTUDIO_PORT: str
    PROXY_SERVER: str
    model_config = SettingsConfigDict(env_file=(".env.fastapi.prod", ".env.fastapi.dev"))
    SHOW_LOG:int= 0

settings = Settings()


class PlaywrightUserDir(StrEnum):
    """
    枚举类，用于表示不同的用户数据目录
    """
    zhihu = "zhihu"


@dataclass
class ChatGptSettings:
    baseurl: str = "https://api.chatanywhere.tech/v1"
    open_ai_api_key: str = 'sk-mZDs5CvKYABSjV2QSOEHy8m5tSZh00uUEjXozezF8dNQHDpS'
    model_name: str = "gpt-3.5-turbo"


# region 基本配置
class pushme:
    _url = "https://push.i-i.me"
    _token = settings.PUSHME_TOKEN

    @property
    def url(self):
        return self._url

    @property
    def token(self):
        return self._token

    def set_url(self, url):
        self._url = url
        return self

    def set_token(self, token):
        self._token = token
        return self


class pushnotify:
    def __init__(self):
        self._pushme = pushme()
        self._pushplus = pushme().set_url('http://www.pushplus.plus/send').set_token(settings.PUSHPLUS_TOKEN)

    @property
    def pushme(self):
        return self._pushme

    @property
    def pushplus(self):
        return self._pushplus


class database:
    @dataclass
    class _MYSQL:
        _base_url: str = f'{settings.MYSQL_HOST}:{settings.MYSQL_PORT}'
        _pwd: str = settings.MYSQL_PASSWORD
        _user: str = settings.MYSQL_USER
        proxy_db_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/proxy_db?charset=utf8mb4&autocommit=true'
        bili_db_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/bilidb?charset=utf8mb4&autocommit=true'  # 话题抽奖
        bili_reserve_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/bili_reserve?charset=utf8mb4&autocommit=true'
        get_other_lot_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/biliopusdb?charset=utf8mb4&autocommit=true'
        dyn_detail_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/dyndetail?charset=utf8mb4&autocommit=true'
        sams_club_URI: str = f'mysql+aiomysql://{_user}:{_pwd}@{_base_url}/samsclub?charset=utf8mb4&autocommit=true'

    @dataclass
    class _REDISINFO:
        def __init__(self, db: int = 15):
            self.host: str = settings.REDIS_HOST
            self.port: str = settings.REDIS_PORT
            self.db: int = db
            self.pwd: str = settings.REDIS_PWD

        def toUrl(self):
            return f'redis://:{self.pwd}@{self.host}:{self.port}/{self.db}'

    MYSQL = _MYSQL()
    proxyRedis = _REDISINFO(15)
    proxySubRedis = _REDISINFO(6)
    lotDataRedisObj = _REDISINFO(2)
    ipInfoRedisObj = _REDISINFO(2)
    getOtherLotRedis = _REDISINFO(15)
    commStorageRedis = _REDISINFO(0)


class SqlAlchemyConfig:
    engine_config = dict(
        echo=False,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,  # 默认是5
        max_overflow=20,
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
        ipv6_change = 'ipv6_change'

    host = settings.RABBITMQ_HOST
    port = settings.RABBITMQ_PORT
    user = settings.RABBITMQ_USER
    pwd = settings.RABBITMQ_PASSWORD
    protocol = 'amqp'
    queue_name_list = [x.value for x in QueueName]
    broker_url = f"{protocol}://{user}:{pwd}@{host}:{port}/"


class _SeleniumConfig:
    edge_path = 'C:/WebDriver/bin/msedgedriver.exe'
    linux_edge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webDriver/linux/msedgedriver')


# endregion


class _CONFIG:
    root_dir = os.path.dirname(os.path.abspath(__file__))  # 代码的根目录
    V2ray_proxy = f'http://{settings.V2RAY_HOST}:{settings.V2RAY_PORT}'
    lm_studio_url = f'http://{settings.LMSTUDIO_HOST}:{settings.LMSTUDIO_PORT}'
    pushnotify = pushnotify()  # 推送设置
    database = database()
    local_llm_setting = ChatGptSettings(
        baseurl=f'{lm_studio_url}/v1',
        open_ai_api_key='114514',
        model_name='google/gemma-2-9b'
    )
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
        local_llm_setting
    ]
    my_ipv6_addr = settings.PROXY_SERVER
    unidbg_addr = f"http://{settings.UNIDBG_HOST}:{settings.UNIDBG_PORT}"
    RabbitMQConfig = RabbitMQConfig()
    selenium_config = _SeleniumConfig()
    sql_alchemy_config = SqlAlchemyConfig()
    playwright_user_dir = PlaywrightUserDir
    _pc_ua = UserAgent(platforms=["desktop", "tablet"])
    _mobile_ua = UserAgent(platforms=["mobile"])

    @property
    def rand_ua(self):
        return self._pc_ua.random

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
    print(settings)
