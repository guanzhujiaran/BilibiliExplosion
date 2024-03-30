from typing import List, Optional

from sqlalchemy import BigInteger, Column, ForeignKeyConstraint, Index, Integer, JSON, Text, text
from sqlalchemy.dialects.mysql import TEXT, TINYINT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class TClickAreaCard(Base):
    __tablename__ = 't_click_area_card'

    id = mapped_column(Integer, primary_key=True)
    json_data = mapped_column(JSON)

    t_topic: Mapped[List['TTopic']] = relationship('TTopic', uselist=True, back_populates='click_area_card')


class TSpaceseries(Base):
    __tablename__ = 't_spaceseries'
    __table_args__ = {'comment': 'B站播放列表'}

    series_id = mapped_column(Integer, primary_key=True, server_default=text('(0)'))
    mid = mapped_column(BigInteger)
    data = mapped_column(JSON)
    name = mapped_column(TEXT, comment='播放列表的名称')


class TTopicCreator(Base):
    __tablename__ = 't_topic_creator'

    uid = mapped_column(BigInteger, primary_key=True)
    face = mapped_column(Text)
    name = mapped_column(Text)

    t_top_details: Mapped[List['TTopDetails']] = relationship('TTopDetails', uselist=True, back_populates='topic_creator')


class TTopicItem(Base):
    __tablename__ = 't_topic_item'

    pkid = mapped_column(Integer, primary_key=True)
    back_color = mapped_column(Text)
    ctime = mapped_column(Integer)
    description = mapped_column(Text)
    discuss = mapped_column(BigInteger)
    dynamics = mapped_column(BigInteger)
    fav = mapped_column(BigInteger)
    id = mapped_column(BigInteger)
    jump_url = mapped_column(Text)
    like = mapped_column(BigInteger)
    name = mapped_column(Text)
    share = mapped_column(BigInteger)
    share_pic = mapped_column(Text)
    share_url = mapped_column(Text)
    view = mapped_column(BigInteger)

    t_top_details: Mapped[List['TTopDetails']] = relationship('TTopDetails', uselist=True, back_populates='topic_item')


class TTrafficCard(Base):
    __tablename__ = 't_traffic_card'

    id = mapped_column(Integer, primary_key=True)
    benefit_point = mapped_column(Text)
    card_desc = mapped_column(Text)
    icon_url = mapped_column(Text)
    jump_title = mapped_column(Text)
    jump_url = mapped_column(Text)
    name = mapped_column(Text)

    t_functional_card: Mapped[List['TFunctionalCard']] = relationship('TFunctionalCard', uselist=True, back_populates='traffic_card')


class TFunctionalCard(Base):
    __tablename__ = 't_functional_card'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='t_functional_card_ibfk_1'),
        Index('traffic_card_id', 'traffic_card_id')
    )

    id = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer)
    json_data = mapped_column(JSON)

    traffic_card: Mapped[Optional['TTrafficCard']] = relationship('TTrafficCard', back_populates='t_functional_card')
    t_topic: Mapped[List['TTopic']] = relationship('TTopic', uselist=True, back_populates='functional_card')


class TTopDetails(Base):
    __tablename__ = 't_top_details'
    __table_args__ = (
        ForeignKeyConstraint(['topic_creator_id'], ['t_topic_creator.uid'], name='t_top_details_ibfk_2'),
        ForeignKeyConstraint(['topic_item_id'], ['t_topic_item.pkid'], name='t_top_details_ibfk_1'),
        Index('topic_creator_id', 'topic_creator_id'),
        Index('topic_item_id', 'topic_item_id')
    )

    id = mapped_column(Integer, primary_key=True)
    close_pub_layer_entry = mapped_column(TINYINT(1))
    has_create_jurisdiction = mapped_column(TINYINT(1))
    operation_content = mapped_column(JSON)
    word_color = mapped_column(Integer)
    topic_item_id = mapped_column(Integer)
    topic_creator_id = mapped_column(BigInteger)

    topic_creator: Mapped[Optional['TTopicCreator']] = relationship('TTopicCreator', back_populates='t_top_details')
    topic_item: Mapped[Optional['TTopicItem']] = relationship('TTopicItem', back_populates='t_top_details')
    t_topic: Mapped[List['TTopic']] = relationship('TTopic', uselist=True, back_populates='topic_detail')


class TTopic(Base):
    __tablename__ = 't_topic'
    __table_args__ = (
        ForeignKeyConstraint(['click_area_card_id'], ['t_click_area_card.id'], name='t_topic_ibfk_1'),
        ForeignKeyConstraint(['functional_card_id'], ['t_functional_card.id'], name='t_topic_ibfk_2'),
        ForeignKeyConstraint(['topic_detail_id'], ['t_top_details.id'], name='t_topic_ibfk_3'),
        Index('click_area_card_id', 'click_area_card_id'),
        Index('functional_card_id', 'functional_card_id'),
        Index('topic_detail_id', 'topic_detail_id'),
        Index('topic_id', 'topic_id', unique=True)
    )

    topic_id = mapped_column(Integer, primary_key=True)
    raw_JSON = mapped_column(JSON)
    click_area_card_id = mapped_column(Integer)
    functional_card_id = mapped_column(Integer)
    topic_detail_id = mapped_column(Integer)

    click_area_card: Mapped[Optional['TClickAreaCard']] = relationship('TClickAreaCard', back_populates='t_topic')
    functional_card: Mapped[Optional['TFunctionalCard']] = relationship('TFunctionalCard', back_populates='t_topic')
    topic_detail: Mapped[Optional['TTopDetails']] = relationship('TTopDetails', back_populates='t_topic')
