from typing import Callable, Dict
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit.annotations import RabbitMessage

from fastapi接口.service.MQ.base.MQClient.BiliLotDataPublisher import BiliLotDataPublisher
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from fastapi接口.service.grpc_module.src.SQLObject.models import Lotdata
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.compo.lottery_data_vec_sql.sql_helper import milvus_sql_helper
from fastapi接口.service.compo.text_embed import lot_data_2_bili_lot_data_ls
from fastapi接口.service.MQ.base.MQClient.base import BaseFastStreamMQ, official_reserve_charge_lot_mq_prop, \
    upsert_official_reserve_charge_lot_mq_prop, upsert_lot_data_by_dynamic_id_prop, upsert_topic_lot_prop, \
    upsert_milvus_bili_lot_data_prop
from fastapi接口.service.opus新版官方抽奖.活动抽奖.定时获取话题抽奖 import topic_robot
from fastapi接口.service.grpc_module.grpc.bapi.biliapi import get_lot_notice
from fastapi接口.service.grpc_module.src.getDynDetail import dyn_detail_scrapy
from utl.pushme.pushme import pushme
from CONFIG import CONFIG

router = RabbitRouter(
    CONFIG.RabbitMQConfig.broker_url,
    include_in_schema=True,
    logger=None,
    max_consumers=1000,  # 对于rabbitmq来说就是 prefetch_count
)


def get_broker():
    return router.broker


def func_wrapper(func: Callable):
    async def wrapper(*args, **kwargs):
        # MQ_logger.debug(
        #     f"【{func.__name__}】收到消息：{args}")
        return await func(*args, **kwargs)

    return wrapper


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
                origin_dynamic_id=_body.origin_dynamic_id
            )
            newly_lot_data = lot_data.get('data')
            if newly_lot_data:
                MQ_logger.debug(f"newly_lot_data: {newly_lot_data}")
                await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
                    newly_lot_data,
                    extra_routing_key="OfficialReserveChargeLotMQ")
                # result = await asyncio.to_thread(grpc_sql_helper.upsert_lot_detail, newly_lot_data)
                return await msg.ack()
            MQ_logger.error(f"未获取到抽奖提示数据！参数：{_body}\t响应：{lot_data}")
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{self.mq_props.queue_name} consume error: {e}')
            pushme(f'{self.mq_props.queue_name} consume error: {e}', e.__str__())
            await msg.nack()


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

                MQ_logger.critical(f"【{self.mq_props.queue_name}】upsert_lot_detail {newly_lot_data} result: {result}")
                return await msg.ack()
            MQ_logger.error(
                f"【{self.mq_props.queue_name}】未获取到抽奖提示数据！参数：{newly_lot_data}")
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'【{self.mq_props.queue_name}】 consume error: {e}')
            pushme(f'【{self.mq_props.queue_name}】 consume error: {e}', e.__str__())
            await msg.nack()


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
            MQ_logger.critical(
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
                    MQ_logger.error(
                        f"【{module_name}】未获取到抽奖提示数据！参数：{lot_data_dynamic_req}")
                return await msg.ack()
            MQ_logger.error(
                f"未获取到【{module_name}】参数！参数：{lot_data_dynamic_req}")
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'【{module_name}】 consume error: {e}')
            pushme(f'【{module_name}】 consume error: {e}', e.__str__())
            await msg.nack()


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
            MQ_logger.critical(
                f"【{module_name}】收到消息：{_body}")
            lot_data = await topic_robot.pipeline(_body.topic_id, use_sem=False)
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{module_name} consume error: {e}')
            pushme(f'{module_name} consume error: {e}', e.__str__())
            await msg.nack()


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
            MQ_logger.critical(
                f"【{module_name}】收到消息：{_body}")
            lot_data = Lotdata(**_body)
            da = await lot_data_2_bili_lot_data_ls(lot_data)
            await milvus_sql_helper.upsert_bili_lot_data(da)
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{module_name} consume error: {e}')
            pushme(f'{module_name} consume error: {e}', e.__str__())
            await msg.nack()



official_reserve_charge_lot = OfficialReserveChargeLot()
upsert_official_reserve_charge_lot = UpsertOfficialReserveChargeLot()
upsert_lot_data_by_dynamic_id = UpsertLotDataByDynamicId()
upsert_topic_lot = UpsertTopicLot()
upsert_milvus_bili_lot_data = UpsertMilvusBiliLotData()
