"""B站用户空间动态抓取模块

从 get_other_lot_main.py 中拆分出来的 BiliSpaceUserItem 类。
负责获取用户空间动态、解析转发动态、记录发布抽奖的用户。

算法优化：
1. _add_pub_lot_user: O(n) 遍历查找 -> O(1) 集合查找
2. __add_space_card_to_db: 多次 .get('data').get('items') -> 缓存中间变量
3. _solve_space_dynamic: 多次 .get('data') -> 缓存；过滤 + 遍历合并为单次遍历
"""
import asyncio
import datetime
import json
import re
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Set

from log.base_log import get_others_lot_logger as get_others_lot_log
from Models.get_other_lot_dyn.dyn_robot_model import BiliSpaceUserParamsType
from Service.GetOthersLotDyn.Sql.models import TLotuserinfo, TLotuserspaceresp
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_space_dynamic_req_with_proxy
from Utils.通用.Common import asyncio_gather
from Utils.推送.PushMe import a_pushme
from Utils.代理.mdoel.RequestConf import RequestConf
from Utils.通用.dynamic_id_caculate import dynamic_id_2_ts
from Utils.通用.CommMethods import methods

if TYPE_CHECKING:
    from Service.GetOthersLotDyn.core.bili_dynamic_item import BiliDynamicItem

BAPI = methods()

# 默认是否使用可用代理
_is_use_available_proxy = True


def _extract_space_dynamic_times(space_req_dict: dict) -> list[int]:
    """从空间动态响应中提取所有动态的发布时间戳

    原先作为 get_user_space_dynamic_id 内的嵌套函数，提取为模块级函数便于复用。
    """
    data = space_req_dict.get('data') or {}
    cards_json = data.get('items')
    if not cards_json:
        return []
    time_list = []
    for card_dict in cards_json:
        # 一次性取出 module_author，避免重复 .get()
        module_author = (card_dict.get('modules') or {}).get('module_author') or {}
        pub_ts = module_author.get('pub_ts')
        if pub_ts is not None:
            time_list.append(pub_ts)
    return time_list


