#根据数据库 生成对象文件

import os

SQLITE_URI = fr'sqlite:///K:/sqlite_database/proxy_database/proxy_db.db''?check_same_thread=False'
os.system(f'sqlacodegen_v2 {SQLITE_URI} > ProxyModel.py')