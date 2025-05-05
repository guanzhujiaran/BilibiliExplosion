from typing import List

from sqlalchemy import Column, Computed, ForeignKeyConstraint, Index, Integer, JSON, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class ProxyTab(Base):
    __tablename__ = 'proxy_tab'
    __table_args__ = (
        Index('computed_proxy_str', 'computed_proxy_str'),
        Index('proxy_id', 'proxy_id', unique=True),
        Index('刷新代理索引', 'status', 'score', 'success_times', 'update_ts'),
        Index('获取可用代理索引', 'status', 'score', 'update_ts'),
        Index('覆盖索引', 'proxy_id', 'status', 'update_ts', 'score', 'add_ts', 'success_times', 'zhihu_status')
    )

    proxy_id = mapped_column(Integer, primary_key=True)
    proxy = mapped_column(JSON, nullable=False)
    status = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    update_ts = mapped_column(Integer, nullable=False)
    score = mapped_column(Integer, nullable=False)
    add_ts = mapped_column(Integer)
    success_times = mapped_column(Integer, server_default=text("'0'"))
    zhihu_status = mapped_column(Integer, server_default=text("'0'"))
    computed_proxy_str = mapped_column(String(255), Computed("(json_unquote(json_extract(`proxy`,concat(_utf8mb4'$.',json_unquote(json_extract(json_keys(`proxy`),_utf8mb4'$[0]'))))))", persisted=True))

    available_proxy: Mapped[List['AvailableProxy']] = relationship('AvailableProxy', uselist=True, back_populates='proxy_tab')


class AvailableProxy(Base):
    __tablename__ = 'available_proxy'
    __table_args__ = (
        ForeignKeyConstraint(['proxy_tab_id'], ['proxy_tab.proxy_id'], name='FK_available_proxy_proxy_tab'),
        Index('proxy_tab_id', 'proxy_tab_id', unique=True)
    )

    proxy_tab_id = mapped_column(Integer, nullable=False)
    pk = mapped_column(Integer, primary_key=True)
    ip = mapped_column(String(1024))
    counter = mapped_column(Integer)
    max_counter_ts = mapped_column(TIMESTAMP)
    resp_code = mapped_column(TINYINT)
    available = mapped_column(TINYINT(1))
    latest_352_ts = mapped_column(TIMESTAMP)
    latest_used_ts = mapped_column(TIMESTAMP)

    proxy_tab: Mapped['ProxyTab'] = relationship('ProxyTab', back_populates='available_proxy')
