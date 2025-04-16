from typing import Callable, Dict
from faststream.rabbit import RabbitQueue, RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit import RabbitExchange, ExchangeType
from faststream.rabbit.annotations import RabbitMessage
import fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer as DynDetailSqlHelperMysqlVer
import fastapi接口.service.grpc_module.src.SQLObject.models as models
import fastapi接口.log.base_log as base_log
import fastapi接口.models.MQ.UpsertLotDataModel as UpsertLotDataModel
import fastapi接口.service.compo.lottery_data_vec_sql.sql_helper as sql_helper
import fastapi接口.service.compo.text_embed as text_embed
import fastapi接口.utils.SqlalchemyTool as SqlalchemyTool
import fastapi接口.service.grpc_module.Utils.GrpcProxyModel as GrpcProxyModel
import fastapi接口.service.grpc_module.Utils.GrpcRedis as GrpcRedis
import fastapi接口.models.MQ.BaseMQModel as BaseMQModel

ExchangeName = BaseMQModel.ExchangeName
grpc_proxy_tools = GrpcRedis.grpc_proxy_tools
GrpcProxyStatus = GrpcProxyModel.GrpcProxyStatus
sqlalchemy_model_2_dict = SqlalchemyTool.sqlalchemy_model_2_dict
lot_data_2_bili_lot_data_ls = text_embed.lot_data_2_bili_lot_data_ls
milvus_sql_helper = sql_helper.milvus_sql_helper
LotDataReq, LotDataDynamicReq, TopicLotData = UpsertLotDataModel.LotDataReq, UpsertLotDataModel.LotDataDynamicReq, UpsertLotDataModel.TopicLotData
QueueName, RoutingKey, RabbitMQConfig = BaseMQModel.QueueName, BaseMQModel.RoutingKey, BaseMQModel.RabbitMQConfig
MQ_logger = base_log.MQ_logger
Lotdata = models.Lotdata
grpc_sql_helper = DynDetailSqlHelperMysqlVer.grpc_sql_helper

from utl.pushme.pushme import pushme
from CONFIG import CONFIG
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SQLHelper

rabbit_mq_config: RabbitMQConfig = RabbitMQConfig(
    host=CONFIG.RabbitMQConfig.host,
    port=CONFIG.RabbitMQConfig.port,
    username=CONFIG.RabbitMQConfig.user,
    password=CONFIG.RabbitMQConfig.pwd,
    protocol='amqp'
)
_rabbit_mq_url = f'{rabbit_mq_config.protocol}://{rabbit_mq_config.username}:{rabbit_mq_config.password}@{rabbit_mq_config.host}:{rabbit_mq_config.port}/'
router = RabbitRouter(_rabbit_mq_url, include_in_schema=True, logger=None)
exch = RabbitExchange(ExchangeName.bili_data.value, auto_delete=False, type=ExchangeType.TOPIC)
proxy_exch = RabbitExchange(ExchangeName.bili_data.value, auto_delete=False, type=ExchangeType.TOPIC)


def get_broker():
    return router.broker


