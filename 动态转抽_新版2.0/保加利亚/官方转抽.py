# -*- coding:utf- 8 -*-
import json
import os
import random
import re
import sys
import time
from atexit import register

import numpy
import requests
# noinspection PyUnresolvedReferences
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import Bilibili_methods.all_methods



class official_Lottery:
    def __init__(self, account_choose):
        register(self.register_log_write)
        self.BAPI = None
        if not os.path.exists('./官方转抽log'):
            os.makedirs('./官方转抽log')
        self.seg_time = [3 * 60]  # 每个转发间隔时间 list类型
        self.log_path = './官方转抽log/官方转抽记录.csv'
        self.new_create_dynamic_id_path = './官方转抽log/转发的动态id记录.csv'
        self.run_path = '../待参加官方抽奖.csv'
        self.log_follow_path = './官方转抽log/官方转抽关注的人.csv'
        self.zhuanfashibai_path = './官方转抽log/转发失败.csv'
        self.username = ''
        self.cookie = gl.get_value(f'cookie{account_choose}')  # 保加利亚
        self.fullcookie = gl.get_value(f'fullcookie{account_choose}')
        self.ua = gl.get_value(f'ua{account_choose}')
        self.fingerprint = gl.get_value(f'fingerprint{account_choose}')
        self.csrf = gl.get_value(f'csrf{account_choose}')
        self.buvid3 = gl.get_value(f'buvid3_{account_choose}')
        self.headers = {}
        self.uid = ''
        self.lottery_list = []
        self.donelist = []
        self.new_create_dynamic_id = []
        self.new_followers = []
        self.first_flag = True

    def login_check(self):
        headers = {
            'User-Agent': self.ua,
            'cookie': self.cookie
        }
        url = 'https://api.bilibili.com/x/web-interface/nav'
        res = requests.get(url=url, headers=headers).json()
        if res['data']['isLogin'] == True:
            name = res['data']['uname']
            self.username = name
            self.uid = res['data']['mid']
            print(f'登录成功,当前账号用户名为{self.username}\tUID:{self.uid}')
            if not os.path.exists(f'./{self.uid}官方转抽log'):
                os.makedirs(f'./{self.uid}官方转抽log')
            return 1
        else:
            print('登陆失败,请重新登录')
            sys.exit('登陆失败,请重新登录')

    def set_headers(self, dynamic_id):
        self.headers = {
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json;charset=UTF-8',
            'cookie': self.cookie,
            'origin': 'https://t.bilibili.com',
            'referer': f'https://t.bilibili.com/{dynamic_id}?spm_id_from=444.41.0.0',
            'user-agent': self.ua
        }
        return self.headers

    def ExClimbWuzhi(self, dynamic_id):
        url = 'https://api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi'
        data = {
            "3064": 1,
            "5062": int(time.time() * 1000),
            "03bf": f"https%3A%2F%2Ft.bilibili.com%2F{dynamic_id}%3Fspm_id_from%3D444.41.0.0",
            "39c8": "",
            "34f1": "",
            "d402": "",
            "654a": "",
            "6e7c": "1920x1080",
            "3c43": {
                "2673": 0,
                "5766": 24,
                "6527": 0,
                "7003": 1,
                "807e": 1,
                "b8ce": self.ua,
                "641c": 0,
                "07a4": "zh-CN",
                "1c57": 128,
                "0bd0": 12,
                "748e": [
                    1920,
                    1080
                ],
                "d61f": [
                    1920,
                    1032
                ],
                "fc9d": -480,
                "6aa9": "Asia/Singapore",
                "75b8": 1,
                "3b21": 1,
                "8a1c": 1,
                "d52f": "not available",
                "adca": "Win32",
                "80c9": [
                    [
                        "PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Chrome PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Chromium PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "Microsoft Edge PDF Viewer",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ],
                    [
                        "WebKit built-in PDF",
                        "Portable Document Format",
                        [
                            [
                                "application/pdf",
                                "pdf"
                            ],
                            [
                                "text/pdf",
                                "pdf"
                            ]
                        ]
                    ]
                ],
                "13ab": "not available",
                "bfe9": "not available",
                "a3c1": [
                    "extensions:ANGLE_instanced_arrays;EXT_blend_minmax;EXT_color_buffer_half_float;EXT_disjoint_timer_query;EXT_float_blend;EXT_frag_depth;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;WEBKIT_EXT_texture_filter_anisotropic;EXT_sRGB;KHR_parallel_shader_compile;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_s3tc;WEBKIT_WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBKIT_WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBKIT_WEBGL_lose_context;WEBGL_multi_draw",
                    "webgl aliased line width range:[1, 1]",
                    "webgl aliased point size range:[1, 1024]",
                    "webgl alpha bits:8",
                    "webgl antialiasing:yes",
                    "webgl blue bits:8",
                    "webgl depth bits:24",
                    "webgl green bits:8",
                    "webgl max anisotropy:16",
                    "webgl max combined texture image units:32",
                    "webgl max cube map texture size:16384",
                    "webgl max fragment uniform vectors:1024",
                    "webgl max render buffer size:16384",
                    "webgl max texture image units:16",
                    "webgl max texture size:16384",
                    "webgl max varying vectors:30",
                    "webgl max vertex attribs:16",
                    "webgl max vertex texture image units:16",
                    "webgl max vertex uniform vectors:4096",
                    "webgl max viewport dims:[32767, 32767]",
                    "webgl red bits:8",
                    "webgl renderer:WebKit WebGL",
                    "webgl shading language version:WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                    "webgl stencil bits:0",
                    "webgl vendor:WebKit",
                    "webgl version:WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                    "webgl unmasked vendor:Google Inc. (AMD)",
                    "webgl unmasked renderer:ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
                    "webgl vertex shader high float precision:23",
                    "webgl vertex shader high float precision rangeMin:127",
                    "webgl vertex shader high float precision rangeMax:127",
                    "webgl vertex shader medium float precision:23",
                    "webgl vertex shader medium float precision rangeMin:127",
                    "webgl vertex shader medium float precision rangeMax:127",
                    "webgl vertex shader low float precision:23",
                    "webgl vertex shader low float precision rangeMin:127",
                    "webgl vertex shader low float precision rangeMax:127",
                    "webgl fragment shader high float precision:23",
                    "webgl fragment shader high float precision rangeMin:127",
                    "webgl fragment shader high float precision rangeMax:127",
                    "webgl fragment shader medium float precision:23",
                    "webgl fragment shader medium float precision rangeMin:127",
                    "webgl fragment shader medium float precision rangeMax:127",
                    "webgl fragment shader low float precision:23",
                    "webgl fragment shader low float precision rangeMin:127",
                    "webgl fragment shader low float precision rangeMax:127",
                    "webgl vertex shader high int precision:0",
                    "webgl vertex shader high int precision rangeMin:31",
                    "webgl vertex shader high int precision rangeMax:30",
                    "webgl vertex shader medium int precision:0",
                    "webgl vertex shader medium int precision rangeMin:31",
                    "webgl vertex shader medium int precision rangeMax:30",
                    "webgl vertex shader low int precision:0",
                    "webgl vertex shader low int precision rangeMin:31",
                    "webgl vertex shader low int precision rangeMax:30",
                    "webgl fragment shader high int precision:0",
                    "webgl fragment shader high int precision rangeMin:31",
                    "webgl fragment shader high int precision rangeMax:30",
                    "webgl fragment shader medium int precision:0",
                    "webgl fragment shader medium int precision rangeMin:31",
                    "webgl fragment shader medium int precision rangeMax:30",
                    "webgl fragment shader low int precision:0",
                    "webgl fragment shader low int precision rangeMin:31",
                    "webgl fragment shader low int precision rangeMax:30"
                ],
                "6bc5": "Google Inc. (AMD)~ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ed31": 0,
                "72bd": 0,
                "097b": 0,
                "52cd": [
                    0,
                    0,
                    0
                ],
                "a658": [
                    "Arial",
                    "Arial Black",
                    "Arial Narrow",
                    "Calibri",
                    "Cambria",
                    "Cambria Math",
                    "Comic Sans MS",
                    "Consolas",
                    "Courier",
                    "Courier New",
                    "Georgia",
                    "Helvetica",
                    "Impact",
                    "Lucida Console",
                    "Lucida Sans Unicode",
                    "Microsoft Sans Serif",
                    "MS Gothic",
                    "MS PGothic",
                    "MS Sans Serif",
                    "MS Serif",
                    "Palatino Linotype",
                    "Segoe Print",
                    "Segoe Script",
                    "Segoe UI",
                    "Segoe UI Light",
                    "Segoe UI Semibold",
                    "Segoe UI Symbol",
                    "Tahoma",
                    "Times",
                    "Times New Roman",
                    "Trebuchet MS",
                    "Verdana",
                    "Wingdings"
                ],
                "d02f": "124.04347527516074"
            },
            "54ef": "{}",
            "8b94": "https%3A%2F%2Ft.bilibili.com%2F%3Fspm_id_from%3D333.1007.0.0",
            "df35": self.buvid3,
            "07a4": "zh-CN",
            "5f45": None,
            "db46": 0
        }
        data = {'payload': json.dumps(data)}
        req = requests.post(url=url, data=json.dumps(data), headers=self.set_headers(dynamic_id))
        if req.json().get('code') == 0:
            print('log_report成功')

    def log_write(self, path, content):
        try:
            with open(path, 'a+', encoding='utf-8') as f:
                for i in content:
                    f.writelines('{}\n'.format(i))
        except:
            with open(path, 'w', encoding='utf-8') as f:
                for i in content:
                    f.writelines('{}\n'.format(i))

    def do_official_lottery(self):
        self.login_check()
        self.BAPI = Bilibili_methods.all_methods.methods()
        f = open(self.run_path, 'r', encoding='utf-8')
        try:
            q = open(f'./{self.uid}官方转抽log/参加过的官方抽奖.csv', 'r', encoding='utf-8')
        except:
            q = open(f'./{self.uid}官方转抽log/参加过的官方抽奖.csv', 'w', encoding='utf-8')
            q.close()
            q = None
        already_list = []
        if q:
            for i in q.readlines():
                already_list.append(i.strip())
            q.close()
        res = f.readlines()
        f.close()
        for i in res:
            i = i.strip()
            self.lottery_list.append(i)
        random.shuffle(self.lottery_list)
        for i in self.lottery_list:
            if i in already_list:
                print('记录过的动态id')
                continue
            with open(f'./{self.uid}官方转抽log/参加过的官方抽奖.csv', 'a+', encoding='utf-8') as q:
                q.writelines(f'{i}\n')
            if i not in self.donelist:
                print(i)
                dynamic_id = re.findall('\d+', i)[0]
                notice = self.BAPI.dynamic_lottery_notice(dynamic_id)
                time.sleep(random.choice(self.BAPI.sleeptime))
                if notice:
                    status = notice.get('data').get('status')
                    lottery_time = notice.get('data').get('lottery_time')
                    sender_uid = notice.get('data').get('sender_uid')

                    first_prize_cmt = notice.get('data').get('first_prize_cmt')
                    first_prize = notice.get('data').get('first_prize')
                    second_prize_cmt = notice.get('data').get('second_prize_cmt')
                    second_prize = notice.get('data').get('second_prize')
                    third_prize_cmt = notice.get('data').get('third_prize_cmt')
                    third_prize = notice.get('data').get('third_prize')

                    business_type = notice.get('data').get('business_type')
                    lottery_at_num = notice.get('data').get('lottery_at_num')
                    lottery_feed_limit = notice.get('data').get('lottery_feed_limit')
                    need_post = notice.get('data').get('need_post')
                    pay_status = notice.get('data').get('pay_status')

                    print(f'开奖up空间：https://space.bilibili.com/{sender_uid} 开奖时间：{self.BAPI.timeshift(lottery_time)} 开奖状态：{status}\n一等奖：{first_prize_cmt}*{first_prize}\n二等奖：{second_prize_cmt}*{second_prize}\n三等奖：{third_prize_cmt}*{third_prize}')
                    print('未知参数：')
                    print(f'business_type：{business_type}')
                    print(f'lottery_at_num：{lottery_at_num}')
                    print(f'lottery_feed_limit：{lottery_feed_limit}')
                    print(f'need_post：{need_post}')
                    print(f'pay_status：{pay_status}')
                    if lottery_time < int(time.time()):
                        print('过期抽奖')
                        time.sleep(random.choice(self.seg_time))
                        continue
                    dyn_detail = self.BAPI.get_dynamic_detail(dynamic_id, self.cookie, self.ua)
                    card_stype = dyn_detail.get('card_stype')
                    if self.first_flag:
                        #self.ExClimbWuzhi(dynamic_id)
                        self.first_flag = False
                    if dyn_detail:
                        if dyn_detail.get('relation') == 0:
                            if self.BAPI.relation_modify(1, dyn_detail.get('author_uid'), self.cookie, self.ua,
                                                         self.csrf):
                                time.sleep(10)
                                self.new_followers.append(
                                    f"https://space.bilibili.com/{dyn_detail.get('author_uid')}/dynamic")
                            else:
                                print(i)
                                exit('关注失败')
                        if dyn_detail.get('is_liked') == 1:
                            print('点过赞的动态')
                            print(i)
                            time.sleep(10)
                            continue
                        repostres = self.BAPI.js_repost_non_content_dyn(dyn_detail, dynamic_id, self.uid, self.cookie, self.ua, self.csrf,card_stype)
                        # 用的是新版的转发api
                        if repostres:
                            new_create_dynamic_id = repostres.get('dyn_id_str')
                            self.new_create_dynamic_id.append(new_create_dynamic_id)
                            self.donelist.append(i)
                            time.sleep(10)
                            self.BAPI.thumb(dynamic_id, self.cookie, self.ua, self.uid, self.csrf,card_stype)
                    else:
                        print('获取动态详情失败')
                        print(dyn_detail)
                else:
                    print('notice出错')
            time.sleep(random.choice(self.seg_time))

    def register_log_write(self):
        self.log_write(self.log_follow_path, self.new_followers)
        self.log_write(self.new_create_dynamic_id_path, self.new_create_dynamic_id)
        self.log_write(self.log_path, self.donelist)
        self.log_write(self.zhuanfashibai_path, self.BAPI.zhuanfashibai)


if __name__ == '__main__':
    a = official_Lottery(2)
    a.seg_time = numpy.linspace(10 * 60, 15 * 60, 500, endpoint=False)
    a.do_official_lottery()
    os.system("python ../../专栏抽奖/转发热门视频_保加利亚.py")
