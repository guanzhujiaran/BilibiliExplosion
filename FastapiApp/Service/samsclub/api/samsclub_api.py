import asyncio
import datetime
import json
import os
import random
from typing import Literal, NewType

import aiofiles
from curl_cffi import Response
from curl_cffi.requests.exceptions import RequestException
from httpx import HTTPError
from enum import StrEnum
from Models.base.custom_pydantic import CustomBaseModel
from log.base_log import sams_club_logger
from Models.v1.samsclub.api_model import RespUserProfile, ApiResponse, UserProfile
from Models.v1.samsclub.samsclub_model import SamsClubAppStorage, SamsClubGrayConfigStrategy, \
    SamsClubGrayConfigStrategyDetails
from Service.samsclub.exceptions.error import UnknownError
from Service.samsclub.tools.headers_gen import SamsClubHeadersGen, sort_headers_with_missing_last
from Utils.推送.PushMe import a_pushme
from Utils.代理.SealedRequests import my_async_httpx

StringNumber = NewType('StringNumber', str)


class SamsClubApiTokenStatEnum(StrEnum):
    INIT = "初始化"
    FAIL = "失效"
    VALID = "有效"


class SamsClubApiStatus(CustomBaseModel):
    token: str
    token_stat: str
    latest_request_ts: datetime.datetime


