import asyncio
import json
import os
from typing import Literal

import aiofiles
from curl_cffi.requests.exceptions import RequestException
from httpx import HTTPError

from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.models.v1.samsclub.api_model import RespUserProfile
from fastapi接口.service.samsclub.exceptions.error import UnknownError
from fastapi接口.service.samsclub.tools.do_samsclub_encryptor import update_do_encrypt_key
from fastapi接口.service.samsclub.tools.headers_gen import SamsClubHeadersGen, sort_headers_with_missing_last
from utl.pushme.pushme import pushme
from utl.代理.SealedRequests import my_async_httpx


class SamsClubApi:
    class FilePath:
        auth_token = os.path.join(os.path.dirname(__file__), 'auth_token.txt')

    async def update_auth_token(self, auth_token):
        async with aiofiles.open(self.FilePath.auth_token, 'w', encoding='utf-8') as f:
            await f.write(auth_token)
        self.headers_gen.auth_token = auth_token

    def __init__(self):
        auth_token = ''
        if os.path.exists(self.FilePath.auth_token):
            with open(self.FilePath.auth_token, 'r') as f:
                if f_content := f.read():
                    auth_token = f_content.strip()
        self.headers_gen = SamsClubHeadersGen(
            auth_token=auth_token,
        )
        self._lock = asyncio.Lock()

    log = sams_club_logger

    _base_url = "https://api-sams.walmartmobile.cn"
    uid = "1818144697779"
    mobile = '0TaB2ZDRnEeE+1REHfzpeA=='
    addressVO = {
        "cityName": "上海市",
        "countryName": "",
        "detailAddress": "",
        "districtName": "宝山区",
        "provinceName": "上海市"
    }
    storeInfoVOList = [{"storeType": 16, "storeId": 6558, "storeDeliveryAttr": [3, 4, 6, 14],
                        "storeDeliveryTemplateId": 1355122139681978902},
                       {"storeType": 256, "storeId": 6758, "storeDeliveryAttr": [9, 13],
                        "storeDeliveryTemplateId": 1893545853000529686},
                       {"storeType": 2, "storeId": 6858, "storeDeliveryAttr": [7],
                        "storeDeliveryTemplateId": 1788616360381840406},
                       {"storeType": 8, "storeId": 9996, "storeDeliveryAttr": [1],
                        "storeDeliveryTemplateId": 1147161263885953814}]
    storeList = [
        "6558",
        "6758",
        "6858",
        "9996",
    ]
    amapHeaders = {
        "provinceCode": "310000",
        "cityCode": "310100",
        "districtCode": "310113",
        "amapProvinceCode": "310000",
        "amapCityCode": "310100",
        "amapDistrictCode": "310113"
    }
    cur_siv = ""
    cur_ssk = ""

    async def update_encrypt_key(self, resp_headers) -> bool:
        """
        True：真更新了
        False：没有更细
        """
        siv = resp_headers.get('siv')
        ssk = resp_headers.get('ssk')
        srd = resp_headers.get('srd')
        if siv and ssk:
            if siv != self.cur_siv or ssk != self.cur_ssk:
                async with self._lock:
                    if siv != self.cur_siv or ssk != self.cur_ssk:
                        self.log.debug("更新加密密钥")
                        await update_do_encrypt_key(siv, ssk, srd)
                        self.cur_siv = siv
                        self.cur_ssk = ssk
                        return True
        return False

    @property
    def base_url(self):
        return self._base_url

    def body_to_json(self, body):
        return json.dumps(body, ensure_ascii=False, separators=(',', ':'))

    async def send(
            self,
            url: str,
            body: dict | None = None,
            method: Literal["POST", "GET"] | None = "POST",
            params: dict | None = None,
            *,
            is_add_amap_headers: bool = True
    ):
        while 1:
            cur_auth_token = self.headers_gen.auth_token
            body_str = self.body_to_json(body) if body else ''
            headers_model = await self.headers_gen.gen_headers(body_str)
            headers = headers_model.model_dump()
            if is_add_amap_headers:
                headers.update(self.amapHeaders)
            headers.update({'Content-Length': str(len(body_str.encode('utf-8')))})
            try:
                resp = await my_async_httpx.request(
                    url,
                    method=method,
                    params=params,
                    headers=sort_headers_with_missing_last(headers),
                    data=body_str,
                    # proxies=CONFIG.custom_proxy
                )
            except (RequestException, HTTPError) as e:
                await asyncio.sleep(10)
                continue
            except Exception as e:
                self.log.exception(f'curl_cffi网络请求未知异常：{e}')
                raise e
            is_updated = await self.update_encrypt_key(resp.headers)
            is_succ = await self.handle_resp_code(resp, auth_token=cur_auth_token, is_updated_encrypt_key=is_updated)
            if not is_succ:
                await asyncio.sleep(10)
                continue
            self.log.debug(f'请求成功：{resp}')
            return resp

    async def get_recommend_store_list_by_location(self):
        url = self._base_url + '/api/v1/sams/merchant/storeApi/getRecommendStoreListByLocation'
        body = {
            "latitude": self.headers_gen.latitude,
            "longitude": self.headers_gen.longitude
        }
        return await self.send(url, body=body, is_add_amap_headers=False)

    async def handle_resp_code(self, response, auth_token: str, is_updated_encrypt_key: bool) -> bool:
        resp_dict = response.json()
        is_succ = resp_dict.get('success')
        resp_code = resp_dict.get('code')
        resp_msg = resp_dict.get('msg')
        if is_succ is not True:
            match resp_code:
                case "SPU_NOT_EXIST":
                    self.log.debug(f'{resp_dict}')
                case "INTERNAL_ERROR":
                    self.log.critical(f'{resp_dict}')
                    await asyncio.sleep(30)
                case "AUTH_FAIL":
                    if is_updated_encrypt_key:
                        return False
                    self.log.critical(f"被强制登出！{resp_dict}")
                    await asyncio.to_thread(pushme, f'山姆会员商店token失效', f'{resp_dict}')
                    self.log.debug(f'等待token更新')
                    while 1:
                        if auth_token != self.headers_gen.auth_token:
                            break
                        await asyncio.sleep(3)
                # raise AUTH_FAIL(f"鉴权失败！响应code：{resp_code}")
                case "BUSYNESS":
                    self.log.critical(f'{resp_msg}')
                    await asyncio.sleep(60)
                case _:
                    self.log.opt(exception=True).critical(f"请求未知错误！{resp_dict}")
                    raise UnknownError(f"未知响应code：{resp_code}")
        return bool(is_succ)

    async def init_api_info(self):
        version_resp = await self.configuration_appVersionUpdate_getAppVersionUpdateInfo()
        version_json = version_resp.json()
        if version_str := version_json.get('data', {}).get('youngVersion'):
            self.headers_gen.version_str = version_str
        resp: RespUserProfile = await self.user_profile()
        self.log.debug(f'用户信息：{resp}')
        self.uid = resp.data.uid
        self.mobile = resp.data.mobile

        # region 账号初始化
        await self.configuration_portal_get_config()
        await self.configuration_portal_cnConfig_getTraditionalCnConfig()
        await self.goods_portal_spu_queryXPlusTagImg()
        await self.channel_portal_AdgroupData_queryAdgroup()
        await self.configuration_portal_cnConfig_getTraditionalCnConfig()
        await self.goods_portal_spu_queryXPlusTagImg()
        await self.configuration_portal_beUpdate()
        await self.activity_taskreport(99)
        await self.configuration_portal_get_config()
        await self.configuration_discoverIcon_getOneIcon()

        # TODO： 这里加一个registerUidToken

        await self.configuration_portal_get_config()
        await self.configuration_portal_getGrayConfig()
        await self.get_gray_config()
        await self.configuration_portal_getGrayPageConfig()
        await self.configuration_portal_resource_query()
        # await self.user_label_scheme_get()
        # await self.cart_merge_visitor_goods()

        # endregion

        store_info_resp = await self.get_recommend_store_list_by_location()
        store_info_resp_dict = store_info_resp.json()
        if store_info_resp_data := store_info_resp_dict.get('data', {}).get('storeList'):
            self.storeList = []  # 字符串的store_id
            self.storeInfoVOList = []  # like
            # {"storeType": 16, "storeId": 6558, "storeDeliveryAttr": [3, 4, 6, 14],
            # "storeDeliveryTemplateId": 1355122139681978902}
            for x in store_info_resp_data:
                self.storeList.append(x.get('storeId'))
                da = {
                    "storeType": int(x.get('storeType')),
                    "storeId": int(x.get('storeId')),
                    "storeDeliveryAttr": x.get('allDeliveryAttrList'),
                    "storeDeliveryTemplateId": int(
                        x.get('storeRecmdDeliveryTemplateData').get('storeDeliveryTemplateId'))
                }
                self.storeInfoVOList.append(da)
        self.log.debug(f'初始化headers信息成功\n{version_str}\n{self.storeList}\n{self.storeInfoVOList}')
        ...

    async def configuration_appVersionUpdate_getAppVersionUpdateInfo(self):
        url = self._base_url + '/api/v1/sams/configuration/appVersionUpdate/getAppVersionUpdateInfo'
        body = {
            "androidChannel": "oppo",
            "nowVersion": self.headers_gen.version_str,
            "requestSource": "2"
        }
        return await self.send(url, body)

    async def spu_query_detail(self, spuId: int):
        url = self._base_url + '/api/v1/sams/goods-portal/spu/queryDetail'
        body = {
            "source": "ANDROID",
            "channel": 1,
            "spuId": int(spuId),
            "uid": self.uid,
            "addressVO": self.addressVO,
            "isTagEntryAbtTest": True,
            "storeInfoVOList": self.storeInfoVOList,
        }
        return await self.send(url, body, is_add_amap_headers=True)

    async def grouping_query_navigation(self):
        """
        {"data":{"dataList":[{"groupingId":"35145","title":"肉蛋果蔬","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/737598112dde476b80f16388af176bb7-1747981873486.jpg","storeId":"-1","children":[]},{"groupingId":"156048","title":"乳品烘焙","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/1d3c5674d2f84621987d7ad83935b99e-1747808674432.png","storeId":"-1","children":[]},{"groupingId":"156050","title":"速食冷冻","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/5319ba9de401426cba6cd25d38330a19-1747130076819.png","storeId":"-1","children":[]},{"groupingId":"34112","title":"休闲零食","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/db859a706fd441fdb0a76f3141512e91-1747130076493.png","storeId":"-1","children":[]},{"groupingId":"34118","title":"酒水饮料","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/6caf4405b9a54de9b91d1dabac7f930d-1747130076315.png","storeId":"-1","children":[]},{"groupingId":"114131","title":"粮油干货","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/4f6b1109ce504b0fb9d3fc85f1e2a2bd-1745462110598.png","storeId":"-1","children":[]},{"groupingId":"113105","title":"个护美妆","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/159366599fe2465f8dc41725293c64ad-1747130075985.png","storeId":"-1","children":[]},{"groupingId":"34138","title":"母婴玩具","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/7d4fdd2642f040c68a95c6fed3323d3a-1747130671688.png","storeId":"-1","children":[]},{"groupingId":"35108","title":"全球购","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/c92e589a28344785b8db64fca8e13396-1745462127490.png","storeId":"-1","children":[]},{"groupingId":"226203","title":"家清纸品","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/6c62b39464d14a8695fba078be98c551-1745462110153.png","storeId":"-1","children":[]},{"groupingId":"113114","title":"家电家居","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/64564235a4a045a88e6b1d675df3cead-1747130076105.png","storeId":"-1","children":[]},{"groupingId":"227225","title":"服饰家纺","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/89e25d19e248408db3a51c0a845a38b6-1747130075756.png","storeId":"-1","children":[]},{"groupingId":"225226","title":"营养保健","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/175f064e283046719c5a9549b37d025c-1747130075307.png","storeId":"-1","children":[]},{"groupingId":"34145","title":"萌宠生活","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/f1e0bac821134f5cb95760b50f2ae421-1747130075542.png","storeId":"-1","children":[]},{"groupingId":"226209","title":"眼镜助听","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/558752e1680b4addbc0e4dd6358bd14e-1745462128233.png","storeId":"-1","children":[]},{"groupingId":"87055","title":"线上专享","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/10efca2b8e6d451e91623ea5b89866f6-1745462128104.png","storeId":"-1","children":[]},{"groupingId":"182207","title":"礼品卡","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/bc01a5c7de744bc09dc8c90f1852871f-1745462110388.png","storeId":"-1","children":[]}],"cardFilterList":[],"searchFilterList":[],"searchAfter":[],"reportInfo":"","hasNextPage":false,"onlyShowSimilarButton":false},"code":"Success","msg":"","errorMsg":"","traceId":"16d3a7318c737acf","requestId":"106560fa03e344ce9f9056c609accd72.101.17481870958365739","rt":0,"success":true}
        :return:
        """
        url = self._base_url + '/api/v1/sams/goods-portal/grouping/queryNavigation'
        body = {
            "isNew": True,
            "storeCategoryList": self.storeInfoVOList
        }
        return await self.send(url, body, is_add_amap_headers=True)

    async def grouping_query_children(self, groupingId: int, navigationId: int):
        """
        {"data":[{"groupingId":"228253","title":"为您推荐","level":2,"navigationId":"1","children":[]},{"groupingId":"275054","title":"新品上市","level":2,"navigationId":"1","children":[{"groupingId":"276053","title":"新品上市","level":3,"navigationId":"1","children":[]}],"childrenSize":1},{"groupingId":"325081","title":"防晒/雨具","level":2,"navigationId":"1","children":[{"groupingId":"323075","title":"防晒服","level":3,"navigationId":"1","children":[]},{"groupingId":"323076","title":"雨具","level":3,"navigationId":"1","children":[]},{"groupingId":"324086","title":"防晒配件","level":3,"navigationId":"1","children":[]}],"childrenSize":3},{"groupingId":"228254","title":"被芯/套件","level":2,"navigationId":"1","children":[{"groupingId":"225254","title":"被芯","level":3,"navigationId":"1","children":[]},{"groupingId":"226219","title":"套件","level":3,"navigationId":"1","children":[]}],"childrenSize":2},{"groupingId":"227227","title":"薄毯/毛巾","level":2,"navigationId":"1","children":[{"groupingId":"225255","title":"薄毯","level":3,"navigationId":"1","children":[]},{"groupingId":"228255","title":"毛巾","level":3,"navigationId":"1","children":[]}],"childrenSize":2},{"groupingId":"225253","title":"枕头/床垫","level":2,"navigationId":"1","children":[{"groupingId":"306010","title":"抱枕","level":3,"navigationId":"1","children":[]},{"groupingId":"226218","title":"枕头","level":3,"navigationId":"1","children":[]},{"groupingId":"227226","title":"床垫","level":3,"navigationId":"1","children":[]}],"childrenSize":3},{"groupingId":"227229","title":"箱包/鞋帽/配饰","level":2,"navigationId":"1","children":[{"groupingId":"228257","title":"旅行箱","level":3,"navigationId":"1","children":[]},{"groupingId":"226222","title":"背包","level":3,"navigationId":"1","children":[]},{"groupingId":"225257","title":"鞋","level":3,"navigationId":"1","children":[]},{"groupingId":"227230","title":"帽","level":3,"navigationId":"1","children":[]},{"groupingId":"290109","title":"个人配饰","level":3,"navigationId":"1","children":[]}],"childrenSize":5},{"groupingId":"226224","title":"春夏女装","level":2,"navigationId":"1","children":[{"groupingId":"227232","title":"上装","level":3,"navigationId":"1","children":[]},{"groupingId":"228260","title":"下装","level":3,"navigationId":"1","children":[]},{"groupingId":"287307","title":"内衣/裤子","level":3,"navigationId":"1","children":[]},{"groupingId":"286324","title":"袜子","level":3,"navigationId":"1","children":[]}],"childrenSize":4},{"groupingId":"227231","title":"春夏男装","level":2,"navigationId":"1","children":[{"groupingId":"228259","title":"上装","level":3,"navigationId":"1","children":[]},{"groupingId":"225259","title":"下装","level":3,"navigationId":"1","children":[]},{"groupingId":"286323","title":"内衣/裤子","level":3,"navigationId":"1","children":[]},{"groupingId":"285324","title":"袜子","level":3,"navigationId":"1","children":[]}],"childrenSize":4},{"groupingId":"228258","title":"春夏童装","level":2,"navigationId":"1","children":[{"groupingId":"225258","title":"上装","level":3,"navigationId":"1","children":[]},{"groupingId":"226223","title":"下装","level":3,"navigationId":"1","children":[]},{"groupingId":"287306","title":"内衣/裤子","level":3,"navigationId":"1","children":[]},{"groupingId":"288296","title":"袜子","level":3,"navigationId":"1","children":[]}],"childrenSize":4},{"groupingId":"326066","title":"婴儿服饰","level":2,"navigationId":"1","children":[{"groupingId":"323070","title":"婴儿服饰","level":3,"navigationId":"1","children":[]}],"childrenSize":1}],"code":"Success","msg":"","errorMsg":"","traceId":"e0c2ff1d0695a907","requestId":"as|06d8aeb326fa4780b539cbac1413b88b.101.17481882133405739","rt":0,"success":true}
        :param navigationId:
        :param groupingId:
        :return:
        """
        url = self._base_url + '/api/v1/sams/goods-portal/grouping/queryChildren'
        body = {
            "storeCategoryList": self.storeInfoVOList,
            "groupingId": int(groupingId),
            "navigationId": navigationId,
            "uid": self.uid
        }
        return await self.send(url, body, is_add_amap_headers=True)

    async def grouping_list(self, firstCategoryId: int, SecondCategoryId: int, frontCategoryIds: list[int],
                            pageNum: int, pageSize: int = 20):
        """

        :param SecondCategoryId:  二级分类id
        :param firstCategoryId: 一级分类id
        :param frontCategoryIds: 一级分类id底下的全部子id
        :param pageNum:
        :param pageSize:
        :return:
        """
        url = self._base_url + '/api/v1/sams/goods-portal/grouping/list'
        body = {
            "pageSize": pageSize,
            "useNewPage": True,
            "addressVO": self.addressVO,
            "storeInfoVOList": self.storeInfoVOList,
            "uid": self.uid,
            "pageNum": pageNum,
            "useNew": True,
            "isTagEntryAbtTest": True,
            "isReversOrder": False,
            "isFastDelivery": False,
            "recommendFirstCategoryId": firstCategoryId,
            "recommendSecondCategoryId": SecondCategoryId,
            "frontCategoryIds": frontCategoryIds,
            "secondCategoryId": SecondCategoryId,
            "isShowCustomTag": True
        }
        return await self.send(url, body, is_add_amap_headers=True)

    async def user_profile(self) -> RespUserProfile:
        url = self._base_url + '/api/v1/sams/sams-user/user/profile'
        params = {
            'auth-token': self.headers_gen.auth_token
        }
        resp = await self.send(
            url,
            params=params,
            method='GET',
            is_add_amap_headers=True
        )
        return RespUserProfile.validate_python(resp.json())

    async def configuration_portal_getGrayConfig(self) -> dict:
        """
        {
    "clientIp": null,
    "code": "Success",
    "data": {
        "publishTime": "1754580517629",
        "strategyDetails": {
            "CN2TCGray": {
                "allEnable": true,
                "bizCode": "CN2TCGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "中文繁简切换",
                "versionKey": ""
            },
            "addCartExp": {
                "allEnable": true,
                "bizCode": "addCartExp",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "加车体验优化",
                "versionKey": ""
            },
            "addrAccurateSearch": {
                "allEnable": true,
                "bizCode": "addrAccurateSearch",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "高德地址精准搜索",
                "versionKey": ""
            },
            "addressCode": {
                "allEnable": true,
                "bizCode": "addressCode",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "请求header带上省市区code",
                "versionKey": ""
            },
            "apartOrder": {
                "allEnable": true,
                "bizCode": "apartOrder",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "合并支付并拆单",
                "versionKey": ""
            },
            "appDecorationReconstruction": {
                "allEnable": true,
                "bizCode": "appDecorationReconstruction",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "APP首页重构",
                "versionKey": ""
            },
            "appLoadingOpt": {
                "allEnable": true,
                "bizCode": "appLoadingOpt",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "加载效率优化",
                "versionKey": ""
            },
            "appSearchGray": {
                "allEnable": true,
                "bizCode": "appSearchGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "APP搜索埋点",
                "versionKey": ""
            },
            "applicableGoods": {
                "allEnable": true,
                "bizCode": "applicableGoods",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "凑单页",
                "versionKey": ""
            },
            "associatedWordExp": {
                "allEnable": false,
                "bizCode": "associatedWordExp",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "搜索联想词算法实验_0424",
                "versionKey": ""
            },
            "associatedWordExp1": {
                "allEnable": false,
                "bizCode": "associatedWordExp1",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"998\",\"expKey\":\"exp_lianxiang_test3_0626_A\",\"groupKey\":\"exp_lianxiang_test3_0626\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_lianxiang_test3_0626\",\"params\":{\"name\":\"原始对照组（75%）\",\"strategy\":\"original\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_associatedWordExp1_exp_lianxiang_test3_0626\",\"userType\":2}",
                "strategyDesc": "搜索联想词算法实验-三期",
                "versionKey": "A"
            },
            "bankcommMemberCard": {
                "allEnable": true,
                "bizCode": "bankcommMemberCard",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "交行联名卡",
                "versionKey": ""
            },
            "bannerComment": {
                "allEnable": false,
                "bizCode": "bannerComment",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"588\",\"expKey\":\"exp_detail_picture_evaluate_1_A\",\"groupKey\":\"exp_detail_picture_evaluate_1\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_detail_picture_evaluate_1\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_bannerComment_exp_detail_picture_evaluate_1\",\"userType\":2}",
                "strategyDesc": "商品详情主图评价模块实验",
                "versionKey": "A"
            },
            "becomeMemberExp": {
                "allEnable": false,
                "bizCode": "becomeMemberExp",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"667\",\"expKey\":\"exp_NewMembership_1029_A\",\"groupKey\":\"exp_NewMembership_1029\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_NewMembership_1029\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_becomeMemberExp_exp_NewMembership_1029\",\"userType\":2}",
                "strategyDesc": "成为会员页实验",
                "versionKey": "A"
            },
            "buyOneAbt": {
                "allEnable": true,
                "bizCode": "buyOneAbt",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "全城配随手买实验",
                "versionKey": "B"
            },
            "cartRestructure": {
                "allEnable": true,
                "bizCode": "cartRestructure",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "购物车重构",
                "versionKey": ""
            },
            "cartRestructureV2": {
                "allEnable": true,
                "bizCode": "cartRestructureV2",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "购物车重构二期",
                "versionKey": ""
            },
            "categoryAddCartRecom": {
                "allEnable": false,
                "bizCode": "categoryAddCartRecom",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"1030\",\"expKey\":\"exp_category_rectest_250626_A\",\"groupKey\":\"exp_category_rectest_250626\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_category_rectest_250626\",\"params\":{\"name\":\"无加购后推荐\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_categoryAddCartRecom_exp_category_rectest_250626\",\"userType\":2}",
                "strategyDesc": "分类页增加加购后推荐位实验",
                "versionKey": "A"
            },
            "categoryOpt": {
                "allEnable": false,
                "bizCode": "categoryOpt",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"927\",\"expKey\":\"exp_fenleiye_PKxiliepin_online_A\",\"groupKey\":\"exp_fenleiye_PKxiliepin_online\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_fenleiye_PKxiliepin_online\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_categoryOpt_exp_fenleiye_PKxiliepin_online\",\"userType\":2}",
                "strategyDesc": "分类页优化",
                "versionKey": "A"
            },
            "categoryRecommend": {
                "allEnable": false,
                "bizCode": "categoryRecommend",
                "group": "true",
                "isOpen": true,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"1090\",\"expKey\":\"rec_category_250723_exp10\",\"groupKey\":\"rec_category_250723\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"rec_category_250723\",\"params\":{\"component\":\"recommend\",\"name\":\"商品大卡\",\"bigpic\":\"true\",\"backend\":\"samall\",\"strategy\":\"max_slot;cate_diversity_slot;f100;new;CBEC_diversity_slot;CBEC_add_slot\",\"isGray\":\"true\",\"group\":\"true\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_categoryRecommend_rec_category_250723\",\"userType\":2}",
                "strategyDesc": "分类页为你推荐",
                "versionKey": "exp10"
            },
            "commentSearchText": {
                "allEnable": false,
                "bizCode": "commentSearchText",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "评价搜索页文案",
                "versionKey": ""
            },
            "commentVideoCompression": {
                "allEnable": false,
                "bizCode": "commentVideoCompression",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "视频压缩",
                "versionKey": ""
            },
            "customerServiceSdk": {
                "allEnable": true,
                "bizCode": "customerServiceSdk",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "客服SDK",
                "versionKey": ""
            },
            "decoration": {
                "allEnable": false,
                "bizCode": "decoration",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "装修重构",
                "versionKey": ""
            },
            "discover": {
                "allEnable": true,
                "bizCode": "discover",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "发现页",
                "versionKey": ""
            },
            "expNewUserGiftMiniProKey": {
                "allEnable": false,
                "bizCode": "expNewUserGiftMiniProKey",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "新人礼包-MiniProgram",
                "versionKey": ""
            },
            "expireMemberCardSupportDowngraded": {
                "allEnable": false,
                "bizCode": "expireMemberCardSupportDowngraded",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"400\",\"expKey\":\"exp_JJxufei_A\",\"groupKey\":\"exp_JJxufei\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_JJxufei\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_expireMemberCardSupportDowngraded_exp_JJxufei\",\"userType\":2}",
                "strategyDesc": "卓越个人主卡过期支持降级消费",
                "versionKey": "A"
            },
            "goodsDetailBlankPageOpt": {
                "allEnable": true,
                "bizCode": "goodsDetailBlankPageOpt",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "商详页切换系列品后空白页优化",
                "versionKey": ""
            },
            "goodsDetailNewTest": {
                "allEnable": false,
                "bizCode": "goodsDetailNewTest",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"884\",\"expKey\":\"exp_detail_new_B\",\"groupKey\":\"exp_detail_new\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_detail_new\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_goodsDetailNewTest_exp_detail_new\",\"userType\":2}",
                "strategyDesc": "商品详情页大改版",
                "versionKey": "B"
            },
            "goodsDetailOpt": {
                "allEnable": true,
                "bizCode": "goodsDetailOpt",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "商详页优化",
                "versionKey": ""
            },
            "goodsDetailPageRecommendOpt": {
                "allEnable": false,
                "bizCode": "goodsDetailPageRecommendOpt",
                "group": "C",
                "isOpen": true,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"913\",\"expKey\":\"rec_description_250508_exp01\",\"groupKey\":\"rec_description_250508\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"rec_description_250508\",\"params\":{\"component\":\"C;no_inventory;after_cart_rec\",\"name\":\"经常一起买优先\",\"backend\":\"sam\",\"strategy\":\"user_DND_5\",\"isGray\":\"true\",\"group\":\"C\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_goodsDetailPageRecommendOpt_rec_description_250508\",\"userType\":2}",
                "strategyDesc": "商详页推荐优化-APP",
                "versionKey": "exp01"
            },
            "goodsDetailParamPk": {
                "allEnable": false,
                "bizCode": "goodsDetailParamPk",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"702\",\"expKey\":\"exp_goods_PK_B\",\"groupKey\":\"exp_goods_PK\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_goods_PK\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_goodsDetailParamPk_exp_goods_PK\",\"userType\":2}",
                "strategyDesc": "商品详情参数PK实验",
                "versionKey": "B"
            },
            "goodsDetailStockReveal": {
                "allEnable": false,
                "bizCode": "goodsDetailStockReveal",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "商品详情页门店库存模块实验",
                "versionKey": ""
            },
            "goodsThumbnail": {
                "allEnable": true,
                "bizCode": "goodsThumbnail",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "终端瀑布流展示系列品小图",
                "versionKey": "B"
            },
            "hippyKitchen": {
                "allEnable": false,
                "bizCode": "hippyKitchen",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "发现厨房hippy改造",
                "versionKey": ""
            },
            "hippyResource": {
                "allEnable": false,
                "bizCode": "hippyResource",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "hippy资源下载管理",
                "versionKey": ""
            },
            "hippyResource1": {
                "allEnable": true,
                "bizCode": "hippyResource1",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "hippy资源下载管理1",
                "versionKey": ""
            },
            "hippyShowOrder": {
                "allEnable": false,
                "bizCode": "hippyShowOrder",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "hippy晒单",
                "versionKey": ""
            },
            "hippySpt": {
                "allEnable": false,
                "bizCode": "hippySpt",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "大厨教做菜双列&短图文",
                "versionKey": ""
            },
            "hippyVideoFeed": {
                "allEnable": false,
                "bizCode": "hippyVideoFeed",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "hippy视频流改造",
                "versionKey": ""
            },
            "homeAddAddressFloat": {
                "allEnable": false,
                "bizCode": "homeAddAddressFloat",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "首页新增地址浮窗",
                "versionKey": ""
            },
            "homeThreeGoodsModule": {
                "allEnable": true,
                "bizCode": "homeThreeGoodsModule",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "IOS首页卡顿优化灰度策略",
                "versionKey": ""
            },
            "inviteGifts": {
                "allEnable": false,
                "bizCode": "inviteGifts",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "邀请有礼",
                "versionKey": ""
            },
            "justStoreSaleSplit": {
                "allEnable": false,
                "bizCode": "justStoreSaleSplit",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "仅门店可售实验",
                "versionKey": ""
            },
            "memberCreateCardPageOpt": {
                "allEnable": true,
                "bizCode": "memberCreateCardPageOpt",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "会籍开卡页优化-APP",
                "versionKey": "B"
            },
            "memberCreateCardPageOptMiniProgram": {
                "allEnable": true,
                "bizCode": "memberCreateCardPageOptMiniProgram",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "会籍开卡页优化-小程序",
                "versionKey": "B"
            },
            "memberGuide": {
                "allEnable": false,
                "bizCode": "memberGuide",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"590\",\"expKey\":\"exp_Member_handbook_A\",\"groupKey\":\"exp_Member_handbook\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_Member_handbook\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_memberGuide_exp_Member_handbook\",\"userType\":2}",
                "strategyDesc": "会员指南",
                "versionKey": "A"
            },
            "memberUnionPay": {
                "allEnable": true,
                "bizCode": "memberUnionPay",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "会籍合并支付",
                "versionKey": ""
            },
            "messageCenterGray": {
                "allEnable": true,
                "bizCode": "messageCenterGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "消息中心",
                "versionKey": ""
            },
            "midSearchPage": {
                "allEnable": false,
                "bizCode": "midSearchPage",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"261\",\"expKey\":\"exp_searchpaga_test_A\",\"groupKey\":\"exp_searchpaga_test\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_searchpaga_test\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_midSearchPage_exp_searchpaga_test\",\"userType\":2}",
                "strategyDesc": "搜索中间页样式",
                "versionKey": "A"
            },
            "mineHeadGray": {
                "allEnable": true,
                "bizCode": "mineHeadGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "个人页重构-安卓",
                "versionKey": ""
            },
            "miniGoodsDetailBuyCardExp": {
                "allEnable": true,
                "bizCode": "miniGoodsDetailBuyCardExp",
                "group": "C",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "商品详情页购买会籍-小程序",
                "versionKey": "C"
            },
            "miniHomePage": {
                "allEnable": true,
                "bizCode": "miniHomePage",
                "group": "A",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "小程序非会员首页",
                "versionKey": "A"
            },
            "newMemberRenewPage": {
                "allEnable": true,
                "bizCode": "newMemberRenewPage",
                "group": "A",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "续费页重构",
                "versionKey": "A"
            },
            "newPeronalConter": {
                "allEnable": false,
                "bizCode": "newPeronalConter",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"750\",\"expKey\":\"exp_mypage_new_A\",\"groupKey\":\"exp_mypage_new\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_mypage_new\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_newPeronalConter_exp_mypage_new\",\"userType\":2}",
                "strategyDesc": "新版个人中心",
                "versionKey": "A"
            },
            "newPicview": {
                "allEnable": true,
                "bizCode": "newPicview",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "ios图片浏览器体验优化",
                "versionKey": ""
            },
            "newTagManageExp": {
                "allEnable": false,
                "bizCode": "newTagManageExp",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"670\",\"expKey\":\"exp_new_tag_manage_20241031_B\",\"groupKey\":\"exp_new_tag_manage_20241031\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_new_tag_manage_20241031\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_newTagManageExp_exp_new_tag_manage_20241031\",\"userType\":2}",
                "strategyDesc": "新标签管理后台灰度实验",
                "versionKey": "B"
            },
            "noSearchRecommend": {
                "allEnable": true,
                "bizCode": "noSearchRecommend",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "搜索无结果为你推荐",
                "versionKey": ""
            },
            "paySdkGray": {
                "allEnable": true,
                "bizCode": "paySdkGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "支付sdk",
                "versionKey": ""
            },
            "personalSwift": {
                "allEnable": false,
                "bizCode": "personalSwift",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "个人中心子页面改造",
                "versionKey": ""
            },
            "preloadFind": {
                "allEnable": false,
                "bizCode": "preloadFind",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "临时价格，发现页预加载IOS技术优化",
                "versionKey": ""
            },
            "presellOrderDelivery": {
                "allEnable": true,
                "bizCode": "presellOrderDelivery",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "预售订单履约",
                "versionKey": ""
            },
            "promotionTaskBox": {
                "allEnable": true,
                "bizCode": "promotionTaskBox",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "营销任务盒子",
                "versionKey": ""
            },
            "rankingPageTag": {
                "allEnable": false,
                "bizCode": "rankingPageTag",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "榜单页及榜单组件排名标签",
                "versionKey": ""
            },
            "remakeSearchRankListUI": {
                "allEnable": true,
                "bizCode": "remakeSearchRankListUI",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "榜单页UI重构-android",
                "versionKey": ""
            },
            "renewPageToH5Gray": {
                "allEnable": true,
                "bizCode": "renewPageToH5Gray",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "续费页改造为H5",
                "versionKey": "B"
            },
            "reportHandler": {
                "allEnable": false,
                "bizCode": "reportHandler",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "IOS埋点上报灰度策略",
                "versionKey": ""
            },
            "reviewSearchText": {
                "allEnable": true,
                "bizCode": "reviewSearchText",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "评价搜索功能",
                "versionKey": "B"
            },
            "rightsCommentExp": {
                "allEnable": true,
                "bizCode": "rightsCommentExp",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "售后评价一期灰度",
                "versionKey": ""
            },
            "scGray": {
                "allEnable": true,
                "bizCode": "scGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "sc",
                "versionKey": ""
            },
            "scPlayer": {
                "allEnable": true,
                "bizCode": "scPlayer",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "视频播放器重构-IOS",
                "versionKey": ""
            },
            "scplayerHome": {
                "allEnable": true,
                "bizCode": "scplayerHome",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "视频播放器重构2.0",
                "versionKey": ""
            },
            "searchResultExp": {
                "allEnable": false,
                "bizCode": "searchResultExp",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"1110\",\"expKey\":\"exp_searchitem_test_0806_G\",\"groupKey\":\"exp_searchitem_test_0806\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_searchitem_test_0806\",\"params\":{\"component\":\"semantics\",\"name\":\"三分类语义模型\",\"strategy\":\"new\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_searchResultExp_exp_searchitem_test_0806\",\"userType\":2}",
                "strategyDesc": "搜索算法实验",
                "versionKey": "G"
            },
            "searchResultStyle": {
                "allEnable": false,
                "bizCode": "searchResultStyle",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "搜索结果样式",
                "versionKey": ""
            },
            "searchSeries": {
                "allEnable": true,
                "bizCode": "searchSeries",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "搜索系列品灰度",
                "versionKey": ""
            },
            "searchTextRecommendExp": {
                "allEnable": false,
                "bizCode": "searchTextRecommendExp",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "搜索底纹词轮播实验",
                "versionKey": ""
            },
            "seriesGoodsOpt": {
                "allEnable": false,
                "bizCode": "seriesGoodsOpt",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "系列品加车等优化",
                "versionKey": ""
            },
            "settleByAtWill": {
                "allEnable": true,
                "bizCode": "settleByAtWill",
                "group": "A",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "结算页随手买一件",
                "versionKey": "A"
            },
            "settleChangeAddress": {
                "allEnable": true,
                "bizCode": "settleChangeAddress",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "结算页切换地址",
                "versionKey": ""
            },
            "showGoodsTag": {
                "allEnable": true,
                "bizCode": "showGoodsTag",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "展示商品标签",
                "versionKey": "B"
            },
            "smallSizePacket": {
                "allEnable": true,
                "bizCode": "smallSizePacket",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "商品小包装价格",
                "versionKey": "B"
            },
            "swiftGray": {
                "allEnable": true,
                "bizCode": "swiftGray",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "接入swift-ios",
                "versionKey": ""
            },
            "topRemake": {
                "allEnable": false,
                "bizCode": "topRemake",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "榜单页重构",
                "versionKey": ""
            },
            "transferToPersonalMainCard": {
                "allEnable": true,
                "bizCode": "transferToPersonalMainCard",
                "group": "A",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "亲友卡/公司卡转个人主卡",
                "versionKey": "A"
            },
            "upgradeExcellenceCardPopup": {
                "allEnable": false,
                "bizCode": "upgradeExcellenceCardPopup",
                "group": "",
                "isOpen": true,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"80\",\"expKey\":\"exp_premium_0829_A\",\"groupKey\":\"exp_premium_0829\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_premium_0829\",\"params\":{\"isGray\":\"true\",\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_upgradeExcellenceCardPopup_exp_premium_0829\",\"userType\":2}",
                "strategyDesc": "升级卓越卡弹窗",
                "versionKey": "A"
            },
            "videoPlayerOpt": {
                "allEnable": false,
                "bizCode": "videoPlayerOpt",
                "group": "",
                "isOpen": false,
                "paramsJson": null,
                "strategyDesc": "视频播放优化",
                "versionKey": ""
            },
            "weblinkcheck": {
                "allEnable": true,
                "bizCode": "weblinkcheck",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "url编码优化",
                "versionKey": ""
            },
            "webviewcheck": {
                "allEnable": true,
                "bizCode": "webviewcheck",
                "group": "",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "webview增加cookie安全校验",
                "versionKey": ""
            },
            "widget3DTouchExp": {
                "allEnable": false,
                "bizCode": "widget3DTouchExp",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"794\",\"expKey\":\"exp_3dtouch_C\",\"groupKey\":\"exp_3dtouch\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_3dtouch\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_widget3DTouchExp_exp_3dtouch\",\"userType\":2}",
                "strategyDesc": "widget3DTouch实验",
                "versionKey": "C"
            },
            "xiliepinSku": {
                "allEnable": true,
                "bizCode": "xiliepinSku",
                "group": "B",
                "isOpen": true,
                "paramsJson": null,
                "strategyDesc": "系列品小图弹出控制",
                "versionKey": "B"
            },
            "xiliepinSkuOpt": {
                "allEnable": false,
                "bizCode": "xiliepinSkuOpt",
                "group": "",
                "isOpen": false,
                "paramsJson": "{\"businessCode\":\"9191\",\"expId\":\"806\",\"expKey\":\"exp_xiliepin_sku_online_A\",\"groupKey\":\"exp_xiliepin_sku_online\",\"guid\":\"1818144697779\",\"kaName\":\"SAMS\",\"layerKey\":\"exp_xiliepin_sku_online\",\"params\":{\"extendInfo\":\"{\\\"deviceInfo\\\":{\\\"appVersion\\\":\\\"5.0.125\\\",\\\"deviceId\\\":\\\"d3e9907ab1881aac891aff90100016e1950c\\\",\\\"deviceType\\\":\\\"android\\\",\\\"systemLanguage\\\":\\\"CN\\\",\\\"userAgent\\\":\\\"okhttp/4.12.0\\\"}}\"},\"qimei\":\"\",\"reportPath\":\"SAMS_online_xiliepinSkuOpt_exp_xiliepin_sku_online\",\"userType\":2}",
                "strategyDesc": "系列品优化V2",
                "versionKey": "A"
            }
        },
        "versionCode": "49ba59abbe56e058"
    },
    "errorMsg": "",
    "msg": "",
    "requestId": "0a96e7adb7a34bed8e639854cd4b27c1.124.17545806800259351",
    "rt": 0,
    "success": true,
    "traceId": "37cac5617d5b60a9"
}
        """
        url = self._base_url + '/api/v1/sams/configuration/portal/getGrayConfig'
        body = {
            "phone": self.mobile,
            "uid": self.uid
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def get_gray_config(self):
        url = self._base_url + '/api/v1/sams/adapter/gray/getGrayConfig'
        body = {
            "cardNo": "",
            "isStoreGray": False,
            "memberStoreId": "",
            "phone": self.mobile,
            "uid": self.uid
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def user_label_scheme_get(self):
        url = self._base_url + '/api/v1/sams/sams-user/user/label_scheme/get'
        body = {
            "type": 2
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def cart_merge_visitor_goods(self):
        url = self._base_url + '/api/v1/sams/trade/cart/mergeVisitorGoods'
        body = {
            "deviceType": "android",
            "uid": self.uid,
            "visitorId": ""
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_get_config(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/getConfig'
        body = {
            "keyId": "info"
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_cnConfig_getTraditionalCnConfig(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/cnConfig/getTraditionalCnConfig'
        body = {
            "keyId": "info"
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def goods_portal_spu_queryXPlusTagImg(self):
        url = self._base_url + '/api/v1/sams/goods-portal/spu/queryXPlusTagImg'
        resp = await self.send(
            url=url,
            method='GET',
            is_add_amap_headers=False
        )
        return resp.json()

    async def channel_portal_AdgroupData_queryAdgroup(self):
        url = self._base_url + '/api/v1/sams/channel/portal/AdgroupData/queryAdgroup'
        body = {
            "adgroupSign": "initpage",
            "source": "ANDROID_APP",
            "storeList": self.storeList,
            "uid": self.uid
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_beUpdate(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/beUpdate'
        body = {
            "androidChannel": "oppo",
            "nowVersion": self.headers_gen.version_str,
            "requestSource": "1"
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def activity_taskreport(self, event_type: int):
        """
        登陆：99

        """
        url = self._base_url + '/api/v1/sams/activity/taskreport'
        body = {
            "events": [
                {
                    "eventData": "",
                    "eventType": event_type
                }
            ],
            "uid": self.uid
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_discoverIcon_getOneIcon(self):
        url = self._base_url + '/api/v1/sams/configuration/discoverIcon/getOneIcon'
        body = {
            "uid": self.uid,
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_getGrayPageConfig(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/getGrayPageConfig'
        body = {}
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_resource_query(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/resource/query'
        body = {
            "name": ""
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()


sams_club_api = SamsClubApi()
if __name__ == '__main__':
    async def _test():
        resp = await sams_club_api.user_profile()
        print(resp)
        # {"data":{"spuId":"1340323","hostItem":"980056231","storeId":"6558","title":"番薯叶 600g","masterBizType":1,"viceBizType":1,"categoryIdList":["10003023","10003240","10004603"],"images":["https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/1963810/ebb8519f-75a9-42d5-a115-f1246b909078_179820200722003646242.jpg?imageMogr2/thumbnail/!80p","https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/1963845/97ce61cd-e28b-401d-a5d5-bc42ee6c4ae0_315720200722003709129.jpg?imageMogr2/thumbnail/!80p"],"imageSizeThreeFour":[],"videos":[],"descVideo":[],"isAvailable":false,"isStoreAvailable":false,"isPutOnSale":false,"sevenDaysReturn":false,"intro":"番薯叶 600g","brandId":"10095137","weight":0.6,"desc":"<p><img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201234/94119c09-95c2-4eb9-ab18-c7aa6dd11e36_452220200723050659327.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201236/7611b8a2-1014-425f-af4a-6eec7e74ec49_699020200723050659401.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201237/1f187a62-2016-4854-911e-b6fd86a75452_323920200723050659476.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201239/98ae614f-8e4a-445e-b12b-e104818f8d64_446020200723050659537.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\"></p>","priceInfo":[],"stockInfo":{"stockQuantity":0,"safeStockQuantity":0,"soldQuantity":0},"limitInfo":[],"tagInfo":[],"newTagInfo":[],"deliveryAttr":3,"favorite":false,"giveaway":false,"spuExtDTO":{"subETitle":"","hostUpc":["2170022000000","2170022000000","2170022000000","2170022000000"],"departmentId":"57","detailVideos":[],"weight":0.6,"deliveryAttr":3,"sevenDaysReturn":false,"giveaway":false,"isAccessory":false,"isRoutine":true,"status":1},"beltInfo":[],"detailVideos":[],"isSerial":false,"spuSpecInfo":[],"specList":{},"specInfo":[],"attrGroupInfo":[{"attrInfo":[{"attrId":"79758","title":"产地","attrValueList":[{}],"isImportant":false}],"attrGroupId":"1","title":"产地"},{"attrInfo":[{"attrId":"79733","title":"净重(g)","attrValueList":[{},{"value":"600"}],"isImportant":false}],"attrGroupId":"7","title":"规格"},{"attrInfo":[{"attrId":"79625","title":"包装","attrValueList":[{"attrValueId":"644722","value":"袋装"}],"isImportant":false}],"attrGroupId":"10","title":"包装"}],"attrInfo":[{"attrId":"79651","title":"进口/国产","attrValueList":[{"attrValueId":"644871","value":"国产"}],"isImportant":false}],"extendedWarrantyList":[],"couponContentList":[],"couponList":[],"promotionList":[],"promotionDetailList":[],"deliveryCapacityCountList":[{"strDate":"2025/05/27 周二","list":[{"startTime":"09:00","endTime":"21:00","closeDate":"2025-05-26","closeTime":"20:00","timeISFull":false,"disabled":false}]}],"isCollectOrder":0,"complianceInfo":{"id":"261038638727561494","value":"山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。\n联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。"},"preSellList":[],"onlyStoreSale":false,"serviceInfo":[],"arrivalEndTimeDesc":"有货，可当日或次日发货，依照您在结算页面选择的配送时间窗而定。","isStoreExtent":false,"isGlobalDirectPurchase":false,"isGlobalOwnPickUp":false,"isAllowDelivery":true,"zoneTypeList":[],"isCrabCard":false,"isShowXPlusTag":false,"isCompare":false,"isGovSpu":false,"standardForIntactGoodsUrl":"https://m-sams.walmartmobile.cn/common/help-center/217","customTabList":[],"isTicket":false},"code":"Success","msg":"","errorMsg":"","traceId":"85aea94bbd506bb4","requestId":"as|4af9157120eb49ccb545f4c1382b458a.101.17481744417475739","rt":0,"success":true}
        # {"data":{"spuId":"1340324","hostItem":"95066","storeId":"6558","title":"飘柔 飘柔家庭绿茶洗发露WS+RJC SHM 12X400ml","masterBizType":1,"viceBizType":1,"categoryIdList":["10003039","10003340","10005326"],"images":["https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2197227/06e20218-1dbd-4da2-9f05-5fb5867df19c_605920200723041907797.jpg?imageMogr2/thumbnail/!80p"],"imageSizeThreeFour":[],"videos":[],"descVideo":[],"isAvailable":false,"isStoreAvailable":false,"isPutOnSale":false,"sevenDaysReturn":true,"intro":"飘柔 飘柔家庭绿茶洗发露WS+RJC SHM 12X400ml","subTitle":"特殊订购商品 需独立购买及到店自提 下单后2周后到货","brandId":"10037226","weight":5.5,"desc":"<p><img border=\"0\" src=\"\">\n<img border=\"0\" src=\"\"></p>","priceInfo":[],"stockInfo":{"stockQuantity":0,"safeStockQuantity":0,"soldQuantity":0},"limitInfo":[],"tagInfo":[],"newTagInfo":[],"favorite":false,"spuExtDTO":{"subTitle":"特殊订购商品 需独立购买及到店自提 下单后2周后到货","subETitle":"","hostUpc":["16903148030470","16903148030470"],"departmentId":"2","detailVideos":[],"weight":5.5,"sevenDaysReturn":true,"status":3},"beltInfo":[],"detailVideos":[],"isSerial":false,"spuSpecInfo":[],"specList":{},"specInfo":[],"attrGroupInfo":[{"attrInfo":[{"attrId":"117093","title":"产地","attrValueList":[{"attrValueId":"1101060","value":"中国大陆"}],"isImportant":false}],"attrGroupId":"1","title":"产地"},{"attrInfo":[{"attrId":"117128","title":"适用对象","attrValueList":[{"attrValueId":"1101280","value":"所有人群"}],"isImportant":false}],"attrGroupId":"2","title":"基本信息"},{"attrInfo":[{"attrId":"117169","title":"净含量（ml/g）","attrValueList":[{},{"value":"4800"}],"isImportant":false}],"attrGroupId":"109","title":"包装规格"}],"attrInfo":[{"attrId":"117122","title":"适合发质","attrValueList":[{"attrValueId":"1101256","value":"油性"}],"isImportant":false},{"attrId":"117066","title":"功效","attrValueList":[{"attrValueId":"1100668","value":"其它"}],"isImportant":false},{"attrId":"117149","title":"单件规格","attrValueList":[{"attrValueId":"1101407","value":"201ml至400ml"}],"isImportant":false}],"extendedWarrantyList":[],"couponContentList":[],"couponList":[],"promotionList":[],"promotionDetailList":[],"deliveryCapacityCountList":[{"strDate":"2025/05/27 周二","list":[{"startTime":"09:00","endTime":"21:00","closeDate":"2025-05-26","closeTime":"20:00","timeISFull":false,"disabled":false}]}],"isCollectOrder":0,"complianceInfo":{"id":"261038638727561494","value":"山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。\n联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。"},"preSellList":[],"onlyStoreSale":false,"serviceInfo":[],"arrivalEndTimeDesc":"有货，实际配送日期根据所在城市情况而定，配送前会与您提前联系确认。","isStoreExtent":false,"isGlobalDirectPurchase":false,"isGlobalOwnPickUp":false,"isAllowDelivery":false,"zoneTypeList":[],"isCrabCard":false,"isShowXPlusTag":false,"isCompare":false,"isGovSpu":false,"standardForIntactGoodsUrl":"https://m-sams.walmartmobile.cn/common/help-center/217","customTabList":[],"isTicket":false},"code":"Success","msg":"","errorMsg":"","traceId":"990087480927d3aa","requestId":"as|456c73a1098e416c92589745bdd853f9.101.17481744569835739","rt":0,"success":true}


    asyncio.run(_test())
