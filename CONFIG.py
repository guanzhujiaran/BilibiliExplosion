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


class database:
    dynDetail = "H:/database/dynDetail.db"
    proxy_db = "K:/sqlite_database/proxy_database/proxy_db.db"


class CONFIG:
    root_dir = 'K:/python test/'  # b站代码的根目录
    pushnotify = pushnotify()
    zhihu_CONFIG = zhihu_CONFIG()  # 知乎设置
    database = database()
