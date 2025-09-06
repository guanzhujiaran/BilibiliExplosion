from typing import List, Optional

from sqlalchemy import BigInteger, Column, ForeignKeyConstraint, Index, Integer, JSON, SmallInteger, String, Text, text
from sqlalchemy.dialects.mysql import TEXT, TINYINT, VARCHAR
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
    show_interact_data = mapped_column(TINYINT(1))

    t_top_details: Mapped[List['TTopDetails']] = relationship('TTopDetails', uselist=True, back_populates='topic_item')


class TTrafficCard(Base):
    __tablename__ = 't_traffic_card'

    id = mapped_column(Integer, primary_key=True)
    benefit_point = mapped_column(Text)
    card_desc = mapped_column(Text)
    icon_url = mapped_column(Text)
    jump_title = mapped_column(Text)
    jump_url = mapped_column(TEXT, comment='不同的话题可能有相同的活动链接，入库的时候查一下有没有相同的jump_url')
    name = mapped_column(Text)
    my_activity_status = mapped_column(SmallInteger, comment='0：未查询活动\r\n1：已成功查询\r\n2：查询了，但获取到的活动为空，也就是未知的活动\r\n3：查询出错了，去日志里查原因')

    t_activity_lottery: Mapped[List['TActivityLottery']] = relationship('TActivityLottery', uselist=True, back_populates='traffic_card')
    t_activity_match_lottery: Mapped[List['TActivityMatchLottery']] = relationship('TActivityMatchLottery', uselist=True, back_populates='traffic_card')
    t_activity_match_task: Mapped[List['TActivityMatchTask']] = relationship('TActivityMatchTask', uselist=True, back_populates='traffic_card')
    t_era_jika: Mapped[List['TEraJika']] = relationship('TEraJika', uselist=True, back_populates='traffic_card')
    t_era_lottery: Mapped[List['TEraLottery']] = relationship('TEraLottery', uselist=True, back_populates='traffic_card')
    t_era_task: Mapped[List['TEraTask']] = relationship('TEraTask', uselist=True, back_populates='traffic_card')
    t_era_video: Mapped[List['TEraVideo']] = relationship('TEraVideo', uselist=True, back_populates='traffic_card')
    t_functional_card: Mapped[List['TFunctionalCard']] = relationship('TFunctionalCard', uselist=True, back_populates='traffic_card')


