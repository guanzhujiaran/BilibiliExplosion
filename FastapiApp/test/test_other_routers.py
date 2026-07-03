# -*- coding: utf-8 -*-
"""
其他路由器接口测试

测试端点:
    GET  /api/v1/ip_info/get              — IPv6信息
    GET  /damo/semantic                   — 情感分析
    POST /damo/semantic                   — 情感分析
    GET  /api/v1/rpc/methods              — RPC方法列表
    POST /api/v1/samsClub/set_new_auth_token  — 更新auth_token
    GET  /api/v1/samsClub/samsclub_api_status — API状态

    GET /api/v1/lottery_database/bili/lottery_statistic/rank/lottery_hof/{lot_type}
    GET /api/v1/lottery_database/bili/lottery_statistic/rank/lottery_result
    POST /api/v1/lottery_database/bili/zhuanlan/lotteryArticle
"""

import pytest
from unittest import mock
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# IP Info
# ============================================================================


class TestIPInfo:

    @pytest.mark.asyncio
    async def test_get(self, client):
        with mock.patch(
            "controller.v1.ip_info.get_ip_info.get_ipv6_from_redis",
            new_callable=mock.AsyncMock, return_value="2001:db8::1",
        ):
            response = await client.get("/api/v1/ip_info/get")
        assert response.status_code == 200
        assert response.json()["data"]["ipv6"] == "2001:db8::1"

    @pytest.mark.asyncio
    async def test_get_empty(self, client):
        with mock.patch(
            "controller.v1.ip_info.get_ip_info.get_ipv6_from_redis",
            new_callable=mock.AsyncMock, return_value=None,
        ):
            response = await client.get("/api/v1/ip_info/get")
        assert response.status_code == 200
        assert response.json()["data"]["ipv6"] == ""


# ============================================================================
# Damo ML
# ============================================================================


class TestDamoML:

    @pytest.mark.asyncio
    async def test_semantic_get(self, client):
        response = await client.get("/damo/semantic?query=你好")
        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_semantic_get_empty(self, client):
        response = await client.get("/damo/semantic?query=")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_semantic_post(self, client):
        response = await client.post("/damo/semantic", json={"data": "你好"})
        assert response.status_code == 200
        assert response.json() is True

    @pytest.mark.asyncio
    async def test_semantic_post_empty(self, client):
        response = await client.post("/damo/semantic", json={})
        assert response.status_code == 200


# ============================================================================
# RPC Info
# ============================================================================


class TestRpcInfo:

    @pytest.mark.asyncio
    async def test_get_methods(self, client):
        response = await client.get("/api/v1/rpc/methods")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["data"], list)


# ============================================================================
# SamsClub
# ============================================================================


class TestSamsClub:

    @pytest.mark.asyncio
    async def test_set_new_auth_token(self, client):
        # auth_token: str (无 Body 注解 → FastAPI 当作 query parameter)
        with mock.patch("controller.v1.samsClub.samsClubController.sams_club_crawler") as mock_cr:
            mock_cr.api.update_auth_token = mock.AsyncMock()
            response = await client.post(
                "/api/v1/samsClub/set_new_auth_token?auth_token=new_token_123",
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_new_auth_token_missing(self, client):
        # 缺少 query param → 422
        response = await client.post("/api/v1/samsClub/set_new_auth_token")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_api_status(self, client):
        import datetime
        with mock.patch("controller.v1.samsClub.samsClubController.sams_club_crawler") as mock_cr:
            from Service.samsclub.api.samsclub_api import SamsClubApiStatus
            mock_cr.api.status = SamsClubApiStatus(
                token="test_token",
                token_stat="有效",
                latest_request_ts=datetime.datetime.now(),
            )
            response = await client.get("/api/v1/samsClub/samsclub_api_status")
        assert response.status_code == 200


# ============================================================================
# Bili Lottery Statistic
# ============================================================================


STAT = "/api/v1/lottery_database/bili"


class TestLotteryStatistic:

    @pytest.mark.asyncio
    async def test_lottery_hof_basic(self, client):
        """验证抽奖统计路由存在（响应非 404）"""
        response = await client.get(f"{STAT}/lottery_hof/official?rank_type=winners")
        assert response.status_code != 404, f"Route should exist, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_lottery_hof_missing_rank_type(self, client):
        response = await client.get(f"{STAT}/lottery_hof/official")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_lottery_result(self, client):
        response = await client.get(f"{STAT}/lottery_result?uid=12345&lot_type=official&rank_type=winners")
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_lottery_result_missing_params(self, client):
        response = await client.get(f"{STAT}/lottery_result")
        assert response.status_code == 422


# ============================================================================
# Bili Zhuanlan
# ============================================================================


ZHUANLAN = "/api/v1/lottery_database/bili/zhuanlan"


class TestZhuanlan:

    @pytest.mark.asyncio
    async def test_lottery_article_endpoint_exists(self, client):
        """验证专栏接口路由存在（非 404）"""
        response = await client.post(f"{ZHUANLAN}/lotteryArticle",
                                     json={"abstract_msg": "测试", "save_to_local_file": False})
        assert response.status_code != 404, f"Route should exist, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_lottery_article_default_abstract(self, client):
        """使用默认摘要值"""
        response = await client.post(f"{ZHUANLAN}/lotteryArticle", json={})
        assert response.status_code != 404
