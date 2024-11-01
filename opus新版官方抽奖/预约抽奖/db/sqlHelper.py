import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute
from typing import Callable, Union
from sqlalchemy import create_engine, inspect, select, and_, func
import CONFIG
from opus新版官方抽奖.预约抽奖.db.models import TReserveRoundInfo, TUpReserveRelationInfo
from opus新版官方抽奖.预约抽奖.etc.log.base_log import reserve_lot_log

lock = asyncio.Lock()


def lock_wrapper(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                reserve_lot_log.exception(e)
                await asyncio.sleep(3)

    return wrapper


class SqlHelper:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        _SQL_URI = CONFIG.MYSQL.bili_reserve_URI
        self._engine = create_async_engine(_SQL_URI)
        self._session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )
        self.reserve_info_column_names = [
        ]

    async def init(self):
        def get_column_name(conn: str) -> list[str]:
            inspector = inspect(conn)
            return inspector.get_columns(TUpReserveRelationInfo.__tablename__)

        async with self._session().bind.connect() as connection:
            column_name_dict = await connection.run_sync(get_column_name)
            self.reserve_info_column_names = list(map(lambda el: el.get('name'), column_name_dict))

    @staticmethod
    def solve_reserve_resp(resp_dict: dict) -> dict:
        """
        解决预约返回的值
        :param resp_dict:
        :return:
        """
        ret_dict = {}
        for k, v in resp_dict.items():
            if type(v) is dict:
                ret_dict.update(**SqlHelper.solve_reserve_resp(v))
            elif v is None:
                pass
            else:
                ret_dict.update({k: v})
        return ret_dict

    @lock_wrapper
    async def add_reserve_info_by_resp_dict(self, origin_resp_dict: dict, round_id: int):
        """
        添加预约信息
        :param resp_dict:
        :return:
        """
        if not self.reserve_info_column_names:
            await self.init()
        resp_dict = SqlHelper.solve_reserve_resp(origin_resp_dict)
        new_field = list(set(resp_dict.keys()) - set(list(self.reserve_info_column_names)))
        if new_field:
            for k in new_field:
                resp_dict.update({"new_field": {k: resp_dict.pop(k)}})
        reserve_info = TUpReserveRelationInfo(**resp_dict)
        reserve_info.raw_JSON = origin_resp_dict
        reserve_info.reserve_round_id = round_id
        if new_field:
            reserve_info.new_field = str(new_field)
        async with self._session() as session:
            async with session.begin():
                await session.merge(reserve_info)

    @lock_wrapper
    async def get_latest_reserve_round(self, readonly=False) -> TReserveRoundInfo:
        async with self._session() as session:
            sql = select(TReserveRoundInfo).order_by(TReserveRoundInfo.id.desc()).limit(1)
            result = await session.execute(sql)
            result = result.scalars().first()
            if not result:
                tReserveRoundInfo = TReserveRoundInfo(
                    round_id=1,
                    is_finished=False,
                    round_start_ts=int(time.time()),
                    round_add_num=0,
                    round_lot_num=0
                )
                await session.merge(tReserveRoundInfo)
                await session.commit()
                return tReserveRoundInfo
            if result.is_finished and not readonly:
                tReserveRoundInfo = TReserveRoundInfo(
                    round_id=result.round_id + 1,
                    is_finished=False,
                    round_start_ts=int(time.time()),
                    round_add_num=0,
                    round_lot_num=0
                )
                await session.merge(tReserveRoundInfo)
                await session.commit()
                return tReserveRoundInfo
            return result

    @lock_wrapper
    async def get_reserve_by_ids(self, ids) -> Union[TUpReserveRelationInfo, None]:
        async with self._session() as session:
            sql = select(TUpReserveRelationInfo).filter(TUpReserveRelationInfo.ids == ids).order_by(
                TUpReserveRelationInfo.ids.desc()).limit(1)
            result = await session.execute(sql)
            result = result.scalars().first()
            return result

    @lock_wrapper
    async def add_reserve_round_info(self, tReserveRoundInfo: TReserveRoundInfo) -> TReserveRoundInfo:
        async with self._session() as session:
            async with session.begin():
                sql = select(TReserveRoundInfo).filter(
                    TReserveRoundInfo.round_id == tReserveRoundInfo.round_id).order_by(
                    TReserveRoundInfo.round_id.desc()).limit(1)
                result = await session.execute(sql)
                result = result.scalars().first()
                if result:
                    result.is_finished = tReserveRoundInfo.is_finished if tReserveRoundInfo.is_finished is not None else result.is_finished
                    result.round_start_ts = tReserveRoundInfo.round_start_ts if tReserveRoundInfo.round_start_ts is not None else result.round_start_ts
                    result.round_add_num = tReserveRoundInfo.round_add_num if tReserveRoundInfo.round_add_num is not None else result.round_add_num
                    result.round_lot_num = tReserveRoundInfo.round_lot_num if tReserveRoundInfo.round_lot_num is not None else result.round_lot_num
                    await session.flush()
                    session.expunge(result)
                    return result
                else:
                    session.add(tReserveRoundInfo)
                    await session.flush()
                    return tReserveRoundInfo

    @lock_wrapper
    async def get_all_reserve_lottery(self) -> list[TUpReserveRelationInfo]:
        async with self._session() as session:
            sql = select(TUpReserveRelationInfo).filter(TUpReserveRelationInfo.lotteryType == 1).order_by(
                TUpReserveRelationInfo.dynamicId.desc())
            result = await session.execute(sql)
            return result.scalars().all()

    @lock_wrapper
    async def get_reserve_lotterys_by_round_id(self, round_id: int) -> list[TUpReserveRelationInfo]:
        async with self._session() as session:
            sql = select(TUpReserveRelationInfo).filter(
                and_(
                    TUpReserveRelationInfo.lotteryType == 1,
                    TUpReserveRelationInfo.reserve_round_id == round_id)
            ).order_by(TUpReserveRelationInfo.dynamicId.desc())
            result = await session.execute(sql)
            return result.scalars().all()

    @staticmethod
    def SqlAlchemyObjList2DictList(obj_list: list, base_model, exclude_attrs: list[str] = None):
        if exclude_attrs is None:
            exclude_attrs = []
        column_attrs = [attr for attr in dir(base_model) if
                        isinstance(getattr(base_model, attr), InstrumentedAttribute)]
        for i in exclude_attrs:
            if i in column_attrs:
                column_attrs.remove(i)
        ret_list = []
        for obj in obj_list:
            _ = {}
            for k in column_attrs:
                _.update({k: getattr(obj, k)})
            ret_list.append(_)
        return ret_list

    @lock_wrapper
    async def get_all_available_reserve_lotterys(self) -> list[TUpReserveRelationInfo]:
        """
        获取所有有效的预约抽奖 （按照etime升序排列
        只抽两天之内的
        :return:
        """
        async with self._session() as session:
            sql = select(TUpReserveRelationInfo).filter(
                and_(
                    TUpReserveRelationInfo.lotteryType == 1,
                    TUpReserveRelationInfo.etime >= int(time.time()),
                    TUpReserveRelationInfo.state != -100,  # 失效的预约抽奖
                    TUpReserveRelationInfo.state != -300,  # 失效的预约抽奖
                    TUpReserveRelationInfo.state != -110,  # 开了的预约抽奖
                    TUpReserveRelationInfo.state != 150,  # 开了的预约抽奖
                )
            ).order_by(TUpReserveRelationInfo.etime.asc())
            result = await session.execute(sql)
            return result.scalars().all()

    @lock_wrapper
    async def get_all_available_reserve_lotterys_by_time(self, limit_time: int, page_number: int = 0, page_size: int = 0) -> \
            tuple[list[TUpReserveRelationInfo], int]:
        """
        获取所有有效的预约抽奖 （按照etime升序排列
        :return:
        """
        if not limit_time:
            and_clause = and_(
                TUpReserveRelationInfo.lotteryType == 1,
                TUpReserveRelationInfo.etime >= int(time.time()),
                TUpReserveRelationInfo.state != -100,  # 失效的预约抽奖
                TUpReserveRelationInfo.state != -300,  # 失效的预约抽奖
                TUpReserveRelationInfo.state != -110,  # 开了的预约抽奖
                TUpReserveRelationInfo.state != 150,  # 开了的预约抽奖
            )
        else:
            and_clause = and_(
                TUpReserveRelationInfo.lotteryType == 1,
                TUpReserveRelationInfo.etime >= int(time.time()),
                TUpReserveRelationInfo.state != -100,  # 失效的预约抽奖
                TUpReserveRelationInfo.state != -300,  # 失效的预约抽奖
                TUpReserveRelationInfo.state != -110,  # 开了的预约抽奖
                TUpReserveRelationInfo.state != 150,  # 开了的预约抽奖
                TUpReserveRelationInfo.etime <= int(time.time()) + limit_time
            )
        sql = select(TUpReserveRelationInfo).filter(
            and_clause
        ).order_by(TUpReserveRelationInfo.etime.asc())
        if page_number and page_size:
            offset_value = (page_number - 1) * page_size
            sql = sql.offset(offset_value).limit(page_size)
        count_sql = select(func.count(TUpReserveRelationInfo.ids)).filter(and_clause)
        async with self._session() as session:
            result = await session.execute(sql)
            count_result = await session.execute(count_sql)
            print(sql.compile(compile_kwargs={'literal_binds': True}))
        return result.scalars().all(), count_result.scalars().first()

    @lock_wrapper
    async def get_available_reserve_lottery_total_num(self) -> int:
        """
        获取所有有效的预约抽奖总数
        :return:
        """
        and_clause = and_(
            TUpReserveRelationInfo.lotteryType == 1,
            TUpReserveRelationInfo.etime >= int(time.time()),
            TUpReserveRelationInfo.state != -100,  # 失效的预约抽奖
            TUpReserveRelationInfo.state != -300,  # 失效的预约抽奖
            TUpReserveRelationInfo.state != -110,  # 开了的预约抽奖
            TUpReserveRelationInfo.state != 150,  # 开了的预约抽奖
        )
        sql = select(func.count(TUpReserveRelationInfo.ids)).filter(and_clause)
        async with self._session() as session:
            result = await session.execute(sql)
            return result.scalars().first()


# region 测试用代码

async def _test_solve_reserve_resp():
    b = SqlHelper()
    print(await b.get_all_available_reserve_lotterys_by_time(0))


# endregion


if __name__ == '__main__':
    asyncio.run(_test_solve_reserve_resp())
    # test()
    # test_solve_reserve_resp()
