import json
import re
import time
import b站cookie.b站cookie_
import b站cookie.globalvar as gl
import requests

# activityType汇总：
# 11：秒杀
# 9：无活动

cookie1 = gl.get_value('cookie1')  # 星瞳
fullcookie1 = gl.get_value('fullcookie1')
ua1 = gl.get_value('ua1')
fingerprint1 = gl.get_value('fingerprint1')
csrf1 = gl.get_value('csrf1')
uid1 = gl.get_value('uid1')
cookie2 = gl.get_value('cookie2')  # 保加利亚
fullcookie2 = gl.get_value('fullcookie2')
ua2 = gl.get_value('ua2')
fingerprint2 = gl.get_value('fingerprint2')
csrf2 = gl.get_value('csrf2')
uid2 = gl.get_value('uid2')
cookie3 = gl.get_value('cookie3')  # 斯卡蒂
fullcookie3 = gl.get_value('fullcookie3')
ua3 = gl.get_value('ua3')
fingerprint3 = gl.get_value('fingerprint3')
csrf3 = gl.get_value('csrf3')
uid3 = gl.get_value('uid3')
cookie4 = gl.get_value('cookie4')  # 墨色
fullcookie4 = gl.get_value('fullcookie4')
ua4 = gl.get_value('ua4')
fingerprint4 = gl.get_value('fingerprint4')
csrf4 = gl.get_value('csrf4')
uid4 = gl.get_value('uid4')
print(int(time.time() * 1000))


# 10057305   1000125786
def order_info(itemsId, skuId, activityId, Type, cookie, ua):
    url = 'https://mall.bilibili.com/mall-c/cart/na/orderinfo?platform=h5&isDegrate=false&mVersion=52&v={}'.format(
        int(time.time() * 1000))
    # skuId代表商品型号
    # itemsId代表商品是啥
    data = {"items":
                [{"itemsId": str(itemsId), "skuId": int(skuId), "skuNum": 1, "shopId": 2233, "activityInfos": None,
                  "cartId": 0}],
            "activityInfo": {"activityId": activityId, "type": Type},
            "buyerId": 0,
            "distId": 0,
            "invoiceId": 0,
            "secKill": 0,
            "cartOrderType": 1,
            "freightCouponCodeId": "",
            "freightCouponIsChecked": 'true'
            }
    headers = {
        'content-type': 'application/json',
        'cookie': cookie,
        'user-agent': ua
    }
    req = requests.request('POST', url=url, data=json.dumps(data), headers=headers)
    payTotalMoneyAll = req.json().get('data').get('payTotalMoneyAll')
    if '.0' or '.00' in payTotalMoneyAll:
        payTotalMoneyAll = re.findall('(.*)\..*', str(payTotalMoneyAll))[0]
    promotionAreaVO = req.json().get('data').get('promotionAreaVO')
    freightCouponVo=req.json().get('data').get('freightCouponVo')
    if freightCouponVo:
        freightCouponCodeId=freightCouponVo.get('freightCouponCodeId')
    else:
        freightCouponCodeId=-1
    if promotionAreaVO:
        couponCodeId = promotionAreaVO.get('couponInfoVO').get('couponCodeId')
    else:
        couponCodeId = -1
    if couponCodeId:
        pass
    else:
        couponCodeId = -1
    benefitAmountAll = req.json().get('data').get('benefitAmountAll')
    if '.0' or '.00' in benefitAmountAll:
        benefitAmountAll = re.findall('(.*)\..*', benefitAmountAll)[0]
    itemsTotalMoneyAll = req.json().get('data').get('itemsTotalMoneyAll')
    if '.0' or '.00' in itemsTotalMoneyAll:
        itemsTotalMoneyAll = re.findall('(.*)\..*', str(itemsTotalMoneyAll))[0]
    expressTotalAmountAll = req.json().get('data').get('expressTotalAmountAll')
    payTotalAmountAll = req.json().get('data').get('payTotalAmountAll')
    if '.0' or '.00' in payTotalAmountAll:
        payTotalAmountAll = re.findall('(.*)\..*', payTotalAmountAll)[0]
    amount = req.json().get('data').get('validList')[0].get('amount')
    distId = req.json().get('data').get('deliver')[0].get('id')
    if '.0' or '.00' in amount:
        amount = re.findall('(.*)\..*', amount)[0]
    retdict = {
        'payTotalMoneyAll': payTotalMoneyAll,
        'couponCodeId': couponCodeId,
        'benefitAmountAll': benefitAmountAll,
        'itemsTotalMoneyAll': itemsTotalMoneyAll,
        'expressTotalAmountAll': expressTotalAmountAll,
        'payTotalAmountAll': payTotalAmountAll,
        'amount': amount,
        'distId': distId,
        'freightCouponCodeId':freightCouponCodeId
    }
    return retdict


