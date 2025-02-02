import asyncio

from fastapi接口.service.MQ.base.MQClient.BiliLotDataMQ import OfficialReserveChargeLotMQ, \
    UpsertOfficialReserveChargeLotMQ, UpsertLotDataByDynamicIdMQ, UpsertTopicLotMQ


def run_mq_consumer():
    tasks = [
        asyncio.create_task(OfficialReserveChargeLotMQ.create_consumer()),
        asyncio.create_task(UpsertOfficialReserveChargeLotMQ.create_consumer()),
        asyncio.create_task(UpsertLotDataByDynamicIdMQ.create_consumer()),
        asyncio.create_task(UpsertTopicLotMQ.create_consumer()),
    ]
    # 等待所有任务完成
    return tasks


async def _test():
    await asyncio.gather(*run_mq_consumer())


if __name__ == '__main__':
    asyncio.new_event_loop()
    asyncio.run(_test(), debug=True)
