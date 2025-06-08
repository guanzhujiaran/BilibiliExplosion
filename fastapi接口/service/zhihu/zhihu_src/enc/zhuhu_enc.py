#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：config.yaml
@File    ：zhihu_encrypt.py.py
@IDE     ：PyCharm
@Author  ：Beier
@Date    ：2023/10/11 14:15
@github  ：https://github.com/srx-2000
'''
import execjs
import requests
import CONFIG
import os

# 知乎加密逻辑复现
x_zse_93 = "101_3_3.0"


class ZhiHuEncrypt:
    my_ipv6_proxy = {'http': CONFIG.CONFIG.my_ipv6_addr, "https": CONFIG.CONFIG.my_ipv6_addr}
    headers = {}

    def __init__(self):
        node = execjs.get()
        enc_js_path = os.path.join(
            os.path.dirname(__file__), '../zhihu_encrypt.js'
        )
        with open(enc_js_path, 'r', encoding='utf-8') as f:
            self.ctx = node.compile(f.read())


    def encode(self, d_c0, apiPath):
        return self.ctx.call('get_xzse96', d_c0, apiPath)

    def get_d_c0(self):
        url_param = "/udid"
        a_v = self.encode('', url_param)
        self.headers.update({"x-zse-96": '2.0_' + a_v})
        first_res = requests.post('https://www.zhihu.com/udid', data={}, headers=ZhiHuEncrypt.headers, timeout=10,
                                  proxies=ZhiHuEncrypt.my_ipv6_proxy)
        cookie_t = requests.utils.dict_from_cookiejar(first_res.cookies)
        d_c0 = cookie_t.get('d_c0')
        return d_c0

    # @staticmethod
    # def get_result(url: str):
    #     url_host = "https://www.zhihu.com"
    #     url_path = url.split("?")[0].replace(url_host, "") + "?"
    #     url_params = url.split("?")[1]
    #     d_c0 = ZhiHuEncrypt.get_d_c0()
    #     a_v = x_zse_93 + "+" + url_path + url_params + "+" + d_c0
    #     encrypted_str = ZhiHuEncrypt.encode(a_v)
    #     ZhiHuEncrypt.headers.update({"x-zse-96": '2.0_' + encrypted_str})
    #     ZhiHuEncrypt.headers.update({"cookie": f"d_c0={d_c0};"})
    #     ZhiHuEncrypt.headers.update({'accept-encoding': 'gzip, deflate',
    #                                  'accept-language': 'zh-CN,zh;q=0.9'})
    #     res = requests.get(url, headers=ZhiHuEncrypt.headers, timeout=10)
    #     logger.info(f"final_result==>{res.text}")
    #     return res.json()

    # @staticmethod
    # def get_headers(url:str)->dict:
    #     url_host = "https://www.zhihu.com"
    #     url_path = url.split("?")[0].replace(url_host, "") + "?"
    #     url_params = url.split("?")[1]
    #     d_c0 = ZhiHuEncrypt.get_d_c0()
    #     a_v = x_zse_93 + "+" + url_path + url_params + "+" + d_c0
    #     encrypted_str = ZhiHuEncrypt.encode(a_v)
    #     new_headers = {
    #         'x-zse-93': x_zse_93,
    #         'x-api-version': '3.0.91',
    #         'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    #         'x-zse-96': '2.0_',
    #         'accept': '*/*',
    #     }
    #     new_headers.update({"x-zse-96": '2.0_' + encrypted_str})
    #     new_headers.update({"cookie": f"d_c0={d_c0};"})
    #     new_headers.update({'accept-encoding': 'gzip, deflate',
    #                                  'accept-language': 'zh-CN,zh;q=0.9'})
    #     return new_headers


zhi_hu_encrypt = ZhiHuEncrypt()

if __name__ == "__main__":
    res = zhi_hu_encrypt.get_d_c0()
    print(res)
