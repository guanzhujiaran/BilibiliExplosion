import asyncio
from typing import Dict
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.MQClient.BiliLotDataFastStream import official_reserve_charge_lot, \
    upsert_official_reserve_charge_lot, upsert_lot_data_by_dynamic_id, upsert_topic_lot, router, exch, \
    upsert_milvus_bili_lot_data, upsert_proxy_info, proxy_exch
from faststream.rabbit.fastapi import RabbitMessage

@router.subscriber(queue=official_reserve_charge_lot.queue, exchange=exch, retry=True)
async def handle_official_reserve_charge_lot(
        body: LotDataReq,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await official_reserve_charge_lot.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_official_reserve_charge_lot.queue, exchange=exch, retry=True)
async def handle_upsert_official_reserve_charge_lot(
        newly_lot_data: Dict,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{newly_lot_data}')
    await upsert_official_reserve_charge_lot.consume(
        newly_lot_data,
        msg,
    )


@router.subscriber(queue=upsert_lot_data_by_dynamic_id.queue, exchange=exch, retry=True)
async def handle_upsert_lot_data_by_dynamic_id(
        lot_data_dynamic_req: LotDataDynamicReq,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{lot_data_dynamic_req}')
    await upsert_lot_data_by_dynamic_id.consume(
        lot_data_dynamic_req,
        msg,
    )


@router.subscriber(queue=upsert_topic_lot.queue, exchange=exch, retry=True)
async def handle_upsert_topic_lot(
        body: TopicLotData,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{TopicLotData}')
    await upsert_topic_lot.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_milvus_bili_lot_data.queue, exchange=exch, retry=True)
async def handle_upsert_milvus_bili_lot_data(
        body: Dict,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await upsert_milvus_bili_lot_data.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_proxy_info.queue, exchange=proxy_exch, retry=True)
async def handle_upsert_proxy_info(
        body: Dict,
        msg: RabbitMessage,
) -> None:
    await upsert_proxy_info.consume(
        body,
        msg
    )


if __name__ == "__main__":
    import fastapi

    app = fastapi.FastAPI()
    app.include_router(router)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
