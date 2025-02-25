import asyncio
from fastapi接口.models.MQ.UpsertLotDataModel import LotDataReq, LotDataDynamicReq, TopicLotData
from fastapi接口.service.MQ.base.BasicAsyncClient import _mq_retry_wrapper
from fastapi接口.service.MQ.base.MQClient.BiliLotDataFastStream import official_reserve_charge_lot, \
    upsert_lot_data_by_dynamic_id, upsert_topic_lot, upsert_official_reserve_charge_lot


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
        return await official_reserve_charge_lot.publish(
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
        return await upsert_official_reserve_charge_lot.publish(
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
        return await upsert_lot_data_by_dynamic_id.publish(
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
        return await upsert_topic_lot.publish(
            body=da, extra_routing_key=extra_routing_key
        )
        # return await asyncio.to_thread(UpsertTopicLotMQ.publish_message, da, extra_routing_key)


async def _test(dynamic_id_list):
    return await asyncio.gather(
        *[BiliLotDataPublisher.pub_upsert_lot_data_by_dynamic_id(dynamic_id, extra_routing_key='_test') for dynamic_id
          in
          dynamic_id_list])


async def _test_pub_official_reserve_charge_lot():
    return await BiliLotDataPublisher.pub_official_reserve_charge_lot(
        business_type=1,
        business_id=994361504012697606,
        origin_dynamic_id=994361504012697606,
        extra_routing_key='manual_publish'
    )
async def _test_pub_upsert_official_reserve_charge_lot():
    return await BiliLotDataPublisher.pub_upsert_official_reserve_charge_lot(
        da={'lottery_id': 211752, 'sender_uid': 3493258283977582, 'business_type': 10, 'business_id': 3313301, 'status': 2, 'lottery_time': 1699672260, 'lottery_at_num': 0, 'lottery_feed_limit': 0, 'need_post': 0, 'pay_status': 0, 'first_prize': 1, 'second_prize': 0, 'third_prize': 0, 'ts': 1739982760, 'participants': 2775, 'has_charge_right': False, 'participated': False, 'followed': False, 'reposted': False, 'lottery_detail_url': 'https://www.bilibili.com/h5/lottery/result?business_id=3313301&business_type=10&lottery_id=211752', 'first_prize_cmt': '红包52R', 'third_prize_cmt': '', 'first_prize_pic': 'https://i0.hdslb.com/bfs/album/708b3604ff2fdd48db610e1767cfae7760932d23.gif', 'second_prize_pic': '', 'third_prize_pic': '', 'vip_batch_sign': '', 'prize_type_first': {'type': 0, 'value': {'stype': 0}}, 'lottery_result': {'first_prize_result': [{'uid': 319222045, 'name': '夏日尽头的小岛', 'face': 'https://i1.hdslb.com/bfs/face/a890e7184f569a44138647f5d67847c36b3fddc6.jpg', 'hongbao_money': 0}]}},
        extra_routing_key= 'ExtractOfficialLottery.update_lot_notice.solve_lot_data'
    )

if __name__ == "__main__":
    asyncio.run(_test_pub_upsert_official_reserve_charge_lot())
