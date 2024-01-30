import asyncio
import typing

import httpx
from httpx import Limits
from httpx._types import RequestContent, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, RequestData


class MYASYNCHTTPX:
    def generate_httpx_proxy_from_requests_proxy(self, request_proxy: dict) -> dict:
        if request_proxy:
            return {
                'http://': request_proxy['http'],
                'https://': request_proxy['https'],
            }
        else:
            return {
                'http://': None,
                'https://': None,
            }

    async def get(self, url, headers=None, verify=False, proxies=None, timeout=10):
        async with httpx.AsyncClient(proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                                     verify=False) as client:
            resp = await client.get(url=url, headers=headers, timeout=timeout, follow_redirects=True)
            return resp

    async def post(self, url, data=None, headers=None, verify=False, proxies=None, timeout=10):
        async with httpx.AsyncClient(proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                                     verify=False) as client:
            resp = await client.post(url=url, data=data, headers=headers, timeout=timeout, follow_redirects=True)
            return resp

    async def request(self, url,
                      data: typing.Optional[RequestData] = None,
                      method='GET',
                      headers: typing.Optional[HeaderTypes] = None,
                      verify=False,
                      proxies=None,
                      timeout=10,
                      content: typing.Optional[RequestContent] = None,
                      files: typing.Optional[RequestFiles] = None,
                      json: typing.Optional[typing.Any] = None,
                      params: typing.Optional[QueryParamTypes] = None,
                      cookies: typing.Optional[CookieTypes] = None,
                      extensions: typing.Optional[dict] = None, ):
        async with httpx.AsyncClient(proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                                     verify=False) as client:
            resp = await client.request(url=url, data=data, method=method, headers=headers, timeout=timeout,
                                        content=content, files=files, json=json, params=params, cookies=cookies,
                                        extensions=extensions, follow_redirects=True)
            return resp


if __name__ == '__main__':
    MyAsyncReq = MYASYNCHTTPX()
    loop = asyncio.get_event_loop()
    task = loop.create_task(MyAsyncReq.request(method="get",
                                               url="https://api.bilibili.com/x/frontend/finger/spi",
                                               headers={
                                                   "Referer": 'https://www.bilibili.com/',
                                                   "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                                   "Cookie": "1",
                                               }, proxies={
            'https': 'http://127.0.0.1:23998',
            'http': 'http://127.0.0.1:23998',
        }))
    loop.run_until_complete(task)
    print(task.result().json())
