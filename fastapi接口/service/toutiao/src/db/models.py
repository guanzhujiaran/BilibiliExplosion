from sqlalchemy import Column, Integer, LargeBinary
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class TFEEDDATA(Base):
    __tablename__ = 'T_FEEDDATA'

    pk = mapped_column(Integer, primary_key=True)
    id = mapped_column(Integer, unique=True)
    publish_time = mapped_column(Integer)
    zippedData = mapped_column(LargeBinary)
