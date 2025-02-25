import os

if __name__ == '__main__':
    # 创建数据库命令
    # Base.metadata.create_all(checkfirst=True, bind=engine)
    from CONFIG import CONFIG
    SQLITE_URI = CONFIG.database.MYSQL.dyn_detail
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')