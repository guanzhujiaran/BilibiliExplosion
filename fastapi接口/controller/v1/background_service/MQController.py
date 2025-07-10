from typing import Dict
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.MQClient.BiliLotDataFastStream import official_reserve_charge_lot, \
    upsert_official_reserve_charge_lot, upsert_lot_data_by_dynamic_id, upsert_topic_lot, router, \
    upsert_milvus_bili_lot_data, bili_voucher
from faststream.rabbit.fastapi import RabbitMessage

from fastapi接口.service.grpc_module.Models.RabbitmqModel import VoucherInfo


@router.subscriber(
    queue=official_reserve_charge_lot.mq_props.rabbit_queue,
    exchange=official_reserve_charge_lot.mq_props.exchange,
    retry=True,
)
async def handle_official_reserve_charge_lot(
        body: LotDataReq,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await official_reserve_charge_lot.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_official_reserve_charge_lot.mq_props.rabbit_queue,
                   exchange=upsert_official_reserve_charge_lot.mq_props.exchange,
                   retry=True,
                   )
async def handle_upsert_official_reserve_charge_lot(
        newly_lot_data: Dict,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{newly_lot_data}')
    await upsert_official_reserve_charge_lot.consume(
        newly_lot_data,
        msg,
    )


@router.subscriber(queue=upsert_lot_data_by_dynamic_id.mq_props.rabbit_queue,
                   exchange=upsert_lot_data_by_dynamic_id.mq_props.exchange,
                   retry=True,
                   )
async def handle_upsert_lot_data_by_dynamic_id(
        lot_data_dynamic_req: LotDataDynamicReq,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{lot_data_dynamic_req}')
    await upsert_lot_data_by_dynamic_id.consume(
        lot_data_dynamic_req,
        msg,
    )


@router.subscriber(queue=upsert_topic_lot.mq_props.rabbit_queue,
                   exchange=upsert_topic_lot.mq_props.exchange,
                   retry=True,
                   )
async def handle_upsert_topic_lot(
        body: TopicLotData,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{TopicLotData}')
    await upsert_topic_lot.consume(
        body,
        msg,
    )


@router.subscriber(queue=upsert_milvus_bili_lot_data.mq_props.rabbit_queue,
                   exchange=upsert_milvus_bili_lot_data.mq_props.exchange,
                   retry=True,
                   )
async def handle_upsert_milvus_bili_lot_data(
        body: Dict,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await upsert_milvus_bili_lot_data.consume(
        body,
        msg,
    )

@router.subscriber(queue=bili_voucher.mq_props.rabbit_queue,
                   exchange=bili_voucher.mq_props.exchange,
                   retry=True,
                   )
async def handle_bili_voucher(
        body:VoucherInfo,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await bili_voucher.consume(
        body,
        msg,
    )

