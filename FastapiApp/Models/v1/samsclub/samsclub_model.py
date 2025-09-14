from pydantic import Field, ConfigDict
from typing import Dict

from Models.base.custom_pydantic import CustomBaseModel


class SamsClubGrayConfigStrategyDetails(CustomBaseModel):
    allEnable: bool
    bizCode: str
    group: str
    isOpen: bool
    paramsJson: str | None
    strategyDesc: str
    versionKey: str


class SamsClubGrayConfigStrategy(CustomBaseModel):
    """
    用于存储动态的灰度策略配置，key 为策略名称（如 reportHandler），value 为对应的配置详情。
    """
    CN2TCGray: SamsClubGrayConfigStrategyDetails
    addCartExp: SamsClubGrayConfigStrategyDetails
    addrAccurateSearch: SamsClubGrayConfigStrategyDetails
    addressCode: SamsClubGrayConfigStrategyDetails
    apartOrder: SamsClubGrayConfigStrategyDetails
    appDecorationReconstruction: SamsClubGrayConfigStrategyDetails
    appLoadingOpt: SamsClubGrayConfigStrategyDetails
    appSearchGray: SamsClubGrayConfigStrategyDetails
    applicableGoods: SamsClubGrayConfigStrategyDetails
    associatedWordExp: SamsClubGrayConfigStrategyDetails
    associatedWordExp1: SamsClubGrayConfigStrategyDetails
    bankcommMemberCard: SamsClubGrayConfigStrategyDetails
    bannerComment: SamsClubGrayConfigStrategyDetails
    becomeMemberExp: SamsClubGrayConfigStrategyDetails
    buyOneAbt: SamsClubGrayConfigStrategyDetails
    cartRestructure: SamsClubGrayConfigStrategyDetails
    cartRestructureV2: SamsClubGrayConfigStrategyDetails
    categoryAddCartRecom: SamsClubGrayConfigStrategyDetails
    categoryOpt: SamsClubGrayConfigStrategyDetails
    categoryRecommend: SamsClubGrayConfigStrategyDetails
    commentSearchText: SamsClubGrayConfigStrategyDetails
    commentVideoCompression: SamsClubGrayConfigStrategyDetails
    customerServiceSdk: SamsClubGrayConfigStrategyDetails
    decoration: SamsClubGrayConfigStrategyDetails
    discover: SamsClubGrayConfigStrategyDetails
    expNewUserGiftMiniProKey: SamsClubGrayConfigStrategyDetails
    expireMemberCardSupportDowngraded: SamsClubGrayConfigStrategyDetails
    goodsDetailBlankPageOpt: SamsClubGrayConfigStrategyDetails
    goodsDetailNewTest: SamsClubGrayConfigStrategyDetails
    goodsDetailOpt: SamsClubGrayConfigStrategyDetails
    goodsDetailPageRecommendOpt: SamsClubGrayConfigStrategyDetails
    goodsDetailParamPk: SamsClubGrayConfigStrategyDetails
    goodsDetailStockReveal: SamsClubGrayConfigStrategyDetails
    goodsThumbnail: SamsClubGrayConfigStrategyDetails
    hippyKitchen: SamsClubGrayConfigStrategyDetails
    hippyResource: SamsClubGrayConfigStrategyDetails
    hippyResource1: SamsClubGrayConfigStrategyDetails
    hippyShowOrder: SamsClubGrayConfigStrategyDetails
    hippySpt: SamsClubGrayConfigStrategyDetails
    hippyVideoFeed: SamsClubGrayConfigStrategyDetails
    homeAddAddressFloat: SamsClubGrayConfigStrategyDetails
    homeThreeGoodsModule: SamsClubGrayConfigStrategyDetails
    inviteGifts: SamsClubGrayConfigStrategyDetails
    justStoreSaleSplit: SamsClubGrayConfigStrategyDetails
    memberCreateCardPageOpt: SamsClubGrayConfigStrategyDetails
    memberCreateCardPageOptMiniProgram: SamsClubGrayConfigStrategyDetails
    memberGuide: SamsClubGrayConfigStrategyDetails
    memberUnionPay: SamsClubGrayConfigStrategyDetails
    messageCenterGray: SamsClubGrayConfigStrategyDetails
    midSearchPage: SamsClubGrayConfigStrategyDetails
    mineHeadGray: SamsClubGrayConfigStrategyDetails
    miniGoodsDetailBuyCardExp: SamsClubGrayConfigStrategyDetails
    miniHomePage: SamsClubGrayConfigStrategyDetails
    newMemberRenewPage: SamsClubGrayConfigStrategyDetails
    newPeronalConter: SamsClubGrayConfigStrategyDetails
    newPicview: SamsClubGrayConfigStrategyDetails
    newTagManageExp: SamsClubGrayConfigStrategyDetails
    noSearchRecommend: SamsClubGrayConfigStrategyDetails
    paySdkGray: SamsClubGrayConfigStrategyDetails
    personalSwift: SamsClubGrayConfigStrategyDetails
    preloadFind: SamsClubGrayConfigStrategyDetails
    presellOrderDelivery: SamsClubGrayConfigStrategyDetails
    promotionTaskBox: SamsClubGrayConfigStrategyDetails
    rankingPageTag: SamsClubGrayConfigStrategyDetails
    remakeSearchRankListUI: SamsClubGrayConfigStrategyDetails
    renewPageToH5Gray: SamsClubGrayConfigStrategyDetails
    reportHandler: SamsClubGrayConfigStrategyDetails
    reviewSearchText: SamsClubGrayConfigStrategyDetails
    rightsCommentExp: SamsClubGrayConfigStrategyDetails
    scGray: SamsClubGrayConfigStrategyDetails
    scPlayer: SamsClubGrayConfigStrategyDetails
    scplayerHome: SamsClubGrayConfigStrategyDetails
    searchResultExp: SamsClubGrayConfigStrategyDetails
    searchResultStyle: SamsClubGrayConfigStrategyDetails
    searchSeries: SamsClubGrayConfigStrategyDetails
    searchTextRecommendExp: SamsClubGrayConfigStrategyDetails
    seriesGoodsOpt: SamsClubGrayConfigStrategyDetails
    settleByAtWill: SamsClubGrayConfigStrategyDetails
    settleChangeAddress: SamsClubGrayConfigStrategyDetails
    showGoodsTag: SamsClubGrayConfigStrategyDetails
    smallSizePacket: SamsClubGrayConfigStrategyDetails
    swiftGray: SamsClubGrayConfigStrategyDetails
    topRemake: SamsClubGrayConfigStrategyDetails
    transferToPersonalMainCard: SamsClubGrayConfigStrategyDetails
    upgradeExcellenceCardPopup: SamsClubGrayConfigStrategyDetails
    videoPlayerOpt: SamsClubGrayConfigStrategyDetails
    weblinkcheck: SamsClubGrayConfigStrategyDetails
    webviewcheck: SamsClubGrayConfigStrategyDetails
    widget3DTouchExp: SamsClubGrayConfigStrategyDetails
    xiliepinSku: SamsClubGrayConfigStrategyDetails
    xiliepinSkuOpt: SamsClubGrayConfigStrategyDetails


