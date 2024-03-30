from typing import List, Optional

from sqlalchemy import BigInteger, Column, ForeignKeyConstraint, Index, Integer, JSON, Text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class TReserveRoundInfo(Base):
    __tablename__ = 't_reserve_round_info'
    __table_args__ = (
        Index('round_id', 'round_id', unique=True),
    )

    id = mapped_column(Integer, primary_key=True)
    round_id = mapped_column(Integer, nullable=False)
    is_finished = mapped_column(TINYINT(1), nullable=False)
    round_start_ts = mapped_column(Integer, nullable=False)
    round_add_num = mapped_column(Integer, nullable=False)
    round_lot_num = mapped_column(Integer, nullable=False)

    t_up_reserve_relation_info: Mapped[List['TUpReserveRelationInfo']] = relationship('TUpReserveRelationInfo', uselist=True, back_populates='reserve_round')


class TUpReserveRelationInfo(Base):
    __tablename__ = 't_up_reserve_relation_info'
    __table_args__ = (
        ForeignKeyConstraint(['reserve_round_id'], ['t_reserve_round_info.round_id'], name='t_up_reserve_relation_info_ibfk_1'),
        Index('reserve_round_id', 'reserve_round_id')
    )

    ids = mapped_column(Integer, primary_key=True)
    code = mapped_column(Integer)
    message = mapped_column(Text)
    ttl = mapped_column(Integer)
    sid = mapped_column(Integer)
    name = mapped_column(Text)
    total = mapped_column(BigInteger)
    stime = mapped_column(Integer)
    etime = mapped_column(Integer)
    isFollow = mapped_column(Integer)
    state = mapped_column(Integer)
    oid = mapped_column(Text)
    type = mapped_column(Integer)
    upmid = mapped_column(BigInteger)
    reserveRecordCtime = mapped_column(Integer)
    livePlanStartTime = mapped_column(Integer)
    upActVisible = mapped_column(Integer)
    lotteryType = mapped_column(Integer)
    text = mapped_column(Text)
    jumpUrl = mapped_column(Text)
    dynamicId = mapped_column(Text)
    reserveTotalShowLimit = mapped_column(BigInteger)
    desc = mapped_column(Text)
    start_show_time = mapped_column(Integer)
    BaseJumpUrl = mapped_column(Text)
    OidView = mapped_column(BigInteger)
    hide = mapped_column(Text)
    ext = mapped_column(Text)
    subType = mapped_column(Text)
    productIdPrice = mapped_column(JSON)
    reserve_products = mapped_column(JSON)
    raw_JSON = mapped_column(JSON)
    reserve_round_id = mapped_column(Integer)
    new_field = mapped_column(JSON, comment='是否有新的字段')

    reserve_round: Mapped[Optional['TReserveRoundInfo']] = relationship('TReserveRoundInfo', back_populates='t_up_reserve_relation_info')
