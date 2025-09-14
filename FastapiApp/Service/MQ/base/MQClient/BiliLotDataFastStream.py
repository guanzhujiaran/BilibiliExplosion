import asyncio
import random
import time
from typing import Callable, Dict, Annotated

from fast_depends import Depends
from faststream.rabbit import RabbitQueue
from faststream.rabbit.fastapi import RabbitMessage, RabbitBroker

from log.base_log import MQ_logger

from Models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from Service.MQ.base.MQClient.base import BaseFastStreamMQ, official_reserve_charge_lot_mq_prop, \
    upsert_official_reserve_charge_lot_mq_prop, upsert_lot_data_by_dynamic_id_prop, upsert_topic_lot_prop, \
    upsert_milvus_bili_lot_data_prop, router, get_broker, bili_voucher_prop
from Service.LangChainCompo.text_embed import lot_data_2_bili_lot_data_ls, save_bili_lot_data_embeddings
from Service.GrpcModule.Models.RabbitmqModel import VoucherInfo
from Service.GrpcModule.Utils.极验.极验点击验证码 import geetest_v3_breaker
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_lot_notice
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Utils.PushMe import a_pushme


async def handle_exception(
        module_name: str,
        e: Exception,
        params: Dict,
        msg: RabbitMessage
):
    error_msg = f"[ERROR]队列:{module_name}\n异常类型:{type(e)}\n异常:{e}\n时间:{time.strftime('%Y-%m-%d %H:%M:%S')}\n参数:{params}"
    MQ_logger.exception(error_msg)
    await a_pushme(
        f"抽奖MQ错误 - {module_name} - {e}",
        error_msg
    )
    await msg.nack()


def func_wrapper(func: Callable):
    async def wrapper(*args, **kwargs):
        # MQ_logger.debug(
        #     f"【{func.__name__}】收到消息：{args}")
        return await func(*args, **kwargs)

    return wrapper


__test_queue = RabbitQueue(
    name="test",
)


@router.after_startup
async def _test(app):
    await router.broker.publish("Hello!", __test_queue)


@router.subscriber(__test_queue, retry=True)
async def hello(
        body: str,
        msg: RabbitMessage,
):
    await asyncio.sleep(random.choice(range(0, 1000)))
    is_ack = random.choice([True, False])
    if is_ack:
        ret = f"ACK!{body} from Rabbit subscriber test!"
        # MQ_logger.info(ret)
        await msg.ack()
    else:
        ret = f"NACK!{body} from Rabbit subscriber test!"
        # MQ_logger.warning(ret)
        await msg.nack()
    return ret


@router.publisher(__test_queue)
@router.get('/test')
async def _test_msg_pub(msg: str, broker: Annotated[RabbitBroker, Depends(get_broker)]):
    ret = f"{msg} from Rabbit publisher test!"
    # MQ_logger.debug(ret)
    await broker.publish(msg, __test_queue)
    return ret


class OfficialReserveChargeLot(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=official_reserve_charge_lot_mq_prop
        )

    @func_wrapper
    async def consume(self,
                      _body: LotDataReq,
                      msg: RabbitMessage,
                      ):
        try:
            lot_data = await get_lot_notice(
                business_id=_body.business_id,
                business_type=_body.business_type,
                origin_dynamic_id=_body.origin_dynamic_id,
            )
            newly_lot_data = lot_data.get('data')
            if newly_lot_data:
                MQ_logger.info(f"newly_lot_data: {newly_lot_data}")
                await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                    newly_lot_data,
                    extra_routing_key="OfficialReserveChargeLotMQ")
                # result = await asyncio.to_thread(grpc_sql_helper.upsert_lot_detail, newly_lot_data)
                return await msg.ack()
            MQ_logger.debug(f"未获取到抽奖提示数据！参数：{_body}\t响应：{lot_data}")
            return await msg.ack()
        except Exception as e:
            await handle_exception(self.mq_props.queue_name, e, _body, msg)


class UpsertOfficialReserveChargeLot(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=upsert_official_reserve_charge_lot_mq_prop
        )

    @func_wrapper
    async def consume(
            self,
            newly_lot_data: Dict,
            msg: RabbitMessage,
    ):

        try:
            if newly_lot_data:
                lot_data = grpc_sql_helper.process_resp_data_dict_2_lotdata(newly_lot_data)
                await BiliLotDataPublisher.pub_upsert_milvus_bili_lot_data(lot_data)
                result = await grpc_sql_helper.upsert_lot_detail(newly_lot_data)

                MQ_logger.info(f"【{self.mq_props.queue_name}】upsert_lot_detail {newly_lot_data} result: {result}")
                return await msg.ack()
            MQ_logger.debug(
                f"【{self.mq_props.queue_name}】未获取到抽奖提示数据！参数：{newly_lot_data}")
            return await msg.ack()
        except Exception as e:
            await handle_exception(self.mq_props.queue_name, e, newly_lot_data, msg)


