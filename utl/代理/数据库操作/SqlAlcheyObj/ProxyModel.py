from sqlalchemy import Column, Index, Integer, JSON, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy.orm.base import Mapped

from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict

Base = declarative_base()


class ProxyTab(Base):
    __tablename__ = 'proxy_tab'
    __table_args__ = (
        Index('proxy_id', 'proxy_id', unique=True),
        Index('刷新代理索引', 'status', 'score', 'success_times', 'update_ts'),
        Index('获取可用代理索引', 'status', 'score', 'update_ts'),
        Index('覆盖索引', 'proxy_id', 'status', 'update_ts', 'score', 'add_ts', 'success_times', 'zhihu_status')
    )

    proxy_id = mapped_column(Integer, primary_key=True)
    proxy = mapped_column(JSON, nullable=False)
    status = mapped_column(Integer, nullable=False, server_default=text("'0'"))  # 只允许-412，不存在-352
    update_ts = mapped_column(Integer, nullable=False)
    score = mapped_column(Integer, nullable=False)
    add_ts = mapped_column(Integer)
    success_times = mapped_column(Integer, server_default=text("'0'"))
    zhihu_status = mapped_column(Integer, server_default=text("'0'"))