def get_items_info_miaosha(itemsId):
    url = 'https://mall.bilibili.com/mall-c-search/items/info?itemsId={}&shopId=2233&itemsVersion=&v={}'.format(itemsId,
                                                                                                                int(time.time() * 1000))
    req = requests.get(url=url)
    retdict = {
        'activityId': '',
        'startTime': '',
        'skuIdList': []
    }
    activityId = req.json().get('data').get('activityInfoVO').get('activityId')
    startTime = req.json().get('data').get('activityInfoVO').get('startTime')
    itemsSkuList = req.json().get('data').get('itemsSkuListVO').get('itemsSkuList')
    for i in itemsSkuList:
        if i.get('skuTagVO'):
            skuId = i.get('id')
            activityPrice = i.get('activityPrice')
            activityStock = i.get('activityStock')
            for p in i.get('skuTagVO').get('activityTagList'):
                name = p.get('name')
                Type = p.get('type')
                retdict['skuIdList'].append({'skuId': skuId, 'name': name, 'type': Type, 'activityStock': activityStock,
                                             'activityPrice': activityPrice})
    retdict.update({'activityId': activityId, 'startTime': startTime})
    return retdict
    # {'activityId': 3749002, 'startTime': 1648450800, 'skuIdList': [{'skuId': 1000125786, 'name': '秒杀', 'type': 5, 'activityStock': 5, 'activityPrice': '1'}]}


