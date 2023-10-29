# coding:utf-8
import os
from CONFIG import CONFIG
# noinspection PyUnresolvedReferences
import math
import random
import re
import sys
import time
import traceback

import requests

import b站cookie.globalvar as gl


# _uuid=4610455EE-A23B-6426-367B-52A6898C6B1706899infoc; b_nut=1653669307; buvid3=AF2477C2-272A-BF16-B6F1-95FDCE2BA28C07794infoc; buvid4=0DE48A73-B1FF-C9DB-C60B-8014D47552B507794-022052800-TDIcPGmL6+BfjziClj/3KQ%3D%3D; buvid_fp_plain=undefined; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; hit-dyn-v2=1; LIVE_BUVID=AUTO1916536694166375; b_ut=5; CURRENT_BLACKGAP=0; blackside_state=0; rpdid=|(J|)kmuY|l)0J'uYlJYYml|R; nostalgia_conf=-1; deviceFingerprint=aa11154b34228952c02be1fc03600659; bsource=share_source_copy_link; CURRENT_QUALITY=116; go_old_video=-1; dy_spec_agreed=1; buvid_fp=335f7689f841284f798ac4444e2b4ec7; i-wanna-go-back=-1; i-wanna-go-feeds=2; SESSDATA=b75552f9%2C1670805451%2Cd3e86%2A61; bili_jct=9886a0b75c1e7c821716a795ea52ff72; sid=c8jd67rm; kfcSource=game_gsc; msource=game_gsc; from=cms_1690_Mibxx44kIkPp_; kfcFrom=cms_1570_MNVD3cfFISqf_; innersign=1; fingerprint3=a6c2f5054548d3cc208f5c10d9b98d48; fingerprint=fd1b18c7a3225d327328088d6eeb0e87; CURRENT_FNVAL=80; PVID=5; _dfcaptcha=65d6f7a0600d171a033cb53525b03e6a; b_lsid=F1010C10F9C_1816B350C49; bp_video_offset_1905702375=672261020211740700
class t:
    def generate_b_lsid(self):
        def o(e):
            return hex(math.ceil(e))[2:].upper()

        def a(e):
            _t = ""
            for i in range(e):
                tep = 16 * random.random()
                print(tep)
                _t += o(tep)
            return s(_t, e)

        def s(e, _t):
            n = ""
            if len(e) < _t:
                for r in range(_t - len(e)):
                    n += "0"
            return n + e

        return a(8)

    def common_cookie_parse(self, cookie):
        c_s = cookie.split(';')
        c_d = dict()
        for i in c_s:
            if i != '' and i != ' ':
                try:
                    k = i.strip().split('=')[0].strip()
                    v = i.strip().split('=')[1].strip()
                except:
                    print(c_s)
                    traceback.print_exc()
                    exit('common_cookie_parse_failed')
                if k == "b_timer":
                    continue
                c_d.update({k: v})
        t = ''
        # for i, j in c_d.items():
        #     if i == 'fingerprint' or i == 'sid' or i == 'DedeUserID' or i == 'DedeUserID__ckMd5' or i == 'SESSDATA' or i == 'bili_jct' or i == '_uuid' or i == 'b_nut' or i == 'fingerprint3' or i == '_dfcaptcha' or i == 'b_lsid' \
        #             or i == 'l' or i == 'buvid3' or i == 'buvid4' or i == 'buvid_fp_plain' or i == 'hit-dyn-v2' or i == 'rpdid' or i == 'deviceFingerprint' or i == 'CURRENT_QUALITY' \
        #             or i == 'go_old_video' or i == 'dy_spec_agreed' or i == 'b_ut' or i == 'canvasFp' or i == 'feSign' or i == 'screenInfo' or i == 'webglFp' or i == '_fmdata' \
        #             or i == '_xid' or i == 'buvid_fp' or i == 'fingerprint3' or i == 'fingerprint' or i == '_dfcaptcha' or i == 'LIVE_BUVID':
        for i, j in c_d.items():
            if i == 'sid' or i == 'DedeUserID' or i == 'DedeUserID__ckMd5' or i == 'SESSDATA' or i == 'bili_jct' or i == 'buvid_fp' or i == 'buvid4' or i == 'lsid':
                if i == 'b_nut':
                    if int(time.time() - j) > 94608:
                        print('cookie中b_nut超时了，最好重新获取cookie')
                        t += '{}={}; '.format(i, j)
                elif i == 'b_lsid':
                    try:
                        b_lsid_time = re.findall('_(.*)', j)[0]
                    except:
                        print('cookie中b_lsid超时了，最好重新获取cookie')
                        b_lsid_time = '1816D3F1635'

                    if int(b_lsid_time, 16) / 1000 - int(time.time()) > 5400:
                        print('cookie中b_lsid已过期，重新生成')
                        new_b_lsid = self.generate_b_lsid()
                        new_b_lsid += '_{}'.format(hex(int(time.time() * 1000))[2:].upper())
                        t += '{}={}; '.format(i, new_b_lsid)
                        print('新b_lsid:', new_b_lsid)
                    else:
                        t += '{}={}; '.format(i, j)
                else:
                    t += '{}={}; '.format(i, j)
            else:
                t += '{}={}; '.format(i, j)
        return t

    def watch_cookie_parse(self, cookie, ua):
        c_s = cookie.split(';')
        c_d = dict()
        buvidgroup = dict()
        for i in c_s:
            if i != '':
                k = i.split('=')[0].strip()
                v = i.split('=')[1].strip()
                if k == "b_timer":
                    continue
                c_d.update({k: v})
        t = ''
        for i, j in c_d.items():
            if i == '_uuid' or i == 'b_lsid' or i == 'b_nut' or i == 'bili_jct' or i == 'blackside_state' or i == 'buvid_fp' or i == 'buvid_fp_plain' \
                    or i == 'CURRENT_BLACKGAP' or i == 'CURRENT_FNVAL' or i == 'DedeUserID' or i == 'DedeUserID__ckMd5' or i == 'fingerprint' \
                    or i == 'fingerprint3' or i == 'hit-dyn-v2' or i == 'LIVE_BUVID' or i == 'nostalgia_conf' or i == 'PVID' or i == 'rpdid' or i == 'SESSDATA' or i == 'sid':
                if i == 'b_nut':
                    t += '{}={}; '.format(i, j)
                # elif i=='b_lsid':
                #     try:
                #         b_lsid_time=re.findall('_(.*)', j)[0]
                #     except:
                #         print('cookie中b_lsid定义出错')
                #         b_lsid_time='1816D3F1635'
                #     if int(b_lsid_time, 16)/1000-int(time.time())>5400:
                #         new_b_lsid=''
                #         for i in range(8):
                #             new_b_lsid+=random.choice(['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'])
                #         new_b_lsid += '_{}'.format(hex(int(time.time()*1000))[2:].upper())
                #         t += '{}={}; '.format(i, new_b_lsid)
                #     else:
                #         t += '{}={}; '.format(i, j)
                elif i == 'buvid3' or i == 'buvid4':
                    if c_d.get(i) is None:
                        if buvidgroup.get(i) is None:
                            buvidgroup = self.getBuvidGroupLoadingIns(cookie, ua)
                            t += '{}={}; '.format(i, buvidgroup.get(i))
                        else:
                            t += '{}={}; '.format(i, buvidgroup.get(i))
                    else:
                        t += '{}={}; '.format(i, c_d.get(i))
                else:
                    t += '{}={}; '.format(i, j)
        return t

    def get_tianxuancookie(self, cookie, ua):
        c_s = cookie.split(';')
        c_d = dict()
        buvidgroup = dict()
        for i in c_s:
            if i != '':
                k = i.split('=')[0].strip()
                v = i.split('=')[1].strip()
                if k == "b_timer":
                    continue
                c_d.update({k: v})
        t = ''
        for i, j in c_d.items():
            if i == 'buvid3	' or i == 'i-wanna-go-back' or i == '_uuid' or i == 'buvid4' or i == 'fingerprint' or i == 'sid' \
                    or i == 'buvid_fp_plain' or i == 'DedeUserID' or i == 'DedeUserID__ckMd5' or i == 'SESSDATA' or i == 'bili_jct' or i == 'b_ut' or i == 'buvid_fp' \
                    or i == 'nostalgia_conf' or i == '_dfcaptcha' or i == 'LIVE_BUVID' or i == 'CURRENT_BLACKGAP' or 'Hm_lvt' in i \
                    or 'Hm_lpvt' in i or i == 'b_lsid' or i == 'blackside_state' or i == 'rpdid' or i == 'CURRENT_FNVAL' \
                    or i == 'innersign' or i == 'PVID':
                # if i=='b_lsid':
                #     try:
                #         b_lsid_time=re.findall('_(.*)', j)[0]
                #     except:
                #         print('cookie中b_lsid定义出错')
                #         exit('cookie中b_lsid定义出错，请重新获取cookie')
                #         return
                #     if int(b_lsid_time, 16)/1000-int(time.time())>5400:
                #         exit('cookie中b_lsid超时了，请重新获取cookie')
                #     new_b_lsid=''
                #     for i in range(8):
                #         new_b_lsid+=random.choice(['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'])
                #     new_b_lsid += '_{}'.format(hex(int(time.time()*1000))[2:].upper())
                #     t += '{}={}; '.format(i, new_b_lsid)
                # else:
                #     t += '{}={}; '.format(i, j)
                if i == 'buvid3' or i == 'buvid4':
                    if c_d.get(i) is None:
                        if buvidgroup.get(i) is None:
                            buvidgroup = self.getBuvidGroupLoadingIns(cookie, ua)
                            t += '{}={}; '.format(i, buvidgroup.get(i))
                        else:
                            t += '{}={}; '.format(i, buvidgroup.get(i))
                    else:
                        t += '{}={}; '.format(i, c_d.get(i))
                else:
                    t += '{}={}; '.format(i, j)
        return t

    def get_csrf(self, cookie):
        c_s = cookie.split(';')
        for i in c_s:
            if i != '':
                k = i.split('=')[0].strip()
                v = i.split('=')[1].strip()
                if k == "bili_jct":
                    return v

    def get_buvid3_from_cookie(self, cookie):
        c_s = cookie.split(';')
        for i in c_s:
            if i != '':
                k = i.split('=')[0].strip()
                v = i.split('=')[1].strip()
                if k == "buvid3":
                    return v

    def get_fingerprint(self, cookie):
        c_s = cookie.split(';')
        for i in c_s:
            if i != '':
                k = i.split('=')[0].strip()
                v = i.split('=')[1].strip()
                if k == "fingerprint":
                    return v

    def getBuvidGroupLoadingIns(self, cookie, ua):
        url = 'https://api.bilibili.com/x/frontend/finger/spi'
        headers = {
            'cookie': cookie,
            'user-agent': ua
        }
        req = requests.get(url=url, headers=headers)
        return {'buvid3': req.json().get('data').get('b_3'), 'buvid4': req.json().get('data').get('b_4')}

    def read_cookie(self, cookie_file_name):
        with open(CONFIG.root_dir+f'b站cookie/cookie_path/{cookie_file_name}', 'r', encoding='utf-8') as f:
            return ''.join(f.readlines()).strip()

    def write_cookie(self, now_cookie, cookie_file_name):
        with open(CONFIG.root_dir+f'b站cookie/cookie_path/{cookie_file_name}', 'w', encoding='utf-8') as f:
            f.writelines(now_cookie)

    def random_hex(self, num):
        s = ''
        for i in range(num):
            s += hex(int(random.random() * 16))[-1:]
        return s


