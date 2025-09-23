from Models.MQ.BaseMQModel import MQPropBase
from Models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from Service.MQ.base.BasicAsyncClient import _mq_retry_wrapper
from Service.MQ.base.MQClient.base import official_reserve_charge_lot_mq_prop, \
    upsert_official_reserve_charge_lot_mq_prop, upsert_lot_data_by_dynamic_id_prop, upsert_topic_lot_prop, \
    upsert_milvus_bili_lot_data_prop, get_broker, bili_voucher_prop, upsert_bili_atari_prop
from Service.GrpcModule.Models.RabbitmqModel import VoucherInfo
from Service.GrpcModule.GrpcSrc.SQLObject.models import Lotdata
from Utils.SqlalchemyTool import sqlalchemy_model_2_dict


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
    async def pub_upsert_official_reserve_charge_lot(da: dict, extra_routing_key: str = "", *args, **kwargs):
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
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
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

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_bili_voucher(
            body: VoucherInfo,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        publisher = publisher_producer(mq_props=bili_voucher_prop)
        return await publisher(
            message=body, extra_routing_key=extra_routing_key
        )

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_bili_atari(
            lottery_id: int,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        publisher = publisher_producer(mq_props=upsert_bili_atari_prop)
        return await publisher(
            message=lottery_id,
            extra_routing_key=extra_routing_key
        )
