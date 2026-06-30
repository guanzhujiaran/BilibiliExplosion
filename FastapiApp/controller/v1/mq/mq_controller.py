from ApiRoutes import RouterPaths, RouterTags
from datetime import datetime
import time
from typing import Dict
from faststream.rabbit.fastapi import RabbitMessage
from Models.MQ.MQRouterModels import (
    LotDataReq,
    LotDataDynamicReq,
    TopicLotData,
    VoucherInfo,
    RabbitMQTestMsgModel,
)
from log.base_log import MQ_logger
from Service.MQ.base.MQClient.BiliLotDataFastStream import (
    official_reserve_charge_lot,
    upsert_official_reserve_charge_lot,
    upsert_lot_data_by_dynamic_id,
    upsert_topic_lot,
    router,
    upsert_milvus_bili_lot_data,
    bili_voucher,
    upsert_bili_atari,
    rabbit_mq_test,
)


@router.subscriber(**official_reserve_charge_lot.sub_params)
async def handle_official_reserve_charge_lot(
    body: LotDataReq,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{body}")
    await official_reserve_charge_lot.consume(
        body,
        msg,
    )


@router.subscriber(**upsert_official_reserve_charge_lot.sub_params)
async def handle_upsert_official_reserve_charge_lot(
    newly_lot_data: dict,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{newly_lot_data}")
    await upsert_official_reserve_charge_lot.consume(
        newly_lot_data,
        msg,
    )


@router.subscriber(**upsert_lot_data_by_dynamic_id.sub_params)
async def handle_upsert_lot_data_by_dynamic_id(
    lot_data_dynamic_req: LotDataDynamicReq,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(
        f"【{msg.raw_message.routing_key}】队列 消费消息：{lot_data_dynamic_req}"
    )
    await upsert_lot_data_by_dynamic_id.consume(
        lot_data_dynamic_req,
        msg,
    )


@router.subscriber(**upsert_topic_lot.sub_params)
async def handle_upsert_topic_lot(
    body: TopicLotData,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{TopicLotData}")
    await upsert_topic_lot.consume(
        body,
        msg,
    )


@router.subscriber(**upsert_milvus_bili_lot_data.sub_params)
async def handle_upsert_milvus_bili_lot_data(
    body: dict | Dict,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{body}")
    await upsert_milvus_bili_lot_data.consume(
        body,
        msg,
    )


@router.subscriber(**upsert_bili_atari.sub_params)
async def handle_upsert_bili_atari(
    body: int,
    msg: RabbitMessage,
):
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{body}")
    await upsert_bili_atari.consume(
        body,
        msg,
    )


@router.subscriber(**bili_voucher.sub_params)
async def handle_bili_voucher(
    body: VoucherInfo,
    msg: RabbitMessage,
) -> None:
    MQ_logger.debug(f"【{msg.raw_message.routing_key}】队列 消费消息：{body}")
    await bili_voucher.consume(
        body,
        msg,
    )


@router.subscriber(**rabbit_mq_test.sub_params)
async def _test_msg_consumer(data: RabbitMQTestMsgModel, msg: RabbitMessage):
    MQ_logger.critical(f"【{msg.raw_message.routing_key}】队列 消费消息：{data}")
    return await rabbit_mq_test.consume(data, msg)


@router.publisher(**rabbit_mq_test.pub_params)
@router.post(RouterPaths.RABBITMQ_TEST_PUBLISH, tags=[RouterTags.MQ_TEST])
async def _test_msg_pub(
    msg: str = f"Ciallo～(∠・ω< )⌒★ 起床时间【{datetime.now()}】喵~",
) -> RabbitMQTestMsgModel:
    ret = f"publish `{msg}` to rabbitmq test!"
    MQ_logger.critical(ret)
    return RabbitMQTestMsgModel(a=int(time.time()), b=ret, c={1: ret}, d=[ret])


# 导入 lottery_data 模块以触发 @rpc_subscriber 装饰器注册 RPC handler
# 必须放在所有 @router.subscriber 注册之后，确保 broker 已就绪
from controller.v1.mq import lottery_data  # noqa: F401, E402

__all__ = ["router"]
