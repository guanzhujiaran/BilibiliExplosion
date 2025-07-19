import asyncio
import gc
import json

from fastapi import Body

from fastapi接口.controller.common.base import new_router
from fastapi接口.dao.redisConn import r
from fastapi接口.log.base_log import myfastapi_logger
from fastapi接口.models.lottery_database.bili.LotteryDataModels import reserveInfo
from fastapi接口.service.bili_live_monitor.src.monitor import BiliLiveLotRedisManager
from fastapi接口.service.get_others_lot_dyn.get_other_lot_main import get_others_lot_dyn
from fastapi接口.service.grpc_module.src.SQLObject.DynDetailSqlHelperMysqlVer import grpc_sql_helper
from fastapi接口.service.grpc_module.src.获取取关对象.GetRmFollowingListV2 import gmflv2
from fastapi接口.service.toutiao.src.FastApiReturns.SpaceFeedLotService.ToutiaoSpaceFeedLot import \
    toutiaoSpaceFeedLotService
from fastapi接口.service.zhihu.获取知乎抽奖想法.根据用户空间获取想法.GetMomentsByUser import zhihu_lotScrapy
from utl.pushme.pushme import pushme

router = new_router()


@router.get('/v1/get/live_lots', description='获取redis中的所有直播相关抽奖信息', )
async def v1_get_live_lots(
        get_all: bool = False
):
    def _():
        ret_list = []
        if get_all:
            return json.loads(r.get(BiliLiveLotRedisManager.RedisMap.all_live_lot.value))
        for k in r.keys():
            if k == BiliLiveLotRedisManager.RedisMap.all_live_lot.value.encode('utf-8'):
                continue
            if b'Lock' in k:
                continue
            res = r.get(k)
            if res:
                ret_list.append(json.loads(res))
        return ret_list

    return await asyncio.to_thread(_)


# region 测试类

@router.get('/test')
async def app_avaliable_api():
    await asyncio.sleep(1)
    return 'Service is running!'


@router.get('/gc')
async def app_avaliable_api():
    await asyncio.to_thread(gc.collect)
    return 'gc完成！'


# endregion

# region 基于Grpc api的功能实现
@router.post('/v1/post/RmFollowingList', response_model=list, description='获取需要取关的up主列表')
async def v1_post_rm_following_list(data: list[int | str] = Body()):
    """
    取关接口 调用的是b站appp端的grpc协议接口，没那么容易被风控
    :param data: list[int] 关注列表 直接传列表即可
    :return:
    """
    return await gmflv2.get_rm_following_list(data)


# endregion

# region 获取抽奖内容接口
@router.post('/lot/upsert_lot_detail')
async def upsert_lot_detail(request_body: dict):
    result = await grpc_sql_helper.upsert_lot_detail(request_body)
    return result


@router.get('/get_others_lot_dyn')
async def api_get_others_lot_dyn():
    myfastapi_logger.error('get_others_lot_dyn 开始获取B站其他用户的动态抽奖！')
    result = await get_others_lot_dyn.get_new_dyn()
    return result


@router.get('/get_others_official_lot_dyn')
async def api_get_others_official_lot_dyn():
    myfastapi_logger.error('get_others_lot_dyn 开始获取别人的官方动态抽奖！')
    return await get_others_lot_dyn.get_official_lot_dyn()


@router.get('/get_others_big_lot')
async def api_get_others_big_lot():
    myfastapi_logger.error('get_others_lot_dyn 开始获取别人的大奖！')
    return await get_others_lot_dyn.get_unignore_Big_lot_dyn()


@router.get('/get_others_big_reserve')
async def api_get_others_big_reserve() -> list[reserveInfo]:
    myfastapi_logger.error('get_others_lot_dyn 开始获取重要的预约抽奖！')
    result = await get_others_lot_dyn.get_unignore_reserve_lot_space()
    reserveInfos = []
    for i in result:  # 对df的每一行数据访问
        reserve_info = reserveInfo(
            reserve_url=f'https://space.bilibili.com/{str(i.upmid)}/dynamic',
            etime=i.etime,
            lottery_prize_info=i.text,
            jump_url=i.jumpUrl,
            reserve_sid=i.sid,
            available=True
        )
        reserveInfos.append(reserve_info)
    return reserveInfos


@router.get('/zhihu/get_others_lot_pins', description='获取知乎抽奖内容，返回url列表，直接访问即可')
async def zhuhu_avaliable_api():
    myfastapi_logger.info('开始获取zhihu抽奖内容')
    resp = await zhihu_lotScrapy.api_get_all_pins()
    await asyncio.to_thread(pushme, f'获取到知乎抽奖{len(resp)}条', '\n'.join(resp)
                            )
    return resp


@router.get('/toutiao/get_others_lot_ids')
async def toutiao_get_others_lot_ids():
    myfastapi_logger.info('开始获取toutiao抽奖内容')
    result = await toutiaoSpaceFeedLotService.main()
    result = result if result else []
    await asyncio.to_thread(pushme, f'获取到头条抽奖{len(result)}条', '\n'.join(result)
                            )
    return result

# endregion
