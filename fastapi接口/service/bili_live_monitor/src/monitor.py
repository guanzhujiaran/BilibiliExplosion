# -*- coding:utf-8 -*-
"""
live_url 在redis数据库中可添加直播间地址，开始金宝箱抽奖后会前往直播间发送wss
"""
import ast
import asyncio
import json
import os
import threading
import time
from collections.abc import Callable
from copy import deepcopy
from enum import Enum
from functools import wraps
from typing import Type, Union
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import CONFIG
from fastapi接口.log.base_log import live_monitor_logger
from fastapi接口.service.bili_live_monitor.utils import tool

from fastapi接口.service.bili_live_monitor.utils.models import *
from fastapi接口.service.bili_live_monitor.utils.tool import AsyncTool
from utl.pushme.pushme import pushme, pushme_try_catch_decorator, async_pushme_try_catch_decorator
from utl.redisTool.RedisManager import SyncRedisManagerBase, RedisManagerBase

sqlhelper_lock = threading.Lock()
async_sqlhelper_lock = asyncio.Lock()


class BiliLiveLotRedisManager(SyncRedisManagerBase):
    class RedisMap(str, Enum):
        goldbox = 'goldbox'
        all_live_lot = 'all_live_lot'

    def __init__(self):
        super().__init__(host='localhost', port=11451, db=0)

    def get_goldbox_info(self):
        return self._get(BiliLiveLotRedisManager.RedisMap.goldbox.value)

    def setex_goldbox_info(self, ttl: int, da: str):
        return self._setex(BiliLiveLotRedisManager.RedisMap.goldbox.value, da, ttl)

    def setex_unignore_lot_info(self, server_data_id, ttl: int, data: str):
        self._setex(server_data_id, data, ttl)

    def set_all_lot_info(self, data: str):
        self._set(self.RedisMap.all_live_lot.value, data)


class AsyncBiliLiveLotRedisManager(RedisManagerBase):
    class RedisMap(str, Enum):
        goldbox = 'goldbox'
        all_live_lot = 'all_live_lot'

    def __init__(self):
        super().__init__(host='localhost', port=11451, db=0)

    async def get_goldbox_info(self):
        return await self._get(BiliLiveLotRedisManager.RedisMap.goldbox.value)

    async def setex_goldbox_info(self, ttl: int, da: str):
        return await self._setex(BiliLiveLotRedisManager.RedisMap.goldbox.value, da, ttl)

    async def setex_unignore_lot_info(self, server_data_id, ttl: int, data: str):
        await self._setex(server_data_id, data, ttl)

    async def set_all_lot_info(self, data: str):
        return await self._set(self.RedisMap.all_live_lot.value, data)


class GOLDBOX:
    septime = 60 * 60  # 一个小时获取一次

    def __init__(self, redis_manager: BiliLiveLotRedisManager | AsyncBiliLiveLotRedisManager):
        self.redis_manager: BiliLiveLotRedisManager = redis_manager
        self.async_redis_manager: AsyncBiliLiveLotRedisManager = redis_manager

    def check_goldbox(self):
        while 1:
            try:
                server_response: list[dict] = tool.Tool.get_goldbox_data()
                # try:
                self.solve_goldbox_data_from_server(server_response)
            except Exception as e:
                live_monitor_logger.exception(f'check_goldbox失败 {e}')
            time.sleep(self.septime)

    async def async_check_goldbox(self):
        while 1:
            try:
                server_response: list[dict] = await AsyncTool.get_goldbox_data()
                # try:
                await self.async_solve_goldbox_data_from_server(server_response)
            except Exception as e:
                live_monitor_logger.exception(f'check_goldbox失败 {e}')
            await asyncio.sleep(self.septime)

    def solve_goldbox_data_from_server(self, server_response):
        if len(server_response):
            redis_da = self.redis_manager.get_goldbox_info()
            if redis_da:
                json_data = json.loads(redis_da)
                for i in json_data.get('goldbox'):
                    aid = i.get('aid')
                    live_url = i.get('live_url', "")
                    if aid:
                        for box in server_response:
                            if box.get('aid') == aid:
                                box.update({'live_url': live_url})
            else:
                for box in server_response:
                    box.update({'live_url': ""})
            max_join_end_time = int(time.time())
            for i in server_response:
                if i.get('join_end_time') >= max_join_end_time:
                    max_join_end_time = i.get('join_end_time')
            live_monitor_logger.info(f'检测到金宝箱抽奖！{server_response}')
            self.redis_manager.setex_goldbox_info(
                max_join_end_time - int(time.time()) if max_join_end_time - int(time.time()) >= 1 else 1,
                json.dumps({'goldbox': server_response}))

    async def async_solve_goldbox_data_from_server(self, server_response):
        if len(server_response):
            redis_da = await self.async_redis_manager.get_goldbox_info()
            if redis_da:
                json_data = json.loads(redis_da)
                for i in json_data.get('goldbox'):
                    aid = i.get('aid')
                    live_url = i.get('live_url', "")
                    if aid:
                        for box in server_response:
                            if box.get('aid') == aid:
                                box.update({'live_url': live_url})
            else:
                for box in server_response:
                    box.update({'live_url': ""})
            max_join_end_time = int(time.time())
            for i in server_response:
                if i.get('join_end_time') >= max_join_end_time:
                    max_join_end_time = i.get('join_end_time')
            live_monitor_logger.info(f'检测到金宝箱抽奖！{server_response}')
            await self.async_redis_manager.setex_goldbox_info(
                max_join_end_time - int(time.time()) if max_join_end_time - int(time.time()) >= 1 else 1,
                json.dumps({'goldbox': server_response}))


