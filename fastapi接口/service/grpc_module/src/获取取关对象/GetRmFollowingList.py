import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import Union, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from Bilibili_methods.all_methods import methods
from CONFIG import CONFIG
from fastapi接口.log.base_log import get_rm_following_list_logger
from fastapi接口.service.grpc_module.Utils.GrpcDynamicRespUtils import DynTool, ObjDynInfo
from fastapi接口.service.grpc_module.src.获取取关对象.db.models import UserInfo, SpaceDyn
from fastapi接口.service.grpc_module.grpc.grpc_api import bili_grpc
current_dir = os.path.dirname(__file__)
def get_file_path(relative_path:str):
    return os.path.join(current_dir, relative_path)
class GetRmFollowingListV1:
    def __init__(self, ):
        self.space_sem = asyncio.Semaphore(100)
        self.sql_lock = asyncio.Lock()
        self.logger = get_rm_following_list_logger
        self.lucky_up_list = []
        self.max_recorded_dyn_num = 300  # 每个uid最多记录多少个动态
        SQLITE_URI = CONFIG.database.followingup_db_RUI
        engine = create_async_engine(
            SQLITE_URI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self.AsyncSession = async_sessionmaker(
            engine,
            expire_on_commit=False,
            autoflush=True
        )  # 每次操作的时候将session实例化一下
        self.check_up_sep_days = 7  # 最多隔7天检查一遍是否发了新动态
        self.BAPI = methods()
        self.max_separat_time = 86400 * 60  # 标记多少天未发动态的up主
        self.now_check_up: list = []

    # region 空间动态crud
    async def create_space_dyn(self, dyn_obj: ObjDynInfo) -> int:
        """
        添加空间动态
        :param dyn_obj:
        :return: 返回是否是抽奖动态
        """
        is_lot_dyn = self.BAPI.choujiangxinxipanduan(dyn_obj.dynCard.dynamicContent)
        while 1:
            try:
                async with self.sql_lock:
                    async with self.AsyncSession() as session:
                        async with session.begin():
                            space_dyn = SpaceDyn(
                                Space_Dyn_uid=dyn_obj.uid,
                                dynamic_id=dyn_obj.dynamicId,
                                dynamic_content=dyn_obj.dynCard.dynamicContent,
                                uname=dyn_obj.uname,
                                dynamic_type=dyn_obj.dynCard.dynType,
                                is_lot_dyn=1 if is_lot_dyn is None else 0,
                                pubts=dyn_obj.dynCard.pubTs,
                                like=dyn_obj.dynCard.dynStat.like,
                                reply=dyn_obj.dynCard.dynStat.reply,
                                repost=dyn_obj.dynCard.dynStat.repost,
                            )
                            session.add(space_dyn)
                            await session.flush()
                            session.expunge(space_dyn)
                            break
            except Exception as e:
                self.logger.info(f'Exception while creating space dyn!\n{e}')
                await asyncio.sleep(random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        return 1 if is_lot_dyn is None else 0

    # endregion
    # region up主信息crud
    async def create_user_info(self, uid):
        """
        添加新的uid
        :param uid:
        :return:
        """
        while 1:
            try:
                async with self.sql_lock:
                    async with self.AsyncSession() as session:
                        async with session.begin():
                            data = UserInfo(
                                uid=uid,
                                upTimeStamp=datetime.fromtimestamp(86400)
                            )
                            merged_data = await session.merge(data)
                            await session.flush()
                            session.expunge(merged_data)
                            break
            except Exception as e:
                self.logger.critical(f'Exception while create user info!{uid}\n{e}')

    # endregion

    async def is_exist_space_dyn(self, dynamic_id: str) -> bool:
        """
        如果空间动态存在动态id就返回True
        :param dynamic_id:
        :return:
        """
        while 1:
            try:
                async with self.sql_lock:
                    async with self.AsyncSession() as session:
                        sql = select(SpaceDyn).where(dynamic_id == SpaceDyn.dynamic_id)
                        result = await session.execute(sql)
                        data = result.scalars().first()
                        if data:
                            return True
                        else:
                            return False
            except Exception as e:
                self.logger.exception(f'Exception while check is exist spece dyn! {dynamic_id}\n{e}')
                await asyncio.sleep(30)

    async def check_up_space_dyn(self, uid: int):
        """
        更新数据库中的up主空间动态和up信息 （爬取数据并处理部分！
        :param uid:
        :return:
        """
        async with self.space_sem:
            try:
                uid = int(uid)
            except:
                self.logger.error("Invalid uid: {}".format(uid))
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
                if uid in self.now_check_up:
                    self.now_check_up.remove(uid)
                return
            history_offset = ""
            dyn_obj = None
            is_lot_up = False
            dynamic_flag = False
            is_lot_dyn = 0
            self.logger.info(f"检查up主 {uid} 空间中")
            while 1:
                try:
                    resp = await bili_grpc.grpc_get_space_dyn_by_uid(uid, history_offset)
                    resp_len = len(resp.get('list', []))
                    self.logger.info(f'获取到{uid}空间响应{resp_len}条！')
                    space_dyn = DynTool.solve_space_dyn(resp)
                    history_offset = space_dyn.historyOffset
                    hasMore = space_dyn.hasMore
                    latest_dynamic_timestamp = int(time.time())
                    if space_dyn.DynList:
                        for dyn_obj in space_dyn.DynList:
                            if not dyn_obj:
                                continue
                            if dyn_obj.dynCard.pubTs <= latest_dynamic_timestamp:
                                latest_dynamic_timestamp = dyn_obj.dynCard.pubTs
                            if await self.is_exist_space_dyn(dyn_obj.dynamicId):
                                dynamic_flag = True
                                break
                            else:
                                is_lot_dyn = await self.create_space_dyn(dyn_obj)
                                if is_lot_dyn:
                                    is_lot_up = True
                    # 终止规则
                    """
                    1.空间没有更多的动态
                    2.遇到获取过的动态
                    3.遇到超时的动态
                    4.遇到抽奖的动态
                    """
                    if is_lot_dyn:
                        break
                    if not hasMore:
                        break
                    if dynamic_flag:
                        break
                    if int(time.time()) - latest_dynamic_timestamp >= self.max_separat_time:  # 超过时间的直接跳过
                        break
                except Exception as e:
                    self.logger.exception(f"获取取关uid:{uid} {history_offset}失败！\n{e}")
                    await asyncio.sleep(10)
            if dyn_obj:
                self.logger.info(
                    f"uid:{uid} {dyn_obj.uname if dyn_obj else ''} 空间有动态")
                await self.update_up_status(uid, dyn_obj.uname, dyn_obj.dynCard.officialVerify)
            else:
                self.logger.critical(
                    f"uid:{uid} {dyn_obj.uname if dyn_obj else ''} 空间没有动态")
                while 1:
                    try:
                        async with self.sql_lock:
                            async with self.AsyncSession() as session:
                                sql = select(UserInfo).where(uid == UserInfo.uid)
                                result = await session.execute(sql)
                                userinfo = result.scalars().first()
                                break
                    except Exception as e:
                        self.logger.exception(f'Exception while query userinfo by uid!{uid}\n{e}')
                await self.update_up_status(uid, userinfo.uname, userinfo.officialVerify)
            self.logger.info(
                f"uid:{uid} {dyn_obj.uname if dyn_obj else ''} 空间动态检查完成！{'是抽奖up' if bool(is_lot_up) else '非抽奖up'}")
            if uid in self.now_check_up:
                self.now_check_up.remove(uid)

    async def update_up_status(self, uid: int, uname: str, officialVerify: int = -2, update_ts: int = int(time.time())):
        """
        根据数据库中内容更新up状态，只有当遇到终止条件时才能将更新时间设置为当前时间
         ### 核心函数！
        :param officialVerify:
        :param uname:
        :param update_ts: 更新时间
        :param uid:
        :return:
        """

        def is_lot_up(spdyn: SpaceDyn):
            """
            判断每个动态是否符合抽奖up的条件
            :param spdyn:
            :return:
            """
            if int(time.time()) - spdyn.pubts >= self.max_separat_time:  # 超过最大时间，不判断动态是否是抽奖动态，直接标记为非抽奖动态
                return False

            return bool(spdyn.is_lot_dyn)

        while 1:
            try:
                async with self.sql_lock:
                    async with self.AsyncSession() as session:
                        async with session.begin():
                            sql = select(SpaceDyn).where(uid == SpaceDyn.Space_Dyn_uid).order_by(SpaceDyn.pubts.desc())
                            result = await session.execute(sql)
                            space_dyn_group_by_uid = result.scalars().all()  # 最新的在最前面
                            isLotUp = 1 if len(list(filter(is_lot_up, space_dyn_group_by_uid))) > 0 else 0
                            if len(space_dyn_group_by_uid) > self.max_recorded_dyn_num:
                                delete_list: Sequence[SpaceDyn] = space_dyn_group_by_uid[
                                                                  -(
                                                                          len(space_dyn_group_by_uid) - self.max_recorded_dyn_num):]
                                for delete_dyn in delete_list:
                                    await session.delete(delete_dyn)
                            sql = update(UserInfo).where(uid == UserInfo.uid).values(
                                isLotUp=isLotUp,
                                upTimeStamp=datetime.fromtimestamp(update_ts),
                                officialVerify=officialVerify,
                                uname=uname,
                            )
                            await session.execute(sql)  # 更新状态！
                            break
            except Exception as e:
                self.logger.exception(f'Exception while check is lot up!{uid}\n{e}')

    async def check_db_exist_up(self, uid: Union[int, str]) -> bool:
        """
        检查数据库中是否存在up，并返回数据库中的up是否为抽奖up
        :param uid:
        :return: True 代表是抽奖up
        """
        while 1:
            try:
                if isinstance(uid, str):
                    if not str.isdigit(uid):
                        self.logger.error(f"Invalid uid! uid:{uid}")
                        return False
                    else:
                        uid = int(uid)
                # self.logger.info(f"Checking uid: {uid}! https://space.bilibili.com/{uid}/dynamic")
                if uid in self.lucky_up_list:
                    return True
                async with self.AsyncSession() as session:
                    sql = select(UserInfo).where(uid == UserInfo.uid)
                    async with self.sql_lock:
                        session_res = await session.execute(sql)
                    res = session_res.scalars().first()
                if res:
                    if (datetime.now() - res.upTimeStamp).days < self.check_up_sep_days:
                        return bool(res.isLotUp)
                    else:
                        self.logger.info(
                            f'uid:{uid}数据库中数据太老\t数据库中最后时间{res.upTimeStamp.strftime("%Y-%m-%d %H:%M:%S")}')
                else:
                    self.logger.info(f'uid:{uid}数据库中不存在')
                    await self.create_user_info(uid)
                # 更新up的空间动态数据库
                await self.check_up_space_dyn(uid)
                return await self.check_db_exist_up(uid)
            except Exception as e:
                self.logger.exception(f'uid:{uid} 获取取关用户空间失败！\n{e}')
                await asyncio.sleep(10)

    async def check_lot_up(self, following_list: list) -> list:
        self.logger.critical(f'检查关注列表:{following_list}')
        tasks = [asyncio.create_task(self.check_db_exist_up(uid)) for uid in following_list]
        while 1:
            if running_task_num := len([x for x in tasks if x.done()]) == 0:
                break
            else:
                self.logger.info(
                    f'当前正在检查关注列表：{len(following_list) - running_task_num}/{len(following_list)}个！')
                await asyncio.sleep(10)
        results = await asyncio.gather(*tasks)
        ret_list = [following_list[idx] for idx, result in enumerate(results) if not result]
        return ret_list

    def get_lucky_up_list(self) -> []:

        if os.path.exists(get_file_path('中奖up.json')):
            with open(get_file_path('中奖up.json'), 'r', encoding='utf-8') as f:
                return json.loads(f.read()).get('up_ids')
        else:
            with open(get_file_path('中奖up.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps({'up_ids': []}, indent=4))
            return []

    async def main(self, following_list: list) -> list:
        if type(following_list) is not list:
            return []
        self.lucky_up_list = self.get_lucky_up_list()
        resp_list = await self.check_lot_up(following_list)
        return resp_list

get_rm_following_list = GetRmFollowingListV1()


