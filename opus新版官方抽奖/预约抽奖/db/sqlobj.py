import os

from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime, UniqueConstraint, Text, Boolean, BigInteger, TEXT
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine

import CONFIG

SQL_URI = CONFIG.MYSQL.bili_reserve_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')

engine = create_engine(SQL_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()

Base = declarative_base()


class t_up_reserve_relation_info(Base):
    __tablename__ = 't_up_reserve_relation_info'

    code = mapped_column(Integer, nullable=True)
    message = mapped_column(Text, nullable=True)
    ttl = mapped_column(Integer, nullable=True)
    sid = mapped_column(Integer, nullable=True)
    name = mapped_column(Text, nullable=True)
    total = mapped_column(BigInteger, nullable=True)
    stime = mapped_column(Integer, nullable=True)
    etime = mapped_column(Integer, nullable=True)
    isFollow = mapped_column(Integer, nullable=True)
    state = mapped_column(Integer, nullable=True)
    oid = mapped_column(Text, nullable=True)
    type = mapped_column(Integer, nullable=True)
    upmid = mapped_column(BigInteger, nullable=True)
    reserveRecordCtime = mapped_column(Integer, nullable=True)
    livePlanStartTime = mapped_column(Integer, nullable=True)
    upActVisible = mapped_column(Integer, nullable=True)
    lotteryType = mapped_column(Integer, nullable=True)
    text = mapped_column(Text, nullable=True)
    jumpUrl = mapped_column(Text, nullable=True)
    dynamicId = mapped_column(Text, nullable=True)
    reserveTotalShowLimit = mapped_column(BigInteger, nullable=True)
    desc = mapped_column(Text, nullable=True)
    start_show_time = mapped_column(Integer, nullable=True)
    BaseJumpUrl= mapped_column(Text, nullable=True)
    OidView = mapped_column(BigInteger, nullable=True)
    ids = mapped_column(Integer, nullable=True, primary_key=True,autoincrement=False)
    hide = mapped_column(Text, nullable=True)
    ext = mapped_column(Text, nullable=True)
    subType = mapped_column(Text, nullable=True)
    productIdPrice = mapped_column(JSON, nullable=True)
    reserve_products = mapped_column(JSON, nullable=True)
    raw_JSON = mapped_column(JSON, nullable=True)

    reserve_round_id = mapped_column(Integer,ForeignKey('t_reserve_round_info.round_id'))
    new_field = mapped_column(JSON, nullable=True, comment='是否有新的字段')


class t_reserve_round_info(Base):
    __tablename__ = 't_reserve_round_info'

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id = mapped_column(Integer, nullable=False, autoincrement=True, unique=True)
    is_finished = mapped_column(Boolean, nullable=False)
    round_start_ts = mapped_column(Integer, nullable=False)
    round_add_num = mapped_column(Integer, nullable=False)
    round_lot_num = mapped_column(Integer, nullable=False)


if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQL_URI} > models.py')
