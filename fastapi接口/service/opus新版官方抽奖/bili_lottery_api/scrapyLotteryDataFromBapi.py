import asyncio
import time
from typing import AsyncGenerator, Literal, get_type_hints

from fastapi接口.log.base_log import myfastapi_logger
from fastapi接口.models.base.custom_pydantic import CustomBaseModel
from fastapi接口.service.BaseCrawler.CrawlerType import UnlimitedCrawler
from fastapi接口.service.BaseCrawler.model.base import WorkerStatus
from fastapi接口.service.BaseCrawler.plugin.statusPlugin import StatsPlugin
from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.common_utils.dynamic_id_caculate import dynamic_id_2_ts
from fastapi接口.service.grpc_module.grpc.bapi import biliapi
from utl.pushme.pushme import pushme
from utl.redisTool.RedisManager import RedisManagerBase


class BusinessParams(CustomBaseModel):
    business_id: int
    business_type: Literal[2, 10]


BusinessIdType = get_type_hints(BusinessParams)['business_id']
BusinessType = get_type_hints(BusinessParams)['business_type']


class RedisHelper(RedisManagerBase):
    class RedisMap(RedisManagerBase.RedisMap):
        dyn_rid = "LotteryApiRobot:setting:dyn_rid"
        reserve_sid = "LotteryApiRobot:setting:reserve_sid"

    async def get_id(self, _type: RedisMap) -> int:
        if result := await self._get(_type.value):
            return int(result)
        else:
            return 0

    async def set_id(self, _type: RedisMap, value: int):
        await self._set(_type.value, value)


class LotteryApiRobot(UnlimitedCrawler[BusinessParams]):
    async def is_stop(self) -> bool:
        return self._cur_stop_times >= self.__max_stop_times

    async def key_params_gen(self, params: BusinessParams) -> AsyncGenerator[int, None]:
        while 1:
            params = BusinessParams(
                business_type=params.business_type,
                business_id=params.business_id + 1
            )
            yield params

    async def handle_fetch(self, params: BusinessParams) -> WorkerStatus:
        return await self.pipeline(params.business_type, params.business_id)

    def __init__(self, business_type: BusinessType):
        self.__business_type: BusinessType = business_type
        self.default_dyn_rid = 345671305
        self.default_reserve_sid = 4234284
        self.sem_limit = 1
        self.min_reserve_sep_ts = 8 * 3600  # 最小的间隔时间
        self.min_dyn_sep_ts = 12 * 3600
        self.__max_stop_times = 5  # 遇到超过时间的次数
        self.redis_helper = RedisHelper()

        self._cur_stop_times = 0
        self.latest_ts = 0

        self.stats_plugin = StatsPlugin(self)
        super().__init__(
            max_sem=self.sem_limit,
            _logger=myfastapi_logger,
            plugins=[self.stats_plugin],
        )

    async def solve_dyn_data(self, data: dict):
        business_id = data.get('business_id')
        if business_id:
            dynamic_ts = dynamic_id_2_ts(business_id)
            if int(time.time()) - dynamic_ts < self.min_dyn_sep_ts:
                self._cur_stop_times += 1
                self.latest_ts = dynamic_ts
                await self.redis_helper.set_id(self.redis_helper.RedisMap.dyn_rid, business_id)
        else:
            self.log.critical(f'business_id：{data} 获取动态时间失败！')

    async def solve_reserve_data(self, data: dict):
        reserve_sid = data.get('business_id')
        reserve_resp = await biliapi.reserve_relation_info(ids=reserve_sid, use_custom_proxy=True)
        if da := reserve_resp.get('data', {}):
            stime = da.get('list', {}).get(str(reserve_sid), {}).get('stime')
            if isinstance(stime, int):
                if int(time.time()) - stime < self.min_reserve_sep_ts:
                    self._cur_stop_times += 1
                    self.latest_ts = stime
                    await self.redis_helper.set_id(self.redis_helper.RedisMap.reserve_sid, reserve_sid)
            else:
                self.log.critical(f'business_id：{data} 获取预约时间失败：{reserve_resp}')

    async def pipeline(
            self,
            business_type: BusinessType,
            business_id: BusinessIdType
    ) -> WorkerStatus:
        try:
            resp_dict = await biliapi.get_lot_notice(business_type, business_id, use_custom_proxy=True)
            self.log.debug(f'params 【{business_type},{business_id}】\n'
                           f' {resp_dict} \n'
                           f'latest_ts:{self.latest_ts}\n'
                           f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.latest_ts))}')
            if data := resp_dict.get('data'):
                self.log.info(f'params 【{business_type},{business_id}】获取到了data：{data}')
                await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                    da=data,
                    extra_routing_key=self.__class__.__name__
                )
                match business_type:
                    case 2:
                        await self.solve_dyn_data(data)
                    case 10:
                        await self.solve_reserve_data(data)

            return WorkerStatus.complete
        except Exception as e:
            self.log.exception(e)
            raise e

    async def main(self):
        try:
            match self.__business_type:
                case 2:
                    await self.run(BusinessParams(
                        business_type=2,
                        business_id=await self.redis_helper.get_id(
                            self.redis_helper.RedisMap.dyn_rid) or self.default_dyn_rid
                    ))
                case 10:
                    await self.run(BusinessParams(
                        business_type=10,
                        business_id=await self.redis_helper.get_id(
                            self.redis_helper.RedisMap.reserve_sid) or self.default_reserve_sid
                    ))
        except Exception as e:
            self.log.error(f'发生异常！{e}')
            pushme(title=f'爬取B站lottery异常', content=str(e))


lottery_api_robot_dyn = LotteryApiRobot(business_type=2)
lottery_api_robot_reserve = LotteryApiRobot(business_type=10)
if __name__ == '__main__':
    asyncio.run(asyncio.gather(lottery_api_robot_dyn.main(), lottery_api_robot_reserve.main()))
