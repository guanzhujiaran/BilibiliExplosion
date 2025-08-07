import os

from sqlalchemy import Integer, TEXT, ForeignKey, JSON, DateTime, UniqueConstraint, Boolean, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine

import CONFIG

SQLURI = CONFIG.database.MYSQL.bili_db_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')

engine = create_engine(SQLURI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()

Base = declarative_base()


# TODO: 牢记：一对多的情况下外键设置在一的那张表上，对上多的那张表的主键即可！

class T_topic(Base):
    __tablename__ = 't_topic'
    topic_id = mapped_column(Integer, unique=True, primary_key=True, autoincrement=False)
    raw_JSON = mapped_column(JSON)
    click_area_card_id = mapped_column(ForeignKey('t_click_area_card.id'), )
    functional_card_id = mapped_column(ForeignKey('t_functional_card.id'), )
    topic_detail_id = mapped_column(ForeignKey('t_top_details.id'), )


class T_click_area_card(Base):
    __tablename__ = 't_click_area_card'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    json_data = mapped_column(JSON)


class T_functional_card(Base):
    __tablename__ = 't_functional_card'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    traffic_card_id = mapped_column(ForeignKey('t_traffic_card.id'))
    json_data = mapped_column(JSON)


class T_traffic_card(Base):
    __tablename__ = 't_traffic_card'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    benefit_point = mapped_column(TEXT)
    card_desc = mapped_column(TEXT)
    icon_url = mapped_column(TEXT)
    jump_title = mapped_column(TEXT)
    jump_url = mapped_column(TEXT)
    name = mapped_column(TEXT)


class T_top_details(Base):
    __tablename__ = 't_top_details'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    close_pub_layer_entry = mapped_column(Boolean)
    has_create_jurisdiction = mapped_column(Boolean)
    operation_content = mapped_column(JSON)
    word_color = mapped_column(Integer)
    topic_item_id = mapped_column(ForeignKey('t_topic_item.pkid'))
    topic_creator_id = mapped_column(ForeignKey('t_topic_creator.uid'))# many

class T_topic_creator(Base):
    __tablename__ = 't_topic_creator'
    face = mapped_column(TEXT)
    name = mapped_column(TEXT)
    uid = mapped_column(BigInteger,primary_key=True,autoincrement=False) # 1


class T_topic_item(Base):
    __tablename__ = 't_topic_item'
    pkid = mapped_column(Integer, primary_key=True, autoincrement=True)
    back_color = mapped_column(TEXT)
    ctime = mapped_column(Integer)
    description = mapped_column(TEXT)
    discuss = mapped_column(BigInteger)
    dynamics = mapped_column(BigInteger)
    fav = mapped_column(BigInteger)
    id = mapped_column(BigInteger)
    jump_url = mapped_column(TEXT)
    like = mapped_column(BigInteger)
    name = mapped_column(TEXT)
    share = mapped_column(BigInteger)
    share_pic = mapped_column(TEXT)
    share_url = mapped_column(TEXT)
    view = mapped_column(BigInteger)


if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLURI} > models.py')
