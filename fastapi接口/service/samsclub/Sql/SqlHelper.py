from typing import Dict, Any, Optional, List

from sqlalchemy import update, select, func, and_, case
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import joinedload

from CONFIG import CONFIG
from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.service.samsclub.Sql.models import (
    SpuInfo,
    SpuCategory,
    SpuNewTagInfo,
    SpuPriceInfo,
    SpuTagInfo,
    SpuVideoInfo,
    SpuStockInfo,
    GroupingInfo,
    CrawlTaskProgress,
)
from fastapi接口.utils.Common import sql_retry_wrapper

class SQLHelper:
    def __init__(self):
        self.engine = create_async_engine(
            CONFIG.database.MYSQL.sams_club_URI,
            pool_pre_ping=True,
            echo=False
        )
        self.async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        self.relationships = {
            'categoryIdList': SpuCategory,
            'newTagInfo': SpuNewTagInfo,
            'priceInfo': SpuPriceInfo,
            'tagInfo': SpuTagInfo,
            'videoInfos': SpuVideoInfo,
            'stockInfo': SpuStockInfo,
        }

    @sql_retry_wrapper
    async def get_price_info_by_spu_id(self, spu_id: str, db: AsyncSession) -> tuple[int, int]:
        """
        返回 现价,原价
        """
        stmt = select(
            func.max(
                case(
                    (SpuPriceInfo.priceType == 0, SpuPriceInfo.price),
                    else_=0
                )
            ).label("price0"),
            func.max(
                case(
                    (SpuPriceInfo.priceType == 1, SpuPriceInfo.price),
                    else_=0
                )
            ).label("price1")
        ).where(
            SpuPriceInfo.spu_id == spu_id,
            SpuPriceInfo.priceType.in_([0, 1])
        )

        res = await db.execute(stmt)
        result = res.first()
        if result and result.price0 is not None and result.price1 is not None:
            return result.price1, result.price0
        return 0, 0

    def gen_update_obj(self, model_class, data_item: dict, spu_id: int | str) -> dict:
        not_in_list = list(self.relationships.keys())
        not_in_list.extend(['pk', 'update_time', 'create_time'])
        obj = {col.name: None for col in model_class.__table__.columns if
               col.name not in not_in_list}
        obj.update({
            'spu_id': spu_id
        }
        )
        obj.update({k: v
                    for k, v in data_item.items() if hasattr(model_class, k)})
        if 'unknow_field' in model_class.__table__.columns:
            if unknow_field := {k: v for k, v in data_item.items() if
                                k not in model_class.__table__.columns and k not in not_in_list}:
                obj['unknow_field'] = unknow_field
        return obj

    @sql_retry_wrapper
    async def _handle_relationships_upsert(self, spu_id: str, spu_data: Dict[str, Any], db: AsyncSession):

        spu_title = spu_data.get('title')
        for rel_name, model_class in self.relationships.items():
            items = spu_data.get(rel_name)
            if items:
                obj_list = []
                stmt = mysql_insert(
                    model_class
                )
                update_cols = {col.name: col for col in stmt.inserted if
                               col.name not in ['pk', 'update_time', 'create_time']}
                match rel_name:
                    case "categoryIdList":
                        for item in items:
                            obj_list.append(dict(categoryId=item,
                                                 spu_id=spu_id))
                    case "stockInfo":
                        obj_list.append(self.gen_update_obj(model_class, items, spu_id))
                    case "priceInfo":
                        cur_price, prev_price = await self.get_price_info_by_spu_id(spu_id, db)
                        for item in items:
                            price = item.get('price')
                            if item.get('priceTypeName') == '销售价':
                                if str(price) != str(cur_price):
                                    obj_list.append(self.gen_update_obj(model_class, item, spu_id))
                                    sams_club_logger.critical(
                                        f'商品id** {spu_id} ** {spu_title}的销售价有变化：{cur_price}->{price}')
                            elif item.get('priceTypeName') == '原始价':
                                if str(price) != str(prev_price):
                                    obj_list.append(self.gen_update_obj(model_class, item, spu_id))
                                    sams_club_logger.critical(
                                        f'商品id** {spu_id} ** {spu_title}的原始价有变化：{prev_price}->{price}')
                            else:
                                raise ValueError("priceTypeName is invalid")
                    case _:
                        for item in items:
                            obj_list.append(self.gen_update_obj(model_class, item, spu_id))
                if not obj_list:
                    continue
                stmt = stmt.values(obj_list).on_duplicate_key_update(
                    update_cols
                )
                await db.execute(
                    stmt
                )
                await db.flush()

    @sql_retry_wrapper
    async def delete_spu_info(self, spu_id: str):
        async with self.async_session() as db:
            spu = await db.get(SpuInfo, spu_id)
            if spu:
                await db.delete(spu)
                await db.commit()

    @sql_retry_wrapper
    async def get_spu_info_by_id(self, spu_id: str) -> Optional[SpuInfo]:
        async with self.async_session() as db:
            return await db.get(SpuInfo, spu_id)

    @sql_retry_wrapper
    async def bulk_upsert_spu_info(self, spu_data_list: List[Dict[str, Any]]):
        """
        批量 Upsert SpuInfo 及其关联数据（一对多、一对一）
        """
        async with self.async_session() as db:
            for spu_data in spu_data_list:
                await self._process_single_upsert(spu_data, db)

            await db.commit()

    async def _process_single_upsert(self, spu_data: Dict[str, Any], db: AsyncSession):
        # 主表：SpuInfo
        spu_dict = self.gen_update_obj(SpuInfo, spu_data, spu_data.get("spuId"))

        update_dict = {k: v for k, v in spu_dict.items() if k != "spu_id"}
        stmt = mysql_insert(SpuInfo).values(**update_dict)
        stmt = stmt.on_duplicate_key_update(**update_dict)

        result = await db.execute(stmt)
        spu_id = spu_dict.get("spuId") or result.inserted_primary_key[0]

        # 子表处理
        await self._handle_relationships_upsert(spu_id, spu_data, db)

    @sql_retry_wrapper
    async def bulk_upsert_grouping_info(self, data_list):
        """
        接收完整响应数据，提取 data.dataList 并 Upsert 到 grouping_info 表
        支持异步、自动重试、JSON 存储
        """
        async with self.async_session() as db:
            for item in data_list:
                await self._upsert_single_grouping(item, db)
            await db.commit()

    async def _upsert_single_grouping(self, item: Dict[str, Any], db: AsyncSession):
        """
        将单个 dataList 条目 Upsert 到 grouping_info 表
        """

        # 只保留模型中存在的字段 + 计算字段不需要传入
        allowed_keys = {col.name for col in GroupingInfo.__table__.columns}

        # 过滤掉非数据库字段（如 isFastDelivery）
        filtered_item = {
            key: value for key, value in item.items()
            if key in allowed_keys
        }

        # 构建 insert 语句
        stmt = mysql_insert(GroupingInfo).values(**filtered_item)

        # 构建 update 字段（排除主键 pk）
        update_dict = {
            key: value for key, value in filtered_item.items()
            if key != "pk"
        }

        # 设置 on_duplicate_key_update
        stmt = stmt.on_duplicate_key_update(**update_dict)

        # 执行
        await db.execute(stmt)

    @sql_retry_wrapper
    async def reset_all_tasks(self):
        """
        将 crawl_task_progress 表中所有任务重置为初始状态：
        last_page_num=1, is_finished=0
        """
        async with self.async_session() as db:
            stmt = (
                update(CrawlTaskProgress)
                .values(last_page_num=1, is_finished=0)
            )
            await db.execute(stmt)
            await db.commit()
            print("✅ 已重置所有抓取任务进度，准备重新开始抓取")

    @sql_retry_wrapper
    async def reset_completed_tasks(self):
        """
        仅重置已完成的任务（is_finished=1）：
        last_page_num=1, is_finished=0
        """
        async with self.async_session() as db:
            stmt = (
                update(CrawlTaskProgress)
                .where(CrawlTaskProgress.is_finished == 1)
                .values(last_page_num=1, is_finished=0)
            )
            await db.execute(stmt)
            await db.commit()
            print("✅ 已重置所有已完成的抓取任务")

    @sql_retry_wrapper
    async def get_unfinished_tasks(self) -> List[Dict[str, Any]]:
        """
        查询所有未完成的任务（is_finished != 1）
        返回 [ {first_category_id: int, second_category_id: int}, ... ]
        """
        async with self.async_session() as db:
            result = await db.execute(
                select(CrawlTaskProgress.first_category_id, CrawlTaskProgress.second_category_id)
                .where(CrawlTaskProgress.is_finished != 1)
            )
            rows = result.all()
            return [
                {"firstCategoryId": row[0], "secondCategoryId": row[1]}
                for row in rows
            ]

    @sql_retry_wrapper
    async def get_grouping_info_by_category_id(self, category_id) -> GroupingInfo | None:
        """
        查询所有未完成的任务（is_finished != 1）
        返回 [ {first_category_id: int, second_category_id: int}, ... ]
        """
        async with self.async_session() as db:
            result = await db.execute(
                select(GroupingInfo)
                .where(GroupingInfo.groupingId == category_id)
                .limit(1)
            )
            res = result.scalars().first()
        return res

    @sql_retry_wrapper
    async def get_grouping_infos_by_parent_grouping_id(self, paren_grouping_id: int | str) -> List[GroupingInfo]:
        async with self.async_session() as db:
            result = await db.execute(
                select(GroupingInfo)
                .where(GroupingInfo.parentGroupingId == paren_grouping_id)
            )
            res = result.scalars().all()
        return res

    @sql_retry_wrapper
    async def get_grouping_infos_by_level(self, level: int) -> List[GroupingInfo]:
        """
        查询所有未完成的任务（is_finished != 1）
        返回 [ {first_category_id: int, second_category_id: int}, ... ]
        """
        async with self.async_session() as db:
            result = await db.execute(
                select(GroupingInfo)
                .where(GroupingInfo.level == level)
            )
            res = result.scalars().all()
        return res

    @sql_retry_wrapper
    async def clear_all_task_progress(self):
        """
        清空 crawl_task_progress 表（慎用）
        """
        async with self.async_session() as db:
            await db.execute(CrawlTaskProgress.__table__.delete())
            await db.commit()
            print("✅ 已清空所有抓取任务进度记录")

    @sql_retry_wrapper
    async def update_task_progress(
            self,
            first_category_id: int,
            second_category_id: int,
            new_page_num: int,
            is_finished: bool = False
    ):
        async with self.async_session() as db:
            stmt = (
                update(CrawlTaskProgress)
                .where(
                    CrawlTaskProgress.first_category_id == first_category_id,
                    CrawlTaskProgress.second_category_id == second_category_id
                )
                .values({
                    'last_page_num': new_page_num,
                    'is_finished': 1 if is_finished else 0
                })
            )
            result = await db.execute(stmt)
            await db.commit()

            if result.rowcount == 0:
                print(f"⚠️ 更新失败：任务 ({first_category_id}, {second_category_id}) 不存在")

    @sql_retry_wrapper
    async def get_or_create_task_progress(self, first_category_id, second_category_id) -> CrawlTaskProgress:
        async with self.async_session() as session:
            result = await session.execute(
                select(CrawlTaskProgress).where(
                    CrawlTaskProgress.first_category_id == first_category_id,
                    CrawlTaskProgress.second_category_id == second_category_id
                )
            )
            task = result.scalars().first()
            if not task:
                # 创建新任务
                task = CrawlTaskProgress(
                    first_category_id=first_category_id,
                    second_category_id=second_category_id,
                    last_page_num=1,
                    is_finished=0
                )
                session.add(task)
                await session.commit()
                await session.refresh(task)

            return task

    async def get_front_category_ids(self, firstCategoryId, secondCategoryId):
        second_grouping_info = await self.get_grouping_info_by_category_id(secondCategoryId)
        if second_grouping_info.title != '为您推荐':
            frontCategoryIds = [int(secondCategoryId)] + [int(child.get('groupingId')) for child in
                                                          second_grouping_info.children]
        else:
            second_grouping_infos = await self.get_grouping_infos_by_parent_grouping_id(firstCategoryId)
            frontCategoryIds = []
            for second_grouping_info in second_grouping_infos:
                second_category_id = second_grouping_info.groupingIdInt
                frontCategoryIds.extend([int(second_category_id)] + [int(child.get('groupingId')) for child in
                                                                     second_grouping_info.children])
        return frontCategoryIds

    @sql_retry_wrapper
    async def get_full_spu_info_by_spu_id(self, spu_id) -> SpuInfo | None:
        """
        查询所有未完成的任务（is_finished != 1）
        返回 [ {first_category_id: int, second_category_id: int}, ... ]
        """
        subq = (
            select(
                SpuPriceInfo.spu_id,
                func.max(SpuPriceInfo.update_time).label("max_update_time")
            )
            .where(
                and_(
                    SpuPriceInfo.priceTypeName == '销售价',
                    SpuPriceInfo.spu_id == spu_id
                )
            )
            .group_by(SpuPriceInfo.spu_id)
            .subquery()
        )

        # 为子查询手动添加别名
        subq_alias = subq.alias()

        # 主查询
        query = (
            select(SpuInfo)
            .join(SpuCategory, SpuInfo.spuId == SpuCategory.spu_id)
            .outerjoin(SpuNewTagInfo, SpuInfo.spuId == SpuNewTagInfo.spu_id)
            .outerjoin(SpuStockInfo, SpuInfo.spuId == SpuStockInfo.spu_id)
            .outerjoin(SpuTagInfo, SpuInfo.spuId == SpuTagInfo.spu_id)
            .outerjoin(SpuVideoInfo, SpuInfo.spuId == SpuVideoInfo.spu_id)
            .outerjoin(subq_alias, SpuInfo.spuId == subq_alias.c.spu_id)
            .outerjoin(
                SpuPriceInfo,
                and_(
                    SpuInfo.spuId == SpuPriceInfo.spu_id,
                    SpuPriceInfo.update_time == subq_alias.c.max_update_time
                )
            ).options(
                joinedload(SpuInfo.spu_price_info),
                joinedload(SpuInfo.spu_category),
                joinedload(SpuInfo.spu_new_tag_info),
                joinedload(SpuInfo.spu_stock_info),
                joinedload(SpuInfo.spu_tag_info),
                joinedload(SpuInfo.spu_video_info),
            )

            .where(SpuInfo.spuId == spu_id)
        )
        async with self.async_session() as db:
            result = await db.execute(query)

            return result.scalars().first()

    async def get_spu_new_tag_tag_mark_group(self) -> list[str]:
        stmt = select(SpuNewTagInfo.tagMark).group_by(SpuNewTagInfo.tagMark)
        async with self.async_session() as db:
            res = await db.execute(stmt)
            if result := res.scalars().all():
                return result
            return []


