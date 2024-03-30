import os

from sqlalchemy import Integer, ForeignKey, JSON, DateTime, UniqueConstraint, BigInteger, Text, Boolean, String
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine
import CONFIG

SQLITE_URI = CONFIG.database.MYSQL.get_other_lot_URI.replace('+aiomysql', '+pymysql').replace('&autocommit=true', '')

engine = create_engine(SQLITE_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()
Base = declarative_base()


class TLotMainInfo(Base):
    __tablename__ = 'T_LotMainInfo'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    lotRound_id = mapped_column(Integer, unique=True)
    allNum = mapped_column(Integer)
    lotNum = mapped_column(Integer)
    uselessNum = mapped_column(Integer)
    isRoundFinished = mapped_column(Boolean)


class TLotDynInfo(Base):
    __tablename__ = 'T_LotDynInfo'
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
    isOfficialAccount = mapped_column(Boolean)
    isManualReply = mapped_column(Text)
    isFollowed = mapped_column(Boolean)
    isLot = mapped_column(Boolean)
    hashTag = mapped_column(Text)
    dynLotRound_id = mapped_column(Integer, ForeignKey('T_LotMainInfo.lotRound_id'))
    rawJsonStr = mapped_column(JSON)


class TLotUserInfo(Base):
    __tablename__ = 'T_LotUserInfo'
    uid = mapped_column(BigInteger, primary_key=True, )
    uname = mapped_column(Text)
    updateNum = mapped_column(Integer)
    updatetime = mapped_column(DateTime)
    isUserSpaceFinished = mapped_column(Integer)
    offset = mapped_column(Text)
    latestFinishedOffset = mapped_column(Text)
    isPubLotUser = mapped_column(Boolean, default=False)


class TLotUserSpaceResp(Base):
    __tablename__ = 'T_LotUserSpaceResp'
    spaceUid = mapped_column(ForeignKey('T_LotUserInfo.uid'))
    spaceOffset = mapped_column(String(64), primary_key=True)
    spaceRespJson = mapped_column(JSON)


if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')
