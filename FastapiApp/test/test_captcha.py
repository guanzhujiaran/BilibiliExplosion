# -*- coding: utf-8 -*-
"""
验证码接口测试

测试端点 (前缀: /api/v1/captcha):
    GET  /gen      — 生成验证码
    POST /verify   — 验证验证码
"""

import pytest
from unittest import mock
from httpx import ASGITransport, AsyncClient

PREFIX = "/api/v1/captcha"


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCaptchaGen:

    @pytest.mark.asyncio
    async def test_gen_success(self, client):
        """成功生成验证码"""
        with mock.patch("controller.v1.captcha.captchaController.captcha_service") as mock_svc:
            mock_svc.generate_captcha = mock.AsyncMock(
                return_value=("captcha_abc123", "base64image==")
            )
            response = await client.get(f"{PREFIX}/gen")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["captcha_id"] == "captcha_abc123"
        assert data["data"]["image"] == "base64image=="

    @pytest.mark.asyncio
    async def test_gen_response_structure(self, client):
        """验证响应结构"""
        with mock.patch("controller.v1.captcha.captchaController.captcha_service") as mock_svc:
            mock_svc.generate_captcha = mock.AsyncMock(return_value=("id_001", "img_data"))
            response = await client.get(f"{PREFIX}/gen")
        data = response.json()
        assert "captcha_id" in data["data"]
        assert "image" in data["data"]


class TestCaptchaVerify:

    @pytest.mark.asyncio
    async def test_verify_valid(self, client):
        """验证码正确"""
        with mock.patch("controller.v1.captcha.captchaController.captcha_service") as mock_svc:
            mock_result = mock.MagicMock()
            mock_result.code = 0
            mock_result.message = "验证通过"
            mock_svc.validate_captcha = mock.AsyncMock(return_value=mock_result)
            response = await client.post(f"{PREFIX}/verify",
                                         json={"captcha_id": "captcha_001", "input_text": "ABCD"})
        assert response.status_code == 200
        assert response.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_verify_invalid(self, client):
        """验证码错误"""
        with mock.patch("controller.v1.captcha.captchaController.captcha_service") as mock_svc:
            mock_result = mock.MagicMock()
            mock_result.code = 400
            mock_result.message = "验证码错误"
            mock_svc.validate_captcha = mock.AsyncMock(return_value=mock_result)
            response = await client.post(f"{PREFIX}/verify",
                                         json={"captcha_id": "captcha_001", "input_text": "WRONG"})
        assert response.status_code == 200
        assert response.json()["code"] == 400

    @pytest.mark.asyncio
    async def test_missing_fields(self, client):
        """缺少必填字段"""
        r = await client.post(f"{PREFIX}/verify", json={})
        assert r.status_code == 422
        r = await client.post(f"{PREFIX}/verify", json={"captcha_id": "id_only"})
        assert r.status_code == 422
        r = await client.post(f"{PREFIX}/verify", json={"input_text": "text_only"})
        assert r.status_code == 422
