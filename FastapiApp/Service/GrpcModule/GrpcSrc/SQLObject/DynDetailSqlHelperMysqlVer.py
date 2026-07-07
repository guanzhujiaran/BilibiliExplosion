# -*- coding: utf-8 -*-
import ast
import asyncio
import datetime
import json
import time
from copy import deepcopy
from typing import Literal, List, Sequence, Union, Optional
import numpy as np
from sqlalchemy import (
    select,
    and_,
    exists,
    func,
    String,
    text,
    or_,
    JSON,
    delete,
    update,
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload
from CONFIG import CONFIG
from Models.lottery_database.bili.LotteryDataBaseQueryModels import (
    BiliLotDataQueryModel,
)
from Models.lottery_database.bili.LotteryDataModels import (
    BiliLotStatisticRankTypeEnum,
    BiliUserInfoSimple,
    AtariLotRankEnum,
    LotteryDataSortEnum,
    SortOrderEnum,
)
from Models.lottery_database.bili.comm import BiliLotDataStatusEnum, LotteryBusinessType
from Utils.通用.Common import log_sql_retry_wrapper
from Utils.通用.dynamic_id_caculate import ts_2_fake_dynamic_id
from Service.GrpcModule.GrpcSrc.SQLObject.models import (
    Bilidyndetail,
    Lotdata,
    ArticlePubRecord,
    BiliUserInfo,
    BiliAtariInfo,
    LotExtraInfo,
)
from dao.base.sqlHelperBase import SqlHelperBase
from dao.biliLotteryStatisticSqlHelper import lottery_data_statistic_sql_helper


class SQLHelper(SqlHelperBase):
    def __init__(self):
        # 爬虫专用连接池，设置 is_crawler=True
        super().__init__(
            mysql_db_url=CONFIG.database.MYSQL.dyn_detail_URI, is_crawler=True
        )

    # region 返回和提交内容预处理

    @classmethod
    def _process_2_save_data(cls, orig_list_dict: list[dict]) -> list[dict]:
        """
        对存入数据预处理，将dict转化为str(dict)
        :param orig_list_dict:
        :return:
        """
        for _dic in orig_list_dict:
            for k, v in _dic.items():
                if type(v) == dict or type(v) == list:
                    _dic[k] = json.dumps(v, ensure_ascii=False)
        return orig_list_dict

    def preprocess_ret_data(self, data):
        """
        对取出的数据进行预处理，包括转换字符串表示的字典、处理大整数（大于9007199254740991）转为字符串以避免精度丢失。
        该函数能够处理嵌套的字典和列表。
        :param data: 输入的数据，可以是字典或列表
        :return: 处理后的数据
        """
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if isinstance(v, str):
                    try:
                        literal_value = ast.literal_eval(v)
                        if isinstance(literal_value, dict) or isinstance(
                            literal_value, list
                        ):
                            data[k] = self.preprocess_ret_data(literal_value)
                        else:
                            data[k] = literal_value
                    except (ValueError, SyntaxError):
                        # 如果解析失败，则保留原值
                        pass
                elif isinstance(v, int) and v > 9007199254740991:
                    data[k] = str(v)
                else:
                    data[k] = self.preprocess_ret_data(v)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    try:
                        literal_value = ast.literal_eval(item)
                        if isinstance(literal_value, dict) or isinstance(
                            literal_value, list
                        ):
                            data[i] = self.preprocess_ret_data(literal_value)
                        else:
                            data[i] = literal_value
                    except (ValueError, SyntaxError):
                        # 如果解析失败，则保留原值
                        pass
                elif isinstance(item, int) and item > 9007199254740991:
                    data[i] = str(item)
                else:
                    data[i] = self.preprocess_ret_data(item)
        return data

    # endregion

    # region 查询相关信息
    async def get_lost_lots(
        self, limit_ts: int = 7 * 3600 * 24
    ) -> Sequence[Union[Bilidyndetail, Lotdata]]:
        """
        获取主表中lot_id存在，但抽奖信息表中不存在数据的lot_id和rid信息
        :return:
        """
        if limit_ts:
            target_ts = int(time.time()) - limit_ts
            fake_dynamic_id = ts_2_fake_dynamic_id(int(target_ts))
        else:
            fake_dynamic_id = 0
        # 使用左连接，并过滤掉Lotdata表中存在对应lottery_id的记录
        query = (
            select(Bilidyndetail)
            .join(Lotdata, Bilidyndetail.lot_id == Lotdata.lottery_id, isouter=True)
            .where(
                and_(
                    Bilidyndetail.lot_id.isnot(None),
                    Lotdata.lottery_id.is_(None),
                    Bilidyndetail.dynamic_id_int > fake_dynamic_id,
                )
            )
            .order_by(Bilidyndetail.dynamic_id_int.desc())
        )

        async with self.async_session() as session:
            result = await session.execute(query)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def get_discountious_rids(self) -> Sequence[int]:
        """
        获取最大值和最小值之间不连续的rid，也就是那些可能获取失败了rid（rid最近的30万条数据）
        :return:
        """
        async with self.async_session() as session:
            # 子查询：获取最近的30万条记录
            subquery = (
                select(Bilidyndetail.rid_int)
                .order_by(Bilidyndetail.rid_int.desc())
                .limit(300000)
                .alias("t1")
            )
            # 主查询：查找缺失的rid值
            query = (
                select((subquery.c.rid_int + 1).label("x"))
                .where(
                    and_(
                        ~exists().where(
                            Bilidyndetail.rid_int == (subquery.c.rid_int + 1)
                        ),
                        (subquery.c.rid_int + 1) > 0,
                        func.length(func.cast(subquery.c.rid_int + 1, String)) < 18,
                    )
                )
                .order_by("x")
            )

            async with self.async_session() as session:
                result = await session.execute(query)
                ret_row = [int(row.x) for row in result]

            return ret_row

    @log_sql_retry_wrapper()
    async def get_all_dynamic_detail_by_dynamic_id(
        self, dynamic_id: str
    ) -> Bilidyndetail | None:
        """
        根据动态id获取特定动态详情
        :param dynamic_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        """
        async with self.async_session() as session:
            sql = (
                select(Bilidyndetail)
                .where(Bilidyndetail.dynamic_id_int == int(dynamic_id))
                .limit(1)
            )
            result = await session.execute(sql)
            return result.scalars().first()

    @log_sql_retry_wrapper()
    async def get_all_dynamic_detail_by_rid(self, rid: str) -> Bilidyndetail | None:
        """
        根据动态id获取特定动态详情
        :param rid: 动态rid
        :return: Bilidyndetail
        """
        async with self.async_session() as session:
            sql = (
                select(Bilidyndetail).where(Bilidyndetail.rid_int == int(rid)).limit(1)
            )
            result = await session.execute(sql)
            return result.scalars().first()

    @log_sql_retry_wrapper()
    async def get_lotDetail_by_lot_id(self, lot_id: int) -> Lotdata | None:
        """
        根据动态id获取所有详情
        :param lot_id: 动态id
        :return:[{...}, {...}] dynAllDetail dict
        """
        async with self.async_session() as session:
            sql = select(Lotdata).where(Lotdata.lottery_id == lot_id).limit(1)
            result = await session.execute(sql)
            return result.scalars().first()

    @log_sql_retry_wrapper()
    async def get_lotDetail_ls_by_lot_ids(
        self, lot_id_ls: List[int]
    ) -> Sequence[Lotdata]:
        async with self.async_session() as session:
            sql = select(Lotdata).where(Lotdata.lottery_id.in_(lot_id_ls))
            result = await session.execute(sql)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def get_rid_bili_dyn_detail(
        self, is_asc: bool = False, is_available_data: bool = False
    ) -> Bilidyndetail | None:
        where_clause = [func.length(Bilidyndetail.rid_int) < 18]
        if is_available_data:
            where_clause.append(Bilidyndetail.dynamic_id_int > 0)
        async with self.async_session() as session:
            if is_asc:
                result = await session.execute(
                    select(Bilidyndetail)
                    .where(*where_clause)
                    .order_by(Bilidyndetail.rid_int.asc())
                    .limit(1)
                )
                return result.scalars().first()
            batch_size = 1000
            # 查询指定数量的rid，按降序排列
            result = await session.execute(
                select(Bilidyndetail.rid_int)
                .where(*where_clause)
                .order_by(Bilidyndetail.rid_int.desc())
                .limit(batch_size)
            )

            rids = np.array(
                [int(row[0]) for row in result], dtype=np.int64
            )  # 将rid转换为NumPy数组

            if len(rids) == 0:
                return None

            # 计算相邻rid之间的差异
            differences = rids[:-1] - rids[1:]

            # 找到第一个不连续的位置
            first_non_consecutive_idx = np.where(differences != 1)[0]

            if len(first_non_consecutive_idx) > 0:
                max_consecutive_id = rids[first_non_consecutive_idx[0]]
            else:
                max_consecutive_id = rids[-1]

            # 查询并返回完整的Bilidyndetail记录
            detail_result = await session.execute(
                select(Bilidyndetail)
                .where(Bilidyndetail.rid_int == max_consecutive_id)
                .limit(1)
            )
            return detail_result.scalars().first()

    @log_sql_retry_wrapper()
    async def get_latest_rid(self) -> int | None:
        batch_size = 1000
        async with self.async_session() as session:
            # 查询指定数量的rid，按降序排列
            result = await session.execute(
                select(Bilidyndetail.rid)
                .where(func.length(Bilidyndetail.rid_int) < 18)
                .order_by(Bilidyndetail.rid_int.desc())
                .limit(batch_size)
            )

            rids = np.array(
                [int(row[0]) for row in result], dtype=np.int64
            )  # 将rid转换为NumPy数组

            if len(rids) == 0:
                return None

            # 计算相邻rid之间的差异
            differences = rids[:-1] - rids[1:]

            # 找到第一个不连续的位置
            first_non_consecutive_idx = np.where(differences != 1)[0]

            if len(first_non_consecutive_idx) > 0:
                max_consecutive_id = rids[first_non_consecutive_idx[0]]
            else:
                max_consecutive_id = rids[-1]

            return max_consecutive_id + 1  # +1 是最大的一个，不加一是第二大的

    @log_sql_retry_wrapper()
    async def query_dynData_by_key_word(
        self, key_word_list: [str], between_ts: List[int] | None = None
    ) -> Sequence[Bilidyndetail]:
        """
        通过like查询需要的动态
        :param key_word_list:
        :param between_ts:
        :return:
        """
        async with self.async_session() as session:
            stmt = select(Bilidyndetail)
            # 动态生成like条件
            conditions = [
                Bilidyndetail.dynData.like(f"%{keyword}%") for keyword in key_word_list
            ]
            if between_ts and type(between_ts) == list and len(between_ts) == 2:
                between_ts.sort()
                conditions.append(
                    and_(
                        func.STR_TO_DATE(
                            Bilidyndetail.dynamic_created_time, "%Y-%m-%d %H:%i:%s"
                        )
                        >= func.FROM_UNIXTIME(between_ts[0]),
                        func.STR_TO_DATE(
                            Bilidyndetail.dynamic_created_time, "%Y-%m-%d %H:%i:%s"
                        )
                        <= func.FROM_UNIXTIME(between_ts[1]),
                    )
                )
            stmt = stmt.where(and_(*conditions)).order_by(
                Bilidyndetail.dynamic_id_int.desc()
            )

            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def query_dynData_by_date(
        self, between_ts: list[int] = None
    ) -> Sequence[Bilidyndetail]:
        """
        通过日期查询需要的动态，默认查询当天
        :param between_ts:
        :param RegExp:
        :return:
        """
        async with self.async_session() as session:
            if between_ts is None:
                today_start = datetime.datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                today_end = (
                    today_start
                    + datetime.timedelta(days=1)
                    - datetime.timedelta(seconds=1)
                )
                between_ts = [int(today_start.timestamp()), int(today_end.timestamp())]
            if len(between_ts) != 2:
                raise ValueError("错误的日期间隔")

                # 使用 FROM_UNIXTIME 将 Unix 时间戳转换为 MySQL 的日期时间格式
            between_fake_dyn_id = [
                ts_2_fake_dynamic_id(between_ts[0]) - 10000000000,
                ts_2_fake_dynamic_id(between_ts[1]) + 10000000000,
            ]

            stmt = (
                select(Bilidyndetail)
                .where(
                    and_(
                        Bilidyndetail.dynamic_id_int >= between_fake_dyn_id[0],
                        Bilidyndetail.dynamic_id_int <= between_fake_dyn_id[1],
                    )
                )
                .order_by(
                    func.STR_TO_DATE(
                        Bilidyndetail.dynamic_created_time, "%Y-%m-%d %H:%i:%s"
                    ).desc()
                )
            )

            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def query_lot_data_by_business_id(
        self, business_id: int | str
    ) -> Lotdata | None:
        async with self.async_session() as session:
            sql = (
                select(Lotdata)
                .where(Lotdata.business_id == business_id)
                .order_by(Lotdata.business_id.desc())
                .limit(1)
            )
            result = await session.execute(sql)
            return result.scalars().first()

    @log_sql_retry_wrapper()
    async def query_official_lottery_by_timelimit(
        self, time_limit: int = 24 * 3600, order_by_ts_desc=True
    ) -> Sequence[Lotdata]:
        """
        通过日期查询需要的动态，默认查询当天
        :return:
        """
        async with self.async_session() as session:
            now_ts = int(time.time())
            target_ts = now_ts + time_limit

            stmt = select(Lotdata).where(
                and_(
                    Lotdata.status == 0,
                    Lotdata.business_type == 1,
                    Lotdata.lottery_time >= now_ts,
                    Lotdata.lottery_time <= target_ts,
                )
            )
            if order_by_ts_desc:
                stmt = stmt.order_by(Lotdata.lottery_time.desc())
            else:
                stmt = stmt.order_by(Lotdata.lottery_time.asc())

            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def query_lottery(
        self, q: BiliLotDataQueryModel
    ) -> tuple[Sequence[Lotdata], int]:
        """
        通过查询模型查询抽奖动态记录
        :param q: BiliLotDataQueryModel 查询模型，包含分页、筛选等参数
        :return: (记录列表, 总数)
        """
        now_ts = int(time.time())
        base_conditions = [
            Lotdata.business_type == q.business_type.value,
        ]
        # 状态筛选
        if q.status is not None:
            base_conditions.append(Lotdata.status == q.status.value)

            if q.status is BiliLotDataStatusEnum.UNFINISHED:
                base_conditions.append(Lotdata.lottery_time >= now_ts)
        
        # 时间范围筛选
        if q.start_ts is not None:
            base_conditions.append(Lotdata.lottery_time >= q.start_ts)

        if q.end_ts is not None:
            base_conditions.append(Lotdata.lottery_time <= q.end_ts)

        # sender_uid 筛选
        if q.sender_uid is not None:
            base_conditions.append(Lotdata.sender_uid == q.sender_uid)

        # 参与人数范围筛选
        if q.min_participants is not None:
            base_conditions.append(Lotdata.participants >= q.min_participants)

        if q.max_participants is not None:
            base_conditions.append(Lotdata.participants <= q.max_participants)

        # 关键词筛选（对抽奖结果描述做 LIKE 模糊匹配）
        if q.keyword is not None and q.keyword.strip():
            base_conditions.append(Lotdata.lottery_result.like(f"%{q.keyword.strip()}%"))

        # 大奖筛选：通过子表 t_lot_extra_info 过滤
        if q.is_grand_prize is True:
            grand_subq = (
                select(LotExtraInfo.lottery_id)
                .where(LotExtraInfo.is_grand_prize == 1)
            )
            base_conditions.append(Lotdata.lottery_id.in_(grand_subq))
        elif q.is_grand_prize is False:
            # 非大奖 = 子表中没有记录，或子表中 is_grand_prize=0
            grand_subq = (
                select(LotExtraInfo.lottery_id)
                .where(LotExtraInfo.is_grand_prize == 1)
            )
            base_conditions.append(Lotdata.lottery_id.not_in(grand_subq))

        # 时间快捷筛选（优先级高于单独的 start_ts/end_ts）
        import datetime as dt
        if q.created_at_preset is not None:
            days = int(q.created_at_preset.value.replace("d", ""))
            threshold = dt.datetime.fromtimestamp(now_ts - days * 86400)
            base_conditions.append(Lotdata.created_at >= threshold)
        if q.pub_time_preset is not None:
            days = int(q.pub_time_preset.value.replace("d", ""))
            base_conditions.append(Lotdata.ts >= (now_ts - days * 86400))

        # 构建查询语句（仅查主表 lotdata，extra_info 由调用方通过 get_extra_info_map 独立批量查询）
        stmt = (
            select(Lotdata)
            .where(and_(*base_conditions))
        )

        # 排序：优先使用 q.sort_by，否则按 lottery_time 升序
        if q.sort_by is not None:
            sort_column = getattr(Lotdata, q.sort_by.value, Lotdata.lottery_time)
            if q.sort_order == SortOrderEnum.asc:
                stmt = stmt.order_by(sort_column.asc())
            else:
                stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(Lotdata.lottery_time.asc())

        # 应用分页：page_num 从 1 开始，offset 由 BiliLotDataQueryModel.offset 统一计算
        # 未给分页参数时默认 limit 1000，避免全量返回导致性能问题
        if q.page_num and q.page_size:
            stmt = stmt.limit(q.page_size).offset(q.offset)
        else:
            stmt = stmt.limit(1000)

        async with self.async_session() as session:
            result = await session.execute(stmt)
            records = result.scalars().all()

            # 使用覆盖索引进行 COUNT 查询，避免全表扫描
            count_stmt = select(func.count(Lotdata.lottery_id)).where(
                and_(*base_conditions)
            )
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            return records, total_count

    @log_sql_retry_wrapper()
    async def query_official_lottery_by_timelimit_page_offset(
        self, q: BiliLotDataQueryModel
    ) -> tuple[Sequence[Lotdata], int]:
        """
        查询官方抽奖（business_type=1），通过 BiliLotDataQueryModel 统一筛选
        :param q: BiliLotDataQueryModel，business_type 固定为 Official
        :return: (记录列表, 总数)
        """
        return await self.query_lottery(
            BiliLotDataQueryModel(
                business_type=LotteryBusinessType.Official,
                status=q.status,
                page_num=q.page_num,
                page_size=q.page_size,
                start_ts=q.start_ts,
                end_ts=q.end_ts,
                sender_uid=q.sender_uid,
                min_participants=q.min_participants,
                max_participants=q.max_participants,
                sort_by=q.sort_by,
                sort_order=q.sort_order,
                is_grand_prize=q.is_grand_prize,
            )
        )

    @log_sql_retry_wrapper()
    async def query_charge_lottery_by_timelimit_page_offset(
        self, q: BiliLotDataQueryModel
    ) -> tuple[Sequence[Lotdata], int]:
        """
        查询充电抽奖（business_type=12），通过 BiliLotDataQueryModel 统一筛选
        :param q: BiliLotDataQueryModel，business_type 固定为 Charge
        :return: (记录列表, 总数)
        """
        return await self.query_lottery(
            BiliLotDataQueryModel(
                business_type=LotteryBusinessType.Charge,
                status=q.status,
                page_num=q.page_num,
                page_size=q.page_size,
                start_ts=q.start_ts,
                end_ts=q.end_ts,
                sender_uid=q.sender_uid,
                min_participants=q.min_participants,
                max_participants=q.max_participants,
                sort_by=q.sort_by,
                sort_order=q.sort_order,
                is_grand_prize=q.is_grand_prize,
            )
        )

    # endregion

    # region 更新和新增内容
    @log_sql_retry_wrapper()
    async def upsert_DynDetail(
        self,
        doc_id: str | int,
        dynamic_id: str | int,
        dynData: dict | None,
        lot_id: str | int | None,
        dynamic_created_time: str | None,
    ):
        async with self.async_session() as session:
            if dynData:
                parsed_dyn_data = json.dumps(dynData, ensure_ascii=False)
            else:
                parsed_dyn_data = None
            if lot_id:
                sql = """
                      INSERT
                      IGNORE INTO lotdata (lottery_id)
    VALUES (:lottery_id); \
                      """
                await session.execute(text(sql), {"lottery_id": lot_id})
            stmt = (
                insert(Bilidyndetail)
                .values(
                    rid=doc_id,
                    dynamic_id=dynamic_id,
                    dynData=parsed_dyn_data,
                    lot_id=lot_id,
                    dynamic_created_time=dynamic_created_time,
                )
                .on_duplicate_key_update(
                    dynamic_id=dynamic_id,
                    dynData=parsed_dyn_data,
                    lot_id=lot_id,
                    dynamic_created_time=dynamic_created_time,
                )
            )

            await session.execute(stmt)
            await session.commit()

    @classmethod
    def process_resp_data_dict_2_lotdata(cls, lot_data_resp_data: dict) -> Lotdata:
        lot_data_dict = deepcopy(lot_data_resp_data)
        # 获取Lotdata的所有列名
        columns = Lotdata.__table__.columns.keys()

        # 分离出不在Lotdata模型中的键值对
        custom_extra = {
            k: lot_data_dict.pop(k)
            for k in list(lot_data_dict.keys())
            if k not in columns and k != "lottery_id"
        }
        if custom_extra:
            lot_data_dict["custom_extra_key"] = json.dumps(custom_extra)
        else:
            lot_data_dict["custom_extra_key"] = None
        cls._process_2_save_data([lot_data_dict])
        return Lotdata(**lot_data_dict)

    @log_sql_retry_wrapper()
    async def upsert_lot_detail(self, lot_data_dict: dict):
        """

        :param lot_data_dict: lottery_notice的响应的data
        :return:更新 返回{'mode':'update'}
                插入 返回{'mode':'insert'}
        """
        # 入库时进行 LLM 大奖判断（dyndetail 专用）
        from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info_for_dyndetail

        prize_cmts = [
            lot_data_dict.get("first_prize_cmt"),
            lot_data_dict.get("second_prize_cmt"),
            lot_data_dict.get("third_prize_cmt"),
        ]
        lottery_text = " ".join(filter(lambda a: a, prize_cmts)).strip()
        if lottery_text:
            try:
                result = await extract_prize_info_for_dyndetail(dyn_content=lottery_text)
                is_grand_prize = int(result.result.is_grand_prize)
            except Exception as e:
                self.log.error(f"LLM 大奖判断失败，默认 0: {e}")
                is_grand_prize = 0
        else:
            is_grand_prize = 0

        async with self.async_session() as session:
            lottery_id = lot_data_dict.get("lottery_id")
            existing_record = await session.execute(
                select(Lotdata).where(Lotdata.lottery_id == lottery_id)
            )
            _exists = existing_record.scalars().first() is not None

            # 使用 process_resp_data_dict_2_lotdata 过滤掉不属于 Lotdata 的字段（如 is_grand_prize）
            lot_data_obj = self.process_resp_data_dict_2_lotdata(lot_data_dict)
            await session.merge(lot_data_obj)
            await session.flush()  # 确保 lotdata 父行先写入，否则 t_lot_extra_info 外键约束会失败

            # 将 SVM 大奖判断结果写入独立子表 t_lot_extra_info
            lottery_id = lot_data_dict.get("lottery_id")
            if lottery_id is not None:
                await self._upsert_extra_info(
                    session=session,
                    lottery_id=int(lottery_id),
                    is_grand_prize=is_grand_prize,
                )

            # 判断是插入还是更新
            mode = "insert" if _exists == 1 else "update"
            await session.commit()
            return {"mode": mode}

    @staticmethod
    async def _upsert_extra_info(session, lottery_id: int, is_grand_prize: int) -> None:
        """原子 upsert：将 SVM 大奖判断结果写入 t_lot_extra_info"""
        stmt = insert(LotExtraInfo).values(
            lottery_id=lottery_id,
            is_grand_prize=is_grand_prize,
        )
        stmt = stmt.on_duplicate_key_update(
            is_grand_prize=stmt.inserted.is_grand_prize,
            updated_at=text('CURRENT_TIMESTAMP'),
        )
        await session.execute(stmt)

    @log_sql_retry_wrapper()
    async def batch_check_existing_extra_info(
        self, lottery_ids: list[int]
    ) -> set[int]:
        """批量查询已存在附加信息的 lottery_id 集合（用于手动回填脚本跳过已判记录）"""
        if not lottery_ids:
            return set()
        async with self.async_session() as session:
            stmt = (
                select(LotExtraInfo.lottery_id)
                .where(LotExtraInfo.lottery_id.in_(lottery_ids))
            )
            res = await session.execute(stmt)
            return {row[0] for row in res.all()}

    @log_sql_retry_wrapper()
    async def batch_save_extra_info(
        self, flags: dict[int, int]
    ) -> None:
        """批量保存附加信息到 t_lot_extra_info（key=lottery_id, value=is_grand_prize）"""
        if not flags:
            return
        async with self.async_session() as session:
            async with session.begin():
                for lottery_id, is_grand_prize in flags.items():
                    await self._upsert_extra_info(
                        session=session,
                        lottery_id=lottery_id,
                        is_grand_prize=is_grand_prize,
                    )

    @log_sql_retry_wrapper()
    async def get_extra_info_map(
        self, lottery_ids: list[int]
    ) -> dict[int, LotExtraInfo]:
        """批量查询 extra_info，返回 {lottery_id: LotExtraInfo}。
        与主表查询完全解耦，调用方先查 lotdata，再批量查 extra_info 自行合并。
        """
        if not lottery_ids:
            return {}
        async with self.async_session() as session:
            stmt = select(LotExtraInfo).filter(
                LotExtraInfo.lottery_id.in_(lottery_ids)
            )
            res = await session.execute(stmt)
            rows = res.scalars().all()
            return {row.lottery_id: row for row in rows}

    # endregion
    @log_sql_retry_wrapper()
    async def get_all_lot_not_drawn(self) -> Sequence[Lotdata]:
        """
        查询所有未开奖的 Lotdata 数据，并加载关联的 Bilidyndetail 数据。
        :return:
        """
        async with self.async_session() as session:
            stmt = (
                select(Lotdata)
                .options(
                    selectinload(Lotdata.bilidyndetail),
                    selectinload(Lotdata.article_pub_record),
                )
                .where(
                    and_(
                        Lotdata.lottery_result.is_(None),
                        Lotdata.status != -1,
                        Lotdata.lottery_time <= func.unix_timestamp(),
                    )
                )
                .order_by(Lotdata.lottery_id)
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

    @log_sql_retry_wrapper()
    async def update_lot_detail(self, *, lottery_id: str | int, **kwargs):
        async with self.async_session() as session:
            stmt = (
                update(Lotdata).where(Lotdata.lottery_id == lottery_id).values(**kwargs)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @log_sql_retry_wrapper()
    async def get_all_lot_with_no_business_id(self) -> Sequence[Lotdata]:
        """
        查询所有没有加载好数据的 Lotdata ，并加载关联的 Bilidyndetail 数据。
        :return:
        """
        async with self.async_session() as session:
            stmt = (
                select(Lotdata)
                .options(selectinload(Lotdata.bilidyndetail))
                .where(
                    and_(
                        Lotdata.business_id.is_(None),
                        Lotdata.bilidyndetail.any(Bilidyndetail.rid.is_not(None)),
                    )
                )
                .order_by(Lotdata.lottery_id)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def get_all_lottery_result_rank(
        self,
        start_ts: int | None = None,
        end_ts: int | None = None,
        business_type: Literal[1, 10, 12, 0] | None = None,
        rank_type: (
            BiliLotStatisticRankTypeEnum | None
        ) = BiliLotStatisticRankTypeEnum.total,
    ) -> list[tuple[int, int]]:
        async with self.async_session() as session:
            if rank_type == BiliLotStatisticRankTypeEnum.total:
                query = text(
                    f"""SELECT uid, 
COUNT(*) AS atari_count
FROM (SELECT jt.uid FROM 
lotData,
JSON_TABLE(lotData.lottery_result, '$.first_prize_result[*]' 
COLUMNS (
uid BIGINT PATH '$.uid'
)
) AS jt
WHERE 
JSON_VALID(lotData.lottery_result)
{'AND lotData.business_type = :business_type' if business_type else ''}
{'AND lotData.lottery_time >= :start_ts' if start_ts else ''}
{'AND lotData.lottery_time <= :end_ts' if end_ts else ''}
UNION ALL

SELECT 
jt.uid
FROM 
lotData,
JSON_TABLE(lotData.lottery_result, '$.second_prize_result[*]' 
COLUMNS (
uid BIGINT PATH '$.uid'
)
) AS jt
WHERE 
JSON_VALID(lotData.lottery_result)
{'AND lotData.business_type = :business_type' if business_type else ''}
{'AND lotData.lottery_time >= :start_ts' if start_ts else ''}
{'AND lotData.lottery_time <= :end_ts' if end_ts else ''}
UNION ALL

SELECT 
jt.uid
FROM 
lotData,
JSON_TABLE(lotData.lottery_result, '$.third_prize_result[*]' 
COLUMNS (
uid BIGINT PATH '$.uid'
)
) AS jt
WHERE 
JSON_VALID(lotData.lottery_result)
{'AND lotData.business_type = :business_type' if business_type else ''}
{'AND lotData.lottery_time >= :start_ts' if start_ts else ''}
{'AND lotData.lottery_time <= :end_ts' if end_ts else ''}
) AS combined_uids
WHERE uid IS NOT NULL
GROUP BY uid
ORDER BY atari_count DESC,uid DESC;
                    """
                )
                result = await session.execute(
                    query,
                    {
                        "business_type": business_type,
                        "start_ts": start_ts,
                        "end_ts": end_ts,
                    },
                )
                return [(row.uid, row.atari_count) for row in result]
            else:
                prize_key = f"{rank_type.value}_prize_result"
                query = text(
                    f"""
SELECT
	jt.uid,
	COUNT(*) as atari_count
FROM
	lotData,
	JSON_TABLE(
		JSON_EXTRACT(
			lottery_result, '$.{prize_key}'
		),
		'$[*]' COLUMNS(uid BIGINT PATH '$.uid')
	) AS jt
WHERE
	JSON_VALID(lottery_result)
	{'AND business_type = :business_type' if business_type else ''}
	{'AND lotData.lottery_time >= :start_ts' if start_ts else ''}
    {'AND lotData.lottery_time <= :end_ts' if end_ts else ''}
GROUP BY
	jt.uid
ORDER BY
	atari_count DESC,
	jt.uid DESC;
                    """
                )
                result = await session.execute(
                    query,
                    {
                        "business_type": business_type,
                        "start_ts": start_ts,
                        "end_ts": end_ts,
                    },
                )

                return [(row.uid, row.atari_count) for row in result]

    @log_sql_retry_wrapper()
    async def get_lottery_result(
        self,
        uid: int | str,
        start_ts: int = 0,
        end_ts: int = 0,
        business_type: Literal[1, 10, 12, 0] = None,
        rank_type: Optional[BiliLotStatisticRankTypeEnum] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> tuple[Sequence[Lotdata], int]:

        # 使用async with语句创建一个异步的session
        async with self.async_session() as session:
            # 将uid转换为整数
            uid_int = int(uid)

            # 创建一个查询Lotdata表的查询对象
            query = select(Lotdata)
            # 创建一个查询Lotdata表记录总数的查询对象
            count_query = select(func.count()).select_from(Lotdata)
            # 如果rank_type存在且不等于total
            if rank_type and rank_type != BiliLotStatisticRankTypeEnum.total:
                # 获取prize_key
                prize_key = f"{rank_type.value}_prize_result"
                # 获取json_path
                json_path = text(f"'$.{prize_key}[*].uid'")
                # 创建条件
                condition = func.json_contains(
                    func.json_extract(Lotdata.lottery_result, json_path),
                    func.cast(uid_int, JSON),
                )
                # 将条件添加到查询对象中
                query = query.where(condition)
                # 将条件添加到查询记录总数的查询对象中
                count_query = count_query.where(condition)
            else:
                # 创建一个空的conditions列表
                conditions = []
                # 遍历prize
                for prize in ["first", "second", "third"]:
                    # 获取json_path
                    json_path = text(f"'$.{prize}_prize_result[*].uid'")
                    # 创建条件
                    conditions.append(
                        func.json_contains(
                            func.json_extract(Lotdata.lottery_result, json_path),
                            func.cast(uid_int, JSON),
                        )
                    )
                # 将条件添加到查询对象中
                query = query.where(or_(*conditions))
                # 将条件添加到查询记录总数的查询对象中
                count_query = count_query.where(or_(*conditions))
            # 如果business_type存在
            if business_type:
                # 将business_type添加到查询对象中
                query = query.where(Lotdata.business_type == business_type)
                # 将business_type添加到查询记录总数的查询对象中
                count_query = count_query.where(Lotdata.business_type == business_type)
            if start_ts:
                # 将start_ts添加到查询对象中
                query = query.where(Lotdata.lottery_time >= start_ts)
                # 将start_ts添加到查询记录总数的查询对象中
                count_query = count_query.where(Lotdata.lottery_time >= start_ts)
            if end_ts:
                # 将end_ts添加到查询对象中
                query = query.where(Lotdata.lottery_time <= end_ts)
                # 将end_ts添加到查询记录总数的查询对象中
                count_query = count_query.where(Lotdata.lottery_time <= end_ts)

            # 执行查询记录总数的查询对象
            total_result = await session.execute(count_query)
            # 获取记录总数
            total = total_result.scalar()

            # 将查询对象按照lottery_id降序排列
            query = query.order_by(Lotdata.lottery_id.desc())
            # 如果offset和limit存在
            if offset is not None and limit is not None:
                # 将offset和limit添加到查询对象中
                query = query.offset(offset).limit(limit)

            # 执行查询对象
            results = await session.execute(query)
            # 返回查询结果和记录总数
            return results.scalars().all(), total

    @log_sql_retry_wrapper()
    async def get_all_bili_user_info(self) -> list[BiliUserInfoSimple]:
        async with self.async_session() as session:
            query = text(
                """
                         WITH all_results AS (SELECT jt.uid,
                                                     jt.name,
                                                     jt.face,
                                                     lotdata.lottery_id,
                                                     ROW_NUMBER() OVER (
				PARTITION BY
					jt.uid
				ORDER BY
					lotdata.lottery_id DESC
			) AS rn
                                              FROM lotData,
                                                   JSON_TABLE(
                                                           lotData.lottery_result,
                                                           '$.first_prize_result[*]' COLUMNS (
					uid BIGINT PATH '$.uid', `name` TEXT PATH '$.name',
					face TEXT PATH '$.face'
				)
                                                   ) AS jt
                                              WHERE JSON_VALID(lotData.lottery_result)
                                              UNION ALL
                                              SELECT jt.uid,
                                                     jt.name,
                                                     jt.face,
                                                     lotdata.lottery_id,
                                                     ROW_NUMBER() OVER (
				PARTITION BY
					jt.uid
				ORDER BY
					lotdata.lottery_id DESC
			) AS rn
                                              FROM lotData,
                                                   JSON_TABLE(
                                                           lotData.lottery_result,
                                                           '$.second_prize_result[*]' COLUMNS (
					uid BIGINT PATH '$.uid', `name` TEXT PATH '$.name',
					face TEXT PATH '$.face'
				)
                                                   ) AS jt
                                              WHERE JSON_VALID(lotData.lottery_result)
                                              UNION ALL
                                              SELECT jt.uid,
                                                     jt.name,
                                                     jt.face,
                                                     lotdata.lottery_id,
                                                     ROW_NUMBER() OVER (
				PARTITION BY
					jt.uid
				ORDER BY
					lotdata.lottery_id DESC
			) AS rn
                                              FROM lotData,
                                                   JSON_TABLE(
                                                           lotData.lottery_result,
                                                           '$.third_prize_result[*]' COLUMNS (
					uid BIGINT PATH '$.uid', `name` TEXT PATH '$.name',
					face TEXT PATH '$.face'
				)
                                                   ) AS jt
                                              WHERE JSON_VALID(lottery_result)),
                              ranked_results AS (SELECT uid,
                                                        name,
                                                        face,
                                                        ROW_NUMBER() OVER (
				PARTITION BY
					uid
				ORDER BY
					lottery_id DESC
			) AS rn
                                                 FROM all_results)
                         SELECT uid,
                                name,
                                face
                         FROM ranked_results
                         WHERE rn = 1
                         ORDER BY uid
                         """
            )
            # 执行查询
            result = await session.execute(query)

            # 获取结果
            rows = [
                BiliUserInfoSimple(uid=str(row.uid), name=row.name, face=row.face)
                for row in result
            ]
            # 如果没有更多数据返回空列表
            if not rows:
                return []
            # 返回当前批次的数据以及下一个批次的起点
            return rows  # 返回当前批次的数据和最后一个uid作为下次查询的起点

    @log_sql_retry_wrapper()
    async def query_all_lottery_data(self) -> Sequence[Lotdata]:
        async with self.async_session() as session:
            stmt = select(Lotdata)
            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def get_all_lot_before_lottery_time(self) -> Sequence[Lotdata]:
        async with self.async_session() as session:
            stmt = select(Lotdata).filter(
                and_(Lotdata.lottery_time > int(time.time()), Lotdata.status == 0)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @log_sql_retry_wrapper()
    async def get_article_pub_record_round_id(self) -> int | None:
        async with self.async_session() as session:
            stmt = (
                select(ArticlePubRecord.round_id)
                .order_by(ArticlePubRecord.round_id.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            if row := result.one_or_none():
                return row.round_id
            return None

    @log_sql_retry_wrapper()
    async def upsert_article_pub_record(self, round_id: int, *business_ids):
        async with self.async_session() as session:
            stmt = insert(ArticlePubRecord).values(
                [
                    {"round_id": round_id, "lot_data_business_id": x}
                    for x in business_ids
                ]
            )
            stmt.on_duplicate_key_update(round_id=round_id)
            await session.execute(stmt)
            await session.commit()

    @log_sql_retry_wrapper()
    async def delete_dyn_detail_by_dyn_ids(self, id_list: list[int]):
        async with self.async_session() as session:
            await session.execute(
                delete(Bilidyndetail).where(Bilidyndetail.dynamic_id_int.in_(id_list))
            )
            await session.commit()

    @log_sql_retry_wrapper()
    async def delete_dyn_detail_by_dyn_rids(self, rid_list: list[str | int]):
        if not rid_list:
            return
        chunk_size = 100
        successful_chunks = 0
        failed_chunks = 0

        for i in range(0, len(rid_list), chunk_size):
            chunk = rid_list[i : i + chunk_size]

            # 对每个分块单独应用重试机制
            @log_sql_retry_wrapper()
            async def process_chunk(chunk_data):
                async with self.async_session() as session:
                    try:
                        # 执行数据库操作
                        stmt = delete(Bilidyndetail).where(
                            Bilidyndetail.rid.in_(chunk_data)
                        )
                        await session.execute(stmt)
                        await session.commit()
                        return len(chunk_data)
                    except Exception as e:
                        await session.rollback()
                        raise

            processed_count = await process_chunk(chunk)
            successful_chunks += 1
            self.log.debug(
                f"成功处理分块 {successful_chunks}，包含 {processed_count} 条记录"
            )

        self.log.info(
            f"分块操作完成: 成功 {successful_chunks} 个分块, 失败 {failed_chunks} 个分块"
        )

    def gen_bai(self, lottery_result, single_lottery_result_data, lot_rank: int):
        bili_atari_info = BiliAtariInfo(
            mid=single_lottery_result_data.get("uid"),
            hongbao_money=single_lottery_result_data.get("hongbao_money"),
            atari_lot_id=lottery_result.lottery_id,
            atari_lot_rank=lot_rank,
            atari_lot_type=lottery_result.business_type,
            atari_timestamp=datetime.datetime.fromtimestamp(
                lottery_result.lottery_time
            ),
        )
        bili_atari_info.bili_user_info = BiliUserInfo(
            uid=single_lottery_result_data.get("uid"),
            name=single_lottery_result_data.get("name"),
            face=single_lottery_result_data.get("face"),
        )
        return bili_atari_info

    @log_sql_retry_wrapper()
    async def sync_all_lottery_result_2_bili_user_info(self, *, lottery_id: int = None):
        """
        同步所有抽奖结果到用户信息表
        :param lottery_id: 抽奖id  如果为None则同步所有抽奖结果
        :return:
        """
        where_clause = []
        if lottery_id:
            where_clause.append(Lotdata.lottery_id == lottery_id)
        else:
            where_clause.append(Lotdata.lottery_result.isnot(None))
        async with self.async_session() as session:
            stmt = select(
                func.JSON_EXTRACT(Lotdata.lottery_result, "$").label("lottery_result"),
                Lotdata.lottery_id,
                Lotdata.business_type,
                Lotdata.lottery_time,
            ).where(*where_clause)
            result = await session.execute(stmt)
            all_lottery_result = result.all()
            bili_atari_info_list = []

            for x in all_lottery_result:
                lottery_result = json.loads(x.lottery_result)
                for y in lottery_result.get("first_prize_result", []):
                    bai = self.gen_bai(x, y, AtariLotRankEnum.first_prize.value)
                    bili_atari_info_list.append(bai)
                for y in lottery_result.get("second_prize_result", []):
                    bai = self.gen_bai(x, y, AtariLotRankEnum.second_prize.value)
                    bili_atari_info_list.append(bai)
                for y in lottery_result.get("third_prize_result", []):
                    bai = self.gen_bai(x, y, AtariLotRankEnum.third_prize.value)
                    bili_atari_info_list.append(bai)
        self.log.debug(
            f"sync_all_lottery_result_2_bili_user_info: {len(bili_atari_info_list)}"
        )
        await lottery_data_statistic_sql_helper.insert_lot_prize_count_bulk(
            bili_atari_info_list=bili_atari_info_list
        )


grpc_sql_helper = SQLHelper()

if __name__ == "__main__":

    async def _test_get_all_lot_not_drawn():
        res = await grpc_sql_helper.get_all_lot_not_drawn()
        print(res)

    async def _test_query_official_lottery_by_timelimit_page_offset():
        res = await grpc_sql_helper.query_official_lottery_by_timelimit_page_offset(
            page_number=1, page_size=10
        )
        print(res)

    async def _test_query_dynData_by_date():
        res = await grpc_sql_helper.query_dynData_by_date([1736309461, 1736409461])
        print(res)

    async def _test_get_lottery_result():
        res = await grpc_sql_helper.get_lottery_result(uid=4237378)
        print(res)

    asyncio.run(_test_get_lottery_result())
