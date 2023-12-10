import os
from datetime import datetime

from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime, UniqueConstraint, text, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine

SQLITE_URI = 'sqlite:///G:/database/Following_Usr.db?check_same_thread=False'

engine = create_engine(SQLITE_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()

Base = declarative_base()


class USER_INFO(Base):
    """用户信息类"""
    __tablename__ = 'UserInfo'
    pk = mapped_column(Integer, primary_key=True, auto_increment=True)
    uid = mapped_column(Integer, unique=True)
    upTimeStamp = mapped_column(TIMESTAMP, server_default="1970-01-01 00:00:00",onupdate=text("CURRENT_TIMESTAMP"))
    isLotUp = mapped_column(Integer, server_default=text('1'))
    officialVerify = mapped_column(Integer, server_default=text('-2'))
    uname = mapped_column(String, server_default=text(''))
    Space_Dyn = relationship('Space_Dyn', back_populates='UserInfo', uselist=False)


class Space_Dyn(Base):
    """用户空间动态（每个用户最多记录个100条）"""
    __tablename__ = 'Space_Dyn'
    pk = mapped_column(Integer, primary_key=True, auto_increment=True)
    Space_Dyn_uid = mapped_column(ForeignKey("UserInfo.uid"))
    uname = mapped_column(String)
    dynamic_id = mapped_column(Integer)
    dynamic_content = mapped_column(String)
    dynamic_type = mapped_column(String)
    is_lot_dyn = mapped_column(Integer, default=0)
    like = mapped_column(Integer, default=0)
    reply = mapped_column(Integer, default=0)
    repost = mapped_column(Integer, default=0)
    USER_INFO = relationship('USER_INFO', back_populates='Space_Dyn')
    pubts = mapped_column(Integer, server_default=text("(strftime('%s','now'))"))


    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')
