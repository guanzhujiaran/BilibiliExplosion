import asyncio
import time
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi接口.log.base_log import get_rm_following_list_logger
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus, WorkerModel
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from fastapi接口.utils.dynamic_id_caculate import dynamic_id_2_ts
from fastapi接口.service.get_others_lot_dyn.Sql.models import TLotmaininfo
from fastapi接口.service.get_others_lot_dyn.Sql.sql_helper import SqlHelper
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import BiliSpaceUserItem, HighlightWordList
from fastapi接口.utils.Common import asyncio_gather

running_uids = set()


class GetRmFollowingListV2(UnlimitedCrawler[int]):
    def __init__(self):
        self.status = StatsPlugin(self)
        super().__init__(
            max_sem=500,
            _logger=get_rm_following_list_logger,
            plugins=[
                self.status
            ]
        )
        self.following_params_queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.check_up_sep_days = 7  # 每个uid的检查间隔
        self.round_id = 1
        self.max_gap_time = 86400 * 60  # 取关多少天未发抽奖动态的up主
        self._is_use_available_proxy = False

    async def is_stop(self) -> bool:
        pass

    async def key_params_gen(self, params: int) -> AsyncGenerator[int, None]:
        while 1:  # 这里的循环必须一致执行,不然提前结束就无法获取了
            uid = await self.following_params_queue.get()
            yield uid

    async def handle_fetch(self, params: int) -> WorkerStatus | Any:
        return await self.fetch_uid_space_dyn(params)

    async def fetch_uid_space_dyn(self, uid: int) -> WorkerStatus | Any:
        uid_space_update_time = await SqlHelper.get_lot_user_info_updatetime_by_uid(uid)
        if uid_space_update_time and (datetime.now() - uid_space_update_time).days < self.check_up_sep_days:
            return WorkerStatus.complete
        bsu = BiliSpaceUserItem(
            lot_round_id=self.round_id,
            uid=uid,
            is_use_available_proxy=self._is_use_available_proxy
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
        return WorkerStatus.complete

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

    async def on_worker_end(self, worker_model: WorkerModel):
        running_uids.discard(worker_model.params)
        await super().on_worker_end(worker_model)

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

    async def add_following_params(self, following_list: list[int]):
        async with self._lock:
            for uid in following_list:
                if uid in running_uids:
                    continue
                running_uids.add(uid)
                await self.following_params_queue.put(uid)

    async def main(self, following_list: list[int] = None, *args, **kwargs):
        async with self._lock:
            if self.status.is_running:
                return
        if following_list is None:
            following_list = []
        if type(following_list) is not list:
            return
        self.round_id = await self._get_round_id()
        await self.run(0)

    async def get_rm_following_list(self, following_list: list[int | str]):
        following_list = [int(x) for x in following_list]
        await self.add_following_params(following_list)
        following_set = set(following_list)
        while following_set & running_uids:
            await asyncio.sleep(1)
        result = [x for x in following_list if not await self.check_lot_up_from_database(x)]
        self.log.critical(f'需要取关up主:{result}')
        return result


gmflv2 = GetRmFollowingListV2()

if __name__ == '__main__':
    async def _mock_request():
        result = await gmflv2.get_rm_following_list([1])
        print(result)
        result = await gmflv2.get_rm_following_list([1])
        print(result)


    async def _test():
        task1 = asyncio.create_task(gmflv2.main([]))
        task2 = _mock_request()
        await asyncio.gather(task1, task2)


    asyncio.run(_test())