class UpsertLotDataByDynamicId(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            mq_props=upsert_lot_data_by_dynamic_id_prop
        )

    @func_wrapper
    async def consume(
            self,
            lot_data_dynamic_req: LotDataDynamicReq,
            msg: RabbitMessage,
    ):
        module_name = self.mq_props.queue_name
        try:
            MQ_logger.debug(
                f"【{module_name}】收到消息：{lot_data_dynamic_req}")
            if lot_data_dynamic_req.dynamic_id:
                dyn_detail = await dyn_detail_scrapy.get_grpc_single_dynDetail_by_dynamic_id(
                    lot_data_dynamic_req.dynamic_id)
                await dyn_detail_scrapy.Sqlhelper.upsert_DynDetail(
                    doc_id=dyn_detail.get('rid'),
                    dynamic_id=dyn_detail.get('dynamic_id'),
                    dynData=dyn_detail.get('dynData'),
                    lot_id=dyn_detail.get('lot_id'),
                    dynamic_created_time=dyn_detail.get('dynamic_created_time'))
                if dyn_detail.get('lot_id'):
                    MQ_logger.info(
                        f"【{module_name}】获取到抽奖提示数据！参数：{lot_data_dynamic_req}")
                else:
                    MQ_logger.debug(
                        f"【{module_name}】未获取到抽奖提示数据！参数：{lot_data_dynamic_req}")
                return await msg.ack()
            MQ_logger.debug(
                f"未获取到【{module_name}】参数！参数：{lot_data_dynamic_req}")
            return await msg.ack()
        except Exception as e:
            await handle_exception(module_name, e, lot_data_dynamic_req, msg)


class UpsertTopicLot(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            mq_props=upsert_topic_lot_prop
        )

    @func_wrapper
    async def consume(
            self,
            _body: TopicLotData,
            msg: RabbitMessage,
    ):
        module_name = self.mq_props.queue_name
        try:
            MQ_logger.debug(
                f"【{module_name}】收到消息：{_body}")
            lot_data = await topic_robot.pipeline(_body.topic_id)
            return await msg.ack()
        except Exception as e:
            await handle_exception(module_name, e, _body, msg)


class UpsertMilvusBiliLotData(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            mq_props=upsert_milvus_bili_lot_data_prop
        )

    @func_wrapper
    async def consume(
            self,
            _body: Dict,
            msg: RabbitMessage,
    ):
        module_name = self.mq_props.queue_name
        try:
            MQ_logger.debug(
                f"【{module_name}】收到消息：{_body}")
            lot_data = Lotdata(**_body)
            da = await lot_data_2_bili_lot_data_ls(lot_data)
            await save_bili_lot_data_embeddings(da)
            return await msg.ack()
        except Exception as e:
            await handle_exception(module_name, e, _body, msg)


class BiliVoucher(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=bili_voucher_prop
        )

    @func_wrapper
    async def consume(
            self,
            voucher_info: VoucherInfo,
            msg: RabbitMessage,
    ):
        module_name = self.mq_props.queue_name
        try:
            MQ_logger.debug(
                f"【{module_name}】收到消息：{voucher_info}")
            if int(time.time()) - voucher_info.generate_ts > 10:
                return await msg.ack()
            await geetest_v3_breaker.a_validate_form_voucher_ua(
                voucher_info.voucher,
                voucher_info.ua,
                voucher_info.ck,
                voucher_info.origin,
                voucher_info.referer,
                voucher_info.ticket,
                voucher_info.version,
                voucher_info.session_id,
                True,
            )
            return await msg.ack()
        except Exception as e:
            await handle_exception(module_name, e, voucher_info, msg)


official_reserve_charge_lot = OfficialReserveChargeLot()
upsert_official_reserve_charge_lot = UpsertOfficialReserveChargeLot()
upsert_lot_data_by_dynamic_id = UpsertLotDataByDynamicId()
upsert_topic_lot = UpsertTopicLot()
upsert_milvus_bili_lot_data = UpsertMilvusBiliLotData()
bili_voucher = BiliVoucher()
if __name__ == '__main__':
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=23332, loop="uvloop")
