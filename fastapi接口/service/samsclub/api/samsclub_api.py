import asyncio
import json
import os

import aiofiles
from curl_cffi.requests.exceptions import RequestException
from httpx import HTTPError

from fastapi接口.log.base_log import sams_club_logger
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

    async def send(self, url: str, body: dict, *, is_add_amap_headers: bool = True):
        while 1:
            cur_auth_token = self.headers_gen.auth_token
            body_str = self.body_to_json(body)
            headers_model = await self.headers_gen.gen_headers(body_str)
            headers = headers_model.model_dump()
            if is_add_amap_headers:
                headers.update(self.amapHeaders)
            headers.update({'Content-Length': str(len(body_str.encode('utf-8')))})
            try:
                resp = await my_async_httpx.post(
                    url,
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

    async def init_headers_info(self):
        version_resp = await self.configuration_appVersionUpdate_getAppVersionUpdateInfo()
        version_json = version_resp.json()
        if version_str := version_json.get('data', {}).get('youngVersion'):
            self.headers_gen.version_str = version_str

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


sams_club_api = SamsClubApi()
if __name__ == '__main__':
    async def _test():
        resp = await sams_club_api.configuration_appVersionUpdate_getAppVersionUpdateInfo()
        print(resp.text)
        # {"data":{"spuId":"1340323","hostItem":"980056231","storeId":"6558","title":"番薯叶 600g","masterBizType":1,"viceBizType":1,"categoryIdList":["10003023","10003240","10004603"],"images":["https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/1963810/ebb8519f-75a9-42d5-a115-f1246b909078_179820200722003646242.jpg?imageMogr2/thumbnail/!80p","https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/1963845/97ce61cd-e28b-401d-a5d5-bc42ee6c4ae0_315720200722003709129.jpg?imageMogr2/thumbnail/!80p"],"imageSizeThreeFour":[],"videos":[],"descVideo":[],"isAvailable":false,"isStoreAvailable":false,"isPutOnSale":false,"sevenDaysReturn":false,"intro":"番薯叶 600g","brandId":"10095137","weight":0.6,"desc":"<p><img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201234/94119c09-95c2-4eb9-ab18-c7aa6dd11e36_452220200723050659327.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201236/7611b8a2-1014-425f-af4a-6eec7e74ec49_699020200723050659401.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201237/1f187a62-2016-4854-911e-b6fd86a75452_323920200723050659476.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\">\n<img alt=\"Members&nbsp;Mark&nbsp;油麦菜VEGETABLES\" src=\"https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2201239/98ae614f-8e4a-445e-b12b-e104818f8d64_446020200723050659537.jpg?imageMogr2/thumbnail/!80p\" style=\"caret-color: rgb(0, 0, 0); text-size-adjust: auto;\"></p>","priceInfo":[],"stockInfo":{"stockQuantity":0,"safeStockQuantity":0,"soldQuantity":0},"limitInfo":[],"tagInfo":[],"newTagInfo":[],"deliveryAttr":3,"favorite":false,"giveaway":false,"spuExtDTO":{"subETitle":"","hostUpc":["2170022000000","2170022000000","2170022000000","2170022000000"],"departmentId":"57","detailVideos":[],"weight":0.6,"deliveryAttr":3,"sevenDaysReturn":false,"giveaway":false,"isAccessory":false,"isRoutine":true,"status":1},"beltInfo":[],"detailVideos":[],"isSerial":false,"spuSpecInfo":[],"specList":{},"specInfo":[],"attrGroupInfo":[{"attrInfo":[{"attrId":"79758","title":"产地","attrValueList":[{}],"isImportant":false}],"attrGroupId":"1","title":"产地"},{"attrInfo":[{"attrId":"79733","title":"净重(g)","attrValueList":[{},{"value":"600"}],"isImportant":false}],"attrGroupId":"7","title":"规格"},{"attrInfo":[{"attrId":"79625","title":"包装","attrValueList":[{"attrValueId":"644722","value":"袋装"}],"isImportant":false}],"attrGroupId":"10","title":"包装"}],"attrInfo":[{"attrId":"79651","title":"进口/国产","attrValueList":[{"attrValueId":"644871","value":"国产"}],"isImportant":false}],"extendedWarrantyList":[],"couponContentList":[],"couponList":[],"promotionList":[],"promotionDetailList":[],"deliveryCapacityCountList":[{"strDate":"2025/05/27 周二","list":[{"startTime":"09:00","endTime":"21:00","closeDate":"2025-05-26","closeTime":"20:00","timeISFull":false,"disabled":false}]}],"isCollectOrder":0,"complianceInfo":{"id":"261038638727561494","value":"山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。\n联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。"},"preSellList":[],"onlyStoreSale":false,"serviceInfo":[],"arrivalEndTimeDesc":"有货，可当日或次日发货，依照您在结算页面选择的配送时间窗而定。","isStoreExtent":false,"isGlobalDirectPurchase":false,"isGlobalOwnPickUp":false,"isAllowDelivery":true,"zoneTypeList":[],"isCrabCard":false,"isShowXPlusTag":false,"isCompare":false,"isGovSpu":false,"standardForIntactGoodsUrl":"https://m-sams.walmartmobile.cn/common/help-center/217","customTabList":[],"isTicket":false},"code":"Success","msg":"","errorMsg":"","traceId":"85aea94bbd506bb4","requestId":"as|4af9157120eb49ccb545f4c1382b458a.101.17481744417475739","rt":0,"success":true}
        # {"data":{"spuId":"1340324","hostItem":"95066","storeId":"6558","title":"飘柔 飘柔家庭绿茶洗发露WS+RJC SHM 12X400ml","masterBizType":1,"viceBizType":1,"categoryIdList":["10003039","10003340","10005326"],"images":["https://sam-material-online-1302115363.file.myqcloud.com//sams-static/goods/2197227/06e20218-1dbd-4da2-9f05-5fb5867df19c_605920200723041907797.jpg?imageMogr2/thumbnail/!80p"],"imageSizeThreeFour":[],"videos":[],"descVideo":[],"isAvailable":false,"isStoreAvailable":false,"isPutOnSale":false,"sevenDaysReturn":true,"intro":"飘柔 飘柔家庭绿茶洗发露WS+RJC SHM 12X400ml","subTitle":"特殊订购商品 需独立购买及到店自提 下单后2周后到货","brandId":"10037226","weight":5.5,"desc":"<p><img border=\"0\" src=\"\">\n<img border=\"0\" src=\"\"></p>","priceInfo":[],"stockInfo":{"stockQuantity":0,"safeStockQuantity":0,"soldQuantity":0},"limitInfo":[],"tagInfo":[],"newTagInfo":[],"favorite":false,"spuExtDTO":{"subTitle":"特殊订购商品 需独立购买及到店自提 下单后2周后到货","subETitle":"","hostUpc":["16903148030470","16903148030470"],"departmentId":"2","detailVideos":[],"weight":5.5,"sevenDaysReturn":true,"status":3},"beltInfo":[],"detailVideos":[],"isSerial":false,"spuSpecInfo":[],"specList":{},"specInfo":[],"attrGroupInfo":[{"attrInfo":[{"attrId":"117093","title":"产地","attrValueList":[{"attrValueId":"1101060","value":"中国大陆"}],"isImportant":false}],"attrGroupId":"1","title":"产地"},{"attrInfo":[{"attrId":"117128","title":"适用对象","attrValueList":[{"attrValueId":"1101280","value":"所有人群"}],"isImportant":false}],"attrGroupId":"2","title":"基本信息"},{"attrInfo":[{"attrId":"117169","title":"净含量（ml/g）","attrValueList":[{},{"value":"4800"}],"isImportant":false}],"attrGroupId":"109","title":"包装规格"}],"attrInfo":[{"attrId":"117122","title":"适合发质","attrValueList":[{"attrValueId":"1101256","value":"油性"}],"isImportant":false},{"attrId":"117066","title":"功效","attrValueList":[{"attrValueId":"1100668","value":"其它"}],"isImportant":false},{"attrId":"117149","title":"单件规格","attrValueList":[{"attrValueId":"1101407","value":"201ml至400ml"}],"isImportant":false}],"extendedWarrantyList":[],"couponContentList":[],"couponList":[],"promotionList":[],"promotionDetailList":[],"deliveryCapacityCountList":[{"strDate":"2025/05/27 周二","list":[{"startTime":"09:00","endTime":"21:00","closeDate":"2025-05-26","closeTime":"20:00","timeISFull":false,"disabled":false}]}],"isCollectOrder":0,"complianceInfo":{"id":"261038638727561494","value":"山姆品质、馈赠精选，如您有大宗采买需求，我们将为您提供全程专业的采买咨询服务。\n联系我们：山姆app - 我的 - 我的服务 - 福利采购，在线提交采买需求，资深采买顾问为您提供一对一专属服务，让福利采购更省心。"},"preSellList":[],"onlyStoreSale":false,"serviceInfo":[],"arrivalEndTimeDesc":"有货，实际配送日期根据所在城市情况而定，配送前会与您提前联系确认。","isStoreExtent":false,"isGlobalDirectPurchase":false,"isGlobalOwnPickUp":false,"isAllowDelivery":false,"zoneTypeList":[],"isCrabCard":false,"isShowXPlusTag":false,"isCompare":false,"isGovSpu":false,"standardForIntactGoodsUrl":"https://m-sams.walmartmobile.cn/common/help-center/217","customTabList":[],"isTicket":false},"code":"Success","msg":"","errorMsg":"","traceId":"990087480927d3aa","requestId":"as|456c73a1098e416c92589745bdd853f9.101.17481744569835739","rt":0,"success":true}


    asyncio.run(_test())
