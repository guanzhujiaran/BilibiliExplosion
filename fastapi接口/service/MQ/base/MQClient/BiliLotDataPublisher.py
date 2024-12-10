import asyncio
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq
from fastapi接口.service.MQ.base.BasicAsyncClient import _mq_retry_wrapper
from fastapi接口.service.MQ.base.MQClient.BiliLotDataMQ import OfficialReserveChargeLotMQ, \
    UpsertOfficialReserveChargeLotMQ, UpsertLotDataByDynamicIdMQ


class BiliLotDataPublisher:
    @staticmethod
    @_mq_retry_wrapper
    async def pub_official_reserve_charge_lot(
            business_type: int | str,
            business_id: int | str,
            origin_dynamic_id: int | str,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        return await asyncio.to_thread(
            OfficialReserveChargeLotMQ.publish_message,
            LotDataReq(
                business_type=business_type,
                business_id=business_id,
                origin_dynamic_id=origin_dynamic_id,
                **kwargs
            ),
            extra_routing_key=extra_routing_key,
        )

    @staticmethod
    @_mq_retry_wrapper
    async def pub_upsert_official_reserve_charge_lot(
            da: dict,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        return await asyncio.to_thread(UpsertOfficialReserveChargeLotMQ.publish_message, da, extra_routing_key)

    @staticmethod
    @_mq_retry_wrapper
    async def pub_upsert_lot_data_by_dynamic_id(
            dynamic_id: int | str,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        da = LotDataDynamicReq(dynamic_id=dynamic_id, **kwargs)
        return await asyncio.to_thread(UpsertLotDataByDynamicIdMQ.publish_message, da, extra_routing_key)


async def _test(dynamic_id_list):
    return await asyncio.gather(
        *[BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id(dynamic_id, extra_routing_key='_test') for dynamic_id in
          dynamic_id_list])

async def _test_pub_official_reserve_charge_lot():
    return await BiliLotDataPublisher.pub_official_reserve_charge_lot(
        business_type=1,
        business_id=994361504012697606,
        origin_dynamic_id=994361504012697606,
        extra_routing_key='mannual_publish'
    )
if __name__ == "__main__":
    asyncio.new_event_loop()
    asyncio.run(_test_pub_official_reserve_charge_lot())
