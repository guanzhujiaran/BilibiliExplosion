from typing import List, Optional

from sqlalchemy import BigInteger, Column, Computed, DECIMAL, DateTime, ForeignKeyConstraint, Index, Integer, JSON, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class CrawlTaskProgress(Base):
    __tablename__ = 'crawl_task_progress'
    __table_args__ = (
        Index('udx_task_key', 'first_category_id', 'second_category_id', unique=True),
    )

    id = mapped_column(BigInteger, primary_key=True)
    first_category_id = mapped_column(Integer, nullable=False)
    second_category_id = mapped_column(Integer, nullable=False)
    last_page_num = mapped_column(Integer, server_default=text("'1'"))
    is_finished = mapped_column(TINYINT, server_default=text("'0'"))
    created_at = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))


class GroupingInfo(Base):
    __tablename__ = 'grouping_info'
    __table_args__ = (
        Index('groupingId', 'groupingId', unique=True),
    )

    pk = mapped_column(BigInteger, primary_key=True)
    level = mapped_column(TINYINT, nullable=False)
    groupingId = mapped_column(VARCHAR(50))
    groupingIdInt = mapped_column(Integer, Computed('(cast(`groupingId` as signed))', persisted=True))
    image = mapped_column(VARCHAR(1000))
    navigationId = mapped_column(VARCHAR(50))
    navigationIdInt = mapped_column(Integer, Computed('(cast(`navigationId` as signed))', persisted=True))
    storeId = mapped_column(VARCHAR(50))
    storeIdInt = mapped_column(Integer, Computed('(cast(`storeId` as signed))', persisted=True))
    title = mapped_column(VARCHAR(50))
    children = mapped_column(JSON)


class SpuInfo(Base):
    __tablename__ = 'spu_info'

    spu_id = mapped_column(String(50), primary_key=True, comment='SPU ID')
    title = mapped_column(String(255), nullable=False)
    brand_id = mapped_column(String(50))
    sub_title = mapped_column(Text)
    image = mapped_column(String(512))
    is_available = mapped_column(TINYINT(1), server_default=text("'1'"))
    is_serial = mapped_column(TINYINT(1))
    serial_id = mapped_column(String(50))
    series_id = mapped_column(String(50))
    delivery_method = mapped_column(String(50))
    delivery_attr = mapped_column(Integer)
    store_id = mapped_column(String(50))
    vender_code = mapped_column(String(50))
    master_biz_type = mapped_column(Integer)
    vice_biz_type = mapped_column(Integer)
    host_item_id = mapped_column(String(50))
    exclusive_spu = mapped_column(TINYINT(1))
    only_store_sale = mapped_column(TINYINT(1))
    has_video = mapped_column(TINYINT(1))
    is_global_direct_purchase = mapped_column(TINYINT(1))
    is_import = mapped_column(TINYINT(1))
    is_show_x_plus_tag = mapped_column(TINYINT(1))
    is_store_extent = mapped_column(TINYINT(1))
    available_stores = mapped_column(JSON)
    city_codes = mapped_column(JSON)
    give_spu_list = mapped_column(JSON)
    limit_info = mapped_column(JSON)
    belt_info = mapped_column(JSON)
    spec_info = mapped_column(JSON)
    spec_list = mapped_column(JSON)
    spu_spec_info = mapped_column(JSON)
    zone_type_list = mapped_column(JSON)
    category_outer_service = mapped_column(JSON)
    common_outer_service = mapped_column(JSON)
    created_at = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    update_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='最后更新时间')

    spu_category: Mapped[List['SpuCategory']] = relationship('SpuCategory', uselist=True, back_populates='spu')
    spu_new_tag_info: Mapped[List['SpuNewTagInfo']] = relationship('SpuNewTagInfo', uselist=True, back_populates='spu')
    spu_price_info: Mapped[List['SpuPriceInfo']] = relationship('SpuPriceInfo', uselist=True, back_populates='spu')
    spu_tag_info: Mapped[List['SpuTagInfo']] = relationship('SpuTagInfo', uselist=True, back_populates='spu')
    spu_video_info: Mapped[List['SpuVideoInfo']] = relationship('SpuVideoInfo', uselist=True, back_populates='spu')


class SpuCategory(Base):
    __tablename__ = 'spu_category'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_category_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    id = mapped_column(BigInteger, primary_key=True)
    category_id = mapped_column(String(50), nullable=False)
    spu_id = mapped_column(String(50))

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_category')


class SpuNewTagInfo(Base):
    __tablename__ = 'spu_new_tag_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_new_tag_info_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    id = mapped_column(BigInteger, primary_key=True)
    spu_id = mapped_column(String(50))
    begin_time = mapped_column(BigInteger)
    logo_image_cn = mapped_column(String(512))
    logo_image_en = mapped_column(String(512))
    logo_image_zh_cn = mapped_column(String(512))
    logo_image_wide = mapped_column(Integer)
    logo_image_high = mapped_column(Integer)
    place_type = mapped_column(Integer)
    priority_value = mapped_column(Integer)
    promotion_tag = mapped_column(String(255))
    style_code = mapped_column(String(50))
    style_type = mapped_column(Integer)
    tag_manage_id = mapped_column(String(50))
    tag_mark = mapped_column(String(255))
    tag_place = mapped_column(Integer)
    tag_sort_type = mapped_column(Integer)
    tag_style_id = mapped_column(String(50))
    title = mapped_column(String(255))

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_new_tag_info')


class SpuPriceInfo(Base):
    __tablename__ = 'spu_price_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_price_info_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    id = mapped_column(BigInteger, primary_key=True)
    spu_id = mapped_column(String(50))
    price = mapped_column(DECIMAL(10, 2))
    price_type = mapped_column(Integer)
    price_type_name = mapped_column(String(255))

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_price_info')


class SpuStockInfo(SpuInfo):
    __tablename__ = 'spu_stock_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_stock_info_ibfk_1'),
    )

    spu_id = mapped_column(String(50), primary_key=True)
    safe_stock_quantity = mapped_column(Integer)
    sold_quantity = mapped_column(Integer)
    stock_quantity = mapped_column(Integer)


class SpuTagInfo(Base):
    __tablename__ = 'spu_tag_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_tag_info_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    id = mapped_column(BigInteger, primary_key=True)
    spu_id = mapped_column(String(50))
    tag_id = mapped_column(String(50))
    title = mapped_column(String(255))
    tag_mark = mapped_column(String(255))
    tag_place = mapped_column(Integer)
    tag_sort_type = mapped_column(Integer)
    priority_value = mapped_column(Integer)
    promotion_tag = mapped_column(String(255))
    begin_time = mapped_column(BigInteger)
    update_time = mapped_column(DateTime)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_tag_info')


class SpuVideoInfo(Base):
    __tablename__ = 'spu_video_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spu_id'], ondelete='CASCADE', name='spu_video_info_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    id = mapped_column(BigInteger, primary_key=True)
    spu_id = mapped_column(String(50))
    video_url = mapped_column(String(512))
    video_cover = mapped_column(String(512))
    duration = mapped_column(Integer)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_video_info')
