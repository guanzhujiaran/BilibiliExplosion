from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class UserInfo(Base):
    __tablename__ = 'UserInfo'

    pk = mapped_column(Integer, primary_key=True)
    uid = mapped_column(Integer, unique=True)
    upTimeStamp = mapped_column(TIMESTAMP, server_default=text("'1970-01-01 00:00:00'"))
    isLotUp = mapped_column(Integer, server_default=text('1'))

    Space_Dyn: Mapped[List['SpaceDyn']] = relationship('SpaceDyn', uselist=True, back_populates='UserInfo_')


class SpaceDyn(Base):
    __tablename__ = 'Space_Dyn'

    pk = mapped_column(Integer, primary_key=True)
    Space_Dyn_uid = mapped_column(ForeignKey('UserInfo.uid'))
    uname = mapped_column(String)
    dynamic_id = mapped_column(Integer)
    dynamic_content = mapped_column(String)
    dynamic_type = mapped_column(String)
    is_lot_dyn = mapped_column(Integer)
    pubts = mapped_column(Integer, server_default=text("strftime('%s','now')"))

    UserInfo_: Mapped[Optional['UserInfo']] = relationship('UserInfo', back_populates='Space_Dyn')