class SamsClubApi:
    class FilePath:
        auth_token = os.path.join(os.path.dirname(__file__), 'auth_token.txt')
        app_storage = os.path.join(os.path.dirname(__file__), 'app_storage.json')

    @property
    def status(self) -> SamsClubApiStatus:
        return SamsClubApiStatus(
            token=self.headers_gen.auth_token,
            token_stat=self.token_stat,
            latest_request_ts=self.latest_request_ts
        )

    async def update_auth_token(self, auth_token):
        async with aiofiles.open(self.FilePath.auth_token, 'w', encoding='utf-8') as f:
            await f.write(auth_token)
        self.headers_gen.auth_token = auth_token

    async def save_app_storage(self):
        async with aiofiles.open(self.FilePath.app_storage, 'w', encoding='utf-8') as f:
            await f.write(self.app_storage.model_dump_json(exclude_none=True, exclude={'extra_fields'}))

    def __init__(self):
        self.req_lock = asyncio.Lock()
        self.latest_request_ts = datetime.datetime.now()
        self.token_stat = SamsClubApiTokenStatEnum.INIT
        auth_token = ''
        try:
            if os.path.exists(self.FilePath.auth_token):
                with open(self.FilePath.auth_token, 'r') as f:
                    if f_content := f.read():
                        auth_token = f_content.strip()
            if os.path.exists(self.FilePath.app_storage):
                with open(self.FilePath.app_storage, 'r') as f:
                    app_storage = json.load(f)
                    if app_storage:
                        try:
                            self.app_storage = SamsClubAppStorage.model_validate(app_storage)
                        except Exception as e:
                            self.log.error(f'app_storage文件解析失败：{e}\n{app_storage}')
        except Exception as e:
            self.log.error(f'读取auth_token文件失败：{e}')
        self.headers_gen = SamsClubHeadersGen(
            auth_token=auth_token,
            version_str=self.app_storage.version_str
        )
        self.secret_param_lock = asyncio.Lock()

    isInited = False
    log = sams_club_logger
    _base_url = "https://api-sams.walmartmobile.cn"
    app_storage: SamsClubAppStorage = SamsClubAppStorage()
    addressVO = {
        "cityName": "上海市",
        "countryName": "",
        "detailAddress": "",
        "districtName": "宝山区",
        "provinceName": "上海市"
    }
    amapHeaders = {
        "provinceCode": "310000",
        "cityCode": "310100",
        "districtCode": "310113",
        "amapProvinceCode": "310000",
        "amapCityCode": "310100",
        "amapDistrictCode": "310113"
    }
    gray_config_strategyDetails: SamsClubGrayConfigStrategy
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
                async with self.secret_param_lock:
                    if siv != self.cur_siv or ssk != self.cur_ssk:
                        self.log.debug("更新加密密钥")
                        await self.headers_gen.update_do_encrypt_key(siv, ssk, srd)
                        self.cur_siv = siv
                        self.cur_ssk = ssk
                        return True
        return False

    @property
    def storeListInt(self):
        return [int(x) for x in self.app_storage.storeList]

    @property
    def storeListStr(self):
        return [str(x) for x in self.app_storage.storeList]

    @property
    def base_url(self):
        return self._base_url

    def body_to_json(self, body):
        return json.dumps(body, ensure_ascii=False, separators=(',', ':'))

    async def send(
            self,
            url: str,
            body: dict | list | None = None,
            method: Literal["POST", "GET"] | None = "POST",
            params: dict | None = None,
            *,
            is_add_amap_headers: bool = True
    ):
        while 1:
            async with self.req_lock:
                if self.isInited:
                    for i in range(random.choice(range(10))):
                        await self.__empty_request()
                self.latest_request_ts = datetime.datetime.now()
                cur_auth_token = self.headers_gen.auth_token
                body_str = self.body_to_json(body) if body else ''
                headers_model = await self.headers_gen.gen_headers(body_str)
                headers = headers_model.model_dump()
                if is_add_amap_headers:
                    headers.update(self.amapHeaders)
                headers.update({'Content-Length': str(len(body_str.encode('utf-8')))})
                try:
                    self.log.debug(f'请求：{url} {method} {body_str}')
                    resp: Response = await my_async_httpx.request(
                        url,
                        method=method,
                        params=params,
                        headers=sort_headers_with_missing_last(headers),
                        data=body_str,
                        # proxies=CONFIG.custom_proxy
                    )
                except (RequestException, HTTPError) as e:
                    self.log.exception(f'curl_cffi网络请求异常：{e}')
                    await asyncio.sleep(30)
                    continue
                except Exception as e:
                    self.log.exception(f'curl_cffi网络请求未知异常：{e}')
                    raise e
                is_updated = await self.update_encrypt_key(resp.headers)
                is_succ = await self.handle_resp_code(resp, auth_token=cur_auth_token,
                                                      is_updated_encrypt_key=is_updated)
                if not is_succ:
                    await asyncio.sleep(10)
                    continue
                self.token_stat = SamsClubApiTokenStatEnum.VALID
                self.log.info(f'请求成功：{resp.text}')
                return resp

    async def get_recommend_store_list_by_location(self):

        url = self._base_url + '/api/v1/sams/merchant/storeApi/getRecommendStoreListByLocation'
        body = {
            "latitude": self.headers_gen.latitude,
            "longitude": self.headers_gen.longitude
        }
        return await self.send(url, body=body, is_add_amap_headers=False)

    async def handle_resp_code(self, response: Response, auth_token: str, is_updated_encrypt_key: bool) -> bool:
        try:
            resp_dict = response.json()
        except Exception as e:
            self.log.exception(f'json序列化失败：{response.request}\n{response.text}')
            await a_pushme(f'samsclub API请求失败！', f'json序列化失败，可能被风控！：{response.request}\n{response.text}')
            await asyncio.sleep(1800)
            await self.init_api_info()
            return False
        is_succ = resp_dict.get('success')
        resp_code = resp_dict.get('code')
        resp_msg = resp_dict.get('msg')
        if is_succ is not True:
            self.token_stat = SamsClubApiTokenStatEnum.FAIL
            match resp_code:
                case "SPU_NOT_EXIST":
                    self.log.critical(f'商品不存在：{resp_dict}')
                case "INTERNAL_ERROR":
                    self.log.critical(f'服务器内部错误：{response.request.url}'
                                      f'\n{response.request.headers}'
                                      f'\n{response.request}'
                                      f'\n{resp_dict}')
                    await asyncio.sleep(120)
                case "AUTH_FAIL":
                    if is_updated_encrypt_key:
                        return False
                    self.log.critical(f"被强制登出，等待token更新：{resp_dict}")
                    await a_pushme(f'山姆会员商店token失效', f'{resp_dict}')
                    while 1:
                        if auth_token != self.headers_gen.auth_token:
                            break
                        await asyncio.sleep(3)
                    self.log.critical(f'token更新成功：{self.headers_gen.auth_token}')
                case "BUSYNESS":
                    self.log.critical(f'服务器繁忙：{resp_msg}')
                    await asyncio.sleep(60)
                case _:
                    self.log.critical(f"请求未知错误！{resp_dict}")
                    raise UnknownError(f"未知响应code：{resp_dict}")
        return bool(is_succ)

    async def __init_address(self):
        self.isInited = False
        if self.app_storage.storeList and self.app_storage.storeInfoVOList: return
        store_info_resp = await self.get_recommend_store_list_by_location()
        store_info_resp_dict = store_info_resp.json()
        if store_info_resp_data := store_info_resp_dict.get('data', {}).get('storeList'):
            self.app_storage.storeList = []  # 字符串的store_id
            self.app_storage.storeInfoVOList = []  # like
            for x in store_info_resp_data:
                self.app_storage.storeList.append(x.get('storeId'))
                da = {
                    "storeType": int(x.get('storeType')),
                    "storeId": int(x.get('storeId')),
                    "storeDeliveryAttr": x.get('allDeliveryAttrList'),
                    "storeDeliveryTemplateId": int(
                        x.get('storeRecmdDeliveryTemplateData').get('storeDeliveryTemplateId'))
                }
                self.app_storage.storeInfoVOList.append(da)
        self.isInited = True

    async def __init_user(self):
        if self.app_storage.uid and self.app_storage.mobile: return
        resp: ApiResponse[UserProfile] = await self.user_profile()
        self.log.debug(f'用户信息：{resp}')
        self.app_storage.uid = resp.data.uid
        self.app_storage.mobile = resp.data.mobile

    async def __empty_request(self):
        await self.headers_gen.get_fetch_cnt()
        self.headers_gen.random_gen.nextInt()

    async def init_api_info(self):
        self.headers_gen = SamsClubHeadersGen(  # 重新实例化一个
            auth_token=self.headers_gen.auth_token,
            version_str=self.app_storage.version_str
        )
        await self.__init_user()
        await self.__init_address()
        await self.save_app_storage()

        # region 账号初始化 根据请求的cnt编写
        await self.configuration_portal_get_config()  # 101
        await self.channel_portal_AdgroupData_queryAdgroup(is_int_store_list=False)  # 102
        await self.goods_portal_spu_queryXPlusTagImg()  # 103
        await self.configuration_portal_cnConfig_getTraditionalCnConfig()  # 104
        await self.configuration_portal_cnConfig_getTraditionalCnConfig()  # 105
        await self.goods_portal_spu_queryXPlusTagImg()  # 106
        await self.activity_taskreport(99)  # 107
        await self.configuration_portal_beUpdate()  # 108
        await self.configuration_portal_get_config()  # 110
        await self.__empty_request()  # 111
        await self.configuration_discoverIcon_getOneIcon()  # 112
        await self.__empty_request()  # 113
        await self.configuration_portal_get_config()  # 114
        await self.configuration_portal_getGrayPageConfig()  # 115
        await self.configuration_portal_resource_query()  # 116
        gray_config_resp_dict = await self.configuration_portal_getGrayConfig()  # 117
        self.gray_config_strategyDetails = SamsClubGrayConfigStrategy.model_validate(
            gray_config_resp_dict.get('data', {}).get('strategyDetails'))
        await self.goods_portal_spu_queryNewDetailsGoods()  # 118
        await self.get_gray_config()  # 119
        await self.configuration_abtest_portal_report(
            self.gray_config_strategyDetails.goodsDetailParamPk
        )  # 120
        await self.configuration_abtest_portal_report(
            self.gray_config_strategyDetails.categoryAddCartRecom
        )  # 121
        await self.configuration_abtest_portal_report(
            self.gray_config_strategyDetails.widget3DTouchExp
        )  # 122
        await self.configuration_abtest_portal_report(
            self.gray_config_strategyDetails.newTagManageExp
        )  # 123
        await self.__empty_request()  # 124
        await self.__empty_request()  # 125
        await self.decoration_portal_show_homePageRecommendByLocation()  # 126
        await self.configuration_searchTextConf_queryList()  # 127
        await self.sams_user_window_getGoUpPlus()  # 128
        await self.message_portal_systemMessage_getTotalUnreadCount()  # 129
        await self.sams_user_membership_query_return_card_floating_window()  # 130
        await self.sams_user_window_get()  # 131
        await self.get_hk_mc_buy_card_info()  # 132
        await self.channel_portal_suspension_getSuspensionImg()  # 133
        await self.user_tag_user_select()  # 134
        await self.trade_cart_getTotalGoodsNum()  # 135
        await self.merchant_addressApi_getHomeAddress()  # 136
        await self.channel_portal_AdgroupData_queryAdgroup(is_int_store_list=True)  # 137
        await self.merchant_visitStoreApi_getStoreByLocation()  # 138
        await self.activity_taskreport(10)  # 139
        await self.__empty_request()  # 140 实际应该zhls上报
        await self.sams_user_user_member_card_info()  # 141
        await self.__init_address()  # 142
        await self.__empty_request()  # 143 实际应该zhls上报
        await self.get_hk_mc_buy_card_info()  # 144
        await self.sams_user_window_upload_avatar_window()  # 145
        await self.channel_portal_AdgroupData_queryNonmemberAd()  # 146
        await self.configuration_searchTextConf_queryList()  # 147
        await self.__empty_request()  # 148
        await self.__empty_request()  # 149
        await self.__empty_request()  # 150
        await self.__empty_request()  # 151
        await self.__empty_request()  # 152
        await self.merchant_addressApi_getAddressCodes()  # 153
        await self.decoration_portal_show_homePageRecommendByLocation()  # 154
        await self.__empty_request()  # 155
        await self.__empty_request()  # 156
        await self.__empty_request()  # 157
        await self.configuration_getZoneTip()  # 158
        await self.__empty_request()  # 159
        await self.__empty_request()  # 160
        await self.sams_user_agreement_user_check_login()
        await self.sams_user_agreement_check()
        await self.message_portal_uidToken_registerUidToken()  # 109
        await self.sams_user_experience_card_new_get()
        await self.sams_user_screen_promotion_get()
        await self.sams_user_reward_receipt_state()
        # endregion

        version_resp = await self.configuration_appVersionUpdate_getAppVersionUpdateInfo()
        version_json = version_resp.json()
        if version_str := version_json.get('data', {}).get('oldVersion'):
            self.headers_gen.version_str = version_str
            self.app_storage.version_str = version_str
        await self.__init_user()
        await self.save_app_storage()
        self.log.debug(
            f'初始化headers信息成功\n{version_str}\n{self.app_storage.storeList}\n{self.app_storage.storeInfoVOList}')

    async def configuration_appVersionUpdate_getAppVersionUpdateInfo(self):
        url = self._base_url + '/api/v1/sams/configuration/appVersionUpdate/getAppVersionUpdateInfo'
        body = {
            "nowVersion": self.headers_gen.version_str,
            "androidChannel": "oppo",
            "requestSource": "2"
        }
        return await self.send(
            url=url,
            body=body,
            method="POST",
            is_add_amap_headers=True
        )

    async def spu_query_detail(self, spuId: int):
        """
    查询商品详细信息

    Args:
        spuId (int): 商品SPU ID

    Returns:
        dict: 包含商品详细信息的字典，结构如下:
            - code (str): 请求状态码
            - data (dict): 商品详情数据，包含以下字段:
                - arrivalEndTimeDesc (str): 到货时间描述
                - attrGroupInfo (list): 属性分组信息
                - attrInfo (list): 商品属性列表
                - brandId (str): 品牌ID
                - categoryIdList (list): 分类ID列表
                - desc (str): 商品描述(HTML格式)
                - images (list): 商品图片URL列表
                - intro (str): 商品简介
                - priceInfo (list): 价格信息
                - spuId (str): 商品SPU ID
                - title (str): 商品标题
                - 其他字段详见返回示例
                {'code': 'Success', 'data': {'arrivalEndTimeDesc': '有货，可当日或次日发货，依照您在结算页面选择的配送时间窗而定。', 'attrGroupInfo': [], 'attrInfo': [{'attrId': '155408', 'attrValueList': [{}, {'value': '1.5kg'}], 'isImportant': False, 'title': '净含量'}, {'attrId': '155409', 'attrValueList': [{'attrValueId': '1136346', 'value': '国产'}], 'isImportant': False, 'title': '进口/国产'}], 'beltInfo': [], 'brandId': '10196732', 'categoryIdList': ['10003023', '10003239', '10011865', '10011889'], 'complianceInfo': {'id': '261038638727561494', 'value': '山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。
        联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。'}, 'couponContentList': [], 'couponList': [], 'customTabList': [], 'deliveryAttr': 3, 'deliveryCapacityCountList': [{'list': [{'closeDate': '2025-09-19', 'closeTime': '20:00', 'disabled': False, 'endTime': '21:00', 'startTime': '09:00', 'timeISFull': False}], 'strDate': '2025/09/20 周六'}], 'desc': '<p><img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567487338160129.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567488055382016.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567487807930369.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567488701321216.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567489682771968.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567490328690688.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567491620544512.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567491972870144.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567492681695233.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567493373759488.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8556881118377107457.jpg?imageMogr2/thumbnail/!80p/ignore-error/1">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8567017512294510592.png">
        <img src="https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/42/bktsitem-ops-prod-8587247830783827969.jpg?imageMogr2/thumbnail/!80p/ignore-error/1"></p>', 'descVideo': [], 'detailVideos': [], 'extendedWarrantyList': [], 'favorite': False, 'giveaway': False, 'hostItem': '867980', 'imageSizeThreeFour': [], 'images': ['https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274468843521.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567279191625729.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275232206849.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274435301377.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275668418561.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274124906497.jpg?imageMogr2/thumbnail/!80p/ignore-error/1', 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567275953618945.jpg?imageMogr2/thumbnail/!80p/ignore-error/1'], 'intro': '脆宝香瓜 1.5kg', 'isAllowDelivery': True, 'isAvailable': False, 'isCollectOrder': 0, 'isCompare': False, 'isCrabCard': False, 'isGlobalDirectPurchase': False, 'isGlobalOwnPickUp': False, 'isGovSpu': False, 'isImport': False, 'isPutOnSale': False, 'isSerial': False, 'isShowXPlusTag': False, 'isStoreAvailable': False, 'isStoreExtent': False, 'isTicket': False, 'limitInfo': [], 'masterBizType': 1, 'netWeight': 1.58, 'newTagInfo': [], 'onlyBarSale': False, 'onlyStoreSale': False, 'preSellList': [], 'priceInfo': [], 'promotionDetailList': [], 'promotionList': [], 'serviceInfo': [], 'sevenDaysReturn': False, 'specInfo': [], 'specList': {}, 'spuExtDTO': {'deliveryAttr': 3, 'departmentId': '56', 'detailVideos': [], 'giveaway': False, 'hostUpc': ['2160844000005', '6925945901028', '2160844000005', '2160844000005'], 'intro': '脆宝香瓜 1.5kg', 'isAccessory': False, 'isImport': False, 'isRoutine': True, 'netWeight': 1.58, 'sevenDaysReturn': False, 'smallPackageNum': 1, 'smallPackageUnit': 'kg', 'status': 5, 'subETitle': 'Fruit; Fresh Melons', 'subTitle': '果肉细腻， 香甜多汁，因为成熟度和光照原因，部分果面会有发黄现象', 'temperature': 1.0, 'thumbnailImage': 'https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/190776/bktpromotion-e2e-prod-8602567274468843521.jpg', 'valuable': True, 'weight': 1.58}, 'spuId': '1333962', 'spuSpecInfo': [], 'standardForIntactGoodsUrl': 'https://m-sams.walmartmobile.cn/common/help-center/217', 'stockInfo': {'safeStockQuantity': 0, 'soldQuantity': 0, 'stockQuantity': 0}, 'storeId': '6558', 'subTitle': '果肉细腻， 香甜多汁，因为成熟度和光照原因，部分果面会有发黄现象', 'tagInfo': [{'id': '1', 'tagMark': 'aboveTheLimitTag', 'tagPlace': 10, 'title': '6.1万人回购'}], 'temperature': 1.0, 'title': '脆宝香瓜 1.5kg', 'valuable': True, 'viceBizType': 1, 'videos': [], 'weight': 1.58, 'zoneTypeList': []}, 'errorMsg': '', 'msg': '', 'requestId': 'as|c6b03323e7ce44a19d9a5c6b9a10389d.101.17582432110405739', 'rt': 0, 'success': True, 'traceId': '72fa312a68001fb5'}

    """
        url = self._base_url + '/api/v1/sams/goods-portal/spu/queryDetail'
        body = {
            "source": "ANDROID",
            "channel": 1,
            "spuId": int(spuId),
            "uid": str(self.app_storage.uid),
            "addressVO": self.addressVO,
            "isTagEntryAbtTest": True,
            "locationSwitch": True,
            "storeInfoVOList": self.app_storage.storeInfoVOList,
        }
        return await self.send(url, body, is_add_amap_headers=True)

    async def grouping_query_navigation(self):
        """
        {"data":{"dataList":[{"groupingId":"35145","title":"肉蛋果蔬","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/737598112dde476b80f16388af176bb7-1747981873486.jpg","storeId":"-1","children":[]},{"groupingId":"156048","title":"乳品烘焙","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/1d3c5674d2f84621987d7ad83935b99e-1747808674432.png","storeId":"-1","children":[]},{"groupingId":"156050","title":"速食冷冻","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/5319ba9de401426cba6cd25d38330a19-1747130076819.png","storeId":"-1","children":[]},{"groupingId":"34112","title":"休闲零食","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/db859a706fd441fdb0a76f3141512e91-1747130076493.png","storeId":"-1","children":[]},{"groupingId":"34118","title":"酒水饮料","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/6caf4405b9a54de9b91d1dabac7f930d-1747130076315.png","storeId":"-1","children":[]},{"groupingId":"114131","title":"粮油干货","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/4f6b1109ce504b0fb9d3fc85f1e2a2bd-1745462110598.png","storeId":"-1","children":[]},{"groupingId":"113105","title":"个护美妆","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/159366599fe2465f8dc41725293c64ad-1747130075985.png","storeId":"-1","children":[]},{"groupingId":"34138","title":"母婴玩具","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/7d4fdd2642f040c68a95c6fed3323d3a-1747130671688.png","storeId":"-1","children":[]},{"groupingId":"35108","title":"全球购","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/c92e589a28344785b8db64fca8e13396-1745462127490.png","storeId":"-1","children":[]},{"groupingId":"226203","title":"家清纸品","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/6c62b39464d14a8695fba078be98c551-1745462110153.png","storeId":"-1","children":[]},{"groupingId":"113114","title":"家电家居","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/64564235a4a045a88e6b1d675df3cead-1747130076105.png","storeId":"-1","children":[]},{"groupingId":"227225","title":"服饰家纺","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/89e25d19e248408db3a51c0a845a38b6-1747130075756.png","storeId":"-1","children":[]},{"groupingId":"225226","title":"营养保健","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/175f064e283046719c5a9549b37d025c-1747130075307.png","storeId":"-1","children":[]},{"groupingId":"34145","title":"萌宠生活","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/020168775/material/1/f1e0bac821134f5cb95760b50f2ae421-1747130075542.png","storeId":"-1","children":[]},{"groupingId":"226209","title":"眼镜助听","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/558752e1680b4addbc0e4dd6358bd14e-1745462128233.png","storeId":"-1","children":[]},{"groupingId":"87055","title":"线上专享","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/10efca2b8e6d451e91623ea5b89866f6-1745462128104.png","storeId":"-1","children":[]},{"groupingId":"182207","title":"礼品卡","isFastDelivery":false,"level":1,"navigationId":"1","image":"https://sam-material-online-1302115363.file.myqcloud.com/persist/3e89d264-b317-4241-a9df-4292c90871a7/1818/024307827/material/1/bc01a5c7de744bc09dc8c90f1852871f-1745462110388.png","storeId":"-1","children":[]}],"cardFilterList":[],"searchFilterList":[],"searchAfter":[],"reportInfo":"","hasNextPage":false,"onlyShowSimilarButton":false},"code":"Success","msg":"","errorMsg":"","traceId":"16d3a7318c737acf","requestId":"106560fa03e344ce9f9056c609accd72.101.17481870958365739","rt":0,"success":true}
        :return:
        """

        url = self._base_url + '/api/v1/sams/goods-portal/grouping/queryNavigation'
        body = {
            "storeCategoryList": self.app_storage.storeInfoVOList,
            "isNew": True
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
            "storeCategoryList": self.app_storage.storeInfoVOList,
            "groupingId": int(groupingId),
            "navigationId": navigationId,
            "uid": self.app_storage.uid
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
            "storeInfoVOList": self.app_storage.storeInfoVOList,
            "uid": self.app_storage.uid,
            "pageNum": int(pageNum),
            "useNew": True,
            "isTagEntryAbtTest": True,
            "isReversOrder": False,
            "isFastDelivery": False,
            "recommendFirstCategoryId": firstCategoryId,
            "recommendSecondCategoryId": SecondCategoryId,
            "showSeriesIcon": False,
            "frontCategoryIds": frontCategoryIds,
            "secondCategoryId": SecondCategoryId,
            "isShowCustomTag": True
        }
        resp = await self.send(url, body, is_add_amap_headers=True)
        await self.configuration_abtest_portal_report(
            self.gray_config_strategyDetails.categoryRecommend
        )
        return resp

    async def user_profile(self) -> ApiResponse[UserProfile]:
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
        resp_user_profile = RespUserProfile.validate_json(resp.text)
        return resp_user_profile

    # region 日志操作相关api
    async def sams_user_user_member_card_info(self):
        url = self._base_url + '/api/v1/sams/sams-user/user/member_card_info'
        resp = await self.send(
            url,
            method='GET',
            is_add_amap_headers=False
        )
        return resp.json()

    async def sams_user_window_upload_avatar_window(self):
        url = self._base_url + '/api/v1/sams/sams-user/window/upload_avatar_window'
        resp = await self.send(
            url,
            method='GET',
            is_add_amap_headers=False
        )
        return resp.json()

    async def merchant_visitStoreApi_getStoreByLocation(self):
        url = self._base_url + '/api/v1/sams/merchant/visitStoreApi/getStoreByLocation'
        body = {"uid": self.app_storage.uid, "longitude": str(self.headers_gen.longitude),
                "latitude": str(self.headers_gen.latitude),
                "locationSwitch": True}

        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def merchant_addressApi_getAddressCodes(self):
        url = self._base_url + '/api/v1/sams/merchant/addressApi/getAddressCodes'
        resp = await self.send(
            url,
            body=None,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def merchant_addressApi_getHomeAddress(self):
        url = self._base_url + '/api/v1/sams/merchant/addressApi/getHomeAddress'
        body = {"uid": self.app_storage.uid, "latitude": self.headers_gen.latitude,
                "longitude": self.headers_gen.longitude,
                "isOpenPosition": 1}
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def trade_cart_getTotalGoodsNum(self):
        url = self._base_url + '/api/v1/sams/trade/cart/getTotalGoodsNum'
        body = {
            "uid": self.app_storage.uid
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def channel_portal_suspension_getSuspensionImg(self):
        url = self._base_url + '/api/v1/sams/channel/portal/suspension/getSuspensionImg'
        resp = await self.send(
            url,
            body=None,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def sams_user_reward_receipt_state(self):
        url = self._base_url + '/api/v1/sams/sams-user/reward/receipt_state'
        resp = await self.send(
            url,
            method='GET',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_screen_promotion_get(self):
        url = self._base_url + '/api/v1/sams/sams-user/screen_promotion/get'
        body = {
            "bindedStatus": 0,
            "isOpenPush": 1,
            "storeIds": self.storeListInt,
            "uid": self.app_storage.uid,
            "userAction": 1,
            "userIdentity": self.headers_gen.device_uuid_str,
            "storeInfoList": self.app_storage.storeInfoVOList
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_experience_card_new_get(self):
        url = self._base_url + '/api/v1/sams/sams-user/experience-card/new/get'
        resp = await self.send(
            url,
            method='GET',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_agreement_check(self):
        url = self._base_url + '/api/v1/sams/sams-user/agreement/check'
        body = {
            "agreementType": 6
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_agreement_user_check_login(self):
        url = self._base_url + '/api/v1/sams/sams-user/agreement/user/check_login'
        body = {
            "channel": "app",
            "userSign": self.headers_gen.device_str
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_window_get(self):
        url = self._base_url + '/api/v1/sams/sams-user/window/get'
        body = {"uid": self.app_storage.uid, "experienceCardFlag": 1, "activityFlag": 1, "isClosedRiskPop": 0,
                "isLimitFrequency": True}
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_membership_query_return_card_floating_window(self):
        url = self._base_url + '/api/v1/sams/sams-user/membership/query_return_card_floating_window'
        body = {
            "scene": 1
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def message_portal_systemMessage_getTotalUnreadCount(self):
        url = self._base_url + '/api/v1/sams/message/portal/systemMessage/getTotalUnreadCount'
        body = {
            "channel": 1,
            "uid": self.app_storage.uid,
            "storeIdList": self.storeListInt,
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def sams_user_window_getGoUpPlus(self):
        url = self._base_url + '/api/v1/sams/sams-user/window/getGoUpPlus'
        body = {
            "sceneType": 1,
            "isReward": True,
            "uid": self.app_storage.uid
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True,
        )
        return resp.json()

    async def configuration_getZoneTip(self):
        url = self._base_url + '/api/v1/sams/configuration/getZoneTip'
        body = {
            "sceneType": 1,
            "lastTimeLatitude": self.headers_gen.latitude,
            "lastTimeLongitude": self.headers_gen.longitude,
        }
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def configuration_abtest_portal_report(self, gray_config_strategy_details: SamsClubGrayConfigStrategyDetails):
        if not gray_config_strategy_details.paramsJson:
            self.log.critical(f"{gray_config_strategy_details} gray_config_strategy_details.paramsJson is None")
            return {}
        url = self._base_url + '/api/v1/sams/configuration/abtest/portal/report'
        body = [
            json.loads(gray_config_strategy_details.paramsJson)
        ]
        resp = await self.send(
            url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def goods_portal_spu_queryNewDetailsGoods(self):
        url = self._base_url + '/api/v1/sams/goods-portal/spu/queryNewDetailsGoods'
        body = {}
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def decoration_portal_show_homePageRecommendByLocation(self):
        url = self._base_url + '/api/v1/sams/decoration/portal/show/homePageRecommendByLocation'
        body = {
            'apiVersion': 1,
            'longitude': self.headers_gen.longitude,
            'latitude': self.headers_gen.latitude,
            'authorize': True,
            'uid': self.app_storage.uid,
            'addressInfo': {
                "cityCode": "",
                "districtCode": "",
                "provinceCode": "",
                "receiverAddress": "定位失败，请手动选择地址"
            },
            'isOpenRecommend': True,
            'storeInfoList': self.app_storage.storeInfoVOList
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_searchTextConf_queryList(self):
        url = self._base_url + '/api/v1/sams/configuration/searchTextConf/queryList'
        body = {
            "storeIdList": self.storeListInt
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=False
        )
        return resp.json()

    async def configuration_portal_getGrayConfig(self) -> dict:
        url = self._base_url + '/api/v1/sams/configuration/portal/getGrayConfig'
        body = {
            "uid": self.app_storage.uid,
            "phone": self.app_storage.mobile
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def get_gray_config(self):
        url = self._base_url + '/api/v1/sams/adapter/gray/getGrayConfig'
        body = {"cardNo": "", "isStoreGray": False, "memberStoreId": "", "phone": self.app_storage.mobile,
                "uid": self.app_storage.uid}
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

    async def configuration_portal_get_config(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/getConfig'
        body = {
            "keyId": "info"
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
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

    async def channel_portal_AdgroupData_queryNonmemberAd(self):
        url = self._base_url + '/api/v1/sams/channel/portal/AdgroupData/queryNonmemberAd'
        body = {
            "adGroupSubType": 1
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def channel_portal_AdgroupData_queryAdgroup(self, is_int_store_list: bool = False):
        url = self._base_url + '/api/v1/sams/channel/portal/AdgroupData/queryAdgroup'
        store_list = self.storeListInt if is_int_store_list else self.storeListStr
        body = {
            "uid": self.app_storage.uid,
            "source": "ANDROID_APP",
            "adgroupSign": "homePageActivity",
            "storeList": store_list
        }

        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def configuration_portal_beUpdate(self):
        url = self._base_url + '/api/v1/sams/configuration/portal/beUpdate'
        body = {
            "nowVersion": self.headers_gen.version_str,
            "androidChannel": "oppo",
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
            "uid": self.app_storage.uid
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
            "uid": self.app_storage.uid,
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
            is_add_amap_headers=True
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
            is_add_amap_headers=True
        )
        return resp.json()

    async def message_portal_uidToken_registerUidToken(self):
        url = self._base_url + '/api/v1/sams/message/portal/uidToken/registerUidToken'
        body = {
            "deviceType": 1,
            "token": "0499024e9d0eb03eb52095ed6b62e0b2d930",
            "pushOpen": "1",
            "uid": self.app_storage.uid
        }
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()

    async def user_tag_user_select(self):
        url = self._base_url + '/api/v1/sams/sams-user/user/tag/user_select?userInfoTypeFlag=1'
        resp = await self.send(
            url=url,
            method='GET',
            is_add_amap_headers=False
        )
        return resp.json()

    async def get_hk_mc_buy_card_info(self):
        url = self._base_url + '/api/v1/sams/sams-user/user/get_hk_mc_buy_card_info'
        body = {}
        resp = await self.send(
            url=url,
            body=body,
            method='POST',
            is_add_amap_headers=True
        )
        return resp.json()
    # endregion


sams_club_api = SamsClubApi()
if __name__ == '__main__':
    async def _test():
        await sams_club_api.init_api_info()
        resp = await sams_club_api.spu_query_detail(
            spuId=1333962
        )
        print(resp)


    asyncio.run(_test())