def func_wrapper(func: Callable):
    async def wrapper(*args, **kwargs):
        # MQ_logger.debug(
        #     f"【{func.__name__}】收到消息：{args}")
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
        self.biliapi = None

    @func_wrapper
    async def consume(self,
                      _body: LotDataReq,
                      msg: RabbitMessage,
                      ):
        try:
            if not self.biliapi:
                import fastapi接口.service.grpc_module.grpc.bapi.biliapi as biliapi
                self.biliapi = biliapi
            lot_data = await self.biliapi.get_lot_notice(
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
                lot_data = grpc_sql_helper.process_resp_data_dict_2_lotdata(newly_lot_data)
                await upsert_milvus_bili_lot_data.publish(lot_data)
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

    async def publish(self, newly_lot_data: Dict, extra_routing_key: str = ""):
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
        self.getDynDetail  =None
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
                if not self.getDynDetail:
                    import fastapi接口.service.grpc_module.src.getDynDetail as getDynDetail
                    self.getDynDetail = getDynDetail
                dyn_detail = await self.getDynDetail.dyn_detail_scrapy.get_grpc_single_dynDetail_by_dynamic_id(
                    lot_data_dynamic_req.dynamic_id)
                await self.getDynDetail.dyn_detail_scrapy.Sqlhelper.upsert_DynDetail(
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
        self.topic_robot = None

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
            if self.topic_robot is None:
                import fastapi接口.service.opus新版官方抽奖.活动抽奖.定时获取话题抽奖 as 定时获取话题抽奖
                self.topic_robot = 定时获取话题抽奖.TopicRobot()
            lot_data = await self.topic_robot.pipeline(_body.topic_id, use_sem=False)
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


class UpsertMilvusBiliLotData(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            queue_name=QueueName.UpsertMilvusBiliLotDataMQ,
            routing_key_name=RoutingKey.UpsertMilvusBiliLotDataMQ
        )

    @func_wrapper
    async def consume(
            self,
            _body: Dict,
            msg: RabbitMessage,
    ):
        module_name = self.queue_name
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

    async def publish(self, body: Lotdata, extra_routing_key=""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        await broker.connect()
        async with broker:
            if extra_routing_key and type(extra_routing_key) is str:
                routing_key = self.routing_key_name + "." + extra_routing_key
            else:
                routing_key = self.routing_key_name
            await broker.publish(
                message=sqlalchemy_model_2_dict(body),
                queue=self.queue,
                exchange=exch,
                routing_key=routing_key
            )
        await broker.close()


class UpsertProxyInfo(BaseFastStreamMQ):

    def __init__(self):
        super().__init__(
            queue_name=QueueName.UpsertProxyInfoMQ,
            routing_key_name=RoutingKey.UpsertProxyInfoMQ
        )

    @func_wrapper
    async def consume(
            self,
            _body: Dict,
            msg: RabbitMessage,
    ):
        module_name = self.queue_name
        try:
            # MQ_logger.critical(
            #     f"【{module_name}】收到消息：{_body}")
            ip_status = GrpcProxyStatus(**_body.get('ip_status'))
            proxy_tab = ProxyTab(**_body.get('proxy_tab'))
            change_score_num = _body.get('change_score_num')
            origin_ip_status = await grpc_proxy_tools.get_ip_status_by_ip(ip_status.ip)
            if origin_ip_status.latest_used_ts >= ip_status.latest_used_ts:  # 原来的状态是最新的话
                ip_status.counter = origin_ip_status.counter
                ip_status.latest_used_ts = origin_ip_status.latest_used_ts
                ip_status.max_counter_ts = origin_ip_status.max_counter_ts
            await SQLHelper.update_to_proxy_list(proxy_tab, change_score_num)
            await grpc_proxy_tools.set_ip_status(ip_status)
            return await msg.ack()
        except Exception as e:
            MQ_logger.exception(f'{module_name} consume error: {e}')
            pushme(f'{module_name} consume error: {e}', e.__str__())
            await msg.nack()

    async def publish(self,
                      ip_status: GrpcProxyStatus,
                      proxy_tab: ProxyTab,
                      change_score_num: int,
                      extra_routing_key=""):
        broker = RabbitBroker(url=_rabbit_mq_url)
        await broker.connect()
        push_msg = {
            "ip_status": ip_status.to_dict(),
            "proxy_tab": sqlalchemy_model_2_dict(proxy_tab),
            "change_score_num": change_score_num,
        }
        async with broker:
            if extra_routing_key and type(extra_routing_key) is str:
                routing_key = self.routing_key_name + "." + extra_routing_key
            else:
                routing_key = self.routing_key_name
            await broker.publish(
                message=push_msg,
                queue=self.queue,
                exchange=proxy_exch,
                routing_key=routing_key
            )
        await broker.close()


official_reserve_charge_lot = OfficialReserveChargeLot()
upsert_official_reserve_charge_lot = UpsertOfficialReserveChargeLot()
upsert_lot_data_by_dynamic_id = UpsertLotDataByDynamicId()
upsert_topic_lot = UpsertTopicLot()
upsert_milvus_bili_lot_data = UpsertMilvusBiliLotData()
upsert_proxy_info = UpsertProxyInfo()
