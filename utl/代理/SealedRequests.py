import asyncio
import random
import ssl
import typing
from typing import Union

from curl_cffi import Response, CurlHttpVersion, BrowserTypeLiteral, requests
# from httpx import AsyncClient
from httpx._types import RequestContent, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, RequestData

from utl.代理.数据库操作.comm import get_scheme_ip_port_form_proxy_dict


class SSLFactory:
    @property
    def bili_cipher(self):
        base_cipher = [
            'ECDHE-RSA-AES128-GCM-SHA256'
        ]
        cipher_suites = [
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "DHE-RSA-AES128-GCM-SHA256",
            "DHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES128-SHA256",
            "ECDHE-RSA-AES256-SHA384",
            "DHE-RSA-AES128-SHA256",
            "DHE-RSA-AES256-SHA256",
            "DHE-RSA-AES256-SHA384",
            "DHE-RSA-AES128-CCM",
            "DHE-RSA-AES256-CCM",
            "DHE-RSA-AES128-CCM8",
            "ECDHE-RSA-CHACHA20-POLY1305",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "DHE-RSA-CHACHA20-POLY1305",
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_CCM_SHA256",
            "TLS_AES_128_CCM_8_SHA256",
        ]
        for i in range(random.choice(range(4))):
            base_cipher.append(cipher_suites.pop(random.choice(range(len(cipher_suites)))))
        common_cipher = ['ECDH+AESGCM',
                         'ECDH+CHACHA20',
                         'DH+AESGCM',
                         'DH+CHACHA20',
                         'ECDH+AES256',
                         'DH+AES256',
                         'ECDH+AES128',
                         'DH+AES',
                         'ECDH+HIGH',
                         'DH+HIGH',
                         'RSA+AESGCM',
                         'RSA+AES',
                         'RSA+HIGH']
        random.shuffle(common_cipher)
        return ':'.join(common_cipher) + ":" + ':'.join(
            base_cipher) + ":!aNULL:!eNULL:!MD5"

    def __call__(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.set_alpn_protocols(["h2"])
        context.set_ciphers(self.bili_cipher)
        return context


sslgen = SSLFactory()
asyncio_timeout = 60


def format_transport(request_proxy: dict | None):
    # if format_ip_str := get_scheme_ip_port_form_proxy_dict(request_proxy):
    #     if 'sock' in format_ip_str or 'socks' in format_ip_str:
    #         return AsyncProxyTransport.from_url(
    #             url=format_ip_str,
    #         )
    return None


def format_httpx_proxy(request_proxy: dict | None) -> str | None:
    if not request_proxy:
        return None
    if format_ip_str := get_scheme_ip_port_form_proxy_dict(request_proxy):
        return format_ip_str
    else:
        return None


# class MYASYNCHTTPX:
#     async def get(self, url, headers=None, verify=False, proxies: Union[dict, None] = None, timeout=10, params=None,
#                   *args, **kwargs):
#         """
#
#         :param url:
#         :param headers:
#         :param verify:
#         :param proxies: like {
#             'http':'http://1.1.1.1',
#             'https':'http://1.1.1.1'
#         }
#         :param timeout:
#         :param params:
#         :param args:
#         :param kwargs:
#         :return:
#         """
#         format_proxy_str = format_httpx_proxy(proxies)
#         async with AsyncClient(
#                 transport=format_transport(proxies),
#                 proxy=format_proxy_str,
#                 http2=True,
#                 verify=True,
#                 timeout=timeout
#         ) as client:
#             client.headers.clear()
#             resp = await asyncio.wait_for(
#                 client.get(url=url, headers=headers, params=params, timeout=timeout, follow_redirects=True,
#                            ),
#                 timeout=asyncio_timeout)
#             return resp
#
#     async def post(self, url, data=None, headers=None, verify=False, proxies=None, timeout=10, *args, **kwargs):
#         format_proxy_str = format_httpx_proxy(proxies)
#         async with AsyncClient(
#                 transport=format_transport(proxies),
#                 proxy=format_proxy_str,
#                 http2=True,
#                 verify=True,
#                 timeout=timeout
#         ) as client:
#             client.headers.clear()
#             resp = await asyncio.wait_for(
#                 client.post(url=url, data=data, headers=headers, timeout=timeout, follow_redirects=True),
#                 timeout=asyncio_timeout
#             )
#             return resp
#
#     async def request(self, url,
#                       data: typing.Optional[RequestData] = None,
#                       method='GET',
#                       headers: typing.Optional[HeaderTypes] = None,
#                       verify=False,
#                       proxies=None,
#                       timeout=10,
#                       content: typing.Optional[RequestContent] = None,
#                       files: typing.Optional[RequestFiles] = None,
#                       json: typing.Optional[typing.Any] = None,
#                       params: typing.Optional[QueryParamTypes] = None,
#                       cookies: typing.Optional[CookieTypes] = None,
#                       extensions: typing.Optional[dict] = None, *args, **kwargs):
#         """
#
#         :param url:
#         :param data:
#         :param method:
#         :param headers:
#         :param verify:
#         :param proxies: {"http":"xxx.xxx.xxx.xxx", "https":"xxx.xxx.xxx.xxx"}
#         :param timeout:
#         :param content:
#         :param files:
#         :param json:
#         :param params:
#         :param cookies:
#         :param extensions:
#         :return:
#         """
#         ca = True
#         if (
#                 'api.bilibili.com/x/gaia-vgate/v1/register' in url or
#                 'api.bilibili.com/x/gaia-vgate/v1/validate' in url
#         ):
#             ca = sslgen()
#             format_proxy_str = None
#             format_transport_ins = None
#         else:
#             format_proxy_str = format_httpx_proxy(proxies)
#             format_transport_ins = format_transport(proxies)
#         async with AsyncClient(
#                 transport=format_transport_ins,
#                 proxy=format_proxy_str,
#                 verify=ca,
#                 http2=True,
#                 http1=False,
#                 follow_redirects=True,
#                 timeout=timeout
#         ) as client:
#             client.headers.clear()
#             resp = await asyncio.wait_for(
#                 client.request(url=url, data=data, method=method, headers=headers, timeout=timeout,
#                                content=content, files=files, json=json, params=params, cookies=cookies,
#                                extensions=extensions, follow_redirects=True
#                                ),
#                 timeout=asyncio_timeout
#             )
#             return resp
#

class MYASYNCHTTPX:
    def __init__(self):
        self.session = requests.AsyncSession(
            max_clients=1000,
            allow_redirects=True,
            timeout=30,
            verify=True,
            trust_env=True,
            impersonate="chrome",
            http_version=CurlHttpVersion.V2_0,
        )

    async def get(self, url, headers=None, verify=False, proxies: Union[dict, None] = None, timeout=10, params=None,
                  *args, **kwargs) -> Response:
        """

        :param url:
        :param headers:
        :param verify:
        :param proxies: like {
            'http':'http://1.1.1.1',
            'https':'http://1.1.1.1'
        }
        :param timeout:
        :param params:
        :param args:
        :param kwargs:
        :return:
        """
        format_proxy_str = format_httpx_proxy(proxies)
        if type(headers) is tuple:
            headers = list(headers)
        impersonate = random.choice(list(BrowserTypeLiteral.__args__))
        resp = await self.session.get(url=url,
                                      # headers=headers,
                                      timeout=timeout,
                                      params=params,
                                      proxy=format_proxy_str,
                                      verify=False,
                                      # default_headers=False,
                                      impersonate=impersonate
                                      )
        return resp

    async def post(self, url, data=None, headers=None, verify=False, proxies: dict = None, timeout=10,
                   json: dict | list | None = None, *args, **kwargs) -> Response:
        format_proxy_str = format_httpx_proxy(proxies)
        if type(headers) is tuple:
            headers = list(headers)
        impersonate = random.choice(list(BrowserTypeLiteral.__args__))
        resp = await self.session.post(url=url, data=data, headers=headers, timeout=timeout,
                                       proxy=format_proxy_str,
                                       verify=False,
                                       default_headers=False,
                                       json=json,
                                       impersonate=impersonate
                                       )
        return resp

    async def request(self, url,
                      data: typing.Optional[RequestData] = None,
                      method: typing.Literal[
                          "GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "TRACE", "PATCH", "QUERY"] = 'GET',
                      headers: typing.Optional[HeaderTypes] = None,
                      verify=False,
                      proxies=None,
                      timeout=10,
                      content: typing.Optional[RequestContent] = None,
                      files: typing.Optional[RequestFiles] = None,
                      json: typing.Optional[typing.Any] = None,
                      params: typing.Optional[QueryParamTypes] = None,
                      cookies: typing.Optional[CookieTypes] = None,
                      extensions: typing.Optional[dict] = None, *args, **kwargs) -> Response:
        """

        :param url:
        :param data:
        :param method:
        :param headers:
        :param verify:
        :param proxies: {"http":"xxx.xxx.xxx.xxx", "https":"xxx.xxx.xxx.xxx"}
        :param timeout:
        :param content:
        :param files:
        :param json:
        :param params:
        :param cookies:
        :param extensions:
        :return:
        """
        if (
                'api.bilibili.com/x/gaia-vgate/v1/register' in url or
                'api.bilibili.com/x/gaia-vgate/v1/validate' in url
        ):
            format_proxy_str = None
        else:
            format_proxy_str = format_httpx_proxy(proxies)
        if type(headers) is tuple:
            headers = list(headers)
        impersonate = random.choice(list(BrowserTypeLiteral.__args__))
        resp = await self.session.request(url=url,
                                          data=data,
                                          method=method,
                                          headers=headers,
                                          timeout=timeout,
                                          files=files, json=json, params=params, cookies=cookies,
                                          proxy=format_proxy_str,
                                          verify=False,
                                          default_headers=False,
                                          impersonate=impersonate
                                          )
        return resp


my_async_httpx = MYASYNCHTTPX()
if __name__ == '__main__':
    MyAsyncReq = MYASYNCHTTPX()
    loop = asyncio.get_event_loop()
    task = loop.create_task(MyAsyncReq.request(
        method="get",
        url='https://test.ipw.cn',
        headers=
        (("Referer", 'https://www.bilibili.com/'),
         ("User-Agent",
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'),
         ("Cookie", "1"),),
        proxies={"sock4": "socks4://1.10.133.155:4145", "socks4": "socks4://1.10.133.155:4145"}
    )
    )
    loop.run_until_complete(task)
    print(task.result().text)
