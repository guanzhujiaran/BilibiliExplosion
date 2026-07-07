import os
from dataclasses import dataclass
from enum import Enum, StrEnum
from fake_useragent import UserAgent
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import AsyncAdaptedQueuePool

_current_dir = os.path.dirname(os.path.abspath(__file__))


class GetOthersLotDynConfig(BaseModel):
    """第三方抽奖动态获取配置 —— 作为 Settings 的嵌套子模型，
    部署时可整个对象填 JSON，也可逐字段用双下划线覆盖。
    例如：get_others_lot='{"space_dyn_concurrency":3}'
    或：  get_others_lot__space_dyn_concurrency=3
    """
    space_dyn_concurrency: int = 1     # 空间动态并发数
    judge_dyn_concurrency: int = 1     # 抽奖判定并发数
    spare_time: int = 86400 * 7            # 多久以前的动态不再获取(秒)，默认7天
    get_dyn_interval: int = 86400 * 2      # 两次完整采集的最小间隔(秒)，默认2天
    dyn_time_limit: int = 1728000      # 返回数据的时间范围(秒)，默认20天
    max_user_list_size: int = 20       # 用户列表最大长度
    remove_check_days: int = 14        # 剔除用户时检查最近N天内的抽奖数
    min_valid_lot_threshold: int = 10  # 低于此阈值的用户将被剔除
    hot_lot_dyn_count: int = 5        # 从评论区挖掘用户时选取的高互动动态数量
    hot_lot_dyn_days: int = 7         # 高互动动态的时间范围(天)
    # 用户列表为空且无法从评论区补充时使用的默认用户 uid 列表
    default_user_uids: list[int] = [
        319857159, 14017844, 1234306704, 31497476, 2147319744,
        410550169, 646686238, 71583520, 279262754, 275744172,
        332793152, 1397970246, 3493092200024392, 386051299, 381282283,
        20958956, 1869690859, 1183157743, 4586734, 1741486871,
        266223923, 646327721, 1803790683, 8544035, 1123570168,
        3494361237031878, 223712517, 480906586, 1040677577, 471565816,
        343104186, 2204166, 290089137, 1855888816, 691536906,
        6477408, 1586295950, 1369967146, 40809204, 1992326018,
        649407876, 256316789, 143412922, 1278208248, 499023056,
        565064296, 693445761, 7538278,
    ]


class LLMApiConfig(BaseModel):
    """OpenAI 兼容 API 配置 —— 作为 Settings 的嵌套子模型列表元素，
    部署时可整个列表填 JSON，也可逐字段用双下划线覆盖。
    例如：llm_apis='[{"base_url":"https://...","model_name":"gpt-3.5","token":"sk-xxx"}]'
    或：  llm_apis__0__base_url=https://...  llm_apis__0__model_name=gpt-3.5
    """
    base_url: str = ""
    model_name: str = ""
    token: str = ""


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
    MILVUS_HOST: str
    MILVUS_PORT: str

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(_current_dir, ".env.fastapi.prod"),
            os.path.join(_current_dir, ".env.fastapi.dev"),
        )
    )
    SHOW_LOG: int = 0
    IS_DEV: int = 1  # 默认开发环境

    # ===== 第三方抽奖动态获取 =====
    get_others_lot: GetOthersLotDynConfig = GetOthersLotDynConfig()

    OLLAMA_ENDPOINT: str = "http://ollama:11434"

    # 外部 LLM API 列表（按顺序优先使用，全部失败后回退到本地 Ollama）
    llm_apis: list[LLMApiConfig] = []


settings = Settings()


class PlaywrightUserDir(StrEnum):
    """
    枚举类，用于表示不同的用户数据目录
    """

    zhihu = "zhihu"


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
        self._pushplus = (
            pushme()
            .set_url("http://www.pushplus.plus/send")
            .set_token(settings.PUSHPLUS_TOKEN)
        )

    @property
    def pushme(self):
        return self._pushme

    @property
    def pushplus(self):
        return self._pushplus


