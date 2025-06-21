from fastapi接口.models.MQ.BaseMQModel import MQPropBase
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.BasicAsyncClient import _mq_retry_wrapper
from fastapi接口.service.MQ.base.MQClient.base import official_reserve_charge_lot_mq_prop, \
    upsert_official_reserve_charge_lot_mq_prop, upsert_lot_data_by_dynamic_id_prop, upsert_topic_lot_prop, \
    upsert_milvus_bili_lot_data_prop, get_broker
from fastapi接口.service.grpc_module.src.SQLObject.models import Lotdata
from fastapi接口.utils.SqlalchemyTool import sqlalchemy_model_2_dict





def publisher_producer(mq_props: MQPropBase):
    async def publisher(message, extra_routing_key: str = ""):
        broker = get_broker()
        await broker.connect()
        if extra_routing_key and type(extra_routing_key) is str:
            routing_key = mq_props.routing_key_name + "." + extra_routing_key
        else:
            routing_key = mq_props.routing_key_name
        await broker.publish(
            message=message,
            queue=mq_props.rabbit_queue,
            exchange=mq_props.exchange,
            routing_key=routing_key
        )

    return publisher


class BiliLotDataPublisher:
    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_official_reserve_charge_lot(
            business_type: int | str,
            business_id: int | str,
            origin_dynamic_id: int | str,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        publisher = publisher_producer(official_reserve_charge_lot_mq_prop)
        return await publisher(
            message=LotDataReq(
                business_type=business_type,
                business_id=business_id,
                origin_dynamic_id=origin_dynamic_id,
                **kwargs
            ),
            extra_routing_key=extra_routing_key
        )

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_official_reserve_charge_lot(da: dict,extra_routing_key: str = "", *args,**kwargs):
        """
        da类似于：{"lottery_id":183958,"sender_uid":497268468,"business_type":10,"business_id":3198459,"status":2,"lottery_time":1695988800,"lottery_at_num":0,"lottery_feed_limit":0,"need_post":0,"first_prize":1,"second_prize":2,"third_prize":3,"ts":1750391138,"participants":232,"has_charge_right":false,"participated":false,"followed":false,"reposted":false,"lottery_detail_url":"https://www.bilibili.com/h5/lottery/result?business_id=3198459&business_type=10&lottery_id=183958","first_prize_cmt":"3元红包","second_prize_cmt":"2元红包","third_prize_cmt":"1元红包","first_prize_pic":"","second_prize_pic":"","third_prize_pic":"","vip_batch_sign":"","vip_redirect_url":"","upower_redirect_url":"","prize_type_first":{"type":0,"value":{"stype":0,"count":0}},"prize_type_second":{"type":0,"value":{"stype":0,"count":0}},"prize_type_third":{"type":0,"value":{"stype":0,"count":0}},"lottery_result":{"first_prize_result":[{"uid":24221832,"name":"A包B听","face":"https://i0.hdslb.com/bfs/face/721e502619510c74332edfa61c6b7db745ae10de.jpg","hongbao_money":0}],"second_prize_result":[{"uid":7355922,"name":"一如无幻","face":"https://i0.hdslb.com/bfs/face/member/noface.jpg","hongbao_money":0},{"uid":454048155,"name":"数字乱打","face":"http://i0.hdslb.com/bfs/face/e55810f9eb33aa6fee10e55d44cff9d0c5238a89.jpg","hongbao_money":0}],"third_prize_result":[{"uid":399112724,"name":"花开心累","face":"https://i2.hdslb.com/bfs/face/36f6c927bd7e128e55d85b0a94732b3dfb3d7b96.jpg","hongbao_money":0},{"uid":479557348,"name":"小手一牵-","face":"https://i1.hdslb.com/bfs/face/ed1af9275d5e946c89ebf526d04ff1137731812c.jpg","hongbao_money":0},{"uid":518244596,"name":"笑花猫","face":"https://i2.hdslb.com/bfs/face/89d10ef46f111be7afabeb335988e46c3aae9175.jpg","hongbao_money":0}]}}
        """
        publisher = publisher_producer(upsert_official_reserve_charge_lot_mq_prop)
        return await publisher(
            message=da,
            extra_routing_key=extra_routing_key
        )
        # return await asyncio.to_thread(UpsertOfficialReserveChargeLotMQ.publish_message, da, extra_routing_key)

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_lot_data_by_dynamic_id(
            dynamic_id: int | str,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        da = LotDataDynamicReq(dynamic_id=dynamic_id, **kwargs)
        publisher = publisher_producer(upsert_lot_data_by_dynamic_id_prop)
        return await publisher(
            message=da, extra_routing_key=extra_routing_key
        )

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_topic_lot(
            topic_id: int | str,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        da = TopicLotData(topic_id=topic_id, **kwargs)
        publisher = publisher_producer(mq_props=upsert_topic_lot_prop)
        return await publisher(
            message=da, extra_routing_key=extra_routing_key
        )
        # return await asyncio.to_thread(UpsertTopicLotMQ.publish_message, da, extra_routing_key)

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_milvus_bili_lot_data(
            body: Lotdata,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        publisher = publisher_producer(mq_props=upsert_milvus_bili_lot_data_prop)
        return await publisher(
            message=sqlalchemy_model_2_dict(body), extra_routing_key=extra_routing_key
        )
