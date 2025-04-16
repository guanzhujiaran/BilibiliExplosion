# -*- coding: utf-8 -*-
import asyncio
import json
import os
import bs4
import httpx
from CONFIG import CONFIG
from utl.代理.SealedRequests import my_async_httpx


import utl.代理.request_with_proxy as RequestWithProxy
import fastapi接口.service.zhihu.zhihu_src.enc.zhuhu_enc as zhihu_enc
import fastapi接口.log.base_log as base_log

zhihu_api_logger = base_log.zhihu_api_logger
ZhiHuEncrypt, x_zse_93 = zhihu_enc.ZhiHuEncrypt, zhihu_enc.x_zse_93


class zhihu_method:
    current_file = os.path.dirname(os.path.abspath(__file__))
    LOG = zhihu_api_logger
    request_with_proxy = RequestWithProxy.request_with_proxy()
    request_with_proxy.channel = 'zhihu'
    my_ipv6_proxy = {'http': CONFIG.my_ipv6_addr, "https": CONFIG.my_ipv6_addr}

    async def __request(self, *args, **kwargs) -> (dict, str):
        while 1:
            try:
                proxy_flag = kwargs.pop('proxy_flag') if 'proxy_flag' in list(kwargs.keys()) else False
                resp = None
                if proxy_flag:
                    req_dict = await self.request_with_proxy.request_with_proxy(*args, **kwargs, mode='single')
                    resp_text = json.dumps(req_dict)
                else:
                    resp = await my_async_httpx.request(*args, **kwargs, proxies=self.my_ipv6_proxy)
                    req_dict = resp.json()
                    resp_text = resp.text
                self.LOG.info(f'{resp_text}')
                return req_dict, resp_text, resp
            except Exception as e:
                self.LOG.exception(e)
                await asyncio.sleep(10)

    async def _get_dc_0(self):
        while 1:  # 这里不能动，因为这个url的resp无法转成json
            try:
                url_param = "/udid"
                a_v = ZhiHuEncrypt.encode(x_zse_93 + url_param)
                ZhiHuEncrypt.headers.update({"x-zse-96": '2.0_' + a_v})
                async with httpx.AsyncClient(
                        proxy=CONFIG.my_ipv6_addr,
                        verify=False,
                ) as cilent:
                    resp = await cilent.post(url='https://www.zhihu.com/udid', headers=ZhiHuEncrypt.headers, )
                cookie_t = resp.cookies
                d_c0 = cookie_t.get('d_c0')
                # logger.info(f"d_c0==> {d_c0}")
                return d_c0
            except Exception as e:
                self.LOG.exception(e)
                await asyncio.sleep(30)

    async def _get_headers(self, url) -> dict:
        url_host = "https://www.zhihu.com"
        url_path = url.split("?")[0].replace(url_host, "") + "?"
        url_params = url.split("?")[1]
        d_c0 = await self._get_dc_0()
        a_v = x_zse_93 + "+" + url_path + url_params + "+" + d_c0
        encrypted_str = ZhiHuEncrypt.encode(a_v)
        new_headers = {
            'x-zse-93': x_zse_93,
            'x-api-version': '3.0.91',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'x-zse-96': '2.0_',
            'accept': '*/*',
        }
        new_headers.update({"x-zse-96": '2.0_' + encrypted_str})
        new_headers.update({"cookie": f"d_c0={d_c0};"})
        new_headers.update({'accept-encoding': 'gzip, deflate',
                            'accept-language': 'zh-CN,zh;q=0.9'})
        return new_headers

    async def get_moments_pin_by_user_id(self, real_name: str, offset: int, limit: int = 20, cookies='',
                                         proxy_flag=False) -> dict:
        '''
        获取知乎个人空间的想法，不包括解析json的步骤
        :param limit:
        :param proxy_flag: 是否使用代理获取resp
        :param real_name: 用户名称，url中的内容，非显示的
        :param offset: 偏移量
        :param cookies: 是否使用cookie
        :return:
        {
        "data":[...],
        "paging":{
    "is_end": false,
    "is_start": false,
    "next": "https://www.zhihu.com/api/v4/v2/pins/liangbailin/moments?includes=data%5B%2A%5D.upvoted_followees%2Cadmin_closed_comment&limit=10&offset=20",
    "previous": "https://www.zhihu.com/api/v4/v2/pins/liangbailin/moments?includes=data%5B%2A%5D.upvoted_followees%2Cadmin_closed_comment&limit=10&offset=0",
    "totals": 51
}}
        '''
        while 1:
            url = f'https://www.zhihu.com/api/v4/v2/pins/{real_name}/moments?offset={offset}&limit={limit}&includes=data[*].upvoted_followees,admin_closed_comment'
            headers = await self._get_headers(url)
            try:
                if not headers:
                    raise Exception('headers is None')
                req_dict, resp_text, resp = await self.__request(method='get', url=url, headers=headers,
                                                                 proxy_flag=proxy_flag)
                if req_dict.get('error'):
                    if req_dict.get('error').get('code') == 40352 or req_dict.get('error').get('code') == 10003:
                        zhihu_api_logger.error(f'HTTP error\n{req_dict}')
                        await asyncio.sleep(10)
                        continue
                return req_dict
            except Exception as e:
                zhihu_api_logger.error(f'请求失败！{e}\n{url}\n{headers}')
                await asyncio.sleep(10)
                continue

    async def get_pin_comment(self, pin_id: str, order_by: str, offset: int, cookie='', proxy_flag=False) -> dict:
        '''
        获取想法评论
        :param proxy_flag:
        :param cookie:
        :param pin_id:
        :param order_by: score/ts
        :param offset:
        :return:
        '''

        url = f'https://www.zhihu.com/api/v4/comment_v5/pins/{pin_id}/root_comment?order_by={order_by}&limit=20&offset={offset} '
        headers = await self._get_headers(url)
        if cookie:
            headers.update({'cookie': cookie})
        req_dict, resp_text, resp = await self.__request(method='get', url=url, headers=headers, proxy_flag=proxy_flag)
        return req_dict

    async def get_pin_detail_by_pin_id(self, pin_id: str, proxy_flag=False) -> dict:
        '''
        获取想法的具体内容
        :param proxy_flag:
        :param pin_id:
        :return:
        '''
        url = f'https://www.zhihu.com/pin/{pin_id}'
        headers = await self._get_headers(url)
        params = {
            'scene': 'pin_moments',
        }

        response = await my_async_httpx.request(method='get', url=url, params=params,
                                                headers=headers)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        initialState = json.loads(soup.select('#js-initialData')[0].text).get('initialState')
        return initialState


async def _test():
    my_zhihu = zhihu_method()
    print(await my_zhihu._get_dc_0())


if __name__ == '__main__':
    asyncio.run(_test())
