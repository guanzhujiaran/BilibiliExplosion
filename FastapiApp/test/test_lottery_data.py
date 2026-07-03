# -*- coding: utf-8 -*-
"""
B站抽奖数据库接口测试

测试端点 (前缀: /api/v1/lottery_database/bili):
    POST /GetReserveLottery   POST /GetOfficialLottery
    POST /GetChargeLottery    POST /GetLiveLottery
    POST /GetTopicLottery     GET  /GetAllLottery
    POST /AddDynamicLottery   POST /BulkAddDynamicLottery
    POST /AddTopicLottery     POST /AddOthersLotDyn
    POST /SearchLotteryByKeyword  POST /SubmitFeedback
    GET  /GetAllLotScrapyStatus   POST /GetOthersLotDynList
    GET  /GetLotteryFilterParams
"""

import pytest
from unittest import mock
from httpx import ASGITransport, AsyncClient

PREFIX = "/api/v1/lottery_database/bili"


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _base_body(**kwargs):
    body = {"page_num": 1, "page_size": 10}
    body.update(kwargs)
    return body


# ============================================================================
# POST /GetReserveLottery
# ============================================================================


class TestGetReserveLottery:
    """POST /GetReserveLottery"""

    @pytest.mark.asyncio
    async def test_basic(self, client):
        """基本请求"""
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_reserve_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(f"{PREFIX}/GetReserveLottery", json=_base_body())
        assert response.status_code == 200
        assert response.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_with_status(self, client):
        """按状态筛选"""
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_reserve_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(
                f"{PREFIX}/GetReserveLottery", json=_base_body(status="unfinished"),
            )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_page(self, client):
        """页码小于最小值应返回 422"""
        response = await client.post(f"{PREFIX}/GetReserveLottery", json={"page_num": 0, "page_size": 10})
        assert response.status_code == 422


# ============================================================================
# POST /GetOfficialLottery
# ============================================================================


