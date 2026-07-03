from datetime import datetime
import json
import time
import asyncio
from typing import Any, Dict
from faststream.rabbit.fastapi import RabbitMessage
from Models.MQ.MQRouterModels import RabbitMQTestMsgModel
from Models.lottery_database.bili.LotteryDataModels import BiliLotteryStatusEnum
from log.base_log import MQ_logger
from Models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from Service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher, publisher_producer
from Service.MQ.base.MQClient.base import BaseFastStreamMQ, official_reserve_charge_lot_mq_prop, \
    upsert_official_reserve_charge_lot_mq_prop, upsert_lot_data_by_dynamic_id_prop, upsert_topic_lot_prop, \
    upsert_milvus_bili_lot_data_prop, router, bili_voucher_prop, upsert_bili_atari_prop, test_mq_prop
from Service.LangChainCompo.text_embed import lot_data_2_bili_lot_data_ls, save_bili_lot_data_embeddings
from Service.GrpcModule.Models.RabbitmqModel import VoucherInfo
from Utils.GrpcUtils.极验.极验点击验证码 import geetest_v3_breaker
from Service.GrpcModule.Grpc.Bapi.BiliApi import get_lot_notice
from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Service.GrpcModule.GrpcSrc.getDynDetail import dyn_detail_scrapy
from Service.opus新版官方抽奖.活动抽奖.话题抽奖.robot import topic_robot
from Utils.推送.PushMe import a_pushme


# 全局锁，确保所有 lottery_id 的处理串行化，避免死锁
# 简单粗暴但有效，适用于并发量不大的场景
_global_lottery_lock = asyncio.Lock()


async def handle_exception(
        module_name: str,
        e: Exception,
        params: Any,
        msg: RabbitMessage
):
    error_msg = f"[ERROR]队列:{module_name}\n异常类型:{type(e)}\n异常:{e}\n时间:{time.strftime('%Y-%m-%d %H:%M:%S')}\n参数:{params}"
    MQ_logger.exception(error_msg)
    await a_pushme(
        f"抽奖MQ错误 - {module_name} - {e}",
        json.dumps(error_msg, ensure_ascii=False)
    )
    await msg.nack()


async def _test_publish(pub_msg: str):
    do_pubish = publisher_producer(mq_props=test_mq_prop)
    test_msg = RabbitMQTestMsgModel(
        a=int(time.time()),
        b=pub_msg,
        c={1: pub_msg},
        d=[pub_msg]
    )
    MQ_logger.critical(f"【{rabbit_mq_test.mq_props.queue_name}】发布测试消息！{test_msg}")
    return await do_pubish(
        message=test_msg,
        extra_routing_key="test"
    )


# region 测试rabbitmq的连通性
@router.after_startup
async def _test_publish_init(app_instance):
    pub_msg = f'Ciallo～(∠・ω< )⌒★ 起床时间【{datetime.now()}】喵~'
    return await _test_publish(pub_msg)


class RabbitMQTest(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=test_mq_prop
        )

    async def consume(self,
                      _body: RabbitMQTestMsgModel,
                      msg: RabbitMessage,
                      ):
        try:
            MQ_logger.critical(f"【{self.mq_props.queue_name}】收到消息：{_body}")
            return await msg.ack()
        except Exception as e:
            await handle_exception(self.mq_props.queue_name, e, _body, msg)


# endregion

class OfficialReserveChargeLot(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=official_reserve_charge_lot_mq_prop
        )

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

    async def consume(
            self,
            newly_lot_data: dict,
            msg: RabbitMessage,
    ):
        """
        需要的数据是类似
        ```json
             {
                "lottery_id": 311007,
                "sender_uid": 401742377,
                "business_type": 1,
                "business_id": 962043520082772000,
                "status": 2,
                "lottery_time": 1723442400
            }
        ```
        这种响应的data字段
        """
        try:
            if newly_lot_data:
                lot_data = grpc_sql_helper.process_resp_data_dict_2_lotdata(newly_lot_data)
                await BiliLotDataPublisher.pub_upsert_milvus_bili_lot_data(lot_data)
                result = await grpc_sql_helper.upsert_lot_detail(newly_lot_data)
                MQ_logger.info(f"【{self.mq_props.queue_name}】upsert_lot_detail {newly_lot_data} result: {result}")
                if lot_data.status == BiliLotteryStatusEnum.end:
                    await BiliLotDataPublisher.pub_upsert_bili_atari(
                        lottery_id=lot_data.lottery_id,
                        extra_routing_key='UpsertOfficialReserveChargeLotMQ'
                    )
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

    async def consume(
            self,
            _body: dict | Dict,
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


class UpsertBiliAtari(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=upsert_bili_atari_prop
        )

    async def consume(
            self,
            lottery_id: int,
            msg: RabbitMessage,
    ):
        module_name = self.mq_props.queue_name
        try:
            async with _global_lottery_lock:
                MQ_logger.debug(
                    f"【{module_name}】收到消息：{lottery_id}")
                await grpc_sql_helper.sync_all_lottery_result_2_bili_user_info(lottery_id=lottery_id)
                return await msg.ack()
        except Exception as e:
            await handle_exception(module_name, e, lottery_id, msg)


class BiliVoucher(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            mq_props=bili_voucher_prop
        )

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
upsert_bili_atari = UpsertBiliAtari()
bili_voucher = BiliVoucher()
rabbit_mq_test = RabbitMQTest()

__all__ = [
    "router",
    "official_reserve_charge_lot",
    "upsert_official_reserve_charge_lot",
    "upsert_lot_data_by_dynamic_id",
    "upsert_topic_lot",
    "upsert_milvus_bili_lot_data",
    "upsert_bili_atari",
    "bili_voucher",
    "rabbit_mq_test",
]
