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


async def _test_get_sign():
    """
    主要问题是中文的解码
    :return:
    """
    expected_sign = "ac668089b221cd5b53ad63e0c88b19c9"
    ts_str = "1747845916506"
    bd ={"source":"ANDROID","channel":1,"spuId":318750486,"uid":"1818144697779","addressVO":{"cityName":"上海市","countryName":"","detailAddress":"","districtName":"静安区","provinceName":"上海市"},"isTagEntryAbtTest":True,"storeInfoVOList":[{"storeType":16,"storeId":6558,"storeDeliveryAttr":[3,4,6,14,5,12,2],"storeDeliveryTemplateId":1355122139681978902},{"storeType":256,"storeId":6758,"storeDeliveryAttr":[9,13],"storeDeliveryTemplateId":1893545853000529686},{"storeType":2,"storeId":4807,"storeDeliveryAttr":[7],"storeDeliveryTemplateId":1788615079357457942},{"storeType":4,"storeId":5237,"storeDeliveryAttr":[3,4],"storeDeliveryTemplateId":1577484737948323606},{"storeType":8,"storeId":9996,"storeDeliveryAttr":[1],"storeDeliveryTemplateId":1147161263885953814}]}
    body_str = json.dumps(bd, ensure_ascii=False, separators=(',', ':'))
    expected_body_hex = '7b22736f75726365223a22414e44524f4944222c226368616e6e656c223a312c227370754964223a3331383735303438362c22756964223a2231383138313434363937373739222c2261646472657373564f223a7b22636974794e616d65223a22e4b88ae6b5b7e5b882222c22636f756e7472794e616d65223a22222c2264657461696c41646472657373223a22222c2264697374726963744e616d65223a22e99d99e5ae89e58cba222c2270726f76696e63654e616d65223a22e4b88ae6b5b7e5b882227d2c226973546167456e74727941627454657374223a747275652c2273746f7265496e666f564f4c697374223a5b7b2273746f726554797065223a31362c2273746f72654964223a363535382c2273746f726544656c697665727941747472223a5b332c342c362c31342c352c31322c325d2c2273746f726544656c697665727954656d706c6174654964223a313335353132323133393638313937383930327d2c7b2273746f726554797065223a3235362c2273746f72654964223a363735382c2273746f726544656c697665727941747472223a5b392c31335d2c2273746f726544656c697665727954656d706c6174654964223a313839333534353835333030303532393638367d2c7b2273746f726554797065223a322c2273746f72654964223a343830372c2273746f726544656c697665727941747472223a5b375d2c2273746f726544656c697665727954656d706c6174654964223a313738383631353037393335373435373934327d2c7b2273746f726554797065223a342c2273746f72654964223a353233372c2273746f726544656c697665727941747472223a5b332c345d2c2273746f726544656c697665727954656d706c6174654964223a313537373438343733373934383332333630367d2c7b2273746f726554797065223a382c2273746f72654964223a393939362c2273746f726544656c697665727941747472223a5b315d2c2273746f726544656c697665727954656d706c6174654964223a313134373136313236333838353935333831347d5d7d'
    body_hex = body_str.encode("utf-8").hex()
    print(body_hex == expected_body_hex)
    print(f"mock body_hex:{body_hex}")
    print(f"real body_hex:{expected_body_hex}")
    fake_n = "b1459645854744cb820f554111ff2feb"
    auth_token = "740d926b981716f4212cb48a4fb7591f9f984d92ee660d5179580a5d95729f81129e1b87cc8bd60f8f9d1a3f88fb7dfa2691e4d19f66631d"
    sign = await get_do_encrypt_result_str(
        SamsClubGetDoEncryptReqModel(
            timestampStr=ts_str,
            bodyStr=body_str,
            uuidStr=fake_n,
            tokenStr=auth_token
        ))
    print(sign == expected_sign)
    print(f"模拟的sign：{sign}")
    print(f"真机得到的sign：{expected_sign}")


if __name__ == "__main__":
    asyncio.run(_test_get_sign())