def _async_sql_helper_wrapper(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        while 1:
            try:
                async with async_sqlhelper_lock:
                    return await func(*args, **kwargs)
            except Exception as e:
                live_monitor_logger.exception(e)
                await asyncio.sleep(1)

    return wrapper


def _sql_helper_wrapper(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        while 1:
            try:
                with sqlhelper_lock:
                    return func(*args, **kwargs)
            except Exception as e:
                live_monitor_logger.exception(e)
                time.sleep(1)

    return wrapper


class SqlHelper:
    SQLITE_URI = CONFIG.database.bili_live_monitor_db_URI
    engine = create_engine(
        SQLITE_URI,
        echo=False  # 是否打印sql日志
    )
    Session = sessionmaker(engine, expire_on_commit=False)  # 每次操作的时候将session实例化一下

    @_sql_helper_wrapper
    def get_anchor_by_server_data_id(self, server_data_id: int) -> Optional[Anchor]:
        with self.Session() as session:
            db_anchor = session.query(Anchor).filter(text("server_data_id=:id")).params(id=server_data_id).first()
        return db_anchor

    @_sql_helper_wrapper
    def add_anchor(self, anchor: Anchor):
        with self.Session() as session:
            session.add(anchor)
            session.commit()

    @_sql_helper_wrapper
    def get_popularity_red_package_by_lot_id(self, lot_id: int) -> Optional[PopularityRedPocket]:
        with self.Session() as session:
            red_pocket = session.query(PopularityRedPocket).filter(text("lot_id=:id")).params(
                id=lot_id).first()
        return red_pocket

    @_sql_helper_wrapper
    def add_popularity_red_package(self, pop: PopularityRedPocket):
        with self.Session() as session:
            session.add(pop)
            session.commit()

    @_sql_helper_wrapper
    def get_room_uid_by_room_id(self, room_id: int) -> Optional[TRoomUid]:
        with self.Session() as session:
            res = session.query(TRoomUid).filter(TRoomUid.room_id == room_id).first()
        return res

    @_sql_helper_wrapper
    def add_room_uid(self, room_id_2_uid: TRoomUid):
        with self.Session() as session:
            session.add(room_id_2_uid)  # 添加上去
            session.commit()

    @_sql_helper_wrapper
    def get_server_data_by_id(self, _id: int) -> Optional[ServerData]:
        with self.Session() as session:
            db_data = session.query(ServerData).filter(text("id=:id")).params(id=_id).first()
        return db_data

    @_sql_helper_wrapper
    def add_server_data(self, server_data: ServerData):
        with self.Session() as session:
            session.add(server_data)
            session.commit()


class AsyncSqlHelper:
    def __init__(self):
        sqlite_uri = CONFIG.database.aiobili_live_monitor_db_URI
        engine = create_async_engine(
            sqlite_uri,
            echo=False,  # 是否打印sql日志
            future=True
        )
        self.Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False,
                                          autoflush=True)  # 每次操作的时候将session实例化一下

    @_async_sql_helper_wrapper
    async def get_anchor_by_server_data_id(self, server_data_id: int) -> Optional[Anchor]:
        async with self.Session() as session:
            db_anchor = await session.execute(
                select(Anchor).filter(text("server_data_id=:id")).params(id=server_data_id))
            return db_anchor.scalars().first()

    @_async_sql_helper_wrapper
    async def add_redpacket_winner(self, popularity_red_pocket_winner: PopularityRedPocketWinner):
        async with self.Session() as session:
            session.add(popularity_red_pocket_winner)
            await session.commit()

    @_async_sql_helper_wrapper
    async def add_anchor(self, anchor: Anchor):
        async with self.Session() as session:
            session.add(anchor)
            await session.commit()

    @_async_sql_helper_wrapper
    async def get_popularity_red_package_by_lot_id(self, lot_id: int) -> Optional[PopularityRedPocket]:
        async with self.Session() as session:
            red_pocket = await session.execute(select(PopularityRedPocket).filter(text("lot_id=:id")).params(
                id=lot_id))
            return red_pocket.scalars().first()

    @_async_sql_helper_wrapper
    async def add_popularity_red_package(self, pop: PopularityRedPocket):
        async with self.Session() as session:
            session.add(pop)
            await session.commit()

    @_async_sql_helper_wrapper
    async def get_room_uid_by_room_id(self, room_id: int) -> Optional[TRoomUid]:
        async with self.Session() as session:
            res = await session.execute(select(TRoomUid).filter(TRoomUid.room_id == room_id))
            return res.scalars().first()

    @_async_sql_helper_wrapper
    async def add_room_uid(self, room_id_2_uid: TRoomUid):
        async with self.Session() as session:
            session.add(room_id_2_uid)  # 添加上去
            await session.commit()

    @_async_sql_helper_wrapper
    async def get_server_data_by_id(self, _id: int) -> Optional[ServerData]:
        async with self.Session() as session:
            db_data = await session.execute(select(ServerData).filter(text("id=:id")).params(id=_id))
            return db_data.scalars().first()

    @_async_sql_helper_wrapper
    async def add_server_data(self, server_data: ServerData):
        async with self.Session() as session:
            session.add(server_data)
            await session.commit()


class BaseMonitor:
    def __init__(self):
        self.gift_list = ["辣条", "小心心", "亿圆", "B坷垃", "i了i了", "情书", "打call", "牛哇", "干杯", "这个好诶",
                          "星愿水晶球", "告白花束", "花式夸夸", "撒花", "守护之翼", "牛哇牛哇", "小花花"]
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.dir, 'config.json')
        self.unignore_keywords = [
            "手办",
            "ps",
            "旗舰手机",
            "铁三角",
            "海盗船",
            # "情书",
            # "告白花束",
            # "花式夸夸",
            "撒花",
            "星愿水晶球",
            "守护之翼",
            '轻薄本',
            '华硕',
            "手机"
        ]
        self.ignore_keywords = [
            "进群"
        ]
        self.ignore_room_id_list: list[int] = [
            31697327
        ]
        self.big_redpocket = 79  # 100元以上的红包推送
        self.recorded_unignore_lot = []  # 记录过的不可忽略大奖记录
        self.check_data_from_server_time = 30  # 每次从服务器获取数据间隔时间
        self.push_time = 5  # 推送到redis的间隔
        self.push_me_sw = False  # 推送到pushme的开关
        self.push_me_time = 60  # 推送到pushme的间隔
        self.latest_push_me_time = 0  # 最后推送pushme的timestamp
        self.recorded_server_data_id_list = []
        self.anchor_list: list[Type[Anchor] | Anchor] = []
        self.recorded_anchor_server_data_id_list: [int] = []  # 记录的天选id
        self.popularity_red_pocket_list: list[Type[PopularityRedPocket] | PopularityRedPocket] = []
        self.recorded_red_pocket_id_list: list[int] = []