cookie_file_name_list = os.listdir(CONFIG.root_dir+'b站cookie/cookie_path')
cookie_file_name_list=sorted(cookie_file_name_list,key=lambda x:int(x[6:-4]))
print(cookie_file_name_list)
t = t()
ua_list = [
    "Mozilla/5.0 BiliDroid/6.90.0 (bbcallen@gmail.com) os/android model/oneplus 6 mobi_app/android build/6900400 channel/html5_search_baidu innerVer/6900410 osVer/6.0.1 network/2",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
]
device_id_list = [
    '9261a91baf687aeb06e6f3afa996b73f',
    '01d5d01ce73b05decc681bd5ac0a92ec',
    '2f4443bf7125070ab1d987d8a49f2a77',
    'e9af00424a3ad80b0c48ff314c8a89e6'
]
for i in range(1, len(cookie_file_name_list) + 1):
    exec(f"fullcookie{i}=t.read_cookie(cookie_file_name_list[{i - 1}])")
    exec(f"cookie{i} = t.common_cookie_parse(fullcookie{i})")  # 星瞳
    exec(f"t.write_cookie(cookie{i},cookie_file_name_list[{i - 1}])")
    try:
        ua_list[i-1]
        exec(f"ua{i} = ua_list[{i - 1}]")
    except:
        exec(f"ua{i} = ua_list[{-1}]")
    exec(f"fingerprint{i} = t.get_fingerprint(fullcookie{i})")
    exec(f"csrf{i} = t.get_csrf(fullcookie{i})")
    exec(f"watch_cookie{i} = t.watch_cookie_parse(fullcookie{i}, ua{i})")
    try:
        temp_dvid = device_id_list[i - 1]
    except:
        temp_dvid = t.random_hex(32)
    exec(f"device_id{i} = temp_dvid")
    exec(f"tianxuan_cookie{i} = t.get_tianxuancookie(fullcookie{i}, ua{i})")
    exec(f"buvid3_{i} = t.get_buvid3_from_cookie(fullcookie{i})")

    exec(f"gl.set_value('cookie{i}', cookie{i})")
    exec(f"gl.set_value('fullcookie{i}', fullcookie{i})")
    exec(f"gl.set_value('ua{i}', ua{i})")
    exec(f"gl.set_value('fingerprint{i}', fingerprint{i})")
    exec(f"gl.set_value('csrf{i}', csrf{i})")
    exec(f"gl.set_value('watch_cookie{i}', watch_cookie{i})")
    exec(f"gl.set_value('device_id{i}', device_id{i})")
    exec(f"gl.set_value('buvid3_{i}', buvid3_{i})")

