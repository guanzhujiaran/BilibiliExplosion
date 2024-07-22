import time

import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, InstrumentedAttribute
from typing import Callable, Union
from sqlalchemy import create_engine, inspect, select, and_
import CONFIG
from opus新版官方抽奖.预约抽奖.db.models import TReserveRoundInfo, TUpReserveRelationInfo

lock = asyncio.Lock()
log = logger.bind(user='reserve_lottery')


def lock_wrapper(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.exception(e)
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
        self.reserve_info_column_names = []

    async def init(self):
        def get_column_name(conn: str) -> list[str]:
            inspector = inspect(conn)
            return inspector.get_columns(TUpReserveRelationInfo.__tablename__)

        async with self._session().bind.connect() as connection:
            self.reserve_info_column_names = await connection.run_sync(get_column_name)

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
        resp_dict = SqlHelper.solve_reserve_resp(origin_resp_dict)
        new_field = list(set(self.reserve_info_column_names) - set(list(resp_dict.keys())))
        for k in new_field:
            resp_dict.pop(k)
        reserve_info = TUpReserveRelationInfo(**resp_dict)
        reserve_info.raw_JSON = origin_resp_dict
        reserve_info.reserve_round_id = round_id
        if new_field:
            reserve_info.new_field = str(new_field)
        async with self._session() as session:
            async with session.begin():
                await session.merge(reserve_info)

    @lock_wrapper
    async def get_latest_reserve_round(self,readonly=False) -> TReserveRoundInfo:
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
    async def get_all_available_reserve_lotterys_by_time(self,limit_time:int) -> list[TUpReserveRelationInfo]:
        """
        获取所有有效的预约抽奖 （按照etime升序排列
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
                    TUpReserveRelationInfo.etime<= int(time.time())+limit_time
                )
            ).order_by(TUpReserveRelationInfo.etime.asc())
            result = await session.execute(sql)
            return result.scalars().all()

# region 测试用代码
async def test():
    a = SqlHelper()

    print(await a.get_latest_reserve_round())


def test_solve_reserve_resp():
    a = {'code': 0, 'message': '0', 'ttl': 1, 'data': {'list': {
        '1538260': {'sid': 1538260, 'name': '一键订阅DPC夏季赛赛程', 'total': 17359, 'stime': 1684130400,
                    'etime': 1687752000, 'isFollow': 0, 'state': 100, 'oid': '', 'type': 3, 'upmid': 17561885,
                    'reserveRecordCtime': 0, 'livePlanStartTime': 1687752000, 'upActVisible': 0, 'lotteryType': 1,
                    'prizeInfo': {'text': '预约有奖：DOTA2炸弹人手办*1份、DOTA2可旋转键帽*1份、DOTA2赛事周边*8份',
                                  'jumpUrl': 'https://www.bilibili.com/h5/lottery/result?business_id=1538260&business_type=10'},
                    'dynamicId': '', 'reserveTotalShowLimit': 0, 'desc': '观赛赢刀塔手办',
                    'start_show_time': 1684130400, 'hide': {}, 'ext': '{}'}}}, 'ids': 1538260}

    print(SqlHelper.solve_reserve_resp(a))


async def test_get_reserve_info_by_ids():
    a = SqlHelper()

    rest = await a.get_reserve_by_ids(1323931)
    print(rest.raw_JSON)


async def test_get_all_available_reserve_lotterys():
    a = SqlHelper()

    rest = await a.get_all_available_reserve_lotterys()
    for i in rest:
        print(i.__dict__)


# endregion


if __name__ == '__main__':
    asyncio.run(test_get_all_available_reserve_lotterys())
    # test()
    # test_solve_reserve_resp()
