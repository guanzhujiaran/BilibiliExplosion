import asyncio
import random
import typing
from typing import Union

from curl_cffi import CurlHttpVersion, CurlOpt, CurlSslVersion
from curl_cffi.requests import AsyncSession, BrowserType, ExtraFingerprints, BrowserTypeLiteral
from httpx import AsyncClient
from httpx._types import RequestContent, RequestFiles, QueryParamTypes, HeaderTypes, CookieTypes, RequestData
import ssl


class SSLFactory:
    tls_ciphers = {
        "Google Chrome": [
            # TLS 1.3 ciphers (Chrome uses a limited set of ciphers for TLS 1.3)
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            # TLS 1.2 and below ciphers
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-CHACHA20-POLY1305"
        ],
        "Mozilla Firefox": [
            # TLS 1.3 ciphers
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            # TLS 1.2 and below ciphers
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-RSA-CHACHA20-POLY1305",
            "ECDHE-RSA-AES256-GCM-SHA384"
        ],
        "Microsoft Edge": [
            # TLS 1.3 ciphers (Edge is based on Chromium, so it's similar to Chrome)
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            # TLS 1.2 and below ciphers
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-CHACHA20-POLY1305"
        ],
        "Safari (on macOS and iOS)": [
            # Safari does not support custom cipher suites configuration, but here are some commonly used ones
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-CHACHA20-POLY1305"
        ],
        "OkHttp (Android library)": [
            # OkHttp uses the system's default SSL context, which can vary by Android version
            # For newer versions, these are some common ciphers:
            "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
            "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
            "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
            "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
            "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
            "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
            "TLS_DHE_DSS_WITH_AES_128_GCM_SHA256",
            "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
            "TLS_DHE_DSS_WITH_AES_256_GCM_SHA384"
        ]
    }
    ciphers = [
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-CHACHA20-POLY1305",
        "ECDHE-RSA-CHACHA20-POLY1305",
        "ECDHE-RSA-AES128-SHA",
        "ECDHE-RSA-AES256-SHA",
        "AES128-GCM-SHA256",
        "AES256-GCM-SHA384",
        "AES128-SHA",
        "AES256-SHA"
    ]

    def __init__(self):
        pass

    @property
    def cipher_string(self):
        return ":".join(self.ciphers)

    def __call__(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        context.set_alpn_protocols(["http/2"])
        context.set_ciphers(self.cipher_string)
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
                verify=sslgen(),
                http2=True,
        ) as client:
            resp = await client.get(url=url, headers=headers, params=params, timeout=timeout, follow_redirects=True)
            return resp

    async def post(self, url, data=None, headers=None, verify=False, proxies=None, timeout=10, *args, **kwargs):
        async with AsyncClient(
                proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                verify=sslgen(),
                http2=True,
        ) as client:
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
        async with AsyncClient(
                proxies=self.generate_httpx_proxy_from_requests_proxy(proxies),
                verify=sslgen(),
                http2=True,
                http1=False,
                follow_redirects=True
        ) as client:
            client.headers.clear()
            resp = await client.request(url=url, data=data, method=method, headers=headers, timeout=timeout,
                                        content=content, files=files, json=json, params=params, cookies=cookies,
                                        extensions=extensions, follow_redirects=True,
                                        )
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
                           ):
        if type(headers) is tuple:
            headers = list(headers)
        impersonate = random.choice(list(BrowserTypeLiteral.__args__))
        fp = ExtraFingerprints(
            tls_min_version=CurlSslVersion.TLSv1_2,
            tls_grease=True if 'chrome' in impersonate else False,
        )
        async with AsyncSession(
                impersonate=BrowserType.chrome99_android,
                http_version=CurlHttpVersion.V2TLS,
                extra_fp=fp,
                default_headers=False,
                timeout=timeout
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
        url='https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&platform=web&gaia_source=main_web&rid=317195215&type=2&features=itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,commentsNewVersion&web_location=333.1368&x-bili-device-req-json=%7B%22platform%22:%22web%22,%22device%22:%22pc%22%7D&x-bili-web-req-json=%7B%22spm_id%22:%22333.1368%22%7D&w_rid=b1a89034dc09c7f56948c9c369136c02&wts=1726333426',
        headers=
        (("Referer", 'https://www.bilibili.com/'),
         ("User-Agent",
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'),
         ("Cookie", "1"),)
        , proxies={
            'https': 'http://192.168.1.7:3128',
            'http': 'http://192.168.1.7:3128',
        }))
    loop.run_until_complete(task)
    print(task.result().text)