# fullcookie2 = t.read_cookie('cookie2')
# cookie2 = t.common_cookie_parse(fullcookie2)  # 保加利亚
# t.write_cookie(cookie2,'cookie2')
# ua2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
# watch_cookie2 = t.watch_cookie_parse(fullcookie2, ua2)
# fingerprint2 = t.get_fingerprint(fullcookie2)
# csrf2 = t.get_csrf(fullcookie2)
# uid2 = "9295261"  # 保加利亚
# uname2 = '保加利亚人妖王'
# tianxuan_cookie2 = t.get_tianxuancookie(fullcookie2, ua2)
# device_id2 = '01d5d01ce73b05decc681bd5ac0a92ec'
# buvid3_2 = t.get_buvid3_from_cookie(fullcookie2)
#
# fullcookie3 = t.read_cookie('cookie3')
# cookie3 = t.common_cookie_parse(fullcookie3)  # 斯卡蒂
# t.write_cookie(cookie3,'cookie3')
# ua3 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
# watch_cookie3 = t.watch_cookie_parse(fullcookie3, ua3)
# fingerprint3 = t.get_fingerprint(fullcookie3)
# csrf3 = t.get_csrf(fullcookie3)
# uid3 = "1905702375"  # 斯卡蒂
# uname3 = '斯卡蒂天下第一T_T'
# share_cookie3 = "_uuid=4610455EE-A23B-6426-367B-52A6898C6B1706899infoc; buvid4=0DE48A73-B1FF-C9DB-C60B-8014D47552B507794-022052800-TDIcPGmL6+BfjziClj/3KQ%3D%3D; buvid3=AF2477C2-272A-BF16-B6F1-95FDCE2BA28C07794infoc; b_nut=1653669307; buvid_fp_plain=undefined; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; hit-dyn-v2=1; buvid_fp=f2d7c8fcd0a23b093d4c3c918d0c3020; LIVE_BUVID=AUTO1916536694166375; b_ut=5; CURRENT_BLACKGAP=0; blackside_state=0; rpdid=|(J|)kmuY|l)0J'uYlJYYml|R; nostalgia_conf=-1; deviceFingerprint=aa11154b34228952c02be1fc03600659; bsource=share_source_copy_link; CURRENT_QUALITY=116; fingerprint=2cffa3406e26229951c005093e1245f8; fingerprint3=6e22edae9b7380c416fdb1f04b006661; go_old_video=-1; i-wanna-go-back=-1; i-wanna-go-feeds=2; SESSDATA=369ed751%2C1670060796%2C43010%2A61; bili_jct=ccee4156bc387c09e02dac48e4fe4422; sid=l24cqsjk; b_lsid=5D133879_18138903D7F; CURRENT_FNVAL=80; innersign=0; PVID=7"
# tianxuan_cookie3 = t.get_tianxuancookie(fullcookie3, ua3)
# device_id3 = '2f4443bf7125070ab1d987d8a49f2a77'
# buvid3_3 = t.get_buvid3_from_cookie(fullcookie3)
#
# fullcookie4 = t.read_cookie('cookie4')
# cookie4 = t.common_cookie_parse(fullcookie4)  # 墨色
# t.write_cookie(cookie4,'cookie4')
# ua4 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
# fingerprint4 = t.get_fingerprint(fullcookie4)
# csrf4 = t.get_csrf(fullcookie4)
# uid4 = "1178256718"  # 墨色
# uname4 = '墨色烟火QWQ'
# watch_cookie4 = t.watch_cookie_parse(fullcookie4, ua4)
# tianxuan_cookie4 = t.get_tianxuancookie(fullcookie4, ua4)
# device_id4 = 'e9af00424a3ad80b0c48ff314c8a89e6'
# buvid3_4 = t.get_buvid3_from_cookie(fullcookie4)

