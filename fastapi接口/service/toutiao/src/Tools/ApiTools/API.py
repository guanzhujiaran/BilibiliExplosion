import asyncio
import json
import random
from enum import Enum
from urllib.parse import urlparse
from fastapi接口.service.toutiao.src.Tools.ApiTools.APIRespTool import FeedListApi
import httpx
from loguru import logger

from fastapi接口.service.toutiao.src.Tools.Enc.ToutiaoDecrypt import ToutiaoDecrypt


def retry(tries=3, interval=5):
    def decorate(func):
        async def wrapper(*args, **kwargs):
            count = 0
            func.isRetryable = False
            log = logger.bind(user=f"{args[0]}")
            while True:
                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    log.exception(f"API {urlparse(args[1]).path} 调用出现异常: {str(e)}")
                    count += 1
                    if count > tries:
                        log.exception(f"API {urlparse(args[1]).path} 调用出现异常: {str(e)}")
                        raise e
                    else:
                        # log.error(f"API {urlparse(args[1]).path} 调用出现异常: {str(e)}，重试中，第{count}次重试")
                        await asyncio.sleep(interval)
                    func.isRetryable = True
                else:
                    if func.isRetryable:
                        pass
                        # log.success(f"重试成功")
                    return result

        return wrapper

    return decorate


def get_ms_token(randomlength=107):
    """
    根据传入长度产生随机字符串
    """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789='
    length = len(base_str) - 1
    for _ in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


class APIEnum(Enum):
    api_pc_list_user_feed = 'https://www.toutiao.com/api/pc/list/user/feed'


class ToutiaoAPI:
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    }
    toutiao_decryptor = ToutiaoDecrypt()

    def __check_response(self, resp_json_str: str) -> str:
        json.loads(resp_json_str)
        return resp_json_str

    @retry()
    async def __get(self, *args, **kwargs) -> str:
        async with httpx.AsyncClient() as client:
            params = kwargs.get('params')
            if params:
                if headers := kwargs.get('headers'):
                    ua = headers.get('user-agent')
                else:
                    ua = self.headers.get('user-agent')
                params['msToken'] = get_ms_token()
                params['a_bogus'] = self.toutiao_decryptor.gen_abogus(params, ua)
                kwargs['params'] = params
            resp = await client.get(*args, **kwargs)
            return self.__check_response(resp.text)

    @retry()
    async def __post(self, *args, **kwargs) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(*args, **kwargs)
            return self.__check_response(resp.text)

    async def getUserFeed(self, user_id: str, max_behot_time: int = 0) -> FeedListApi:
        """
        获取用户粉丝勋章和直播间ID
        """
        url = APIEnum.api_pc_list_user_feed.value
        params = {
            "category": "profile_all",
            "token": user_id,
            "max_behot_time": max_behot_time,
            "aid": 24,
            "app_name": "toutiao_web",
        }
        resp = await self.__get(url, params=params, headers=self.headers)
        feed_list_api = FeedListApi(resp)
        return feed_list_api


async def _async_test():
    t = ToutiaoAPI()
    resp = await t.getUserFeed("MS4wLjABAAAAzPC55Y5v2l2OE-EHAwjyCUyQ_pP_1HFUoWe-28ttrkWJzr_AyONMq8fJs8SGGhYX")
    print(resp.RespDict)


if __name__ == "__main__":
    asyncio.run(_async_test())
