import asyncio
import time
from datetime import datetime
from typing import Type, Union

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Bilibili_methods.all_methods import methods
from CONFIG import CONFIG
from grpc获取动态.Utils.GrpcUtils import DynTool, ObjDynInfo
from utl.代理.grpc_api import BiliGrpc
from grpc获取动态.src.获取取关对象.db.models import UserInfo, SpaceDyn

grpcapi = BiliGrpc()


class GetRmFollowingListV1:
    def __init__(self, ):
        self.max_recorded_dyn_num = 100  # 每个uid最多记录多少个动态
        SQLITE_URI = 'sqlite:///G:/database/Following_Usr.db?check_same_thread=False'
        engine = create_engine(
            SQLITE_URI,
            echo=False  # 是否打印sql日志
        )
        self.Session = sessionmaker(engine, expire_on_commit=False, autoflush=True)  # 每次操作的时候将session实例化一下
        self.check_up_sep_days = 7  # 最多隔7天检查一遍是否发了新动态
        self.BAPI = methods()
        self.max_separat_time = 86400 * 30  # 标记多少天未发动态的up主
        self.now_check_up: list = []

    # region 空间动态crud
    async def create_space_dyn(self, dyn_obj: ObjDynInfo):
        """
        添加空间动态
        :param dyn_obj:
        :return:
        """
        is_lot_dyn = self.BAPI.choujiangxinxipanduan(dyn_obj.dynCard.dynamicContent)
        with self.Session() as session:
            space_dyn = SpaceDyn(
                Space_Dyn_uid=dyn_obj.uid,
                dynamic_id=dyn_obj.dynamicId,
                dynamic_content=dyn_obj.dynCard.dynamicContent,
                uname=dyn_obj.uname,
                dynamic_type=dyn_obj.dynCard.dynType,
                is_lot_dyn=1 if is_lot_dyn is None else 0,
                pubts=dyn_obj.dynCard.pubTs
            )
            session.add(space_dyn)
            session.commit()

    # endregion
    # region up主信息crud
    async def create_user_info(self, uid):
        """
        添加新的uid
        :param uid:
        :return:
        """
        with self.Session() as session:
            session.add(UserInfo(
                uid=uid,
                upTimeStamp=datetime.fromtimestamp(0)
            ))
            session.commit()

    # endregion

    async def is_exist_space_dyn(self, dynamic_id: str) -> bool:
        """
        如果空间动态存在动态id就返回True
        :param dynamic_id:
        :return:
        """
        with self.Session() as session:
            resp = session.query(SpaceDyn).filter(dynamic_id == SpaceDyn.dynamic_id).first()
            if resp:
                return True
            else:
                return False

    async def check_up_space_dyn(self, uid: int):
        """
        更新数据库中的up主空间动态和up信息
        :param uid:
        :return:
        """
        try:
            uid = int(uid)
        except:
            return
        checking_mark = False
        while 1:
            if uid in self.now_check_up:
                await asyncio.sleep(1)
                checking_mark = True
            else:
                self.now_check_up.append(uid)
                break
        if checking_mark:
            return
        history_offset = ""
        while 1:
            dynamic_flag = False
            resp = grpcapi.grpc_get_space_dyn_by_uid(uid, history_offset)
            space_dyn = DynTool.solve_space_dyn(resp)
            logger.info(space_dyn.__dict__)
            history_offset = space_dyn.historyOffset
            hasMore = space_dyn.hasMore
            latest_dynamic_timestamp = int(time.time())

            for dyn_obj in space_dyn.DynList:
                if dyn_obj.dynCard.pubTs <= latest_dynamic_timestamp:
                    latest_dynamic_timestamp = dyn_obj.dynCard.pubTs
                if await self.is_exist_space_dyn(dyn_obj.dynamicId):
                    dynamic_flag = True
                    break
                else:
                    await self.create_space_dyn(dyn_obj)
            if not hasMore:
                break
            if dynamic_flag:
                break
            if int(time.time()) - latest_dynamic_timestamp >= self.max_separat_time:  # 超过时间的直接跳过
                break
        self.now_check_up.remove(uid)

    async def update_up_status(self, uid):
        """
        根据数据库中内容更新up状态 ### 核心函数！
        :param uid:
        :return:
        """

        def is_lot_up(spdyn: Type[SpaceDyn]):
            """
            判断每个动态是否符合抽奖up的条件
            :param spdyn:
            :return:
            """
            if int(time.time()) - spdyn.pubts >= self.max_separat_time:
                return False

            return bool(spdyn.is_lot_dyn)

        with self.Session() as session:
            space_dyn_group_by_uid = session.query(SpaceDyn).filter(uid == SpaceDyn.Space_Dyn_uid).order_by(
                SpaceDyn.pubts.desc()).all()  # 最新的在最前面
            isLotUp = 1 if len(list(filter(is_lot_up, space_dyn_group_by_uid))) > 0 else 0
            if len(space_dyn_group_by_uid) > self.max_recorded_dyn_num:
                delete_list = space_dyn_group_by_uid[-(len(space_dyn_group_by_uid) - self.max_recorded_dyn_num):]
                for delete_dyn in delete_list:
                    session.query(SpaceDyn).filter(SpaceDyn.dynamic_id == delete_dyn.dynamic_id).delete()
            session.query(UserInfo).filter(UserInfo.uid == uid).update({
                "isLotUp": isLotUp,
                'upTimeStamp': datetime.fromtimestamp(int(time.time()))
            })  # 更新状态！
            session.commit()

    async def check_db_exist_up(self, uid: Union[int,str]) -> bool:
        """
        检查数据库中是否存在up，并返回数据库中的up是否为抽奖up
        :param uid:
        :return:
        """
        if isinstance(uid,str):
            if not str.isdigit(uid):
                logger.error(f"Invalid uid! uid:{uid}")
                return False
        logger.debug(f"Checking uid: {uid}!")
        with self.Session() as session:
            res = session.query(UserInfo).filter(uid == UserInfo.uid).first()
            if res:
                if (datetime.now()-res.upTimeStamp).days < self.check_up_sep_days:
                    return bool(res.isLotUp)
            else:
                await self.create_user_info(uid)

        # 更新up的空间动态数据库
        await self.check_up_space_dyn(uid)
        # 更新up抽奖状态，并将数据库中的每个up主的动态数量控制在100个以内，减少占用的存储空间
        await self.update_up_status(uid)
        return await self.check_db_exist_up(uid)

    async def check_lot_up(self, following_list: list) -> list:
        promise_list = []
        ret_list = []
        for uid in following_list:
            promise_list.append(self.check_db_exist_up(uid))
        for idx in range(len(promise_list)):
            if not await promise_list[idx]:
                ret_list.append(following_list[idx])
        return ret_list

    async def main(self, following_list: list) -> list:
        if type(following_list) is not list:
            return []
        return await self.check_lot_up(following_list)