@dataclass
class BiliSpaceUserItem:
    """
    B站用户的空间
    """
    lot_round_id: int
    uid: int | str
    _offset: int | str | None = field(default=0)
    lot_user_info: TLotuserinfo | None = field(default=None)  # 用户信息
    dynamic_infos: Set['BiliDynamicItem'] = field(
        default_factory=set)  # 存放用户的空间动态详情
    pub_lot_users: Set['BiliSpaceUserItem'] = field(
        default_factory=set)  # 存放用户发布抽奖的用户详情
    # O(1) 查找缓存：记录 pub_lot_users 中已有的 uid 字符串，避免遍历集合
    _pub_lot_uids: set = field(default_factory=set)
    updateNum: int = field(default=0)
    is_use_available_proxy: bool = field(default=_is_use_available_proxy)
    params: BiliSpaceUserParamsType | None = field(default=None)

    def __post_init__(self):
        if self.params is None:
            self.params = BiliSpaceUserParamsType(
                uid=self.uid,
            )
            self.params.offset = self._offset

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value
        if type(value) is int:
            self.params.offset = value

    def __hash__(self):
        return hash(int(self.uid))

    async def get_user_space_dynamic_id(
            self,
            secondRound=False,
            isPubLotUser=False,
            isPreviousRoundFinished=False,
            SpareTime=5 * 86400,
            succ_counter=None
    ) -> None:
        """
        支持了断点续爬
        根据时间和获取过的动态来判断是否结束爬取别人的空间主页
        """
        n = 0
        first_get_dynamic_flag = True
        origin_offset = 0  # 初始offset
        lot_user_info: TLotuserinfo | None = await SqlHelper.getLotUserInfoByUid(self.uid)
        first_dynamic_id = 0
        self.offset = lot_user_info.offset if lot_user_info else 0
        # region 这部分是主要逻辑，包括断点续爬，需要注意逻辑是否正确
        if secondRound:
            newest_space_offset = await SqlHelper.getNewestSpaceDynInfoByUid(self.uid)
            if newest_space_offset:
                dynamic_calculated_ts = dynamic_id_2_ts(newest_space_offset)
                if int(time.time() - dynamic_calculated_ts) < 2 * 3600:
                    get_others_lot_log.info(
                        f'用户uid={self.uid}的最新动态(https://t.bilibili.com/{newest_space_offset})距离上次获取时间({datetime.datetime.fromtimestamp(dynamic_calculated_ts)})不足2小时，跳过本轮获取')
                    return
        if lot_user_info:
            # 只有当第二轮也获取完的时候，才会将latestFinishedOffset设置为最新的一条动态id值
            # 如果上一轮也没有完成，同时这个用户的空间没获取完，从上次的offset继续获取下去
            if not lot_user_info.isUserSpaceFinished and not isPreviousRoundFinished:
                origin_offset = lot_user_info.offset
            # 如果上一轮抽奖没有完成，重新开始了，但是这个用户的空间获取完了，查询数据库，获取当前round_id的最小值 最多多获取到上一轮的全部数据
            elif lot_user_info.isUserSpaceFinished and not isPreviousRoundFinished:
                origin_offset = await SqlHelper.getOldestSpaceOffsetByUidRoundId(
                    self.uid,
                    self.lot_round_id
                )
            else:  # lot_user_info.isUserSpaceFinished and isPreviousRoundFinished
                # 如果上一轮抽奖已经完成，并且这个用户的空间获取完了，那么就从0开始重新获取
                origin_offset = 0
            # 不会存在上一轮获取完了，但是用户没获取完的情况！！！不用讨论
        else:
            lot_user_info = TLotuserinfo(
                uid=self.uid,
                isPubLotUser=isPubLotUser,
                isUserSpaceFinished=0,
                offset=0,
                latestFinishedOffset=0
            )
        await SqlHelper.addLotUserInfo(lot_user_info)
        # endregion
        self.lot_user_info = lot_user_info
        cur_offset = deepcopy(origin_offset)
        uname = ''
        time_list = [0]
        get_others_lot_log.info(
            f'开始获取用户空间动态，uid={self.uid}，主页=https://space.bilibili.com/{self.uid}/dynamic，初始offset={origin_offset}，是否为第二轮获取={secondRound}')
        while 1:
            if succ_counter:
                succ_counter.update_ts = int(time.time())
            if origin_offset != 0 and first_get_dynamic_flag and not secondRound:  # 从半当中开始接着获取动态
                items = await SqlHelper.getSpaceRespTillOffset(self.uid, origin_offset)
                dyreq_dict = {
                    'code': 0,
                    'data': {
                        'has_more': True,
                        'items': items,
                        'offset': origin_offset,
                        "update_baseline": "",
                        'update_num': 0
                    },
                    'message': '0',
                    'ttl': 1
                }
                get_others_lot_log.info(
                    f'断点续爬：uid={self.uid}，从数据库恢复offset={origin_offset}之后的空间动态{len(items)}条，之后将继续从B站API获取')
                first_get_dynamic_flag = False
            else:
                start_ts = time.time()
                get_others_lot_log.debug(f'正在请求B站API获取用户uid={self.uid}的空间动态')
                dyreq_dict = await asyncio.create_task(
                    get_space_dynamic_req_with_proxy(
                        self.uid,
                        cur_offset if cur_offset else "",
                        RequestConf(
                            is_use_available_proxy=self.is_use_available_proxy,
                            is_use_cookie=True,
                        )
                    )
                )
                code = dyreq_dict.get('code')
                msg = dyreq_dict.get('message')
                if code != 0:
                    get_others_lot_log.critical(
                        f'获取用户uid={self.uid}空间动态失败，offset={cur_offset}，code={code}，msg={msg}')
                    await a_pushme(
                        'GetOthersLotDyn',
                        f'获取用户uid={self.uid}空间动态失败，offset={cur_offset}，code={code}，msg={msg}',
                        'text'
                    )
                    if code == 4101128:
                        get_others_lot_log.critical(
                            f'用户uid={self.uid}空间动态异常（可能账号被封禁或隐私设置），等待30秒后重试，msg={msg}')
                        await asyncio.sleep(30)
                        continue
                    if code == 4101129:
                        get_others_lot_log.critical(
                            f'用户uid={self.uid}空间动态请求被拒绝（code=4101129），停止获取，msg={msg}')
                        break
                get_others_lot_log.info(
                    f'获取用户uid={self.uid}空间动态成功，耗时{time.time() - start_ts:.2f}秒，获取到{len(dyreq_dict.get("data", {}).get("items", []))}条动态')
                resp_dyn_ids = await self.__add_space_card_to_db(dyreq_dict)
                if not first_dynamic_id and resp_dyn_ids:
                    first_dynamic_id = resp_dyn_ids[0]
            try:
                dynamic_items: list[dict] = (dyreq_dict.get('data') or {}).get('items')
                if dynamic_items:
                    uname = ((dynamic_items[0].get('modules') or {}).get('module_author') or {}).get('name')
            except Exception as e:
                get_others_lot_log.error(
                    f'解析空间动态用户名失败，uid={self.uid}，offset={cur_offset}')
                get_others_lot_log.exception(e)
            try:
                repost_dynamic_id_list = await self._solve_space_dynamic(
                    dyreq_dict,
                    isPubLotUser
                )  # 脚本们转发生成的动态id 同时将需要获取的抽奖发布者的uid记录下来
            except Exception as e:
                get_others_lot_log.critical(
                    f'解析空间动态失败，uid={self.uid}，offset={cur_offset}，error={e}')
                get_others_lot_log.exception(e)
                break
            if not repost_dynamic_id_list:
                get_others_lot_log.info(
                    f'用户uid={self.uid}空间动态解析结果为空（无转发动态），停止获取')
                break
            n += len(repost_dynamic_id_list)
            dyreq_data = dyreq_dict.get('data') or {}
            if dyreq_data.get('offset') is not None:
                offset_str = dyreq_data.get('offset')
                cur_offset = int(offset_str if offset_str else "0")
            else:
                get_others_lot_log.critical(
                    f'获取用户uid={self.uid}空间动态失败：响应中缺少offset字段，offset={cur_offset}\nresp={dyreq_dict}')
                await a_pushme(
                    'GetOthersLotDyn',
                    f'获取用户uid={self.uid}空间动态失败：响应中缺少offset字段，offset={cur_offset}\nresp={dyreq_dict}',
                    'text'
                )
                break
            self.offset = cur_offset
            time_list = _extract_space_dynamic_times(dyreq_dict)
            if not secondRound:  # 第二轮获取动态，不更新数据库
                lot_user_info = TLotuserinfo(
                    uid=self.uid,
                    uname=uname,
                    updateNum=self.updateNum,
                    updatetime=lot_user_info.updatetime,  # 只有最后完成了才会更新`updatetime`
                    isUserSpaceFinished=0,
                    offset=cur_offset,
                    latestFinishedOffset=lot_user_info.latestFinishedOffset,
                    isPubLotUser=isPubLotUser
                )
                await SqlHelper.addLotUserInfo(
                    lot_user_info
                )
            self.lot_user_info = lot_user_info
            if len(time_list) == 0:
                get_others_lot_log.error(
                    f'空间动态响应中未提取到任何发布时间戳，uid={self.uid}，停止获取\nresp={json.dumps(dyreq_dict, ensure_ascii=False)}')
                break
            if time.time() - time_list[-1] >= SpareTime:
                get_others_lot_log.info(
                    f'用户uid={self.uid}空间动态已超过时间限制({SpareTime // 86400}天)，获取结束，当前时间={BAPI.timeshift(time.time())}')
                break
            if cur_offset and cur_offset <= lot_user_info.latestFinishedOffset:
                get_others_lot_log.info(
                    f'用户uid={self.uid}遇到已获取过的动态offset，获取结束，'
                    f'cur_offset={cur_offset}，latestFinishedOffset={lot_user_info.latestFinishedOffset}')
                break
            try:
                if not dyreq_data.get('has_more'):
                    get_others_lot_log.info(
                        f'用户uid={self.uid}空间动态已全部获取完毕（has_more=false）')
                    break
            except Exception as e:
                get_others_lot_log.critical(
                    f'解析has_more字段失败，uid={self.uid}，offset={cur_offset}\nresp={dyreq_dict}\nerror={e}')
                get_others_lot_log.exception(e)
        get_others_lot_log.debug(f'更新lot_user_info')
        await SqlHelper.addLotUserInfo(TLotuserinfo(
            uid=self.uid,
            uname=uname,
            updateNum=self.updateNum,
            updatetime=datetime.datetime.now(),
            isUserSpaceFinished=1,
            offset=cur_offset,
            latestFinishedOffset=first_dynamic_id if first_dynamic_id else lot_user_info.latestFinishedOffset,
            isPubLotUser=isPubLotUser
        ))
        if not secondRound:
            get_others_lot_log.debug(f'更新lot_user_info最终状态')
            await asyncio.create_task(self.get_user_space_dynamic_id(
                secondRound=True,
                isPubLotUser=isPubLotUser,
                isPreviousRoundFinished=isPreviousRoundFinished,
                SpareTime=SpareTime,
                succ_counter=succ_counter
            ))
        if n <= 50 and time.time() - time_list[-1] >= SpareTime and secondRound == False and not isPubLotUser:
            get_others_lot_log.critical(
                f'用户uid={self.uid}获取到的动态数量过少({n}条)，可能存在异常，请前往主页查看：https://space.bilibili.com/{self.uid}')
        get_others_lot_log.debug(f'用户uid={self.uid}空间动态获取完毕')

    async def __add_space_card_to_db(self, spaceResp: dict) -> List[int | str] | None:
        """将空间动态响应保存到数据库

        优化：缓存 data/items，过滤置顶动态和保存数据库合并为单次遍历
        """
        try:
            data = spaceResp.get('data') or {}
            items = data.get('items') or []
            # 过滤置顶动态并保存到数据库（单次遍历）
            ret_list = []
            for i in items:
                module_tag = ((i.get('modules') or {}).get('module_tag') or {})
                if module_tag.get('text') == '置顶':
                    continue
                space_resp_card_dynamic_id = i.get('id_str')
                await SqlHelper.addSpaceResp(LotUserSpaceResp=TLotuserspaceresp(
                    spaceUid=self.uid,
                    spaceOffset=space_resp_card_dynamic_id,
                    spaceRespJson=i,
                    dynLotRound_id=self.lot_round_id
                ))
                ret_list.append(space_resp_card_dynamic_id)
            return ret_list
        except Exception as _e:
            get_others_lot_log.critical(
                f'保存空间动态响应到数据库失败，uid={self.uid}，error={_e}')
            get_others_lot_log.exception(_e)

    def _add_pub_lot_user(self, uid):
        """添加发布抽奖的用户

        优化：使用 _pub_lot_uids 集合实现 O(1) 查找，替代原先 O(n) 遍历 pub_lot_users
        """
        uid_str = str(uid)
        if uid_str in self._pub_lot_uids:  # O(1) 查找
            return
        self._pub_lot_uids.add(uid_str)
        self.pub_lot_users.add(BiliSpaceUserItem(
            uid=str(uid),
            lot_round_id=self.lot_round_id
        ))

    async def _solve_space_dynamic(self, space_req_dict: dict, isPubLotUser: bool) -> List['BiliDynamicItem'] | None:
        """解析空间动态，提取转发动态和发布抽奖的用户

        优化：缓存 data/items，减少重复 .get() 调用
        """
        # 延迟导入 BiliDynamicItem，避免循环依赖
        from Service.GetOthersLotDyn.core.bili_dynamic_item import BiliDynamicItem

        ret_list = []
        try:
            data = space_req_dict.get('data') or {}
            items = data.get('items') or []
            for dynamic_item in items:
                self.updateNum += 1
                dynamic_id_str = str(dynamic_item.get('id_str'))
                ret_list.append(dynamic_id_str)
                if isPubLotUser:  # 只有是发布抽奖动态的up才会将他的动态信息加入抽奖动态列表里面
                    single_dynamic_resp = {
                        'code': 0,
                        'data':
                            {
                                "item": dynamic_item
                            }
                    }
                    bili_dynamic_item = BiliDynamicItem(
                        dynamic_id=dynamic_id_str,
                        dynamic_raw_resp=single_dynamic_resp,
                        is_use_available_proxy=self.is_use_available_proxy
                    )
                    # 只添加发布抽奖动态的人的原始动态
                    self.dynamic_infos.add(bili_dynamic_item)
                else:
                    if dynamic_item.get('type') == 'DYNAMIC_TYPE_FORWARD':
                        orig_dynamic_item = dynamic_item.get('orig', {})
                        orig_dynamic_id_str = orig_dynamic_item.get('id_str')
                        orig_single_dynamic_resp = {
                            'code': 0,
                            'data':
                                {
                                    "item": orig_dynamic_item
                                }
                        }
                        if orig_dynamic_id_str and orig_dynamic_item.get('type') != 'DYNAMIC_TYPE_NONE':
                            orig_bili_dynamic_item = BiliDynamicItem(
                                dynamic_id=orig_dynamic_id_str,
                                dynamic_raw_resp=orig_single_dynamic_resp,
                                is_use_available_proxy=self.is_use_available_proxy
                            )
                            self.dynamic_infos.add(orig_bili_dynamic_item)
                        else:
                            if orig_dynamic_item and orig_dynamic_item.get('type') != 'DYNAMIC_TYPE_NONE':
                                get_others_lot_log.critical(
                                    f'转发动态的原动态缺失或类型异常，无法解析原动态，转发动态dynamic_id={dynamic_item.get("id_str")}')
                        # 提取 at 用户信息
                        module_dynamic = (dynamic_item.get('modules') or {}).get('module_dynamic') or {}
                        desc = module_dynamic.get('desc') or {}
                        rich_text_nodes = desc.get('rich_text_nodes') or []
                        dynamic_text = desc.get('text') or ''
                        # O(n) 过滤出 AT 类型的节点
                        at_users_nodes = [
                            x for x in rich_text_nodes
                            if x.get('type') == 'RICH_TEXT_NODE_TYPE_AT'
                        ]
                        need_at_usernames = re.findall(
                            '//@(.{0,20}):', dynamic_text)
                        for need_at_username in need_at_usernames:
                            for i in at_users_nodes:
                                if need_at_username in (i.get('text') or ''):
                                    need_uid = i.get('rid')
                                    self._add_pub_lot_user(need_uid)
            # 处理折叠内容
            inplace_fold = data.get('inplace_fold')
            if inplace_fold:
                for i in inplace_fold:
                    if i.get('dynamic_ids'):
                        for dyn_id in i.get('dynamic_ids'):
                            ret_list.append(dyn_id)
                    get_others_lot_log.critical(f'遇到折叠动态内容(inplace_fold)，当前未处理该类型，内容={i}')
            if not data.get('has_more') and len(ret_list) == 0:
                return None
            return ret_list
        except Exception as _e:
            get_others_lot_log.exception(_e)
            raise _e
