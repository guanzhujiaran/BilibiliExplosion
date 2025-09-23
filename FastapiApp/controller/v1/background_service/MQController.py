from typing import Dict
from faststream.rabbit.fastapi import RabbitMessage
from Service.MQ.base.MQClient.base import BaseFastStreamMQ
from log.base_log import MQ_logger
from Models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from Service.MQ.base.MQClient.BiliLotDataFastStream import official_reserve_charge_lot, \
    upsert_official_reserve_charge_lot, upsert_lot_data_by_dynamic_id, upsert_topic_lot, router, \
    upsert_milvus_bili_lot_data, bili_voucher, upsert_bili_atari
from Service.GrpcModule.Models.RabbitmqModel import VoucherInfo


def gen_sub_params(mq_client: BaseFastStreamMQ):
    return {
        "queue": mq_client.mq_props.rabbit_queue,
        "exchange": mq_client.mq_props.exchange,
        "retry": True,
        "no_ack": True
    }


@router.subscriber(
    **gen_sub_params(official_reserve_charge_lot)
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


@router.subscriber(
    **gen_sub_params(upsert_official_reserve_charge_lot)
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


@router.subscriber(
    **gen_sub_params(upsert_lot_data_by_dynamic_id)
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


@router.subscriber(
    **gen_sub_params(upsert_topic_lot)
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


@router.subscriber(
    **gen_sub_params(upsert_milvus_bili_lot_data)
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


@router.subscriber(
    **gen_sub_params(upsert_bili_atari)
)
async def handle_upsert_bili_atari(
        body: int,
        msg: RabbitMessage,
):
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await upsert_bili_atari.consume(
        body,
        msg,
    )


@router.subscriber(
    **gen_sub_params(bili_voucher)
)
async def handle_bili_voucher(
        body: VoucherInfo,
        msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f'【{msg.raw_message.routing_key}】队列 消费消息：{body}')
    await bili_voucher.consume(
        body,
        msg,
    )