class TestGetOfficialLottery:

    @pytest.mark.asyncio
    async def test_basic(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_official_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(f"{PREFIX}/GetOfficialLottery", json=_base_body())
        assert response.status_code == 200


# ============================================================================
# POST /GetChargeLottery
# ============================================================================


class TestGetChargeLottery:

    @pytest.mark.asyncio
    async def test_basic(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_charge_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(f"{PREFIX}/GetChargeLottery", json=_base_body())
        assert response.status_code == 200


# ============================================================================
# POST /GetLiveLottery
# ============================================================================


class TestGetLiveLottery:

    @pytest.mark.asyncio
    async def test_basic(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_live_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(f"{PREFIX}/GetLiveLottery", json=_base_body())
        assert response.status_code == 200


# ============================================================================
# POST /GetTopicLottery
# ============================================================================


class TestGetTopicLottery:

    @pytest.mark.asyncio
    async def test_basic(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_topic_lottery",
            new_callable=mock.AsyncMock, return_value=([], 0),
        ):
            response = await client.post(f"{PREFIX}/GetTopicLottery", json=_base_body())
        assert response.status_code == 200


# ============================================================================
# GET /GetAllLottery
# ============================================================================


class TestGetAllLottery:

    @pytest.mark.asyncio
    async def test_default(self, client):
        empty = {
            "common_lottery": [],
            "common_lottery_total": 0,
            "must_join_common_lottery": [],
            "reserve_lottery": [],
            "official_lottery": [],
        }
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_all_lottery",
            new_callable=mock.AsyncMock, return_value=empty,
        ):
            # GetAllLottery 是 POST 端点
            response = await client.post(f"{PREFIX}/GetAllLottery")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_page_size(self, client):
        """page_size 超出最大值"""
        response = await client.post(f"{PREFIX}/GetAllLottery?page_size=2000")
        assert response.status_code == 422


# ============================================================================
# POST /AddDynamicLottery
# ============================================================================


class TestAddDynamicLottery:

    @pytest.mark.asyncio
    async def test_by_id(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.add_dynamic_lottery_by_dynamic_id",
            new_callable=mock.AsyncMock,
            return_value={"msg": "ok", "is_succ": True, "is_new": True, "dynamic_id_or_url": "9876543210"},
        ):
            response = await client.post(f"{PREFIX}/AddDynamicLottery", json={"dynamic_id_or_url": "9876543210"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_body(self, client):
        response = await client.post(f"{PREFIX}/AddDynamicLottery", json={})
        assert response.status_code == 422


# ============================================================================
# POST /BulkAddDynamicLottery
# ============================================================================


class TestBulkAddDynamicLottery:

    @pytest.mark.asyncio
    async def test_bulk(self, client):
        with mock.patch("controller.v1.lotttery_database.bili.LotteryData.asyncio_gather",
                        new_callable=mock.AsyncMock,
                        return_value=[{"msg": "ok", "is_succ": True, "is_new": True, "dynamic_id_or_url": "123"}]):
            response = await client.post(f"{PREFIX}/BulkAddDynamicLottery",
                                         json={"dynamic_id_or_urls": ["123", "456"]})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_field(self, client):
        response = await client.post(f"{PREFIX}/BulkAddDynamicLottery", json={})
        assert response.status_code == 422


# ============================================================================
# POST /AddTopicLottery
# ============================================================================


class TestAddTopicLottery:

    @pytest.mark.asyncio
    async def test_add(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.add_topic_lottery",
            new_callable=mock.AsyncMock,
            return_value={"msg": "ok", "is_succ": True, "is_new": True, "topic_id": "12345"},
        ):
            response = await client.post(f"{PREFIX}/AddTopicLottery", json={"topic_id": 12345})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_field(self, client):
        response = await client.post(f"{PREFIX}/AddTopicLottery", json={})
        assert response.status_code == 422


# ============================================================================
# POST /AddOthersLotDyn — 需登录，无登录态返回 401
# ============================================================================


class TestAddOthersLotDyn:

    @pytest.mark.asyncio
    async def test_unauthorized(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.require_gateway_login",
        ) as mock_auth:
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(status_code=401, detail="未登录")
            response = await client.post(f"{PREFIX}/AddOthersLotDyn", json={"dynamic_id_or_url": "123"})
            assert response.status_code == 401


# ============================================================================
# POST /SearchLotteryByKeyword
# ============================================================================


class TestSearchLotteryByKeyword:

    @pytest.mark.asyncio
    async def test_search(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.search_lottery_text",
            new_callable=mock.AsyncMock, return_value=[],
        ), mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.get_lottery_entity_num",
            new_callable=mock.AsyncMock, return_value=0,
        ):
            response = await client.post(f"{PREFIX}/SearchLotteryByKeyword",
                                         json={"keyword": "抽奖", "page_num": 1, "page_size": 10})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_keyword(self, client):
        response = await client.post(f"{PREFIX}/SearchLotteryByKeyword",
                                     json={"page_num": 1, "page_size": 10})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_keyword(self, client):
        response = await client.post(f"{PREFIX}/SearchLotteryByKeyword",
                                     json={"keyword": "", "page_num": 1, "page_size": 10})
        assert response.status_code == 422


# ============================================================================
# POST /SubmitFeedback
# ============================================================================


class TestSubmitFeedback:

    @pytest.mark.asyncio
    async def test_submit(self, client):
        with mock.patch("controller.v1.lotttery_database.bili.LotteryData.a_pushme",
                        new_callable=mock.AsyncMock) as mock_push:
            mock_resp = mock.MagicMock()
            mock_resp.status_code = 200
            mock_push.return_value = mock_resp
            response = await client.post(f"{PREFIX}/SubmitFeedback", json={"message": "测试反馈"})
        assert response.status_code == 200
        assert response.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_missing_message(self, client):
        response = await client.post(f"{PREFIX}/SubmitFeedback", json={})
        assert response.status_code == 422


# ============================================================================
# GET /GetAllLotScrapyStatus
# ============================================================================


class TestGetAllLotScrapyStatus:

    @pytest.mark.asyncio
    async def test_get(self, client):
        response = await client.get(f"{PREFIX}/GetAllLotScrapyStatus")
        assert response.status_code == 200
        assert response.json()["code"] == 0


# ============================================================================
# POST /GetOthersLotDynList — 需登录
# ============================================================================


class TestGetOthersLotDynList:

    @pytest.mark.asyncio
    async def test_unauthorized(self, client):
        with mock.patch(
            "controller.v1.lotttery_database.bili.LotteryData.require_gateway_login",
        ) as mock_auth:
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(status_code=401, detail="未登录")
            response = await client.post(f"{PREFIX}/GetOthersLotDynList", json=_base_body())
            assert response.status_code == 401


# ============================================================================
# GET /GetLotteryFilterParams
# ============================================================================


class TestGetLotteryFilterParams:

    @pytest.mark.asyncio
    async def test_get(self, client):
        response = await client.get(f"{PREFIX}/GetLotteryFilterParams")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "endpoints" in data["data"]
