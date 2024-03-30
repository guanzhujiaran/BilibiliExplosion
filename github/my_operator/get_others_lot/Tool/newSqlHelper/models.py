from typing import List, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKeyConstraint, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class TLotmaininfo(Base):
    __tablename__ = 't_lotmaininfo'
    __table_args__ = (
        Index('lotRound_id', 'lotRound_id', unique=True),
    )

    id = mapped_column(Integer, primary_key=True)
    lotRound_id = mapped_column(Integer)
    allNum = mapped_column(Integer)
    lotNum = mapped_column(Integer)
    uselessNum = mapped_column(Integer)
    isRoundFinished = mapped_column(TINYINT(1))

    t_lotdyninfo: Mapped[List['TLotdyninfo']] = relationship('TLotdyninfo', uselist=True, back_populates='dynLotRound')


class TLotuserinfo(Base):
    __tablename__ = 't_lotuserinfo'

    uid = mapped_column(BigInteger, primary_key=True)
    uname = mapped_column(Text)
    updateNum = mapped_column(Integer)
    updatetime = mapped_column(DateTime)
    isUserSpaceFinished = mapped_column(Integer)
    offset = mapped_column(Text)
    latestFinishedOffset = mapped_column(Text)
    isPubLotUser = mapped_column(TINYINT(1))

    t_lotuserspaceresp: Mapped[List['TLotuserspaceresp']] = relationship('TLotuserspaceresp', uselist=True, back_populates='t_lotuserinfo')


class TLotdyninfo(Base):
    __tablename__ = 't_lotdyninfo'
    __table_args__ = (
        ForeignKeyConstraint(['dynLotRound_id'], ['t_lotmaininfo.lotRound_id'], name='t_lotdyninfo_ibfk_1'),
        Index('dynLotRound_id', 'dynLotRound_id')
    )

    dynId = mapped_column(String(64), primary_key=True)
    dynamicUrl = mapped_column(Text)
    authorName = mapped_column(Text)
    up_uid = mapped_column(BigInteger)
    pubTime = mapped_column(DateTime)
    dynContent = mapped_column(Text)
    commentCount = mapped_column(Integer)
    repostCount = mapped_column(Integer)
    highlightWords = mapped_column(Text)
    officialLotType = mapped_column(Text)
    officialLotId = mapped_column(Text)
    isOfficialAccount = mapped_column(TINYINT(1))
    isManualReply = mapped_column(Text)
    isFollowed = mapped_column(TINYINT(1))
    isLot = mapped_column(TINYINT(1))
    hashTag = mapped_column(Text)
    dynLotRound_id = mapped_column(Integer)
    rawJsonStr = mapped_column(JSON)

    dynLotRound: Mapped[Optional['TLotmaininfo']] = relationship('TLotmaininfo', back_populates='t_lotdyninfo')


class TLotuserspaceresp(Base):
    __tablename__ = 't_lotuserspaceresp'
    __table_args__ = (
        ForeignKeyConstraint(['spaceUid'], ['t_lotuserinfo.uid'], name='t_lotuserspaceresp_ibfk_1'),
        Index('spaceUid', 'spaceUid')
    )

    spaceOffset = mapped_column(String(64), primary_key=True)
    spaceUid = mapped_column(BigInteger)
    spaceRespJson = mapped_column(JSON)

    t_lotuserinfo: Mapped[Optional['TLotuserinfo']] = relationship('TLotuserinfo', back_populates='t_lotuserspaceresp')
