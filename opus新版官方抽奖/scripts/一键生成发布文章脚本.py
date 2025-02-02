import asyncio

from opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import GenerateTopicLotCv
from opus新版官方抽奖.转发抽奖.提交专栏信息 import ExctractOfficialLottery
from opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import GenerateReserveLotCv

__abstract_msg = "由于代理不够+只获取了图片动态，内容不全。\n写了个网站 http://serena.dynv6.net/ （仅限ipv6访问）正在完善中，提供了一个提交数据的接口\n"


async def gen_topic_cv():
    gc = GenerateTopicLotCv(
        cookie="",
        ua="",
        csrf='',
        buvid="",
        abstract=__abstract_msg
    )
    await gc.main()


async def gen_dynamic_cv():
    e = ExctractOfficialLottery()
    await e.save_article(abstract=__abstract_msg)


async def gen_reserve_cv():
    gc = GenerateReserveLotCv('', '', '', '', abstract=__abstract_msg)
    await gc.reserve_lottery()


async def gen_all_cv():
    await asyncio.gather(
        gen_topic_cv(),
        gen_dynamic_cv(),
        gen_reserve_cv()
    )


if __name__ == "__main__":
    asyncio.run(gen_all_cv())
