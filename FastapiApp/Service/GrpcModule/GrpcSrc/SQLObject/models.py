from typing import List, Optional

from sqlalchemy import BigInteger, Column, Computed, ForeignKeyConstraint, Index, Integer, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import LONGTEXT, TEXT, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class BiliUserInfo(Base):
    __tablename__ = 'bili_user_info'
    __table_args__ = (
        Index('name', 'name', 'uid'),
    )

    uid = mapped_column(BigInteger, primary_key=True)
    name = mapped_column(VARCHAR(50))
    face = mapped_column(TEXT)

    bili_atari_info: Mapped[List['BiliAtariInfo']] = relationship('BiliAtariInfo', uselist=True, back_populates='bili_user_info')


class Lotdata(Base):
    __tablename__ = 'lotdata'
    __table_args__ = (
        Index('UQ_business_id', 'business_id', unique=True),
        Index('business_id', 'business_id'),
        Index('idx_lottery_id', 'lottery_id', 'business_id', 'lottery_time', 'sender_uid', 'business_type'),
        Index('lottery_time', 'lottery_time'),
        Index('sender_uid', 'sender_uid')
    )

    lottery_id = mapped_column(BigInteger, primary_key=True)
    business_id = mapped_column(BigInteger)
    status = mapped_column(BigInteger)
    lottery_time = mapped_column(BigInteger)
    lottery_at_num = mapped_column(BigInteger)
    lottery_feed_limit = mapped_column(BigInteger)
    first_prize = mapped_column(BigInteger)
    second_prize = mapped_column(BigInteger)
    third_prize = mapped_column(BigInteger)
    lottery_result = mapped_column(Text(collation='utf8mb4_general_ci'))
    first_prize_cmt = mapped_column(Text(collation='utf8mb4_general_ci'))
    second_prize_cmt = mapped_column(Text(collation='utf8mb4_general_ci'))
    third_prize_cmt = mapped_column(Text(collation='utf8mb4_general_ci'))
    first_prize_pic = mapped_column(Text(collation='utf8mb4_general_ci'))
    second_prize_pic = mapped_column(Text(collation='utf8mb4_general_ci'))
    third_prize_pic = mapped_column(Text(collation='utf8mb4_general_ci'))
    need_post = mapped_column(BigInteger)
    business_type = mapped_column(BigInteger)
    sender_uid = mapped_column(BigInteger)
    prize_type_first = mapped_column(Text(collation='utf8mb4_general_ci'))
    prize_type_second = mapped_column(Text(collation='utf8mb4_general_ci'))
    prize_type_third = mapped_column(Text(collation='utf8mb4_general_ci'))
    pay_status = mapped_column(BigInteger)
    ts = mapped_column(BigInteger)
    _gt_ = mapped_column(BigInteger)
    has_charge_right = mapped_column(Text(collation='utf8mb4_general_ci'))
    lottery_detail_url = mapped_column(Text(collation='utf8mb4_general_ci'))
    participants = mapped_column(BigInteger)
    participated = mapped_column(Text(collation='utf8mb4_general_ci'))
    vip_batch_sign = mapped_column(Text(collation='utf8mb4_general_ci'))
    exclusive_level = mapped_column(Text(collation='utf8mb4_general_ci'))
    followed = mapped_column(BigInteger)
    reposted = mapped_column(BigInteger)
    custom_extra_key = mapped_column(Text(collation='utf8mb4_general_ci'))
    created_at = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    article_pub_record: Mapped[List['ArticlePubRecord']] = relationship('ArticlePubRecord', uselist=True, back_populates='lot_data_business')
    bili_atari_info: Mapped[List['BiliAtariInfo']] = relationship('BiliAtariInfo', uselist=True, back_populates='atari_lot')
    bilidyndetail: Mapped[List['Bilidyndetail']] = relationship('Bilidyndetail', uselist=True, back_populates='lot')


class ArticlePubRecord(Base):
    __tablename__ = 'article_pub_record'
    __table_args__ = (
        ForeignKeyConstraint(['lot_data_business_id'], ['lotdata.business_id'], name='FK_article_pub_record_lotdata'),
        Index('lot_data_business_id', 'lot_data_business_id', unique=True),
        {'comment': '发布专栏记录'}
    )

    lot_data_business_id = mapped_column(BigInteger, nullable=False)
    pk = mapped_column(BigInteger, primary_key=True)
    round_id = mapped_column(Integer, comment='每一轮的号码')

    lot_data_business: Mapped['Lotdata'] = relationship('Lotdata', back_populates='article_pub_record')


class BiliAtariInfo(Base):
    __tablename__ = 'bili_atari_info'
    __table_args__ = (
        ForeignKeyConstraint(['atari_lot_id'], ['lotdata.lottery_id'], name='FK__lotdata_1'),
        ForeignKeyConstraint(['mid'], ['bili_user_info.uid'], name='FK_bili_atari_info_bili_user_info'),
        Index('FK__lotdata_1', 'atari_lot_id'),
        Index('atari_lot_rank', 'atari_lot_rank'),
        Index('atari_lot_type', 'atari_lot_type'),
        Index('atari_timestamp', 'atari_timestamp'),
        Index('mid', 'mid', 'atari_lot_id', unique=True)
    )

    pk = mapped_column(BigInteger, primary_key=True)
    mid = mapped_column(BigInteger)
    hongbao_money = mapped_column(Integer)
    atari_lot_id = mapped_column(BigInteger)
    atari_lot_rank = mapped_column(TINYINT, comment='1：一等奖\r\n2：二等奖\r\n3：三等奖')
    atari_lot_type = mapped_column(TINYINT, comment='中奖类型，对应B站business_id')
    atari_timestamp = mapped_column(TIMESTAMP)

    atari_lot: Mapped[Optional['Lotdata']] = relationship('Lotdata', back_populates='bili_atari_info')
    bili_user_info: Mapped[Optional['BiliUserInfo']] = relationship('BiliUserInfo', back_populates='bili_atari_info')


class Bilidyndetail(Base):
    __tablename__ = 'bilidyndetail'
    __table_args__ = (
        ForeignKeyConstraint(['lot_id'], ['lotdata.lottery_id'], name='biliDynDetail_FK_0_0'),
        Index('biliDynDetail_FK_0_0', 'lot_id')
    )

    rid = mapped_column(VARCHAR(255), primary_key=True, server_default=text("''"))
    dynamic_id = mapped_column(VARCHAR(255))
    dynData = mapped_column(LONGTEXT)
    lot_id = mapped_column(BigInteger)
    dynamic_created_time = mapped_column(VARCHAR(255))
    rid_int = mapped_column(BigInteger, Computed('(cast(`rid` as signed))', persisted=True))
    dynamic_id_int = mapped_column(BigInteger, Computed('(cast(`dynamic_id` as signed))', persisted=True))

    lot: Mapped[Optional['Lotdata']] = relationship('Lotdata', back_populates='bilidyndetail')