class DataBaseConfig:
    @dataclass
    class _MYSQL:
        _base_url: str = f"{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
        _pwd: str = settings.MYSQL_PASSWORD
        _user: str = settings.MYSQL_USER
        proxy_db_URI: str = (
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/proxy_db?charset=utf8mb4&autocommit=true"
        )
        bili_db_URI: str = (
            # 话题抽奖
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/bilidb?charset=utf8mb4&autocommit=true"
        )
        bili_reserve_URI: str = (
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/bili_reserve?charset=utf8mb4&autocommit=true"
        )
        get_other_lot_URI: str = (
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/biliopusdb?charset=utf8mb4&autocommit=true"
        )
        dyn_detail_URI: str = (
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/dyndetail?charset=utf8mb4&autocommit=true"
        )
        sams_club_URI: str = (
            f"mysql+aiomysql://{_user}:{_pwd}@{_base_url}/samsclub?charset=utf8mb4&autocommit=true"
        )

    @dataclass
    class _REDISINFO:
        def __init__(self, db: int = 15):
            self.host: str = settings.REDIS_HOST
            self.port: str = settings.REDIS_PORT
            self.db: int = db
            self.pwd: str = settings.REDIS_PWD

        def toUrl(self):
            return f"redis://:{self.pwd}@{self.host}:{self.port}/{self.db}"

    MYSQL = _MYSQL()
    proxyRedis = _REDISINFO(15)
    proxySubRedis = _REDISINFO(6)
    lotDataRedisObj = _REDISINFO(2)
    ipInfoRedisObj = _REDISINFO(2)
    getOtherLotRedis = _REDISINFO(15)
    commStorageRedis = _REDISINFO(0)
    rabbitmqCacheRedis = _REDISINFO(0)


class SqlAlchemyConfig:
    # 业务连接池配置 - 供 router/service 等业务使用，保留足够的连接处理外部请求
    engine_config = dict(
        echo=False,
        pool_size=100,
        max_overflow=40,
        pool_use_lifo=True,
    )
    session_config = dict(
        expire_on_commit=False,
        autoflush=False,
    )


class CrawlerSqlAlchemyConfig:
    """
    爬虫专用连接池配置 - 与业务连接池完全隔离
    即使爬虫并发高占用大量连接，也不会影响业务请求
    池子大小与业务池相同，但使用独立的连接池实例
    """
    engine_config = dict(
        echo=False,
        pool_size=100,  # 与业务池大小相同，独立使用
        max_overflow=40,
        pool_use_lifo=True,
    )
    session_config = dict(
        expire_on_commit=False,
        autoflush=False,
    )


class RabbitMQConfig:
    class QueueName(Enum):
        ipv6_change = "ipv6_change"

    host = settings.RABBITMQ_HOST
    port = settings.RABBITMQ_PORT
    user = settings.RABBITMQ_USER
    pwd = settings.RABBITMQ_PASSWORD
    protocol = "amqp"
    queue_name_list = [x.value for x in QueueName]
    broker_url = f"{protocol}://{user}:{pwd}@{host}:{port}/?heartbeat=180"



# endregion


class _CONFIG:
    root_dir = os.path.dirname(os.path.abspath(__file__))  # 代码的根目录
    V2ray_proxy = f"http://{settings.V2RAY_HOST}:{settings.V2RAY_PORT}"
    lm_studio_url = f"http://{settings.LMSTUDIO_HOST}:{settings.LMSTUDIO_PORT}"
    pushnotify = pushnotify()  # 推送设置
    database = DataBaseConfig()
    my_ipv6_addr = settings.PROXY_SERVER
    unidbg_addr = f"http://{settings.UNIDBG_HOST}:{settings.UNIDBG_PORT}"
    RabbitMQConfig = RabbitMQConfig()
    sql_alchemy_config = SqlAlchemyConfig()
    crawler_sql_alchemy_config = CrawlerSqlAlchemyConfig()
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
        return {"http": self.my_ipv6_addr, "https": self.my_ipv6_addr}

    @property
    def custom_v2ray_proxy(self):
        return {"http": self.V2ray_proxy, "https": self.V2ray_proxy}


CONFIG = _CONFIG()

if __name__ == "__main__":
    print(settings)
