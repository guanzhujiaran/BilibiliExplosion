import time
from typing import Any, AsyncGenerator

from fastapi接口.log.base_log import live_monitor_logger
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import ParamsType, WorkerStatus
from fastapi接口.service.grpc_module.grpc.bapi import biliapi


class BiliLiveCrawler(UnlimitedCrawler[int]):
    async def is_stop(self) -> bool:
        return False

    async def key_params_gen(self, params: ParamsType) -> AsyncGenerator[ParamsType, None]:
        #TODO 这里维护一个列表，根据时间返回房间号，
        sync_live_area_ts = 0
        while 1:
            if int(time.time()) - sync_live_area_ts > 24 * 60 * 60:
                live_area_list_resp = await biliapi.xlive_web_interface_v1_index_getWebAreaList(use_custom_proxy=True)
                self.live_area_list = live_area_list_resp.get('data', {}).get('data', [])
                sync_live_area_ts = int(time.time())



    async def handle_fetch(self, params: ParamsType) -> WorkerStatus | Any:
        pass

    def __init__(self):
        super().__init__(
            _logger=live_monitor_logger
        )
        self.live_area_list = []

    async def main(self):
        ...
