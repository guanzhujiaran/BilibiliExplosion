from typing import Dict, Any, List, Optional

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.mysql import insert as mysql_insert
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
from CONFIG import CONFIG
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

    @sql_retry_wrapper
    async def add_spu_info(self, spu_data: Dict[str, Any]):
        async with self.async_session() as db:
            spu_dict = {k: v for k, v in spu_data.items() if hasattr(SpuInfo, k)}
            spu = SpuInfo(**spu_dict)

            db.add(spu)
            await db.flush()

            await self._handle_relationships(spu, spu_data, db)

            await db.commit()
            return spu.spu_id

    @sql_retry_wrapper
    async def _handle_relationships(self, spu: SpuInfo, spu_data: Dict[str, Any], db: AsyncSession):
        relationships = {
            'spu_category': SpuCategory,
            'spu_new_tag_info': SpuNewTagInfo,
            'spu_price_info': SpuPriceInfo,
            'spu_tag_info': SpuTagInfo,
            'spu_video_info': SpuVideoInfo,
        }

        for rel_name, model_class in relationships.items():
            items = spu_data.get(rel_name)
            if items:
                obj_list = []
                for item in items:
                    obj = model_class(**{k: v for k, v in item.items() if hasattr(model_class, k)})
                    obj.spu_id = spu.spu_id
                    obj_list.append(obj)
                db.add_all(obj_list)
                await db.flush()

        # 处理一对一关系：库存信息
        stock_info = spu_data.get('stock_info')
        if stock_info:
            stock_obj = SpuStockInfo(**{
                k: v for k, v in stock_info.items()
                if hasattr(SpuStockInfo, k)
            })
            stock_obj.spu_id = spu.spu_id
            db.add(stock_obj)
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
        spu_dict = {k: v for k, v in spu_data.items() if hasattr(SpuInfo, k)}

        stmt = mysql_insert(SpuInfo).values(**spu_dict)
        update_dict = {k: v for k, v in spu_dict.items() if k != "spu_id"}
        stmt = stmt.on_duplicate_key_update(**update_dict)

        result = await db.execute(stmt)
        spu_id = spu_dict.get("spu_id") or result.inserted_primary_key[0]

        # 子表处理
        await self._handle_relationships_upsert(spu_id, spu_data, db)

    @sql_retry_wrapper
    async def upsert_spu_info(self, spu_data: Dict[str, Any]):
        """
        Upsert SpuInfo 及其关联数据（一对多、一对一）
        """
        async with self.async_session() as db:
            try:
                # 主表：SpuInfo
                spu_dict = {k: v for k, v in spu_data.items() if hasattr(SpuInfo, k)}
                stmt = mysql_insert(SpuInfo).values(**spu_dict)
                update_dict = {k: v for k, v in spu_dict.items() if k != "spu_id"}
                stmt = stmt.on_duplicate_key_update(**update_dict)

                result = await db.execute(stmt)
                spu_id = spu_dict.get("spu_id") or result.inserted_primary_key[0]

                # 处理子表
                await self._handle_relationships_upsert(spu_id, spu_data, db)

                await db.commit()
                return spu_id
            except Exception as e:
                await db.rollback()
                raise e

    async def _handle_relationships_upsert(self, spu_id: str, spu_data: Dict[str, Any], db: AsyncSession):
        relationships = {
            'spu_category': SpuCategory,
            'spu_new_tag_info': SpuNewTagInfo,
            'spu_price_info': SpuPriceInfo,
            'spu_tag_info': SpuTagInfo,
            'spu_video_info': SpuVideoInfo,
        }

        for rel_name, model_class in relationships.items():
            items = spu_data.get(rel_name)
            if items:
                for item in items:
                    item_dict = {k: v for k, v in item.items() if hasattr(model_class, k)}
                    item_dict["spu_id"] = spu_id

                    stmt = mysql_insert(model_class).values(**item_dict)
                    update_dict = {k: v for k, v in item_dict.items() if k not in ("spu_id", "id")}
                    stmt = stmt.on_duplicate_key_update(**update_dict)
                    await db.execute(stmt)

        # 处理一对一关系：库存信息
        stock_info = spu_data.get('stock_info')
        if stock_info:
            stock_dict = {k: v for k, v in stock_info.items() if hasattr(SpuStockInfo, k)}
            stock_dict["spu_id"] = spu_id

            stmt = mysql_insert(SpuStockInfo).values(**stock_dict)
            update_dict = {k: v for k, v in stock_dict.items() if k not in ("spu_id", "id")}
            stmt = stmt.on_duplicate_key_update(**update_dict)
            await db.execute(stmt)

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
    async def get_grouping_info_by_category_id(self, category_id) -> GroupingInfo|None:
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
    async def get_grouping_infos_by_level(self, level:int) -> List[GroupingInfo]:
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


sql_helper = SQLHelper()

if __name__ == '__main__':
    import asyncio
    async def _test():
        res = await sql_helper.get_grouping_info(333015)
        print(res.children)

    asyncio.run(_test())