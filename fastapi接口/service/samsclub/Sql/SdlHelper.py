from typing import Optional, List, TypeVar

import sqlalchemy
import strawberry
from sqlalchemy import select, asc, desc, func
from strawberry import Info
from strawberry.fastapi import GraphQLRouter
from strawberry_sqlalchemy_mapper import StrawberrySQLAlchemyMapper

from .SqlHelper import sql_helper
from .models import SpuInfo, SpuCategory, SpuNewTagInfo, SpuPriceInfo, SpuStockInfo, SpuTagInfo, SpuVideoInfo

# 初始化映射器
mapper = StrawberrySQLAlchemyMapper()


async def get_context():
    async with sql_helper.async_session() as db:
        yield {"db": db}


@mapper.type(SpuInfo)
class SpuInfoType:
    __exclude__ = ['spu_category', 'spu_new_tag_info', 'spu_price_info', 'spu_stock_info', 'spu_tag_info',
                   'spu_video_info']

    @strawberry.field
    async def latestPriceInfo(self, info: Info) -> Optional["SpuPriceInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuPriceInfo)
            .where(SpuPriceInfo.spu_id == self.spuId)
            .order_by(SpuPriceInfo.pk.desc())
            .limit(1)
        )
        return result.scalars().first()

    @strawberry.field
    async def categories(self, info: Info) -> List["SpuCategoryType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuCategory)
            .where(SpuCategory.spu_id == self.spuId)
            .order_by(SpuCategory.pk.desc())
        )
        return result.scalars().all()

    @strawberry.field
    async def newTagInfos(self, info: Info) -> List["SpuNewTagInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuNewTagInfo)
            .where(SpuNewTagInfo.spu_id == self.spuId)
            .order_by(SpuNewTagInfo.pk.desc())
        )
        return result.scalars().all()

    @strawberry.field
    async def tagInfos(self, info: Info) -> List["SpuTagInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuTagInfo)
            .where(SpuTagInfo.spu_id == self.spuId)
            .order_by(SpuTagInfo.pk.desc())
        )
        return result.scalars().all()

    @strawberry.field
    async def videoInfos(self, info: Info) -> List["SpuVideoInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuVideoInfo)
            .where(SpuVideoInfo.spu_id == self.spuId)
            .order_by(SpuVideoInfo.pk.desc())
        )
        return result.scalars().all()

    @strawberry.field
    async def stockInfo(self, info: Info) -> Optional["SpuStockInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuStockInfo)
            .where(SpuStockInfo.spu_id == self.spuId)
            .order_by(SpuStockInfo.pk.desc())
        )
        return result.scalars().first()

    @strawberry.field
    async def pricediff(self,info:Info):
        db = info.context['db']
        return (await db.execute(
            select(SpuPriceInfo.price)
            .where(SpuPriceInfo.spu_id == self.spuId)
            .order_by(SpuPriceInfo.pk.desc())
            .limit(1)
        )).scalars().first() - (await db.execute(
            select(SpuPriceInfo.price)
            .where(SpuPriceInfo.spu_id == self.spuId)
            .order_by(SpuPriceInfo.pk.asc())
            .limit(1)
        )).scalars().first()

@mapper.type(SpuPriceInfo)
class SpuPriceInfoType:
    __exclude__ = ["spu"]


@mapper.type(SpuCategory)
class SpuCategoryType:
    __exclude__ = ["spu"]


@mapper.type(SpuNewTagInfo)
class SpuNewTagInfoType:
    __exclude__ = ["spu"]

    @strawberry.field
    async def tagMarkGroup(self, info: Info) -> List[str]:
        stmt = select(SpuNewTagInfo.tagMark).group_by(SpuNewTagInfo.tagMark)
        db = info.context['db']
        result = await db.execute(stmt)
        return result.scalars().all()


@mapper.type(SpuStockInfo)
class SpuStockInfoType:
    __exclude__ = ["spu"]


@mapper.type(SpuTagInfo)
class SpuTagInfoType:
    __exclude__ = ["spu"]


