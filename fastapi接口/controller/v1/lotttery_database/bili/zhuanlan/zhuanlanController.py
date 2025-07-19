import asyncio

from fastapi接口.models.common import CommonResponseModel
from fastapi接口.models.v1.bili.zhuanlan import LotteryArticleResp, lotteryArticleReq, ArticleInfo
from fastapi接口.service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import GenerateTopicLotCv
from fastapi接口.service.opus新版官方抽奖.转发抽奖.提交专栏信息 import ExtractOfficialLottery
from fastapi接口.service.opus新版官方抽奖.预约抽奖.etc.submitReserveLottery import GenerateReserveLotCv
from .base import new_router

router = new_router()


@router.post(
    '/lotteryArticle',
    summary="获取专栏文章",
    response_model=CommonResponseModel[LotteryArticleResp]
)
async def get_lottery_article(body: lotteryArticleReq):
    gc_topic = GenerateTopicLotCv(cookie="", ua="", csrf='', buvid="", abstract=body.abstract_msg)

    e = ExtractOfficialLottery()
    gc_reserve = GenerateReserveLotCv('', '', '', '', abstract=body.abstract_msg)
    topic, (official, charge), reserve = await asyncio.gather(
        gc_topic.main(
            pub_cv=False,
            save_to_local_file=body.save_to_local_file
        ),
        e.save_article(
            abstract=body.abstract_msg,
            pub_cv=False,
            save_to_local_file=body.save_to_local_file
        ),
        gc_reserve.main(
            is_api_update=False,
            pub_cv=False,
            save_to_local_file=body.save_to_local_file)
    )
    return CommonResponseModel(
        data=LotteryArticleResp(
            reserve=ArticleInfo(title=reserve.title, content=reserve.manualSubmitContent),
            official=ArticleInfo(title=official.title, content=official.manualSubmitContent),
            charge=ArticleInfo(title=charge.title, content=charge.manualSubmitContent),
            topic=ArticleInfo(title=topic.title, content=topic.manualSubmitContent),
        )
    )
