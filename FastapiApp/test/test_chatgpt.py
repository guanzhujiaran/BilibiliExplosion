# -*- coding: utf-8 -*-
"""
ChatGPT/LLM 接口测试

测试端点 (前缀: /api/v1/ChatGpt3_5):
    POST /ReplySingle      — 单轮回复
    GET  /LLMStatus        — LLM 状态
    POST /ResetLLMStatus   — 重置 LLM 状态
    GET  /helloWorld       — 健康检查
"""

import time
import pytest
from unittest import mock
from httpx import ASGITransport, AsyncClient

PREFIX = "/api/v1/ChatGpt3_5"


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestReplySingle:

    @pytest.mark.asyncio
    async def test_success(self, client):
        with mock.patch("controller.v1.ChatGpt3_5.ReplySingle.chatgpt") as mock_ai:
            mock_ai.SingleReply = mock.AsyncMock(return_value="这是AI的回答")
            response = await client.post(f"{PREFIX}/ReplySingle",
                                         json={"question": "今天天气怎么样？", "ts": int(time.time())})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["answer"] == "这是AI的回答"

    @pytest.mark.asyncio
    async def test_missing_field(self, client):
        response = await client.post(f"{PREFIX}/ReplySingle", json={"question": "只有问题"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_service_error(self, client):
        with mock.patch("controller.v1.ChatGpt3_5.ReplySingle.chatgpt") as mock_ai:
            mock_ai.SingleReply = mock.AsyncMock(side_effect=Exception("AI服务不可用"))
            response = await client.post(f"{PREFIX}/ReplySingle",
                                         json={"question": "测试", "ts": int(time.time())})
        assert response.status_code == 200
        assert response.json()["code"] == 500


class TestLLMStatus:

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        with mock.patch("controller.v1.ChatGpt3_5.ReplySingle.chatgpt") as mock_ai:
            mock_ai.show_openai_client.return_value = mock.MagicMock(
                available_num=3, total_num=5, llm_list=[]
            )
            response = await client.get(f"{PREFIX}/LLMStatus")
        assert response.status_code == 200
        assert response.json()["code"] == 0


class TestResetLLMStatus:

    @pytest.mark.asyncio
    async def test_reset(self, client):
        # base_url: str | None = Body(...) → body 是纯字符串
        with mock.patch("controller.v1.ChatGpt3_5.ReplySingle.chatgpt") as mock_ai:
            mock_ai.reset_llm_status.return_value = "已重置"
            response = await client.post(f"{PREFIX}/ResetLLMStatus",
                                         content='"http://localhost:1234"',
                                         headers={"Content-Type": "application/json"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_base_url(self, client):
        # base_url: str | None = Body(...) → null body is valid
        response = await client.post(f"{PREFIX}/ResetLLMStatus",
                                     content="null",
                                     headers={"Content-Type": "application/json"})
        assert response.status_code != 404, f"Route should exist, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_empty_body(self, client):
        # 空 body → 422（Body(...) 要求必填）
        response = await client.post(f"{PREFIX}/ResetLLMStatus")
        assert response.status_code == 422


class TestHelloWorld:

    @pytest.mark.asyncio
    async def test_mode_1(self, client):
        response = await client.get(f"{PREFIX}/helloWorld?mode=1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["data"], dict)

    @pytest.mark.asyncio
    async def test_mode_2(self, client):
        response = await client.get(f"{PREFIX}/helloWorld?mode=2")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert isinstance(data["data"], str)

    @pytest.mark.asyncio
    async def test_invalid_mode(self, client):
        # mode: int = Query(..., le=2)，mode=3 触发 Pydantic 校验 → 422
        response = await client.get(f"{PREFIX}/helloWorld?mode=3")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_mode(self, client):
        response = await client.get(f"{PREFIX}/helloWorld")
        assert response.status_code == 422
