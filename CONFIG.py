import copy

from dataclasses import dataclass


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
        self._url= url

    def set_token(self, token):
        self._token = token


class pushnotify:
    def __init__(self):
        push_template = pushme()
        self._pushme = copy.deepcopy(push_template)
        push_template.set_url( 'http://www.pushplus.plus/send')
        push_template.set_token(  '044b3325295b47228409452e0e7aeef7')
        self._pushplus = copy.deepcopy(push_template)

    @property
    def pushme(self):
        return self._pushme

    @property
    def pushplus(self):
        return self._pushplus


class zhihu_CONFIG:
    root_dir = 'K:/zhihu/'


@dataclass
class MYSQL:
    proxy_db_URI: str = 'mysql+aiomysql://root:114514@localhost:3306/proxy_db?charset=utf8mb4&autocommit=true'


@dataclass
class DBINFO:
    DB_path: str
    DB_URI: str


@dataclass
class REDISINFO:
    host: str = 'localhost'
    port: int = 11451
    db: int = 15


class database:
    dynDetail = "H:/database/dynDetail.db"
    proxy_db = "K:/sqlite_database/proxy_database/proxy_db.db"
    proxy_db_URI = 'sqlite+aiosqlite:///K:/sqlite_database/proxy_database/proxy_db.db?check_same_thread=False'
    followingup_db_RUI = 'sqlite+aiosqlite:///G:/database/Following_Usr.db?check_same_thread=False'  # 取关up数据库地址
    get_other_lotDb = DBINFO('H:/GetOthersLotDB/LotInfoDB.db', 'sqlite+aiosqlite:///H:/GetOthersLotDB/LotInfoDB.db')
    MYSQL = MYSQL()
    proxyRedis = REDISINFO()


class CONFIG:
    root_dir = 'K:/python test/'  # b站代码的根目录
    pushnotify = pushnotify() # 推送设置
    zhihu_CONFIG = zhihu_CONFIG()  # 知乎设置
    database = database()
    UA_LIST = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36', ]  # UA列表
