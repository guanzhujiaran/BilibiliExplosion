# -*- coding: utf-8 -*-
import asyncio
import json
import os
import re
from copy import deepcopy
import bs4
import httpx
from loguru import logger
from CONFIG import CONFIG
from utl.代理.SealedRequests import my_async_httpx
from utl.代理.redisProxyRequest.RedisRequestProxy import request_with_proxy_internal
from fastapi接口.service.zhihu.zhihu_src.enc.zhuhu_enc import x_zse_93, zhi_hu_encrypt
from fastapi接口.log.base_log import zhihu_api_logger

_lock = asyncio.Lock()


class ZhihuMethod:
    current_file = os.path.dirname(os.path.abspath(__file__))
    LOG = zhihu_api_logger
    request_with_proxy = request_with_proxy_internal
    login_cookie = '_xsrf=CU2MUeK1W7Q8DUuYZ03kokwlUqoF3L6S; __zse_ck=004_4ThcbzvwtBMbzuEXaG07nxdv1kGJUGaLklvSW4EWAsdZaLKrUU0RcLkz1hAkXM0awS0ZM4Ds5SVA6o22VLvfGdWg7zqK2Tkkp0U2pPfD01RHKRH4LkMb5essE0=F3VL5-g1tVFdHc36ChatoD7fbCimZE3JLXJHtjYDzYMGokVns5ZsCkb//o2Gpr+MWomIi8xbTUv7nhzYiLmL/RG6gjKPt8eBNX0qqjb2BfoinZn06NTWb0Wa3pIOQEu+kTWFus9IDmgEDIC6UmLuONbr+rooa8yfJiIN8Jy1QgHy7njJ0=; _zap=8bec4112-691a-41aa-94c4-af37b238d268; d_c0=GPCTsuSBvhqPToPZ60eaiI7YRYylldl3iY0=|1752241333; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1752241335; HMACCOUNT=DFBE1B944ABDFA24; BEC=4589376d83fd47c9203681b16177ae43; captcha_session_v2=2|1:0|10:1752241335|18:captcha_session_v2|88:VEFXa0hVaVZXS0VqQkRGajBxUVVvaTVMTzVqMitKeW83ampvcXlOTkJGUkZuWFB5V1NKYzJWVzZxR3ltakhRVA==|709a49923965271bb69836c6ff5b86b75d77a0267b5ab5e9c0c7c89849cd2111; captcha_ticket_v2=2|1:0|10:1752241343|17:captcha_ticket_v2|728:eyJ2YWxpZGF0ZSI6IkNOMzFfWGlKZU9reEpUTHlVOUpnZVY4alY1dEZhLldMcmlpMUFjWWFNYWthdGFockNCLkhsNllQTlNzKmw1TTI0aXFmd3o4bng0Nk9XQmtJUXE1MVNDQzVRS1ZSYVJGbFZ3VDJhZzAwX1FwNU12a3cxVG1fMjB4X1FkSmhoRHVSUDZubGg5b1lJdFZPUVh5YXpJQ1U1YmhFVEhjTjUuTmwuVGwxLnBscG9ja2dDcFNoRlRuZWJOMHlWcWZ5a0tXcFMuODZ0QVI0d3oxQk1SSGZsSjlyQ3JXcG54OUQzWkk2NWxiTTI4UVc0Unc2YklCT3puNmFmUnZPUm5ELlR6cnBFYXZHbU5WUnhZVzJFOWR6UktLRGlZcVNzdzJmbmxoLkI5eDlOd0pGbWhJalhnVURJTjVwLjUwWnNwbjRSUENoTFE5ckFYQ3Z3emFhZFFFd19ma2twMVZsbHpkUmZwZnhHYTRTS0hHaXh1TERXc2xteCpuUVowRVNGWm9aekRGOUFLa01iaWVrMm9Pd1lsQ2dNdnJJYXFnV0RlOWJ0eHc2KllzKmNXMmJfclBRa1N5aEc0RTRDNUI0WGJsYXJNQW5vMmUyZ2l0cmxia2xTU1RTQnJwU0tqZXc5THFxUTlQQ21EaFZWSEg4SyouX0sxb1FpVSpuSDNKbnFZU1V2MTJ5dTZTUHc4RGNzV1k3N192X2lfMSJ9|ea5597ae302ffab5c700018661ad16a223f244273250e431a27113eb3dc7858c; z_c0=2|1:0|10:1752241356|4:z_c0|92:Mi4xZFZEd0J3QUFBQUFZOEpPeTVJRy1HaVlBQUFCZ0FsVk56R0plYVFDTnFpTkJUSnJwU2w3Z2pkcUhQcTFjbXN2Z2RB|f1a2665ab1a4b3de420ab23a72a37e766948646c6f621891cee186e109bc5666; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1752241358'
    request_headers = {
        'cookie': login_cookie,
        'x-zse-93': x_zse_93,
        'user-agent': CONFIG.rand_ua,
        'accept': '*/*',
        'x-requested-with': 'fetch'
    }

    async def __request(self,**kwargs) -> (dict, str):
        while 1:
            try:
                proxy_flag = kwargs.pop('proxy_flag') if 'proxy_flag' in list(kwargs.keys()) else False
                resp = None
                if proxy_flag:
                    req_dict = await self.request_with_proxy.request_with_proxy( **kwargs)
                    resp_text = json.dumps(req_dict)
                else:
                    resp = await my_async_httpx.request(
                        **kwargs,
                        proxies=CONFIG.custom_proxy
                    )
                    req_dict = resp.json()
                    resp_text = resp.text
                self.LOG.debug(f'{resp_text}')
                return req_dict, resp_text, resp
            except Exception as e:
                self.LOG.exception(e)
                await asyncio.sleep(10)

    async def _get_dc_0(self, headers):
        while 1:  # 这里不能动，因为这个url的resp无法转成json
            try:
                url_param = "/udid"
                zse_96 = zhi_hu_encrypt.encode('', url_param)
                headers.update({"x-zse-96": zse_96})
                async with httpx.AsyncClient(
                        proxy=CONFIG.my_ipv6_addr,
                        verify=False,
                        follow_redirects=True,
                        timeout=10
                ) as cilent:
                    resp = await cilent.post(url='https://www.zhihu.com/udid', headers=headers, )
                cookie_t = resp.cookies
                d_c0 = cookie_t.get('d_c0')
                logger.info(f"d_c0==> {d_c0}")
                return d_c0
            except Exception as e:
                self.LOG.exception(e)
                await asyncio.sleep(30)

    async def _get_headers(self, url) -> dict:
        url_host = "https://www.zhihu.com"
        url_path = url.split("?")[0].replace(url_host, "") + "?"
        url_params = url.split("?")[1]
        headers = deepcopy(self.request_headers)
        if 'd_c0' not in headers.get('cookie', ''):
            async with _lock:
                headers = deepcopy(self.request_headers)
                if 'd_c0' not in headers.get('cookie', ''):
                    d_c0 = await self._get_dc_0(headers)
                    self.request_headers.update({
                        "cookie": ' '.join([self.login_cookie, f"d_c0={d_c0};"]).strip()
                    })
                else:
                    d_c0 = ''.join(re.findall('d_c0=(.*?);', headers.get('cookie')))

        else:
            d_c0 = ''.join(re.findall('d_c0=(.*?);', headers.get('cookie')))
        encrypted_str = zhi_hu_encrypt.encode(d_c0, url_path + url_params)
        headers.update({
            "x-zse-96": encrypted_str,
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9'
        }
        )
        return headers

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
            headers.update({
                'referer': f'https://www.zhihu.com/people/{real_name}/pins'
            })
            try:
                if not headers:
                    raise Exception('headers is None')
                req_dict, resp_text, resp = await self.__request(
                    method='get',
                    url=url,
                    headers=headers,
                    proxy_flag=proxy_flag,

                )
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

    

if __name__ =="__main__":
    c =ZhihuMethod()
    res = asyncio.run(c.get_moments_pin_by_user_id('tao-guang-yang-hui-1-50',0))
    print(res)