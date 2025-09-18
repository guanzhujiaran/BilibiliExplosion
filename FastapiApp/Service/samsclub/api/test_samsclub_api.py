import pytest
from unittest.mock import AsyncMock, patch
from FastapiApp.Service.samsclub.api.samsclub_api import SamsClubAPI

@pytest.mark.asyncio
async def test_grouping_query_navigation():
    """
    测试 grouping_query_navigation 方法的功能和边界情况。
    包括正常请求、异常处理和返回数据验证。
    """
    # 模拟 SamsClubAPI 实例
    api = SamsClubAPI("https://example.com", "token")
    api.app_storage = AsyncMock()
    api.app_storage.storeInfoVOList = ["store1", "store2"]
    api.send = AsyncMock(return_value={
        "data": {
            "dataList": [
                {"groupingId": "35145", "title": "肉蛋果蔬", "isFastDelivery": False, "level": 1, "navigationId": "1", "image": "https://example.com/image1.jpg", "storeId": "-1", "children": []}
            ],
            "cardFilterList": [],
            "searchFilterList": [],
            "searchAfter": [],
            "reportInfo": "",
            "hasNextPage": False,
            "onlyShowSimilarButton": False
        },
        "code": "Success",
        "msg": "",
        "errorMsg": "",
        "traceId": "16d3a7318c737acf",
        "requestId": "106560fa03e344ce9f9056c609accd72.101.17481870958365739",
        "rt": 0,
        "success": True
    })

    # 调用方法
    result = await api.grouping_query_navigation()

    # 验证返回数据
    assert result["data"]["dataList"][0]["title"] == "肉蛋果蔬"
    assert result["code"] == "Success"
    assert api.send.call_count == 1

@pytest.mark.asyncio
async def test_grouping_query_navigation_empty_store_list():
    """
    测试 grouping_query_navigation 方法在 storeInfoVOList 为空时的行为。
    """
    api = SamsClubAPI("https://example.com", "token")
    api.app_storage = AsyncMock()
    api.app_storage.storeInfoVOList = []
    api.send = AsyncMock(return_value={
        "data": {"dataList": []},
        "code": "Success",
        "success": True
    })

    result = await api.grouping_query_navigation()
    assert len(result["data"]["dataList"]) == 0

@pytest.mark.asyncio
async def test_grouping_query_navigation_error_response():
    """
    测试 grouping_query_navigation 方法在 API 返回错误时的行为。
    """
    api = SamsClubAPI("https://example.com", "token")
    api.app_storage = AsyncMock()
    api.app_storage.storeInfoVOList = ["store1"]
    api.send = AsyncMock(return_value={
        "code": "Error",
        "errorMsg": "Internal Server Error",
        "success": False
    })

    result = await api.grouping_query_navigation()
    assert result["success"] is False
    assert "Internal Server Error" in result["errorMsg"]