def ordercreate(cookie, ua, buvid, uid, activityId, Type, itemsId, skuId):
    order_info_dict = order_info(itemsId, skuId, activityId, Type, cookie, ua)
    print(order_info_dict)
    benefitAmountAll = order_info_dict.get('benefitAmountAll')
    itemsTotalMoneyAll = order_info_dict.get('itemsTotalMoneyAll')
    expressTotalAmountAll = order_info_dict.get('expressTotalAmountAll')
    payTotalAmountAll = order_info_dict.get('payTotalAmountAll')
    couponCodeId = order_info_dict.get('couponCodeId')
    amount = order_info_dict.get('amount')
    distId = order_info_dict.get('distId')
    freightCouponCodeId=order_info_dict.get('freightCouponCodeId')
    kfcActivityId=3147002#cookie内固定值
    url = 'https://mall.bilibili.com/mall-c/cart/na/ordercreate?buvid={buvid}&platform=h5&uid={uid}&channel=1&build=1&isDegrate=false&mVersion=12&vtoken=1222481474843480064'.format(
        buvid=buvid, uid=uid)
    data = {"activityInfo": {"activityId": activityId, "type": int(Type), "marketingId": None},
            'activityId':str(kfcActivityId),
            "secKill": 0,
            "failUrl": "https://mall.bilibili.com/detail.html?loadingShow=1&noTitleBar=1&itemsId={}".format(itemsId),
            "returnUrl": "https://mall.bilibili.com/orderlist.html?noTitleBar=1&status=0",
            "benefitAmountAll": str(benefitAmountAll),
            "buyerId": 0,
            "cartOrderType": 1,
            "deviceInfo": "WEB",
            "deviceType": 2,
            "distId": distId,
            "expressTotalAmountAll": '{}'.format(str(expressTotalAmountAll)),
            "from": "mall_search_mall",
            "recId": "",
            "source": "link",
            "invoiceId": 0,
            "itemsTotalAmountAll": '{}'.format(str(itemsTotalMoneyAll)),
            "orders": [{"buyerComment": "",
                        "items": [{"cartId": 0,
                                   "itemsId": int(itemsId),
                                   "amount": amount,
                                   "skuId": int(skuId),
                                   "skuNum": 1,
                                   "blindBoxId": None,
                                   "orderId": None,
                                   "activityInfos": [],
                                   "resourceType": None,
                                   "resourceId": None}],
                        "shopId": "2233",
                        "shopIsNotice": 1}],
            "payTotalAmountAll": payTotalAmountAll,
            "couponCodeId": couponCodeId,
            'freightCouponCodeId':freightCouponCodeId,
            'freightCouponIsChecked':True
            }
    headers = {
        'cookie': cookie+'vtoken=1222481474843480064;'+'kfcActivityId={};'.format(kfcActivityId),
        #'cookie':"_uuid=497E01B3-E062-B3A8-4AE1-B3683F4FFE7683211infoc; buvid3=220C5F13-6424-4BD0-8872-4B40887E6C1E148807infoc; LIVE_BUVID=AUTO7616267760598581; rpdid=|(J|)kmuY)uY0J'uYkY~)|uJk; dy_spec_agreed=1; deviceFingerprint=6acc97506371743cf62aea5c0538a22b; kfcActivityId=3147002; video_page_version=v_old_home; blackside_state=0; CURRENT_BLACKGAP=0; b_ut=5; fingerprint_s=5ea0004c8a1adb114ab08988046b2476; buvid4=52F4A825-FEA4-FC7D-7403-5C7DBC3ECB0706073-022012116-TDIcPGmL6+DKg3KlPV0wGg%3D%3D; CURRENT_QUALITY=112; buvid_fp_plain=undefined; addressId=0; fingerprint3=304e2f2d343c0c1a16d27512e9010d47; CURRENT_FNVAL=4048; bsource=share_source_copy_link; nostalgia_conf=-1; bp_t_offset_1905702375=639227636386627617; kfcSource=link; msource=link; SESSDATA=46722015%2C1663570119%2Cbad3e%2A31; bili_jct=71f910950b1e7e5e773d650aadf8a51b; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; sid=6upalf8l; buvid_fp=b1603eb98899ac0b675f09636b4452c6; i-wanna-go-back=-1; innersign=1; fingerprint=b1603eb98899ac0b675f09636b4452c6; bp_video_offset_1905702375=642373167329837000; Hm_lvt_8d8d2f308d6e6dffaf586bd024670861=1647963030; hasFollowed=1; from=mall_search_mall; kfcFrom=mall_search_mall; vtoken=1222481474843480064; _dfcaptcha=5858aa0cabb3abd40142e6f7b519f4f7; failUrl=https%3A//mall.bilibili.com/detail.html%3FloadingShow%3D1%26noTitleBar%3D1%26itemsId%3D10048944; c=lAseEarW-1648463257253-ae7099ee6bcc3697886895; _fmdata=WLsK9nxg5aYzRsLTxEDWHnCbl0Ncq3KoFcn%2Fur41BxdqG7MdMkqiL0NM%2BYqai8%2BraHfWxfRXEJ33lWDoj2eYyClvO2zFXfZKaAPiVhbQdRA%3D; _xid=EOIn%2FDkvp23fNnQTTrLPObHTABp0pwJusoRAXeGMzcFOstps7rdLTV%2B%2FErys3wz6DL2%2B59%2Fm0u4pMFLFkTMjvA%3D%3D; b_lsid=FEFDFD66_17FD0250B25; PVID=10; Hm_lpvt_8d8d2f308d6e6dffaf586bd024670861=1648467525",
        'user-agent': ua,
        'content-type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://mall.bilibili.com/confirmorder.html?noTitleBar=1'
    }
    req = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(req.text)
    return req.json()

#
# miaosha_dict = get_items_info_miaosha(10034828)
# activityId = miaosha_dict.get('activityId')
# startTime = miaosha_dict.get('startTime')
# skuId = miaosha_dict.get('skuIdList')[0].get('skuId')
# name = miaosha_dict.get('skuIdList')[0].get('name')
# Type = miaosha_dict.get('skuIdList')[0].get('type')
# activityStock = miaosha_dict.get('skuIdList')[0].get('activityStock')
# activityPrice = miaosha_dict.get('skuIdList')[0].get('activityPrice')
# print(miaosha_dict)
# ordercreate(cookie3, ua3, '220C5F13-6424-4BD0-8872-4B40887E6C1E148807infoc', uid3, activityId, Type, 10034828, skuId)

