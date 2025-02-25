import asyncio
import traceback
from pika.exchange_type import ExchangeType
from fastapi接口.log.base_log import MQ_logger
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.BasicAsyncClient import BasicMessageReceiver, QueueName, ExchangeName, \
    RoutingKey, BasicMessageSender
from grpc获取动态.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from grpc获取动态.grpc.bapi.biliapi import get_lot_notice
from opus新版官方抽奖.活动抽奖 import 定时获取话题抽奖
from utl.pushme.pushme import pushme


class OfficialReserveChargeLotMQ(BasicMessageReceiver):
    e = ExchangeName.bili_data
    t = ExchangeType.topic
    q = QueueName.OfficialReserveChargeLotMQ
    r = RoutingKey.OfficialReserveChargeLotMQ

    async def consume(self, method, properties, body):
        try:
            MQ_logger.critical(
                f"【{OfficialReserveChargeLotMQ.__name__}】收到消息：{self.decode_message(body=body)}\n{method}")
            _body: LotDataReq = LotDataReq(**self.decode_message(body=body))
            lot_data = await get_lot_notice(
                business_id=_body.business_id,
                business_type=_body.business_type,
                origin_dynamic_id=_body.origin_dynamic_id
            )
            newly_lot_data = lot_data.get('data')
            if newly_lot_data:
                MQ_logger.debug(f"newly_lot_data: {newly_lot_data}")
                result = await grpc_sql_helper.upsert_lot_detail(newly_lot_data)
                MQ_logger.critical(f"插入数据：{newly_lot_data.get('lottery_id')}\t结果：{result}")
                return self.acknowledge_message(delivery_tag=method.delivery_tag)
            MQ_logger.error(f"未获取到抽奖提示数据！参数：{_body}\t响应：{lot_data}")
            return self.acknowledge_message(delivery_tag=method.delivery_tag)
        except Exception as e:
            MQ_logger.exception(f'OfficialReserveChargeLotMQ consume error: {e}')
            pushme(f'OfficialReserveChargeLotMQ consume error: {e}', traceback.format_exc())
            self.nacknowledge_message(delivery_tag=method.delivery_tag)

    @classmethod
    async def create_consumer(cls):
        """创建消费者"""
        worker = cls(cls.e, cls.t, cls.q, cls.r)
        # worker.prefetch_count = 10  # 一次处理10条消息
        await worker.run()

    @classmethod
    def publish_message(cls, body: LotDataReq, extra_routing_key: str = ""):
        """发布消息"""
        body = body.model_dump()
        MQ_logger.info(f"【{cls.__name__}】发布消息：{body}")
        message_sender = BasicMessageSender(cls.e, cls.t, cls.q, cls.r)
        while 1:
            try:
                message_sender.send_message(body, extra_routing_key=extra_routing_key)
                break
            except Exception as e:
                MQ_logger.exception(f'【{cls.__name__}】 publish error: {e}')
                pushme(f'【{cls.__name__}】 publish error: {e}', traceback.format_exc())


class UpsertOfficialReserveChargeLotMQ(BasicMessageReceiver):
    """
    所有的官方抽奖、充电抽奖、预约抽奖都会保存到sqlite的dynDetail数据库的lotData表里面
    """
    e = ExchangeName.bili_data
    t = ExchangeType.topic
    q = QueueName.UpsertOfficialReserveChargeLotMQ
    r = RoutingKey.UpsertOfficialReserveChargeLotMQ

    async def consume(self, method, properties, body):
        try:
            newly_lot_data = self.decode_message(body=body)
            MQ_logger.critical(f"【{UpsertOfficialReserveChargeLotMQ.__name__}】收到消息：{newly_lot_data}\n{method}")
            if newly_lot_data:
                result = await grpc_sql_helper.upsert_lot_detail(newly_lot_data)
                MQ_logger.critical(f"插入数据：{newly_lot_data.get('lottery_id')}\t结果：{result}")
                return self.acknowledge_message(delivery_tag=method.delivery_tag)
            MQ_logger.error(
                f"【{UpsertOfficialReserveChargeLotMQ.__name__}】未获取到抽奖提示数据！参数：{newly_lot_data}\n原始参数：{body}")
            return self.acknowledge_message(delivery_tag=method.delivery_tag)
        except Exception as e:
            MQ_logger.exception(f'【{UpsertOfficialReserveChargeLotMQ.__name__}】 consume error: {e}')
            pushme(f'【{UpsertOfficialReserveChargeLotMQ.__name__}】 consume error: {e}', traceback.format_exc())
            self.nacknowledge_message(delivery_tag=method.delivery_tag)

    @classmethod
    async def create_consumer(cls):
        """创建消费者"""
        worker = cls(cls.e, cls.t, cls.q, cls.r)
        # worker.prefetch_count = 10  # 一次处理10条消息
        await worker.run()

    @classmethod
    def publish_message(cls, body: dict, extra_routing_key: str = ""):
        """发布消息"""
        MQ_logger.info(f"【{cls.__name__}】发布消息：{body}")
        message_sender = BasicMessageSender(cls.e, cls.t, cls.q, cls.r)
        while 1:
            try:
                message_sender.send_message(
                    body,
                    extra_routing_key=extra_routing_key
                )
                break
            except Exception as e:
                MQ_logger.exception(f'【{cls.__name__}】 publish error: {e}')
                pushme(f'【{cls.__name__}】 publish error: {e}', traceback.format_exc())