class SamsClubAppStorage(CustomBaseModel):
    uid: str = ""
    mobile: str = ""
    storeInfoVOList: list[dict] = Field(default_factory=list)
    storeList: list[str] = Field(default_factory=list)
    version_str: str = "5.0.125"


class SamsClubHeadersModel(CustomBaseModel):
    model_config = ConfigDict(extra='ignore', serialize_by_alias=True, )
    language: str = "CN"
    system_language: str = Field("CN", alias="system-language")
    device_type: str = Field("android", alias="device-type")
    tpg: str = Field("1")
    app_version: str = Field("5.0.120", alias="app-version")
    device_id: str = Field("d3e9907ab1881aac891aff90100016e1950c", alias="device-id")
    device_os_version: str = Field("11", alias="device-os-version")
    device_name: str = Field("OnePlus_ONEPLUS+A6000", alias="device-name")
    treq_id: str = Field(..., alias="treq-id")
    auth_token: str = Field(...,
                            alias="auth-token")
    longitude: str | float = Field(...)
    latitude: str | float = Field(...)
    p: str = Field("1656120205")
    t: str = Field(...)
    n: str = Field(...)
    sy: str = Field("0")
    st: str = Field(...)
    sny: str = "c"
    rcs: str = "1"
    spv: str = "2.0"
    Local_Longitude: str | float = Field(..., alias="Local-Longitude")
    Local_Latitude: str | float = Field(..., alias="Local-Latitude")
    zoneType: str = "1"
    content_type: str = Field("application/json;charset=utf-8", alias="Content-Type")
    Host: str = "api-sams.walmartmobile.cn"
    Connection: str = 'Keep-Alive'
    accept_encoding: str = Field("gzip", alias='Accept-Encoding')
    user_agent: str = Field("okhttp/4.12.0", alias="User-Agent")


