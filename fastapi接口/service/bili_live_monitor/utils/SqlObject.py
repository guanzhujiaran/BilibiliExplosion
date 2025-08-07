import os

from sqlalchemy import Integer, String, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy import create_engine

SQLITE_URI = fr'sqlite:///H:\liveLotMonitorDB\Bili_live_database.db''?check_same_thread=False'

engine = create_engine(SQLITE_URI, echo=True)
DbSession = sessionmaker(bind=engine)
db_session = DbSession()

Base = declarative_base()


class Server_Data(Base):
    __tablename__ = 'server_data'
    pk = mapped_column(Integer,primary_key=True,auto_increment=True)
    id = mapped_column('id', Integer, unique=False)
    created_at = mapped_column(DateTime)
    data = mapped_column(String)
    ip = mapped_column(String)
    room_id = mapped_column(Integer)
    updated_at = mapped_column(DateTime)
    anchor: Mapped["anchor"] = relationship(back_populates="Server_Data")
    popularity_red_pocket: Mapped["popularity_red_pocket"] = relationship(back_populates="Server_Data")

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
class anchor(Base):
    __tablename__ = 'anchor'
    __table_args__ = (UniqueConstraint("server_data_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_data_id = mapped_column(ForeignKey('server_data.id'))
    room_id = mapped_column(Integer)
    status = mapped_column(Integer)
    asset_icon = mapped_column(String)
    award_name = mapped_column(String)
    award_num = mapped_column(Integer)
    award_image = mapped_column(String)
    danmu = mapped_column(String)
    time = mapped_column(Integer)
    current_time = mapped_column(Integer)
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
    server_data: Mapped["Server_Data"] = relationship(back_populates='anchor')
    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

class popularity_red_pocket(Base):
    __tablename__ = 'popularity_red_pocket'
    __table_args__ = (UniqueConstraint("lot_id"),)
    id = mapped_column(Integer, primary_key=True,autoincrement=True)
    lot_id = mapped_column(ForeignKey('server_data.id'))
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
    current_time = mapped_column(Integer)
    lot_status = mapped_column(Integer)
    h5_url = mapped_column(String)
    user_status = mapped_column(Integer)
    lot_config_id = mapped_column(Integer)
    total_price = mapped_column(Integer)
    wait_num = mapped_column(Integer)
    server_data: Mapped["Server_Data"] = relationship(back_populates='popularity_red_pocket')
    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

class room_uid(Base):
    __tablename__ = 't_room_uid'
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id=mapped_column(Integer)
    uid=mapped_column(Integer)

if __name__ == '__main__':
    # 创建数据库命令
    # Base.metadata.create_all(checkfirst=True, bind=engine)
    os.system(f'sqlacodegen_v2 {SQLITE_URI} > models.py')

