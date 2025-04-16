from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class ServerData(Base):
    __tablename__ = 'server_data'

    pk = mapped_column(Integer, primary_key=True)
    id = mapped_column(Integer)
    created_at = mapped_column(DateTime)
    data = mapped_column(String)
    ip = mapped_column(String)
    room_id = mapped_column(Integer)
    updated_at = mapped_column(DateTime)

    anchor: Mapped['Anchor'] = relationship('Anchor', uselist=False, back_populates='server_data')
    popularity_red_pocket: Mapped['PopularityRedPocket'] = relationship('PopularityRedPocket', uselist=False, foreign_keys='[PopularityRedPocket.lot_id]', back_populates='lot')
    popularity_red_pocket_: Mapped[List['PopularityRedPocket']] = relationship('PopularityRedPocket', uselist=True, foreign_keys='[PopularityRedPocket.room_id]', back_populates='room')


class TRoomUid(Base):
    __tablename__ = 't_room_uid'

    id = mapped_column(Integer, primary_key=True)
    room_id = mapped_column(Integer)
    uid = mapped_column(Integer)


class Anchor(Base):
    __tablename__ = 'anchor'

    id = mapped_column(Integer, primary_key=True)
    server_data_id = mapped_column(ForeignKey('server_data.id'), unique=True)
    room_id = mapped_column(Integer)
    status = mapped_column(Integer)
    asset_icon = mapped_column(String)
    award_name = mapped_column(String)
    award_num = mapped_column(Integer)
    award_image = mapped_column(String)
    danmu = mapped_column(String)
    time = mapped_column(Integer)
    current_ts = mapped_column(Integer)
    join_type = mapped_column(Integer)
    require_type = mapped_column(Integer)
    require_value = mapped_column(Integer)
    require_text = mapped_column(String)
    gift_id = mapped_column(Integer)
    gift_name = mapped_column(String)
    gift_num = mapped_column(Integer)
    gift_price = mapped_column(Integer)
    cur_gift_num = mapped_column(Integer)
    goaway_time = mapped_column(Integer)
    award_users = mapped_column(JSON)
    show_panel = mapped_column(Integer)
    url = mapped_column(String)
    lot_status = mapped_column(Integer)
    web_url = mapped_column(String)
    send_gift_ensure = mapped_column(Integer)
    goods_id = mapped_column(Integer)
    award_type = mapped_column(Integer)
    award_price_text = mapped_column(Integer)
    ruid = mapped_column(Integer)
    asset_icon_webp = mapped_column(String)
    danmu_type = mapped_column(Integer)
    danmu_new = mapped_column(JSON)

    server_data: Mapped[Optional['ServerData']] = relationship('ServerData', back_populates='anchor')


class PopularityRedPocket(Base):
    __tablename__ = 'popularity_red_pocket'

    id = mapped_column(Integer, primary_key=True)
    lot_id = mapped_column(ForeignKey('server_data.id'), unique=True)
    room_id = mapped_column(ForeignKey('server_data.room_id'))
    sender_uid = mapped_column(Integer)
    sender_face = mapped_column(String)
    join_requirement = mapped_column(Integer)
    danmu = mapped_column(String)
    awards = mapped_column(JSON)
    start_time = mapped_column(Integer)
    end_time = mapped_column(Integer)
    last_time = mapped_column(Integer)
    remove_time = mapped_column(Integer)
    replace_time = mapped_column(Integer)
    current_ts = mapped_column(Integer)
    lot_status = mapped_column(Integer)
    h5_url = mapped_column(String)
    user_status = mapped_column(Integer)
    lot_config_id = mapped_column(Integer)
    total_price = mapped_column(Integer)
    wait_num = mapped_column(Integer)

    lot: Mapped[Optional['ServerData']] = relationship('ServerData', foreign_keys=[lot_id], back_populates='popularity_red_pocket')
    room: Mapped[Optional['ServerData']] = relationship('ServerData', foreign_keys=[room_id], back_populates='popularity_red_pocket_')
    popularity_red_pocket_winner: Mapped[List['PopularityRedPocketWinner']] = relationship('PopularityRedPocketWinner', uselist=True, back_populates='lot')


class PopularityRedPocketWinner(Base):
    __tablename__ = 'popularity_red_pocket_winner'
    __table_args__ = (
        Index('idx_unique_lot_id_uid', 'lot_id', 'uid', unique=True),
    )

    pk = mapped_column(Integer, primary_key=True)
    lot_id = mapped_column(ForeignKey('popularity_red_pocket.lot_id'))
    award_big_pic = mapped_column(Text)
    award_name = mapped_column(Text)
    award_pic = mapped_column(Text)
    award_price = mapped_column(Integer)
    bag_id = mapped_column(Integer)
    gift_id = mapped_column(Integer)
    gift_num = mapped_column(Integer)
    guard_ext = mapped_column(Text)
    is_mystery = mapped_column(Integer)
    name = mapped_column(Text)
    outdate_time = mapped_column(Integer)
    uid = mapped_column(Integer)
    uinfo = mapped_column(JSON)
    use_timestamp = mapped_column(Integer)
    user_type = mapped_column(Integer)

    lot: Mapped[Optional['PopularityRedPocket']] = relationship('PopularityRedPocket', back_populates='popularity_red_pocket_winner')
