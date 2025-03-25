#根据数据库 生成对象文件

import os

import CONFIG

SQLITE_URI = CONFIG.database.MYSQL.proxy_db_URI
os.system(f'sqlacodegen_v2 {SQLITE_URI} > ProxyModel.py')