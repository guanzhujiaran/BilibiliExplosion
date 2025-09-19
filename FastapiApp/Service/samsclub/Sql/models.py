from typing import List, Optional

from sqlalchemy import BigInteger, Column, Computed, DateTime, Double, ForeignKeyConstraint, Index, Integer, JSON, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TEXT, TINYINT, VARCHAR
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
    parentGroupingId = mapped_column(Integer)
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
    __table_args__ = (
        Index('title', 'title', 'update_time', 'spuId', 'create_time'),
    )

    spuId = mapped_column(VARCHAR(50), primary_key=True, comment='SPU ID')
    title = mapped_column(String(255), nullable=False)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    brandId = mapped_column(VARCHAR(50))
    subTitle = mapped_column(TEXT)
    image = mapped_column(String(512))
    isAvailable = mapped_column(TINYINT(1))
    isSerial = mapped_column(TINYINT(1))
    serialId = mapped_column(VARCHAR(50))
    seriesId = mapped_column(VARCHAR(50))
    deliveryMethod = mapped_column(VARCHAR(50))
    deliveryAttr = mapped_column(Integer)
    storeId = mapped_column(VARCHAR(50))
    venderCode = mapped_column(VARCHAR(50))
    masterBizType = mapped_column(Integer)
    viceBizType = mapped_column(Integer)
    hostItemId = mapped_column(VARCHAR(50))
    exclusiveSpu = mapped_column(TINYINT(1))
    onlyStoreSale = mapped_column(TINYINT(1))
    hasVideo = mapped_column(TINYINT(1))
    isGlobalDirectPurchase = mapped_column(TINYINT(1))
    isImport = mapped_column(TINYINT(1))
    isShowXPlusTag = mapped_column(TINYINT(1))
    isStoreExtent = mapped_column(TINYINT(1))
    availableStores = mapped_column(JSON)
    cityCodes = mapped_column(JSON)
    giveSpuList = mapped_column(JSON)
    limitInfo = mapped_column(JSON)
    beltInfo = mapped_column(JSON)
    specInfo = mapped_column(JSON)
    specList = mapped_column(JSON)
    spuSpecInfo = mapped_column(JSON)
    zoneTypeList = mapped_column(JSON)
    categoryOuterService = mapped_column(JSON)
    smallPackagePriceDisplay = mapped_column(String(255))
    commonOuterService = mapped_column(JSON)
    unknow_field = mapped_column(JSON)
    onlyBarSale = mapped_column(TINYINT(1), comment='是否只在餐吧销售')
    arrivalEndTimeDesc = mapped_column(Text)
    attrGroupInfo = mapped_column(JSON)
    attrInfo = mapped_column(JSON)
    complianceInfo = mapped_column(JSON)
    couponContentList = mapped_column(JSON)
    couponList = mapped_column(JSON)
    customTabList = mapped_column(JSON)
    deliveryCapacityCountList = mapped_column(JSON)
    desc = mapped_column(Text)
    descVideo = mapped_column(JSON)
    detailVideos = mapped_column(JSON)
    extendedWarrantyList = mapped_column(JSON)
    favorite = mapped_column(TINYINT(1))
    giveaway = mapped_column(TINYINT(1))
    imageSizeThreeFour = mapped_column(JSON)
    images = mapped_column(JSON)
    intro = mapped_column(Text)
    isAllowDelivery = mapped_column(TINYINT(1))
    isCollectOrder = mapped_column(Integer)
    isCompare = mapped_column(TINYINT(1))
    isCrabCard = mapped_column(TINYINT(1))
    isGlobalOwnPickUp = mapped_column(TINYINT(1))
    isGovSpu = mapped_column(TINYINT(1))
    isPutOnSale = mapped_column(TINYINT(1), comment='false 就代表下架了')
    isStoreAvailable = mapped_column(TINYINT(1))
    isTicket = mapped_column(TINYINT(1))
    netWeight = mapped_column(Double(asdecimal=True))
    preSellList = mapped_column(JSON)
    promotionDetailList = mapped_column(JSON)
    promotionList = mapped_column(JSON)
    serviceInfo = mapped_column(JSON)
    sevenDaysReturn = mapped_column(TINYINT(1))
    spuExtDTO = mapped_column(JSON)
    standardForIntactGoodsUrl = mapped_column(Text)
    temperature = mapped_column(Integer)
    valuable = mapped_column(TINYINT(1))
    weight = mapped_column(Double(asdecimal=True))
    purchaseLimitText = mapped_column(Text)
    purchaseLimitMinNum = mapped_column(Integer)
    globalShoppingTaxRateExplain = mapped_column(Text)
    hostItem = mapped_column(Text)

    spu_category: Mapped[List['SpuCategory']] = relationship('SpuCategory', uselist=True, back_populates='spu')
    spu_new_tag_info: Mapped[List['SpuNewTagInfo']] = relationship('SpuNewTagInfo', uselist=True, back_populates='spu')
    spu_price_info: Mapped[List['SpuPriceInfo']] = relationship('SpuPriceInfo', uselist=True, back_populates='spu')
    spu_stock_info: Mapped[List['SpuStockInfo']] = relationship('SpuStockInfo', uselist=True, back_populates='spu')
    spu_tag_info: Mapped[List['SpuTagInfo']] = relationship('SpuTagInfo', uselist=True, back_populates='spu')
    spu_video_info: Mapped[List['SpuVideoInfo']] = relationship('SpuVideoInfo', uselist=True, back_populates='spu')


