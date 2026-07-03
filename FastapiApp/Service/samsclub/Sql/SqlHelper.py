import os
from typing import Dict, Any, Optional, List, Sequence
from sqlalchemy import update, select, func, and_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import joinedload
from CONFIG import CONFIG
from Utils.推送.PushMe import a_pushme
from dao.base.sqlHelperBase import SqlHelperBase
from log.base_log import sams_club_logger
from Service.samsclub.Sql.models import (
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
from Utils.通用.Common import log_sql_retry_wrapper


class SQLHelper(SqlHelperBase):
    def __init__(self):
        mysql_db_url = CONFIG.database.MYSQL.sams_club_URI
        # 爬虫专用连接池，设置 is_crawler=True
        super().__init__(mysql_db_url=mysql_db_url, is_crawler=True)
        self.is_update_price = False
        self.relationships = {
            'categoryIdList': SpuCategory,
            'newTagInfo': SpuNewTagInfo,
            'priceInfo': SpuPriceInfo,
            'tagInfo': SpuTagInfo,
            'videoInfos': SpuVideoInfo,
            'stockInfo': SpuStockInfo,
        }

    async def get_price_info_by_spu_id_type(self, spu_id: str, price_type: int, db: AsyncSession) -> int:
        """
        返回 现价,原价
        """
        stmt = select(
            SpuPriceInfo.price
        ).where(
            SpuPriceInfo.spu_id == spu_id,
            SpuPriceInfo.priceType == price_type
        ).order_by(
            SpuPriceInfo.pk.desc()
        ).limit(1)
        res = await db.execute(stmt)
        result = res.first()
        return result and result.price or 0

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
                        if self.is_update_price:
                            break
                        for item in items:
                            price = item.get('price')
                            priceType = item.get('priceType')
                            priceTypeName = item.get('priceTypeName')
                            origin_price = await self.get_price_info_by_spu_id_type(
                                spu_id=spu_id,
                                price_type=priceType,
                                db=db
                            )
                            if str(origin_price) != str(price):
                                obj_list.append(self.gen_update_obj(model_class, item, spu_id))
                                sams_club_logger.critical(
                                    f'商品id** {spu_id} ** {spu_title}的{priceTypeName}有变化：{origin_price}->{price}')
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

    @log_sql_retry_wrapper()
    async def delete_spu_info(self, spu_id: str):
        async with self.async_session() as db:
            spu = await db.get(SpuInfo, spu_id)
            if spu:
                await db.delete(spu)
                await db.commit()

    @log_sql_retry_wrapper()
    async def get_spu_info_by_id(self, spu_id: str) -> Optional[SpuInfo]:
        async with self.async_session() as db:
            return await db.get(SpuInfo, spu_id)

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
    async def bulk_upsert_grouping_info(self, data_list):
        """
        接收完整响应数据，提取 data.dataList 并 Upsert 到 grouping_info 表
        支持异步、自动重试、JSON 存储
        """
        async with self.async_session() as db:
            for item in data_list:
                if type(item) is not dict:
                    await a_pushme(f'[ERR] [{os.path.relpath(__file__)}.{self.__class__.__name__}]',
                                   f"Error: item is not dict: {item}")
                    continue
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

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
    async def get_grouping_infos_by_parent_grouping_id(self, paren_grouping_id: int | str) -> Sequence[GroupingInfo]:
        async with self.async_session() as db:
            result = await db.execute(
                select(GroupingInfo)
                .where(GroupingInfo.parentGroupingId == paren_grouping_id)
            )
            res = result.scalars().all()
        return res

    @log_sql_retry_wrapper()
    async def get_grouping_infos_by_level(self, level: int) -> Sequence[GroupingInfo]:
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

    @log_sql_retry_wrapper()
    async def clear_all_task_progress(self):
        """
        清空 crawl_task_progress 表（慎用）
        """
        async with self.async_session() as db:
            await db.execute(CrawlTaskProgress.__table__.delete())
            await db.commit()
            print("✅ 已清空所有抓取任务进度记录")

    @log_sql_retry_wrapper()
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

    @log_sql_retry_wrapper()
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
        if second_grouping_info and second_grouping_info.title != '为您推荐':
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

    @log_sql_retry_wrapper()
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

    async def get_spu_new_tag_tag_mark_group(self) -> Sequence[str]:
        stmt = select(SpuNewTagInfo.tagMark).group_by(SpuNewTagInfo.tagMark)
        async with self.async_session() as db:
            res = await db.execute(stmt)
            if result := res.scalars().all():
                return result
            return []

    async def get_spu_ids_by_is_put_on_sale(self, is_put_on_sale: bool = True) -> Sequence[str]:
        stmt = select(SpuInfo.spuId).where(SpuInfo.isPutOnSale == is_put_on_sale)
        async with self.async_session() as db:
            res = await db.execute(stmt)
            if result := res.scalars().all():
                return result
            return []


sql_helper = SQLHelper()

if __name__ == '__main__':
    import asyncio

    sql_helper.is_update_price = True


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
        res = await sql_helper.get_spu_info_by_id(1)
        print(res)


    async def _test_query_price():
        async with sql_helper.async_session() as db:
            res = await sql_helper.get_price_info_by_spu_id(
                325257813, db
            )
            print(res)


    async def _test_get_price_info_by_spu_id_type():
        async with sql_helper.async_session() as db:
            res = await sql_helper.get_price_info_by_spu_id_type(
                316210211, 4, db
            )
            print(res)


    async def _test_upsert_bulk():
        da_list = [
            {
                'spuId': '185658184',
                'hostItemId': '981069287',
                'storeId': '5237',
                'seriesId': '185658184',
                'title': '茭白 600g',
                'subTitle': '肉质饱满 可食用率高 鲜嫩脆甜',
                'masterBizType': 1,
                'viceBizType': 1,
                'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5480243/1642856808090345474.jpg',
                'videoInfos': [],
                'isAvailable': True,
                'priceInfo': [
                    {
                        'priceType': 2,
                        'price': '0',
                        'priceTypeName': '原始价'
                    },
                    {
                        'priceType': 1,
                        'price': '1590',
                        'priceTypeName': '销售价'
                    }
                ],
                'stockInfo': {
                    'stockQuantity': 2,
                    'safeStockQuantity': 0,
                    'soldQuantity': 0
                },
                'isImport': False,
                'limitInfo': [],
                'tagInfo': [
                    {
                        'title': '极速达仅剩2件',
                        'tagPlace': 0,
                        'tagMark': 'STOCK_NUM'
                    },
                    {
                        'id': '2',
                        'title': '1257人认为"鲜嫩可口"',
                        'tagPlace': 10,
                        'tagMark': 'aboveTheLimitTag'
                    }
                ],
                'newTagInfo':
                    [
                        {
                            'tagManageId': '14',
                            'title': '极速达',
                            'tagPlace': 2,
                            'tagMark': 'FAST_DELIVERY',
                            'placeType': 0,
                            'priorityValue': 1,
                            'tagStyleId': '37',
                            'styleCode': '0',
                            'styleType': 1,
                            'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                            'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                            'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                            'logoImageWide': 114,
                            'logoImageHigh': 45,
                            'logoImageEnWide': 81,
                            'logoImageEnHigh': 45,
                            'logoImageZhCnWide': 114,
                            'logoImageZhCnHigh': 45
                        },
                        {
                            'tagManageId': '19',
                            'title': '极速达仅剩XX件',
                            'tagPlace': 4,
                            'tagMark': 'STOCK_NUM',
                            'placeType': 0,
                            'priorityValue': 19,
                            'tagStyleId': '41',
                            'styleCode': '0',
                            'styleType': 2,
                            'titleCn': '仅剩2件',
                            'titleEn': '2Left for Delivery',
                            'textColorCn': '#DE1C24',
                            'backColorCn': '',
                            'textColorEn': '#DE1C24',
                            'backColorEn': ''
                        },
                        {
                            'id': '2',
                            'tagManageId': '24',
                            'title': '1257人认为"鲜嫩可口"',
                            'tagPlace': 4,
                            'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT',
                            'placeType': 0,
                            'priorityValue': 23,
                            'tagStyleId': '30',
                            'styleCode': '0',
                            'styleType': 2,
                            'titleCn': '1257人认为 “鲜嫩可口”',
                            'titleEn': '1257 members think “Tender and tasty”',
                            'textColorCn': '#C98249',
                            'backColorCn': '',
                            'textColorEn': '#c98249',
                            'backColorEn': '',
                            'count': '1257',
                            'otherTagInfo': '鲜嫩可口',
                            'otherTagInfoEn': 'Tender and tasty',
                            'statisticsTagType': 2
                        }
                    ],
                'deliveryAttr': 3,
                'availableStores': [],
                'beltInfo': [],
                'hasVideo': False,
                'onlyStoreSale': False,
                'brandId': '10196732',
                'categoryIdList': ['10003023', '10003240', '10004709'],
                'categoryOuterService':
                    {
                        'service_type': 'recommend',
                        'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                        'scene_id': 15,
                        'spu_type': 1,
                        'position_id': 0
                    },
                'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
                'isStoreExtent': False,
                'exclusiveSpu': False,
                'isGlobalDirectPurchase': False,
                'venderCode': '565682',
                'deliveryMethod': 'GLS',
                'zoneTypeList': [],
                'isShowXPlusTag': False,
                'cityCodes': [],
                'giveSpuList': [],
                'isSerial': False,
                'spuSpecInfo': [],
                'specList': {},
                'specInfo': []
            },
            {'spuId': '320711102', 'hostItemId': '980313539', 'storeId': '5237', 'seriesId': '320711102',
             'title': '贝贝南瓜2.2kg',
             'subTitle': '老熟粉面；口感绵密',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/464141/bktsitem-ops-prod-8613469102987390976.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '2990', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 11, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1747985726022',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1747985726022', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45}], 'deliveryAttr': 3, 'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10267947',
             'categoryIdList': ['10003023', '10003240', '10004610'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 1},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '108162',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '78713546', 'hostItemId': '981040006', 'storeId': '6558', 'seriesId': '78713546',
             'title': '梅花肉 约1.8kg',
             'subTitle': '精选猪颈部梅花肉，适合煎烤，叉烧，饺子馅，肉香四溢(由于各门店切割工艺不同,请以收到的具体实物为准)',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/330396/bktpromotion-e2e-prod-8546430520892583936.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '5590',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 59, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10003', 'title': '冰鲜', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'id': '2', 'title': '9052人认为"肉质鲜嫩"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'id': '10003', 'tagManageId': '106', 'title': '冰鲜', 'tagPlace': 4, 'tagMark': 'STATIC',
                  'placeType': 0,
                  'tagSortType': 1, 'priorityValue': 10, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                  'tagStyleId': '17',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '冰鲜', 'titleEn': 'Chilled',
                  'textColorCn': '#DE1C24',
                  'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''},
                 {'id': '2', 'tagManageId': '24', 'title': '9052人认为"肉质鲜嫩"', 'tagPlace': 4,
                  'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23, 'tagStyleId': '30',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '9052人认为 “肉质鲜嫩”',
                  'titleEn': '9052 members think “Fresh and tender”', 'textColorCn': '#C98249', 'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '9052', 'otherTagInfo': '肉质鲜嫩',
                  'otherTagInfoEn': 'Fresh and tender', 'statisticsTagType': 2}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10196732',
             'categoryIdList': ['10003023', '10003229', '10004700'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 2},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '378336',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '320517696', 'hostItemId': '980313611', 'storeId': '5237', 'seriesId': '320517696',
             'title': '松花菜',
             'subTitle': '基地直供；脆嫩细腻', 'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/464144/bktsitem-ops-prod-8613769693886259201.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '1190',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 2, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [{'title': '极速达仅剩2件', 'tagPlace': 0, 'tagMark': 'STOCK_NUM'},
                                          {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                                           'beginTime': '1748499955140', 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748499955140', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'tagManageId': '19', 'title': '极速达仅剩XX件', 'tagPlace': 4, 'tagMark': 'STOCK_NUM',
                 'placeType': 0,
                 'priorityValue': 19, 'tagStyleId': '41', 'styleCode': '0', 'styleType': 2, 'titleCn': '仅剩2件',
                 'titleEn': '2Left for Delivery', 'textColorCn': '#DE1C24', 'backColorCn': '',
                 'textColorEn': '#DE1C24',
                 'backColorEn': ''}], 'deliveryAttr': 3, 'availableStores': [], 'beltInfo': [], 'hasVideo': False,
             'onlyStoreSale': False, 'brandId': '10269571', 'categoryIdList': ['10003023', '10003240', '10004709'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 3},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '125252',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '1278220', 'hostItemId': '420588', 'storeId': '5237', 'seriesId': '1278220',
             'title': '荔枝王1.5kg',
             'subTitle': '个头硕大，肉厚多汁，严格锁鲜', 'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/162716/bktsitem-ops-prod-8613836092063199232.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '6990', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 4, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1749004242818',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1749004242818', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45}], 'deliveryAttr': 3, 'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10196732',
             'categoryIdList': ['10003023', '10003239', '10011864', '10011871'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 4},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '160563',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '320216564', 'hostItemId': '980312835', 'storeId': '5237', 'seriesId': '320216564',
             'title': '黑椒调味牛排 800克（400克*2）', 'subTitle': '微甜黑椒风味；建议煎烤', 'masterBizType': 1,
             'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/464020/bktsitem-ops-prod-8611284878012289025.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '11900', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 18, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10002', 'title': '冷冻', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1748405413037',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748405413037', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '10002', 'tagManageId': '105', 'title': '冷冻', 'tagPlace': 4, 'tagMark': 'STATIC',
                 'placeType': 0,
                 'tagSortType': 1, 'priorityValue': 9, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagStyleId': '16',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '冷冻', 'titleEn': 'Frozen', 'textColorCn': '#DE1C24',
                 'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10271517',
             'categoryIdList': ['10003023', '10003229', '10004682'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 5},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '109772',
             'deliveryMethod': 'DSV', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '269798646', 'hostItemId': '981114881', 'storeId': '5237', 'seriesId': '269798646',
             'title': '玫瑰香青提  1.5kg',
             'subTitle': '脆甜多汁，特殊的玫瑰香味，个大饱满，果肉晶莹剔透，鲜甜爽口，回味无穷',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/407410/bktsitem-ops-prod-8614445714717396993.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '9990',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 25, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1749096250719',
                 'promotionTag': '新品'},
                {'id': '2', 'title': '1531人认为"个大饱满"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                  'tagSortType': 11,
                  'priorityValue': 0, 'beginTime': '1749096250719', 'promotionTag': '新品', 'tagStyleId': '34',
                  'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                  'logoImageWide': 114, 'logoImageHigh': 114},
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '2', 'tagManageId': '24', 'title': '1531人认为"个大饱满"', 'tagPlace': 4,
                  'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23, 'tagStyleId': '30',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '1531人认为 “个大饱满”',
                  'titleEn': '1531 members think “Larger full”', 'textColorCn': '#C98249', 'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '1531', 'otherTagInfo': '个大饱满',
                  'otherTagInfoEn': 'Larger full', 'statisticsTagType': 2}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10196732',
             'categoryIdList': ['10003023', '10003239', '10004685'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 6},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '010356',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '320004015', 'hostItemId': '980307664', 'storeId': '5237', 'seriesId': '320004015',
             'title': '普洱茶叶蛋', 'subTitle': '440g*5袋/盒，富硒+无抗双认证，安全蛋源；精选大叶普洱，茶香四溢',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/463464/bktsitem-ops-prod-8616064757303975936.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '4590', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 8, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1748316343365',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748316343365', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45}], 'deliveryAttr': 3, 'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10269391',
             'categoryIdList': ['10003023', '10003228', '10011839', '10012104'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 7},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '013398',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '320511978', 'hostItemId': '980312164', 'storeId': '5237', 'seriesId': '320511978',
             'title': '星期零鸡蛋豆腐800g', 'subTitle': '选用鲜豆浆融合鲜蛋液制作；双重蛋白质（鸡蛋、大豆蛋白质）',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/463960/bktsitem-ops-prod-8613050663227461633.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '2590', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 6, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10001', 'title': '冷藏', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1748584851130',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748584851130', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '10001', 'tagManageId': '104', 'title': '冷藏', 'tagPlace': 4, 'tagMark': 'STATIC',
                 'placeType': 0,
                 'tagSortType': 1, 'priorityValue': 8, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagStyleId': '15',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '冷藏', 'titleEn': 'Refrigerated',
                 'textColorCn': '#DE1C24',
                 'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10269902',
             'categoryIdList': ['10003023', '10011852', '10011853'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 8},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '390081',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '10556684', 'hostItemId': '980093330', 'storeId': '5237', 'seriesId': '10556684',
             'title': '去皮铁棍山药 800g', 'subTitle': '产自河南温县 口感软糯 糍实甜香 适合蒸 煮 炒 煲汤等',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/297093/bktpromotion-e2e-prod-8551459393195831297.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '3890', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 5, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [],
             'tagInfo': [
                 {'id': '2', 'title': '1606人认为"香甜软糯"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '2', 'tagManageId': '24', 'title': '1606人认为"香甜软糯"', 'tagPlace': 4,
                  'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23, 'tagStyleId': '30',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '1606人认为 “香甜软糯”',
                  'titleEn': '1606 members think “Sweet and soft waxy”', 'textColorCn': '#C98249', 'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '1606', 'otherTagInfo': '香甜软糯',
                  'otherTagInfoEn': 'Sweet and soft waxy', 'statisticsTagType': 2}], 'deliveryAttr': 3,
             'availableStores': [], 'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10196732',
             'categoryIdList': ['10003023', '10003240', '10004709'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 9},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '565682',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '299223883', 'hostItemId': '980271868', 'storeId': '5237', 'seriesId': '299223883',
             'title': '水果甜玉米1.5kg', 'subTitle': '亦蔬亦果；鲜甜爆汁', 'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/460707/bktsitem-ops-prod-8615229066483453952.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '2790', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 42, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1748921428920',
                 'promotionTag': '新品'},
                {'id': '5', 'title': '月销20万+件', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748921428920', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '5', 'tagManageId': '23', 'title': '月销20万+件', 'tagPlace': 4,
                 'tagMark': 'SPU_MONTHLY_SALES_COUNT', 'placeType': 0, 'priorityValue': 20, 'tagStyleId': '29',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '月销20万+件',
                 'titleEn': '20万+ pieces sold in current month', 'textColorCn': '#C98249', 'backColorCn': '',
                 'textColorEn': '#c98249', 'backColorEn': '', 'count': '20万+', 'statisticsTagType': 5}],
             'deliveryAttr': 3,
             'availableStores': [], 'beltInfo': [{'id': '334121',
                                                  'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/0147360703/material/1/8839e29cd8824ff696ddd5d9f0afa3b4-1748937338721.png'}],
             'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10268313',
             'categoryIdList': ['10003023', '10003240', '10004709'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 10},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '108162',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '276192340', 'hostItemId': '981118800', 'storeId': '5237', 'seriesId': '276192340',
             'title': '上海青苗 600g', 'subTitle': '甜糯多汁，柔嫩易嚼', 'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/418533/bktsitem-ops-prod-8618168845575532544.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '990', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 12, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '336129', 'title': '长期节省5.21', 'tagPlace': 12, 'tagMark': 'upperLeft', 'tagSortType': 6,
                 'priorityValue': 1, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagCustomExtInfo': {'id': '65', 'tagId': '336129',
                                      'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png',
                                      'titleColor': '', 'titleBackgroundColor': '', 'styleType': 1,
                                      'priorityType': 1,
                                      'isUse': 1, 'displayRange': '1,2,3',
                                      'createTime': '2025-05-21T09:34:02.000+00:00',
                                      'updateTime': '2025-05-22T10:19:04.000+00:00'}},
                {'id': '3', 'title': '3.1万条好评', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}], 'newTagInfo': [
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '3', 'tagManageId': '25', 'title': '3.1万条好评', 'tagPlace': 4,
                 'tagMark': 'SPU_GOODS_COMMENT_COUNT', 'placeType': 0, 'priorityValue': 26, 'tagStyleId': '31',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '3.1万条好评', 'titleEn': '3.1万 positive reviews',
                 'textColorCn': '#C98249', 'backColorCn': '', 'textColorEn': '#c98249', 'backColorEn': '',
                 'count': '3.1万',
                 'otherTagInfo': '鲜嫩可口', 'otherTagInfoEn': 'Tender and tasty', 'statisticsTagType': 3},
                {'id': '336129', 'tagManageId': '150', 'title': '长期节省5.21', 'tagPlace': 1, 'tagMark': 'CUSTOM',
                 'placeType': 0, 'tagSortType': 6, 'priorityValue': 27,
                 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagStyleId': '89', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png'}],
             'deliveryAttr': 3, 'availableStores': [], 'beltInfo': [{'id': '335118',
                                                                     'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/0147360703/material/1/03ed9ddb025a41dca0791a420d1c395b-1747792522773.png'}],
             'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10267947',
             'categoryIdList': ['10003023', '10003240', '10004603'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 11},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '108162',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '321983721', 'hostItemId': '980314031', 'storeId': '5237', 'seriesId': '321983721',
             'title': '美式干腌眼肉牛排500克（2盒）', 'subTitle': '澳洲进口眼肉牛排；建议煎烤', 'masterBizType': 1,
             'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/464021/bktsitem-ops-prod-8615545511192936448.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '14800', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 5, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10002', 'title': '冷冻', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1748827201112',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1748827201112', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '10002', 'tagManageId': '105', 'title': '冷冻', 'tagPlace': 4, 'tagMark': 'STATIC',
                 'placeType': 0,
                 'tagSortType': 1, 'priorityValue': 9, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagStyleId': '16',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '冷冻', 'titleEn': 'Frozen', 'textColorCn': '#DE1C24',
                 'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10271517',
             'categoryIdList': ['10003023', '10003229', '10004682'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 12},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '109772',
             'deliveryMethod': 'DSV', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '258704188', 'hostItemId': '981108705', 'storeId': '5237', 'seriesId': '258704188',
             'title': '欧芹低脂鸡里脊 1.34kg',
             'subTitle': '柳叶形鸡里脊，鲜嫩不柴 调理腌制入味，多汁味美 支持无油水煎',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/395704/bktsitem-ops-prod-8613107218614423552.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '5490', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 20, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10002', 'title': '冷冻', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'id': '2', 'title': '2714人认为"肉质鲜嫩"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '10002', 'tagManageId': '105', 'title': '冷冻', 'tagPlace': 4, 'tagMark': 'STATIC',
                  'placeType': 0,
                  'tagSortType': 1, 'priorityValue': 9, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                  'tagStyleId': '16',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '冷冻', 'titleEn': 'Frozen', 'textColorCn': '#DE1C24',
                  'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''},
                 {'id': '2', 'tagManageId': '24', 'title': '2714人认为"肉质鲜嫩"', 'tagPlace': 4,
                  'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23, 'tagStyleId': '30',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '2714人认为 “肉质鲜嫩”',
                  'titleEn': '2714 members think “Fresh and tender”', 'textColorCn': '#C98249', 'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '2714', 'otherTagInfo': '肉质鲜嫩',
                  'otherTagInfoEn': 'Fresh and tender', 'statisticsTagType': 2}], 'deliveryAttr': 3,
             'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10196732',
             'categoryIdList': ['10003023', '10003228', '10004624'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 13},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '313945',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '319114773', 'hostItemId': '980311118', 'storeId': '5237', 'seriesId': '319114773',
             'title': '湘佳  川香红油手撕鸡1.16kg',
             'subTitle': '精选山地养殖走地黄羽鸡；盐焗风味腌制、搭配川香红油料包',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/463676/bktsitem-ops-prod-8610521243350581248.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 1, 'price': '6990', 'priceTypeName': '销售价'},
                           {'priceType': 2, 'price': '0', 'priceTypeName': '原始价'}],
             'stockInfo': {'stockQuantity': 2, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10003', 'title': '冰鲜', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'title': '极速达仅剩2件', 'tagPlace': 0, 'tagMark': 'STOCK_NUM'},
                {'title': '新品', 'tagPlace': 1, 'tagMark': 'upperLeft', 'tagSortType': 11,
                 'beginTime': '1747985725805',
                 'promotionTag': '新品'}], 'newTagInfo': [
                {'tagManageId': '4', 'title': '新品', 'tagPlace': 1, 'tagMark': 'NEW', 'placeType': 0,
                 'tagSortType': 11,
                 'priorityValue': 0, 'beginTime': '1747985725805', 'promotionTag': '新品', 'tagStyleId': '34',
                 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/58bc7e3d5b8d4d4fad67395efc13c9e3-1730111728019.png',
                 'logoImageWide': 114, 'logoImageHigh': 114},
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'id': '10003', 'tagManageId': '106', 'title': '冰鲜', 'tagPlace': 4, 'tagMark': 'STATIC',
                 'placeType': 0,
                 'tagSortType': 1, 'priorityValue': 10, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagStyleId': '17',
                 'styleCode': '0', 'styleType': 2, 'titleCn': '冰鲜', 'titleEn': 'Chilled', 'textColorCn': '#DE1C24',
                 'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''},
                {'tagManageId': '19', 'title': '极速达仅剩XX件', 'tagPlace': 4, 'tagMark': 'STOCK_NUM',
                 'placeType': 0,
                 'priorityValue': 19, 'tagStyleId': '41', 'styleCode': '0', 'styleType': 2, 'titleCn': '仅剩2件',
                 'titleEn': '2Left for Delivery', 'textColorCn': '#DE1C24', 'backColorCn': '',
                 'textColorEn': '#DE1C24',
                 'backColorEn': ''}], 'deliveryAttr': 3, 'availableStores': [], 'beltInfo': [], 'hasVideo': False,
             'onlyStoreSale': False, 'brandId': '10269020', 'categoryIdList': ['10003023', '10003228', '10004624'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 14},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '318330',
             'deliveryMethod': 'DSV', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '1333962', 'hostItemId': '867980', 'storeId': '5237', 'seriesId': '1333962',
             'title': '脆宝香瓜 1.5kg', 'subTitle': '果肉细腻， 香甜多汁，因为成熟度和光照原因，部分果面会有发黄现象',
             'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274468843521.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '3190',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 5, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [],
             'tagInfo': [{'id': '1', 'title': '6.3万人回购', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '1', 'tagManageId': '22', 'title': '6.3万人回购', 'tagPlace': 4,
                  'tagMark': 'SPU_YEARS_REBUY_COUNT',
                  'placeType': 0, 'priorityValue': 22, 'tagStyleId': '28', 'styleCode': '0', 'styleType': 2,
                  'titleCn': '6.3万人回购', 'titleEn': '6.3万 repurchases', 'textColorCn': '#C98249',
                  'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '6.3万', 'statisticsTagType': 1}],
             'deliveryAttr': 3, 'availableStores': [], 'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False,
             'brandId': '10196732', 'categoryIdList': ['10003023', '10003239', '10011865', '10011889'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 15},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '144543',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '280207178', 'hostItemId': '981119127', 'storeId': '5237', 'seriesId': '280207178',
             'title': '高山螺丝椒700g', 'subTitle': '椒肉饱满，爽脆细嫩，香辣醇厚', 'masterBizType': 1,
             'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/428146/bktpromotion-e2e-prod-8522088940459233280.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '1290',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 2, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [{'title': '极速达仅剩2件', 'tagPlace': 0, 'tagMark': 'STOCK_NUM'},
                                          {'id': '2', 'title': '1496人认为"商品品质好"', 'tagPlace': 10,
                                           'tagMark': 'aboveTheLimitTag'}], 'newTagInfo': [
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'tagManageId': '19', 'title': '极速达仅剩XX件', 'tagPlace': 4, 'tagMark': 'STOCK_NUM',
                 'placeType': 0,
                 'priorityValue': 19, 'tagStyleId': '41', 'styleCode': '0', 'styleType': 2, 'titleCn': '仅剩2件',
                 'titleEn': '2Left for Delivery', 'textColorCn': '#DE1C24', 'backColorCn': '',
                 'textColorEn': '#DE1C24',
                 'backColorEn': ''},
                {'id': '2', 'tagManageId': '24', 'title': '1496人认为"商品品质好"', 'tagPlace': 4,
                 'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23,
                 'tagStyleId': '30', 'styleCode': '0', 'styleType': 2,
                 'titleCn': '1496人认为 “商品品质好”', 'titleEn': '1496 members think “Good quality”',
                 'textColorCn': '#C98249', 'backColorCn': '', 'textColorEn': '#c98249',
                 'backColorEn': '', 'count': '1496', 'otherTagInfo': '商品品质好',
                 'otherTagInfoEn': 'Good quality', 'statisticsTagType': 2}], 'deliveryAttr': 3,
             'availableStores': [], 'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10267947',
             'categoryIdList': ['10003023', '10003240', '10004714'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 16},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '125252',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '106173991', 'hostItemId': '981051138', 'storeId': '5237', 'seriesId': '106173991',
             'title': '有机香蕉 1.2kg', 'subTitle': '有机产品认证 软糯香甜', 'masterBizType': 1, 'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5129666/00b75812-0863-4765-9731-51473cf373b0_689020221024112756211.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '2290',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 6, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': True,
             'limitInfo': [], 'tagInfo': [{'title': '进口', 'tagPlace': 7, 'tagMark': 'IMPORTED'},
                                          {'id': '2', 'title': '8156人认为"香甜软糯"', 'tagPlace': 10,
                                           'tagMark': 'aboveTheLimitTag'}], 'newTagInfo': [
                {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                 'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                 'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                 'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                 'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                 'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                 'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                {'tagManageId': '20', 'title': '进口', 'tagPlace': 4, 'tagMark': 'IMPORTED', 'placeType': 0,
                 'priorityValue': 11, 'tagStyleId': '14', 'styleCode': '0', 'styleType': 2, 'titleCn': '进口',
                 'titleEn': 'Imported', 'textColorCn': '#DE1C24', 'backColorCn': '', 'textColorEn': '#DE1C24',
                 'backColorEn': ''}, {'id': '2', 'tagManageId': '24', 'title': '8156人认为"香甜软糯"', 'tagPlace': 4,
                                      'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23,
                                      'tagStyleId': '30', 'styleCode': '0', 'styleType': 2,
                                      'titleCn': '8156人认为 “香甜软糯”',
                                      'titleEn': '8156 members think “Sweet and soft waxy”',
                                      'textColorCn': '#C98249',
                                      'backColorCn': '', 'textColorEn': '#c98249', 'backColorEn': '',
                                      'count': '8156',
                                      'otherTagInfo': '香甜软糯', 'otherTagInfoEn': 'Sweet and soft waxy',
                                      'statisticsTagType': 2}], 'deliveryAttr': 3, 'availableStores': [],
             'beltInfo': [],
             'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10004860',
             'categoryIdList': ['10003023', '10003239', '10011866', '10011903'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15,
                                      'spu_type': 1, 'position_id': 17},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '125252',
             'deliveryMethod': 'GLS', 'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [],
             'giveSpuList': [],
             'isSerial': False, 'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '10487278', 'hostItemId': '980093108', 'storeId': '5237', 'seriesId': '10487278',
             'title': 'Pan Fish 生冷冻三文鱼块 1kg',
             'subTitle': '本产品虽已人工去刺去骨并多次 复检，但食用时仍需要注意残骨，避免伤害', 'masterBizType': 1,
             'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5634613/672920231130164850980.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '13500',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 43, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10002', 'title': '冷冻', 'tagPlace': 7, 'tagMark': 'TEMPERATURE', 'tagSortType': 1,
                 'priorityValue': 0, 'updateTime': '2025-06-09T17:53:43.000+00:00'}, {'id': '1133449360676366358',
                                                                                      'title': '{"name":"海鲜水产榜","rankLink":"sams://samsDiscoverDecoration?isFullScreen=1&urlLink=https%3A%2F%2Fdecoration-sams.walmartmobile.cn%2Ftop-buyback-list.html%3FcontentDetailId%3D1133449360676366358%26hippymodule%3Dmain%26hippyrouter%3Dtop-detail%253Ftype%253Dtop-classify%2526contentDetailId%253D1133449360676366358%26hippygraykey%3DtopRemake%26categoryId%3D317681352569954","sort":1}',
                                                                                      'tagPlace': 9,
                                                                                      'tagMark': 'underThePrice'},
                {'id': '2', 'title': '3136人认为"味道鲜美"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '10002', 'tagManageId': '105', 'title': '冷冻', 'tagPlace': 4, 'tagMark': 'STATIC',
                  'placeType': 0,
                  'tagSortType': 1, 'priorityValue': 9, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                  'tagStyleId': '16',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '冷冻', 'titleEn': 'Frozen', 'textColorCn': '#DE1C24',
                  'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''},
                 {'id': '2', 'tagManageId': '24', 'title': '3136人认为"味道鲜美"', 'tagPlace': 4,
                  'tagMark': 'SPU_GOODS_COMMENT_WORD_COUNT', 'placeType': 0, 'priorityValue': 23, 'tagStyleId': '30',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '3136人认为 “味道鲜美”',
                  'titleEn': '3136 members think “Very tasty”', 'textColorCn': '#C98249', 'backColorCn': '',
                  'textColorEn': '#c98249', 'backColorEn': '', 'count': '3136', 'otherTagInfo': '味道鲜美',
                  'otherTagInfoEn': 'Very tasty', 'statisticsTagType': 2}], 'deliveryAttr': 3, 'availableStores': [],
             'beltInfo': [], 'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10254834',
             'categoryIdList': ['10003023', '10003230', '10004630'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 18},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '371743',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []},
            {'spuId': '1277708', 'hostItemId': '980060727', 'storeId': '5237', 'seriesId': '1277708',
             'title': 'MM 有机菜心 600g', 'subTitle': '基地直供 有机种植 软嫩细滑', 'masterBizType': 1,
             'viceBizType': 1,
             'image': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2133816/90007404-d8f0-466c-9dc2-010b9b761f7a_136420200722221824421.jpg',
             'videoInfos': [], 'isAvailable': True,
             'priceInfo': [{'priceType': 2, 'price': '0', 'priceTypeName': '原始价'},
                           {'priceType': 1, 'price': '1590',
                            'priceTypeName': '销售价'}],
             'stockInfo': {'stockQuantity': 3, 'safeStockQuantity': 0, 'soldQuantity': 0}, 'isImport': False,
             'limitInfo': [], 'tagInfo': [
                {'id': '10006', 'title': '有机', 'tagPlace': 7, 'tagMark': 'ORGANIC', 'tagSortType': 4,
                 'priorityValue': 0,
                 'updateTime': '2025-06-09T17:53:43.000+00:00'},
                {'title': '极速达仅剩3件', 'tagPlace': 0, 'tagMark': 'STOCK_NUM'},
                {'id': '333140', 'title': '长期降价6.3', 'tagPlace': 12, 'tagMark': 'upperLeft', 'tagSortType': 6,
                 'priorityValue': 1, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                 'tagCustomExtInfo': {'id': '69', 'tagId': '333140',
                                      'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png',
                                      'styleType': 1, 'priorityType': 1, 'isUse': 1, 'displayRange': '1,3,2',
                                      'createTime': '2025-06-03T08:59:47.000+00:00',
                                      'updateTime': '2025-06-03T08:59:47.000+00:00'}},
                {'id': '2', 'title': '1607人认为"鲜嫩可口"', 'tagPlace': 10, 'tagMark': 'aboveTheLimitTag'}],
             'newTagInfo': [
                 {'tagManageId': '14', 'title': '极速达', 'tagPlace': 2, 'tagMark': 'FAST_DELIVERY', 'placeType': 0,
                  'priorityValue': 1, 'tagStyleId': '37', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/a4222ce7e74643f7be605af5c9a5fa8d-1730112872083.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/fefe1240432b4e2d9ce3a0258a833707-1730112871878.png',
                  'logoImageZhCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/ed55cdf310d143738a133e4f85d831ab-1730112871737.png',
                  'logoImageWide': 114, 'logoImageHigh': 45, 'logoImageEnWide': 81, 'logoImageEnHigh': 45,
                  'logoImageZhCnWide': 114, 'logoImageZhCnHigh': 45},
                 {'id': '10006', 'tagManageId': '109', 'title': '有机', 'tagPlace': 4, 'tagMark': 'STATIC',
                  'placeType': 0,
                  'tagSortType': 4, 'priorityValue': 14, 'updateTime': '2025-06-09T17:53:43.000+00:00',
                  'tagStyleId': '20',
                  'styleCode': '0', 'styleType': 2, 'titleCn': '有机', 'titleEn': 'Organic',
                  'textColorCn': '#DE1C24',
                  'backColorCn': '', 'textColorEn': '#DE1C24', 'backColorEn': ''},
                 {'tagManageId': '19', 'title': '极速达仅剩XX件', 'tagPlace': 4, 'tagMark': 'STOCK_NUM',
                  'placeType': 0,
                  'priorityValue': 19, 'tagStyleId': '41', 'styleCode': '0', 'styleType': 2, 'titleCn': '仅剩3件',
                  'titleEn': '3Left for Delivery', 'textColorCn': '#DE1C24', 'backColorCn': '',
                  'textColorEn': '#DE1C24',
                  'backColorEn': ''},
                 {'id': '333140', 'tagManageId': '154', 'title': '长期降价6.3', 'tagPlace': 1, 'tagMark': 'CUSTOM',
                  'placeType': 0, 'tagSortType': 6, 'priorityValue': 28,
                  'updateTime': '2025-06-09T17:53:43.000+00:00',
                  'tagStyleId': '93', 'styleCode': '0', 'styleType': 1,
                  'logoImageCn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png',
                  'logoImageEn': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/072455857/material/1/7d622e6e7adf4a03a45b57914054f6ed-1715077900790.png'}],
             'deliveryAttr': 3, 'availableStores': [], 'beltInfo': [{'id': '335128',
                                                                     'image': 'https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/0147360703/material/1/0caae554f62e436c98054fe5b7f71bfc-1748937292128.png'}],
             'hasVideo': False, 'onlyStoreSale': False, 'brandId': '10194688',
             'categoryIdList': ['10003023', '10003240', '10004711'],
             'categoryOuterService': {'service_type': 'recommend',
                                      'alg_id': 'rn#0|int_f#1|di_f#0|nr_p#1|b_f#1|st_rn#6|cj_t#1|bab#1@24',
                                      'scene_id': 15, 'spu_type': 1,
                                      'position_id': 19},
             'commonOuterService': '{"service_type":"recommend","sequence_id":"1818144697779_1749576746141_2_273","alg_type":9527,"has_more":true,"request_id":"w_1749576746032_837","channel_id":42}',
             'isStoreExtent': False, 'exclusiveSpu': False, 'isGlobalDirectPurchase': False, 'venderCode': '131888',
             'zoneTypeList': [], 'isShowXPlusTag': False, 'cityCodes': [], 'giveSpuList': [], 'isSerial': False,
             'spuSpecInfo': [], 'specList': {}, 'specInfo': []}]

        res = await sql_helper.bulk_upsert_spu_info(da_list)

        print(res)


    async def _test_upsert_spu_detail1():
        da = {'code': 'Success',
              'data': {'arrivalEndTimeDesc': '有货，可当日或次日发货，依照您在结算页面选择的配送时间窗而定。',
                       'attrGroupInfo': [], 'attrInfo': [
                      {'attrId': '155408', 'attrValueList': [{}, {'value': '1.5kg'}], 'isImportant': False,
                       'title': '净含量'},
                      {'attrId': '155409', 'attrValueList': [{'attrValueId': '1136346', 'value': '国产'}],
                       'isImportant': False, 'title': '进口/国产'}], 'beltInfo': [], 'brandId': '10196732',
                       'categoryIdList': ['10003023', '10003239', '10011865', '10011889'],
                       'complianceInfo': {'id': '261038638727561494',
                                          'value': '山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。'},
                       'couponContentList': [], 'couponList': [], 'customTabList': [], 'deliveryAttr': 3,
                       'deliveryCapacityCountList': [{'list': [
                           {'closeDate': '2025-09-19', 'closeTime': '20:00', 'disabled': False, 'endTime': '21:00',
                            'startTime': '09:00', 'timeISFull': False}], 'strDate': '2025/09/20 周六'}],
                       'desc': '<p><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567487338160129.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567488055382016.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567487807930369.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567488701321216.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567489682771968.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567490328690688.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567491620544512.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567491972870144.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567492681695233.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567493373759488.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8556881118377107457.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8567017512294510592.png"><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8587247830783827969.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"></p>',
                       'descVideo': [], 'detailVideos': [], 'extendedWarrantyList': [], 'favorite': False,
                       'giveaway': False, 'hostItem': '867980', 'imageSizeThreeFour': [], 'images': [
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274468843521.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567279191625729.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275232206849.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274435301377.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275668418561.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274124906497.jpg?imageMogr2/thumbnail/!80p/ignore-error/1',
                      'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275953618945.jpg?imageMogr2/thumbnail/!80p/ignore-error/1'],
                       'intro': '脆宝香瓜 1.5kg', 'isAllowDelivery': True, 'isAvailable': False, 'isCollectOrder': 0,
                       'isCompare': False, 'isCrabCard': False, 'isGlobalDirectPurchase': False,
                       'isGlobalOwnPickUp': False, 'isGovSpu': False, 'isImport': False, 'isPutOnSale': False,
                       'isSerial': False, 'isShowXPlusTag': False, 'isStoreAvailable': False, 'isStoreExtent': False,
                       'isTicket': False, 'limitInfo': [], 'masterBizType': 1, 'netWeight': 1.58, 'newTagInfo': [],
                       'onlyBarSale': False, 'onlyStoreSale': False, 'preSellList': [], 'priceInfo': [],
                       'promotionDetailList': [], 'promotionList': [], 'serviceInfo': [], 'sevenDaysReturn': False,
                       'specInfo': [], 'specList': {},
                       'spuExtDTO': {'deliveryAttr': 3, 'departmentId': '56', 'detailVideos': [], 'giveaway': False,
                                     'hostUpc': ['2160844000005', '6925945901028', '2160844000005', '2160844000005'],
                                     'intro': '脆宝香瓜 1.5kg', 'isAccessory': False, 'isImport': False,
                                     'isRoutine': True, 'netWeight': 1.58, 'sevenDaysReturn': False,
                                     'smallPackageNum': 1, 'smallPackageUnit': 'kg', 'status': 5,
                                     'subETitle': 'Fruit; Fresh Melons',
                                     'subTitle': '果肉细腻， 香甜多汁，因为成熟度和光照原因，部分果面会有发黄现象',
                                     'temperature': 1.0,
                                     'thumbnailImage': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274468843521.jpg',
                                     'valuable': True, 'weight': 1.58}, 'spuId': '1333962', 'spuSpecInfo': [],
                       'standardForIntactGoodsUrl': 'https://m-sams.walmartmobile.cn/common/help-center/217',
                       'stockInfo': {'safeStockQuantity': 0, 'soldQuantity': 0, 'stockQuantity': 0}, 'storeId': '6558',
                       'subTitle': '果肉细腻， 香甜多汁，因为成熟度和光照原因，部分果面会有发黄现象',
                       'tagInfo': [{'id': '1', 'tagMark': 'aboveTheLimitTag', 'tagPlace': 10, 'title': '6.1万人回购'}],
                       'temperature': 1.0, 'title': '脆宝香瓜 1.5kg', 'valuable': True, 'viceBizType': 1, 'videos': [],
                       'weight': 1.58, 'zoneTypeList': []}, 'errorMsg': '', 'msg': '',
              'requestId': 'as|c6b03323e7ce44a19d9a5c6b9a10389d.101.17582432110405739', 'rt': 0, 'success': True,
              'traceId': '72fa312a68001fb5'}
        da_list = [da.get('data')]
        res = await sql_helper.bulk_upsert_spu_info(da_list)
        print(res)


    async def _test_upsert_spu_detial2():
        true = True
        false = False
        da = {"data": {"spuId": "100035921", "hostItem": "888800005786", "storeId": "9996",
                       "title": " a2 Platinum 婴儿配方奶粉（1段）900g （0-6个月）", "masterBizType": 1, "viceBizType": 2,
                       "categoryIdList": ["10003018", "10003044", "10005070", "10005563"], "images": [
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5673029/340920240131191030450.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061310/3c6d7e45-f692-40ec-ae12-271e1947dba0_219520220928130748101.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061311/f186000a-5248-403c-89b9-732fc937749c_993920220928130748197.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061314/4571eb14-da84-4a69-96bb-e43d8ddc64c1_748420220928130748454.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061312/6694ee02-866c-49a9-9548-7d3ebe8003b2_975920220928130748263.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061315/4ede448f-9cbd-43bd-9686-8389857c5a45_438720220928130748629.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061313/f6449a86-3719-4f41-bf3a-5113bfeae27c_119320220928130748344.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061316/7a2e67b9-a96d-4d48-ac7b-50a87f57de2a_678820220928130748820.jpg?imageMogr2/thumbnail/!80p/ignore-error/1",
                "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061317/2bff2b07-fefe-4223-acb1-4414fc4769fe_714120220928130748929.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"],
                       "imageSizeThreeFour": [], "videos": [], "descVideo": [], "isAvailable": True,
                       "isStoreAvailable": True, "isPutOnSale": True, "sevenDaysReturn": False,
                       "intro": "a2 Platinum 婴儿配方奶粉（1段）900g （0-6个月）",
                       "subTitle": "建议纯母乳喂养至少六个月 2027/6/25 到期", "brandId": "10271298",
                       "desc": "<p><img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061326/a8be6fe6-e1cb-4e88-8ab5-e07d9378649d_610020220928130900307.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5061331/0a87c0a6-9ff1-4a28-8063-23886242c248_421920220928130900965.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/6059235/bkts-promotion-e2e-prod-8628656978268172288.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631502384500736.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631503445655553.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631503655378945.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631504091582465.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631504372592640.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631504624263168.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631504796233729.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631505219850240.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631505848983552.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631506008371200.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631506406834177.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5898451/bktpromotion-e2e-prod-8550003543344128000.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631605652467713.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631606113837057.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\">\n<img src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/336462/bktpromotion-e2e-prod-8499631606289993729.jpg?imageMogr2/thumbnail/!80p/ignore-error/1\"></p>",
                       "priceInfo": [{"priceType": 2, "price": "0", "priceTypeName": "原始价"},
                                     {"priceType": 1, "price": "24890", "priceTypeName": "销售价"}],
                       "stockInfo": {"stockQuantity": 18127, "safeStockQuantity": 0, "soldQuantity": 0},
                       "limitInfo": [{"limitType": 2, "limitNum": 6, "text": "限购6件", "cycleDays": 1}],
                       "purchaseLimitText": "每天限购6件", "purchaseLimitMinNum": 6,
                       "tagInfo": [{"title": "进口", "tagPlace": 7, "tagMark": "IMPORTED"},
                                   {"title": "每天限购6件", "tagPlace": 3, "tagMark": "PURCHASE_LIMIT"},
                                   {"id": "2", "title": "403人认为\"商品品质好\"", "tagPlace": 10,
                                    "tagMark": "aboveTheLimitTag"}], "newTagInfo": [
                {"tagManageId": "2", "title": "每天限购6件", "tagPlace": 4, "tagMark": "PURCHASE_LIMIT", "placeType": 0,
                 "priorityValue": 0, "tagStyleId": "58", "styleCode": "1", "styleType": 2, "titleCn": "限购6件",
                 "titleEn": "Limited to 6 pcs", "textColorCn": "#DE1C24", "borderColorCn": "#de1c24", "backColorCn": "",
                 "textColorEn": "#DE1C24", "borderColorEn": "#de1c24", "backColorEn": ""},
                {"tagManageId": "15", "title": "全球购", "tagPlace": 2, "tagMark": "GLOBAL_SHOPPING", "placeType": 0,
                 "priorityValue": 1, "tagStyleId": "38", "styleCode": "0", "styleType": 1,
                 "logoImageCn": "https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/eb0bf805fe09400788553e573f76bf76-1730112973407.png",
                 "logoImageEn": "https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/3b0375d25b584dde924ce6367c6fda38-1730112973652.png",
                 "logoImageZhCn": "https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/023433675/material/1/8ec02f2ac1bb4ad193cc92ee14e11a78-1730112973779.png",
                 "logoImageWide": 114, "logoImageHigh": 45, "logoImageEnWide": 168, "logoImageEnHigh": 45,
                 "logoImageZhCnWide": 114, "logoImageZhCnHigh": 45},
                {"tagManageId": "20", "title": "进口", "tagPlace": 3, "tagMark": "IMPORTED", "placeType": 0,
                 "priorityValue": 6, "tagStyleId": "59", "styleCode": "1", "styleType": 2, "titleCn": "进口",
                 "titleEn": "Imported", "textColorCn": "#0165b8", "backColorCn": "", "textColorEn": "#0165b8",
                 "backColorEn": ""}], "deliveryAttr": 1, "favorite": False, "giveaway": false,
                       "spuExtDTO": {"subTitle": "建议纯母乳喂养至少六个月 2027/6/25 到期",
                                     "intro": "a2 Platinum 婴儿配方奶粉（1段）900g （0-6个月）",
                                     "hostUpc": ["94219029605984"], "departmentId": "303", "valuable": false,
                                     "detailVideos": [], "weight": 0.01, "isImport": true, "emg": "9421902960598",
                                     "isv": "9421902960598", "deliveryAttr": 1, "sevenDaysReturn": false,
                                     "giveaway": false, "isAccessory": false, "isRoutine": true,
                                     "thumbnailImage": "https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/5673029/340920240131191030450.jpg",
                                     "status": 1}, "beltInfo": [], "valuable": false, "detailVideos": [],
                       "isImport": true, "emg": "9421902960598", "isv": "9421902960598", "isSerial": true,
                       "spuSpecInfo": [{"spuId": "113260712", "hostItem": "888800005787",
                                        "specInfo": [{"specKey": "产品", "specValue": "婴儿配方奶粉（1段）400g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "112926668", "hostItem": "888800005789",
                                        "specInfo": [{"specKey": "产品", "specValue": "婴儿配方奶粉（2段）400g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "100035921", "hostItem": "888800005786",
                                        "specInfo": [{"specKey": "产品", "specValue": "婴儿配方奶粉（1段）900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "100040422", "hostItem": "888800005788",
                                        "specInfo": [{"specKey": "产品", "specValue": "婴儿配方奶粉（2段）900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "107769985", "hostItem": "888800005790",
                                        "specInfo": [{"specKey": "产品", "specValue": "幼儿配方奶粉（3段）900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "275665449", "hostItem": "888810000115",
                                        "specInfo": [{"specKey": "产品", "specValue": "儿童配方奶粉（4段）900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "171563663", "hostItem": "888800006177",
                                        "specInfo": [{"specKey": "产品", "specValue": "儿童营养奶粉 (4-12岁) 750g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "1913020", "hostItem": "888800003001",
                                        "specInfo": [{"specKey": "产品", "specValue": "孕妇奶粉 900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "237920555", "hostItem": "888800006814",
                                        "specInfo": [{"specKey": "产品", "specValue": "全脂速溶奶粉900g"}],
                                        "isPutOnSale": true, "outOfStock": false},
                                       {"spuId": "275114095", "hostItem": "888800007408", "specInfo": [
                                           {"specKey": "产品", "specValue": "紫吨吨营养奶粉礼盒(行动力+自护力)"}],
                                        "isPutOnSale": true, "outOfStock": false}],
                       "specList": {"婴儿配方奶粉（1段）400g": {"spuId": "113260712"},
                                    "幼儿配方奶粉（3段）900g": {"spuId": "107769985"},
                                    "全脂速溶奶粉900g": {"spuId": "237920555"},
                                    "婴儿配方奶粉（2段）900g": {"spuId": "100040422"},
                                    "紫吨吨营养奶粉礼盒(行动力+自护力)": {"spuId": "275114095"},
                                    "孕妇奶粉 900g": {"spuId": "1913020"},
                                    "婴儿配方奶粉（1段）900g": {"spuId": "100035921"},
                                    "婴儿配方奶粉（2段）400g": {"spuId": "112926668"},
                                    "儿童营养奶粉 (4-12岁) 750g": {"spuId": "171563663"},
                                    "儿童配方奶粉（4段）900g": {"spuId": "275665449"}}, "specInfo": [{"产品": [
                "婴儿配方奶粉（1段）400g", "婴儿配方奶粉（2段）400g", "婴儿配方奶粉（1段）900g", "婴儿配方奶粉（2段）900g",
                "幼儿配方奶粉（3段）900g", "儿童配方奶粉（4段）900g", "儿童营养奶粉 (4-12岁) 750g", "孕妇奶粉 900g",
                "全脂速溶奶粉900g", "紫吨吨营养奶粉礼盒(行动力+自护力)"]}], "attrGroupInfo": [{"attrInfo": [
                {"attrId": "35205", "title": "年龄", "attrValueList": [{"attrValueId": "286654", "value": "0-6个月"}],
                 "isImportant": false}], "attrGroupId": "2", "title": "基本信息"}, {"attrInfo": [
                {"attrId": "35299", "title": "总净重(g)", "attrValueList": [{}, {"value": "900"}],
                 "isImportant": false}], "attrGroupId": "7", "title": "规格"}, {"attrInfo": [
                {"attrId": "35290", "title": "保质期", "attrValueList": [{}, {"value": "见包装"}],
                 "isImportant": false}], "attrGroupId": "8", "title": "食品安全信息"}, {"attrInfo": [
                {"attrId": "35240", "title": "包装", "attrValueList": [{"attrValueId": "287554", "value": "罐装"}],
                 "isImportant": false}], "attrGroupId": "10", "title": "包装"}], "attrInfo": [
                {"attrId": "35236", "title": "单件规格", "attrValueList": [{"attrValueId": "287277", "value": "900g"}],
                 "isImportant": false},
                {"attrId": "35233", "title": "是否进口", "attrValueList": [{"attrValueId": "287268", "value": "进口"}],
                 "isImportant": false}], "extendedWarrantyList": [], "couponContentList": [], "couponList": [],
                       "promotionList": [], "promotionDetailList": [], "deliveryCapacityCountList": [],
                       "complianceInfo": {"id": "261038638727561494",
                                          "value": "山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。\n联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。"},
                       "preSellList": [],
                       "globalShoppingTaxRateExplain": "1.该商品价格已包含跨境电商综合税。\n2.跨境电商综合税需按一般贸易增值税及消费税额的70%征收，山姆全球购代征代缴，税费以提交订单时的金额为准。\n3.财政部，海关总署，国家税务总局发布跨境电子商务零售进口税收政策，自2019年1月1日起，跨境电商单次交易限值为人民币5000元，个人年度交易限值为人民币26000元。",
                       "onlyStoreSale": False, "onlyBarSale": False, "serviceInfo": [],
                       "arrivalEndTimeDesc": "有货，预计一周内送达。", "isStoreExtent": False,
                       "isGlobalDirectPurchase": False, "isGlobalOwnPickUp": False, "siteInfoResponses": {},
                       "isAllowDelivery": True, "zoneTypeList": [], "isCrabCard": False, "isShowXPlusTag": False,
                       "isCompare": False, "isGovSpu": False,
                       "standardForIntactGoodsUrl": "https://m-sams.walmartmobile.cn/common/help-center/217",
                       "serialId": "3562", "customTabList": [], "isTicket": false}, "code": "Success", "msg": "",
              "errorMsg": "", "traceId": "4e963727ee499b9e",
              "requestId": "as|84e880a6a7a948e1a25b56a92bbddf6d.166.17582507843231047", "rt": 0, "success": True}
        da_list = [da.get('data')]
        res = await sql_helper.bulk_upsert_spu_info(da_list)
        print(res)


    async def _test_get_spu_ids_by_is_put_on_sale():
        res = await sql_helper.get_spu_ids_by_is_put_on_sale(True)
        print(res)


    asyncio.run(_test_upsert_spu_detial2())
