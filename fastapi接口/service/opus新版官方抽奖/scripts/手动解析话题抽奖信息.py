from fastapi接口.service.opus新版官方抽奖.活动抽奖.获取话题抽奖信息 import ExtractTopicLottery
import asyncio

e = ExtractTopicLottery()


async def handle_topic_lottery_url(url, traffic_card_id):
    await e.handle_topic_lottery_url(url, traffic_card_id)


if __name__ == '__main__':
    asyncio.run(handle_topic_lottery_url('https://live.bilibili.com/blackboard/era/kGyveB9x1E1Z3nQM.html',3650))
