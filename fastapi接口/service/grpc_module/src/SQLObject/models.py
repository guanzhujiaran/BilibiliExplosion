from typing import List, Optional

from sqlalchemy import BigInteger, Column, Computed, ForeignKeyConstraint, Index, Integer, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class Lotdata(Base):
    __tablename__ = 'lotdata'
    __table_args__ = (
        Index('business_id', 'business_id'),
        Index('idx_lottery_id', 'lottery_id'),
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

    article_pub_record: Mapped['ArticlePubRecord'] = relationship('ArticlePubRecord', uselist=False, back_populates='lot_data_business')
    bilidyndetail: Mapped['Bilidyndetail'] = relationship('Bilidyndetail', uselist=False, back_populates='lot')


class ArticlePubRecord(Base):
    __tablename__ = 'article_pub_record'
    __table_args__ = (
        ForeignKeyConstraint(['lot_data_business_id'], ['lotdata.business_id'], name='FK__lotdata'),
        Index('lot_data_business_id', 'lot_data_business_id', unique=True),
        {'comment': '发布专栏记录'}
    )

    lot_data_business_id = mapped_column(BigInteger, nullable=False)
    pk = mapped_column(BigInteger, primary_key=True)
    round_id = mapped_column(Integer, comment='每一轮的号码')

    lot_data_business: Mapped['Lotdata'] = relationship('Lotdata', back_populates='article_pub_record')


class Bilidyndetail(Base):
    __tablename__ = 'bilidyndetail'
    __table_args__ = (
        ForeignKeyConstraint(['lot_id'], ['lotdata.lottery_id'], onupdate='CASCADE', name='biliDynDetail_FK_0_0'),
        Index('dynamic_id_int', 'dynamic_id_int'),
        Index('idx_dynamic_created_time', 'dynamic_created_time'),
        Index('idx_dynamic_id', 'dynamic_id'),
        Index('idx_lot_id', 'lot_id'),
        Index('idx_rid_int', 'rid_int'),
        Index('rid', 'rid')
    )

    rid = mapped_column(VARCHAR(255), primary_key=True, server_default=text("''"))
    dynamic_id = mapped_column(Text(collation='utf8mb4_general_ci'))
    dynData = mapped_column(LONGTEXT)
    lot_id = mapped_column(BigInteger)
    dynamic_created_time = mapped_column(Text(collation='utf8mb4_general_ci'))
    rid_int = mapped_column(BigInteger, Computed('(cast(`rid` as signed))', persisted=True))
    dynamic_id_int = mapped_column(BigInteger, Computed('(cast(`dynamic_id` as signed))', persisted=True))

    lot: Mapped[Optional['Lotdata']] = relationship('Lotdata', back_populates='bilidyndetail')