class TActivityLottery(Base):
    __tablename__ = 't_activity_lottery'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_activity_lottery_t_traffic_card'),
        Index('FK_activity_lottery_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer)
    lotteryId = mapped_column(String(50))
    continueTimes = mapped_column(JSON)
    list = mapped_column(JSON)

    traffic_card: Mapped[Optional['TTrafficCard']] = relationship('TTrafficCard', back_populates='t_activity_lottery')


class TActivityMatchLottery(Base):
    __tablename__ = 't_activity_match_lottery'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_activity_match_lottery_t_traffic_card'),
        Index('FK_activity_match_lottery_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer)
    lottery_id = mapped_column(String(50))
    activity_id = mapped_column(String(50))

    traffic_card: Mapped[Optional['TTrafficCard']] = relationship('TTrafficCard', back_populates='t_activity_match_lottery')


class TActivityMatchTask(Base):
    __tablename__ = 't_activity_match_task'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_t_activity_match_task_t_traffic_card'),
        Index('FK_t_activity_match_task_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer, nullable=False)
    task_desc = mapped_column(VARCHAR(50))
    interact_type = mapped_column(JSON)
    task_group_id = mapped_column(JSON)
    task_name = mapped_column(String(50))
    url = mapped_column(VARCHAR(255))

    traffic_card: Mapped['TTrafficCard'] = relationship('TTrafficCard', back_populates='t_activity_match_task')


class TEraJika(Base):
    __tablename__ = 't_era_jika'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_era_jika_t_traffic_card'),
        Index('FK_era_jika_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer, nullable=False)
    activityUrl = mapped_column(VARCHAR(255), server_default=text("''"))
    jikaId = mapped_column(VARCHAR(50), server_default=text("''"))
    topId = mapped_column(Integer)
    topName = mapped_column(VARCHAR(50), server_default=text("''"))

    traffic_card: Mapped['TTrafficCard'] = relationship('TTrafficCard', back_populates='t_era_jika')


class TEraLottery(Base):
    __tablename__ = 't_era_lottery'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_era_lottery_t_traffic_card'),
        Index('FK_era_lottery_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer, nullable=False)
    activity_id = mapped_column(VARCHAR(50))
    gifts = mapped_column(JSON)
    icon = mapped_column(VARCHAR(50))
    lottery_id = mapped_column(VARCHAR(50))
    lottery_type = mapped_column(Integer)
    per_time = mapped_column(Integer)
    point_name = mapped_column(VARCHAR(50))

    traffic_card: Mapped['TTrafficCard'] = relationship('TTrafficCard', back_populates='t_era_lottery')


class TEraTask(Base):
    __tablename__ = 't_era_task'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK__t_traffic_card'),
        Index('FK__t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer, nullable=False)
    awardName = mapped_column(VARCHAR(50))
    taskDes = mapped_column(VARCHAR(255))
    taskId = mapped_column(VARCHAR(50))
    taskName = mapped_column(VARCHAR(50))
    taskType = mapped_column(Integer)
    topicID = mapped_column(VARCHAR(50))
    topicName = mapped_column(VARCHAR(50))

    traffic_card: Mapped['TTrafficCard'] = relationship('TTrafficCard', back_populates='t_era_task')


class TEraVideo(Base):
    __tablename__ = 't_era_video'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], name='FK_era_video_t_traffic_card'),
        Index('FK_era_video_t_traffic_card', 'traffic_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer)
    poolList = mapped_column(JSON)
    topic_id = mapped_column(Integer)
    topic_name = mapped_column(String(50))
    videoSource_id = mapped_column(String(50))

    traffic_card: Mapped[Optional['TTrafficCard']] = relationship('TTrafficCard', back_populates='t_era_video')


class TFunctionalCard(Base):
    __tablename__ = 't_functional_card'
    __table_args__ = (
        ForeignKeyConstraint(['traffic_card_id'], ['t_traffic_card.id'], ondelete='SET NULL', name='t_functional_card_ibfk_1'),
        Index('t_functional_card_ibfk_1', 'traffic_card_id')
    )

    id = mapped_column(Integer, primary_key=True)
    traffic_card_id = mapped_column(Integer)
    json_data = mapped_column(JSON)

    traffic_card: Mapped[Optional['TTrafficCard']] = relationship('TTrafficCard', back_populates='t_functional_card')
    t_capsule: Mapped[List['TCapsule']] = relationship('TCapsule', uselist=True, back_populates='functional_card')
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
    head_img_url = mapped_column(String(255))
    head_img_backcolor = mapped_column(VARCHAR(16))
    topic_item_id = mapped_column(Integer)
    topic_creator_id = mapped_column(BigInteger, comment='如果是null代表可能是系统发布的话题，热议类新闻等内容，不算uid')

    topic_creator: Mapped[Optional['TTopicCreator']] = relationship('TTopicCreator', back_populates='t_top_details')
    topic_item: Mapped[Optional['TTopicItem']] = relationship('TTopicItem', back_populates='t_top_details')
    t_topic: Mapped[List['TTopic']] = relationship('TTopic', uselist=True, back_populates='topic_detail')


class TCapsule(Base):
    __tablename__ = 't_capsule'
    __table_args__ = (
        ForeignKeyConstraint(['functional_card_id'], ['t_functional_card.id'], name='FK_t_capsule_t_functional_card'),
        Index('FK_t_capsule_t_functional_card', 'functional_card_id')
    )

    pk = mapped_column(Integer, primary_key=True)
    functional_card_id = mapped_column(Integer, nullable=False)
    name = mapped_column(String(50), nullable=False)
    jump_url = mapped_column(String(255), nullable=False)
    icon_url = mapped_column(String(255), nullable=False)

    functional_card: Mapped['TFunctionalCard'] = relationship('TFunctionalCard', back_populates='t_capsule')


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
