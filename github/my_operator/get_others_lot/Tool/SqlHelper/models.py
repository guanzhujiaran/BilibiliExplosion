from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class TLotMainInfo(Base):
    __tablename__ = 'T_LotMainInfo'

    id = mapped_column(Integer, primary_key=True)
    lotRound = mapped_column(Integer, nullable=False)
    allNum = mapped_column(Integer, nullable=False)
    lotNum = mapped_column(Integer, nullable=False)
    uselessNum = mapped_column(Integer, nullable=False)
    isRoundFinished = mapped_column(Integer, nullable=False)

    T_LotDynInfo: Mapped[List['TLotDynInfo']] = relationship('TLotDynInfo', uselist=True, back_populates='T_LotMainInfo')


class TLotUserInfo(Base):
    __tablename__ = 'T_LotUserInfo'

    id = mapped_column(Integer, primary_key=True)
    uid = mapped_column(Integer, nullable=False)
    uname = mapped_column(String, nullable=False)
    updateNum = mapped_column(Integer, nullable=False)
    updatetime = mapped_column(DateTime, nullable=False)
    isUserSpaceFinished = mapped_column(Integer, nullable=False)
    offset = mapped_column(Integer, nullable=False)
    latestFinishedOffset = mapped_column(Integer)

    T_LotDynInfo: Mapped[List['TLotDynInfo']] = relationship('TLotDynInfo', uselist=True, foreign_keys='[TLotDynInfo.authorName]', back_populates='T_LotUserInfo')
    T_LotDynInfo_: Mapped[List['TLotDynInfo']] = relationship('TLotDynInfo', uselist=True, foreign_keys='[TLotDynInfo.up_uid]', back_populates='T_LotUserInfo_')
    T_LotUserSpaceResp: Mapped[List['TLotUserSpaceResp']] = relationship('TLotUserSpaceResp', uselist=True, back_populates='T_LotUserInfo')


class TLotDynInfo(Base):
    __tablename__ = 'T_LotDynInfo'

    id = mapped_column(Integer, primary_key=True)
    dynId = mapped_column(String, nullable=False)
    dynamicUrl = mapped_column(String, nullable=False)
    authorName = mapped_column(ForeignKey('T_LotUserInfo.uname', onupdate='CASCADE'), nullable=False)
    up_uid = mapped_column(ForeignKey('T_LotUserInfo.uid', onupdate='CASCADE'), nullable=False)
    pubTime = mapped_column(DateTime, nullable=False)
    dynContent = mapped_column(String, nullable=False)
    commentCount = mapped_column(Integer, nullable=False)
    repostCount = mapped_column(Integer, nullable=False)
    highlightWords = mapped_column(String, nullable=False)
    officialLotType = mapped_column(String, nullable=False)
    officialLotId = mapped_column(String, nullable=False)
    isOfficialAccount = mapped_column(Integer, nullable=False)
    isManualReply = mapped_column(String, nullable=False)
    isFollowed = mapped_column(Integer, nullable=False)
    isLot = mapped_column(Integer, nullable=False)
    hashTag = mapped_column(String, nullable=False)
    dynLotRound = mapped_column(ForeignKey('T_LotMainInfo.lotRound', ondelete='SET NULL', onupdate='CASCADE'), nullable=False)
    rawJsonStr = mapped_column(String, nullable=False)

    T_LotUserInfo: Mapped['TLotUserInfo'] = relationship('TLotUserInfo', foreign_keys=[authorName], back_populates='T_LotDynInfo')
    T_LotMainInfo: Mapped['TLotMainInfo'] = relationship('TLotMainInfo', back_populates='T_LotDynInfo')
    T_LotUserInfo_: Mapped['TLotUserInfo'] = relationship('TLotUserInfo', foreign_keys=[up_uid], back_populates='T_LotDynInfo_')


class TLotUserSpaceResp(Base):
    __tablename__ = 'T_LotUserSpaceResp'

    id = mapped_column(Integer, primary_key=True)
    spaceUid = mapped_column(ForeignKey('T_LotUserInfo.uid', onupdate='CASCADE'), nullable=False)
    spaceOffset = mapped_column(Integer, nullable=False)
    spaceRespJson = mapped_column(String, nullable=False)

    T_LotUserInfo: Mapped['TLotUserInfo'] = relationship('TLotUserInfo', back_populates='T_LotUserSpaceResp')
