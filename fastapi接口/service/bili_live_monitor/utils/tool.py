import datetime
import requests
from CONFIG import CONFIG
from fastapi接口.log.base_log import live_monitor_logger
from utl.代理.SealedRequests import my_async_httpx

__proxies__ = None
request_retry_times = 30


class Tool:
    @staticmethod
    def get_data_from_server() -> list[dict]:
        url = 'http://flyx.fun:1369/sync/get_users/kasfdhjakwda1qwsd15wad4q5aqfhhjc?skip=0&limit=50'
        headers = {
            "Content-Type": "application/json",
            "Connection": "close",
            'User-Agent': CONFIG.rand_ua
        }
        req: list[dict] = requests.request(method="GET", url=url, headers=headers,
                                           proxies=__proxies__).json()
        return req

    @staticmethod
    def getLotteryInfoWeb(roomid) -> dict:
        '''
        手机端抓包获取的获取直播间抽奖信息，app版本就是少个web，其他都一样
        :param roomid:
        :return:
        '''
        url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/lottery/getLotteryInfo"
        params = {
            "roomid": roomid
        }
        headers = {
            'Referer': f'https://live.bilibili.com/{roomid}', 'Connection': 'close',
            'User-Agent': CONFIG.rand_ua
        }
        req = requests.request(method="GET", url=url, headers=headers, params=params, proxies=__proxies__).json()
        return req

    @staticmethod
    def getLotteryInterfaceV1AnchorCheck(roomid) -> dict:
        '''
        单独获取天选抽奖data
        :param roomid:
        :return:
        '''
        url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/Anchor/Check"
        params = {
            "roomid": roomid
        }
        headers = {
            'Referer': f'https://live.bilibili.com/{roomid}', 'Connection': 'close',
            'User-Agent': CONFIG.rand_ua
        }
        req = requests.request(method="GET", url=url, headers=headers, params=params, proxies=__proxies__).json()
        return req

    @staticmethod
    def get_roomid_2_uid(room_id):
        url = 'https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room'
        headers = {
            'authority': 'api.live.bilibili.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'max-age=0',
            'dnt': '1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': CONFIG.rand_ua,
        }
        params = {
            'roomid': room_id,
        }
        response = requests.get(url, params=params, headers=headers,
                                proxies=__proxies__)
        req_dict = response.json()
        uid = 0
        if req_dict.get('code') == 0:
            uid = req_dict.get('data').get('info').get('uid', 0)
        else:
            live_monitor_logger.critical(f'获取room_id对应uid信息失败！响应：{req_dict}')
        return uid

    @staticmethod
    def str_2_DateTime(date_string: str, date_format: str = '%Y-%m-%dT%H:%M:%S', time_zone_offset=0) -> datetime:
        datetime_object = datetime.datetime.strptime(date_string, date_format) + datetime.timedelta(
            hours=time_zone_offset)
        return datetime_object

    @staticmethod
    def get_goldbox_data() -> list[dict]:
        url = 'http://flyx.fun:1369/sync/GOLDBOX'
        headers = {
            "Content-Type": "application/json",
            "Connection": "close",
            'User-Agent': CONFIG.rand_ua
        }
        req: list[dict] = requests.request(method="GET", url=url, headers=headers,
                                           proxies=__proxies__
                                           ).json()
        return req


class AsyncTool:

    @staticmethod
    async def get_data_from_server() -> list[dict] | None:
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = 'http://flyx.fun:1369/sync/get_users/kasfdhjakwda1qwsd15wad4q5aqfhhjc?skip=0&limit=50'
                headers = {
                    "Content-Type": "application/json",
                    "Connection": "close",
                    'User-Agent': CONFIG.rand_ua
                }
                req: list[dict] = (await my_async_httpx.request(method="GET", url=url, headers=headers,
                                                                proxies=p)).json()
                return req
            except Exception as e:
                p = CONFIG.custom_proxy
        return None

    @staticmethod
    async def RedPocketGetWinners(lot_id: int, room_id: int) -> dict:
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/popularityRedPocket/RedPocketGetWinners"
                params = {
                    "lot_id": lot_id,
                    "write_off_only": False
                }
                headers = {
                    'Referer': f'https://live.bilibili.com/{room_id}', 'Connection': 'close',
                    'User-Agent': CONFIG.rand_ua
                }
                req = (
                    await my_async_httpx.request(method="GET", url=url, headers=headers, params=params,
                                                 proxies=p)).json()
                return req
            except Exception as e:
                p = CONFIG.custom_proxy

    @staticmethod
    async def getLotteryInfoWeb(roomid) -> dict:
        '''
        手机端抓包获取的获取直播间抽奖信息，app版本就是少个web，其他都一样
        :param roomid:
        :return:
        '''
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/lottery/getLotteryInfo"
                params = {
                    "roomid": roomid
                }
                headers = {
                    'Referer': f'https://live.bilibili.com/{roomid}', 'Connection': 'close',
                    'User-Agent': CONFIG.rand_ua
                }
                req = (
                    await my_async_httpx.request(method="GET", url=url, headers=headers, params=params,
                                                 proxies=p)).json()
                return req
            except Exception as e:
                p = CONFIG.custom_proxy

    @staticmethod
    async def getLotteryInterfaceV1AnchorCheck(room_id) -> dict:
        '''
        单独获取天选抽奖data
        :param room_id:
        :return:
        '''
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = "https://api.live.bilibili.com/xlive/lottery-interface/v1/Anchor/Check"
                params = {
                    "roomid": room_id
                }
                headers = {
                    'Referer': f'https://live.bilibili.com/{room_id}', 'Connection': 'close',
                    'User-Agent': CONFIG.rand_ua
                }
                req = (
                    await my_async_httpx.request(method="GET", url=url, headers=headers, params=params,
                                                 proxies=p)).json()
                return req
            except Exception as e:
                p = CONFIG.custom_proxy

    @staticmethod
    async def get_roomid_2_uid(room_id):
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = 'https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room'
                headers = {
                    'authority': 'api.live.bilibili.com',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'cache-control': 'max-age=0',
                    'dnt': '1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': CONFIG.rand_ua,
                }
                params = {
                    'roomid': room_id,
                }
                response = await my_async_httpx.request(url, params=params, headers=headers,
                                                        proxies=p)
                req_dict = response.json()
                uid = 0
                if req_dict.get('code') == 0:
                    uid = req_dict.get('data').get('info').get('uid', 0)
                else:
                    live_monitor_logger.critical(f'获取room_id对应uid信息失败！响应：{req_dict}')
                return uid
            except Exception as e:
                p = CONFIG.custom_proxy

    @staticmethod
    def str_2_DateTime(date_string: str, date_format: str = '%Y-%m-%dT%H:%M:%S', time_zone_offset=0) -> datetime:
        datetime_object = datetime.datetime.strptime(date_string, date_format) + datetime.timedelta(
            hours=time_zone_offset)
        return datetime_object

    @staticmethod
    async def get_goldbox_data() -> list[dict] | None:
        p = __proxies__
        for _ in range(request_retry_times):
            try:
                url = 'http://flyx.fun:1369/sync/GOLDBOX'
                headers = {
                    "Content-Type": "application/json",
                    "Connection": "close",
                    'User-Agent': CONFIG.rand_ua
                }
                req: list[dict] = (await my_async_httpx.request(method="GET", url=url, headers=headers,
                                                                proxies=p
                                                                )).json()
                return req
            except Exception as e:
                p = CONFIG.custom_proxy


if __name__ == "__main__":
    ...
