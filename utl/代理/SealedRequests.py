import asyncio
import copy
import random
import typing
from typing import Union

import certifi
from curl_cffi import CurlHttpVersion, CurlOpt, CurlSslVersion
from curl_cffi.requests import AsyncSession, BrowserType, ExtraFingerprints, BrowserTypeLiteral
from httpx import AsyncClient
from httpx._types import RequestContent, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, RequestData
import ssl


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

    async def get(self, url, headers=None, verify=False, proxies: Union[dict, None] = None, timeout=10, params=None,
                  *args, **kwargs):
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
        async with AsyncClient(
                proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                http2=True,
                verify=False,
        ) as client:
            client.headers.clear()
            resp = await client.get(url=url, headers=headers, params=params, timeout=timeout, follow_redirects=True)
            return resp

    async def post(self, url, data=None, headers=None, verify=False, proxies=None, timeout=10, *args, **kwargs):
        async with AsyncClient(
                proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                http2=True,
                verify=False,
        ) as client:
            client.headers.clear()
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
                      extensions: typing.Optional[dict] = None, *args, **kwargs):
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
        ca = False
        if (
                'api.bilibili.com/x/gaia-vgate/v1/register' in url or
                'api.bilibili.com/x/gaia-vgate/v1/validate' in url
        ):
            ca = sslgen()
            proxies = None
        async with AsyncClient(
                proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                verify=ca,
                http2=True,
                http1=False,
                follow_redirects=True
        ) as client:
            client.headers.clear()
            resp = await client.request(url=url, data=data, method=method, headers=headers, timeout=timeout,
                                        content=content, files=files, json=json, params=params, cookies=cookies,
                                        extensions=extensions, follow_redirects=True
                                        )
            await resp.aread()
            return resp

    async def cffi_request(self, url,
                           data: typing.Optional[RequestData] = None,
                           method='GET',
                           headers: typing.Optional[HeaderTypes] = None,
                           verify=False,
                           proxies=None,
                           timeout=10,
                           files: typing.Optional[RequestFiles] = None,
                           json: typing.Optional[typing.Any] = None,
                           params: typing.Optional[QueryParamTypes] = None,
                           cookies: typing.Optional[CookieTypes] = None,
                           *args,
                           **kwargs
                           ):
        if type(headers) is tuple:
            headers = list(headers)
        impersonate = random.choice(list(BrowserTypeLiteral.__args__))
        # fp = ExtraFingerprints(
        #     tls_min_version=CurlSslVersion.TLSv1,
        #     tls_grease=True if 'chrome' in impersonate else False,
        # )
        async with AsyncSession(
                impersonate=impersonate,
                # extra_fp=fp,
                default_headers=False,
                timeout=timeout,
                verify=False
        ) as client:
            client.headers.clear()
            resp = await client.request(url=url, data=data, method=method, headers=headers, timeout=timeout,
                                        files=files, json=json, params=params, cookies=cookies,
                                        proxies=proxies,
                                        verify=False,
                                        default_headers=False,
                                        )
        return resp


if __name__ == '__main__':
    MyAsyncReq = MYASYNCHTTPX()
    loop = asyncio.get_event_loop()
    task = loop.create_task(MyAsyncReq.request(
        method="get",
        url='https://tls.browserleaks.com/json',
        headers=
        (("Referer", 'https://www.bilibili.com/'),
         ("User-Agent",
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'),
         ("Cookie", "1"),)
    ))
    loop.run_until_complete(task)
    print(task.result().text)