class SamsClubEncryptModel(CustomBaseModel):
    device_id_str: str
    version_str: str
    device_name: str
    do_encrypt_result_str: str


class SamsClubGetDoEncryptReqModel(CustomBaseModel):
    timestampStr: str
    bodyStr: str
    uuidStr: str
    tokenStr: str


class SamsClubQuerySpuInfoParamsModel(CustomBaseModel):
    spu_new_tag_tag_mark: str | None
    spu_info_title: str | None
    spu_info_update_asc: bool | None
    spu_price_asc: bool | None
    spu_price_min: bool | None
    spu_price_max: bool | None


__all__ = [
    'SamsClubQuerySpuInfoParamsModel',
    'SamsClubGetDoEncryptReqModel',
    'SamsClubEncryptModel',
    'SamsClubHeadersModel',
    'SamsClubGrayConfigStrategy',
    'SamsClubGrayConfigStrategyDetails'
]
if __name__ == '__main__':
    def _test_SamsClubGrayConfigStrategy():
        a = SamsClubGrayConfigStrategy.model_validate_json('{"CN2TCGray":{"allEnable":true,"bizCode":"CN2TCGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"中文繁简切换","versionKey":""},"addCartExp":{"allEnable":true,"bizCode":"addCartExp","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"加车体验优化","versionKey":""},"addrAccurateSearch":{"allEnable":true,"bizCode":"addrAccurateSearch","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"高德地址精准搜索","versionKey":""},"addressCode":{"allEnable":true,"bizCode":"addressCode","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"请求header带上省市区code","versionKey":""},"apartOrder":{"allEnable":true,"bizCode":"apartOrder","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"合并支付并拆单","versionKey":""},"appDecorationReconstruction":{"allEnable":true,"bizCode":"appDecorationReconstruction","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"APP首页重构","versionKey":""},"appLoadingOpt":{"allEnable":true,"bizCode":"appLoadingOpt","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"加载效率优化","versionKey":""},"appSearchGray":{"allEnable":true,"bizCode":"appSearchGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"APP搜索埋点","versionKey":""},"applicableGoods":{"allEnable":true,"bizCode":"applicableGoods","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"凑单页","versionKey":""},"associatedWordExp":{"allEnable":false,"bizCode":"associatedWordExp","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"搜索联想词算法实验_0424","versionKey":""},"associatedWordExp1":{"allEnable":false,"bizCode":"associatedWordExp1","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"998\\",\\"expKey\\":\\"exp_lianxiang_test3_0626_A\\",\\"groupKey\\":\\"exp_lianxiang_test3_0626\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_lianxiang_test3_0626\\",\\"params\\":{\\"name\\":\\"原始对照组（75%）\\",\\"strategy\\":\\"original\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_associatedWordExp1_exp_lianxiang_test3_0626\\",\\"userType\\":2}","strategyDesc":"搜索联想词算法实验-三期","versionKey":"A"},"bankcommMemberCard":{"allEnable":true,"bizCode":"bankcommMemberCard","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"交行联名卡","versionKey":""},"bannerComment":{"allEnable":false,"bizCode":"bannerComment","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"588\\",\\"expKey\\":\\"exp_detail_picture_evaluate_1_A\\",\\"groupKey\\":\\"exp_detail_picture_evaluate_1\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_detail_picture_evaluate_1\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_bannerComment_exp_detail_picture_evaluate_1\\",\\"userType\\":2}","strategyDesc":"商品详情主图评价模块实验","versionKey":"A"},"becomeMemberExp":{"allEnable":false,"bizCode":"becomeMemberExp","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"667\\",\\"expKey\\":\\"exp_NewMembership_1029_A\\",\\"groupKey\\":\\"exp_NewMembership_1029\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_NewMembership_1029\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_becomeMemberExp_exp_NewMembership_1029\\",\\"userType\\":2}","strategyDesc":"成为会员页实验","versionKey":"A"},"buyOneAbt":{"allEnable":true,"bizCode":"buyOneAbt","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"全城配随手买实验","versionKey":"B"},"cartRestructure":{"allEnable":true,"bizCode":"cartRestructure","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"购物车重构","versionKey":""},"cartRestructureV2":{"allEnable":true,"bizCode":"cartRestructureV2","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"购物车重构二期","versionKey":""},"categoryAddCartRecom":{"allEnable":false,"bizCode":"categoryAddCartRecom","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"1030\\",\\"expKey\\":\\"exp_category_rectest_250626_A\\",\\"groupKey\\":\\"exp_category_rectest_250626\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_category_rectest_250626\\",\\"params\\":{\\"name\\":\\"无加购后推荐\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_categoryAddCartRecom_exp_category_rectest_250626\\",\\"userType\\":2}","strategyDesc":"分类页增加加购后推荐位实验","versionKey":"A"},"categoryOpt":{"allEnable":false,"bizCode":"categoryOpt","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"927\\",\\"expKey\\":\\"exp_fenleiye_PKxiliepin_online_A\\",\\"groupKey\\":\\"exp_fenleiye_PKxiliepin_online\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_fenleiye_PKxiliepin_online\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_categoryOpt_exp_fenleiye_PKxiliepin_online\\",\\"userType\\":2}","strategyDesc":"分类页优化","versionKey":"A"},"categoryRecommend":{"allEnable":false,"bizCode":"categoryRecommend","group":"true","isOpen":true,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"1090\\",\\"expKey\\":\\"rec_category_250723_exp10\\",\\"groupKey\\":\\"rec_category_250723\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"rec_category_250723\\",\\"params\\":{\\"component\\":\\"recommend\\",\\"name\\":\\"商品大卡\\",\\"bigpic\\":\\"true\\",\\"backend\\":\\"samall\\",\\"strategy\\":\\"max_slot;cate_diversity_slot;f100;new;CBEC_diversity_slot;CBEC_add_slot\\",\\"isGray\\":\\"true\\",\\"group\\":\\"true\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_categoryRecommend_rec_category_250723\\",\\"userType\\":2}","strategyDesc":"分类页为你推荐","versionKey":"exp10"},"commentSearchText":{"allEnable":false,"bizCode":"commentSearchText","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"评价搜索页文案","versionKey":""},"commentVideoCompression":{"allEnable":false,"bizCode":"commentVideoCompression","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"视频压缩","versionKey":""},"customerServiceSdk":{"allEnable":true,"bizCode":"customerServiceSdk","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"客服SDK","versionKey":""},"decoration":{"allEnable":false,"bizCode":"decoration","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"装修重构","versionKey":""},"discover":{"allEnable":true,"bizCode":"discover","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"发现页","versionKey":""},"expNewUserGiftMiniProKey":{"allEnable":false,"bizCode":"expNewUserGiftMiniProKey","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"新人礼包-MiniProgram","versionKey":""},"expireMemberCardSupportDowngraded":{"allEnable":false,"bizCode":"expireMemberCardSupportDowngraded","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"400\\",\\"expKey\\":\\"exp_JJxufei_A\\",\\"groupKey\\":\\"exp_JJxufei\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_JJxufei\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_expireMemberCardSupportDowngraded_exp_JJxufei\\",\\"userType\\":2}","strategyDesc":"卓越个人主卡过期支持降级消费","versionKey":"A"},"goodsDetailBlankPageOpt":{"allEnable":true,"bizCode":"goodsDetailBlankPageOpt","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"商详页切换系列品后空白页优化","versionKey":""},"goodsDetailNewTest":{"allEnable":false,"bizCode":"goodsDetailNewTest","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"884\\",\\"expKey\\":\\"exp_detail_new_B\\",\\"groupKey\\":\\"exp_detail_new\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_detail_new\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_goodsDetailNewTest_exp_detail_new\\",\\"userType\\":2}","strategyDesc":"商品详情页大改版","versionKey":"B"},"goodsDetailOpt":{"allEnable":true,"bizCode":"goodsDetailOpt","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"商详页优化","versionKey":""},"goodsDetailPageRecommendOpt":{"allEnable":false,"bizCode":"goodsDetailPageRecommendOpt","group":"C","isOpen":true,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"913\\",\\"expKey\\":\\"rec_description_250508_exp01\\",\\"groupKey\\":\\"rec_description_250508\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"rec_description_250508\\",\\"params\\":{\\"component\\":\\"C;no_inventory;after_cart_rec\\",\\"name\\":\\"经常一起买优先\\",\\"backend\\":\\"sam\\",\\"strategy\\":\\"user_DND_5\\",\\"isGray\\":\\"true\\",\\"group\\":\\"C\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_goodsDetailPageRecommendOpt_rec_description_250508\\",\\"userType\\":2}","strategyDesc":"商详页推荐优化-APP","versionKey":"exp01"},"goodsDetailParamPk":{"allEnable":false,"bizCode":"goodsDetailParamPk","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"702\\",\\"expKey\\":\\"exp_goods_PK_B\\",\\"groupKey\\":\\"exp_goods_PK\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_goods_PK\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_goodsDetailParamPk_exp_goods_PK\\",\\"userType\\":2}","strategyDesc":"商品详情参数PK实验","versionKey":"B"},"goodsDetailStockReveal":{"allEnable":false,"bizCode":"goodsDetailStockReveal","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"商品详情页门店库存模块实验","versionKey":""},"goodsThumbnail":{"allEnable":true,"bizCode":"goodsThumbnail","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"终端瀑布流展示系列品小图","versionKey":"B"},"hippyKitchen":{"allEnable":false,"bizCode":"hippyKitchen","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"发现厨房hippy改造","versionKey":""},"hippyResource":{"allEnable":false,"bizCode":"hippyResource","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"hippy资源下载管理","versionKey":""},"hippyResource1":{"allEnable":true,"bizCode":"hippyResource1","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"hippy资源下载管理1","versionKey":""},"hippyShowOrder":{"allEnable":false,"bizCode":"hippyShowOrder","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"hippy晒单","versionKey":""},"hippySpt":{"allEnable":false,"bizCode":"hippySpt","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"大厨教做菜双列&短图文","versionKey":""},"hippyVideoFeed":{"allEnable":false,"bizCode":"hippyVideoFeed","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"hippy视频流改造","versionKey":""},"homeAddAddressFloat":{"allEnable":false,"bizCode":"homeAddAddressFloat","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"首页新增地址浮窗","versionKey":""},"homeThreeGoodsModule":{"allEnable":true,"bizCode":"homeThreeGoodsModule","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"IOS首页卡顿优化灰度策略","versionKey":""},"inviteGifts":{"allEnable":false,"bizCode":"inviteGifts","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"邀请有礼","versionKey":""},"justStoreSaleSplit":{"allEnable":false,"bizCode":"justStoreSaleSplit","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"仅门店可售实验","versionKey":""},"memberCreateCardPageOpt":{"allEnable":true,"bizCode":"memberCreateCardPageOpt","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"会籍开卡页优化-APP","versionKey":"B"},"memberCreateCardPageOptMiniProgram":{"allEnable":true,"bizCode":"memberCreateCardPageOptMiniProgram","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"会籍开卡页优化-小程序","versionKey":"B"},"memberGuide":{"allEnable":false,"bizCode":"memberGuide","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"590\\",\\"expKey\\":\\"exp_Member_handbook_A\\",\\"groupKey\\":\\"exp_Member_handbook\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_Member_handbook\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_memberGuide_exp_Member_handbook\\",\\"userType\\":2}","strategyDesc":"会员指南","versionKey":"A"},"memberUnionPay":{"allEnable":true,"bizCode":"memberUnionPay","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"会籍合并支付","versionKey":""},"messageCenterGray":{"allEnable":true,"bizCode":"messageCenterGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"消息中心","versionKey":""},"midSearchPage":{"allEnable":false,"bizCode":"midSearchPage","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"261\\",\\"expKey\\":\\"exp_searchpaga_test_A\\",\\"groupKey\\":\\"exp_searchpaga_test\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_searchpaga_test\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_midSearchPage_exp_searchpaga_test\\",\\"userType\\":2}","strategyDesc":"搜索中间页样式","versionKey":"A"},"mineHeadGray":{"allEnable":true,"bizCode":"mineHeadGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"个人页重构-安卓","versionKey":""},"miniGoodsDetailBuyCardExp":{"allEnable":true,"bizCode":"miniGoodsDetailBuyCardExp","group":"C","isOpen":true,"paramsJson":null,"strategyDesc":"商品详情页购买会籍-小程序","versionKey":"C"},"miniHomePage":{"allEnable":true,"bizCode":"miniHomePage","group":"A","isOpen":true,"paramsJson":null,"strategyDesc":"小程序非会员首页","versionKey":"A"},"newMemberRenewPage":{"allEnable":true,"bizCode":"newMemberRenewPage","group":"A","isOpen":true,"paramsJson":null,"strategyDesc":"续费页重构","versionKey":"A"},"newPeronalConter":{"allEnable":false,"bizCode":"newPeronalConter","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"750\\",\\"expKey\\":\\"exp_mypage_new_A\\",\\"groupKey\\":\\"exp_mypage_new\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_mypage_new\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_newPeronalConter_exp_mypage_new\\",\\"userType\\":2}","strategyDesc":"新版个人中心","versionKey":"A"},"newPicview":{"allEnable":true,"bizCode":"newPicview","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"ios图片浏览器体验优化","versionKey":""},"newTagManageExp":{"allEnable":false,"bizCode":"newTagManageExp","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"670\\",\\"expKey\\":\\"exp_new_tag_manage_20241031_B\\",\\"groupKey\\":\\"exp_new_tag_manage_20241031\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_new_tag_manage_20241031\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_newTagManageExp_exp_new_tag_manage_20241031\\",\\"userType\\":2}","strategyDesc":"新标签管理后台灰度实验","versionKey":"B"},"noSearchRecommend":{"allEnable":true,"bizCode":"noSearchRecommend","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"搜索无结果为你推荐","versionKey":""},"paySdkGray":{"allEnable":true,"bizCode":"paySdkGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"支付sdk","versionKey":""},"personalSwift":{"allEnable":false,"bizCode":"personalSwift","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"个人中心子页面改造","versionKey":""},"preloadFind":{"allEnable":false,"bizCode":"preloadFind","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"临时价格，发现页预加载IOS技术优化","versionKey":""},"presellOrderDelivery":{"allEnable":true,"bizCode":"presellOrderDelivery","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"预售订单履约","versionKey":""},"promotionTaskBox":{"allEnable":true,"bizCode":"promotionTaskBox","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"营销任务盒子","versionKey":""},"rankingPageTag":{"allEnable":false,"bizCode":"rankingPageTag","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"榜单页及榜单组件排名标签","versionKey":""},"remakeSearchRankListUI":{"allEnable":true,"bizCode":"remakeSearchRankListUI","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"榜单页UI重构-android","versionKey":""},"renewPageToH5Gray":{"allEnable":true,"bizCode":"renewPageToH5Gray","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"续费页改造为H5","versionKey":"B"},"reportHandler":{"allEnable":false,"bizCode":"reportHandler","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"IOS埋点上报灰度策略","versionKey":""},"reviewSearchText":{"allEnable":true,"bizCode":"reviewSearchText","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"评价搜索功能","versionKey":"B"},"rightsCommentExp":{"allEnable":true,"bizCode":"rightsCommentExp","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"售后评价一期灰度","versionKey":""},"scGray":{"allEnable":true,"bizCode":"scGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"sc","versionKey":""},"scPlayer":{"allEnable":true,"bizCode":"scPlayer","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"视频播放器重构-IOS","versionKey":""},"scplayerHome":{"allEnable":true,"bizCode":"scplayerHome","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"视频播放器重构2.0","versionKey":""},"searchResultExp":{"allEnable":false,"bizCode":"searchResultExp","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"1110\\",\\"expKey\\":\\"exp_searchitem_test_0806_G\\",\\"groupKey\\":\\"exp_searchitem_test_0806\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_searchitem_test_0806\\",\\"params\\":{\\"component\\":\\"semantics\\",\\"name\\":\\"三分类语义模型\\",\\"strategy\\":\\"new\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_searchResultExp_exp_searchitem_test_0806\\",\\"userType\\":2}","strategyDesc":"搜索算法实验","versionKey":"G"},"searchResultStyle":{"allEnable":false,"bizCode":"searchResultStyle","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"搜索结果样式","versionKey":""},"searchSeries":{"allEnable":true,"bizCode":"searchSeries","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"搜索系列品灰度","versionKey":""},"searchTextRecommendExp":{"allEnable":false,"bizCode":"searchTextRecommendExp","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"1060\\",\\"expKey\\":\\"exp_searchshaded_test_0804_A\\",\\"groupKey\\":\\"exp_searchshaded_test_0804\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_searchshaded_test_0804\\",\\"params\\":{\\"name\\":\\"原始对照组（90%）\\",\\"strategy\\":\\"present\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_searchTextRecommendExp_exp_searchshaded_test_0804\\",\\"userType\\":2}","strategyDesc":"搜索底纹词轮播实验","versionKey":"A"},"seriesGoodsOpt":{"allEnable":false,"bizCode":"seriesGoodsOpt","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"系列品加车等优化","versionKey":""},"settleByAtWill":{"allEnable":true,"bizCode":"settleByAtWill","group":"A","isOpen":true,"paramsJson":null,"strategyDesc":"结算页随手买一件","versionKey":"A"},"settleChangeAddress":{"allEnable":true,"bizCode":"settleChangeAddress","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"结算页切换地址","versionKey":""},"showGoodsTag":{"allEnable":true,"bizCode":"showGoodsTag","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"展示商品标签","versionKey":"B"},"smallSizePacket":{"allEnable":true,"bizCode":"smallSizePacket","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"商品小包装价格","versionKey":"B"},"swiftGray":{"allEnable":true,"bizCode":"swiftGray","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"接入swift-ios","versionKey":""},"topRemake":{"allEnable":false,"bizCode":"topRemake","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"榜单页重构","versionKey":""},"transferToPersonalMainCard":{"allEnable":true,"bizCode":"transferToPersonalMainCard","group":"A","isOpen":true,"paramsJson":null,"strategyDesc":"亲友卡/公司卡转个人主卡","versionKey":"A"},"upgradeExcellenceCardPopup":{"allEnable":false,"bizCode":"upgradeExcellenceCardPopup","group":"","isOpen":true,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"80\\",\\"expKey\\":\\"exp_premium_0829_A\\",\\"groupKey\\":\\"exp_premium_0829\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_premium_0829\\",\\"params\\":{\\"isGray\\":\\"true\\",\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_upgradeExcellenceCardPopup_exp_premium_0829\\",\\"userType\\":2}","strategyDesc":"升级卓越卡弹窗","versionKey":"A"},"videoPlayerOpt":{"allEnable":false,"bizCode":"videoPlayerOpt","group":"","isOpen":false,"paramsJson":null,"strategyDesc":"视频播放优化","versionKey":""},"weblinkcheck":{"allEnable":true,"bizCode":"weblinkcheck","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"url编码优化","versionKey":""},"webviewcheck":{"allEnable":true,"bizCode":"webviewcheck","group":"","isOpen":true,"paramsJson":null,"strategyDesc":"webview增加cookie安全校验","versionKey":""},"widget3DTouchExp":{"allEnable":false,"bizCode":"widget3DTouchExp","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"794\\",\\"expKey\\":\\"exp_3dtouch_C\\",\\"groupKey\\":\\"exp_3dtouch\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_3dtouch\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_widget3DTouchExp_exp_3dtouch\\",\\"userType\\":2}","strategyDesc":"widget3DTouch实验","versionKey":"C"},"xiliepinSku":{"allEnable":true,"bizCode":"xiliepinSku","group":"B","isOpen":true,"paramsJson":null,"strategyDesc":"系列品小图弹出控制","versionKey":"B"},"xiliepinSkuOpt":{"allEnable":false,"bizCode":"xiliepinSkuOpt","group":"","isOpen":false,"paramsJson":"{\\"businessCode\\":\\"9191\\",\\"expId\\":\\"806\\",\\"expKey\\":\\"exp_xiliepin_sku_online_A\\",\\"groupKey\\":\\"exp_xiliepin_sku_online\\",\\"guid\\":\\"1818144697779\\",\\"kaName\\":\\"SAMS\\",\\"layerKey\\":\\"exp_xiliepin_sku_online\\",\\"params\\":{\\"extendInfo\\":\\"{\\\\\\"deviceInfo\\\\\\":{\\\\\\"appVersion\\\\\\":\\\\\\"5.0.126\\\\\\",\\\\\\"deviceId\\\\\\":\\\\\\"d3e9907ab1881aac891aff90100016e1950c\\\\\\",\\\\\\"deviceType\\\\\\":\\\\\\"android\\\\\\",\\\\\\"systemLanguage\\\\\\":\\\\\\"CN\\\\\\",\\\\\\"userAgent\\\\\\":\\\\\\"okhttp/4.12.0\\\\\\"}}\\"},\\"qimei\\":\\"\\",\\"reportPath\\":\\"SAMS_online_xiliepinSkuOpt_exp_xiliepin_sku_online\\",\\"userType\\":2}","strategyDesc":"系列品优化V2","versionKey":"A"}}',strict=False)
        print(a)

    _test_SamsClubGrayConfigStrategy()
