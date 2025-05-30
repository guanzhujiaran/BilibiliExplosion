from CONFIG import CONFIG
from sqlacodegen_v2 import generate_models

SQL_URI = CONFIG.database.MYSQL.sams_club_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')
generate_models(db_url=SQL_URI, outfile_path='./models.py')
