from typing import Callable, Dict
import asyncio
from faststream.rabbit import RabbitQueue, fastapi, RabbitBroker
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.BaseMQModel import QueueName, RoutingKey, RabbitMQConfig
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from grpc获取动态.grpc.bapi.biliapi import get_lot_notice
from grpc获取动态.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from faststream.rabbit.annotations import (
    RabbitMessage,
)
from utl.pushme.pushme import pushme
from CONFIG import CONFIG
from faststream.rabbit import RabbitExchange, ExchangeType
from fastapi接口.models.MQ.BaseMQModel import ExchangeName

rabbit_mq_config: RabbitMQConfig = RabbitMQConfig(
    host=CONFIG.RabbitMQConfig.host,
    port=CONFIG.RabbitMQConfig.port,
    username=CONFIG.RabbitMQConfig.user,
    password=CONFIG.RabbitMQConfig.pwd,
    protocol='amqp'
)
_rabbit_mq_url = f'{rabbit_mq_config.protocol}://{rabbit_mq_config.username}:{rabbit_mq_config.password}@{rabbit_mq_config.host}:{rabbit_mq_config.port}/'
router = fastapi.RabbitRouter(_rabbit_mq_url, include_in_schema=True)
exch = RabbitExchange(ExchangeName.bili_data.value, auto_delete=False, type=ExchangeType.TOPIC)


def get_broker():
    return router.broker


def func_wrapper(func: Callable):
    async def wrapper(*args, **kwargs):
        MQ_logger.critical(
            f"【{func.__name__}】收到消息：{args}")
        return await func(*args, **kwargs)

    return wrapper


class BaseFastStreamMQ:
    def __init__(self, queue_name: QueueName, routing_key_name: RoutingKey, ):
        self.queue_name = queue_name
        self.routing_key_name = routing_key_name  # 默认使用通配符
        self.queue = RabbitQueue(
            name=queue_name,
            routing_key=routing_key_name + '.#'
        )

    async def consume(self, *args, **kwargs):
        raise NotImplementedError("子类必须实现此方法")

    async def publish(self, *args, **kwargs):
        raise NotImplementedError("子类必须实现此方法")