class UpsertLotDataByDynamicIdMQ(BasicMessageReceiver):
    q = QueueName.UpsertLotDataByDynamicIdMQ
    t = ExchangeType.topic
    e = ExchangeName.bili_data
    r = RoutingKey.UpsertLotDataByDynamicIdMQ

    def __init__(self):
        super().__init__(self.e, self.t, self.q, self.r)
        from grpc获取动态.src.getDynDetail import dyn_detail_scrapy
        self.dyn_detail_scrapy = dyn_detail_scrapy

    async def consume(self, method, properties, body):
        try:
            MQ_logger.critical(
                f"【{UpsertLotDataByDynamicIdMQ.__name__}】收到消息：{self.decode_message(body=body)}\n{method}")
            lot_data_dynamic_req: LotDataDynamicReq = LotDataDynamicReq(**self.decode_message(body=body))
            if lot_data_dynamic_req.dynamic_id:
                dyn_detail = await self.dyn_detail_scrapy.get_grpc_single_dynDetail_by_dynamic_id(
                    lot_data_dynamic_req.dynamic_id)
                await self.dyn_detail_scrapy.Sqlhelper.upsert_DynDetail(
                    doc_id=dyn_detail.get('rid'),
                    dynamic_id=dyn_detail.get('dynamic_id'),
                    dynData=dyn_detail.get('dynData'),
                    lot_id=dyn_detail.get('lot_id'),
                    dynamic_created_time=dyn_detail.get('dynamic_created_time')
                )
                if dyn_detail.get('lot_id'):
                    MQ_logger.info(
                        f"【{UpsertLotDataByDynamicIdMQ.__name__}】获取到抽奖提示数据！参数：{self.decode_message(body=body)}\n{method}")
                else:
                    MQ_logger.error(
                        f"【{UpsertLotDataByDynamicIdMQ.__name__}】未获取到抽奖提示数据！参数：{self.decode_message(body=body)}\n{method}")
                return self.acknowledge_message(delivery_tag=method.delivery_tag)
            MQ_logger.error(
                f"未获取到【{UpsertLotDataByDynamicIdMQ.__name__}】参数！参数：{self.decode_message(body=body)}\n{method}")
            return self.acknowledge_message(delivery_tag=method.delivery_tag)
        except Exception as e:
            MQ_logger.exception(f'【{UpsertLotDataByDynamicIdMQ.__name__}】 consume error: {e}')
            pushme(f'【{UpsertLotDataByDynamicIdMQ.__name__}】 consume error: {e}', traceback.format_exc())
            self.nacknowledge_message(delivery_tag=method.delivery_tag)

    @classmethod
    async def create_consumer(cls):
        """创建消费者"""
        worker = cls()
        # worker.prefetch_count = 10  # 一次处理10条消息
        await worker.run()

    @classmethod
    def publish_message(cls, body: LotDataDynamicReq, extra_routing_key: str = ""):
        """发布消息"""
        body = body.model_dump()
        MQ_logger.info(f"【{cls.__name__}】发布消息：{body}")
        message_sender = BasicMessageSender(cls.e, cls.t, cls.q, cls.r)
        while 1:
            try:
                message_sender.send_message(body, extra_routing_key=extra_routing_key)
                break
            except Exception as e:
                MQ_logger.exception(f'【{cls.__name__}】 publish error: {e}')
                pushme(f'【{cls.__name__}】 publish error: {e}', traceback.format_exc())


class UpsertTopicLotMQ(BasicMessageReceiver):
    e = ExchangeName.bili_data
    t = ExchangeType.topic
    q = QueueName.UpsertTopicLotMQ
    r = RoutingKey.UpsertTopicLotMQ

    async def consume(self, method, properties, body):
        try:
            MQ_logger.critical(
                f"【{UpsertTopicLotMQ.__name__}】收到消息：{self.decode_message(body=body)}\n{method}")
            _body: TopicLotData = TopicLotData(**self.decode_message(body=body))
            if 定时获取话题抽奖.topic_robot is None:
                定时获取话题抽奖.topic_robot = 定时获取话题抽奖.TopicRobot()
            lot_data = await 定时获取话题抽奖.topic_robot.pipeline(_body.topic_id, use_sem=False)
            return self.acknowledge_message(delivery_tag=method.delivery_tag)
        except Exception as e:
            MQ_logger.exception(f'UpsertTopicLotMQ consume error: {e}')
            pushme(f'UpsertTopicLotMQ consume error: {e}', traceback.format_exc())
            self.nacknowledge_message(delivery_tag=method.delivery_tag)

    @classmethod
    async def create_consumer(cls):
        """创建消费者"""
        worker = cls(cls.e, cls.t, cls.q, cls.r)
        # worker.prefetch_count = 10  # 一次处理10条消息
        await worker.run()

    @classmethod
    def publish_message(cls, body: TopicLotData, extra_routing_key: str = ""):
        """发布消息"""
        body = body.model_dump()
        MQ_logger.info(f"【{cls.__name__}】发布消息：{body}")
        message_sender = BasicMessageSender(cls.e, cls.t, cls.q, cls.r)
        while 1:
            try:
                message_sender.send_message(body, extra_routing_key=extra_routing_key)
                break
            except Exception as e:
                MQ_logger.exception(f'【{cls.__name__}】 publish error: {e}')
                pushme(f'【{cls.__name__}】 publish error: {e}', traceback.format_exc())


if __name__ == "__main__":
    asyncio.new_event_loop()
    # UpsertLotDataByDynamicIdMQ.create_consumer()
    # UpsertOfficialReserveChargeLotMQ.create_consumer()
    OfficialReserveChargeLotMQ.create_consumer()
