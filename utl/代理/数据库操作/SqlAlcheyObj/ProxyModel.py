from sqlalchemy import Column, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class ProxyTab(Base):
    __tablename__ = 'proxy_tab'

    proxy = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default=text('0'))
    update_ts = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    proxy_id = Column(Integer, primary_key=True)
    add_ts = Column(Integer)
    success_times = Column(Integer, server_default=text('0'))
    zhihu_status = Column(Integer, server_default=text('0'))

    def to_dict(self):
        return {
            'proxy': self.proxy,
            'status': self.status,
            'update_ts': self.update_ts,
            'score': self.score,
            'proxy_id': self.proxy_id,
            'add_ts': self.add_ts,
            'success_times': self.success_times,
            'zhihu_status': self.zhihu_status,
        }


class SDGrpcStat(ProxyTab):
    __tablename__ = 'SD_grpc_stat'

    proxy_id = Column(ForeignKey('proxy_tab.proxy_id'), primary_key=True)
    sd_status = Column('status', Integer, server_default=text('0'), )
    sd_update_ts = Column('update_ts', Integer)
    sd_success_times = Column('success_times', Integer, server_default=text('0'))
    sd_score = Column('score', Integer, server_default=text('50'))

    proxy_tab = relationship('ProxyTab', backref='sd_grpc_stat')

    def to_dict(self):
        return {
            'proxy': self.proxy,
            'status': self.sd_status,
            'update_ts': self.sd_update_ts,
            'score': self.sd_score,
            'proxy_id': self.proxy_id,
            'add_ts': self.add_ts,
            'success_times': self.sd_success_times,
            'zhihu_status': self.zhihu_status,
        }