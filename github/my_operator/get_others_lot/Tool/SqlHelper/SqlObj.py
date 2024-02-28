import os

from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine
import CONFIG

SQLITE_URI = CONFIG.database.get_other_lotDb.DB_URI.replace('+aiosqlite','')

engine = create_engine(SQLITE_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()
Base = declarative_base()


class TLotMainInfo(Base):
    __tablename__ = 'T_LotMainInfo'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lotRound: Mapped[int] = mapped_column(Integer)
    allNum: Mapped[int] = mapped_column(Integer)
    lotNum: Mapped[int] = mapped_column(Integer)
    uselessNum: Mapped[int] = mapped_column(Integer)
    isRoundFinished: Mapped[int] = mapped_column(Integer)


class TLotDynInfo(Base):
    __tablename__ = 'T_LotDynInfo'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dynId: Mapped[str] = mapped_column(String)
    dynamicUrl: Mapped[str] = mapped_column(String)
    authorName: Mapped[str] = mapped_column(String,
                                            ForeignKey('T_LotUserInfo.uname', onupdate='CASCADE', ondelete='NO ACTION'))
    up_uid: Mapped[int] = mapped_column(Integer,
                                        ForeignKey('T_LotUserInfo.uid', onupdate='CASCADE', ondelete='NO ACTION'))
    pubTime: Mapped[str] = mapped_column(DateTime)
    dynContent: Mapped[str] = mapped_column(String)
    commentCount: Mapped[int] = mapped_column(Integer)
    repostCount: Mapped[int] = mapped_column(Integer)
    highlightWords: Mapped[str] = mapped_column(String)
    officialLotType: Mapped[str] = mapped_column(String)
    officialLotId: Mapped[int] = mapped_column(String)
    isOfficialAccount: Mapped[int] = mapped_column()
    isManualReply: Mapped[str] = mapped_column(String)
    isFollowed: Mapped[int] = mapped_column(Integer)
    isLot: Mapped[int] = mapped_column(Integer)
    hashTag: Mapped[str] = mapped_column(String)
    dynLotRound: Mapped[int] = mapped_column(Integer, ForeignKey('T_LotMainInfo.lotRound', onupdate='CASCADE',
                                                                 ondelete='SET NULL'))
    rawJsonStr: Mapped[str] = mapped_column(String)


class TLotUserInfo(Base):
    __tablename__ = 'T_LotUserInfo'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(Integer)
    uname: Mapped[str] = mapped_column(String)
    updateNum: Mapped[int] = mapped_column(Integer)
    updatetime: Mapped[str] = mapped_column(DateTime)
    isUserSpaceFinished: Mapped[int] = mapped_column(Integer)
    offset: Mapped[int] = mapped_column(Integer)
    latestFinishedOffset: Mapped[int] = mapped_column(Integer)
class TLotUserSpaceResp(Base):
    __tablename__ = 'T_LotUserSpaceResp'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spaceUid: Mapped[int] = mapped_column(ForeignKey('T_LotUserInfo.uid', onupdate='CASCADE',
                                                                 ondelete='NO ACTION'))
    spaceOffset: Mapped[int] = mapped_column(Integer)
    spaceRespJson: Mapped[str] = mapped_column(String)

if __name__ == '__main__':
    # 创建数据库命令
    Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')
