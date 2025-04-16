import os

from sqlalchemy import Integer, BLOB
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, mapped_column

from fastapi接口.service.toutiao.src.ToutiaoSetting import CONFIG

SQLITE_URI = CONFIG.DBSetting.SpaceFeedDataDb

engine = create_engine(SQLITE_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()

Base = declarative_base()


class FeedData(Base):
    __tablename__ = 'T_FEEDDATA'
    pk = mapped_column(Integer, primary_key=True,autoincrement=True)
    id = mapped_column(Integer, unique=True)
    publish_time = mapped_column(Integer)
    zippedData = mapped_column(BLOB)



if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')