class OfficialReserveChargeLot(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            queue_name=QueueName.OfficialReserveChargeLotMQ,
            routing_key_name=RoutingKey.OfficialReserveChargeLotMQ
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
                await upsert_official_reserve_charge_lot.publish(
                    newly_lot_data,
                    extra_routing_key="OfficialReserveChargeLotMQ")
                # result = await asyncio.to_thread(grpc_sql_helper.upsert_lot_detail, newly_lot_data)
                return await msg.ack()
            MQ_logger.error(f"未获取到抽奖提示数据！参数：{_body}\t响应：{lot_data}")
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{self.queue_name} consume error: {e}')
            pushme(f'{self.queue_name} consume error: {e}', e.__str__())
            await msg.nack()

    async def publish(self, body: LotDataReq, extra_routing_key: str = ""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        await broker.connect()
        if extra_routing_key and type(extra_routing_key) is str:
            routing_key = self.routing_key_name + "." + extra_routing_key
        else:
            routing_key = self.routing_key_name
        await broker.publish(
            message=body,
            queue=self.queue,
            exchange=exch,
            routing_key=routing_key
        )
        await broker.close()


class UpsertOfficialReserveChargeLot(BaseFastStreamMQ):
    def __init__(self):
        super().__init__(
            queue_name=QueueName.UpsertOfficialReserveChargeLotMQ,
            routing_key_name=RoutingKey.UpsertOfficialReserveChargeLotMQ
        )

    @func_wrapper
    async def consume(
            self,
            newly_lot_data: Dict,
            msg: RabbitMessage,
    ):

        try:
            if newly_lot_data:
                result = await grpc_sql_helper.upsert_lot_detail(newly_lot_data)
                MQ_logger.critical(f"【{self.queue_name}】upsert_lot_detail {newly_lot_data} result: {result}")
                return await msg.ack()
            MQ_logger.error(
                f"【{self.queue_name}】未获取到抽奖提示数据！参数：{newly_lot_data}")
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'【{self.queue_name}】 consume error: {e}')
            pushme(f'【{self.queue_name}】 consume error: {e}', e.__str__())
            await msg.nack()

    async def publish(self, newly_lot_data: dict, extra_routing_key: str = ""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        if extra_routing_key and type(extra_routing_key) is str:
            routing_key = self.routing_key_name + "." + extra_routing_key
        else:
            routing_key = self.routing_key_name
        await broker.connect()
        await broker.publish(
            message=newly_lot_data,
            queue=self.queue,
            exchange=exch,
            routing_key=routing_key
        )
        await broker.close()


class UpsertLotDataByDynamicId(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            queue_name=QueueName.UpsertLotDataByDynamicIdMQ,
            routing_key_name=RoutingKey.UpsertLotDataByDynamicIdMQ
        )
        self.dyn_detail_scrapy = None

    @func_wrapper
    async def consume(
            self,
            lot_data_dynamic_req: LotDataDynamicReq,
            msg: RabbitMessage,
    ):
        module_name = self.queue_name
        try:
            MQ_logger.critical(
                f"【{module_name}】收到消息：{lot_data_dynamic_req}")
            if lot_data_dynamic_req.dynamic_id:
                if not self.dyn_detail_scrapy:
                    from grpc获取动态.src.getDynDetail import dyn_detail_scrapy
                    self.dyn_detail_scrapy = dyn_detail_scrapy
                dyn_detail = await self.dyn_detail_scrapy.get_grpc_single_dynDetail_by_dynamic_id(
                    lot_data_dynamic_req.dynamic_id)
                await self.dyn_detail_scrapy.Sqlhelper.upsert_DynDetail(
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

    async def publish(self, lot_data_dynamic_req: LotDataDynamicReq, extra_routing_key: str = ""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        await broker.connect()
        if extra_routing_key and type(extra_routing_key) is str:
            routing_key = self.routing_key_name + "." + extra_routing_key
        else:
            routing_key = self.routing_key_name
        await broker.publish(
            message=lot_data_dynamic_req,
            queue=self.queue,
            exchange=exch,
            routing_key=routing_key
        )
        await broker.close()


class UpsertTopicLot(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            queue_name=QueueName.UpsertTopicLotMQ,
            routing_key_name=RoutingKey.UpsertTopicLotMQ
        )
        from opus新版官方抽奖.活动抽奖 import 定时获取话题抽奖
        self.定时获取话题抽奖 = 定时获取话题抽奖

    @func_wrapper
    async def consume(
            self,
            _body: TopicLotData,
            msg: RabbitMessage,
    ):
        module_name = self.queue_name
        try:
            MQ_logger.critical(
                f"【{module_name}】收到消息：{_body}")
            if self.定时获取话题抽奖.topic_robot is None:
                self.定时获取话题抽奖.topic_robot = self.定时获取话题抽奖.TopicRobot()
            lot_data = await self.定时获取话题抽奖.topic_robot.pipeline(_body.topic_id, use_sem=False)
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{module_name} consume error: {e}')
            pushme(f'{module_name} consume error: {e}', e.__str__())
            await msg.nack()

    async def publish(self, body: TopicLotData, extra_routing_key=""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        await broker.connect()
        async with broker:
            if extra_routing_key and type(extra_routing_key) is str:
                routing_key = self.routing_key_name + "." + extra_routing_key
            else:
                routing_key = self.routing_key_name
            await broker.publish(
                message=body,
                queue=self.queue,
                exchange=exch,
                routing_key=routing_key
            )
        await broker.close()


official_reserve_charge_lot = OfficialReserveChargeLot()
upsert_official_reserve_charge_lot = UpsertOfficialReserveChargeLot()
upsert_lot_data_by_dynamic_id = UpsertLotDataByDynamicId()
upsert_topic_lot = UpsertTopicLot()