class SpuCategory(Base):
    __tablename__ = 'spu_category'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], ondelete='CASCADE', name='spu_category_ibfk_1'),
        Index('create_time', 'create_time', 'update_time', 'categoryId', 'spu_id', 'pk'),
        Index('uq_spuId_categoryId', 'spu_id', 'categoryId', unique=True)
    )

    pk = mapped_column(BigInteger, primary_key=True)
    categoryId = mapped_column(VARCHAR(50), nullable=False)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    spu_id = mapped_column(String(50))

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_category')


class SpuNewTagInfo(Base):
    __tablename__ = 'spu_new_tag_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], ondelete='CASCADE', name='spu_new_tag_info_ibfk_1'),
        Index('title', 'title', 'spu_id'),
        Index('uq_spuId_tagManageId', 'spu_id', 'tagManageId', unique=True)
    )

    pk = mapped_column(BigInteger, primary_key=True)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    spu_id = mapped_column(String(50))
    beginTime = mapped_column(BigInteger)
    endTime = mapped_column(BigInteger)
    originalPrice = mapped_column(String(50))
    promotionPrice = mapped_column(String(50))
    savedMoney = mapped_column(Integer)
    titleCn = mapped_column(String(50))
    logoImageCn = mapped_column(VARCHAR(512))
    logoImageEn = mapped_column(VARCHAR(512))
    logoImageZhCn = mapped_column(VARCHAR(512))
    logoImageWide = mapped_column(Integer)
    logoImageHigh = mapped_column(Integer)
    placeType = mapped_column(Integer)
    priorityValue = mapped_column(Integer)
    promotionTag = mapped_column(VARCHAR(255))
    styleCode = mapped_column(VARCHAR(50))
    styleType = mapped_column(Integer)
    tagManageId = mapped_column(VARCHAR(50))
    tagMark = mapped_column(VARCHAR(255))
    tagPlace = mapped_column(Integer)
    tagSortType = mapped_column(Integer)
    tagStyleId = mapped_column(VARCHAR(50))
    title = mapped_column(VARCHAR(255))
    id = mapped_column(String(50))
    unknow_field = mapped_column(JSON)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_new_tag_info')


class SpuPriceInfo(Base):
    __tablename__ = 'spu_price_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], name='FK_spu_price_info_spu_info'),
        Index('spu_id', 'spu_id', 'price', 'priceType', 'update_time', 'create_time')
    )

    pk = mapped_column(BigInteger, primary_key=True)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    spu_id = mapped_column(String(50))
    price = mapped_column(Integer)
    priceType = mapped_column(Integer)
    priceTypeName = mapped_column(VARCHAR(255))
    unknow_field = mapped_column(JSON)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_price_info')


class SpuStockInfo(Base):
    __tablename__ = 'spu_stock_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], ondelete='CASCADE', name='spu_stock_info_ibfk_1'),
        Index('spu_id', 'spu_id', unique=True)
    )

    pk = mapped_column(BigInteger, primary_key=True)
    spu_id = mapped_column(String(50), nullable=False)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    safeStockQuantity = mapped_column(Integer)
    soldQuantity = mapped_column(Integer)
    stockQuantity = mapped_column(Integer)
    unknow_field = mapped_column(JSON)

    spu: Mapped['SpuInfo'] = relationship('SpuInfo', back_populates='spu_stock_info')


class SpuTagInfo(Base):
    __tablename__ = 'spu_tag_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], ondelete='CASCADE', name='spu_tag_info_ibfk_1'),
        Index('spu_id_tag_Id', 'spu_id', 'id', unique=True),
        Index('spu_id_tag_mark', 'spu_id', 'tagMark', unique=True)
    )

    pk = mapped_column(BigInteger, primary_key=True)
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    spu_id = mapped_column(String(50))
    id = mapped_column(VARCHAR(50))
    title = mapped_column(VARCHAR(1024))
    tagMark = mapped_column(VARCHAR(255))
    tagPlace = mapped_column(Integer)
    tagSortType = mapped_column(Integer)
    priorityValue = mapped_column(Integer)
    promotionTag = mapped_column(VARCHAR(255))
    beginTime = mapped_column(BigInteger)
    unknow_field = mapped_column(JSON)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_tag_info')


class SpuVideoInfo(Base):
    __tablename__ = 'spu_video_info'
    __table_args__ = (
        ForeignKeyConstraint(['spu_id'], ['spu_info.spuId'], ondelete='CASCADE', name='spu_video_info_ibfk_1'),
        Index('spu_id', 'spu_id')
    )

    pk = mapped_column(BigInteger, primary_key=True)
    create_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = mapped_column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    spu_id = mapped_column(String(50))
    videoUrl = mapped_column(VARCHAR(512))
    videoCover = mapped_column(VARCHAR(512))
    duration = mapped_column(Integer)
    unknow_field = mapped_column(JSON)

    spu: Mapped[Optional['SpuInfo']] = relationship('SpuInfo', back_populates='spu_video_info')
