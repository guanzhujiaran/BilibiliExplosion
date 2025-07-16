import asyncio

from fastapi接口.service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import GenerateTopicLotCv
from fastapi接口.service.opus新版官方抽奖.转发抽奖.提交专栏信息 import ExtractOfficialLottery
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import GenerateReserveLotCv
from fastapi接口.utils.Common import asyncio_gather

__abstract_msg = "由于代理不够+只获取了图片动态，内容不全。\n写了个网站 http://serena.dynv6.net/ （仅限ipv6访问）正在完善中\n"
__save_path = './'


async def gen_topic_cv():
    gc = GenerateTopicLotCv(
        cookie="",
        ua="",
        csrf='',
        buvid="",
        abstract=__abstract_msg
    )
    gc.save_dir = __save_path
    await gc.main()


async def gen_dynamic_cv(is_api_update: bool):
    """
    生成充电和官方抽奖的专栏
    :return:
    """
    e = ExtractOfficialLottery()
    e.save_dir = __save_path
    await e.save_article(abstract=__abstract_msg, is_api_update=is_api_update, save_dir=__save_path)


async def gen_reserve_cv(is_api_update: bool):
    gc = GenerateReserveLotCv('', '', '', '', abstract=__abstract_msg)
    await gc.main(is_api_update=is_api_update)


async def gen_all_cv(is_api_update: bool = False):
    await asyncio_gather(
        gen_topic_cv(),
        gen_dynamic_cv(is_api_update),
        gen_reserve_cv(is_api_update)
    )
    print('全部生成完成')


if __name__ == "__main__":
    asyncio.run(gen_all_cv(False))
