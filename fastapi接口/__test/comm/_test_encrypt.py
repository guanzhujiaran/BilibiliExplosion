import asyncio
import json
from fastapi接口.models.v1.samsclub.samsclub_model import SamsClubEncryptModel, SamsClubGetDoEncryptReqModel
from fastapi接口.service.samsclub.tools.do_samsclub_encryptor import get_st, get_do_encrypt_result_str


async def _test():
    """
    目前不带body的st是正确的，应该就是body的入参格式了，多试几次
    :return:
    """
    device_id = "d3e9907ab1881aac891aff90100016e1950c"
    version_str = "5.0.120"
    device_name = "OnePlus_ONEPLUS+A6000"
    ts_str = "1747844641913"
    body = {"source": "ANDROID",
            "channel": 1,
            "spuId": 319481518,
            "uid": "1818144697779",
            "addressVO": {
                "cityName": "上海市",
                "countryName": "",
                "detailAddress": "",
                "districtName": "静安区",
                "provinceName": "上海市"
            },
            "isTagEntryAbtTest": True,
            "storeInfoVOList":
                [{"storeType": 16, "storeId": 6558, "storeDeliveryAttr": [3, 4, 6, 14, 5, 12, 2],
                  "storeDeliveryTemplateId": 1355122139681978902},
                 {"storeType": 256, "storeId": 6758, "storeDeliveryAttr": [9, 13],
                  "storeDeliveryTemplateId": 1893545853000529686},
                 {"storeType": 2, "storeId": 4807, "storeDeliveryAttr": [7],
                  "storeDeliveryTemplateId": 1788615079357457942},
                 {"storeType": 4, "storeId": 5237, "storeDeliveryAttr": [3, 4],
                  "storeDeliveryTemplateId": 1577484737948323606},
                 {"storeType": 8, "storeId": 9996, "storeDeliveryAttr": [1],
                  "storeDeliveryTemplateId": 1147161263885953814}]}

    body_str = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
    print(body_str)
    fake_n = "2b02ce2d88ff408abf3cc01fd1a8682d"
    auth_token = "740d926b981716f4212cb48a4fb7591f9f984d92ee660d5179580a5d95729f81129e1b87cc8bd60f8f9d1a3f88fb7dfa2691e4d19f66631d"
    do_encrypt_result_str = await get_do_encrypt_result_str(
        SamsClubGetDoEncryptReqModel(
            timestampStr=ts_str,
            bodyStr=body_str,
            uuidStr=fake_n,
            tokenStr=auth_token
        ))
    st = get_st(
        SamsClubEncryptModel(
            device_id_str=device_id,
            version_str=version_str,
            device_name=device_name,
            do_encrypt_result_str=do_encrypt_result_str
        ),
    )

    expected_st = "0ef6a9015c9defd39c323b6cd097f195"

    print(st == expected_st)
    print(f"模拟的st：{st}")
    print(f"真机得到的st：{expected_st}")


async def _test_get_st():
    """
    主要问题是中文的解码
    :return:
    """
    expected_st = "e78820a012a719b1172bf8dd700616ff"
    ts_str = "1749107959247"
    bd = {"source": "ANDROID", "channel": 1, "spuId": 323074516, "uid": "1818144697779",
          "addressVO": {"cityName": "上海市",
                        "countryName": "",
                        "detailAddress": "",
                        "districtName": "静安区",
                        "provinceName": "上海市"}, "isTagEntryAbtTest": True, "storeInfoVOList": [
            {"storeType": 16, "storeId": 6558, "storeDeliveryAttr": [3, 4, 6, 14, 5, 12, 2],
             "storeDeliveryTemplateId": 1355122139681978902},
            {"storeType": 256, "storeId": 6758, "storeDeliveryAttr": [9, 13],
             "storeDeliveryTemplateId": 1893545853000529686},
            {"storeType": 2, "storeId": 4807, "storeDeliveryAttr": [7], "storeDeliveryTemplateId": 1788615079357457942},
            {"storeType": 4, "storeId": 5237, "storeDeliveryAttr": [3, 4],
             "storeDeliveryTemplateId": 1577484737948323606},
            {"storeType": 8, "storeId": 9996, "storeDeliveryAttr": [1],
             "storeDeliveryTemplateId": 1147161263885953814}]}
    body_str = json.dumps(bd, ensure_ascii=False, separators=(',', ':'))
    fake_n = "085cd8d4a77c49e4952b492b0bde663d"
    auth_token = "740d926b981716f4212cb48a4fb7591f9fb5b4bc5d4f995d51727e4bbc0a0a781dd523b87df46a648f9d1a3f88fb7dfa0b86d752dab027b6"
    sign = await get_do_encrypt_result_str(
        SamsClubGetDoEncryptReqModel(
            timestampStr=ts_str,
            bodyStr=body_str,
            uuidStr=fake_n,
            tokenStr=auth_token
        ))
    st = get_st(
        SamsClubEncryptModel(
            device_id_str="d3e9907ab1881aac891aff90100016e1950c",
            version_str="5.0.122",
            device_name="OnePlus_ONEPLUS+A6000",
            do_encrypt_result_str=sign
        ),
    )
    assert expected_st == st, f"st不匹配，预期：{expected_st}，实际：{st}"
    print(f"模拟的st：\n{st}")
    print(f"真机得到的st:\n{expected_st}")


if __name__ == "__main__":
    asyncio.run(_test_get_st())