# gl.set_value('uname1', uname1)
# gl.set_value('cookie1', cookie1)
# gl.set_value('fullcookie1', fullcookie1)
# gl.set_value('ua1', ua1)
# gl.set_value('fingerprint1', fingerprint1)
# gl.set_value('csrf1', csrf1)
# gl.set_value('uid1', uid1)
# gl.set_value('watch_cookie1', watch_cookie1)
# gl.set_value('device_id1', device_id1)
# gl.set_value('buvid3_1', buvid3_1)
#
# gl.set_value('uname2', uname2)
# gl.set_value('cookie2', cookie2)
# gl.set_value('fullcookie2', fullcookie2)
# gl.set_value('ua2', ua2)
# gl.set_value('fingerprint2', fingerprint2)
# gl.set_value('csrf2', csrf2)
# gl.set_value('uid2', uid2)
# gl.set_value('watch_cookie2', watch_cookie2)
# gl.set_value('tianxuan_cookie2', tianxuan_cookie2)
# gl.set_value('device_id2', device_id2)
# gl.set_value('buvid3_2', buvid3_2)
#
# gl.set_value('uname3', uname3)
# gl.set_value('cookie3', cookie3)
# gl.set_value('fullcookie3', fullcookie3)
# gl.set_value('ua3', ua3)
# gl.set_value('fingerprint3', fingerprint3)
# gl.set_value('csrf3', csrf3)
# gl.set_value('uid3', uid3)
# gl.set_value('watch_cookie3', watch_cookie3)
# gl.set_value('share_cookie3', share_cookie3)
# gl.set_value('tianxuan_cookie3', tianxuan_cookie3)
# gl.set_value('device_id3', device_id3)
# gl.set_value('buvid3_3', buvid3_3)
#
# gl.set_value('uname4', uname4)
# gl.set_value('cookie4', cookie4)
# gl.set_value('fullcookie4', fullcookie4)
# gl.set_value('ua4', ua4)
# gl.set_value('fingerprint4', fingerprint4)
# gl.set_value('csrf4', csrf4)
# gl.set_value('uid4', uid4)
# gl.set_value('watch_cookie4', watch_cookie4)
# gl.set_value('tianxuan_cookie4', tianxuan_cookie4)
# gl.set_value('device_id4', device_id4)
# gl.set_value('buvid3_4', buvid3_4)
