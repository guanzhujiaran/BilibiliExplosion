import asyncio
import time
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi接口.log.base_log import get_rm_following_list_logger
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus, WorkerModel
from fastapi接口.service.common_utils.dynamic_id_caculate import dynamic_id_2_ts
from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotmaininfo
from fastapi接口.service.get_others_lot_dyn.Sql.sql_helper import SqlHelper
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import BiliSpaceUserItem, HighlightWordList
from fastapi接口.utils.Common import asyncio_gather

running_uids = set()


class GetRmFollowingListV2(UnlimitedCrawler[int]):
    def __init__(self):
        super().__init__(
            max_sem=10,
            _logger=get_rm_following_list_logger
        )
        self.following_list = []
        self.running_uids = running_uids
        self._lock = asyncio.Lock()
        self.check_up_sep_days = 7  # 每个uid的检查间隔
        self.round_id = 1
        self.max_gap_time = 86400 * 60  # 取关多少天未发抽奖动态的up主
        self.is_use_available_proxy = False

    async def is_stop(self) -> bool:
        pass

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        for uid in self.following_list:
            yield uid

    async def handle_fetch(self, params: int) -> WorkerStatus | Any:
        if params in self.running_uids:
            async with self._lock:
                while params in self.running_uids:
                    await asyncio.sleep(10)
        self.running_uids.add(params)
        return await self.fetch_uid_space_dyn(params)

    async def fetch_uid_space_dyn(self, uid: int) -> WorkerStatus | Any:
        uid_space_update_time = await SqlHelper.get_lot_user_info_updatetime_by_uid(uid)
        if uid_space_update_time and (datetime.now() - uid_space_update_time).days < self.check_up_sep_days:
            return
        bsu = BiliSpaceUserItem(
            lot_round_id=self.round_id,
            uid=uid,
            is_use_available_proxy=self.is_use_available_proxy
        )
        await bsu.get_user_space_dynamic_id(
            secondRound=True,
            isPubLotUser=True,  # 需要检查这个uid发布的动态，不光是转发的动态
            isPreviousRoundFinished=True,
            SpareTime=7 * 86400,
        )
        dyn_set = set(bsu.dynamic_infos)
        await asyncio_gather(
            *[x.judge_lottery(highlight_word_list=HighlightWordList, lotRound_id=self.round_id) for x in dyn_set])

    async def on_worker_end(self, worker_model: WorkerModel):
        self.running_uids.discard(worker_model.params)

    async def _get_round_id(self) -> int:
        round_info = await SqlHelper.getLatestFinishedRound()
        if not round_info:
            latest_round = TLotmaininfo(
                lotRound_id=1,
                allNum=0,
                lotNum=0,
                uselessNum=0,
                isRoundFinished=False,
            )
            await SqlHelper.addLotMainInfo(latest_round)
            return 1
        return round_info.lotRound_id

    async def check_lot_up_from_database(self, uid) -> bool:
        """
        返回bool值，true表示这个uid是发起抽奖的up
        """
        latest_lot_dyn = await SqlHelper.getLatestLotDynInfoByUid(uid)
        if latest_lot_dyn:
            if int(time.time()) - dynamic_id_2_ts(latest_lot_dyn.dynId) >= self.max_gap_time:
                return False
            return True
        return False

    async def main(self, following_list: list[int], *args, **kwargs) -> list[int]:
        if type(following_list) is not list:
            return []
        self.following_list = following_list
        self.round_id = await self._get_round_id()
        await self.run(0)
        result = [x for x in following_list if not await self.check_lot_up_from_database(x)]
        self.log.debug(result)
        return result


if __name__ == '__main__':
    a = GetRmFollowingListV2()
    asyncio.run(a.main([532791]))
