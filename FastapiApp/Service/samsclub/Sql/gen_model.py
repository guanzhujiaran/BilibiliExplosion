from CONFIG import CONFIG
from sqlacodegen_v2 import generate_models
import os
SQL_URI = CONFIG.database.MYSQL.sams_club_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')
generate_models(db_url=SQL_URI, outfile_path=os.path.join( os.path.dirname(__file__),'./models.py'))
