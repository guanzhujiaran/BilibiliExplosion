# -*- coding:utf- 8 -*-
import asyncio
import json
import math
import random
import time
import urllib.parse

import requests


async def handleSelfDefReport(eventname: str, url: str, cookie: str, ua: str, ptype=1,
                              target_url='', screenx=2560, screeny=1440, abtest='{}',
                              language='zh-CN', laboratory='null', is_selfdef=1, refer_url='',**ops) -> list:
    """
    # ptype platform_type 指平台类型 手机为2 电脑为1
      点击“同时转发到我的动态”时不记录log

    # 指定 eventname 为 dynamic_pv：浏览动态
    #                  dynamic_thumb：点赞动态
    #
    """
    msg_queue = []

    def get_lsid(full_ck):
        c_s = full_ck.split(';')
        for i in c_s:
            i = i.strip()
            if i != '':
                try:
                    k = i.split('=')[0].strip()
                    v = i.split('=')[1].strip()
                except:
                    print('log_reporter_get_lsid_failed')
                    print(i)
                    exit('log_reporter_get_lsid_failed')
                if k == "b_lsid":
                    return v
        new_b_lsid = ''
        for i in range(8):
            new_b_lsid += random.choice(['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'])
        new_b_lsid += '_{}'.format(hex(int(time.time() * 1000))[2:].upper())
        return new_b_lsid

    def get_buvid_fp(full_ck):
        c_s = full_ck.split(';')
        for i in c_s:
            i = i.strip()
            if i != '':
                try:
                    k = i.split('=')[0].strip()
                    v = i.split('=')[1].strip()
                except:
                    print('log_reporter_get_buvid_fp_failed')
                    print(i)
                    exit('log_reporter_get_buvid_fp_failed')
                if k == "buvid_fp":
                    return v

    def get_buvid_4(full_ck):
        c_s = full_ck.split(';')
        c_d = dict()
        buvidgroup = dict()
        for i in c_s:
            i=i.strip()
            if i != '':
                try:
                    k = i.split('=')[0].strip()
                    v = i.split('=')[1].strip()
                except:
                    print('log_reporter_get_buvid_4_failed')
                    print(i)
                    exit('log_reporter_get_buvid_4_failed')
                if k == "b_timer":
                    continue
                c_d.update({k: v})
        for i, j in c_d.items():
            if i == 'buvid4':
                if c_d.get(i) is None:
                    if buvidgroup.get(i) is None:
                        buvidgroup = getBuvidGroupLoadingIns(cookie, ua)
                        return buvidgroup.get(i).replace('%3D', '=')
                    else:
                        return buvidgroup.get(i).replace('%3D', '=')
                else:
                    return c_d.get(i).replace('%3D', '=')

    def get_b_nut(full_ck):
        c_s = full_ck.split(';')
        for i in c_s:
            i = i.strip()
            if i != '':
                try:
                    k = i.split('=')[0].strip()
                    v = i.split('=')[1].strip()
                except:
                    print('log_reporter_get_b_nut_failed')
                    print(i)
                    exit('log_reporter_get_b_nut_failed')
                if k == "b_nut":
                    return v

        return 1660454474

    def getBuvidGroupLoadingIns(_cookie, _ua):
        url = 'https://api.bilibili.com/x/frontend/finger/spi'
        headers = {
            'cookie': _cookie,
            'user-agent': _ua
        }
        req = requests.get(url=url, headers=headers)
        return {'buvid3': req.json().get('data').get('b_3'), 'buvid4': req.json().get('data').get('b_4')}

    def generate_uuid():
        def a(_e):
            _t = ''
            for _n in range(_e):
                _t += o(16 * random.random())
            return s(_t, _e)

        def o(_e):
            ret = hex(math.ceil(_e))[2:].upper()
            if ret == '10':
                return 'A'
            return ret

        def s(_e, _t):
            _n = ''
            if len(_e) < _t:
                for _r in range(_t - len(_e) + 1):
                    _n += '0'
            return _n + _e

        e = a(8)
        t = a(4)
        n = a(4)
        r = a(4)
        o = a(12)
        _i = int(time.time() * 1000)
        return e + "-" + t + "-" + n + "-" + r + "-" + o + s(str(int(_i % 1e5)), 5) + "infoc"

    def generate_msg(obj: dict) -> str:
        '''

        :return:
        '''
        logIdConfig = {'abtest': "001449", 'appear': "000016", 'click': "000017", 'errorLog': "002203",
                       'h5_selfDef': "000080", 'performance': "000015", 'pv': "000014",
                       'tech': "013324"}  # tech是指用了脚本刷b站的
        ret_list = []

        key = obj['key']
        for _i in logIdConfig.keys():
            if _i in key.lower():
                key = _i
        logId = '{}{}'.format(logIdConfig.get(key), int(time.time() * 1000))
        ret_list.append(logId)
        ret_list.append(urllib.parse.quote(url).replace('/', '%2F'))
        ret_list.append(obj['spm_id'])
        if key == 'click' or key == ' pv':
            ret_list.append(target_url)
        ret_list.append(int(time.time()) * 1000)
        if key == 'click':
            ret_list.append(screenx)
            ret_list.append(screeny)
        ret_list.append('{}x{}'.format(screenx, screeny))
        ret_list.append(ptype)
        ret_list.append(json.dumps(obj['msg']).replace('"', '%22').replace(' ', ''))
        ret_list.append(abtest)
        if key == 'click':
            ret_list.append(refer_url)
        if key == 'pv' or key == 'click':
            ret_list.append(generate_uuid())
        else:
            ret_list.append('')
        if key == 'appear':
            ret_list.append('')
        else:
            ret_list.append(language)
        ret_list.append(laboratory)
        ret_list.append(obj['is_selfdef'])
        # lsid = ''
        # for i in range(8):
        #     lsid += random.choice(['1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'])
        # lsid += '_{}'.format(hex(int(time.time() * 1000))[2:].upper())
        # buvid_group = await getBuvidGroupLoadingIns(cookie, ua)
        # buvid_3 = buvid_group.get('buvid3')
        # buvid_4 = buvid_group.get('buvid4')
        send_msg = ''
        for i in ret_list:
            send_msg += '{}|'.format(i)
        send_msg = send_msg[0:len(send_msg) - 1]
        send_msg = send_msg.replace("|", "", 1)
        return send_msg

    SpmPrefix_dict = {'t.bilibili.com': '444.42',  # 控制台输入
                      # e = document.getElementsByTagName("meta")
                      # e.spm_prefix.content
                      'live.bilibili.com': '888.73213', }

    if eventname == 'dynamic_pv':
        dynamic_id = str(ops.get('ops').get('dynamic_id'))
        _type = ops.get('ops').get('type')
        card_stype = ops.get('ops').get('card_stype')
        oid = str(ops.get('ops').get('oid'))
        buvid_fp = get_buvid_fp(cookie)
        buvid4 = get_buvid_4(cookie)
        b_nut_h = int(int(int(get_b_nut(cookie)) / 1000) * 1000)
        lsid = get_lsid(cookie)
        laboratory = 'null'
        smg_obj = {
            "msg": {"bsource": "share_source_weibo", "b_nut_h": b_nut_h, "lsid": lsid,
                    "buvid_fp": buvid_fp,
                    "buvid4": buvid4},
            'is_selfdef': 'undefined',
            'spm_id': '444.42.0.0',
            'key': 'pv'
        }
        msg_queue.append(generate_msg(smg_obj))
        laboratory = ''
        smg_obj = {
            "msg": {"b_nut_h": b_nut_h, "lsid": lsid,
                    "buvid_fp": buvid_fp,
                    "buvid4": buvid4},
            'is_selfdef': 1,
            'spm_id': '444.42.mini.header.show',
            'key': 'appear'
        }
        msg_queue.append(generate_msg(smg_obj))
        laboratory = ''
        smg_obj = {'msg': {
            "card_id": dynamic_id, "card_type": 'DYN', "card_stype": card_stype,
            "b_nut_h": b_nut_h, "lsid": lsid,
            "buvid_fp": buvid_fp,
            "buvid4": buvid4},
            'spm_id': '444.42.list.card.show',
            'is_selfdef': 1,
            'key': 'appear'
        }
        msg_queue.append(generate_msg(smg_obj) + '|')
        laboratory = 'null'
        smg_obj = {'msg':
                       {"event": "replyShow",
                        "value": {"ordering": "heat", "type": _type, "oid": oid, "version": "old"},
                        "bsource": "share_source_copy_link"}
            ,
                   'spm_id': '444.42.selfDef.replyShow',
                   'is_selfdef': 1,
                   'key': 'click'
                   }
        msg_queue.append(generate_msg(smg_obj))

    if eventname == 'dynamic_thumb':
        dynamic_id = str(ops.get('ops').get('dynamic_id'))
        card_stype = ops.get('ops').get('card_stype')
        b_nut_h = int(int(int(get_b_nut(cookie)) / 1000) * 1000)
        lsid = get_lsid(cookie)
        buvid_fp = get_buvid_fp(cookie)
        buvid4 = get_buvid_4(cookie)
        smg_obj = {'msg':
                       {"card_id":dynamic_id,
                        "card_type":"DYN",
                        "card_stype":card_stype,
                        "b_nut_h":b_nut_h,
                        "lsid":lsid,
                        "buvid_fp":buvid_fp,
                        "buvid4":buvid4
                        },
                   'spm_id': '444.42.list.card_like.click',
                   'is_selfdef': 1,
                   'key': 'click'
                   }

        msg_queue.append(generate_msg(smg_obj))

    if eventname == 'dynamic_comment':
        _type = ops.get('ops').get('type')
        oid = str(ops.get('ops').get('oid'))
        smg_obj = {'msg':
                       {"event":"replyInputClick",
                        "value":{
                            "type":_type,
                            "oid":oid,
                            "position":1
                        },
                        "bsource": "share_source_weibo"},
                   'spm_id': '444.42.selfDef.replyInputClick',
                   'is_selfdef': 1,
                   'key': 'click'
                   }
        msg_queue.append(generate_msg(smg_obj))

        smg_obj = {'msg':
                       {"event": "replySendClick",
                        "value": {
                            "type": _type,
                            "oid": oid,
                            "position": 1
                        },
                        "bsource": "share_source_weibo"},
                   'spm_id': '444.42.selfDef.replySendClick',
                   'is_selfdef': 1,
                   'key': 'click'
                   }
        msg_queue.append(generate_msg(smg_obj))

        smg_obj = {'msg':
                       {"event": "reply-send-click",
                        "value": {
                            "type": _type,
                            "oid": oid,
                            "ordering":"heat"
                        },
                        "bsource": "share_source_weibo"},
                   'spm_id': '444.42.selfDef.reply-send-click',
                   'is_selfdef': 1,
                   'key': 'click'
                   }
        msg_queue.append(generate_msg(smg_obj))

    if eventname=='dynamic_forward_click':
        dynamic_id = str(ops.get('ops').get('dynamic_id'))
        card_stype = ops.get('ops').get('card_stype')
        b_nut_h = int(int(int(get_b_nut(cookie)) / 1000) * 1000)
        lsid = get_lsid(cookie)
        buvid_fp = get_buvid_fp(cookie)
        buvid4 = get_buvid_4(cookie)
        smg_obj = {'msg':
                       {"card_id":dynamic_id,
                        "card_type":"DYN",
                        "card_stype":card_stype,
                        "b_nut_h":b_nut_h,
                        "lsid":lsid,
                        "buvid_fp":buvid_fp,
                        "buvid4": buvid4
                        },
                   'spm_id': '444.42.list.card_forward.click',
                   'is_selfdef': 1,
                   'key': 'click'
                   }

        msg_queue.append(generate_msg(smg_obj))



    return msg_queue