@mapper.type(SpuVideoInfo)
class SpuVideoInfoType:
    __exclude__ = ["spu"]


# 必须调用 finalize 才会注册所有类型
mapper.finalize()


@strawberry.type
class PageInfoType:
    total: int
    page: int
    page_size: int
    has_next_page: bool


Item = TypeVar('Item')


@strawberry.type
class SpuInfoPaginator[Item]:
    items: List[Item]
    page_info: PageInfoType


@strawberry.type
class Query:
    @strawberry.field
    async def getSpuInfo(self, spuId: str, info: Info) -> SpuInfoType:
        db = info.context['db']
        result = await db.execute(
            select(SpuInfo).where(SpuInfo.spuId == spuId)
        )
        return result.scalars().first()

    @strawberry.field
    async def getSpuInfos(
            self,
            info: Info,
            pn: int = 1,
            ps: int = 10,
            spu_new_tag_tag_mark: str | None = None,
            spu_info_title: str | None = None,
            spu_info_update_asc: bool = True,
            spu_price_asc: bool = True,
            spu_price_min: int | None = None,
            spu_price_max: int | None = None,
    ) -> SpuInfoPaginator[SpuInfoType]:
        # 获取共享 session
        session = info.context["db"]

        # 基础查询语句
        stmt = select(SpuInfo)

        # 标签过滤
        if spu_new_tag_tag_mark:
            stmt = stmt.join(SpuNewTagInfo).where(SpuNewTagInfo.tagMark == spu_new_tag_tag_mark)

        # 标题模糊匹配
        if spu_info_title:
            stmt = stmt.where(SpuInfo.title.ilike(f"%{spu_info_title}%"))

        # 子查询：获取最新价格
        latest_price_subquery = (
            select(SpuPriceInfo.price)
            .where(SpuPriceInfo.spu_id == SpuInfo.spuId)
            .order_by(SpuPriceInfo.pk.desc())
            .limit(1)
            .correlate(SpuInfo)
            .scalar_subquery()
        )

        # 如果有价格筛选或排序需求，则添加子查询字段
        need_price_filter = any([
            spu_price_min is not None,
            spu_price_max is not None,
            spu_price_asc is not None
        ])
        if need_price_filter:
            stmt = stmt.add_columns(latest_price_subquery.label("latest_price"))

        # 提取 where 条件（SQLAlchemy 2.x）
        where_clauses = []
        if stmt.whereclause is not None:
            if isinstance(stmt.whereclause, sqlalchemy.sql.elements.BinaryExpression):
                where_clauses.append(stmt.whereclause)
            else:
                where_clauses.extend(stmt.whereclause.clauses)

        # 构建 count 查询
        count_query = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_query)
        total = int(total_result.scalar_one())

        # 分页逻辑
        offset = (pn - 1) * ps
        if offset >= total:
            return SpuInfoPaginator(
                items=[],
                page_info=PageInfoType(
                    total=total,
                    page=pn,
                    page_size=ps,
                    has_next_page=False
                )
            )

        # 排序逻辑
        order_columns = []

        if need_price_filter:
            price_order_func = asc if spu_price_asc else desc
            order_columns.append(price_order_func("latest_price"))

        update_time_order_func = asc if spu_info_update_asc else desc
        order_columns.append(update_time_order_func(SpuInfo.update_time))

        if order_columns:
            stmt = stmt.order_by(*order_columns)

        # 分页
        paginated_stmt = stmt.limit(ps).offset(offset)

        try:
            result = await session.execute(paginated_stmt)
            items = [row[0] for row in result.unique().all()]
        except Exception as e:
            # 异常处理
            print(f"Error executing query: {e}")
            return SpuInfoPaginator(
                items=[],
                page_info=PageInfoType(
                    total=0,
                    page=pn,
                    page_size=ps,
                    has_next_page=False
                )
            )

        return SpuInfoPaginator(
            items=items,
            page_info=PageInfoType(
                total=total,
                page=pn,
                page_size=ps,
                has_next_page=(offset + ps) < total
            )
        )


schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