############下一步搞定验证码！
def get_verify(cookie,ua):#post
    url='https://show.bilibili.com/open/verify/opencaptcha/get'
    data={"ct":"eyJ0c3RJZCI6InIzVUNWdlRzbWYvNHJEVGlQTTROQmc9PSIsImN1c3RvbWVySWQiOiJYQUdvakpDNDFCOXI0SXdzIiwidGltZXN0YW1wIjoicnZhRzlCWDdnM3FQOGRRT0NaeFdXc002aTk4PSIsImRldmljZUlkIjoibEJ6SDJaaUZBOVk4aHR4eFlPTHZ0SjdXTitXTGdPRDFheWhOWUNDbVdDYnJOYnNDIiwiYXBwVHlwZSI6ImR0T3pEOGFLUmtzPSIsImRldmljZVR5cGUiOiJjQ2dsS1lqcjk5UT0iLCJuZXR3b3JrIjoidmJ3eHFDb0VqSjg9In0=","customerId":10002,"deviceId":"daed52348da8ef2f48b45483d4f76dfa","voucher":"o/NaMDaJA/Bn8engoco6PaU7imZF7xGFCOVVPHELtPwgfMrD6ejWEaXE7aOaTbpWxFPjlsugC325FUqoSweVlRW6Pr5yk5ZC05WlFbg/NcO5OkLuMau0RfBsIp1ZSy2he/gMWiuVCR13WuNVxigFKPFhRkGcgO024UeAfDlCqFzZlFMtT9i40Izsq5F7NTI+7+JS/hgfr5yvQiXyIc/ruwskyOXKahM953B5mc3LV9HFLtaR7zJSXohmuKC/5ChZI5ZGFLo/L0tZwiOBLea72zrmOh/oPE80Wok5mvE5WWE48l9qFlBfY/4nTTiNhtZ/USoFhjDdsscKaHmNqSQL95x2fvBGVxz4oeI5pQq2WoCrxo61NY4svbAM6MjtK5FZa2sRodunsBXkxSNewGWj4KmwFktqkLcUQcHHbMO3ByCML6OmB86Nek12F+Iorqwv6jVY3+vvVOOkLSNIn38n/HRtI/71e5uwQuwlJ/uBkKY6opdVl2Q1/kPbF8Avl6aiTRifmChkK7y8uyxU+saZ+7C53Z9bEbXEIf/grXfArho=","apiStartTime":int(time.time()*1000),"csrf":"71f910950b1e7e5e773d650aadf8a51b"}
    headers={
        'cookie': cookie,
        'user-agent': ua,
        'content-type': 'application/json',
    }
    req=requests.post(url=url,data=json.dumps(data),headers=headers)
    print(req.text)
