from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.BasicAsyncClient import _mq_retry_wrapper
import fastapi接口.service.MQ.base.MQClient.BiliLotDataFastStream as BiliLotDataFastStream
from fastapi接口.service.grpc_module.Utils.GrpcProxyModel import GrpcProxyStatus
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab


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
        return await BiliLotDataFastStream.official_reserve_charge_lot.publish(
            body=LotDataReq(
                business_type=business_type,
                business_id=business_id,
                origin_dynamic_id=origin_dynamic_id,
                **kwargs
            ),
            extra_routing_key=extra_routing_key
        )
        # 老版本的，已经弃用
        # return await asyncio.to_thread(
        #     OfficialReserveChargeLotMQ.publish_message,
        #     LotDataReq(
        #         business_type=business_type,
        #         business_id=business_id,
        #         origin_dynamic_id=origin_dynamic_id,
        #         **kwargs
        #     ),
        #     extra_routing_key=extra_routing_key,
        # )

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_official_reserve_charge_lot(
            da: dict,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        return await BiliLotDataFastStream.upsert_official_reserve_charge_lot.publish(
            newly_lot_data=da,
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
        return await BiliLotDataFastStream.upsert_lot_data_by_dynamic_id.publish(
            lot_data_dynamic_req=da, extra_routing_key=extra_routing_key
        )
        # return await asyncio.to_thread(UpsertLotDataByDynamicIdMQ.publish_message, )

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
        return await BiliLotDataFastStream.upsert_topic_lot.publish(
            body=da, extra_routing_key=extra_routing_key
        )
        # return await asyncio.to_thread(UpsertTopicLotMQ.publish_message, da, extra_routing_key)

    @staticmethod
    @_mq_retry_wrapper(max_retries=-1)
    async def pub_upsert_proxy_info(
            ip_status: GrpcProxyStatus,
            proxy_tab: ProxyTab,
            change_score_num: int,
            extra_routing_key: str = "",
            *args,
            **kwargs
    ):
        for i, value in enumerate(args, start=1):
            kwargs[f"extra_field_{i}"] = value
        return await BiliLotDataFastStream.upsert_proxy_info.publish(
            ip_status=ip_status,
            proxy_tab=proxy_tab,
            change_score_num=change_score_num,
            extra_routing_key=extra_routing_key
        )

