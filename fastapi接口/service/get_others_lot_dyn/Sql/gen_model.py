import os

from CONFIG import CONFIG

SQL_URI = CONFIG.database.MYSQL.get_other_lot_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')

os.system(f'sqlacodegen_v2 {SQL_URI} > models.py')