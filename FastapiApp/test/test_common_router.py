# -*- coding: utf-8 -*-
"""
CommonRouter 接口测试

测试端点:
    GET  /test                           — 服务可用性检查
    GET  /gc                             — 垃圾回收
    GET  /v1/get/live_lots              — 获取直播抽奖
    POST /v1/post/RmFollowingList        — 取关列表
    POST /lot/upsert_lot_detail          — 插入/更新抽奖详情
    GET  /get_others_lot_dyn             — 获取他人动态抽奖
    GET  /get_others_official_lot_dyn    — 获取他人官方动态抽奖
    GET  /get_others_big_lot             — 获取他人大奖
    GET  /get_others_big_reserve         — 获取重要预约抽奖
    GET  /zhihu/get_others_lot_pins      — 获取知乎抽奖
    GET  /toutiao/get_others_lot_ids     — 获取头条抽奖
"""

import pytest
from unittest import mock
from httpx import ASGITransport, AsyncClient


# ============================================================================
# Helper
# ============================================================================


@pytest.fixture
async def client(app):
    """异步 HTTP 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# GET /test — 服务可用性检查
# ============================================================================


@pytest.mark.asyncio
async def test_health_check_returns_ok(client):
    """测试服务可用性检查返回 200"""
    response = await client.get("/test")
    assert response.status_code == 200
    assert response.json() == "Service is running!"


# ============================================================================
# GET /gc — 垃圾回收
# ============================================================================


@pytest.mark.asyncio
async def test_gc_returns_ok(client):
    """测试垃圾回收接口返回 200"""
    response = await client.get("/gc")
    assert response.status_code == 200
    assert response.json() == "gc完成！"


# ============================================================================
# GET /v1/get/live_lots — 获取直播抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_live_lots_default(client):
    """测试默认参数获取直播抽奖"""
    response = await client.get("/v1/get/live_lots")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_live_lots_with_param(client):
    """测试带参数获取直播抽奖"""
    response = await client.get("/v1/get/live_lots?get_all=true")
    assert response.status_code == 200


# ============================================================================
# POST /v1/post/RmFollowingList — 取关列表
# ============================================================================


@pytest.mark.asyncio
async def test_rm_following_list_with_empty_body(client):
    """测试空请求体"""
    with mock.patch("controller.common.CommonRouter.gmflv2") as mock_gmflv2:
        mock_gmflv2.get_rm_following_list = mock.AsyncMock(return_value=[])
        response = await client.post("/v1/post/RmFollowingList", json=[])
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rm_following_list_with_uids(client):
    """测试传入 UID 列表"""
    with mock.patch("controller.common.CommonRouter.gmflv2") as mock_gmflv2:
        mock_gmflv2.get_rm_following_list = mock.AsyncMock(return_value=[1, 2, 3])
        response = await client.post("/v1/post/RmFollowingList", json=[123, 456])
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rm_following_list_with_string_uids(client):
    """测试传入字符串类型 UID 列表"""
    with mock.patch("controller.common.CommonRouter.gmflv2") as mock_gmflv2:
        mock_gmflv2.get_rm_following_list = mock.AsyncMock(return_value=["123", "456"])
        response = await client.post("/v1/post/RmFollowingList", json=["123", "456"])
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rm_following_list_invalid_body(client):
    """测试无效请求体（应返回 422）"""
    response = await client.post("/v1/post/RmFollowingList", json={"not": "a list"})
    assert response.status_code == 422


# ============================================================================
# POST /lot/upsert_lot_detail — 插入/更新抽奖详情
# ============================================================================


@pytest.mark.asyncio
async def test_upsert_lot_detail(client):
    """测试插入抽奖详情"""
    with mock.patch("controller.common.CommonRouter.grpc_sql_helper") as mock_helper:
        mock_helper.upsert_lot_detail = mock.AsyncMock(return_value={"status": "ok"})
        response = await client.post("/lot/upsert_lot_detail", json={"lottery_id": 123})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_upsert_lot_detail_empty_body(client):
    """测试空请求体"""
    with mock.patch("controller.common.CommonRouter.grpc_sql_helper") as mock_helper:
        mock_helper.upsert_lot_detail = mock.AsyncMock(return_value={"status": "ok"})
        response = await client.post("/lot/upsert_lot_detail", json={})
        assert response.status_code == 200


# ============================================================================
# GET /get_others_lot_dyn — 获取他人动态抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_get_others_lot_dyn(client):
    """测试获取他人动态抽奖"""
    with mock.patch("controller.common.CommonRouter.get_others_lot_dyn") as mock_svc:
        mock_svc.get_new_dyn = mock.AsyncMock(return_value=[])
        response = await client.get("/get_others_lot_dyn")
        assert response.status_code == 200


# ============================================================================
# GET /get_others_official_lot_dyn — 获取他人官方动态抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_get_others_official_lot_dyn(client):
    """测试获取他人官方动态抽奖"""
    with mock.patch("controller.common.CommonRouter.get_others_lot_dyn") as mock_svc:
        mock_svc.get_official_lot_dyn = mock.AsyncMock(return_value=[])
        response = await client.get("/get_others_official_lot_dyn")
        assert response.status_code == 200


# ============================================================================
# GET /get_others_big_lot — 获取他人大奖
# ============================================================================


@pytest.mark.asyncio
async def test_get_others_big_lot(client):
    """测试获取他人大奖"""
    with mock.patch("controller.common.CommonRouter.get_others_lot_dyn") as mock_svc:
        mock_svc.get_unignore_Big_lot_dyn = mock.AsyncMock(return_value=[])
        response = await client.get("/get_others_big_lot")
        assert response.status_code == 200


# ============================================================================
# GET /get_others_big_reserve — 获取重要预约抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_get_others_big_reserve_empty(client):
    """测试返回空列表"""
    with mock.patch("controller.common.CommonRouter.get_others_lot_dyn") as mock_svc:
        mock_svc.get_unignore_reserve_lot_space = mock.AsyncMock(return_value=[])
        response = await client.get("/get_others_big_reserve")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# GET /zhihu/get_others_lot_pins — 获取知乎抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_zhihu_lot_pins(client):
    """测试获取知乎抽奖"""
    with mock.patch("controller.common.CommonRouter.zhihu_lotScrapy") as mock_zhihu, \
         mock.patch("controller.common.CommonRouter.a_pushme", new_callable=mock.AsyncMock):
        mock_zhihu.api_get_all_pins = mock.AsyncMock(return_value=[])
        response = await client.get("/zhihu/get_others_lot_pins")
        assert response.status_code == 200


# ============================================================================
# GET /toutiao/get_others_lot_ids — 获取头条抽奖
# ============================================================================


@pytest.mark.asyncio
async def test_toutiao_lot_ids(client):
    """测试获取头条抽奖"""
    with mock.patch("controller.common.CommonRouter.toutiaoSpaceFeedLotService") as mock_svc, \
         mock.patch("controller.common.CommonRouter.a_pushme", new_callable=mock.AsyncMock):
        mock_svc.main = mock.AsyncMock(return_value=[])
        response = await client.get("/toutiao/get_others_lot_ids")
        assert response.status_code == 200
