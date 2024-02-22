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


class pushnotify:
    def __init__(self):
        self._pushme = pushme()

    @property
    def pushme(self):
        return self._pushme


class zhihu_CONFIG:
    root_dir = 'K:/zhihu/'


@dataclass
class MYSQL:
    proxy_db_URI: str = 'mysql+aiomysql://root:114514@localhost:3306/proxy_db?charset=utf8&autocommit=true'


class database:
    dynDetail = "H:/database/dynDetail.db"
    proxy_db = "K:/sqlite_database/proxy_database/proxy_db.db"
    proxy_db_URI = 'sqlite+aiosqlite:///K:/sqlite_database/proxy_database/proxy_db.db?check_same_thread=False'
    followingup_db_RUI = 'sqlite+aiosqlite:///G:/database/Following_Usr.db?check_same_thread=False'  # 取关up数据库地址
    MYSQL = MYSQL()


class CONFIG:
    root_dir = 'K:/python test/'  # b站代码的根目录
    pushnotify = pushnotify()
    zhihu_CONFIG = zhihu_CONFIG()  # 知乎设置
    database = database()
    UA_LIST = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36', ]  # UA列表