def check(cookie,ua):#post
    url='https://show.bilibili.com/open/verify/opencaptcha/check'
    data={"ct":"eyJkZXZpY2VJZCI6ImxCekgyWmlGQTlZOGh0eHhZT0x2dEo3V04rV0xnT0QxYXloTllDQ21XQ2JyTmJzQyIsInRva2VuIjoiTnJIUytNRlhhc28xVVh2VWZLVjY1UWQ1dEZIOS9hMlNHUk5YN0tKbTY4OGxoSlliIiwiY2FwdGNoYUlkIjoiRnRvQ3ZSVDNrVjJoTTVSRFpPWnp6OHA5dUM5MlQreWxsUVlWWi9hQk9RQ0F3OXhYWEVOWERPVUx3Q1lHNEhVNFFneHhLRW1qMkRZemhuUHYrNENWVmttWmpIb3FRSjZoVjhDV0g1T0RWL2RxQ085M1dnVU9wUXkwTjBnPSIsImFuc3dlciI6Ild6TUh3bzFWOUUxZGF3dHNTUzQxRm8rNUdPWmpiQ1ZjMWxEUDVHeVFXM3JBaTE2NDd4NmJkU1BoRHdVUTZOTzllcThuYjMzeTYyM3VRcVVpYjBkckp0TDhxTUU9Iiwic2NhbGUiOiJXRDRIR0hiRkZNWT0iLCJ0aW1lc3RhbXAiOiJ0MmZ3TGNOV2JiZDJZang1WDFXeWdLQUdRYkk9IiwiYXBwVHlwZSI6ImR0T3pEOGFLUmtzPSIsImRldmljZVR5cGUiOiJjQ2dsS1lqcjk5UT0iLCJuZXR3b3JrIjoidmJ3eHFDb0VqSjg9IiwiY3VyclRpbWUiOiJGSmU5UUpFa2xCck9QeGpFIiwidG90YWxUaW1lIjoiL2NaSndMQkZFcWtlZzZmNSIsImZhaWxDb3VudCI6IjZzb2REZnlUcmV3PSJ9",
          "customerId":10002,
          "deviceId":"daed52348da8ef2f48b45483d4f76dfa",
          "voucher":"o/NaMDaJA/Bn8engoco6PaU7imZF7xGFCOVVPHELtPwgfMrD6ejWEaXE7aOaTbpWxFPjlsugC325FUqoSweVlRW6Pr5yk5ZC05WlFbg/NcO5OkLuMau0RfBsIp1ZSy2he/gMWiuVCR13WuNVxigFKPFhRkGcgO024UeAfDlCqFzZlFMtT9i40Izsq5F7NTI+7+JS/hgfr5yvQiXyIc/ruwskyOXKahM953B5mc3LV9HFLtaR7zJSXohmuKC/5ChZI5ZGFLo/L0tZwiOBLea72zrmOh/oPE80Wok5mvE5WWE48l9qFlBfY/4nTTiNhtZ/USoFhjDdsscKaHmNqSQL95x2fvBGVxz4oeI5pQq2WoCrxo61NY4svbAM6MjtK5FZa2sRodunsBXkxSNewGWj4KmwFktqkLcUQcHHbMO3ByCML6OmB86Nek12F+Iorqwv6jVY3+vvVOOkLSNIn38n/HRtI/71e5uwQuwlJ/uBkKY6opdVl2Q1/kPbF8Avl6aiTRifmChkK7y8uyxU+saZ+7C53Z9bEbXEIf/grXfArho=","verifyVoucher":"kxIQjw5gjDak5xruydPdpwdr/hL9Ljc4snltXTvt8P2Z8rWGRwGoZ9V1aFEJYuLRCeZUBu/Gm9/BPPj0oQLL8srsRlJeqlCqaPCZt/Huo/yIH4floYGQqNtCdj9K3bigJRavNQnEbV+Eg0gFV5lmhrrHupo/j3xzy0KhTiYg155JWyFeUUptdt5HQEjnqdAePQXYUQcGuqn1HMMBEjk5v50TxkadX5z0On6rCTEGs/gx2hoYDYJeYNJQzhKEgqhRubzw5YkDdecTupdtvpM0SecdlEXWQVfdwmVEmkxEQLFQ3At6NtkAUL8YoBjLkB5tD38V6XmdA3vVz9meQKvjF4EBdMeb5wqIuvshlwX1eWd8vTnjwHjMXU1ckt7wzwnVGHEr7bHbiXewQPxMxRUAFMU6NHgIQTaG9Z7mOTT7ug0O5YvT7aX96tF1Hnsi/BAZT88li4rdGK4vOL7PKWnZkqDSnq3rzolf/iCcAKgKBDj4J3TPPvuEZd54p22phbECR8lx4M9npy/dkEpTXRnyhwNW+xUTSHDoJ34OOL38GqBq9416bFAav+5UPMkvvibh7YEiqQQ0myuvIp9tkdXgqJid4XT4idlQp5k9vXUJSjj4MFxNh0MufFey8kWbvsQE5xBGYicQQ3XQPvGRYhVLTxxtsKy3y+5YoPARVwwbIFjXjeeV27S++eeb+5gfGdxbM+cT3j3/bN1hKeHatIN4O9JXwMz6Kolud9cq9qnoTHOeZ8mUqTFej2qFexYw2Z4J",
          "csrf":"71f910950b1e7e5e773d650aadf8a51b"}
    headers = {
        'cookie': cookie,
        'user-agent': ua,
        'content-type': 'application/json',
    }
    req=requests.post(url=url,data=json.dumps(data),headers=headers)
    print(req.text)
get_verify(cookie3,ua3)
check(cookie3,ua3)