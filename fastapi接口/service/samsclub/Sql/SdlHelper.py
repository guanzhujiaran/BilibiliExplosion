from typing import Optional, List, TypeVar

import strawberry
from sqlalchemy import select, asc, desc, func, case, and_
from sqlalchemy.sql.functions import coalesce
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
    maxPriceDiff: Optional[int] = strawberry.field(default=None, description="历史最高价与历史最低价之差")
    curPriceDiff: Optional[int] = strawberry.field(default=None, description="历史最高价与当前最新价之差")
    latestPriceDiff: Optional[int] = strawberry.field(default=None, description="最新两次价格之差")

    @strawberry.field
    async def allPriceInfos(self, info: Info, limit: int = 100) -> List["SpuPriceInfoType"]:
        db = info.context['db']
        result = await db.execute(
            select(SpuPriceInfo)
            .where(SpuPriceInfo.spu_id == self.spuId)
            .limit(limit)
            .order_by(SpuPriceInfo.pk.desc())
        )
        return result.scalars().all()

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
class SpuNewTagInfoTagMarkGroupType:
    tagMark: str
    title: str


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
    async def SpuNewTagInfoTagMarkGroup(self, info: Info) -> List[SpuNewTagInfoTagMarkGroupType]:
        stmt = select(
            SpuNewTagInfo.tagMark,
            func.any_value(SpuNewTagInfo.title).label("title")
        ).group_by(SpuNewTagInfo.tagMark)
        db = info.context['db']
        result = await db.execute(stmt)
        return result.all()

    @strawberry.field
    async def getMaxPrice(self, info: Info) -> int:
        stmt = select(func.max(SpuPriceInfo.price))
        db = info.context['db']
        result = await db.execute(stmt)
        return result.scalar_one()

    # region 主查询：查询所有 SpuInfo
    @strawberry.field
    async def getSpuInfos(
            self,
            info: Info,
            pn: int = 1,
            ps: int = 10,
            spuId: int | None = None,
            spuNewTagTagMarkList: list[str] | None = None,
            spuInfoTitle: str | None = None,
            spuInfoUpdateAsc: bool | None = False,
            spuInfoCreateAsc: bool | None = False,
            priceDiffMaxAsc: bool | None = None,
            priceDiffCurAsc: bool | None = None,
            priceDiffLatestAsc: bool | None = None,
            priceAsc: bool | None = None,
            priceMin: int | None = None,
            priceMax: int | None = None,
    ) -> SpuInfoPaginator[SpuInfoType]:
        session = info.context["db"]

        # --- 步骤 1: 构建基础查询语句 (stmt) with Unconditional Price Calculations ---

        # The price calculation logic is now applied to EVERY query.
        # Use a window function to rank prices for each spu_id
        ranked_prices = select(
            SpuPriceInfo.spu_id,
            SpuPriceInfo.price,
            func.row_number().over(
                partition_by=SpuPriceInfo.spu_id,
                order_by=SpuPriceInfo.pk.desc()
            ).label("rn")
        ).subquery("ranked_prices")

        # CTE to calculate latest, previous, max, and min prices
        price_calcs_cte = select(
            ranked_prices.c.spu_id,
            func.max(case((ranked_prices.c.rn == 1, ranked_prices.c.price))).label("latest_price"),
            func.max(case((ranked_prices.c.rn == 2, ranked_prices.c.price))).label("previous_price"),
            func.max(ranked_prices.c.price).label("max_price"),
            func.min(ranked_prices.c.price).label("min_price")
        ).group_by(ranked_prices.c.spu_id).cte("price_calcs_cte")

        # Start the main statement by selecting from SpuInfo
        stmt = select(SpuInfo)

        # ALWAYS join the main query with the CTE
        # We use an outer join to ensure we don't lose SpuInfo records that have no price entries.
        stmt = stmt.join(price_calcs_cte, SpuInfo.spuId == price_calcs_cte.c.spu_id, isouter=True)

        # ALWAYS add the calculated columns to the select statement.
        # Use coalesce to handle cases with no prices (outer join) and provide default 0 values.
        stmt = stmt.add_columns(
            coalesce(price_calcs_cte.c.max_price - price_calcs_cte.c.min_price, 0).label("max_price_diff"),
            coalesce(price_calcs_cte.c.max_price - price_calcs_cte.c.latest_price, 0).label("cur_price_diff"),
            coalesce(price_calcs_cte.c.previous_price - price_calcs_cte.c.latest_price, 0).label(
                "latest_price_diff"),
            coalesce(price_calcs_cte.c.latest_price, 0).label("latest_price")
            # Also add latest_price for filtering/sorting
        )

        # --- 步骤 2: 条件性地添加其他 JOINS ---
        where_conditions = []
        if spuNewTagTagMarkList:
            stmt = stmt.join(SpuNewTagInfo, SpuInfo.spuId == SpuNewTagInfo.spu_id).distinct()
            where_conditions.append(SpuNewTagInfo.tagMark.in_(spuNewTagTagMarkList))

        # --- 步骤 3: 收集并应用 WHERE 条件 ---
        if spuId:
            where_conditions.append(SpuInfo.spuId == spuId)
        if spuInfoTitle:
            where_conditions.append(SpuInfo.title.ilike(f"%{spuInfoTitle}%"))

        # Price range filtering now works directly on the calculated `latest_price` column
        if priceMin is not None:
            where_conditions.append(price_calcs_cte.c.latest_price >= priceMin)
        if priceMax is not None:
            where_conditions.append(price_calcs_cte.c.latest_price <= priceMax)

        if where_conditions:
            stmt = stmt.where(and_(*where_conditions))

        # --- 步骤 4: 查询总数 ---
        # The count query is derived from the statement with all joins and filters.
        count_subquery = stmt.with_only_columns(func.count(SpuInfo.spuId.distinct())).order_by(None)
        total_result = await session.execute(count_subquery)
        total = total_result.scalar_one()

        # --- 步骤 5: 添加排序逻辑 ---
        order_columns = []
        if priceAsc is not None:
            order_columns.append(desc("latest_price") if not priceAsc else asc("latest_price"))
        if priceDiffMaxAsc is not None:
            order_columns.append(desc("max_price_diff") if not priceDiffMaxAsc else asc("max_price_diff"))
        if priceDiffCurAsc is not None:
            order_columns.append(desc("cur_price_diff") if not priceDiffCurAsc else asc("cur_price_diff"))
        if priceDiffLatestAsc is not None:
            order_columns.append(desc("latest_price_diff") if not priceDiffLatestAsc else asc("latest_price_diff"))
        if spuInfoCreateAsc is not None:
            order_columns.append(desc(SpuInfo.create_time) if not spuInfoCreateAsc else asc(SpuInfo.create_time))
        # Add default/fallback sorting
        order_columns.append(desc(SpuInfo.update_time) if not spuInfoUpdateAsc else asc(SpuInfo.update_time))

        stmt = stmt.order_by(*order_columns)

        # --- 步骤 6: 应用分页并执行最终查询 ---
        offset = (pn - 1) * ps
        paginated_stmt = stmt.limit(ps).offset(offset)

        result = await session.execute(paginated_stmt)

        # --- 步骤 7: 正确处理查询结果 ---
        # Since we always join and add columns, the result is always a list of Row objects.
        # We no longer need the if/else for simple vs complex queries.
        items = []
        rows = result.unique().all()
        for row in rows:
            spu_info_obj = row.SpuInfo

            # ALWAYS attach the calculated properties to the object instance.
            # Strawberry will read these attributes to resolve the GraphQL fields.
            spu_info_obj.maxPriceDiff = row.max_price_diff
            spu_info_obj.curPriceDiff = row.cur_price_diff
            spu_info_obj.latestPriceDiff = row.latest_price_diff

            items.append(spu_info_obj)

        return SpuInfoPaginator(
            items=items,
            page_info=PageInfoType(
                total=total,
                page=pn,
                page_size=ps,
                has_next_page=(offset + ps) < total
            )
        )
    # endregion


schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
