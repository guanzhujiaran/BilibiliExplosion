
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.MQClient.BiliLotDataFastStream import official_reserve_charge_lot, \
    upsert_official_reserve_charge_lot, upsert_lot_data_by_dynamic_id, upsert_topic_lot, router, exch
from faststream.rabbit.fastapi import RabbitMessage



@router.subscriber(queue=official_reserve_charge_lot.queue, exchange=exch, retry=True)
async def handle_official_reserve_charge_lot(
        body: LotDataReq,
        msg: RabbitMessage,
) -> None:
    await official_reserve_charge_lot.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_official_reserve_charge_lot.queue, exchange=exch, retry=True)
async def handle_upsert_official_reserve_charge_lot(
        newly_lot_data: dict,
        msg: RabbitMessage,
) -> None:
    await upsert_official_reserve_charge_lot.consume(
        newly_lot_data,
        msg,
    )


@router.subscriber(queue=upsert_lot_data_by_dynamic_id.queue, exchange=exch, retry=True)
async def handle_upsert_lot_data_by_dynamic_id(
        lot_data_dynamic_req: LotDataDynamicReq,
        msg: RabbitMessage,
) -> None:
    await upsert_lot_data_by_dynamic_id.consume(
        lot_data_dynamic_req,
        msg,
    )


@router.subscriber(queue=upsert_topic_lot.queue, exchange=exch, retry=True)
async def handle_upsert_topic_lot(
        body: TopicLotData,
        msg: RabbitMessage,
) -> None:
    await upsert_topic_lot.consume(
        body,
        msg,
    )
