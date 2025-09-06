import os
from sqlacodegen_v2 import generate_models
from CONFIG import CONFIG
SQL_URI = CONFIG.database.MYSQL.dyn_detail.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')
generate_models(db_url=SQL_URI, outfile_path='./models.py')