class Monitor(BaseMonitor):

    def __init__(self):
        super().__init__()
        self.sq = SqlHelper()
        self.redis_manager = BiliLiveLotRedisManager()
        self.GOLDBOX = GOLDBOX(self.redis_manager)
        threading.Timer(10, self.show_lot).start()
        threading.Timer(self.push_time, self.push_lot_data).start()
        threading.Thread(target=self.GOLDBOX.check_goldbox).start()
        self.fresh_config()

    def fresh_config(self):
        try:

            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = json.loads(f.read())
                self.unignore_keywords = cfg.get('unignore_keywords') if cfg.get(
                    'unignore_keywords') else self.unignore_keywords
                self.ignore_keywords = cfg.get('ignore_keywords') if cfg.get(
                    'ignore_keywords') else self.unignore_keywords
                self.ignore_room_id_list = cfg.get('ignore_room_id_list') if cfg.get(
                    'ignore_room_id_list') else self.ignore_room_id_list
                self.big_redpocket = cfg.get('big_redpocket') if cfg.get('big_redpocket') else self.big_redpocket
                self.check_data_from_server_time = cfg.get('check_data_from_server_time') if cfg.get(
                    'check_data_from_server_time') else self.check_data_from_server_time
                self.push_me_sw = cfg.get('push_me_sw') if cfg.get('push_me_sw') else self.push_me_sw
            else:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    cfg = {
                        "unignore_keywords": self.unignore_keywords,
                        "big_redpocket": self.big_redpocket,
                        "check_data_from_server_time": self.check_data_from_server_time,
                        "push_me_sw": self.push_me_sw
                    }

                    f.write(json.dumps(cfg, indent=4, ensure_ascii=False))
        except Exception as e:
            live_monitor_logger.exception(f'刷新配置文件失败！{e}')

    def remove_anchor_list_element(self, server_data_id):
        """
        移除anchorlist的元素
        :param server_data_id:
        :return:
        """
        for i in self.anchor_list:
            if i.server_data_id == server_data_id:
                self.anchor_list.remove(i)
                break
        self.recorded_anchor_server_data_id_list = self.recorded_anchor_server_data_id_list[-1000:]

    def remove_popularity_red_pocket(self, lot_id):
        """
        移除popularity_red_pocket_list的元素
        :param lot_id:
        :return:
        """
        for i in self.popularity_red_pocket_list:
            if i.lot_id == lot_id:
                self.popularity_red_pocket_list.remove(i)
                break
        self.recorded_red_pocket_id_list = self.recorded_red_pocket_id_list[-1000:]

    def generate_redis_data_form(self, da: Union[Type[Anchor], Type[PopularityRedPocket]]) -> dict:
        '''
        生成推送到redis的json格式数据
        :param da:
        :return:
        '''
        if type(da) is Anchor:
            anchor = da
            return {
                'type': 'anchor',
                'lot_id': anchor.server_data_id,
                'gift_num': anchor.gift_num,
                'gift_price': anchor.gift_price,
                'anchor_uid': anchor.ruid,
                'room_id': anchor.room_id,
                'require_type': anchor.require_type,
                'end_time': anchor.current_ts + anchor.time,
                'danmu': anchor.danmu,
                'award_name': anchor.award_name,
                'live_room_url': f'https://live.bilibili.com/{anchor.room_id}?hotRank=0&launch_id=1000229&live_from=71003',
                'app_schema': f'bilibili://live/{anchor.room_id}',
            }
        if type(da) is PopularityRedPocket:
            popularity_red_pocket = da
            return {
                'type': 'popularity_red_pocket',
                'lot_id': popularity_red_pocket.lot_id,
                'anchor_uid': self.get_roomid_2_uid(popularity_red_pocket.room_id),
                'room_id': popularity_red_pocket.room_id,
                'end_time': popularity_red_pocket.end_time,
                'total_price': popularity_red_pocket.total_price,
                'live_room_url': f'https://live.bilibili.com/{popularity_red_pocket.room_id}?hotRank=0&launch_id=1000229&live_from=71003',
                'app_schema': f'bilibili://live/{popularity_red_pocket.room_id}',
            }

    def push_lot_data(self):
        """
        将抽奖信息推送到pushme上面
        :return:
        """

        def push_anchor() -> List[Type[Anchor]]:
            """
            返回所有抽奖
            :return:
            """
            title = '天选时刻'
            content = ''
            anchor_list = deepcopy(self.anchor_list)
            unignore_list = []
            if not anchor_list:
                return []
            anchor_list.sort(key=lambda x: (x.time + x.current_ts))
            for anchor in anchor_list:
                anchor_left_ts = int(anchor.time + anchor.current_ts - int(time.time()))
                if anchor_left_ts <= 0:
                    continue
                if anchor.require_type == 2 or anchor.require_type == 3:  # 0:无 1:关注主播 2:粉丝勋章 3:大航海 4:直播用户等级 5:主站等级
                    continue
                app_jump_url = f'bilibili://live/{anchor.room_id}'
                award_show_text = f'{anchor.award_name} * {anchor.award_num}'
                anchor_money = anchor.gift_price * anchor.gift_num
                push_text = f'【{anchor.require_text}】\n【{award_show_text}】\n【{anchor_left_ts}秒】\n需要【{anchor_money // 1000}】元参加\n【弹幕：{anchor.danmu}】\n>>[【直播间】]({app_jump_url})'
                content += f'>{push_text}\n---\n'
                if int(anchor.room_id) not in self.ignore_room_id_list and all(
                        element not in award_show_text + anchor.danmu for element in
                        self.ignore_keywords):
                    # live_monitor_log.critical(f'{award_show_text + anchor.danmu}不包含ignore关键词！！！{self.ignore_keywords}')
                    if any(element in award_show_text + anchor.danmu for element in
                           self.unignore_keywords):
                        live_monitor_logger.info(
                            f'{award_show_text + anchor.danmu}不包含不忽略关键词！！！{self.unignore_keywords}')
                        if anchor_money == 0 and anchor.award_name not in ['小花花']:
                            self.recorded_unignore_lot.append(anchor.id)
                            unignore_list.append(f'>{push_text}\n---\n')
                            if not self.redis_manager.exists(anchor.server_data_id):
                                live_monitor_logger.debug(f'添加至redis {anchor.server_data_id}')
                                self.redis_manager.setex_unignore_lot_info(anchor.server_data_id, anchor_left_ts,
                                                                           json.dumps(
                                                                               self.generate_redis_data_form(anchor))
                                                                           )
            if content:
                if int(time.time()) - self.latest_push_me_time >= self.push_me_time and self.push_me_sw:
                    pushme(title, content, 'markdata')
            if unignore_list and self.push_me_sw:
                pushme('天选抽奖', ''.join(unignore_list), 'markdown')
            return anchor_list

        def push_red_popup() -> List[Type[PopularityRedPocket]]:
            title = '直播间红包'
            content = ''
            popularity_red_pocket_list = deepcopy(self.popularity_red_pocket_list)
            unignore_list = []
            if not popularity_red_pocket_list:
                return []
            popularity_red_pocket_list.sort(key=lambda x: x.end_time)
            for popularity_red_pocket in popularity_red_pocket_list:
                popularity_red_pocket_left_ts = int(popularity_red_pocket.end_time - int(time.time()))
                app_jump_url = f'bilibili://live/{popularity_red_pocket.room_id}'
                push_text = f'【红包金额：{popularity_red_pocket.total_price // 1000}元】\n【{popularity_red_pocket_left_ts:^4}秒】\n【弹幕：{popularity_red_pocket.danmu:^15}】\n【剩余{popularity_red_pocket.wait_num}个红包】\n>>[【直播间】]({app_jump_url})'
                content += f'>{push_text}\n---\n'
                if popularity_red_pocket.total_price // 1000 >= self.big_redpocket and popularity_red_pocket.lot_id not in self.recorded_unignore_lot:
                    self.recorded_unignore_lot.append(popularity_red_pocket.lot_id)
                    unignore_list.append(f'>{push_text}\n---\n')
                    if not self.redis_manager.exists(popularity_red_pocket.lot_id):
                        live_monitor_logger.debug(f'添加至redis {popularity_red_pocket.lot_id}')
                        self.redis_manager.setex_unignore_lot_info(popularity_red_pocket.lot_id,
                                                                   popularity_red_pocket_left_ts if popularity_red_pocket_left_ts > 0 else 1,
                                                                   json.dumps(self.generate_redis_data_form(
                                                                       popularity_red_pocket))
                                                                   )

            if content:
                if int(time.time()) - self.latest_push_me_time >= self.push_me_time and self.push_me_sw:
                    self.latest_push_me_time = int(time.time())
                    pushme(title, content, 'markdata')
            if unignore_list and self.push_me_sw:
                pushme('大红包抽奖', ''.join(unignore_list), 'markdown')
            return popularity_red_pocket_list

        try:
            # live_monitor_logger.info('推送至pushme！')
            ac_list = push_anchor()
            rp_list = push_red_popup()
            self.redis_manager.set_all_lot_info(  # 添加进redis的一般抽奖
                json.dumps([self.generate_redis_data_form(x) for x in ac_list + rp_list])
            )
        except Exception as e:
            live_monitor_logger.exception(f'推送至pushme失败！{e}')

        self.fresh_config()

        self.recorded_unignore_lot = self.recorded_unignore_lot[-100:]
        threading.Timer(self.push_time, self.push_lot_data).start()

    def show_lot(self):
        """
        循环抽奖列表，打印在屏幕上，过期的就删掉
        :return:
        """
        try:
            anchor_list: list[Type[Anchor]] = deepcopy(self.anchor_list)
            if anchor_list:
                anchor_list.sort(key=lambda x: (x.time + x.current_ts))
            for anchor in anchor_list:
                anchor_left_ts = int(anchor.time + anchor.current_ts - int(time.time()))
                if anchor_left_ts <= 0:
                    self.remove_anchor_list_element(anchor.server_data_id)
                    continue
                live_url = f'https://live.bilibili.com/{anchor.room_id}'
                award_show_text = f'{anchor.award_name} * {anchor.award_num}'
                anchor_money = anchor.gift_price * anchor.gift_num
                live_monitor_log_text = f'{self.generate_redis_data_form(anchor)}\n【天选时刻】{anchor.server_data_id:^8}【{anchor.require_text:^14}】【{award_show_text:^10}】【{anchor_left_ts:^4}秒】 需要【{anchor_money // 1000:^3}】元参加 【弹幕：{anchor.danmu:^15}】 【{live_url:^35}】'
                live_monitor_logger.debug(live_monitor_log_text)
            popularity_red_pocket_list: list[Type[PopularityRedPocket]] = deepcopy(self.popularity_red_pocket_list)
            if popularity_red_pocket_list:
                popularity_red_pocket_list.sort(key=lambda x: x.end_time)
            for popularity_red_pocket in popularity_red_pocket_list:
                popularity_red_pocket_left_ts = int(popularity_red_pocket.end_time - int(time.time()))
                if popularity_red_pocket_left_ts <= 0:
                    self.remove_popularity_red_pocket(popularity_red_pocket.lot_id)
                    continue
                live_url = f'https://live.bilibili.com/{popularity_red_pocket.room_id}'
                live_monitor_log_text = f'{self.generate_redis_data_form(popularity_red_pocket)}\n【红包抽奖{popularity_red_pocket.lot_id:^10}】 【红包金额：{popularity_red_pocket.total_price // 1000:^4}元】 【{popularity_red_pocket_left_ts:^4}秒】 【弹幕：{popularity_red_pocket.danmu:^15}】 【剩余{popularity_red_pocket.wait_num}个红包】 【{live_url:^35}】'
                live_monitor_logger.info(live_monitor_log_text)
            live_monitor_logger.info("\n****************************************************\n")
        except Exception as e:
            live_monitor_logger.exception('循环获取抽奖信息失败！{e}')
        threading.Timer(10, self.show_lot).start()

    def check_data_from_server(self):
        while 1:
            try:
                server_response: list[dict] = tool.Tool.get_data_from_server()
                # try:
                self.solve_data_from_server(server_response)
                time.sleep(self.check_data_from_server_time)
            except Exception as e:
                live_monitor_logger.error(f'获取服务器数据失败！{e}')

    def solve_serve_data(self, da: dict):

        data: str = da.get('data')
        lottery_info_web_data = {}
        bt = 0

        while bt <= 3:
            try:
                eval_data = ast.literal_eval(data)
                if type(eval_data) is list:  # 群友中奖通知
                    return
                if eval_data.get('type') == 'anchor':
                    db_anchor = self.sq.get_anchor_by_server_data_id(da.get('id'))
                    if db_anchor:
                        anchor_left_ts = int(db_anchor.time + db_anchor.current_ts - int(time.time()))
                        if anchor_left_ts <= 0:
                            return
                        self.anchor_list.append(db_anchor)
                        return
                if eval_data.get('type') == 'popularity_red_pocket':
                    red_pocket = self.sq.get_popularity_red_package_by_lot_id(da.get('id'))
                    if red_pocket:
                        popularity_red_pocket_left_ts = int(red_pocket.end_time - int(time.time()))
                        if popularity_red_pocket_left_ts <= 0:
                            return
                        self.popularity_red_pocket_list.append(red_pocket)
                        return
                lottery_info_web_data = tool.Tool.getLotteryInfoWeb(da.get('room_id'))
                self.solve_lottery_info_web_data(lottery_info_web_data, da)
                return
            except Exception as e:
                if '【' in data:
                    live_monitor_logger.info(
                        f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                if '在线打卡' in data:
                    live_monitor_logger.info(
                        f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                if data in self.gift_list:
                    live_monitor_logger.info(
                        f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                bt += 1
                live_monitor_logger.exception(f'解析服务器数据失败，当前重试次数：{bt}{da}\n{lottery_info_web_data}\n{e}')
                continue
        live_monitor_logger.error(f'解析服务器数据失败！！！\t{da}')

    def solve_lottery_info_web_data(self, lottery_info_web_data: dict, server_data: dict):
        data = lottery_info_web_data.get('data')
        anchor_data: dict or None = data.get('anchor')
        popularity_red_pocket_data: list[dict] or None = data.get('popularity_red_pocket')
        if anchor_data:
            anchor = Anchor(
                server_data_id=anchor_data.get('id'),
                room_id=anchor_data.get('room_id'),
                status=anchor_data.get('status'),
                asset_icon=anchor_data.get('asset_icon'),
                award_name=anchor_data.get('award_name'),
                award_num=anchor_data.get('award_num'),
                award_image=anchor_data.get('award_image'),
                danmu=anchor_data.get('danmu'),
                time=anchor_data.get('time'),
                current_ts=anchor_data.get('current_time'),
                join_type=anchor_data.get('join_type'),
                require_type=anchor_data.get('require_type'),
                require_value=anchor_data.get('require_value'),
                require_text=anchor_data.get('require_text'),
                gift_id=anchor_data.get('gift_id'),
                gift_name=anchor_data.get('gift_name'),
                gift_num=anchor_data.get('gift_num'),
                gift_price=anchor_data.get('gift_price'),
                cur_gift_num=anchor_data.get('cur_gift_num'),
                goaway_time=anchor_data.get('goaway_time'),
                award_users=json.dumps(anchor_data.get('award_users'), ensure_ascii=False),
                show_panel=anchor_data.get('show_panel'),
                url=anchor_data.get('url'),
                lot_status=anchor_data.get('lot_status'),
                web_url=anchor_data.get('web_url'),
                send_gift_ensure=anchor_data.get('send_gift_ensure'),
                goods_id=anchor_data.get('goods_id'),
                award_type=anchor_data.get('award_type'),
                award_price_text=anchor_data.get('award_price_text'),
                ruid=anchor_data.get('ruid'),
                asset_icon_webp=anchor_data.get('asset_icon_webp'),
                danmu_type=anchor_data.get('danmu_type'),
                danmu_new=json.dumps(anchor_data.get('danmu_new'), ensure_ascii=False),
            )
            self.sq.add_anchor(anchor)
            if anchor.server_data_id not in self.recorded_anchor_server_data_id_list:
                self.anchor_list.append(anchor)
                self.recorded_anchor_server_data_id_list.append(anchor.server_data_id)

        if popularity_red_pocket_data:
            for item in popularity_red_pocket_data:
                pop = PopularityRedPocket(
                    lot_id=item.get('lot_id'),
                    room_id=server_data.get('room_id'),
                    sender_uid=item.get('sender_uid'),
                    sender_face=item.get('sender_face'),
                    join_requirement=item.get('join_requirement'),
                    danmu=item.get('danmu'),
                    awards=json.dumps(item.get('awards'), ensure_ascii=False),
                    start_time=item.get('start_time'),
                    end_time=item.get('end_time'),
                    last_time=item.get('last_time'),
                    remove_time=item.get('remove_time'),
                    replace_time=item.get('replace_time'),
                    current_ts=item.get('current_time'),
                    lot_status=item.get('lot_status'),
                    h5_url=item.get('h5_url'),
                    user_status=item.get('user_status'),
                    lot_config_id=item.get('lot_config_id'),
                    total_price=item.get('total_price'),
                    wait_num=item.get('wait_num'),
                )
                self.sq.add_popularity_red_package(pop)
                if pop.lot_id not in self.recorded_red_pocket_id_list:
                    self.popularity_red_pocket_list.append(pop)
                    self.recorded_red_pocket_id_list.append(pop.lot_id)

    def get_roomid_2_uid(self, room_id: int) -> int:
        try:
            res = self.sq.get_room_uid_by_room_id(room_id)
            if res is not None:
                return res.uid
            uid = tool.Tool.get_roomid_2_uid(room_id)
            room_id_2_uid = TRoomUid(
                room_id=room_id,
                uid=uid
            )
            self.sq.add_room_uid(room_id_2_uid)
            return uid
        except Exception as e:
            live_monitor_logger.exception(f'获取room_id对应uid信息失败！错误信息：{e}')
            return 0

    def solve_data_from_server(self, server_response: list[dict]):
        for da in server_response:
            _id = da['id']
            if _id != 999999999999:
                db_data = self.sq.get_server_data_by_id(_id)
                if db_data:
                    # live_monitor_log.debug(f'已存在id:{id}\n{db_data.__dict__}')
                    if _id in self.recorded_server_data_id_list:
                        continue
                    if _id in self.recorded_anchor_server_data_id_list or _id in self.recorded_red_pocket_id_list:
                        continue  # 已存在则跳过
                else:
                    sd = ServerData(
                        id=da.get('id'),
                        created_at=tool.Tool.str_2_DateTime(da.get('created_at'), '%Y-%m-%dT%H:%M:%S', 8),
                        data=da.get('data'),
                        ip=da.get('ip'),
                        room_id=da.get('room_id'),
                        updated_at=tool.Tool.str_2_DateTime(da.get('updated_at'), '%Y-%m-%dT%H:%M:%S', 8)
                    )
                    self.sq.add_server_data(sd)
            if _id not in self.recorded_server_data_id_list:
                self.recorded_server_data_id_list.append(_id)
                self.recorded_server_data_id_list = self.recorded_server_data_id_list[-1000:]
            Thd = threading.Thread(target=self.solve_serve_data, args=(da,))
            Thd.start()

    @pushme_try_catch_decorator
    def main(self, ShowLog=True):
        logger.info('启动监控直播抽奖程序！！！')
        if not ShowLog:
            live_monitor_logger.remove()
        live_monitor_logger.add(
            os.path.join(CONFIG.CONFIG.root_dir, "fastapi接口/scripts/log/error_live_monitor_log.log"),
            level="WARNING",
            encoding="utf-8",
            enqueue=True,
            rotation="500MB",
            compression="zip",
            retention="15 days",
            filter=lambda record: record["extra"].get('user') == "live_monitor_log"
        )
        self.check_data_from_server()


class AsyncMonitor(BaseMonitor):

    def __init__(self):
        super().__init__()
        self.sq = AsyncSqlHelper()

        self.redis_manager = AsyncBiliLiveLotRedisManager()
        self.GOLDBOX = GOLDBOX(self.redis_manager)
        self.tasks = []
        self.fresh_config()
        self.task_set = set()

    def init_background_task(self):
        _t1 = asyncio.create_task(self.show_lot())
        _t2 = asyncio.create_task(self.push_lot_data())
        _t3 = asyncio.create_task(self.GOLDBOX.async_check_goldbox())
        self.tasks.extend([_t1, _t2, _t3])

    def fresh_config(self):
        try:
            if os.path.exists(self.dir + 'config.json'):
                with open(self.dir + 'config.json', 'r', encoding='utf-8') as f:
                    cfg = json.loads(f.read())
                self.unignore_keywords = cfg.get('unignore_keywords') if cfg.get(
                    'unignore_keywords') else self.unignore_keywords
                self.ignore_keywords = cfg.get('ignore_keywords') if cfg.get(
                    'ignore_keywords') else self.unignore_keywords
                self.ignore_room_id_list = cfg.get('ignore_room_id_list') if cfg.get(
                    'ignore_room_id_list') else self.ignore_room_id_list
                self.big_redpocket = cfg.get('big_redpocket') if cfg.get('big_redpocket') else self.big_redpocket
                self.check_data_from_server_time = cfg.get('check_data_from_server_time') if cfg.get(
                    'check_data_from_server_time') else self.check_data_from_server_time
                self.push_me_sw = cfg.get('push_me_sw') if cfg.get('push_me_sw') else self.push_me_sw
            else:
                with open(self.dir + 'config.json', 'w', encoding='utf-8') as f:
                    cfg = {
                        "unignore_keywords": self.unignore_keywords,
                        "big_redpocket": self.big_redpocket,
                        "check_data_from_server_time": self.check_data_from_server_time,
                        "push_me_sw": self.push_me_sw
                    }
                    f.write(json.dumps(cfg, indent=4))
        except Exception as e:
            live_monitor_logger.exception(f'刷新配置文件失败！{e}')

    def remove_anchor_list_element(self, server_data_id):
        """
        移除anchorlist的元素
        :param server_data_id:
        :return:
        """
        for i in self.anchor_list:
            if i.server_data_id == server_data_id:
                self.anchor_list.remove(i)
                break
        self.recorded_anchor_server_data_id_list = self.recorded_anchor_server_data_id_list[-1000:]

    def remove_popularity_red_pocket(self, lot_id):
        """
        移除popularity_red_pocket_list的元素
        :param lot_id:
        :return:
        """
        for i in self.popularity_red_pocket_list:
            if i.lot_id == lot_id:
                self.popularity_red_pocket_list.remove(i)
                break
        self.recorded_red_pocket_id_list = self.recorded_red_pocket_id_list[-1000:]

    async def generate_redis_data_form(self, da: Union[Type[Anchor], Type[PopularityRedPocket]]) -> dict:
        '''
        生成推送到redis的json格式数据
        :param da:
        :return:
        '''
        if type(da) is Anchor:
            anchor = da
            return {
                'type': 'anchor',
                'lot_id': anchor.server_data_id,
                'gift_num': anchor.gift_num,
                'gift_price': anchor.gift_price,
                'anchor_uid': anchor.ruid,
                'room_id': anchor.room_id,
                'require_type': anchor.require_type,
                'end_time': anchor.current_ts + anchor.time,
                'danmu': anchor.danmu,
                'award_name': anchor.award_name,
                'live_room_url': f'https://live.bilibili.com/{anchor.room_id}?hotRank=0&launch_id=1000229&live_from=71003',
                'app_schema': f'bilibili://live/{anchor.room_id}',
            }
        if type(da) is PopularityRedPocket:
            popularity_red_pocket = da
            return {
                'type': 'popularity_red_pocket',
                'lot_id': popularity_red_pocket.lot_id,
                'anchor_uid': await self.get_roomid_2_uid(popularity_red_pocket.room_id),
                'room_id': popularity_red_pocket.room_id,
                'end_time': popularity_red_pocket.end_time,
                'total_price': popularity_red_pocket.total_price,
                'live_room_url': f'https://live.bilibili.com/{popularity_red_pocket.room_id}?hotRank=0&launch_id=1000229&live_from=71003',
                'app_schema': f'bilibili://live/{popularity_red_pocket.room_id}',
            }

    async def push_lot_data(self):
        """
        将抽奖信息推送到pushme上面
        :return:
        """

        async def push_anchor() -> List[Type[Anchor]]:
            """
            返回所有抽奖
            :return:
            """
            title = '天选时刻'
            content = ''
            anchor_list = deepcopy(self.anchor_list)
            unignore_list = []
            if not anchor_list:
                return []
            anchor_list.sort(key=lambda x: (x.time + x.current_ts))
            for anchor in anchor_list:
                anchor_left_ts = int(anchor.time + anchor.current_ts - int(time.time()))
                if anchor_left_ts <= 0:
                    continue
                if anchor.require_type == 2 or anchor.require_type == 3:  # 0:无 1:关注主播 2:粉丝勋章 3:大航海 4:直播用户等级 5:主站等级
                    continue
                app_jump_url = f'bilibili://live/{anchor.room_id}'
                award_show_text = f'{anchor.award_name} * {anchor.award_num}'
                anchor_money = anchor.gift_price * anchor.gift_num
                push_text = f'【{anchor.require_text}】\n【{award_show_text}】\n【{anchor_left_ts}秒】\n需要【{anchor_money // 1000}】元参加\n【弹幕：{anchor.danmu}】\n>>[【直播间】]({app_jump_url})'
                content += f'>{push_text}\n---\n'
                if int(anchor.room_id) not in self.ignore_room_id_list and all(
                        element not in award_show_text + anchor.danmu for element in
                        self.ignore_keywords):
                    # live_monitor_log.critical(f'{award_show_text + anchor.danmu}不包含ignore关键词！！！{self.ignore_keywords}')
                    if any(element in award_show_text + anchor.danmu for element in
                           self.unignore_keywords):
                        live_monitor_logger.info(
                            f'{award_show_text + anchor.danmu}不包含不忽略关键词！！！{self.unignore_keywords}')
                        if anchor_money == 0 and anchor.award_name not in ['小花花']:
                            self.recorded_unignore_lot.append(anchor.id)
                            unignore_list.append(f'>{push_text}\n---\n')
                            if not await self.redis_manager.exists(anchor.server_data_id):
                                live_monitor_logger.debug(f'添加至redis {anchor.server_data_id}')
                                await self.redis_manager.setex_unignore_lot_info(
                                    anchor.server_data_id, anchor_left_ts,
                                    json.dumps(
                                        await self.generate_redis_data_form(anchor))
                                )
            if content:
                if int(time.time()) - self.latest_push_me_time >= self.push_me_time and self.push_me_sw:
                    await asyncio.to_thread(pushme, title, content, 'markdata')
            if unignore_list and self.push_me_sw:
                await asyncio.to_thread(pushme, '天选抽奖', ''.join(unignore_list), 'markdown')
            return anchor_list

        async def push_red_popup() -> List[Type[PopularityRedPocket]]:
            title = '直播间红包'
            content = ''
            popularity_red_pocket_list = deepcopy(self.popularity_red_pocket_list)
            unignore_list = []
            if not popularity_red_pocket_list:
                return []
            popularity_red_pocket_list.sort(key=lambda x: x.end_time)
            for popularity_red_pocket in popularity_red_pocket_list:
                popularity_red_pocket_left_ts = int(popularity_red_pocket.end_time - int(time.time()))
                app_jump_url = f'bilibili://live/{popularity_red_pocket.room_id}'
                push_text = f'【红包金额：{popularity_red_pocket.total_price // 1000}元】\n【{popularity_red_pocket_left_ts:^4}秒】\n【弹幕：{popularity_red_pocket.danmu:^15}】\n【剩余{popularity_red_pocket.wait_num}个红包】\n>>[【直播间】]({app_jump_url})'
                content += f'>{push_text}\n---\n'
                if popularity_red_pocket.total_price // 1000 >= self.big_redpocket and popularity_red_pocket.lot_id not in self.recorded_unignore_lot:
                    self.recorded_unignore_lot.append(popularity_red_pocket.lot_id)
                    unignore_list.append(f'>{push_text}\n---\n')
                    if not await self.redis_manager.exists(popularity_red_pocket.lot_id):
                        live_monitor_logger.debug(f'添加至redis {popularity_red_pocket.lot_id}')
                        await self.redis_manager.setex_unignore_lot_info(
                            popularity_red_pocket.lot_id,
                            popularity_red_pocket_left_ts if popularity_red_pocket_left_ts > 0 else 1,
                            json.dumps(await self.generate_redis_data_form(popularity_red_pocket))
                        )
            if content:
                if int(time.time()) - self.latest_push_me_time >= self.push_me_time and self.push_me_sw:
                    self.latest_push_me_time = int(time.time())
                    await asyncio.to_thread(pushme, title, content, 'markdata')
            if unignore_list and self.push_me_sw:
                await asyncio.to_thread(pushme, '大红包抽奖', ''.join(unignore_list), 'markdown')
            return popularity_red_pocket_list

        while 1:
            try:
                # live_monitor_logger.info('推送至pushme！')
                ac_list = await push_anchor()
                rp_list = await push_red_popup()
                await self.redis_manager.set_all_lot_info(json.dumps(
                    [await self.generate_redis_data_form(x) for x in
                     ac_list + rp_list])
                )  # 添加进redis的一般抽奖

            except Exception as e:
                live_monitor_logger.exception(f'推送至pushme失败！{e}')
            await asyncio.to_thread(self.fresh_config)
            self.recorded_unignore_lot = self.recorded_unignore_lot[-100:]
            await asyncio.sleep(self.push_time)

    async def show_lot(self):
        """
        循环抽奖列表，打印在屏幕上，过期的就删掉
        :return:
        """
        while 1:
            try:
                anchor_list: list[Type[Anchor]] = deepcopy(self.anchor_list)
                if anchor_list:
                    anchor_list.sort(key=lambda x: (x.time + x.current_ts))
                for anchor in anchor_list:
                    anchor_left_ts = int(anchor.time + anchor.current_ts - int(time.time()))
                    if anchor_left_ts <= 0:
                        self.remove_anchor_list_element(anchor.server_data_id)
                        continue
                    live_url = f'https://live.bilibili.com/{anchor.room_id}'
                    award_show_text = f'{anchor.award_name} * {anchor.award_num}'
                    anchor_money = anchor.gift_price * anchor.gift_num
                    live_monitor_log_text = f'{await self.generate_redis_data_form(anchor)}\n【天选时刻】{anchor.server_data_id:^8}【{anchor.require_text:^14}】【{award_show_text:^10}】【{anchor_left_ts:^4}秒】 需要【{anchor_money // 1000:^3}】元参加 【弹幕：{anchor.danmu:^15}】 【{live_url:^35}】'
                    # live_monitor_logger.debug(live_monitor_log_text)
                popularity_red_pocket_list: list[Type[PopularityRedPocket]] = deepcopy(self.popularity_red_pocket_list)
                if popularity_red_pocket_list:
                    popularity_red_pocket_list.sort(key=lambda x: x.end_time)
                for popularity_red_pocket in popularity_red_pocket_list:
                    popularity_red_pocket_left_ts = int(popularity_red_pocket.end_time - int(time.time()))
                    if popularity_red_pocket_left_ts <= 0:
                        self.remove_popularity_red_pocket(popularity_red_pocket.lot_id)
                        continue
                    live_url = f'https://live.bilibili.com/{popularity_red_pocket.room_id}'
                    live_monitor_log_text = f'{await self.generate_redis_data_form(popularity_red_pocket)}\n【红包抽奖{popularity_red_pocket.lot_id:^10}】 【红包金额：{popularity_red_pocket.total_price // 1000:^4}元】 【{popularity_red_pocket_left_ts:^4}秒】 【弹幕：{popularity_red_pocket.danmu:^15}】 【剩余{popularity_red_pocket.wait_num}个红包】 【{live_url:^35}】'
                    # live_monitor_logger.debug(live_monitor_log_text)
                # live_monitor_logger.info("\n****************************************************\n")
            except Exception as e:
                live_monitor_logger.exception(f'循环获取抽奖信息失败！{e}')
            await asyncio.sleep(10)

    async def async_solve_server_data(self, da: dict):
        data: str = da.get('data')
        lottery_info_web_data = {}
        bt = 0
        while bt <= 3:
            try:
                eval_data = ast.literal_eval(data)
                if type(eval_data) is list:  # 群友中奖通知
                    return
                if eval_data.get('type') == 'anchor':
                    db_anchor = await self.sq.get_anchor_by_server_data_id(da.get('id'))
                    if db_anchor:
                        anchor_left_ts = int(db_anchor.time + db_anchor.current_ts - int(time.time()))
                        if anchor_left_ts <= 0:
                            return
                        self.anchor_list.append(db_anchor)
                        return
                if eval_data.get('type') == 'popularity_red_pocket':
                    red_pocket = await self.sq.get_popularity_red_package_by_lot_id(da.get('id'))
                    if red_pocket:
                        popularity_red_pocket_left_ts = int(red_pocket.end_time - int(time.time()))
                        if popularity_red_pocket_left_ts <= 0:
                            return
                        self.popularity_red_pocket_list.append(red_pocket)
                        return
                lottery_info_web_data = await AsyncTool.getLotteryInfoWeb(da.get('room_id'))
                await self.solve_lottery_info_web_data(lottery_info_web_data, da)
                return
            except Exception as e:
                if '【' in data:
                    # live_monitor_logger.info(
                    #     f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                if '在线打卡' in data:
                    # live_monitor_logger.info(
                    #     f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                if data in self.gift_list:
                    # live_monitor_logger.info(
                    #     f'\n{data} https://space.bilibili.com/{da.get("room_id")} ip:{da.get("ip")} {da.get("updated_at")}')
                    return
                bt += 1
                live_monitor_logger.exception(f'解析服务器数据失败，当前重试次数：{bt}{da}\n{lottery_info_web_data}\n{e}')
                await asyncio.sleep(3)
                continue
        live_monitor_logger.error(f'解析服务器数据失败！！！\t{da}')

    async def solve_redpacket_winner(self, lot_id: int, room_id: int):
        return
        resp = await AsyncTool.RedPocketGetWinners(lot_id, room_id)
        if data := resp.get('data'):
            if winners := data.get('winner_info'):
                for winner in winners:
                    pr_winner = PopularityRedPocketWinner(
                        lot_id=lot_id,
                        award_big_pic=winner.get('award_big_pic'),
                        award_name=winner.get('award_name'),
                        award_pic=winner.get('award_pic'),
                        award_price=winner.get('award_price'),
                        bag_id=winner.get('bag_id'),
                        gift_id=winner.get('gift_id'),
                        gift_num=winner.get('gift_num'),
                        guard_ext=winner.get('guard_ext'),
                        is_mystery=winner.get('is_mystery'),
                        name=winner.get('name'),
                        outdate_time=winner.get('outdate_time'),
                        uid=winner.get('uid'),
                        uinfo=winner.get('uinfo'),
                        use_timestamp=winner.get('use_timestamp'),
                        user_type=winner.get('user_type'),
                    )
                    await self.sq.add_redpacket_winner(pr_winner)
            # live_monitor_logger.debug(
            #     f"【红包抽奖】id:{lot_id} 检查到奖品数量【{data.get('award_num')}/{data.get('total_num')}】的中奖信息：{data.get('winner_info')}")

    async def solve_anchor_winner(self, server_data):
        lottery_info_web_data = await AsyncTool.getLotteryInfoWeb(server_data.get('room_id'))
        return await self.solve_lottery_info_web_data(lottery_info_web_data, server_data, True)

    async def solve_lottery_info_web_data(self, lottery_info_web_data: dict, server_data: dict,
                                          is_check_result: bool = False):
        data = lottery_info_web_data.get('data')
        anchor_data: dict or None = data.get('anchor')
        popularity_red_pocket_data: list[dict] or None = data.get('popularity_red_pocket')
        if anchor_data:
            anchor = Anchor(
                server_data_id=anchor_data.get('id'),
                room_id=anchor_data.get('room_id'),
                status=anchor_data.get('status'),
                asset_icon=anchor_data.get('asset_icon'),
                award_name=anchor_data.get('award_name'),
                award_num=anchor_data.get('award_num'),
                award_image=anchor_data.get('award_image'),
                danmu=anchor_data.get('danmu'),
                time=anchor_data.get('time'),
                current_ts=anchor_data.get('current_time'),
                join_type=anchor_data.get('join_type'),
                require_type=anchor_data.get('require_type'),
                require_value=anchor_data.get('require_value'),
                require_text=anchor_data.get('require_text'),
                gift_id=anchor_data.get('gift_id'),
                gift_name=anchor_data.get('gift_name'),
                gift_num=anchor_data.get('gift_num'),
                gift_price=anchor_data.get('gift_price'),
                cur_gift_num=anchor_data.get('cur_gift_num'),
                goaway_time=anchor_data.get('goaway_time'),
                award_users=json.dumps(anchor_data.get('award_users'), ensure_ascii=False),
                show_panel=anchor_data.get('show_panel'),
                url=anchor_data.get('url'),
                lot_status=anchor_data.get('lot_status'),
                web_url=anchor_data.get('web_url'),
                send_gift_ensure=anchor_data.get('send_gift_ensure'),
                goods_id=anchor_data.get('goods_id'),
                award_type=anchor_data.get('award_type'),
                award_price_text=anchor_data.get('award_price_text'),
                ruid=anchor_data.get('ruid'),
                asset_icon_webp=anchor_data.get('asset_icon_webp'),
                danmu_type=anchor_data.get('danmu_type'),
                danmu_new=json.dumps(anchor_data.get('danmu_new'), ensure_ascii=False),
            )
            await self.sq.add_anchor(anchor)
            if json.loads(anchor.award_users):
                ...
                # live_monitor_logger.debug(
                #     f'【天选时刻】{anchor.server_data_id:^8} https://live.bilibili.com/{anchor.room_id} 检查到奖品【{anchor.award_name} * {anchor.award_num}】的中奖信息：{anchor.award_users}')
            else:
                delay = anchor.current_ts + anchor.time - int(time.time()) + 1
                delay = delay if delay > 0 else 0.5
                if is_check_result:
                    ...
                    # live_monitor_logger.debug(
                    #     f'【天选时刻】{anchor.server_data_id:^8} https://live.bilibili.com/{anchor.room_id} 未检查到奖品【{anchor.award_name} * {anchor.award_num}】的中奖信息：{anchor.award_users} {delay}秒后重新获取')
                loop = asyncio.get_running_loop()
                loop.call_later(
                    delay,
                    lambda: asyncio.create_task(self.solve_anchor_winner(
                        server_data))
                )
            if anchor.server_data_id not in self.recorded_anchor_server_data_id_list:
                self.anchor_list.append(anchor)
                self.recorded_anchor_server_data_id_list.append(anchor.server_data_id)

        if popularity_red_pocket_data:
            for item in popularity_red_pocket_data:
                pop = PopularityRedPocket(
                    lot_id=item.get('lot_id'),
                    room_id=server_data.get('room_id'),
                    sender_uid=item.get('sender_uid'),
                    sender_face=item.get('sender_face'),
                    join_requirement=item.get('join_requirement'),
                    danmu=item.get('danmu'),
                    awards=json.dumps(item.get('awards'), ensure_ascii=False),
                    start_time=item.get('start_time'),
                    end_time=item.get('end_time'),
                    last_time=item.get('last_time'),
                    remove_time=item.get('remove_time'),
                    replace_time=item.get('replace_time'),
                    current_ts=item.get('current_time'),
                    lot_status=item.get('lot_status'),
                    h5_url=item.get('h5_url'),
                    user_status=item.get('user_status'),
                    lot_config_id=item.get('lot_config_id'),
                    total_price=item.get('total_price'),
                    wait_num=item.get('wait_num'),
                )
                await self.sq.add_popularity_red_package(pop)
                if pop.lot_id not in self.recorded_red_pocket_id_list:
                    loop = asyncio.get_running_loop()
                    loop.call_later(
                        pop.end_time - int(time.time()),
                        lambda: asyncio.create_task(self.solve_redpacket_winner(
                            pop.lot_id, pop.room_id)
                        )
                    )
                    self.popularity_red_pocket_list.append(pop)
                    self.recorded_red_pocket_id_list.append(pop.lot_id)

    async def get_roomid_2_uid(self, room_id: int) -> int:
        try:
            res = await self.sq.get_room_uid_by_room_id(room_id)
            if res is not None:
                return res.uid
            uid = await AsyncTool.get_roomid_2_uid(room_id)
            room_id_2_uid = TRoomUid(
                room_id=room_id,
                uid=uid
            )
            await self.sq.add_room_uid(room_id_2_uid)
            return uid
        except Exception as e:
            live_monitor_logger.exception(f'获取room_id对应uid信息失败！错误信息：{e}')
            return 0

    async def async_solve_data_from_server(self, server_response: list[dict]):
        for da in server_response:
            _id = da['id']
            if _id != 999999999999:
                db_data = await self.sq.get_server_data_by_id(_id)
                if db_data:
                    # live_monitor_log.debug(f'已存在id:{id}\n{db_data.__dict__}')
                    if _id in self.recorded_server_data_id_list:
                        continue
                    if _id in self.recorded_anchor_server_data_id_list or _id in self.recorded_red_pocket_id_list:
                        continue  # 已存在则跳过
                else:
                    sd = ServerData(
                        id=da.get('id'),
                        created_at=tool.Tool.str_2_DateTime(da.get('created_at'), '%Y-%m-%dT%H:%M:%S', 8),
                        data=da.get('data'),
                        ip=da.get('ip'),
                        room_id=da.get('room_id'),
                        updated_at=tool.Tool.str_2_DateTime(da.get('updated_at'), '%Y-%m-%dT%H:%M:%S', 8)
                    )
                    await self.sq.add_server_data(sd)
            if _id not in self.recorded_server_data_id_list:
                self.recorded_server_data_id_list.append(_id)
                self.recorded_server_data_id_list = self.recorded_server_data_id_list[-1000:]
            task = asyncio.create_task(self.async_solve_server_data(da))
            task.add_done_callback(lambda t: self.task_set.remove(t))
            self.task_set.add(task)

    @async_pushme_try_catch_decorator
    async def async_main(self, ShowLog=True):
        live_monitor_logger.info('启动监控直播抽奖程序！！！')
        await self.async_check_data_from_server()

    async def async_check_data_from_server(self):
        self.init_background_task()
        while 1:
            try:
                server_response: list[dict] = await AsyncTool.get_data_from_server()
                # try:
                task = asyncio.create_task(self.async_solve_data_from_server(server_response))
                task.add_done_callback(lambda t: self.task_set.remove(t))
                self.task_set.add(task)

            except Exception as e:
                live_monitor_logger.error(f'获取服务器数据失败！{e}')
            finally:
                await asyncio.sleep(self.check_data_from_server_time)


bili_live_async_monitor = AsyncMonitor()

if __name__ == '__main__':
    async def _test():
        _m = AsyncMonitor()

        await _m.async_main()


    async def _test_sql():
        assq = AsyncSqlHelper()
        print(1)
        result = await assq.get_room_uid_by_room_id(1017)
        print(result)


    asyncio.run(_test())