sql_helper = SQLHelper()

if __name__ == '__main__':
    import asyncio


    async def _test_upsert_single():
        async with sql_helper.async_session() as db:
            spu_data = {'spuId': '270141075', 'hostItemId': '888800007384', 'storeId': '9996', 'seriesId': '270141075',
                        'title': '活灵魂酒庄红葡萄酒 2019年 750ml', 'subTitle': '浓郁甘冽 余韵细腻', 'masterBizType': 1,
                        'viceBizType': 2,
                        'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/407666/670320240523195431465.jpg',
                        'videoInfos': [], 'isAvailable': True,
                        'priceInfo': [{'priceType': 1, 'price': '109900', 'priceTypeName': '销售价'},
                                      {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
                        'stockInfo': {'stockQuantity': 954, 'safeStockQuantity': 0, 'soldQuantity': 0},
                        'isImport': True,
                        'limitInfo': [{'limitType': 2, 'limitNum': 6, 'text': '限购6件', 'cycleDays': 1}],
                        'tagInfo': [{'title': '进口', 'tagPlace': 7, 'tagMark': 'IMPORTED'},
                                    {'title': '限购6件', 'tagPlace': 0, 'tagMark': 'PURCHASE_LIMIT'}], 'newTagInfo': [
                    {'tagManageId': '15', 'title': '全球购', 'tagPlace': 2, 'tagMark': 'GLOBAL_SHOPPING',
                     'placeType': 0, 'priorityValue': 2, 'tagStyleId': '38', 'styleCode': '0', 'styleType': 1,
                     'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/eb0bf805fe09400788553e573f76bf76-1730112973407.png',
                     'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/3b0375d25b584dde924ce6367c6fda38-1730112973652.png',
                     'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/8ec02f2ac1bb4ad193cc92ee14e11a78-1730112973779.png',
                     'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 168, 'logoImageEnHigh': 45,
                     'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                    {'tagManageId': '20', 'title': '进口', 'tagPlace': 4, 'tagMark': 'IMPORTED', 'placeType': 0,
                     'priorityValue': 11, 'tagStyleId': '14', 'styleCode': '0', 'styleType': 2, 'titleCn': '进口',
                     'titleEn': 'Imported', 'textColorCn': '#DE1C24', 'backColorCn': '', 'textColorEn': '#DE1C24',
                     'backColorEn': ''},
                    {'tagManageId': '2', 'title': '限购6件', 'tagPlace': 4, 'tagMark': 'PURCHASE_LIMIT', 'placeType': 0,
                     'priorityValue': 13, 'tagStyleId': '6', 'styleCode': '0', 'styleType': 2, 'titleCn': '限购6件',
                     'titleEn': 'Limited to 6 pcs', 'textColorCn': '#DE1C24', 'backColorCn': '',
                     'textColorEn': '#DE1C24', 'backColorEn': ''}], 'deliveryAttr': 1, 'availableStores': [],
                        'beltInfo': [{'id': '281048',
                                      'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/095108154/material/1/6c35715988644623b19aae3c4cdfd523-1727235263246.png'}],
                        'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10267752',
                        'categoryIdList': ['10003036', '10003048', '10004799', '10007844'],
                        'categoryOuterService': {'service_type': 'normal', 'positionId': 102,
                                                 'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                                 'scene_id': 15, 'spu_type': 1}, 'isStoreExtent': False,
                        'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'zoneTypeList': [],
                        'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
                        'spuSpecInfo': [], 'specList': {}, 'specInfo': []}
            await sql_helper._process_single_upsert(spu_data, db)


    async def _test_get_full_spu_info_by_spu_id():
        res = await sql_helper.get_full_spu_info_by_spu_id(69473441)
        print(res)


    async def _test_get_spu_new_tag_tag_mark_group():
        res = await sql_helper.get_spu_new_tag_tag_mark_group()
        print(res)


    async def _test_query_spu_info():
        res = await sql_helper.query_spu_info(1)
        print(res)


    asyncio.run(_test_query_spu_info())
